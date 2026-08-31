"""The programmes officiels: filter them, search them, and see what works them."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.models.level import Level
from core.schemas import ProgramItemOut
from core.services.schedule import ProgramQuery, load_program_item, search_program_items

program_items_router = APIRouter(prefix="/program-items", tags=["Programmes"])

PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class ProgramItemPage(BaseModel):
    """One page of items de programme, and how many matched in all."""

    total: int
    limit: int
    offset: int
    items: list[ProgramItemOut]


@program_items_router.get("")
async def list_program_items(  # noqa: PLR0913 - one parameter per filter §7 écran 4 asks for
    session: Annotated[AsyncSession, Depends(get_session)],
    level: Annotated[Level | None, Query()] = None,
    subject: Annotated[str | None, Query(description="Code de la matière")] = None,
    domain: Annotated[str | None, Query(description="Code du domaine")] = None,
    q: Annotated[str | None, Query(description="Recherche plein texte (français)")] = None,
    needs_review: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProgramItemPage:
    """Filter the items de programme by niveau, matière and domaine, and search them.

    `q` goes through `websearch_to_tsquery('french', …)` against the generated
    `search_vector` column, so it stems (« fractions » finds « fraction ») and honours
    quoted phrases and `-mot`. Without `q`, items come back in the order the source prints
    them; with one, by rank.
    """
    items, total = await search_program_items(
        session,
        ProgramQuery(
            level=level,
            subject=subject,
            domain=domain,
            text=q,
            needs_review=needs_review,
            limit=limit,
            offset=offset,
        ),
    )
    return ProgramItemPage(total=total, limit=limit, offset=offset, items=items)


@program_items_router.get("/{identifier}")
async def read_program_item(
    identifier: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProgramItemOut:
    """Return one item de programme with the file and the page it was read from."""
    found = await load_program_item(session, identifier)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cet item de programme n'existe pas")
    return found
