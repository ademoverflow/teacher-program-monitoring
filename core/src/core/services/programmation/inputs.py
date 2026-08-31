"""What the planner needs to know, as plain frozen data.

The placement rules are where the bugs live, and CI has no Postgres, so nothing in
``core.services.programmation`` touches a session: the planner reads these dataclasses
and returns séance drafts. Two builders fill them — one from the versioned seeds
(``plan_input_from_seeds``, used by the tests) and one from the database
(``core.services.programmation.writer``) — and both spell the keys the same way, so a
draft can be written back without the planner ever knowing a UUID.
"""

from dataclasses import dataclass, field
from datetime import date, time

from core.models.level import Level
from core.models.weekday import Weekday
from core.services.school_calendar import build_school_calendar
from core.services.seed_files import (
    load_calendar_reference,
    load_program_items,
    load_sequences,
    load_settings,
    load_timetable,
)

# A créneau of 20 minutes or less is a rituel: it repeats every day rather than
# advancing through a programme (MASTER-PROMPT.md §4.1 prints them as the short cells,
# §4.3 calls calcul mental and Flash Maths rituals). See ADR-0015.
RITUAL_MINUTES = 20


def slot_key(day_of_week: Weekday, starts_at: time, level: Level) -> str:
    """Name a créneau the way ``uq_timetable_slots_day_start_level`` identifies it."""
    return f"{int(day_of_week)}-{starts_at:%H:%M}-{level.value}"


def sequence_key(method: str, number: int) -> str:
    """Name a séquence the way ``uq_sequences_method_number`` identifies it."""
    return f"{method}-{number}"


def sequence_session_key(method: str, number: int, session_number: int) -> str:
    """Name a séance de séquence by its séquence and its own number."""
    return f"{method}-{number}-{session_number}"


def program_item_key(level: Level, subject: str, domain: str | None, title: str) -> str:
    """Name an item de programme the way ADR-0005 identifies it."""
    return f"{level.value}|{subject}|{domain or ''}|{title}"


@dataclass(frozen=True, slots=True)
class PlannedWeek:
    """A semaine de classe and the période it belongs to."""

    number: int
    period_code: str
    number_in_period: int


@dataclass(frozen=True, slots=True)
class PlannedDay:
    """A jour de classe. A chômé one keeps its place in the week and gets no séance."""

    date: date
    day_of_week: Weekday
    week_number: int
    is_off: bool


@dataclass(frozen=True, slots=True)
class Slot:
    """One créneau of the weekly timetable template."""

    key: str
    day_of_week: Weekday
    starts_at: time
    ends_at: time
    duration_minutes: int
    label: str
    subject: str | None
    domain: str | None
    level: Level
    alternation_group: str | None

    @property
    def is_ritual(self) -> bool:
        """Say whether this is a short daily cell that repeats rather than progresses."""
        return self.duration_minutes <= RITUAL_MINUTES


@dataclass(frozen=True, slots=True)
class SequenceStep:
    """One séance of a séquence, as the méthodo lays it out."""

    key: str
    number: int
    title: str
    content: str | None
    materials: str | None


@dataclass(frozen=True, slots=True)
class Sequence:
    """A séquence of a méthodo, and the séances it details (littérature only, so far)."""

    key: str
    method: str
    level: Level
    number: int
    title: str
    objectives: str | None
    period_code: str | None
    subject: str | None
    domain: str | None
    steps: tuple[SequenceStep, ...] = ()


@dataclass(frozen=True, slots=True)
class ProgramItem:
    """One item of the official curriculum, reduced to what a séance links to."""

    key: str
    level: Level
    subject: str
    domain: str | None
    title: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AlternationSlot:
    """Which matière an alternating créneau teaches, when the choice is per créneau."""

    day_of_week: Weekday
    starts_at: time
    subject: str


@dataclass(frozen=True, slots=True)
class Alternation:
    """How one ``alternation_group`` resolves to a matière (ADR-0002, ADR-0013)."""

    group: str
    mode: str
    subjects: tuple[str, ...] = ()
    slots: tuple[AlternationSlot, ...] = ()


