"""Typed readers for the versioned JSON seeds in ``core/seed``.

The seed files are the versioned source of truth for everything the database is
rebuilt from (``make seed``). Reading them through these models means a malformed
or drifted seed fails loudly at load time rather than half-populating a table.
"""

import json
from datetime import date, time
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict

from core.models.level import Level
from core.models.weekday import FRENCH_WEEKDAYS, Weekday

# core/src/core/services/seed_files.py -> core/
SEED_DIR = Path(__file__).resolve().parents[3] / "seed"


class SeedModel(BaseModel):
    """Base for every seed record: immutable, and tolerant of ``$comment`` keys."""

    model_config = ConfigDict(frozen=True, extra="ignore")


class SchoolYearSeed(SeedModel):
    """The school year the whole database is scoped to."""

    label: str
    zone: str
    starts_on: date
    ends_on: date


class PeriodSeed(SeedModel):
    """One of the five périodes, with its first and last day of class."""

    code: str
    label: str
    starts_on: date
    ends_on: date


class HolidaySeed(SeedModel):
    """A stretch of school holidays. ``ends_on`` is open for the summer."""

    label: str
    starts_on: date
    ends_on: date | None


class DayOffSeed(SeedModel):
    """A public holiday or bridge day falling on what would be a jour de classe."""

    date: date
    reason: str


class CalendarReference(SeedModel):
    """The reference calendar facts of MASTER-PROMPT.md §4.2.

    Weeks and school days are *derived* from these facts (see
    ``core.services.school_calendar``), never listed here.
    """

    school_year: SchoolYearSeed
    periods: list[PeriodSeed]
    holidays: list[HolidaySeed]
    days_off: list[DayOffSeed]


def _weekday(value: object) -> object:
    """Accept the French day name the timetable seed is written with."""
    if isinstance(value, str) and value in FRENCH_WEEKDAYS:
        return FRENCH_WEEKDAYS[value]
    return value


FrenchWeekday = Annotated[Weekday, BeforeValidator(_weekday)]


class DomainSeed(SeedModel):
    """A domaine: a subdivision of a matière as the official curriculum cuts it up."""

    code: str
    label: str
    level: Level = Level.COMMUN


class SubjectSeed(SeedModel):
    """A matière and the domaines that belong to it."""

    code: str
    label: str
    color: str
    domains: list[DomainSeed] = []


class TimetableSlotSeed(SeedModel):
    """One créneau of the weekly timetable template (MASTER-PROMPT.md §4.1)."""

    day: FrenchWeekday
    starts_at: time
    ends_at: time
    duration_minutes: int
    label: str
    subject: str | None = None
    domain: str | None = None
    level: Level = Level.COMMUN
    alternation_group: str | None = None


def _read(name: str) -> Any:  # noqa: ANN401
    """Parse one JSON seed file by name."""
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


@lru_cache
def load_calendar_reference() -> CalendarReference:
    """Read ``core/seed/calendar.json``."""
    return CalendarReference.model_validate(_read("calendar.json"))


@lru_cache
def load_subjects() -> tuple[SubjectSeed, ...]:
    """Read ``core/seed/subjects.json``."""
    return tuple(SubjectSeed.model_validate(item) for item in _read("subjects.json")["subjects"])


@lru_cache
def load_timetable() -> tuple[TimetableSlotSeed, ...]:
    """Read ``core/seed/timetable.json``."""
    return tuple(
        TimetableSlotSeed.model_validate(item) for item in _read("timetable.json")["slots"]
    )
