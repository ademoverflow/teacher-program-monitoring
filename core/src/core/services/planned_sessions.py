"""Writing a séance by hand: what the teacher may add, change and remove.

The generator writes the year (``services/planning``); this is the other door, the one
§8 Phase 4 calls « CRUD planned_sessions ». It exists to let the teacher correct a
placement, not to let anything through: the EDT is immutable (§10), so a séance still has
to sit in a créneau of its own weekday, at a niveau that créneau teaches, on a jour that is
not chômé — and the natural key of ADR-0009 still allows one séance per
(jour, créneau, niveau).
"""

import datetime
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Row, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.base import table_of
from core.models.curriculum import ProgramItem
from core.models.level import Level
from core.models.planning import PlannedSession, PlannedSessionProgramItem
from core.models.timetable import TimetableSlot
from core.services.school_day import find_school_day, next_position, not_a_school_day


class PlacementError(Exception):
    """A séance the EDT or the calendar does not allow.

    The message is French and is shown to the teacher: this is the API's way of saying
    « toute impossibilité de placement se signale, ne se contourne pas » (§10).
    """


@dataclass(frozen=True, slots=True)
class Placement:
    """Where a séance goes — the natural key of ADR-0009, with the jour named by its date."""

    date: datetime.date
    timetable_slot_id: uuid.UUID
    level: Level


async def _day_of(session: AsyncSession, placement: Placement) -> Row:
    """Find the jour de classe and the créneau, and refuse what the EDT forbids."""
    slots = table_of(TimetableSlot)
    day = await find_school_day(session, placement.date)
    if day is None:
        raise PlacementError(not_a_school_day(placement.date))
    if day.is_off:
        message = (
            f"{placement.date.isoformat()} est chômé ({day.off_reason}) : "
            f"aucune séance ne s'y place"
        )
        raise PlacementError(message)

    slot = (
        await session.execute(select(slots).where(slots.c.id == placement.timetable_slot_id))
    ).one_or_none()
    if slot is None:
        message = "Ce créneau n'existe pas"
        raise PlacementError(message)
    if slot.day_of_week != day.day_of_week:
        message = (
            "Ce créneau n'est pas un créneau de ce jour de la semaine : "
            "l'emploi du temps ne se déplace pas"
        )
        raise PlacementError(message)
    if slot.level not in (Level.COMMUN, placement.level.value):
        message = f"Ce créneau est un créneau {slot.level}, pas {placement.level.value}"
        raise PlacementError(message)
    return day


async def _replace_program_items(
    session: AsyncSession, session_id: uuid.UUID, item_ids: list[uuid.UUID]
) -> None:
    """Set the items de programme a séance links, dropping the ones it no longer names."""
    links, items = table_of(PlannedSessionProgramItem), table_of(ProgramItem)
    await session.execute(delete(links).where(links.c.planned_session_id == session_id))
    if not item_ids:
        return
    found = await session.execute(select(items.c.id).where(items.c.id.in_(item_ids)))
    known = {row.id for row in found.all()}
    unknown = [str(item) for item in item_ids if item not in known]
    if unknown:
        message = f"Items de programme inconnus : {', '.join(unknown)}"
        raise PlacementError(message)
    await session.execute(
        insert(links).values(
            [
                {"planned_session_id": session_id, "program_item_id": item}
                for item in dict.fromkeys(item_ids)
            ]
        )
    )


async def create_planned_session(
    session: AsyncSession,
    placement: Placement,
    *,
    values: dict[str, Any],
    program_item_ids: list[uuid.UUID] | None = None,
) -> uuid.UUID:
    """Add one séance, and return its id.

    ``position`` defaults to the end of the day rather than to zero: the cahier journal is
    initialised in that order (ADR-0021), and a new séance that landed first would rewrite
    the morning.
    """
    day = await _day_of(session, placement)
    sessions = table_of(PlannedSession)

    taken = (
        await session.execute(
            select(sessions.c.id).where(
                sessions.c.school_day_id == day.id,
                sessions.c.timetable_slot_id == placement.timetable_slot_id,
                sessions.c.level == placement.level.value,
            )
        )
    ).one_or_none()
    if taken is not None:
        message = (
            f"Ce créneau porte déjà une séance {placement.level.value} "
            f"le {placement.date.isoformat()}"
        )
        raise PlacementError(message)

    if values.get("position") is None:
        values["position"] = await next_position(session, sessions, day.id)

    identifier = (
        await session.execute(
            insert(sessions)
            .values(
                school_day_id=day.id,
                timetable_slot_id=placement.timetable_slot_id,
                level=placement.level.value,
                **values,
            )
            .returning(sessions.c.id)
        )
    ).scalar_one()
    await _replace_program_items(session, identifier, program_item_ids or [])
    return identifier


async def update_planned_session(
    session: AsyncSession,
    identifier: uuid.UUID,
    *,
    values: dict[str, Any],
    program_item_ids: list[uuid.UUID] | None = None,
) -> bool:
    """Change what a séance says. Returns ``False`` if there is no such séance.

    Only what a séance *says* is editable: its jour, its créneau and its niveau are its
    identity (ADR-0009), and moving one is deleting it and adding another.
    """
    sessions = table_of(PlannedSession)
    exists = (
        await session.execute(select(sessions.c.id).where(sessions.c.id == identifier))
    ).one_or_none()
    if exists is None:
        return False
    if values:
        await session.execute(update(sessions).where(sessions.c.id == identifier).values(**values))
    if program_item_ids is not None:
        await _replace_program_items(session, identifier, program_item_ids)
    return True


async def delete_planned_session(session: AsyncSession, identifier: uuid.UUID) -> bool:
    """Remove a séance. Returns ``False`` if there was none.

    The links to the items de programme go with it (``ON DELETE CASCADE``); a ligne de
    cahier journal that pointed at it keeps its text and loses the pointer
    (``ON DELETE SET NULL``), because what the teacher wrote down is hers.
    """
    sessions = table_of(PlannedSession)
    removed = await session.execute(
        delete(sessions).where(sessions.c.id == identifier).returning(sessions.c.id)
    )
    return removed.one_or_none() is not None
