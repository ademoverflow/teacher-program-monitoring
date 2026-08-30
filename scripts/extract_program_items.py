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
    Section,
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
GUTTER = 3  # narrowest run of blank columns that can separate two table columns
GUTTER_TOLERANCE = 0.2  # share of a table's lines allowed to write through a gutter
# Running heads and page feet the source repeats: full-width, so they would flatten
# every gutter of the table they land in.
PAGE_FURNITURE = ("D’après le BOEN", "no 25 du 22 juin", "© Direction générale")
# Bullets the source draws in a symbol font, and the character they are drawn as.
SYMBOL_BULLETS = ("\uf0b7", "\uf09f")
BULLET = "•"


# Two of a table's columns sharing a line: text, a run of spaces, more text. A cell
# that opens with a bullet indents its own text, which is not that.
COLUMN_BLEED = re.compile(r"\S {3,}\S")
BULLET_INDENT = re.compile(r"^[-•—]\s+")


def bleeds(description: str) -> bool:
    """Say whether a table's columns failed to separate anywhere in a description.

    Rebuilt columns read as prose; a line that still holds a run of spaces between two
    words is one where the gutter was not found and two columns were welded together.
    The item is still the PDF's own text, but shuffled, so it is worth a second look.
    """
    return any(
        COLUMN_BLEED.search(BULLET_INDENT.sub("", line)) for line in description.splitlines()
    )


class Item(NamedTuple):
    """One extracted program item, before it is written out."""

    level: str
    subject: str
    domain: str | None
    domain_label: str | None
    title: str
    description: str
    page: int

    @property
    def needs_review(self) -> bool:
        """§8 Phase 2: « needs_review sur tout item incertain »."""
        return bleeds(self.description)


def page_text(page: int) -> str:
    """Read one page of the PDF with its layout preserved.

    The bullets of the EMC and EVAR tables are drawn in a symbol font and come back as
    private-use code points, which no French collation and no reader can do anything
    with; they are turned back into the bullet they are drawn as.
    """
    text = subprocess.run(  # noqa: S603
        ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(PDF), "-"],  # noqa: S607
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    for symbol in SYMBOL_BULLETS:
        text = text.replace(symbol, BULLET)
    return text


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
# A « Question : … » or « Mots-clés : … » line runs on when it does not close: those
# lines are printed full-width above the table and wrap onto the next line.
SENTENCE_CLOSE = ".?!"


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


class _Headings(NamedTuple):
    """How one prose programme prints its headings.

    Three ways of recognising one, all derived from the same ``Programme``: the
    sections it is cut into, the headings whose item is the prose below them, and — for
    langues vivantes, whose headings are too many to list — the shape they take.
    """

    sections: dict[str, Section]
    paragraphs: set[str]
    pattern: re.Pattern[str] | None

    @classmethod
    def of(cls, programme: Programme) -> "_Headings":
        """Read the three off a programme."""
        return cls(
            {section.heading: section for section in programme.sections},
            set(programme.paragraph_titles),
            re.compile(programme.heading_pattern) if programme.heading_pattern else None,
        )

    def ends_a_block(self, line: str) -> bool:
        """Say whether a block of prose ends here, at the next heading of any kind."""
        return (
            line in self.paragraphs
            or line in self.sections
            or line in LEVEL_MARKERS
            or line in OTHER_LEVEL_MARKERS
            or bool(self.pattern and self.pattern.search(line))
        )

    def block_at(
        self, lines: list[str], index: int, level: str | None, section: str
    ) -> "_Block | None":
        """Read the block the line at ``index`` opens, if it opens one."""
        line = lines[index].strip()
        under = lines[index + 1 :]
        match = self.pattern.search(line) if self.pattern else None
        if match:
            # The heading names the niveau it belongs to; trust it over the last
            # marker seen, which may be several pages back.
            return _Block(line, _prose_under(under, self.ends_a_block), match.group(1))
        if level is None:
            return None
        if line in self.paragraphs:
            return _Block(line, _prose_under(under, self.ends_a_block), level)
        if self.pattern or line not in OBJECTIVES_MARKERS:
            # A programme whose headings all match the pattern keeps its « Objectifs
            # d'apprentissage » lists inside the block that opened above.
            return None
        title = _heading_before(lines[:index], section)
        body = _objectives_under(under)
        return _Block(title, body, level) if title and body else None


def read_prose(programme: Programme) -> list[Item]:
    """Read every item of one prose programme.

    The niveau and the domaine are page-spanning state: the source prints « Cours
    moyen deuxième année » once and everything under it belongs to CM2 until the next
    marker, however many pages later that is.
    """
    headings = _Headings.of(programme)
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
            if line in headings.sections:
                section = headings.sections[line]
                if section.coarse:
                    coarse = section
                continue

            block = headings.block_at(lines, index, level, section.heading)
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


