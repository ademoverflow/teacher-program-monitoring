"""The seeded timetable template is the one printed in docs/edt.pdf (MASTER-PROMPT.md §4.1).

The EDT is immutable (§10): these assertions are the guardrail against it drifting.
"""

from collections import Counter
from datetime import time
from itertools import pairwise

from core.models.level import Level
from core.models.weekday import Weekday
from core.services.seed_files import load_timetable

SLOTS = load_timetable()

TOTAL_SLOTS = 44
SLOTS_PER_DAY = {Weekday.MONDAY: 10, Weekday.TUESDAY: 12, Weekday.THURSDAY: 12, Weekday.FRIDAY: 10}
ALTERNATION_GROUPS = {"histoire-geographie": 4, "arts-plastiques-education-musicale": 2}
SPLIT_SLOTS = 8
FRIDAY_CALCUL_MENTAL_MINUTES = 15


MINUTES_PER_HOUR = 60


def _span_minutes(starts_at: time, ends_at: time) -> int:
    """Minutes between two times of the same day."""
    return (ends_at.hour - starts_at.hour) * MINUTES_PER_HOUR + ends_at.minute - starts_at.minute


def test_the_template_has_forty_four_creneaux() -> None:
    """10 teaching slots on each of the 4 days, plus one extra row per split cell."""
    assert len(SLOTS) == TOTAL_SLOTS
    assert TOTAL_SLOTS == 10 * 4 + 4


def test_each_day_carries_its_creneaux() -> None:
    """Tuesday and Thursday carry two extra rows each: they hold the split cells."""
    assert Counter(slot.day for slot in SLOTS) == SLOTS_PER_DAY


def test_the_template_never_schedules_a_wednesday() -> None:
    """§2: « Lundi, mardi, jeudi, vendredi uniquement (pas de mercredi) »."""
    assert Weekday.WEDNESDAY not in {slot.day for slot in SLOTS}


def test_creneaux_are_unique_per_day_start_and_niveau() -> None:
    """(day, start, niveau) is the natural key ``make seed`` upserts on."""
    keys = [(slot.day, slot.starts_at, slot.level) for slot in SLOTS]

    assert len(set(keys)) == len(keys)


def test_split_cells_give_one_creneau_per_niveau() -> None:
    """§4.1: mardi 11h30, mardi 14h15, jeudi 11h30 and jeudi 15h00 are split CM1/CM2."""
    split = [slot for slot in SLOTS if slot.level is not Level.COMMUN]

    assert len(split) == SPLIT_SLOTS
    assert Counter(slot.level for slot in split) == {Level.CM1: 4, Level.CM2: 4}
    assert {(slot.day, slot.starts_at) for slot in split} == {
        (Weekday.TUESDAY, time(11, 30)),
        (Weekday.TUESDAY, time(14, 15)),
        (Weekday.THURSDAY, time(11, 30)),
        (Weekday.THURSDAY, time(15, 0)),
    }


def test_six_creneaux_alternate_between_two_matieres() -> None:
    """§4.1: 4 « Histoire ou Géographie » (2 per niveau), 2 « Arts plastiques / Éduc. musicale »."""
    alternating = [slot for slot in SLOTS if slot.alternation_group]

    assert Counter(slot.alternation_group for slot in alternating) == ALTERNATION_GROUPS
    assert len(alternating) == sum(ALTERNATION_GROUPS.values())


def test_alternating_creneaux_name_no_matiere() -> None:
    """ADR-0002: the matière is resolved when the year is generated, not by the template."""
    for slot in SLOTS:
        if slot.alternation_group:
            assert slot.subject is None, slot.label


def test_history_and_geography_alternate_twice_a_week_for_each_niveau() -> None:
    """§4.1: « 2 créneaux/semaine/niveau »."""
    levels = Counter(
        slot.level for slot in SLOTS if slot.alternation_group == "histoire-geographie"
    )

    assert levels == {Level.CM1: 2, Level.CM2: 2}


def test_a_creneau_lasts_as_long_as_its_place_in_the_grid() -> None:
    """Everywhere except Friday's calcul mental — see ADR-0003."""
    mismatched = [
        slot
        for slot in SLOTS
        if _span_minutes(slot.starts_at, slot.ends_at) != slot.duration_minutes
    ]

    assert len(mismatched) == 1
    assert mismatched[0].day is Weekday.FRIDAY
    assert mismatched[0].starts_at == time(9, 55)
    assert mismatched[0].duration_minutes == FRIDAY_CALCUL_MENTAL_MINUTES


def test_friday_runs_two_thirty_minute_creneaux_up_to_the_lunch_break() -> None:
    """ADR-0003: the two 30' cells span 11h30-12h30, not the 45'/15' grid of the other days."""
    late_morning = sorted(
        (
            slot
            for slot in SLOTS
            if slot.day is Weekday.FRIDAY and time(11, 30) <= slot.starts_at < time(12, 30)
        ),
        key=lambda slot: slot.starts_at,
    )

    assert [(s.starts_at, s.ends_at, s.duration_minutes) for s in late_morning] == [
        (time(11, 30), time(12, 0), 30),
        (time(12, 0), time(12, 30), 30),
    ]


def test_no_two_creneaux_overlap_for_the_same_niveau() -> None:
    """A pupil is never expected in two places at once."""
    for day in SLOTS_PER_DAY:
        for level in (Level.CM1, Level.CM2):
            same_class = sorted(
                (s for s in SLOTS if s.day is day and s.level in (level, Level.COMMUN)),
                key=lambda slot: slot.starts_at,
            )
            for earlier, later in pairwise(same_class):
                assert earlier.ends_at <= later.starts_at, f"{day} {level}: {earlier.label}"
