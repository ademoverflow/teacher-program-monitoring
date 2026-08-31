"""The cahier journal: filled once from the day's séances, then lived in.

`docs/exemple-cahier-journal-quotidien.pdf` prints three columns —
« Discipline - Durée », « Objectif(s) et compétence(s) », « Bilan » — and what goes in the
first two is what a séance already knows. Initialising a day is copying that across; the
bilan is written after the lesson and starts empty.

The rule that shapes everything here is §10's: « les cahiers journaux … ne sont jamais
écrasés ». The generator honours it from the other side (``_untouchable_days`` in
``planning/writer.py``); here it means a day whose cahier journal exists is never filled
again, not even partly, and never in part.
"""

import datetime
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Row, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.base import table_of
from core.models.calendar import SchoolDay
from core.models.curriculum import Subject
from core.models.journal import JournalEntry
from core.models.level import Level
from core.models.planning import PlannedSession
from core.models.timetable import TimetableSlot
from core.schemas import JournalEntryOut


class JournalError(Exception):
    """A date the cahier journal has no day for, said in French for the API."""


class OrderError(JournalError):
    """An order that does not name exactly the lignes of the day it reorders."""


@dataclass(frozen=True, slots=True)
class Journal:
    """A day's cahier journal, and whether the day has one at all.

    A day never initialised and a day whose lignes have all been deleted are different
    states: only the first may be filled from the séances, or a teacher who emptied a day
    on purpose would find it full again on her next visit.
    """

    entries: tuple[JournalEntryOut, ...]
    initialised: bool


def _discipline(row: Row) -> str:
    """Name the discipline of a ligne, the way the teacher writes it in the first column.

    The créneau's own label is that name — it is the EDT's wording (§4.1), and the example
    cahier journal prints exactly that kind of short heading. The six alternating créneaux
    are the exception: their label names a pair (« Histoire ou Géographie »), so the
    matière the séance resolved to is what goes down (ADR-0002).

    The niveau is appended wherever the séance is not commun, because a split créneau puts
    two lignes at the same hour and the teacher has to tell them apart (ADR-0010).
    """
    name = row.subject_label if row.is_alternating and row.subject_label else row.slot_label
    level = Level(row.level)
    return name if level is Level.COMMUN else f"{name} ({level.value})"


def _objectives(title: str, objectives: str | None) -> str:
    """Fill the « Objectif(s) et compétence(s) » column: what is taught, then what it aims at.

    The example prints both in that one cell — « Séquence 1 Les types de phrases … », and
    under « Utiliser les nombres jusqu'à 200 » a « Séance 1 ». A séance whose objectifs
    repeat its title says it once.
    """
    if not objectives or objectives.strip() == title.strip():
        return title
    return f"{title}\n{objectives}"


def _rendered(row: Row) -> JournalEntryOut:
    """Render one ligne de cahier journal."""
    return JournalEntryOut(
        id=row.id,
        school_day_id=row.school_day_id,
        planned_session_id=row.planned_session_id,
        discipline=row.discipline,
        duration_minutes=row.duration_minutes,
        objectives=row.objectives,
        bilan=row.bilan,
        notes=row.notes,
        position=row.position,
    )


async def _day_id(session: AsyncSession, day: datetime.date) -> uuid.UUID:
    """Find the jour de classe, or say that this date is not one."""
    days = table_of(SchoolDay)
    found = (await session.execute(select(days.c.id).where(days.c.date == day))).one_or_none()
    if found is None:
        message = f"{day.isoformat()} n'est pas un jour de classe"
        raise JournalError(message)
    return found.id


async def load_journal(session: AsyncSession, day: datetime.date) -> Journal:
    """Read a day's cahier journal, in the order its lignes are written down."""
    day_id = await _day_id(session, day)
    entries = table_of(JournalEntry)
    rows = (
        await session.execute(
            select(entries)
            .where(entries.c.school_day_id == day_id)
            .order_by(entries.c.position, entries.c.created_at)
        )
    ).all()
    return Journal(
        entries=tuple(_rendered(row) for row in rows),
        initialised=await _is_initialised(session, day_id),
    )


async def _is_initialised(session: AsyncSession, day_id: uuid.UUID) -> bool:
    """Say whether the day has ever had a cahier journal.

    Read off the lignes themselves: the day is initialised as soon as one exists. A day
    emptied afterwards reads as not initialised again, which is the one case this cannot
    tell apart — and the one where filling it from the séances is what the teacher would
    ask for anyway.
    """
    entries = table_of(JournalEntry)
    held = (
        await session.execute(
            select(func.count()).select_from(entries).where(entries.c.school_day_id == day_id)
        )
    ).scalar_one()
    return held > 0