def gutters(lines: list[str], expected: int) -> list[int]:
    """Find where the ``expected`` columns of a table start and end.

    A gutter is a run of character positions blank down every line of the table. A few
    cells in the source run wide enough to leave a single space where the gutter should
    be, and that loses the gutter entirely, welding two columns into one line by line;
    so when a table does not yield ``expected - 1`` gutters, the rule is relaxed one
    line at a time until it does.

    Relaxing lets in candidates that are not gutters, so the runs are ranked by what a
    gutter actually does: separate text. A run scores the number of lines that have
    text on both sides of it, which is nil for the right margin and small for a ragged
    edge inside a column.
    """
    width = max((len(line) for line in lines), default=0)
    padded = [line.ljust(width) for line in lines]
    blank_lines = [sum(1 for line in padded if line[column] == " ") for column in range(width)]

    def runs_blank_on(threshold: int) -> list[tuple[int, int]]:
        """Every run of at least ``GUTTER`` positions blank on ``threshold`` lines."""
        found: list[tuple[int, int]] = []
        start: int | None = None
        for column in range(width + 1):
            empty = column < width and blank_lines[column] >= threshold
            if empty and start is None:
                start = column
            elif not empty and start is not None:
                if column - start >= GUTTER and start > 0:
                    found.append((start, column))
                start = None
        return found

    def separations(run: tuple[int, int]) -> int:
        """Count the lines this run actually stands between."""
        left, right = run
        return sum(1 for line in padded if line[:left].strip() and line[right:].strip())

    runs: list[tuple[int, int]] = []
    for written_through in range(round(len(padded) * GUTTER_TOLERANCE) + 1):
        runs = runs_blank_on(len(padded) - written_through)
        if len(runs) >= expected - 1:
            break

    kept = sorted(sorted(runs, key=separations, reverse=True)[: expected - 1])
    return [0, *(run[1] for run in kept), width]


def columns(slices: list[list[str]], expected: int) -> list[list[str]]:
    """Split each page of a table on its own gutters, then line the columns up.

    A table that runs over a page break is redrawn on the next page, and rarely at
    exactly the same character offsets — EMC shifts by one, and a continuation whose
    first column is empty starts at what looks like position zero. So each page is
    split on its own, and its columns are then matched to the columns of the page that
    showed the most of them, by which of those they overlap the most.
    """
    split = [(gutters(lines, expected), lines) for lines in slices if lines]
    if not split:
        return []
    reference, _ = max(split, key=lambda pair: len(pair[0]))
    columns_of = list(pairwise(reference))
    cells: list[list[str]] = [[] for _ in columns_of]

    def nearest(span: tuple[int, int]) -> int:
        """Which reference column a page's column belongs to: the one it covers most."""
        left, right = span
        overlaps = [min(right, end) - max(left, start) for start, end in columns_of]
        return overlaps.index(max(overlaps))

    for bounds, lines in split:
        width = max(len(line) for line in lines)
        padded = [line.ljust(width) for line in lines]
        for left, right in pairwise(bounds):
            cell = [line[left:right] for line in padded]
            # A bullet at the very end of a cell belongs to the column after it: the
            # gutter falls a character late where a row opens with one.
            written = [entry.strip().rstrip(BULLET).strip() for entry in cell if entry.strip()]
            written = [entry for entry in written if entry]
            if not written:
                continue
            # Where the text sits, not where the slice was cut: a page that carries
            # only one column of the table gets cut at zero, and matching on that
            # would file its rows under the table's first column.
            starts = left + min(len(entry) - len(entry.lstrip()) for entry in cell if entry.strip())
            ends = left + max(len(entry.rstrip()) for entry in cell)
            cells[nearest((starts, ends))].extend(written)
    return cells


def _is_column_header(line: str, columns: tuple[str, ...]) -> bool:
    """Tell a piece of a column's header from a row of the table.

    A header the source centred over two lines arrives here in pieces, so a piece
    counts when it sits inside one of the column names — long enough that a row of
    the table cannot be mistaken for one.
    """
    return len(line) >= HEADER_FRAGMENT and any(
        line in column or column in line for column in columns
    )


