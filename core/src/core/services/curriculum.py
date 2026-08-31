"""Browsing and searching the programmes officiels.

The search is Postgres': ``websearch_to_tsquery('french', …)`` against the ``search_vector``
column Phase 2 generated and its GIN index (§6). Never ``ILIKE`` — the French dictionary is
what makes « fractions » find « fraction », and what makes a search of 220 blocks of
curriculum return the ones that are about a word rather than the ones that contain it.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.base import table_of
from core.models.curriculum import Domain, ProgramItem, Subject
from core.models.level import Level
from core.schemas import PAGE_SIZE, ProgramItemOut
from core.services.reference import Reference, load_reference, program_item_ref


@dataclass(frozen=True, slots=True)
class ProgramQuery:
    """What the programme browser is asking for — §7 écran 4's filters and its search."""

    level: Level | None = None
    subject: str | None = None
    domain: str | None = None
    text: str | None = None
    limit: int = PAGE_SIZE
    offset: int = 0


def _out(row: Row, reference: Reference) -> ProgramItemOut:
    """Render one item de programme with everything the browser shows of it."""
    return ProgramItemOut(
        **program_item_ref(row, reference).model_dump(),
        description=row.description,
        source_file=row.source_file,
        source_page=row.source_page,
        source_order=row.source_order,
        needs_review=row.needs_review,
    )


async def search_program_items(
    session: AsyncSession, query: ProgramQuery
) -> tuple[list[ProgramItemOut], int]:
    """Filter and search the items de programme, and say how many matched in all.

    Results are ranked when there is a search and ordered by ``source_order`` when there is
    not: the order the programme prints its blocks in is the only order they have, since
    their id is a random UUID (ADR-0015).
    """
    items, subjects, domains = table_of(ProgramItem), table_of(Subject), table_of(Domain)
    filters = []
    if query.level is not None:
        filters.append(items.c.level == query.level.value)
    if query.subject:
        filters.append(
            items.c.subject_id.in_(select(subjects.c.id).where(subjects.c.code == query.subject))
        )
    if query.domain:
        filters.append(
            items.c.domain_id.in_(select(domains.c.id).where(domains.c.code == query.domain))
        )

    matched = None
    if query.text and query.text.strip():
        matched = func.websearch_to_tsquery("french", query.text)
        filters.append(items.c.search_vector.op("@@")(matched))

    total = (
        await session.execute(select(func.count()).select_from(items).where(*filters))
    ).scalar_one()
    ordering = (
        [func.ts_rank(items.c.search_vector, matched).desc(), items.c.source_order]
        if matched is not None
        else [items.c.source_order]
    )
    rows = (
        await session.execute(
            select(items)
            .where(*filters)
            .order_by(*ordering)
            .limit(query.limit)
            .offset(query.offset)
        )
    ).all()

    reference = await load_reference(session)
    return [_out(row, reference) for row in rows], total


async def load_program_item(session: AsyncSession, identifier: uuid.UUID) -> ProgramItemOut | None:
    """Read one item de programme, or ``None`` if there is no such item."""
    items = table_of(ProgramItem)
    row = (await session.execute(select(items).where(items.c.id == identifier))).one_or_none()
    if row is None:
        return None
    return _out(row, await load_reference(session))
