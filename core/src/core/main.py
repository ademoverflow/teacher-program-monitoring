from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from core import __version__
from core.routers import health_router


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

app.include_router(health_router, prefix=API_PREFIX)
