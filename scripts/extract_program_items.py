#!/usr/bin/env python3
"""Extract the CM1/CM2 curriculum from ``docs/programme-cm1-cm2.pdf`` into a seed file.

Run it from the repo root::

    ./scripts/extract_program_items.py

It rewrites ``core/seed/program_items.json``. The point of keeping it in the repo is
that the seed stays checkable against the PDF: every item here is text the PDF prints,
copied, never rephrased (MASTER-PROMPT.md §10).

Two shapes of page are read:

* pages laid out as prose with « Objectifs d'apprentissage » lists — français,
  mathématiques, langues vivantes, EPS. The heading above the list is the item's
  title, the list is its description.
* pages laid out as multi-column tables — EMC, histoire-géographie, EVAR, and the
  enseignements artistiques. Columns are recovered from the blank gutters that
  ``pdftotext -layout`` preserves, and the item is the thème or the section.

Sciences et technologie (p. 90-107) has no text layer at all — those pages are images.
It is transcribed by hand into ``scripts/curriculum_sciences.json`` and merged here.
"""

import json
import re
import subprocess
import sys
import unicodedata
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curriculum_map import (
    HISTOIRE_GEOGRAPHIE,
    LEVEL_MARKERS,
    OTHER_LEVEL_MARKERS,
    PROGRAMMES,
    SOURCE_FILE,
    TABLES,
    Programme,
    TableProgramme,
)

REPO = Path(__file__).resolve().parents[1]
PDF = REPO / SOURCE_FILE
SEED = REPO / "core" / "seed" / "program_items.json"
SCIENCES = Path(__file__).resolve().parent / "curriculum_sciences.json"

# The source writes the plural when a block lists several objectives and the singular
# when it lists one (EPS does both on the same page).
OBJECTIVES_MARKERS = frozenset({"Objectifs d’apprentissage", "Objectif d’apprentissage"})
# Shortest run of characters that can carry a piece of a wrapped column header.
HEADER_FRAGMENT = 10
GUTTER = 3  # blank columns that separate two table columns


class Item(NamedTuple):
    """One extracted program item, before it is written out."""

    level: str
    subject: str
    domain: str | None
    domain_label: str | None
    title: str
    description: str
    page: int


def page_text(page: int) -> str:
    """Read one page of the PDF with its layout preserved."""
    return subprocess.run(  # noqa: S603
        ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(PDF), "-"],  # noqa: S607
        capture_output=True,
        check=True,
        text=True,
    ).stdout


def join_wrapped(lines: list[str]) -> list[str]:
    """Rejoin lines the PDF wrapped mid-sentence.

    A wrapped line starts lower-case (or with a closing bracket or a digit
    continuing a numbered clause); a new objective starts with a capital.
    """
    joined: list[str] = []
    for line in lines:
        if not line:  # a blank line the prose reader kept as a paragraph break
            joined.append(line)
            continue
        first = line[0]
        continues = joined and joined[-1] and (first.islower() or first in ")]»,;")
        if continues:
            joined[-1] = f"{joined[-1]} {line}"
        else:
            joined.append(line)
    return joined


SENTENCE_END = ".:;,"


def _heading_before(lines: list[str], section: str) -> str:
    """Find the heading an « Objectifs d'apprentissage » list hangs under.

    Usually it is the line right above — a heading, never a sentence, so it never
    closes on a full stop. In mathématiques it is often further up, with paragraphs of
    explanation in between; there the list belongs to the section heading the reader
    is already inside, which is what ``section`` carries.
    """
    above = next((line.strip() for line in reversed(lines) if line.strip()), "")
    looks_like_heading = above and above[-1] not in SENTENCE_END and any(c.isalpha() for c in above)
    return above if looks_like_heading else section


def _objectives_under(lines: list[str]) -> list[str]:
    """Collect the objectives printed under an « Objectifs d'apprentissage » marker."""
    body: list[str] = []
    for following in lines:
        stripped = following.strip()
        if not stripped:
            break
        if stripped in OBJECTIVES_MARKERS:
            body.pop()  # the line before it was the next block's heading
            break
        body.append(stripped)
    return body


