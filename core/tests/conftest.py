"""The database every test that needs one shares, and the client the router tests drive.

Phase 4 is almost entirely database, so the suite runs against a real Postgres rather than
a mock: CI starts one as a service (ADR-0018), and locally the core container's own
database answers. Where none does, the fixtures skip and the rest of the suite still runs.

Every test works inside a transaction that is rolled back, so the database is left exactly
as the test found it — including when an endpoint commits, which is what
``join_transaction_mode="create_savepoint"`` is for (ADR-0019).
"""

import asyncio
import subprocess
import sys
from collections.abc import AsyncIterator
from datetime import date
from pathlib import Path

import pytest
from core.database import async_db_url, get_session
from core.main import app
from core.services.planning.writer import generate_year
from core.services.seeding import seed_database
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

# core/tests/conftest.py -> the repository root, which is what alembic.ini's relative
# paths are anchored to.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPOSITORY_ROOT / "core/src/core/alembic/alembic.ini"

# Before the pupils' first day, so no jour de classe is in the past and the whole year is
# written. A fixture that depended on the day it ran on would generate a different year in
# June than in September.
BEFORE_THE_YEAR = date(2026, 8, 31)


def _migrate() -> None:
    """Bring the test database up to ``head``.

    Run out of process because Alembic drives a synchronous engine and configures logging
    globally; inside pytest that fights the event loop the async fixtures own.
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), "upgrade", "head"],
        check=False,
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        pytest.fail(f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}")


async def _fill() -> None:
    """Load the seeds and generate the year, so the read endpoints have one to read.

    Both are idempotent (§8 Phase 1 and Phase 3), so this is a no-op against the core
    container's database, which ``make seed`` has already filled, and it is what brings
    CI's blank Postgres up to the same state.
    """
    engine = create_async_engine(async_db_url, poolclass=NullPool)
    try:
        async with AsyncSession(engine) as session:
            await seed_database(session)
            await generate_year(session, reference_date=BEFORE_THE_YEAR)
            await session.commit()
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def database() -> str:
    """Skip unless a Postgres answers, and hand back a migrated, filled database.

    Session-scoped: the migration and the fill happen once for the whole suite.
    """

    async def probe() -> None:
        engine = create_async_engine(async_db_url, poolclass=NullPool)
        try:
            connection = await engine.connect()
            await connection.close()
        finally:
            await engine.dispose()

    try:
        asyncio.run(probe())
    except Exception as error:  # noqa: BLE001 - anything at all here means "no database"
        pytest.skip(f"no database reachable: {error}")

    _migrate()
    asyncio.run(_fill())
    return async_db_url


@pytest.fixture
async def session(database: str) -> AsyncIterator[AsyncSession]:
    """Open a session whose work is always rolled back.

    The session is bound to a connection whose outer transaction the fixture owns, so a
    ``commit()`` inside an endpoint only releases a savepoint and the rollback still undoes
    everything. The engine is built per test and pools nothing: pytest-asyncio gives each
    test its own event loop, and an asyncpg connection cannot move between loops.
    """
    engine = create_async_engine(database, poolclass=NullPool)
    connection = await engine.connect()
    transaction = await connection.begin()
    open_session = AsyncSession(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    try:
        yield open_session
    finally:
        await open_session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Drive the app over ASGI, on the test's own event loop and inside its transaction.

    ``TestClient`` runs the app from another thread's event loop, which an asyncpg
    connection cannot be shared with, so the router tests speak to the app through httpx
    directly (ADR-0019). The lifespan is not entered: migrating is the fixture's job here,
    not the app's.
    """
    app.dependency_overrides[get_session] = lambda: session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as open_client:
        yield open_client
    app.dependency_overrides.clear()
