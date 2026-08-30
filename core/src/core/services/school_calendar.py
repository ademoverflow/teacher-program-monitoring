"""Expand the reference calendar facts into the year's weeks and jours de classe.

MASTER-PROMPT.md §4.2 gives the périodes' bounds and the days off; everything else
about the year -- which weeks exist, which days are taught -- follows from them by
calculation. §4.2 is explicit that these counts must be *verified* by the code
rather than assumed, so nothing here is hand-enumerated.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from core.models.weekday import Weekday
from core.services.seed_files import CalendarReference

DAYS_IN_A_WEEK = 7

# Class is on Monday, Tuesday, Thursday and Friday -- never on a Wednesday.
CLASS_WEEKDAYS: tuple[Weekday, ...] = (
    Weekday.MONDAY,
    Weekday.TUESDAY,
    Weekday.THURSDAY,
    Weekday.FRIDAY,
)


@dataclass(frozen=True, slots=True)
class CalendarWeek:
    """A semaine de classe: Monday to Friday, numbered globally and within its période."""

    number: int
    period_code: str
    number_in_period: int
    starts_on: date
    ends_on: date


@dataclass(frozen=True, slots=True)
class CalendarDay:
    """A jour de classe. ``is_off`` marks the ones lost to a public holiday or a bridge."""

    date: date
    week_number: int
    is_off: bool
    off_reason: str | None


@dataclass(frozen=True, slots=True)
class SchoolCalendar:
    """The year's skeleton: its weeks and its jours de classe."""

    weeks: tuple[CalendarWeek, ...]
    days: tuple[CalendarDay, ...]


def monday_of(day: date) -> date:
    """Return the Monday of the week ``day`` falls in."""
    return day - timedelta(days=day.isoweekday() - 1)


def build_school_calendar(reference: CalendarReference) -> SchoolCalendar:
    """Derive every semaine and every jour de classe of the year.

    A week belongs to a période as soon as its Monday-to-Friday span overlaps that
    période, so the year's first week counts even though class only starts on its
    Tuesday. A day is a jour de classe when it is a Monday, Tuesday, Thursday or
    Friday *inside* a période's bounds -- which is why the Monday before the pupils'
    first day gets no row at all, while a public holiday does (see ADR-0001).
    """
    weeks: list[CalendarWeek] = []
    days: list[CalendarDay] = []
    reasons = {day_off.date: day_off.reason for day_off in reference.days_off}

    for period in reference.periods:
        monday = monday_of(period.starts_on)
        number_in_period = 0

        while monday <= period.ends_on:
            number_in_period += 1
            week = CalendarWeek(
                number=len(weeks) + 1,
                period_code=period.code,
                number_in_period=number_in_period,
                starts_on=monday,
                ends_on=monday + timedelta(days=4),
            )
            weeks.append(week)

            for weekday in CLASS_WEEKDAYS:
                day = monday + timedelta(days=weekday - 1)
                if not (period.starts_on <= day <= period.ends_on):
                    continue
                days.append(
                    CalendarDay(
                        date=day,
                        week_number=week.number,
                        is_off=day in reasons,
                        off_reason=reasons.get(day),
                    )
                )

            monday += timedelta(days=DAYS_IN_A_WEEK)

    return SchoolCalendar(weeks=tuple(weeks), days=tuple(days))
