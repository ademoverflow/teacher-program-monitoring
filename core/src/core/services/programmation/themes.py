"""Read out of a thème which périodes it is meant to occupy.

Histoire and géographie have no domaine: their programme is cut into thèmes, and a
thème names its own place in the year — « (deuxième et troisième périodes) », « (1 ou 2
périodes au choix) ». No other matière's programme does that, so this is the only place
the generator is told where something goes rather than deciding (ADR-0016).
"""

import re
import unicodedata
from dataclasses import dataclass

from core.services.programmation.inputs import ProgramItem

PERIOD_CODES = ("P1", "P2", "P3", "P4", "P5")

_ORDINALS = {
    "premiere": "P1",
    "deuxieme": "P2",
    "troisieme": "P3",
    "quatrieme": "P4",
    "cinquieme": "P5",
}
# The mention always sits in brackets, and always says « période ».
_BRACKETED = re.compile(r"\(([^()]*p[eé]riode[^()]*)\)", re.IGNORECASE)
_COUNT = re.compile(r"(\d+)\s*(?:ou\s*(\d+))?\s*p[eé]riode", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class ThemePeriods:
    """What a thème says about its place in the year.

    Either it names its périodes (``codes``), or it only says how many it wants
    (``minimum``/``maximum``) and the generator picks which.
    """

    codes: tuple[str, ...] = ()
    minimum: int = 0
    maximum: int = 0

    @property
    def names_its_periods(self) -> bool:
        """Say whether the source named its périodes, rather than only how many."""
        return bool(self.codes)


def _fold(text: str) -> str:
    """Strip accents so « première » and « premiere » read the same."""
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(char) != "Mn"
    )


def _read(text: str) -> ThemePeriods | None:
    """Read the bracketed mention of périodes out of one piece of text."""
    for match in _BRACKETED.finditer(text):
        inside = match.group(1)
        folded = _fold(inside)
        named = [code for word, code in _ORDINALS.items() if re.search(rf"\b{word}\b", folded)]
        if named:
            return ThemePeriods(codes=tuple(sorted(set(named))))
        counted = _COUNT.search(inside)
        if counted:
            low = int(counted.group(1))
            high = int(counted.group(2) or counted.group(1))
            return ThemePeriods(minimum=low, maximum=high)
    return None


def periods_of(theme: ProgramItem) -> ThemePeriods | None:
    """Read what the thème says about its périodes, from its intitulé or its description.

    The intitulé is read first. One thème — « Vers une France républicaine » at CM2 —
    prints its période inside the block instead of in the heading, which is why the
    description is read at all; it is only read when the heading says nothing, so a
    « période napoléonienne » in a body of text cannot be mistaken for a placement.
    """
    return _read(theme.title) or _read(theme.description or "")


def assign_periods(themes: tuple[ProgramItem, ...]) -> dict[str, tuple[str, ...]]:
    """Give every thème of one matière and one niveau the périodes it will occupy.

    A thème that names its périodes gets exactly those. The others — the géographie
    thèmes, which only say « 1 période » or « 1 ou 2 périodes au choix » — are walked
    through P1…P5 in the order the programme prints them, each taking its minimum
    first; whatever périodes are left over are handed back to the thèmes that allow
    more, again in order. That last step is ours: the source leaves the choice open.
    """
    read = {theme.key: periods_of(theme) or ThemePeriods(minimum=1, maximum=1) for theme in themes}
    assigned: dict[str, tuple[str, ...]] = {
        theme.key: read[theme.key].codes for theme in themes if read[theme.key].names_its_periods
    }

    open_themes = [theme for theme in themes if theme.key not in assigned]
    if not open_themes:
        return assigned

    lengths = {theme.key: max(read[theme.key].minimum, 1) for theme in open_themes}
    spare = len(PERIOD_CODES) - sum(lengths.values())
    for theme in open_themes:
        found = read[theme.key]
        taken = min(max(found.maximum - found.minimum, 0), max(spare, 0))
        lengths[theme.key] += taken
        spare -= taken

    cursor = 0
    for theme in open_themes:
        length = min(lengths[theme.key], len(PERIOD_CODES) - cursor)
        assigned[theme.key] = PERIOD_CODES[cursor : cursor + length]
        cursor += length
    return assigned
