"""The jour de classe and its séances, in the order they run."""

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.schemas import DayDetail
from core.services.schedule import load_day

days_router = APIRouter(prefix="/days", tags=["Jours"])


@days_router.get("/{day}")
async def read_day(
    day: datetime.date,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DayDetail:
    """Return one jour de classe with its séances and the items de programme they link.

    A jour chômé answers like any other, with `is_off`, its motif and no séance: the day
    keeps its place in the semaine so the plan can account for it (ADR-0001).
    """
    found = await load_day(session, day)
    if found is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"{day.isoformat()} n'est pas un jour de classe"
        )
    return found
