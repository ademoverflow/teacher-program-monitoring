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
from core.schemas import SessionDetail, SessionSummary
from core.services.schedule import load_session, sessions_of_program_item
from core.services.sessions import (
    Placement,
    PlacementError,
    create_session,
    delete_session,
    update_session,
)

sessions_router = APIRouter(prefix="/sessions", tags=["Séances"])

PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class SessionCreate(BaseModel):
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


class SessionUpdate(BaseModel):
    """What a séance may be told to say. Its jour, créneau and niveau are its identity."""

    title: str | None = Field(default=None, min_length=1)
    objectives: str | None = None
    content: str | None = None
    materials: str | None = None
    status: SessionStatus | None = None
    position: int | None = None
    program_item_ids: list[uuid.UUID] | None = None


async def _rendered(session: AsyncSession, identifier: uuid.UUID) -> SessionDetail:
    """Read a séance back after writing it, so the caller gets the whole rendered shape."""
    found = await load_session(session, identifier)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette séance n'existe pas")
    return found


@sessions_router.get("/{identifier}")
async def read_session(
    identifier: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SessionDetail:
    """Return one séance with its créneau, its séquence and its items de programme."""
    return await _rendered(session, identifier)


@sessions_router.post("", status_code=status.HTTP_201_CREATED)
async def add_session(
    body: SessionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SessionDetail:
    """Add a séance to a (jour, créneau, niveau).

    Answers 409 rather than failing on the constraint when that triple is already taken,
    when the jour is chômé, or when the créneau belongs to another weekday or another
    niveau: the EDT is immutable (§10), so a placement it forbids is refused here.
    """
    values = body.model_dump(
        exclude={"date", "timetable_slot_id", "level", "program_item_ids"},
    )
    try:
        identifier = await create_session(
            session,
            Placement(date=body.date, timetable_slot_id=body.timetable_slot_id, level=body.level),
            values=values,
            program_item_ids=body.program_item_ids,
        )
    except PlacementError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    await session.commit()
    return await _rendered(session, identifier)


@sessions_router.patch("/{identifier}")
async def edit_session(
    identifier: uuid.UUID,
    body: SessionUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SessionDetail:
    """Change what a séance says — its title, objectifs, contenu, matériel, statut, rang."""
    values = body.model_dump(exclude_unset=True, exclude={"program_item_ids"})
    try:
        found = await update_session(
            session,
            identifier,
            values=values,
            program_item_ids=body.program_item_ids,
        )
    except PlacementError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    if not found:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette séance n'existe pas")
    await session.commit()
    return await _rendered(session, identifier)


@sessions_router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_session(
    identifier: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Remove a séance. A re-generation puts it back — the programmation is deterministic."""
    if not await delete_session(session, identifier):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette séance n'existe pas")
    await session.commit()


class LinkedSessions(BaseModel):
    """The séances that work one item de programme, paged."""

    total: int
    sessions: list[SessionSummary]


async def linked_sessions(
    session: AsyncSession, item_id: uuid.UUID, limit: int, offset: int
) -> LinkedSessions:
    """Page through the séances linking one item de programme."""
    found, total = await sessions_of_program_item(session, item_id, limit=limit, offset=offset)
    return LinkedSessions(total=total, sessions=found)


@sessions_router.get("")
async def list_sessions(
    session: Annotated[AsyncSession, Depends(get_session)],
    program_item_id: Annotated[uuid.UUID, Query()],
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LinkedSessions:
    """List the séances working one item de programme — §7 écran 4's « voir les séances liées ».

    A rituel links the same items on every occurrence (ADR-0015), so this list runs to the
    whole year and is paged. The semaine and the jour views are how séances are listed by
    date; this endpoint exists for the programme browser.
    """
    return await linked_sessions(session, program_item_id, limit, offset)
