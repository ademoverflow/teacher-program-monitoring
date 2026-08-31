"""The calendrier: the whole année scolaire, and where today sits in it."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.clock import today
from core.database import get_session
from core.schemas import TodayOut, YearOverview
from core.services.schedule import load_today, load_year

calendar_router = APIRouter(prefix="/calendar", tags=["Calendrier"])


@calendar_router.get("")
async def read_year(
    session: Annotated[AsyncSession, Depends(get_session)],
    on: Annotated[date, Depends(today)],
) -> YearOverview:
    """Return the année scolaire: its périodes, their semaines, and the vacances.

    This is §7 écran 1 in one request — the year view never has to walk the semaines.
    """
    year = await load_year(session, on)
    if year is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucune année scolaire n'est chargée")
    return year


@calendar_router.get("/today")
async def read_today(
    session: Annotated[AsyncSession, Depends(get_session)],
    on: Annotated[date, Depends(today)],
) -> TodayOut:
    """Return today's jour de classe if there is one, and the jour de classe to open.

    « Aujourd'hui » is the home page (§7), and it lands outside the year most of the time:
    a Wednesday, a weekend, the vacances. On one of the four jours chômés, `school_day`
    still comes back — with its motif — and `next_taught_day` says where to go instead.
    """
    return await load_today(session, on)
