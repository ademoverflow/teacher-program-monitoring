from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from core import __version__
from core.routers import (
    calendar_router,
    days_router,
    generation_router,
    health_router,
    journal_router,
    program_items_router,
    sessions_router,
    settings_router,
    subjects_router,
    timetable_router,
    weeks_router,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator:
    """Lifespan of the application.

    Args:
        app (FastAPI): FastAPI application instance.

    Returns:
        AsyncIterator: Async context manager for lifespan.

    """
    config = Config("core/src/core/alembic/alembic.ini")
    command.upgrade(config, "head")
    yield


app = FastAPI(
    title="Teacher Program Monitoring",
    description="Teacher Program Monitoring Core API",
    version=__version__,
    lifespan=lifespan,
)

# Every router is mounted under /api: the webapp reaches the API through the Vite
# proxy (`/api` -> core), so every browser request is same-origin and no CORS
# middleware is needed.
API_PREFIX = "/api"

for router in (
    health_router,
    calendar_router,
    timetable_router,
    subjects_router,
    weeks_router,
    days_router,
    sessions_router,
    journal_router,
    program_items_router,
    generation_router,
    settings_router,
):
    app.include_router(router, prefix=API_PREFIX)