async def initialise_journal(session: AsyncSession, day: datetime.date) -> Journal:
    """Fill a day's cahier journal from its séances, once.

    A day that already has one comes back untouched: §10 says a cahier journal is never
    overwritten, and « the first time the vue jour is opened » (§8 Phase 6) is the only
    time this writes.
    """
    day_id = await _day_id(session, day)
    if await _is_initialised(session, day_id):
        return await load_journal(session, day)

    sessions, slots, subjects, entries = (
        table_of(PlannedSession),
        table_of(TimetableSlot),
        table_of(Subject),
        table_of(JournalEntry),
    )
    rows = (
        await session.execute(
            # Column by column: ``planned_sessions`` and ``timetable_slots`` both have an
            # ``id`` and a ``level``, and a whole-table select would leave which one a
            # row attribute means to the order of the FROM clause.
            select(
                sessions.c.id.label("session_id"),
                sessions.c.level,
                sessions.c.title,
                sessions.c.objectives,
                slots.c.label.label("slot_label"),
                slots.c.is_alternating,
                slots.c.duration_minutes,
                subjects.c.label.label("subject_label"),
            )
            .join(slots, slots.c.id == sessions.c.timetable_slot_id)
            .join(subjects, subjects.c.id == sessions.c.subject_id, isouter=True)
            .where(sessions.c.school_day_id == day_id)
            .order_by(sessions.c.position, sessions.c.level)
        )
    ).all()
    if rows:
        await session.execute(
            insert(entries).values(
                [
                    {
                        "school_day_id": day_id,
                        "planned_session_id": row.session_id,
                        "discipline": _discipline(row),
                        # The créneau's teaching time, not ``ends_at - starts_at``: the
                        # cahier journal prints a durée (ADR-0003).
                        "duration_minutes": row.duration_minutes,
                        "objectives": _objectives(row.title, row.objectives),
                        "position": rank,
                    }
                    for rank, row in enumerate(rows, start=1)
                ]
            )
        )
    return await load_journal(session, day)


async def add_entry(session: AsyncSession, day: datetime.date, values: dict[str, Any]) -> uuid.UUID:
    """Add one ligne at the end of a day's cahier journal."""
    day_id = await _day_id(session, day)
    entries = table_of(JournalEntry)
    if values.get("position") is None:
        last = (
            await session.execute(
                select(func.max(entries.c.position)).where(entries.c.school_day_id == day_id)
            )
        ).scalar_one()
        values["position"] = (last or 0) + 1
    return (
        await session.execute(
            insert(entries).values(school_day_id=day_id, **values).returning(entries.c.id)
        )
    ).scalar_one()


async def load_entry(session: AsyncSession, identifier: uuid.UUID) -> JournalEntryOut | None:
    """Read one ligne back. Returns ``None`` if there is no such ligne."""
    entries = table_of(JournalEntry)
    row = (await session.execute(select(entries).where(entries.c.id == identifier))).one_or_none()
    return None if row is None else _rendered(row)


async def update_entry(
    session: AsyncSession, identifier: uuid.UUID, values: dict[str, Any]
) -> JournalEntryOut | None:
    """Change one ligne. Returns ``None`` if there is no such ligne."""
    entries = table_of(JournalEntry)
    if values:
        await session.execute(update(entries).where(entries.c.id == identifier).values(**values))
    row = (await session.execute(select(entries).where(entries.c.id == identifier))).one_or_none()
    return None if row is None else _rendered(row)


async def delete_entry(session: AsyncSession, identifier: uuid.UUID) -> bool:
    """Remove one ligne. Returns ``False`` if there was none."""
    entries = table_of(JournalEntry)
    removed = await session.execute(
        delete(entries).where(entries.c.id == identifier).returning(entries.c.id)
    )
    return removed.one_or_none() is not None


async def reorder(session: AsyncSession, day: datetime.date, order: list[uuid.UUID]) -> Journal:
    """Renumber a day's lignes into the given order.

    The order has to name every ligne of the day and nothing else: a partial order would
    leave two lignes claiming one rank, and the cahier journal is a list rather than a set.
    """
    day_id = await _day_id(session, day)
    entries = table_of(JournalEntry)
    held = {
        row.id
        for row in (
            await session.execute(select(entries.c.id).where(entries.c.school_day_id == day_id))
        ).all()
    }
    if set(order) != held or len(order) != len(held):
        message = (
            "L'ordre doit nommer exactement les lignes du cahier journal de ce jour, "
            "une fois chacune"
        )
        raise OrderError(message)

    for rank, identifier in enumerate(order, start=1):
        await session.execute(
            update(entries).where(entries.c.id == identifier).values(position=rank)
        )
    return await load_journal(session, day)
