"""SQLModel models.

Every table model MUST be imported here: Alembic's autogenerate only sees the
tables registered on ``SQLModel.metadata`` at import time (see ``alembic/env.py``).
"""

from .app_setting import AppSetting
from .calendar import Period, SchoolDay, SchoolHoliday, SchoolYear, Week
from .curriculum import Domain, ProgramItem, Subject
from .journal import JournalEntry, JournalRevision
from .level import Level
from .planning import PlannedSession, PlannedSessionProgramItem
from .sequence import Sequence, SequenceSession
from .status import RevisionStatus, SessionStatus
from .timetable import TimetableSlot
from .user import User
from .weekday import Weekday

__all__ = [
    "AppSetting",
    "Domain",
    "JournalEntry",
    "JournalRevision",
    "Level",
    "Period",
    "PlannedSession",
    "PlannedSessionProgramItem",
    "ProgramItem",
    "RevisionStatus",
    "SchoolDay",
    "SchoolHoliday",
    "SchoolYear",
    "Sequence",
    "SequenceSession",
    "SessionStatus",
    "Subject",
    "TimetableSlot",
    "User",
    "Week",
    "Weekday",
]
