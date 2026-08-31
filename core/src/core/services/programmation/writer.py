"""Read the year out of the database, plan it, and write the séances back.

The planner knows nothing about the database (see ``inputs``); everything that does is
here. Two rules govern the writing and both come from §10: a re-generation upserts on
the natural key rather than inserting a second year, and it never touches a jour de
classe that is in the past or that already has a cahier journal.
"""

import uuid
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date, time
from typing import Any

from sqlalchemy import Table, delete, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from core.models.calendar import Period, SchoolDay, Week
from core.models.curriculum import Domain, ProgramItem, Subject
from core.models.journal import JournalEntry
from core.models.level import Level
from core.models.planning import PlannedSession, PlannedSessionProgramItem
from core.models.sequence import Sequence as SequenceModel
from core.models.sequence import SequenceSession
from core.models.timetable import TimetableSlot
from core.models.weekday import FRENCH_WEEKDAYS, Weekday
from core.services.programmation.inputs import (
    Alternation,
    AlternationSlot,
    PlanInput,
    PlannedDay,
    PlannedWeek,
    program_item_key,
    sequence_key,
    sequence_session_key,
    slot_key,
)
from core.services.programmation.inputs import ProgramItem as PlanProgramItem
from core.services.programmation.inputs import Sequence as PlanSequence
from core.services.programmation.inputs import SequenceStep as PlanSequenceStep
from core.services.programmation.inputs import Slot as PlanSlot
from core.services.programmation.planner import SessionDraft, plan_year

ALTERNATION_PREFIX = "alternance."
# One statement per batch rather than one per séance: there are over 1700 of them and
# §8 gives the whole generation under a minute.
BATCH = 500


@dataclass(frozen=True, slots=True)
class GenerationReport:
    """What one run of the generation did, and everything it could not do."""

    periods: tuple[str, ...]
    sessions_planned: int
    sessions_written: int
    days_written: int
    days_untouched: tuple[date, ...]
    days_off: int
    program_links: int
    sequences_placed: dict[str, int]
    alternations: dict[str, int]
    problems: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        """Say whether the generation hit nothing it had to report."""
        return not self.problems


def _table(model: type[SQLModel]) -> Table:
    """Return the SQLAlchemy table behind a SQLModel table class."""
    return SQLModel.metadata.tables[str(model.__tablename__)]


def _batches(rows: Sequence[Any], size: int = BATCH) -> Iterator[Sequence[Any]]:
    """Cut a list of rows into statement-sized batches."""
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


async def load_plan_input(session: AsyncSession) -> PlanInput:
    """Read the year, the timetable, the méthodos and the programmes out of the database.

    The planner is given the same shape whether it is fed from here or from the seed
    files, which is what lets the placement rules be tested where there is no Postgres.
    """
    weeks_table, periods_table = _table(Week), _table(Period)
    rows = (
        await session.execute(
            select(
                weeks_table.c.id,
                weeks_table.c.number,
                weeks_table.c.number_in_period,
                periods_table.c.code,
            ).join(periods_table, periods_table.c.id == weeks_table.c.period_id)
        )
    ).all()
    weeks = tuple(
        PlannedWeek(number=row.number, period_code=row.code, number_in_period=row.number_in_period)
        for row in rows
    )
    numbers = {row.id: row.number for row in rows}
    days = tuple(
        PlannedDay(
            date=row.date,
            day_of_week=Weekday(row.day_of_week),
            week_number=numbers[row.week_id],
            is_off=row.is_off,
        )
        for row in (await session.execute(select(_table(SchoolDay)))).all()
    )

    subjects = {row.id: row.code for row in (await session.execute(select(_table(Subject)))).all()}
    domains = {row.id: row.code for row in (await session.execute(select(_table(Domain)))).all()}

    slots = tuple(
        PlanSlot(
            key=slot_key(Weekday(row.day_of_week), row.starts_at, Level(row.level)),
            day_of_week=Weekday(row.day_of_week),
            starts_at=row.starts_at,
            ends_at=row.ends_at,
            duration_minutes=row.duration_minutes,
            label=row.label,
            subject=subjects.get(row.subject_id),
            domain=domains.get(row.domain_id),
            level=Level(row.level),
            alternation_group=row.alternation_group,
        )
        for row in (await session.execute(select(_table(TimetableSlot)))).all()
    )

    steps: dict[uuid.UUID, list[PlanSequenceStep]] = {}
    sequence_rows = (await session.execute(select(_table(SequenceModel)))).all()
    named = {row.id: (row.method, row.number) for row in sequence_rows}
    for row in (await session.execute(select(_table(SequenceSession)))).all():
        method, number = named[row.sequence_id]
        steps.setdefault(row.sequence_id, []).append(
            PlanSequenceStep(
                key=sequence_session_key(method, number, row.number),
                number=row.number,
                title=row.title,
                content=row.content,
                materials=row.materials,
            )
        )
    sequences = tuple(
        PlanSequence(
            key=sequence_key(row.method, row.number),
            method=row.method,
            level=Level(row.level),
            number=row.number,
            title=row.title,
            objectives=row.objectives,
            period_code=row.period_code,
            subject=subjects.get(row.subject_id),
            domain=domains.get(row.domain_id),
            steps=tuple(sorted(steps.get(row.id, []), key=lambda step: step.number)),
        )
        for row in sequence_rows
    )

    items = _table(ProgramItem)
    program_items = tuple(
        PlanProgramItem(
            key=program_item_key(
                Level(row.level), subjects[row.subject_id], domains.get(row.domain_id), row.title
            ),
            level=Level(row.level),
            subject=subjects[row.subject_id],
            domain=domains.get(row.domain_id),
            title=row.title,
            description=row.description,
        )
        for row in (await session.execute(select(items).order_by(items.c.source_order))).all()
    )

    alternations = tuple(
        _alternation(row.key.removeprefix(ALTERNATION_PREFIX), row.value)
        for row in (await session.execute(text("SELECT key, value FROM app_settings"))).all()
        if row.key.startswith(ALTERNATION_PREFIX)
    )

    return PlanInput(
        weeks=tuple(sorted(weeks, key=lambda week: week.number)),
        days=tuple(sorted(days, key=lambda day: day.date)),
        slots=slots,
        sequences=sequences,
        program_items=program_items,
        alternations=alternations,
    )


