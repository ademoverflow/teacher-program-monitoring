"""Load the versioned JSON seeds into the database, idempotently.

``make seed`` runs this. Every row is upserted on its natural key, so running it
twice leaves the database in exactly the state one run leaves it in: the seeds in
``core/seed`` are the versioned source of truth and the database can always be
rebuilt from them (``make down && make up && make seed``).

Rows are never deleted: the loader owns what the seeds describe and leaves anything
else — a séance, a cahier journal — alone.
"""

import uuid
from typing import Any

from sqlalchemy import Table, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from core.database import engine
from core.models.calendar import Period, SchoolDay, SchoolHoliday, SchoolYear, Week
from core.models.curriculum import Domain, ProgramItem, Subject
from core.models.level import Level
from core.models.sequence import Sequence, SequenceSession
from core.models.timetable import TimetableSlot
from core.services.school_calendar import build_school_calendar
from core.services.seed_files import (
    ProgramItemSeed,
    SequenceSeed,
    TimetableSlotSeed,
    load_calendar_reference,
    load_program_items,
    load_sequences,
    load_subjects,
    load_timetable,
)

Row = dict[str, Any]


def _table(model: type[SQLModel]) -> Table:
    """Return the SQLAlchemy table behind a SQLModel table class."""
    return SQLModel.metadata.tables[str(model.__tablename__)]


async def _upsert(
    session: AsyncSession,
    model: type[SQLModel],
    rows: list[Row],
    *,
    on: list[str] | None = None,
    constraint: str | None = None,
) -> int:
    """Insert ``rows``, updating the ones whose natural key is already there."""
    if not rows:
        return 0

    table = _table(model)
    statement = insert(table).values(list(rows))
    updatable = {
        column: statement.excluded[column] for column in rows[0] if column not in (on or ())
    }
    statement = statement.on_conflict_do_update(
        constraint=constraint,
        index_elements=None if constraint else list(on or ()),
        set_={**updatable, "updated_at": text("now()")},
    )
    await session.execute(statement)
    return len(rows)


async def _ids_by(session: AsyncSession, model: type[SQLModel], *key: str) -> dict[Any, Any]:
    """Map each row's natural key to its primary key.

    Pass every column of the natural key: a période's code or a semaine's number
    only identifies a row within its school year.
    """
    table = _table(model)
    columns = [table.c[name] for name in key]
    result = await session.execute(select(table.c.id, *columns))
    return {
        (values[0] if len(values) == 1 else tuple(values)): identifier
        for identifier, *values in result.all()
    }


async def seed_calendar(session: AsyncSession) -> dict[str, int]:
    """Seed the school year, its périodes, vacances, semaines and jours de classe."""
    reference = load_calendar_reference()
    year = reference.school_year
    counts: dict[str, int] = {}

    counts["school_years"] = await _upsert(
        session,
        SchoolYear,
        [
            {
                "label": year.label,
                "zone": year.zone,
                "starts_on": year.starts_on,
                "ends_on": year.ends_on,
            }
        ],
        on=["label"],
    )
    await session.flush()
    year_id = (await _ids_by(session, SchoolYear, "label"))[year.label]

    counts["periods"] = await _upsert(
        session,
        Period,
        [
            {
                "school_year_id": year_id,
                "code": period.code,
                "label": period.label,
                "starts_on": period.starts_on,
                "ends_on": period.ends_on,
            }
            for period in reference.periods
        ],
        constraint="uq_periods_year_code",
    )
    counts["school_holidays"] = await _upsert(
        session,
        SchoolHoliday,
        [
            {
                "school_year_id": year_id,
                "label": holiday.label,
                "starts_on": holiday.starts_on,
                "ends_on": holiday.ends_on,
            }
            for holiday in reference.holidays
        ],
        constraint="uq_school_holidays_year_label",
    )
    await session.flush()
    period_ids = await _ids_by(session, Period, "school_year_id", "code")

    calendar = build_school_calendar(reference)
    counts["weeks"] = await _upsert(
        session,
        Week,
        [
            {
                "school_year_id": year_id,
                "period_id": period_ids[year_id, week.period_code],
                "number": week.number,
                "number_in_period": week.number_in_period,
                "starts_on": week.starts_on,
                "ends_on": week.ends_on,
            }
            for week in calendar.weeks
        ],
        constraint="uq_weeks_year_number",
    )
    await session.flush()
    week_ids = await _ids_by(session, Week, "school_year_id", "number")

    counts["school_days"] = await _upsert(
        session,
        SchoolDay,
        [
            {
                "week_id": week_ids[year_id, day.week_number],
                "date": day.date,
                "day_of_week": day.date.isoweekday(),
                "is_off": day.is_off,
                "off_reason": day.off_reason,
            }
            for day in calendar.days
        ],
        on=["date"],
    )
    return counts


async def seed_subjects(session: AsyncSession) -> dict[str, int]:
    """Seed the matières and the domaines that belong to them."""
    subjects = load_subjects()
    counts = {
        "subjects": await _upsert(
            session,
            Subject,
            [
                {"code": subject.code, "label": subject.label, "color": subject.color}
                for subject in subjects
            ],
            on=["code"],
        )
    }
    await session.flush()
    subject_ids = await _ids_by(session, Subject, "code")

    counts["domains"] = await _upsert(
        session,
        Domain,
        [
            {
                "subject_id": subject_ids[subject.code],
                "code": domain.code,
                "label": domain.label,
                "level": domain.level.value,
            }
            for subject in subjects
            for domain in subject.domains
        ],
        constraint="uq_domains_subject_code_level",
    )
    return counts


