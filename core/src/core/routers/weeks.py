"""The semaine, rendered as the grid of §4.1."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.schemas import WeekDetail
from core.services.schedule import load_week

weeks_router = APIRouter(prefix="/weeks", tags=["Semaines"])


@weeks_router.get("/{number}")
async def read_week(
    number: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WeekDetail:
    """Return one semaine: its jours, and in each of them every créneau of that weekday.

    A cell carries 0, 1 or 2 séances. Two mean a commun créneau split by niveau
    (ADR-0010) — one CM1 and one CM2 in the same 45 minutes — which is not the same thing
    as the times where the EDT itself holds two créneaux side by side. None mean a jour
    chômé, which keeps its cells and its motif rather than disappearing (ADR-0001).

    S1 has three jours: the year opens on a mardi.
    """
    week = await load_week(session, number)
    if week is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Aucune semaine numéro {number}")
    return week
