from .calendar import calendar_router
from .health import health_router
from .subjects import subjects_router
from .timetable import timetable_router

__all__ = [
    "calendar_router",
    "health_router",
    "subjects_router",
    "timetable_router",
]
