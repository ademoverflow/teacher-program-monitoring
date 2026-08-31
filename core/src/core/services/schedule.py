"""Reading the year back out: the calendrier, a semaine as a grid, a jour as a list.

The generator writes 1740 séances against 44 créneaux; rendering one semaine of that is a
handful of small tables joined to a hundred rows, so the reference tables — the matières,
the domaines, the créneaux, the séquences — are read whole once per request and joined in
Python. There are 12, 45, 44 and 120 of them; a join per séance would cost more.

Everything here returns the schemas of ``core.schemas``. The routers add HTTP and nothing
else.
"""

import datetime
import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Row, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.base import table_of
from core.models.calendar import Period, SchoolDay, SchoolHoliday, SchoolYear, Week
from core.models.curriculum import Domain, ProgramItem, Subject
from core.models.journal import JournalEntry
from core.models.level import Level
from core.models.planning import PlannedSession, PlannedSessionProgramItem
from core.models.sequence import Sequence, SequenceSession
from core.models.status import SessionStatus
from core.models.timetable import TimetableSlot
from core.models.weekday import Weekday
from core.schemas import (
    DayDetail,
    DayInWeek,
    DayRef,
    DomainRef,
    HolidayOut,
    PeriodRef,
    PeriodSummary,
    ProgramItemOut,
    ProgramItemRef,
    SequenceRef,
    SequenceStepRef,
    SessionDetail,
    SessionSummary,
    SlotSummary,
    SubjectRef,
    SubjectWithDomains,
    TodayOut,
    WeekCell,
    WeekDetail,
    WeekSummary,
    YearOverview,
)


@dataclass(frozen=True, slots=True)
class Reference:
    """The tables a rendered séance points at, read whole and keyed by their id."""

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


def _sessions_query() -> Select[Any]:
    """Select every séance column plus the date of its jour de classe."""
    sessions, days = table_of(PlannedSession), table_of(SchoolDay)
    return select(sessions, days.c.date).join(days, days.c.id == sessions.c.school_day_id)


def _common(row: Row, reference: Reference) -> dict[str, Any]:
    """Build the fields every rendering of a séance carries."""
    return {
        "id": row.id,
        "school_day_id": row.school_day_id,
        "date": row.date,
        "timetable_slot_id": row.timetable_slot_id,
        "level": Level(row.level),
        "title": row.title,
        "status": SessionStatus(row.status),
        "position": row.position,
        "subject": reference.subjects.get(row.subject_id),
        "domain": reference.domains.get(row.domain_id),
        "sequence": reference.sequences.get(row.sequence_id),
    }


def _summary(row: Row, reference: Reference) -> SessionSummary:
    """Render one séance the way the semaine grid draws it."""
    return SessionSummary(**_common(row, reference))


def _detail(row: Row, reference: Reference, items: list[ProgramItemRef]) -> SessionDetail:
    """Render one séance with everything it says."""
    return SessionDetail(
        **_common(row, reference),
        objectives=row.objectives,
        content=row.content,
        materials=row.materials,
        slot=reference.slots[row.timetable_slot_id],
        sequence_session=reference.steps.get(row.sequence_session_id),
        program_items=items,
    )


async def _program_items_of(
    session: AsyncSession, session_ids: list[uuid.UUID], reference: Reference
) -> dict[uuid.UUID, list[ProgramItemRef]]:
    """Read the items de programme those séances link, in the source's own order."""
    if not session_ids:
        return {}
    links, items = table_of(PlannedSessionProgramItem), table_of(ProgramItem)
    rows = (
        await session.execute(
            select(links.c.planned_session_id, items)
            .join(items, items.c.id == links.c.program_item_id)
            .where(links.c.planned_session_id.in_(session_ids))
            .order_by(items.c.source_order)
        )
    ).all()
    found: dict[uuid.UUID, list[ProgramItemRef]] = defaultdict(list)
    for row in rows:
        found[row.planned_session_id].append(program_item_ref(row, reference))
    return found


def program_item_ref(row: Row, reference: Reference) -> ProgramItemRef:
    """Render one item de programme as a séance names it."""
    return ProgramItemRef(
        id=row.id,
        level=Level(row.level),
        title=row.title,
        subject=reference.subjects.get(row.subject_id),
        domain=reference.domains.get(row.domain_id),
    )


