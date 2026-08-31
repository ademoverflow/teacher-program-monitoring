"""The cahier journal of one jour de classe: initialise it, edit it, reorder it."""

import datetime
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.schemas import JournalDay, JournalEntryOut
from core.services.journal import (
    JournalError,
    OrderError,
    add_entry,
    delete_entry,
    initialise_journal,
    load_entry,
    load_journal,
    reorder,
    update_entry,
)

journal_router = APIRouter(prefix="/journal", tags=["Cahier journal"])


class EntryCreate(BaseModel):
    """A ligne the teacher writes herself — a séance that was not planned, a note."""

    discipline: str = Field(min_length=1)
    duration_minutes: int | None = Field(default=None, ge=0)
    objectives: str | None = None
    bilan: str | None = None
    notes: str | None = None
    planned_session_id: uuid.UUID | None = None
    position: int | None = None


class EntryUpdate(BaseModel):
    """What a ligne may be told to say. Everything on it is the teacher's to change."""

    discipline: str | None = Field(default=None, min_length=1)
    duration_minutes: int | None = Field(default=None, ge=0)
    objectives: str | None = None
    bilan: str | None = None
    notes: str | None = None
    position: int | None = None


class EntryOrder(BaseModel):
    """The lignes of one day, in the order they should now be read."""

    entry_ids: list[uuid.UUID]


@journal_router.get("/{day}")
async def read_journal(
    day: datetime.date,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JournalDay:
    """Return a day's cahier journal, in the order its lignes are written down.

    A day never opened comes back with `initialised: false` and no ligne — the vue jour is
    what asks for it to be filled.
    """
    try:
        return await load_journal(session, day)
    except JournalError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error


@journal_router.post(
    "/{day}/initialise",
    responses={status.HTTP_201_CREATED: {"description": "Le cahier journal a été rempli"}},
)
async def initialise(
    day: datetime.date,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JournalDay:
    """Fill a day's cahier journal from its séances, once.

    Idempotent by design rather than by accident: a day that already has a cahier journal
    comes back exactly as it is, because §10 says one is never overwritten. Call it every
    time the vue jour opens — **201** says this call filled the day, **200** that it found
    it already filled (or that a jour chômé has nothing to fill it with).
    """
    try:
        journal = await initialise_journal(session, day)
    except JournalError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    await session.commit()
    response.status_code = status.HTTP_201_CREATED if journal.created else status.HTTP_200_OK
    return journal.day


@journal_router.post("/{day}/entries", status_code=status.HTTP_201_CREATED)
async def add_journal_entry(
    day: datetime.date,
    body: EntryCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JournalEntryOut:
    """Add a ligne at the end of a day's cahier journal."""
    try:
        identifier = await add_entry(session, day, body.model_dump())
    except JournalError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    await session.commit()
    written = await load_entry(session, identifier)
    if written is None:  # pragma: no cover - the row was just written
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette ligne n'existe pas")
    return written


@journal_router.patch("/entries/{identifier}")
async def edit_journal_entry(
    identifier: uuid.UUID,
    body: EntryUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JournalEntryOut:
    """Change one ligne — its discipline, its durée, ses objectifs, son bilan, ses notes."""
    written = await update_entry(session, identifier, body.model_dump(exclude_unset=True))
    if written is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette ligne n'existe pas")
    await session.commit()
    return written


@journal_router.delete("/entries/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_journal_entry(
    identifier: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Remove one ligne. The cahier journal is the teacher's: nothing puts it back."""
    if not await delete_entry(session, identifier):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette ligne n'existe pas")
    await session.commit()


@journal_router.put("/{day}/order")
async def reorder_journal(
    day: datetime.date,
    body: EntryOrder,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JournalDay:
    """Renumber a day's lignes into the given order.

    The list must name every ligne of the day exactly once: a partial order would leave two
    lignes claiming one rank, and a cahier journal is a list, not a set.
    """
    try:
        journal = await reorder(session, day, body.entry_ids)
    except OrderError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except JournalError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    await session.commit()
    return journal
