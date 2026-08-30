"""Séquences from the teaching methods, and the séances they lay out.

Filled from the pedagogical PDFs in Phase 2.
"""

import uuid
from datetime import datetime
from typing import ClassVar

from sqlalchemy import Boolean, Column, Integer, String, Text, UniqueConstraint, text
from sqlmodel import Field, SQLModel

from core.models.base import (
    created_at_column,
    enum_check,
    reference,
    updated_at_column,
    uuid_primary_key,
)
from core.models.level import Level


class Sequence(SQLModel, table=True):
    """A run of séances from one teaching method covering one notion."""

    __tablename__: ClassVar[str] = "sequences"
    __table_args__: ClassVar[tuple] = (
        UniqueConstraint("method", "number", name="uq_sequences_method_number"),
        enum_check("sequences", "level", Level),
    )

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime = created_at_column()
    updated_at: datetime = updated_at_column()

    method: str = Field(sa_column=Column(String, nullable=False))
    level: Level = Field(sa_column=Column(String, nullable=False))
    number: int = Field(sa_column=Column(Integer, nullable=False))
    title: str = Field(sa_column=Column(Text, nullable=False))
    objectives: str | None = Field(sa_column=Column(Text, nullable=True), default=None)
    period_code: str | None = Field(sa_column=Column(String, nullable=True), default=None)
    subject_id: uuid.UUID | None = reference("subjects.id", nullable=True, ondelete="SET NULL")
    # Set where the méthodo says which domaine a séquence belongs to — the RETZ CM1
    # progression colour-codes grammaire against conjugaison, and the EDT teaches them
    # in different créneaux. Null where the source does not say (see the ADR).
    domain_id: uuid.UUID | None = reference("domains.id", nullable=True, ondelete="SET NULL")
    needs_review: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default=text("false")), default=False
    )


class SequenceSession(SQLModel, table=True):
    """One séance of a séquence, as the method lays it out."""

    __tablename__: ClassVar[str] = "sequence_sessions"
    __table_args__: ClassVar[tuple] = (
        UniqueConstraint("sequence_id", "number", name="uq_sequence_sessions_sequence_number"),
    )

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime = created_at_column()
    updated_at: datetime = updated_at_column()

    sequence_id: uuid.UUID = reference("sequences.id")
    number: int = Field(sa_column=Column(Integer, nullable=False))
    title: str = Field(sa_column=Column(Text, nullable=False))
    content: str | None = Field(sa_column=Column(Text, nullable=True), default=None)
    duration_minutes: int | None = Field(sa_column=Column(Integer, nullable=True), default=None)
    materials: str | None = Field(sa_column=Column(Text, nullable=True), default=None)
    needs_review: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default=text("false")), default=False
    )
