"""The gabarit EDT: the 44 créneaux the whole year is laid over."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.schemas import SlotSummary
from core.services.reference import load_timetable

timetable_router = APIRouter(prefix="/timetable", tags=["Emploi du temps"])


@timetable_router.get("")
async def read_timetable(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[SlotSummary]:
    """Return the créneaux of §4.1, ordered by day and by hour.

    The gabarit is immutable (§10) and is read-only here: it is what draws the rows of the
    semaine grid, including for a semaine that has no séance at all.
    """
    return await load_timetable(session)