class _OpenTable:
    """The table being read: what it will be titled, and the lines gathered so far.

    Both table readers walk pages line by line and close the table they were reading
    when the next heading turns up, so both need somewhere to put the lines in
    between. Mutable, unlike ``Item``, because that is what accumulating is.
    """

    def __init__(self, *, level: str, subject: str, title: str, page: int) -> None:
        self.level = level
        self.subject = subject
        self.title = title
        self.page = page
        self.intro: list[str] = []
        self.region: dict[int, list[str]] = {}

    def gather(self, page: int, raw: str, intro_prefixes: tuple[str, ...]) -> None:
        """Put one line where it belongs: above the table, or inside it.

        The line is kept exactly as ``pdftotext -layout`` printed it, indentation
        included, because that indentation is what tells the table's columns apart.

        A « Question : … » or « Mots-clés : … » line is printed full-width above the
        table and wraps onto the next line when it is long, so a line following one
        that has not closed its sentence continues it rather than opening a row.
        """
        line = raw.strip()
        if line.startswith(PAGE_FURNITURE):
            return
        if intro_prefixes and line.startswith(intro_prefixes):
            self.intro.append(line)
        elif self.intro and self.intro[-1][-1] not in SENTENCE_CLOSE:
            self.intro[-1] = f"{self.intro[-1]} {line}"
        else:
            self.region.setdefault(page, []).append(raw)

    def describe(self, columns_named: tuple[str, ...]) -> str:
        """Rebuild the table as text, column by column, under the names it prints.

        The lines are kept page by page, because a table redrawn after a page break
        rarely lands on the same character offsets; ``columns`` splits each page and
        lines the results up.
        """
        parts = list(self.intro)
        table = columns(list(self.region.values()), len(columns_named))
        for name, cell in zip(columns_named, table, strict=False):
            if cell:
                parts.append(f"{name}\n" + "\n".join(join_wrapped(cell)))
        return "\n\n".join(part for part in parts if part)


def read_histoire_geographie() -> list[Item]:
    """Read the thèmes of the histoire-géographie programme.

    A thème is the item: the source names it, gives it its question, its table of
    objectives, attendus and repères, and its mots-clés, and plans the year in thèmes.
    Histoire and géographie share these pages, and the matière switches on its heading.
    """
    programme = HISTOIRE_GEOGRAPHIE
    intro_prefixes = ("Question :", "Mots-clés :", "Mots clés :", "Fil directeur")
    subject = programme.subject
    level: str | None = None
    items: list[Item] = []
    table: _OpenTable | None = None

    def close(open_table: _OpenTable | None) -> None:
        """Turn the thème that was being read into an item."""
        description = open_table.describe(programme.columns) if open_table else ""
        if open_table and description:
            items.append(
                Item(
                    level=open_table.level,
                    subject=open_table.subject,
                    domain=None,
                    domain_label=None,
                    title=open_table.title,
                    description=description,
                    page=open_table.page,
                )
            )

    for page in range(programme.first_page, programme.last_page + 1):
        for raw in page_text(page).splitlines():
            line = raw.strip()
            marker = next((key for key in LEVEL_MARKERS if line.startswith(key)), None)
            ends_the_theme = (
                line in {"Histoire", "Géographie"}
                or marker
                or line in OTHER_LEVEL_MARKERS
                or line.startswith("Sixième")
                or (line.startswith("Thème ") and level is not None)
            )
            if ends_the_theme:
                close(table)
                table = None
            if line in {"Histoire", "Géographie"}:
                subject = "histoire" if line == "Histoire" else "geographie"
            elif marker:
                level = LEVEL_MARKERS[marker]
            elif line in OTHER_LEVEL_MARKERS or line.startswith("Sixième"):
                level = None
            elif line.startswith("Thème ") and level is not None:
                table = _OpenTable(level=level, subject=subject, title=line, page=page)
            elif table and line and not _is_column_header(line, programme.columns):
                table.gather(page, raw, intro_prefixes)
    close(table)
    return items


def read_sectioned_tables(programme: TableProgramme) -> list[Item]:
    """Read a programme cut into named sections, each holding one table."""
    level = programme.level
    levels = dict(programme.levels)
    headers = {part for column in programme.columns for part in column.split(" ")} | set(
        programme.columns
    )
    items: list[Item] = []
    table: _OpenTable | None = None

    def close(open_table: _OpenTable | None) -> None:
        """Turn the section that was being read into an item."""
        description = open_table.describe(programme.columns) if open_table else ""
        if not (open_table and description):
            return
        from_section = programme.domain_from_section
        items.append(
            Item(
                level=open_table.level,
                subject=programme.subject,
                domain=slug(open_table.title) if from_section else programme.domain,
                domain_label=open_table.title if from_section else programme.domain_label,
                title=open_table.title,
                description=description,
                page=open_table.page,
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
            heading, wrapped = _match_section(lines, index, programme.sections)
            if line in levels or any(line.startswith(stop) for stop in programme.stops):
                close(table)
                table = None
                level = levels.get(line, "")
            elif heading and level:
                close(table)
                skip_next = wrapped
                table = _OpenTable(level=level, subject=programme.subject, title=heading, page=page)
            elif (
                table
                and line
                and not (line in headers or _is_column_header(line, programme.columns))
            ):
                table.gather(page, raw, programme.intro_prefixes)
    close(table)
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

    Pages 90-107 of the source are images with no text layer, so they were read in
    vision and copied into ``scripts/curriculum_sciences.json`` rather than parsed.
    The items themselves start on p. 93, after the programme's principes.
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
            "",
            "needs_review marque les items dont le tableau source n'a pas pu être découpé",
            "proprement en colonnes : le texte est bien celui du PDF, mais deux colonnes se",
            "partagent une ligne au lieu de se suivre. À relire contre la page indiquée.",
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
            | ({"needs_review": True} if item.needs_review else {})
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