def _period_ref(row: Row) -> PeriodRef:
    """Render the période a semaine or a jour belongs to."""
    return PeriodRef(
        id=row.period_id,
        code=row.period_code,
        label=row.period_label,
        starts_on=row.period_starts_on,
        ends_on=row.period_ends_on,
    )


def _week_with_period() -> Select[Any]:
    """Select a semaine together with its période, under names that do not collide."""
    weeks, periods = table_of(Week), table_of(Period)
    return select(
        weeks.c.id.label("week_id"),
        weeks.c.number,
        weeks.c.number_in_period,
        weeks.c.starts_on,
        weeks.c.ends_on,
        periods.c.id.label("period_id"),
        periods.c.code.label("period_code"),
        periods.c.label.label("period_label"),
        periods.c.starts_on.label("period_starts_on"),
        periods.c.ends_on.label("period_ends_on"),
    ).join(periods, periods.c.id == weeks.c.period_id)


async def load_week(session: AsyncSession, number: int) -> WeekDetail | None:
    """Render one semaine as the grid of §4.1, or ``None`` if the year has no such number.

    Every créneau of every jour comes back, whether or not a séance was planned in it: a
    jour chômé keeps its cells and its motif (ADR-0001), and a cell carries two séances
    where a per-niveau méthodo splits a commun créneau (ADR-0010).
    """
    weeks = table_of(Week)
    week = (
        await session.execute(_week_with_period().where(weeks.c.number == number))
    ).one_or_none()
    if week is None:
        return None

    first, last = (
        await session.execute(select(func.min(weeks.c.number), func.max(weeks.c.number)))
    ).one()

    school_days = table_of(SchoolDay)
    day_rows = (
        await session.execute(
            select(school_days)
            .where(school_days.c.week_id == week.week_id)
            .order_by(school_days.c.date)
        )
    ).all()

    reference = await load_reference(session)
    sessions = table_of(PlannedSession)
    session_rows = (
        await session.execute(
            _sessions_query()
            .where(sessions.c.school_day_id.in_([row.id for row in day_rows]))
            .order_by(sessions.c.position, sessions.c.level)
        )
    ).all()

    in_cell: dict[tuple[uuid.UUID, uuid.UUID], list[SessionSummary]] = defaultdict(list)
    for row in session_rows:
        in_cell[row.school_day_id, row.timetable_slot_id].append(_summary(row, reference))

    return WeekDetail(
        number=week.number,
        number_in_period=week.number_in_period,
        starts_on=week.starts_on,
        ends_on=week.ends_on,
        period=_period_ref(week),
        previous_week_number=week.number - 1 if week.number > first else None,
        next_week_number=week.number + 1 if week.number < last else None,
        days=[
            DayInWeek(
                id=day.id,
                date=day.date,
                day_of_week=Weekday(day.day_of_week),
                is_off=day.is_off,
                off_reason=day.off_reason,
                cells=[
                    WeekCell(slot=slot, sessions=in_cell.get((day.id, slot.id), []))
                    for slot in reference.slots_of(Weekday(day.day_of_week))
                ],
            )
            for day in day_rows
        ],
    )


async def load_day(session: AsyncSession, day: datetime.date) -> DayDetail | None:
    """Render one jour de classe and its séances, or ``None`` if the year has no such day."""
    school_days = table_of(SchoolDay)
    weeks = table_of(Week)
    found = (
        await session.execute(
            _week_with_period()
            .add_columns(school_days)
            .join(school_days, school_days.c.week_id == weeks.c.id)
            .where(school_days.c.date == day)
        )
    ).one_or_none()
    if found is None:
        return None

    previous_day = (
        await session.execute(select(func.max(school_days.c.date)).where(school_days.c.date < day))
    ).scalar_one()
    next_day = (
        await session.execute(select(func.min(school_days.c.date)).where(school_days.c.date > day))
    ).scalar_one()
    held = (
        await session.execute(
            select(func.count())
            .select_from(table_of(JournalEntry))
            .where(table_of(JournalEntry).c.school_day_id == found.id)
        )
    ).scalar_one()

    reference = await load_reference(session)
    sessions = table_of(PlannedSession)
    rows = (
        await session.execute(
            _sessions_query()
            .where(sessions.c.school_day_id == found.id)
            .order_by(sessions.c.position, sessions.c.level)
        )
    ).all()
    items = await _program_items_of(session, [row.id for row in rows], reference)

    return DayDetail(
        id=found.id,
        date=found.date,
        day_of_week=Weekday(found.day_of_week),
        is_off=found.is_off,
        off_reason=found.off_reason,
        week_number=found.number,
        number_in_period=found.number_in_period,
        period=_period_ref(found),
        previous_day=previous_day,
        next_day=next_day,
        has_journal=held > 0,
        sessions=[_detail(row, reference, items.get(row.id, [])) for row in rows],
    )


