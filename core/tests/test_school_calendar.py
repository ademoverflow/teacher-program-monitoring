"""The 2026-2027 school year expands to the calendar MASTER-PROMPT.md §4.2 describes.

Every expected figure here is quoted from §4.2 or from the arrêté it cites; none is
recomputed the way ``build_school_calendar`` computes it.
"""

from datetime import date, timedelta
from itertools import pairwise

from core.models.weekday import Weekday
from core.services.school_calendar import build_school_calendar
from core.services.seed_files import load_calendar_reference

REFERENCE = load_calendar_reference()
CALENDAR = build_school_calendar(REFERENCE)

WEEKS_PER_PERIOD = {"P1": 7, "P2": 7, "P3": 5, "P4": 6, "P5": 11}
TOTAL_WEEKS = 36
TOTAL_SCHOOL_DAYS = 143
TOTAL_DAYS_OFF = 4
TOTAL_TEACHING_DAYS = 139

DAYS_OFF = {
    date(2027, 3, 29): "Lundi de Pâques",
    date(2027, 5, 6): "Ascension",
    date(2027, 5, 7): "Pont de l'Ascension",
    date(2027, 5, 17): "Lundi de Pentecôte",
}


def test_the_year_has_thirty_six_weeks_of_class() -> None:
    """§4.2: « Total : 36 semaines de classe »."""
    assert len(CALENDAR.weeks) == TOTAL_WEEKS


def test_each_periode_has_the_expected_number_of_weeks() -> None:
    """§4.2: P1…P5 run 7, 7, 5, 6 and 11 weeks."""
    counts: dict[str, int] = {}
    for week in CALENDAR.weeks:
        counts[week.period_code] = counts.get(week.period_code, 0) + 1

    assert counts == WEEKS_PER_PERIOD


def test_weeks_are_numbered_from_one_to_thirty_six_without_a_hole() -> None:
    """Semaines carry a number global to the year (S1…S36)."""
    assert [week.number for week in CALENDAR.weeks] == list(range(1, TOTAL_WEEKS + 1))


def test_each_periode_numbers_its_weeks_from_one() -> None:
    """A semaine also carries its number within its période (P2-S3)."""
    for code, expected in WEEKS_PER_PERIOD.items():
        numbers = [w.number_in_period for w in CALENDAR.weeks if w.period_code == code]
        assert numbers == list(range(1, expected + 1))


def test_every_week_runs_monday_to_friday() -> None:
    """§5: a semaine carries its Monday and Friday dates."""
    for week in CALENDAR.weeks:
        assert week.starts_on.isoweekday() == Weekday.MONDAY
        assert week.ends_on.isoweekday() == Weekday.FRIDAY
        assert week.ends_on - week.starts_on == timedelta(days=4)


def test_the_year_starts_on_tuesday_the_first_of_september() -> None:
    """§4.2: « Rentrée élèves : mardi 01/09/2026 » — the Monday before is not a jour de classe."""
    first = CALENDAR.days[0]

    assert first.date == date(2026, 9, 1)
    assert first.date.isoweekday() == Weekday.TUESDAY
    assert first.week_number == 1
    assert CALENDAR.weeks[0].starts_on == date(2026, 8, 31)


def test_the_year_ends_on_friday_the_second_of_july() -> None:
    """§4.2: P5 runs to ven 02/07/2027."""
    assert CALENDAR.days[-1].date == date(2027, 7, 2)


def test_there_are_one_hundred_and_forty_three_school_days() -> None:
    """Four jours de classe in each of the 36 weeks, less the Monday before the first day."""
    assert len(CALENDAR.days) == TOTAL_SCHOOL_DAYS
    assert TOTAL_WEEKS * len(("lun", "mar", "jeu", "ven")) - 1 == TOTAL_SCHOOL_DAYS


def test_class_is_never_on_a_wednesday() -> None:
    """§2: « Lundi, mardi, jeudi, vendredi uniquement (pas de mercredi) »."""
    weekdays = {day.date.isoweekday() for day in CALENDAR.days}

    assert Weekday.WEDNESDAY not in weekdays
    assert weekdays == {1, 2, 4, 5}


def test_the_four_public_holidays_are_flagged_with_their_reason() -> None:
    """§4.2: Pâques 29/03, Ascension + pont 06-07/05, Pentecôte 17/05."""
    flagged = {day.date: day.off_reason for day in CALENDAR.days if day.is_off}

    assert flagged == DAYS_OFF


def test_one_hundred_and_thirty_nine_days_are_actually_taught() -> None:
    """§3 Phase 3: « les ~139 jours de classe »."""
    taught = [day for day in CALENDAR.days if not day.is_off]

    assert len(taught) == TOTAL_TEACHING_DAYS
    assert TOTAL_TEACHING_DAYS == TOTAL_SCHOOL_DAYS - TOTAL_DAYS_OFF


def test_every_school_day_falls_inside_its_periode() -> None:
    """A jour de classe never lands in the holidays."""
    bounds = {p.code: (p.starts_on, p.ends_on) for p in REFERENCE.periods}
    week_period = {w.number: w.period_code for w in CALENDAR.weeks}

    for day in CALENDAR.days:
        starts_on, ends_on = bounds[week_period[day.week_number]]
        assert starts_on <= day.date <= ends_on


def test_periodes_and_holidays_tile_the_year_without_a_gap() -> None:
    """Each période is followed immediately by its vacances, and vice versa."""
    spans = sorted(
        [(p.starts_on, p.ends_on, p.code) for p in REFERENCE.periods]
        + [(h.starts_on, h.ends_on, h.label) for h in REFERENCE.holidays if h.ends_on],
    )

    for (_, ends_on, label), (starts_on, _, following) in pairwise(spans):
        assert ends_on + timedelta(days=1) == starts_on, f"gap between {label} and {following}"

    summer = next(h for h in REFERENCE.holidays if h.ends_on is None)
    assert summer.starts_on == REFERENCE.school_year.ends_on + timedelta(days=1)
