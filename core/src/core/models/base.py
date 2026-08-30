"""Shared column patterns for every table.

Every table follows ``models/user.py``: a UUID primary key defaulted by Postgres and
server-side ``created_at``/``updated_at``. These are functions rather than a shared
base class because a SQLAlchemy ``Column`` can only ever be attached to one table.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import UUID, CheckConstraint, Column, DateTime, ForeignKey, text
from sqlmodel import Field


def uuid_primary_key() -> Any:  # noqa: ANN401
    """Build a UUID primary key, defaulted by Postgres with ``gen_random_uuid()``."""
    return Field(
        sa_column=Column(UUID, primary_key=True, server_default=text("gen_random_uuid()")),
        default_factory=uuid.uuid4,
    )


def created_at_column() -> Any:  # noqa: ANN401
    """Creation timestamp, set by Postgres."""
    return Field(
        sa_column=Column(DateTime(timezone=True), server_default=text("now()"), nullable=False),
        default_factory=datetime.now,
    )


def updated_at_column() -> Any:  # noqa: ANN401
    """Last-write timestamp, maintained by Postgres."""
    return Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=text("now()"),
            onupdate=text("now()"),
            nullable=False,
        ),
        default_factory=datetime.now,
    )


def reference(target: str, *, nullable: bool = False, ondelete: str = "CASCADE") -> Any:  # noqa: ANN401
    """Build a UUID foreign key to ``target`` (``"table.column"``), indexed for joins."""
    return Field(
        sa_column=Column(
            UUID,
            ForeignKey(target, ondelete=ondelete),
            nullable=nullable,
            index=True,
        ),
        default=None,
    )


def enum_check(table: str, column: str, values: type[StrEnum]) -> CheckConstraint:
    """Constrain a text column to the values of ``values`` (see ADR-0004)."""
    allowed = ", ".join(f"'{member.value}'" for member in values)
    return CheckConstraint(f"{column} IN ({allowed})", name=f"ck_{table}_{column}")