def _alternation(group: str, value: dict[str, Any]) -> Alternation:
    """Read one alternance réglage out of the JSON ``app_settings`` stores it as."""
    return Alternation(
        group=group,
        mode=value.get("mode", ""),
        subjects=tuple(value.get("subjects", ())),
        slots=tuple(
            AlternationSlot(
                day_of_week=_weekday(slot["day"]),
                starts_at=time.fromisoformat(slot["starts_at"]),
                subject=slot["subject"],
            )
            for slot in value.get("slots", ())
        ),
    )


def _weekday(value: int | str) -> Weekday:
    """Read a day of the week, whether the réglage names it or numbers it."""
    if isinstance(value, str) and value in FRENCH_WEEKDAYS:
        return FRENCH_WEEKDAYS[value]
    return Weekday(int(value))


async def _untouchable_days(session: AsyncSession, reference: date) -> set[date]:
    """Find the jours de classe a re-generation must leave exactly as they are.

    §10: « Les cahiers journaux et les jours passés ne sont jamais écrasés ». No cahier
    journal exists yet, and the rule still lives here rather than waiting for Phase 6.
    """
    days = _table(SchoolDay)
    past = await session.execute(select(days.c.date).where(days.c.date < reference))
    written = await session.execute(
        select(days.c.date)
        .join(_table(JournalEntry), _table(JournalEntry).c.school_day_id == days.c.id)
        .distinct()
    )
    return {row.date for row in past.all()} | {row.date for row in written.all()}


@dataclass(frozen=True, slots=True)
class _Keys:
    """Resolves the natural keys a draft carries to the primary keys a row needs."""

    days: dict[date, uuid.UUID]
    slots: dict[str, uuid.UUID]
    sequences: dict[str, uuid.UUID]
    steps: dict[str, uuid.UUID]
    subjects: dict[str, uuid.UUID]
    domains: dict[tuple[uuid.UUID, str], uuid.UUID]
    items: dict[str, uuid.UUID]

    @classmethod
    async def load(cls, session: AsyncSession) -> "_Keys":
        """Read every table the drafts point at."""
        days = _table(SchoolDay)
        slots = _table(TimetableSlot)
        sequences = _table(SequenceModel)
        steps = _table(SequenceSession)
        subjects = _table(Subject)
        domains = _table(Domain)
        items = _table(ProgramItem)

        named = {
            row.id: (row.method, row.number)
            for row in (await session.execute(select(sequences))).all()
        }
        subject_codes = {
            row.id: row.code for row in (await session.execute(select(subjects))).all()
        }
        domain_codes = {row.id: row.code for row in (await session.execute(select(domains))).all()}

        return cls(
            days={row.date: row.id for row in (await session.execute(select(days))).all()},
            slots={
                slot_key(Weekday(row.day_of_week), row.starts_at, Level(row.level)): row.id
                for row in (await session.execute(select(slots))).all()
            },
            sequences={
                sequence_key(method, number): identifier
                for identifier, (method, number) in named.items()
            },
            steps={
                sequence_session_key(*named[row.sequence_id], row.number): row.id
                for row in (await session.execute(select(steps))).all()
            },
            subjects={code: identifier for identifier, code in subject_codes.items()},
            domains={
                (row.subject_id, row.code): row.id
                for row in (await session.execute(select(domains))).all()
            },
            items={
                program_item_key(
                    Level(row.level),
                    subject_codes[row.subject_id],
                    domain_codes.get(row.domain_id),
                    row.title,
                ): row.id
                for row in (await session.execute(select(items))).all()
            },
        )

    def domain(self, subject: str | None, domain: str | None) -> uuid.UUID | None:
        """Look up a domaine under its own matière, failing loudly on a dangling code."""
        if not (subject and domain):
            return None
        return self.domains[self.subjects[subject], domain]