def _prose_under(lines: list[str], is_boundary: Callable[[str], bool]) -> list[str]:
    """Collect everything printed under a heading, up to the next heading."""
    body: list[str] = []
    for following in lines:
        stripped = following.strip()
        if not stripped:
            if body:
                body.append("")
            continue
        if is_boundary(stripped):
            break
        body.append(stripped)
    while body and not body[-1]:
        body.pop()
    return body


class _Block(NamedTuple):
    """A heading and the text under it, ready to become an item."""

    title: str
    body: list[str]
    level: str | None


def read_prose(programme: Programme) -> list[Item]:
    """Read every item of one prose programme.

    The niveau and the domaine are page-spanning state: the source prints « Cours
    moyen deuxième année » once and everything under it belongs to CM2 until the next
    marker, however many pages later that is.
    """
    sections = {section.heading: section for section in programme.sections}
    paragraphs = set(programme.paragraph_titles)
    pattern = re.compile(programme.heading_pattern) if programme.heading_pattern else None

    def is_boundary(line: str) -> bool:
        """Say whether a block of prose ends here, at the next heading of any kind."""
        return (
            line in paragraphs
            or line in sections
            or line in LEVEL_MARKERS
            or line in OTHER_LEVEL_MARKERS
            or bool(pattern and pattern.search(line))
        )

    opening = programme.sections[0]
    level: str | None = None
    section = opening
    coarse = opening
    items: list[Item] = []

    for page in range(programme.first_page, programme.last_page + 1):
        lines = page_text(page).splitlines()
        for index, raw in enumerate(lines):
            line = raw.strip()
            if not line:
                continue
            if line in LEVEL_MARKERS:
                level = LEVEL_MARKERS[line]
                section = coarse
                continue
            if line in OTHER_LEVEL_MARKERS:
                level = None
                continue
            if line in sections:
                section = sections[line]
                if section.coarse:
                    coarse = section
                continue

            block = _block_at(
                lines, index, level, section.heading, pattern, paragraphs, is_boundary
            )
            if block is None:
                continue
            level = block.level
            items.append(
                Item(
                    level=block.level or "",
                    subject=programme.subject,
                    domain=section.code,
                    domain_label=section.label,
                    title=block.title,
                    description="\n".join(join_wrapped(block.body)),
                    page=page,
                )
            )
    return items


def _block_at(  # noqa: PLR0913 - the reader's whole state, passed rather than shared
    lines: list[str],
    index: int,
    level: str | None,
    section: str,
    pattern: re.Pattern[str] | None,
    paragraphs: set[str],
    is_boundary: Callable[[str], bool],
) -> _Block | None:
    """Read the block the line at ``index`` opens, if it opens one."""
    line = lines[index].strip()
    match = pattern.search(line) if pattern else None
    if match:
        # The heading names the niveau it belongs to; trust it over the last marker
        # seen, which may be several pages back.
        return _Block(line, _prose_under(lines[index + 1 :], is_boundary), match.group(1))
    if level is None:
        return None
    if line in paragraphs:
        return _Block(line, _prose_under(lines[index + 1 :], is_boundary), level)
    if pattern or line not in OBJECTIVES_MARKERS:
        # A programme whose headings all match the pattern keeps its « Objectifs
        # d'apprentissage » lists inside the block that opened above.
        return None
    title = _heading_before(lines[:index], section)
    body = _objectives_under(lines[index + 1 :])
    return _Block(title, body, level) if title and body else None


def columns(lines: list[str]) -> list[list[str]]:
    """Split layout-preserved lines into the columns their blank gutters describe."""
    width = max((len(line) for line in lines), default=0)
    padded = [line.ljust(width) for line in lines]
    blank = [all(line[column] == " " for line in padded) for column in range(width)]

    gutters: list[tuple[int, int]] = []
    start: int | None = None
    for column, empty in enumerate([*blank, False]):
        if empty and start is None:
            start = column
        elif not empty and start is not None:
            if column - start >= GUTTER:
                gutters.append((start, column))
            start = None

    bounds = [0, *(gutter[1] for gutter in gutters if gutter[0] > 0), width]
    result: list[list[str]] = []
    for left, right in pairwise(bounds):
        cell = [line[left:right].rstrip() for line in padded]
        text = [entry.strip() for entry in cell if entry.strip()]
        if text:
            result.append(text)
    return result


