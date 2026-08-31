from .app_settings import settings_router
from .calendar import calendar_router
from .days import days_router
from .generation import generation_router
from .health import health_router
from .journal import journal_router
from .program_items import program_items_router
from .sessions import sessions_router
from .subjects import subjects_router
from .timetable import timetable_router
from .weeks import weeks_router

__all__ = [
    "calendar_router",
    "days_router",
    "generation_router",
    "health_router",
    "journal_router",
    "program_items_router",
    "sessions_router",
    "settings_router",
    "subjects_router",
    "timetable_router",
    "weeks_router",
]
