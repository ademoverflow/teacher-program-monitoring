"""The séances: read one, add one, change one, remove one."""

import datetime
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.models.level import Level
from core.models.status import SessionStatus
from core.schemas import (
    MAX_PAGE_SIZE,
    PAGE_SIZE,
    PlannedSessionDetail,
    PlannedSessionPage,
)
from core.services.planned_sessions import (
    Placement,
    PlacementError,
    create_planned_session,
    delete_planned_session,
    update_planned_session,
)
from core.services.schedule import load_planned_session, planned_sessions_of_program_item

planned_sessions_router = APIRouter(prefix="/planned-sessions", tags=["Séances"])


class PlannedSessionCreate(BaseModel):
    """A séance the teacher adds by hand, named by the natural key of ADR-0009."""

    date: datetime.date
    timetable_slot_id: uuid.UUID
    level: Level
    title: str = Field(min_length=1)
    objectives: str | None = None
    content: str | None = None
    materials: str | None = None
    status: SessionStatus = SessionStatus.PLANIFIEE
    position: int | None = None
    program_item_ids: list[uuid.UUID] = []


class PlannedSessionUpdate(BaseModel):
    """What a séance may be told to say. Its jour, créneau and niveau are its identity."""

    title: str | None = Field(default=None, min_length=1)
    objectives: str | None = None
    content: str | None = None
    materials: str | None = None
    status: SessionStatus | None = None
    position: int | None = None
    program_item_ids: list[uuid.UUID] | None = None


async def _read_back(session: AsyncSession, identifier: uuid.UUID) -> PlannedSessionDetail:
    """Read a séance back after writing it, so the caller gets the whole rendered shape."""
    found = await load_planned_session(session, identifier)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette séance n'existe pas")
    return found


@planned_sessions_router.get("")
async def list_planned_sessions(
    session: Annotated[AsyncSession, Depends(get_session)],
    program_item_id: Annotated[uuid.UUID, Query()],
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PlannedSessionPage:
    """List the séances working one item de programme — §7 écran 4's « séances liées ».

    A rituel links the same items on every occurrence (ADR-0015), so this list runs to the
    whole year and is paged. The semaine and the jour views are how séances are listed by
    date; this endpoint exists for the programme browser.
    """
    found, total = await planned_sessions_of_program_item(
        session, program_item_id, limit=limit, offset=offset
    )
    return PlannedSessionPage(total=total, limit=limit, offset=offset, sessions=found)


@planned_sessions_router.get("/{identifier}")
async def read_planned_session(
    identifier: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlannedSessionDetail:
    """Return one séance with its créneau, its séquence and its items de programme."""
    return await _read_back(session, identifier)


@planned_sessions_router.post("", status_code=status.HTTP_201_CREATED)
async def add_planned_session(
    body: PlannedSessionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlannedSessionDetail:
    """Add a séance to a (jour, créneau, niveau).

    Answers 409 rather than failing on the constraint when that triple is already taken,
    when the jour is chômé, or when the créneau belongs to another weekday or another
    niveau: the EDT is immutable (§10), so a placement it forbids is refused here.
    """
    values = body.model_dump(exclude={"date", "timetable_slot_id", "level", "program_item_ids"})
    try:
        identifier = await create_planned_session(
            session,
            Placement(date=body.date, timetable_slot_id=body.timetable_slot_id, level=body.level),
            values=values,
            program_item_ids=body.program_item_ids,
        )
    except PlacementError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    await session.commit()
    return await _read_back(session, identifier)


@planned_sessions_router.patch("/{identifier}")
async def edit_planned_session(
    identifier: uuid.UUID,
    body: PlannedSessionUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlannedSessionDetail:
    """Change what a séance says — its title, objectifs, contenu, matériel, statut, rang."""
    values = body.model_dump(exclude_unset=True, exclude={"program_item_ids"})
    try:
        found = await update_planned_session(
            session, identifier, values=values, program_item_ids=body.program_item_ids
        )
    except PlacementError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    if not found:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette séance n'existe pas")
    await session.commit()
    return await _read_back(session, identifier)


@planned_sessions_router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_planned_session(
    identifier: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Remove a séance. A re-generation puts it back — the programmation is deterministic."""
    if not await delete_planned_session(session, identifier):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette séance n'existe pas")
    await session.commit()
