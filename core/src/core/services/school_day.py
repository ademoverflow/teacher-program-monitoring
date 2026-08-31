"""Finding a jour de classe, and saying where a new row goes inside one.

``school_calendar.py`` builds the jours de classe from the seeds; this is the other side —
what the writers need from one. Both the cahier journal and the séances anchor on a date and
both append at the end of the day, so the lookup, the sentence said when a date is not a jour
de classe, and the next rank live here rather than twice.
"""

import datetime
import uuid

from sqlalchemy import Row, Table, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.base import table_of
from core.models.calendar import SchoolDay


def not_a_school_day(day: datetime.date) -> str:
    """Say, in French, that the year has no jour de classe on this date.

    There is never class on a Wednesday, at the weekend or during the vacances (§2), and
    those dates have no row at all — unlike the four jours chômés, which do (ADR-0001).
    """
    return f"{day.isoformat()} n'est pas un jour de classe"


async def find_school_day(session: AsyncSession, day: datetime.date) -> Row | None:
    """Read the jour de classe on that date, or ``None`` if there is none."""
    days = table_of(SchoolDay)
    return (await session.execute(select(days).where(days.c.date == day))).one_or_none()


async def next_position(session: AsyncSession, table: Table, day_id: uuid.UUID) -> int:
    """Give the rank a new row takes at the end of its day.

    The end, not the start: a séance and a ligne de cahier journal are both read in the
    order of the day, and one that landed first would rewrite the morning.
    """
    last = (
        await session.execute(
            select(func.max(table.c.position)).where(table.c.school_day_id == day_id)
        )
    ).scalar_one()
    return (last or 0) + 1
