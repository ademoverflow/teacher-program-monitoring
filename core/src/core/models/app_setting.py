"""Application settings the teacher can change: the alternation choices, the AI model.

One row per setting, keyed by name.
"""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from core.models.base import created_at_column, updated_at_column, uuid_primary_key


class AppSetting(SQLModel, table=True):
    """One key/value setting. ``value`` is JSON so a setting can hold structure."""

    __tablename__: ClassVar[str] = "app_settings"

    id: uuid.UUID = uuid_primary_key()
    created_at: datetime = created_at_column()
    updated_at: datetime = updated_at_column()

    key: str = Field(sa_column=Column(String, nullable=False, unique=True))
    value: Any | None = Field(sa_column=Column(JSONB, nullable=True), default=None)
    label: str | None = Field(sa_column=Column(Text, nullable=True), default=None)
