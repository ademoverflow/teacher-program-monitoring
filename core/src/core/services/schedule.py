"""Reading the year back out: the calendrier, a semaine as a grid, a jour as a list.

Everything here returns the schemas of ``core.schemas`` (ADR-0022); the routers add HTTP and
nothing else. The small tables a séance points at come from ``services/reference.py``, read
whole once per request and joined in Python.
"""

import datetime
import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import Row, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.base import table_of
from core.models.calendar import Period, SchoolDay, SchoolHoliday, SchoolYear, Week
from core.models.curriculum import ProgramItem
from core.models.journal import JournalEntry
from core.models.level import Level
from core.models.planning import PlannedSession, PlannedSessionProgramItem
from core.models.status import SessionStatus
from core.models.weekday import Weekday
from core.schemas import (
    DayDetail,
    DayInWeek,
    DayRef,
    HolidayOut,
    PeriodRef,
    PeriodSummary,
    PlannedSessionDetail,
    PlannedSessionSummary,
    ProgramItemRef,
    TodayOut,
    WeekCell,
    WeekDetail,
    WeekSummary,
    YearOverview,
)
from core.services.reference import Reference, load_reference, program_item_ref

# --------------------------------------------------------------------------------------
# Séances
# --------------------------------------------------------------------------------------


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


def _summary(row: Row, reference: Reference) -> PlannedSessionSummary:
    """Render one séance the way the semaine grid draws it."""
    return PlannedSessionSummary(**_common(row, reference))


def _detail(row: Row, reference: Reference, items: list[ProgramItemRef]) -> PlannedSessionDetail:
    """Render one séance with everything it says."""
    return PlannedSessionDetail(
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


async def load_planned_session(
    session: AsyncSession, identifier: uuid.UUID
) -> PlannedSessionDetail | None:
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


async def planned_sessions_of_program_item(
    session: AsyncSession, item_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[PlannedSessionSummary], int]:
    """List the séances linking one item de programme — §7 écran 4's « séances liées ».

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


# --------------------------------------------------------------------------------------
# The semaine and the jour
# --------------------------------------------------------------------------------------


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

    in_cell: dict[tuple[uuid.UUID, uuid.UUID], list[PlannedSessionSummary]] = defaultdict(list)
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


def _day_in_the_year() -> Select[Any]:
    """Select a jour de classe together with its semaine and its période."""
    school_days, weeks = table_of(SchoolDay), table_of(Week)
    return (
        _week_with_period()
        .add_columns(school_days)
        .join(school_days, school_days.c.week_id == weeks.c.id)
    )


async def load_day(session: AsyncSession, day: datetime.date) -> DayDetail | None:
    """Render one jour de classe and its séances, or ``None`` if the year has no such day."""
    school_days = table_of(SchoolDay)
    found = (
        await session.execute(_day_in_the_year().where(school_days.c.date == day))
    ).one_or_none()
    if found is None:
        return None

    previous_day = (
        await session.execute(select(func.max(school_days.c.date)).where(school_days.c.date < day))
    ).scalar_one()
    next_day = (
        await session.execute(select(func.min(school_days.c.date)).where(school_days.c.date > day))
    ).scalar_one()
    entries = table_of(JournalEntry)
    held = (
        await session.execute(
            select(func.count()).select_from(entries).where(entries.c.school_day_id == found.id)
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
        period_code=row.period_code,
    )


async def load_day_ref(session: AsyncSession, day: datetime.date) -> DayRef | None:
    """Render one jour de classe and where it sits, without touching its séances."""
    school_days = table_of(SchoolDay)
    found = (
        await session.execute(_day_in_the_year().where(school_days.c.date == day))
    ).one_or_none()
    return None if found is None else _day_ref(found)


async def next_taught_day(session: AsyncSession, after: datetime.date) -> DayRef | None:
    """Find the first jour de classe on or after ``after`` that is actually taught.

    « Aujourd'hui » lands on a Wednesday, a weekend, the vacances and four jours chômés;
    this is what the home page opens instead (§7).
    """
    school_days = table_of(SchoolDay)
    found = (
        await session.execute(
            _day_in_the_year()
            .where(school_days.c.date >= after, school_days.c.is_off.is_(False))
            .order_by(school_days.c.date)
            .limit(1)
        )
    ).one_or_none()
    return None if found is None else _day_ref(found)


# --------------------------------------------------------------------------------------
# The year
# --------------------------------------------------------------------------------------


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
    """Say where the teacher stands: today's jour de classe, and the one to open.

    A jour chômé is still a jour de classe (ADR-0001), so it comes back in ``school_day``
    with its motif; ``next_taught_day`` is then the following taught day. On an ordinary
    taught day the two are the same date, which is what makes « Aujourd'hui » one lookup.
    """
    return TodayOut(
        date=on,
        school_day=await load_day_ref(session, on),
        next_taught_day=await next_taught_day(session, on),
    )