def _is_column_header(line: str, columns: tuple[str, ...]) -> bool:
    """Tell a piece of a column's header from a row of the table.

    A header the source centred over two lines arrives here in pieces, so a piece
    counts when it sits inside one of the column names — long enough that a row of
    the table cannot be mistaken for one.
    """
    return len(line) >= HEADER_FRAGMENT and any(
        line in column or column in line for column in columns
    )


def _table_description(
    programme: TableProgramme, region: list[tuple[int, str]], intro: list[str]
) -> str:
    """Rebuild a table as text, column by column, under the names the source prints.

    A table can run over a page break, and the two halves rarely line up on the same
    character columns, so each page's slice is split on its own gutters and the pieces
    are stitched together per column afterwards.
    """
    per_page: dict[int, list[str]] = {}
    for page, line in region:
        per_page.setdefault(page, []).append(line)

    cells: list[list[str]] = [[] for _ in programme.columns]
    for lines in per_page.values():
        split = columns(lines)
        for index, cell in enumerate(split[: len(cells)]):
            cells[index].extend(cell)

    parts = list(intro)
    for name, cell in zip(programme.columns, cells, strict=True):
        if cell:
            parts.append(f"{name}\n" + "\n".join(join_wrapped(cell)))
    return "\n\n".join(part for part in parts if part)


def read_histoire_geographie() -> list[Item]:
    """Read the thèmes of the histoire-géographie programme.

    A thème is the item: the source names it, gives it its question, its table of
    objectives, attendus and repères, and its mots-clés, and plans the year in thèmes.
    """
    programme = HISTOIRE_GEOGRAPHIE
    subject = programme.subject
    level: str | None = None
    items: list[Item] = []
    current: dict[str, object] | None = None

    def flush() -> None:
        """Close the thème being read and turn it into an item."""
        if current is None:
            return
        description = _table_description(
            programme,
            current["region"],  # type: ignore[arg-type]
            current["intro"],  # type: ignore[arg-type]
        )
        if description:
            items.append(
                Item(
                    level=current["level"],  # type: ignore[arg-type]
                    subject=current["subject"],  # type: ignore[arg-type]
                    domain=None,
                    domain_label=None,
                    title=current["title"],  # type: ignore[arg-type]
                    description=description,
                    page=current["page"],  # type: ignore[arg-type]
                )
            )

    for page in range(programme.first_page, programme.last_page + 1):
        for raw in page_text(page).splitlines():
            line = raw.strip()
            if line in {"Histoire", "Géographie"}:
                flush()
                current = None
                subject = "histoire" if line == "Histoire" else "geographie"
                continue
            marker = next((key for key in LEVEL_MARKERS if line.startswith(key)), None)
            if marker:
                flush()
                current = None
                level = LEVEL_MARKERS[marker]
                continue
            if line in OTHER_LEVEL_MARKERS or line.startswith("Sixième"):
                flush()
                current = None
                level = None
                continue
            if line.startswith("Thème ") and level is not None:
                flush()
                current = {
                    "level": level,
                    "subject": subject,
                    "title": line,
                    "page": page,
                    "intro": [],
                    "region": [],
                }
                continue
            if current is None or not line:
                continue
            if line.startswith(("Question :", "Mots-clés :", "Mots clés :", "Fil directeur")):
                current["intro"].append(line)  # type: ignore[union-attr]
            elif not _is_column_header(line, programme.columns):
                current["region"].append((page, raw))  # type: ignore[union-attr]
    flush()
    return items


