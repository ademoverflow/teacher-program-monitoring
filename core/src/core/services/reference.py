"""The small tables a rendered séance points at, read whole and joined in Python.

The generator writes 1740 séances against 12 matières, 45 domaines, 44 créneaux and 120
séquences. Reading those four tables entire, once per request, and looking each séance up in
a dict costs less than joining them per row — and it gives every reader the same rendering
of a matière or a créneau, which is what keeps the API's shapes consistent.
"""

import uuid
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.base import table_of
from core.models.curriculum import Domain, Subject
from core.models.level import Level
from core.models.sequence import Sequence, SequenceSession
from core.models.timetable import TimetableSlot
from core.models.weekday import Weekday
from core.schemas import (
    DomainRef,
    ProgramItemRef,
    SequenceRef,
    SequenceStepRef,
    SlotSummary,
    SubjectRef,
    SubjectWithDomains,
)


@dataclass(frozen=True, slots=True)
class Reference:
    """The matières, domaines, créneaux and séquences, keyed by their id."""

    subjects: dict[uuid.UUID, SubjectRef]
    domains: dict[uuid.UUID, DomainRef]
    slots: dict[uuid.UUID, SlotSummary]
    sequences: dict[uuid.UUID, SequenceRef]
    steps: dict[uuid.UUID, SequenceStepRef]

    def slots_of(self, day_of_week: Weekday) -> list[SlotSummary]:
        """Return the créneaux of one weekday, in the order the grid prints them.

        Sorted by niveau after the hour so that a time where the EDT holds two créneaux —
        mardi 11h30 CM1 and CM2 — always comes back in the same order.
        """
        return sorted(
            (slot for slot in self.slots.values() if slot.day_of_week == day_of_week),
            key=lambda slot: (slot.starts_at, slot.level.value),
        )


async def load_reference(session: AsyncSession) -> Reference:
    """Read the matières, domaines, créneaux and séquences — 221 rows in all."""
    subjects = {
        row.id: SubjectRef(id=row.id, code=row.code, label=row.label, color=row.color)
        for row in (await session.execute(select(table_of(Subject)))).all()
    }
    domains = {
        row.id: DomainRef(id=row.id, code=row.code, label=row.label, level=Level(row.level))
        for row in (await session.execute(select(table_of(Domain)))).all()
    }
    slots = {
        row.id: SlotSummary(
            id=row.id,
            day_of_week=Weekday(row.day_of_week),
            starts_at=row.starts_at,
            ends_at=row.ends_at,
            duration_minutes=row.duration_minutes,
            label=row.label,
            level=Level(row.level),
            is_alternating=row.is_alternating,
            alternation_group=row.alternation_group,
            subject=subjects.get(row.subject_id),
            domain=domains.get(row.domain_id),
        )
        for row in (await session.execute(select(table_of(TimetableSlot)))).all()
    }
    sequences = {
        row.id: SequenceRef(
            id=row.id,
            method=row.method,
            level=Level(row.level),
            number=row.number,
            title=row.title,
        )
        for row in (await session.execute(select(table_of(Sequence)))).all()
    }
    steps = {
        row.id: SequenceStepRef(id=row.id, number=row.number, title=row.title)
        for row in (await session.execute(select(table_of(SequenceSession)))).all()
    }
    return Reference(
        subjects=subjects, domains=domains, slots=slots, sequences=sequences, steps=steps
    )


def program_item_ref(row: Row, reference: Reference) -> ProgramItemRef:
    """Render one item de programme the way a séance and a search both name it."""
    return ProgramItemRef(
        id=row.id,
        level=Level(row.level),
        title=row.title,
        subject=reference.subjects.get(row.subject_id),
        domain=reference.domains.get(row.domain_id),
    )


async def load_timetable(session: AsyncSession) -> list[SlotSummary]:
    """Read the 44 créneaux of the gabarit, in the order the grid prints them."""
    reference = await load_reference(session)
    return sorted(
        reference.slots.values(),
        key=lambda slot: (slot.day_of_week, slot.starts_at, slot.level.value),
    )


async def load_subjects(session: AsyncSession) -> list[SubjectWithDomains]:
    """Read the matières with their domaines — the programme filters, and the colours."""
    subjects, domains = table_of(Subject), table_of(Domain)
    under: dict[uuid.UUID, list[DomainRef]] = defaultdict(list)
    for row in (
        await session.execute(select(domains).order_by(domains.c.level, domains.c.label))
    ).all():
        under[row.subject_id].append(
            DomainRef(id=row.id, code=row.code, label=row.label, level=Level(row.level))
        )
    return [
        SubjectWithDomains(
            id=row.id,
            code=row.code,
            label=row.label,
            color=row.color,
            domains=under.get(row.id, []),
        )
        for row in (await session.execute(select(subjects).order_by(subjects.c.label))).all()
    ]