@dataclass(frozen=True, slots=True)
class PlanInput:
    """Everything the planner reads. Ordered, so the plan is reproducible."""

    weeks: tuple[PlannedWeek, ...]
    days: tuple[PlannedDay, ...]
    slots: tuple[Slot, ...]
    sequences: tuple[Sequence, ...]
    program_items: tuple[ProgramItem, ...]
    alternations: tuple[Alternation, ...] = ()

    _weeks_by_number: dict[int, PlannedWeek] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Index the semaines: every day and every créneau is placed through one."""
        object.__setattr__(self, "_weeks_by_number", {week.number: week for week in self.weeks})

    def week(self, number: int) -> PlannedWeek:
        """Return the semaine with that number."""
        return self._weeks_by_number[number]

    def taught_days(self) -> tuple[PlannedDay, ...]:
        """Return the jours de classe that are actually taught, in date order."""
        return tuple(sorted((day for day in self.days if not day.is_off), key=lambda d: d.date))

    def slots_of(self, day_of_week: Weekday) -> tuple[Slot, ...]:
        """Return the créneaux of one day of the week, in the order they run."""
        return tuple(
            sorted(
                (slot for slot in self.slots if slot.day_of_week == day_of_week),
                key=lambda slot: (slot.starts_at, slot.level.value),
            )
        )

    def sequences_of(self, method: str) -> tuple[Sequence, ...]:
        """Return the séquences of one méthodo, in number order."""
        return tuple(
            sorted((s for s in self.sequences if s.method == method), key=lambda s: s.number)
        )

    def items_of(self, subject: str, domain: str | None, level: Level) -> tuple[ProgramItem, ...]:
        """Return the items of a matière, narrowed to a domaine when the créneau names one.

        Order is the seed's, which is the order the programme prints them in — that is
        what makes spreading them over the year a progression rather than a shuffle.
        """
        return tuple(
            item
            for item in self.program_items
            if item.subject == subject
            and item.level == level
            and (domain is None or item.domain == domain)
        )

    def levels_with_items(self, subject: str, domain: str | None) -> tuple[Level, ...]:
        """Return the niveaux the programme of a matière is written for.

        Most matières are written per niveau; EPS, arts plastiques and éducation
        musicale are written once for the cycle and come out ``commun``.
        """
        found = {
            item.level
            for item in self.program_items
            if item.subject == subject and (domain is None or item.domain == domain)
        }
        return tuple(level for level in (Level.CM1, Level.CM2, Level.COMMUN) if level in found)

    def alternation(self, group: str) -> Alternation | None:
        """Return the réglage resolving one alternation_group, if the teacher has one."""
        return next((a for a in self.alternations if a.group == group), None)


def plan_input_from_seeds() -> PlanInput:
    """Build the planner's input from the versioned seeds in ``core/seed``.

    This is the same year ``make seed`` puts in the database, which is what lets the
    placement rules be tested where there is no Postgres.
    """
    calendar = build_school_calendar(load_calendar_reference())
    weeks = tuple(
        PlannedWeek(
            number=week.number,
            period_code=week.period_code,
            number_in_period=week.number_in_period,
        )
        for week in calendar.weeks
    )
    days = tuple(
        PlannedDay(
            date=day.date,
            day_of_week=Weekday(day.date.isoweekday()),
            week_number=day.week_number,
            is_off=day.is_off,
        )
        for day in calendar.days
    )
    slots = tuple(
        Slot(
            key=slot_key(slot.day, slot.starts_at, slot.level),
            day_of_week=slot.day,
            starts_at=slot.starts_at,
            ends_at=slot.ends_at,
            duration_minutes=slot.duration_minutes,
            label=slot.label,
            subject=slot.subject,
            domain=slot.domain,
            level=slot.level,
            alternation_group=slot.alternation_group,
        )
        for slot in load_timetable()
    )
    sequences = tuple(
        Sequence(
            key=sequence_key(sequence.method, sequence.number),
            method=sequence.method,
            level=sequence.level,
            number=sequence.number,
            title=sequence.title,
            objectives=sequence.objectives,
            period_code=sequence.period_code,
            subject=sequence.subject,
            domain=sequence.domain,
            steps=tuple(
                SequenceStep(
                    key=sequence_session_key(sequence.method, sequence.number, step.number),
                    number=step.number,
                    title=step.title,
                    content=step.content,
                    materials=step.materials,
                )
                for step in sequence.sessions
            ),
        )
        for sequence in load_sequences()
    )
    program_items = tuple(
        ProgramItem(
            key=program_item_key(item.level, item.subject, item.domain, item.title),
            level=item.level,
            subject=item.subject,
            domain=item.domain,
            title=item.title,
            description=item.description,
        )
        for item in load_program_items()
    )
    alternations = tuple(
        Alternation(
            group=setting.key.removeprefix("alternance."),
            mode=setting.value.mode,
            subjects=tuple(setting.value.subjects),
            slots=tuple(
                AlternationSlot(
                    day_of_week=slot.day,
                    starts_at=slot.starts_at,
                    subject=slot.subject,
                )
                for slot in setting.value.slots
            ),
        )
        for setting in load_settings()
        if setting.key.startswith("alternance.")
    )
    return PlanInput(
        weeks=weeks,
        days=days,
        slots=slots,
        sequences=sequences,
        program_items=program_items,
        alternations=alternations,
    )


__all__ = [
    "Alternation",
    "AlternationSlot",
    "PlanInput",
    "PlannedDay",
    "PlannedWeek",
    "ProgramItem",
    "Sequence",
    "SequenceStep",
    "Slot",
    "plan_input_from_seeds",
    "program_item_key",
    "sequence_key",
    "sequence_session_key",
    "slot_key",
]
