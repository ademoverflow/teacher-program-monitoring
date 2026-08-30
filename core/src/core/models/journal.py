"""The cahier journal: what actually happened on a day, and the AI's proposals to change it.

A cahier journal starts as a copy of the day's séances and then lives its own life —
it is never overwritten by a regeneration of the programmation (§10).
"""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import Column, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from core.models.base import (
    created_at_column,
    enum_check,
    enum_default,
    reference,
    updated_at_column,
    uuid_primary_key,
)
from core.models.status import RevisionStatus


class JournalEntry(SQLModel, table=True):
    """One line of a day's cahier journal: discipline and duration, objectives, bilan."""

    __tablename__: ClassVar[str] = "journal_entries"

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime = created_at_column()
    updated_at: datetime = updated_at_column()

    school_day_id: uuid.UUID = reference("school_days.id")
    planned_session_id: uuid.UUID | None = reference(
        "planned_sessions.id", nullable=True, ondelete="SET NULL"
    )
    discipline: str = Field(sa_column=Column(String, nullable=False))
    duration_minutes: int | None = Field(sa_column=Column(Integer, nullable=True), default=None)
    objectives: str | None = Field(sa_column=Column(Text, nullable=True), default=None)
    bilan: str | None = Field(sa_column=Column(Text, nullable=True), default=None)
    notes: str | None = Field(sa_column=Column(Text, nullable=True), default=None)
    position: int = Field(sa_column=Column(Integer, nullable=False, server_default=text("0")))


class JournalRevision(SQLModel, table=True):
    """A change to a day's cahier journal proposed by the AI, and what became of it."""

    __tablename__: ClassVar[str] = "journal_revisions"
    __table_args__: ClassVar[tuple] = (enum_check("journal_revisions", "status", RevisionStatus),)

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime = created_at_column()
    updated_at: datetime = updated_at_column()

    school_day_id: uuid.UUID = reference("school_days.id")
    feedback: str = Field(sa_column=Column(Text, nullable=False))
    snapshot_before: Any | None = Field(sa_column=Column(JSONB, nullable=True), default=None)
    snapshot_after: Any | None = Field(sa_column=Column(JSONB, nullable=True), default=None)
    summary: str | None = Field(sa_column=Column(Text, nullable=True), default=None)
    status: RevisionStatus = Field(
        sa_column=Column(
            String, nullable=False, server_default=enum_default(RevisionStatus.PROPOSEE)
        ),
        default=RevisionStatus.PROPOSEE,
    )
    model: str | None = Field(sa_column=Column(String, nullable=True), default=None)
    settled_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True), default=None
    )
