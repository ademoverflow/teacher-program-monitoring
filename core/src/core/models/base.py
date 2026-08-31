"""Shared column patterns for every table, and the way to reach a table itself.

Every table follows ``models/user.py``: a UUID primary key defaulted by Postgres and
server-side ``created_at``/``updated_at``. These are functions rather than a shared
base class because a SQLAlchemy ``Column`` can only ever be attached to one table.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import UUID, CheckConstraint, Column, DateTime, ForeignKey, Table, text
from sqlmodel import Field, SQLModel


def table_of(model: type[SQLModel]) -> Table:
    """Return the SQLAlchemy table behind a SQLModel table class.

    The bulk writers — the seed loader and the year generator — build their statements
    on the table rather than the mapped class, and both reach it through here.
    """
    return SQLModel.metadata.tables[str(model.__tablename__)]


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


def _sql_literal(member: Enum) -> str:
    """Render an enum member as the SQL literal stored for it."""
    return str(member.value) if isinstance(member.value, int) else f"'{member.value}'"


def enum_check(table: str, column: str, values: type[Enum]) -> CheckConstraint:
    """Constrain a column to the values of ``values`` (see ADR-0004).

    Generated from the enum so the constraint and the Python type cannot drift.
    """
    allowed = ", ".join(_sql_literal(member) for member in values)
    return CheckConstraint(f"{column} IN ({allowed})", name=f"ck_{table}_{column}")


def enum_default(member: Enum) -> Any:  # noqa: ANN401
    """Build the server-side default for an enum column, taken from the enum itself.

    Spelling the literal here rather than at each call site keeps the default in
    step with ``enum_check`` when a value is renamed.
    """
    return text(_sql_literal(member))