async def seed_timetable(session: AsyncSession) -> dict[str, int]:
    """Seed the 44 créneaux of the weekly timetable template."""
    slots = load_timetable()
    subject_ids = await _ids_by(session, Subject, "code")
    domain_ids = await _ids_by(session, Domain, "subject_id", "code", "level")

    def subject_of(slot: TimetableSlotSeed) -> uuid.UUID | None:
        """Return the matière taught in ``slot``, if the créneau names one."""
        # Indexed, not ``.get``: a code the seed names but the database does not
        # have is a broken seed, and must not become a silent NULL.
        return subject_ids[slot.subject] if slot.subject else None

    def domain_of(slot: TimetableSlotSeed) -> uuid.UUID | None:
        """Return the domaine taught in ``slot``, resolved under its own matière."""
        if not (slot.subject and slot.domain):
            return None
        return domain_ids[subject_ids[slot.subject], slot.domain, Level.COMMUN.value]

    return {
        "timetable_slots": await _upsert(
            session,
            TimetableSlot,
            [
                {
                    "day_of_week": int(slot.day),
                    "starts_at": slot.starts_at,
                    "ends_at": slot.ends_at,
                    "duration_minutes": slot.duration_minutes,
                    "label": slot.label,
                    "subject_id": subject_of(slot),
                    "domain_id": domain_of(slot),
                    "level": slot.level.value,
                    "is_alternating": slot.alternation_group is not None,
                    "alternation_group": slot.alternation_group,
                }
                for slot in slots
            ],
            constraint="uq_timetable_slots_day_start_level",
        )
    }


async def seed_program_items(session: AsyncSession) -> dict[str, int]:
    """Seed the items of the official CM1/CM2 curriculum."""
    items = load_program_items()
    subject_ids = await _ids_by(session, Subject, "code")
    domain_ids = await _ids_by(session, Domain, "subject_id", "code", "level")

    def domain_of(item: ProgramItemSeed) -> uuid.UUID | None:
        """Resolve the domaine an item belongs to, under its own matière."""
        if not item.domain:
            return None
        # Indexed, not ``.get``: a domaine the seed names but the database does not
        # have is a broken seed, and must not become a silent NULL.
        return domain_ids[subject_ids[item.subject], item.domain, Level.COMMUN.value]

    return {
        "program_items": await _upsert(
            session,
            ProgramItem,
            [
                {
                    "level": item.level.value,
                    "subject_id": subject_ids[item.subject],
                    "domain_id": domain_of(item),
                    "title": item.title,
                    "description": item.description,
                    "source_file": item.source_file,
                    "source_page": item.source_page,
                    "needs_review": item.needs_review,
                }
                for item in items
            ],
            constraint="uq_program_items_level_subject_domain_title",
        )
    }


async def seed_sequences(session: AsyncSession) -> dict[str, int]:
    """Seed the séquences of the méthodos and the séances they lay out."""
    sequences = load_sequences()
    subject_ids = await _ids_by(session, Subject, "code")
    domain_ids = await _ids_by(session, Domain, "subject_id", "code", "level")

    def domain_of(sequence: SequenceSeed) -> uuid.UUID | None:
        """Resolve the domaine a séquence belongs to, when the méthodo names one."""
        if not (sequence.subject and sequence.domain):
            return None
        return domain_ids[subject_ids[sequence.subject], sequence.domain, Level.COMMUN.value]

    counts = {
        "sequences": await _upsert(
            session,
            Sequence,
            [
                {
                    "method": sequence.method,
                    "level": sequence.level.value,
                    "number": sequence.number,
                    "title": sequence.title,
                    "objectives": sequence.objectives,
                    "period_code": sequence.period_code,
                    "subject_id": subject_ids[sequence.subject] if sequence.subject else None,
                    "domain_id": domain_of(sequence),
                    "needs_review": sequence.needs_review,
                }
                for sequence in sequences
            ],
            constraint="uq_sequences_method_number",
        )
    }
    await session.flush()
    sequence_ids = await _ids_by(session, Sequence, "method", "number")

    counts["sequence_sessions"] = await _upsert(
        session,
        SequenceSession,
        [
            {
                "sequence_id": sequence_ids[sequence.method, sequence.number],
                "number": item.number,
                "title": item.title,
                "content": item.content,
                "duration_minutes": item.duration_minutes,
                "materials": item.materials,
                "needs_review": item.needs_review,
            }
            for sequence in sequences
            for item in sequence.sessions
        ],
        constraint="uq_sequence_sessions_sequence_number",
    )
    return counts


async def seed_database(session: AsyncSession) -> dict[str, int]:
    """Load every structural seed. Safe to run as often as you like.

    Writes are flushed but not committed: committing is the caller's decision.
    """
    counts = await seed_subjects(session)
    counts |= await seed_calendar(session)
    await session.flush()
    counts |= await seed_timetable(session)
    counts |= await seed_program_items(session)
    counts |= await seed_sequences(session)
    await session.flush()
    return counts


async def seed() -> dict[str, int]:
    """Entry point for ``make seed``. Returns how many rows each table was given."""
    async with AsyncSession(engine) as session:
        counts = await seed_database(session)
        await session.commit()
    return counts
