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
from core.models.app_setting import AppSetting
from core.models.calendar import Period, SchoolDay, SchoolHoliday, SchoolYear, Week
from core.models.curriculum import Domain, ProgramItem, Subject
from core.models.level import Level
from core.models.sequence import Sequence, SequenceSession
from core.models.timetable import TimetableSlot
from core.services.school_calendar import build_school_calendar
from core.services.seed_files import (
    load_calendar_reference,
    load_program_items,
    load_sequences,
    load_settings,
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


async def _insert_missing(session: AsyncSession, model: type[SQLModel], rows: list[Row]) -> int:
    """Insert ``rows`` only where the natural key is free, leaving what is there alone.

    Used for the rows the seed *starts* the teacher off with rather than owns: the
    alternances of §4.1 are explicitly « à paramétrer, modifiable dans l'app », so a
    later ``make seed`` must not undo a choice she has changed (ADR-0013).
    """
    if not rows:
        return 0

    statement = insert(_table(model)).values(list(rows)).on_conflict_do_nothing()
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


class _Curriculum:
    """Resolves the matière and domaine codes a seed names to their primary keys.

    Every seed that hangs something off the curriculum — a créneau, an item de
    programme, a séquence — needs the same two lookups, and needs them to fail loudly:
    a code the seed names but the database does not have is a broken seed, and must
    not land as a silent NULL. Both lookups are therefore indexed, never ``.get``.
    """

    def __init__(self, subjects: dict[Any, Any], domains: dict[Any, Any]) -> None:
        self._subjects = subjects
        self._domains = domains

    @classmethod
    async def load(cls, session: AsyncSession) -> "_Curriculum":
        """Read every matière and domaine already in the database."""
        return cls(
            await _ids_by(session, Subject, "code"),
            await _ids_by(session, Domain, "subject_id", "code", "level"),
        )

    def subject(self, code: str | None) -> uuid.UUID | None:
        """Look up the matière a seed names, if it names one."""
        return self._subjects[code] if code else None

    def domain(self, subject: str | None, code: str | None) -> uuid.UUID | None:
        """Look up the domaine a seed names, under its own matière."""
        if not (subject and code):
            return None
        return self._domains[self._subjects[subject], code, Level.COMMUN.value]


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


async def seed_settings(session: AsyncSession) -> dict[str, int]:
    """Seed the réglages the teacher starts from — the two alternances of §4.1."""
    return {
        "app_settings": await _insert_missing(
            session,
            AppSetting,
            [
                {
                    "key": setting.key,
                    "label": setting.label,
                    "value": setting.value.model_dump(mode="json", exclude_none=True),
                }
                for setting in load_settings()
            ],
        )
    }


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
    curriculum = await _Curriculum.load(session)

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
                    "subject_id": curriculum.subject(slot.subject),
                    "domain_id": curriculum.domain(slot.subject, slot.domain),
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
    curriculum = await _Curriculum.load(session)

    return {
        "program_items": await _upsert(
            session,
            ProgramItem,
            [
                {
                    "level": item.level.value,
                    "subject_id": curriculum.subject(item.subject),
                    "domain_id": curriculum.domain(item.subject, item.domain),
                    "title": item.title,
                    "description": item.description,
                    "source_file": item.source_file,
                    "source_page": item.source_page,
                    "source_order": order,
                    "needs_review": item.needs_review,
                }
                for order, item in enumerate(items)
            ],
            constraint="uq_program_items_level_subject_domain_title",
        )
    }


async def seed_sequences(session: AsyncSession) -> dict[str, int]:
    """Seed the séquences of the méthodos and the séances they lay out."""
    sequences = load_sequences()
    curriculum = await _Curriculum.load(session)

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
                    "subject_id": curriculum.subject(sequence.subject),
                    "domain_id": curriculum.domain(sequence.subject, sequence.domain),
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
                "number": sequence_session.number,
                "title": sequence_session.title,
                "content": sequence_session.content,
                "duration_minutes": sequence_session.duration_minutes,
                "materials": sequence_session.materials,
                "needs_review": sequence_session.needs_review,
            }
            for sequence in sequences
            for sequence_session in sequence.sessions
        ],
        constraint="uq_sequence_sessions_sequence_number",
    )
    return counts


async def seed_database(session: AsyncSession) -> dict[str, int]:
    """Load every structural seed. Safe to run as often as you like.

    Writes are flushed but not committed: committing is the caller's decision.
    """
    counts = await seed_subjects(session)
    counts |= await seed_settings(session)
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
