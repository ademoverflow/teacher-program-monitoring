"""SQLModel models.

Every table model MUST be imported here: Alembic's autogenerate only sees the
tables registered on ``SQLModel.metadata`` at import time (see ``alembic/env.py``).
"""

from .user import User

__all__ = [
    "User",
]
