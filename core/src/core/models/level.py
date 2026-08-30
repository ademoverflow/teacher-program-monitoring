"""The niveau a piece of teaching is aimed at."""

from enum import StrEnum


class Level(StrEnum):
    """CM1, CM2, or ``commun`` when both levels are taught together.

    The values are the domain's own words (MASTER-PROMPT.md §2) and are what is
    stored in the database.
    """

    CM1 = "CM1"
    CM2 = "CM2"
    COMMUN = "commun"
