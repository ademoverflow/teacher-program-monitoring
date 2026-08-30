"""The weekly timetable template — the gabarit of MASTER-PROMPT.md §4.1.

The 44 rows repeat identically every week of the year and are immutable (§10).
Six of them carry an ``alternation_group`` instead of a matière: see ADR-0002.
"""

import uuid
from datetime import datetime, time
from typing import ClassVar

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Integer,
    SmallInteger,
    String,
    Time,
    UniqueConstraint,
    text,
)
from sqlmodel import Field, SQLModel

from core.models.base import (
    created_at_column,
    enum_check,
    reference,
    updated_at_column,
    uuid_primary_key,
)
from core.models.level import Level


class TimetableSlot(SQLModel, table=True):
    """One créneau: a day, a time range, and what is taught in it.

    ``duration_minutes`` is the teaching time printed in the cell and is *not*
    always ``ends_at - starts_at`` — see ADR-0003.
    """

    __tablename__: ClassVar[str] = "timetable_slots"
    __table_args__: ClassVar[tuple] = (
        UniqueConstraint(
            "day_of_week", "starts_at", "level", name="uq_timetable_slots_day_start_level"
        ),
        enum_check("timetable_slots", "level", Level),
        CheckConstraint(
            "is_alternating = (alternation_group IS NOT NULL)",
            name="ck_timetable_slots_alternation",
        ),
        CheckConstraint("starts_at < ends_at", name="ck_timetable_slots_time_range"),
    )

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime = created_at_column()
    updated_at: datetime = updated_at_column()

    day_of_week: int = Field(sa_column=Column(SmallInteger, nullable=False))
    starts_at: time = Field(sa_column=Column(Time, nullable=False))
    ends_at: time = Field(sa_column=Column(Time, nullable=False))
    duration_minutes: int = Field(sa_column=Column(Integer, nullable=False))
    label: str = Field(sa_column=Column(String, nullable=False))
    subject_id: uuid.UUID | None = reference("subjects.id", nullable=True, ondelete="SET NULL")
    domain_id: uuid.UUID | None = reference("domains.id", nullable=True, ondelete="SET NULL")
    level: Level = Field(
        sa_column=Column(String, nullable=False, server_default=text("'commun'")),
        default=Level.COMMUN,
    )
    is_alternating: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default=text("false")), default=False
    )
    alternation_group: str | None = Field(sa_column=Column(String, nullable=True), default=None)
