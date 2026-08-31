"""The matières and the domaines under them — the colours, and the programme filters."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.schemas import SubjectWithDomains
from core.services.schedule import load_subjects

subjects_router = APIRouter(prefix="/subjects", tags=["Matières"])


@subjects_router.get("")
async def read_subjects(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[SubjectWithDomains]:
    """Return the matières with their domaines.

    ``poesie`` comes back like the others and carries no item de programme: the programme
    officiel has a poésie entrée inside français rather than a poésie section (ADR-0014).
    """
    return await load_subjects(session)