def read_sectioned_tables(programme: TableProgramme) -> list[Item]:
    """Read a programme cut into named sections, each holding one table."""
    level = programme.level
    items: list[Item] = []
    current: dict[str, object] | None = None
    levels = dict(programme.levels)
    headers = {part for column in programme.columns for part in column.split(" ")} | set(
        programme.columns
    )

    def flush() -> None:
        """Close the section being read and turn it into an item."""
        if current is None:
            return
        description = _table_description(
            programme,
            current["region"],  # type: ignore[arg-type]
            current["intro"],  # type: ignore[arg-type]
        )
        if not description:
            return
        title = current["title"]  # type: ignore[assignment]
        items.append(
            Item(
                level=current["level"],  # type: ignore[arg-type]
                subject=programme.subject,
                domain=slug(title) if programme.domain_from_section else programme.domain,
                domain_label=title if programme.domain_from_section else programme.domain_label,
                title=title,  # type: ignore[arg-type]
                description=description,
                page=current["page"],  # type: ignore[arg-type]
            )
        )

    for page in range(programme.first_page, programme.last_page + 1):
        lines = page_text(page).splitlines()
        skip_next = False
        for index, raw in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            line = raw.strip()
            if line in levels:
                flush()
                current = None
                level = levels[line]
                continue
            if any(line.startswith(stop) for stop in programme.stops):
                flush()
                current = None
                level = ""
                continue
            heading, consumed = _match_section(lines, index, programme.sections)
            if heading and level:
                flush()
                skip_next = consumed
                current = {
                    "level": level,
                    "title": heading,
                    "page": page,
                    "intro": [],
                    "region": [],
                }
                continue
            if current is None or not line:
                continue
            if line.startswith(programme.intro_prefixes) if programme.intro_prefixes else False:
                current["intro"].append(line)  # type: ignore[union-attr]
                continue
            if line in headers or _is_column_header(line, programme.columns):
                continue
            current["region"].append((page, raw))  # type: ignore[union-attr]
    flush()
    return items


def _match_section(lines: list[str], index: int, sections: tuple[str, ...]) -> tuple[str, bool]:
    """Match a section heading at ``index``, joining the next line when it wrapped."""
    line = lines[index].strip()
    if line in sections:
        return line, False
    if index + 1 < len(lines):
        joined = f"{line} {lines[index + 1].strip()}".strip()
        if joined in sections:
            return joined, True
    return "", False


def read_sciences() -> list[Item]:
    """Read the hand-transcribed sciences et technologie programme.

    Pages 92-107 of the source are images with no text layer, so they were read in
    vision and copied into ``scripts/curriculum_sciences.json`` rather than parsed.
    """
    payload = json.loads(SCIENCES.read_text(encoding="utf-8"))
    return [
        Item(
            level=item["level"],
            subject=payload["subject"],
            domain=domain["code"],
            domain_label=domain["label"],
            title=item["title"],
            description=item["description"],
            page=item["page"],
        )
        for domain in payload["domains"]
        for item in domain["items"]
    ]


def slug(text: str) -> str:
    """Turn a heading into a domaine code."""
    stripped = unicodedata.normalize("NFKD", text.replace("’", "'"))
    ascii_only = stripped.encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", ascii_only.lower())).strip("-")


def main() -> None:
    """Write ``core/seed/program_items.json``."""
    items: list[Item] = []
    for programme in PROGRAMMES:
        items.extend(read_prose(programme))
    items.extend(read_sciences())
    items.extend(read_histoire_geographie())
    for table in TABLES:
        items.extend(read_sectioned_tables(table))

    domains: dict[tuple[str, str], str] = {}
    for item in items:
        if item.domain:
            domains[item.subject, item.domain] = item.domain_label or item.domain

    payload = {
        "$comment": [
            "Items des programmes officiels CM1/CM2, extraits de docs/programme-cm1-cm2.pdf",
            "par scripts/extract_program_items.py. Titres et descriptions sont le texte du PDF,",
            "recopié : rien n'est reformulé (MASTER-PROMPT.md §10).",
        ],
        "items": [
            {
                "level": item.level,
                "subject": item.subject,
                "domain": item.domain,
                "title": item.title,
                "description": item.description,
                "source_file": SOURCE_FILE,
                "source_page": item.page,
            }
            for item in items
        ],
    }
    SEED.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(items)} items -> {SEED.relative_to(REPO)}")  # noqa: T201
    print("domaines référencés (à tenir dans core/seed/subjects.json) :")  # noqa: T201
    for (subject, code), label in sorted(domains.items()):
        print(f"  {subject:<24} {code:<52} {label}")  # noqa: T201


if __name__ == "__main__":
    main()