async def load_day_ref(session: AsyncSession, day: datetime.date) -> DayRef | None:
    """Render one jour de classe and where it sits, without touching its séances."""
    school_days, weeks, periods = table_of(SchoolDay), table_of(Week), table_of(Period)
    found = (
        await session.execute(
            select(school_days, weeks.c.number, weeks.c.number_in_period, periods.c.code)
            .join(weeks, weeks.c.id == school_days.c.week_id)
            .join(periods, periods.c.id == weeks.c.period_id)
            .where(school_days.c.date == day)
        )
    ).one_or_none()
    return None if found is None else _day_ref(found)


def _day_ref(row: Row) -> DayRef:
    """Render a jour de classe row already joined to its semaine and its période."""
    return DayRef(
        id=row.id,
        date=row.date,
        day_of_week=Weekday(row.day_of_week),
        is_off=row.is_off,
        off_reason=row.off_reason,
        week_number=row.number,
        number_in_period=row.number_in_period,
        period_code=row.code,
    )


async def next_school_day(session: AsyncSession, after: datetime.date) -> DayRef | None:
    """Find the first jour de classe on or after ``after`` that is actually taught.

    « Aujourd'hui » lands on a Wednesday, a weekend, the vacances and four jours chômés;
    this is what the home page opens instead (§7).
    """
    school_days, weeks, periods = table_of(SchoolDay), table_of(Week), table_of(Period)
    found = (
        await session.execute(
            select(school_days, weeks.c.number, weeks.c.number_in_period, periods.c.code)
            .join(weeks, weeks.c.id == school_days.c.week_id)
            .join(periods, periods.c.id == weeks.c.period_id)
            .where(school_days.c.date >= after, school_days.c.is_off.is_(False))
            .order_by(school_days.c.date)
            .limit(1)
        )
    ).one_or_none()
    return None if found is None else _day_ref(found)


async def load_session(session: AsyncSession, identifier: uuid.UUID) -> SessionDetail | None:
    """Render one séance, or ``None`` if there is no such séance."""
    sessions = table_of(PlannedSession)
    row = (
        await session.execute(_sessions_query().where(sessions.c.id == identifier))
    ).one_or_none()
    if row is None:
        return None
    reference = await load_reference(session)
    items = await _program_items_of(session, [row.id], reference)
    return _detail(row, reference, items.get(row.id, []))