def _row(draft: SessionDraft, keys: _Keys) -> dict[str, Any]:
    """Turn one draft into the row ``planned_sessions`` stores."""
    return {
        "school_day_id": keys.days[draft.date],
        "timetable_slot_id": keys.slots[draft.slot],
        "level": draft.level.value,
        "sequence_id": keys.sequences[draft.sequence] if draft.sequence else None,
        "sequence_session_id": keys.steps[draft.sequence_step] if draft.sequence_step else None,
        "subject_id": keys.subjects[draft.subject] if draft.subject else None,
        "domain_id": keys.domain(draft.subject, draft.domain),
        "title": draft.title,
        "objectives": draft.objectives,
        "content": draft.content,
        "materials": draft.materials,
        "position": draft.position,
    }


async def generate_year(
    session: AsyncSession,
    *,
    reference_date: date,
    periods: Sequence[str] | None = None,
) -> GenerationReport:
    """Generate the year's séances, or only those of the given périodes.

    Idempotent: every séance is upserted on ``(school_day_id, timetable_slot_id, level)``
    so a second run leaves the same rows. Writes are flushed, never committed — that is
    the caller's decision, as it is for the seeds.
    """
    plan_input = await load_plan_input(session)
    plan = plan_year(plan_input)

    period_of = {week.number: week.period_code for week in plan_input.weeks}
    week_of = {day.date: day.week_number for day in plan_input.days}
    untouchable = await _untouchable_days(session, reference_date)
    wanted = set(periods) if periods else None

    drafts = [
        draft
        for draft in plan.sessions
        if draft.date not in untouchable
        and (wanted is None or period_of[week_of[draft.date]] in wanted)
    ]

    keys = await _Keys.load(session)
    written = await _write(session, drafts, keys)

    skipped = sorted({draft.date for draft in plan.sessions if draft.date in untouchable})
    return GenerationReport(
        periods=tuple(sorted(wanted)) if wanted else tuple(sorted(set(period_of.values()))),
        sessions_planned=len(plan.sessions),
        sessions_written=len(drafts),
        days_written=len({draft.date for draft in drafts}),
        days_untouched=tuple(skipped),
        days_off=sum(1 for day in plan_input.days if day.is_off),
        program_links=written,
        sequences_placed=plan.sequences_placed,
        alternations=plan.alternations,
        problems=plan.problems,
    )


async def _write(session: AsyncSession, drafts: Sequence[SessionDraft], keys: _Keys) -> int:
    """Upsert the séances and replace the items de programme they link."""
    if not drafts:
        return 0

    table = _table(PlannedSession)
    identifiers: dict[tuple[uuid.UUID, uuid.UUID, str], uuid.UUID] = {}
    for batch in _batches([_row(draft, keys) for draft in drafts]):
        insertion = insert(table).values(list(batch))
        updatable = {
            column: insertion.excluded[column]
            for column in batch[0]
            if column not in ("school_day_id", "timetable_slot_id", "level")
        }
        statement = insertion.on_conflict_do_update(
            constraint="uq_planned_sessions_day_slot_level",
            set_={**updatable, "updated_at": text("now()")},
        ).returning(table.c.id, table.c.school_day_id, table.c.timetable_slot_id, table.c.level)
        for row in (await session.execute(statement)).all():
            identifiers[row.school_day_id, row.timetable_slot_id, row.level] = row.id

    links = _table(PlannedSessionProgramItem)
    session_ids = list(identifiers.values())
    for batch in _batches(session_ids, size=5000):
        await session.execute(delete(links).where(links.c.planned_session_id.in_(list(batch))))

    rows = [
        {
            "planned_session_id": identifiers[
                keys.days[draft.date], keys.slots[draft.slot], draft.level.value
            ],
            "program_item_id": keys.items[item],
        }
        for draft in drafts
        for item in draft.program_items
    ]
    for batch in _batches(rows, size=2000):
        await session.execute(insert(links).values(list(batch)).on_conflict_do_nothing())
    return len(rows)


async def generate(reference_date: date | None = None) -> GenerationReport:
    """Entry point for ``make generate``: plan the year and commit it."""
    from core.database import engine  # noqa: PLC0415

    async with AsyncSession(engine) as session:
        report = await generate_year(session, reference_date=reference_date or date.today())  # noqa: DTZ011
        await session.commit()
    return report
