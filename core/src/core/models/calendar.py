"""The year's skeleton: the school year, its périodes, vacances, semaines and jours de classe.

Rows here are derived from ``core/seed/calendar.json`` by
``core.services.school_calendar`` — see ADR-0001 for which days get a row.
"""

import datetime
import uuid
from typing import ClassVar

from sqlalchemy import Boolean, Column, Date, Integer, SmallInteger, String, UniqueConstraint, text
from sqlmodel import Field, SQLModel

from core.models.base import created_at_column, reference, updated_at_column, uuid_primary_key


class SchoolYear(SQLModel, table=True):
    """A school year, with the education zone whose holiday calendar it follows."""

    __tablename__: ClassVar[str] = "school_years"

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime.datetime = created_at_column()
    updated_at: datetime.datetime = updated_at_column()

    label: str = Field(sa_column=Column(String, nullable=False, unique=True))
    zone: str = Field(sa_column=Column(String, nullable=False))
    starts_on: datetime.date = Field(sa_column=Column(Date, nullable=False))
    ends_on: datetime.date = Field(sa_column=Column(Date, nullable=False))


class Period(SQLModel, table=True):
    """A période: a block of class between two stretches of vacances."""

    __tablename__: ClassVar[str] = "periods"
    __table_args__: ClassVar[tuple] = (
        UniqueConstraint("school_year_id", "code", name="uq_periods_year_code"),
    )

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime.datetime = created_at_column()
    updated_at: datetime.datetime = updated_at_column()

    school_year_id: uuid.UUID = reference("school_years.id")
    code: str = Field(sa_column=Column(String, nullable=False))
    label: str = Field(sa_column=Column(String, nullable=False))
    starts_on: datetime.date = Field(sa_column=Column(Date, nullable=False))
    ends_on: datetime.date = Field(sa_column=Column(Date, nullable=False))


class SchoolHoliday(SQLModel, table=True):
    """A stretch of vacances. ``ends_on`` is open for the summer holidays."""

    __tablename__: ClassVar[str] = "school_holidays"
    __table_args__: ClassVar[tuple] = (
        UniqueConstraint("school_year_id", "label", name="uq_school_holidays_year_label"),
    )

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime.datetime = created_at_column()
    updated_at: datetime.datetime = updated_at_column()

    school_year_id: uuid.UUID = reference("school_years.id")
    label: str = Field(sa_column=Column(String, nullable=False))
    starts_on: datetime.date = Field(sa_column=Column(Date, nullable=False))
    ends_on: datetime.date | None = Field(sa_column=Column(Date, nullable=True), default=None)


class Week(SQLModel, table=True):
    """A semaine de classe, numbered both globally (S1…S36) and within its période."""

    __tablename__: ClassVar[str] = "weeks"
    __table_args__: ClassVar[tuple] = (
        UniqueConstraint("school_year_id", "number", name="uq_weeks_year_number"),
        UniqueConstraint("school_year_id", "starts_on", name="uq_weeks_year_starts_on"),
    )

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime.datetime = created_at_column()
    updated_at: datetime.datetime = updated_at_column()

    school_year_id: uuid.UUID = reference("school_years.id")
    period_id: uuid.UUID = reference("periods.id")
    number: int = Field(sa_column=Column(Integer, nullable=False))
    number_in_period: int = Field(sa_column=Column(Integer, nullable=False))
    starts_on: datetime.date = Field(sa_column=Column(Date, nullable=False))
    ends_on: datetime.date = Field(sa_column=Column(Date, nullable=False))


class SchoolDay(SQLModel, table=True):
    """A jour de classe. ``is_off`` marks the ones lost to a public holiday or a bridge."""

    __tablename__: ClassVar[str] = "school_days"

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime.datetime = created_at_column()
    updated_at: datetime.datetime = updated_at_column()

    week_id: uuid.UUID = reference("weeks.id")
    date: datetime.date = Field(sa_column=Column(Date, nullable=False, unique=True))
    day_of_week: int = Field(sa_column=Column(SmallInteger, nullable=False))
    is_off: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default=text("false")), default=False
    )
    off_reason: str | None = Field(sa_column=Column(String, nullable=True), default=None)