async def sessions_of_program_item(
    session: AsyncSession, item_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[SessionSummary], int]:
    """List the séances linking one item de programme — §7 écran 4's « voir les séances liées ».

    Ordered by the day they fall on: a rituel links the same items all year (ADR-0015), so
    this list is long by design and is paged.
    """
    links, sessions, days = (
        table_of(PlannedSessionProgramItem),
        table_of(PlannedSession),
        table_of(SchoolDay),
    )
    linked = select(links.c.planned_session_id).where(links.c.program_item_id == item_id)
    total = (
        await session.execute(
            select(func.count()).select_from(links).where(links.c.program_item_id == item_id)
        )
    ).scalar_one()
    rows = (
        await session.execute(
            _sessions_query()
            .where(sessions.c.id.in_(linked))
            .order_by(days.c.date, sessions.c.position, sessions.c.level)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    reference = await load_reference(session)
    return [_summary(row, reference) for row in rows], total


async def load_year(session: AsyncSession, on: datetime.date) -> YearOverview | None:
    """Render the whole année scolaire — §7 écran 1 — or ``None`` if none is seeded.

    Each semaine reports how many of its jours are chômés, so the year view can show the
    hole in P4-S6 without opening the semaine.
    """
    years, periods, weeks, holidays, days = (
        table_of(SchoolYear),
        table_of(Period),
        table_of(Week),
        table_of(SchoolHoliday),
        table_of(SchoolDay),
    )
    year = (await session.execute(select(years).limit(1))).one_or_none()
    if year is None:
        return None

    off = {
        row.week_id: row.days_off
        for row in (
            await session.execute(
                select(days.c.week_id, func.count().label("days_off"))
                .where(days.c.is_off.is_(True))
                .group_by(days.c.week_id)
            )
        ).all()
    }
    week_rows = (await session.execute(select(weeks).order_by(weeks.c.number))).all()
    by_period: dict[uuid.UUID, list[WeekSummary]] = defaultdict(list)
    current: int | None = None
    for row in week_rows:
        by_period[row.period_id].append(
            WeekSummary(
                number=row.number,
                number_in_period=row.number_in_period,
                starts_on=row.starts_on,
                ends_on=row.ends_on,
                days_off=off.get(row.id, 0),
            )
        )
        if row.starts_on <= on <= row.ends_on:
            current = row.number

    return YearOverview(
        label=year.label,
        zone=year.zone,
        starts_on=year.starts_on,
        ends_on=year.ends_on,
        today=on,
        current_week_number=current,
        periods=[
            PeriodSummary(
                id=row.id,
                code=row.code,
                label=row.label,
                starts_on=row.starts_on,
                ends_on=row.ends_on,
                weeks=by_period.get(row.id, []),
            )
            for row in (await session.execute(select(periods).order_by(periods.c.code))).all()
        ],
        holidays=[
            HolidayOut(label=row.label, starts_on=row.starts_on, ends_on=row.ends_on)
            for row in (
                await session.execute(select(holidays).order_by(holidays.c.starts_on))
            ).all()
        ],
    )


async def load_today(session: AsyncSession, on: datetime.date) -> TodayOut:
    """Say where the teacher stands: today's jour de classe, and the next one to open."""
    day = await load_day_ref(session, on)
    return TodayOut(
        date=on,
        school_day=day if day is not None and not day.is_off else None,
        next_school_day=await next_school_day(session, on),
    )


async def load_timetable(session: AsyncSession) -> list[SlotSummary]:
    """Read the 44 créneaux of the gabarit, in the order the grid prints them."""
    reference = await load_reference(session)
    return sorted(
        reference.slots.values(),
        key=lambda slot: (slot.day_of_week, slot.starts_at, slot.level.value),
    )


async def load_subjects(session: AsyncSession) -> list[SubjectWithDomains]:
    """Read the matières with the domaines under them — the programme filters, and the colours."""
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


@dataclass(frozen=True, slots=True)
class ProgramQuery:
    """What the programme browser is asking for — §7 écran 4's filters and its search."""

    level: Level | None = None
    subject: str | None = None
    domain: str | None = None
    text: str | None = None
    needs_review: bool | None = None
    limit: int = 50
    offset: int = 0


async def search_program_items(
    session: AsyncSession, query: ProgramQuery
) -> tuple[list[ProgramItemOut], int]:
    """Filter and search the items de programme, and say how many matched in all.

    The search is Postgres': ``websearch_to_tsquery('french', …)`` against the generated
    ``search_vector`` column and its GIN index, never an ``ILIKE`` — which is what lets
    « fractions » find « fraction » and what §6 asks for. Results are ranked when there is
    a search and ordered by ``source_order`` when there is not, because the order the
    programme prints its blocks in is the only order they have (their id is a random UUID).
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
    if query.needs_review is not None:
        filters.append(items.c.needs_review.is_(query.needs_review))

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
    return [_program_item_out(row, reference) for row in rows], total


def _program_item_out(row: Row, reference: Reference) -> ProgramItemOut:
    """Render one item de programme with everything the browser shows of it."""
    return ProgramItemOut(
        **program_item_ref(row, reference).model_dump(),
        description=row.description,
        source_file=row.source_file,
        source_page=row.source_page,
        source_order=row.source_order,
        needs_review=row.needs_review,
    )


async def load_program_item(session: AsyncSession, identifier: uuid.UUID) -> ProgramItemOut | None:
    """Read one item de programme, or ``None`` if there is no such item."""
    items = table_of(ProgramItem)
    row = (await session.execute(select(items).where(items.c.id == identifier))).one_or_none()
    if row is None:
        return None
    return _program_item_out(row, await load_reference(session))
