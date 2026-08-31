"""Launching the generation, and asking before it overwrites a période already under way.

These tests need Postgres — ``conftest.py`` skips them where none answers.
"""

from collections.abc import Iterator
from datetime import date

import pytest
from core.clock import today
from core.main import app
from httpx import AsyncClient

from tests.expected import (
    CONFLICT,
    DAYS_OFF,
    OK,
    PERIODS,
    PLANNED_SESSIONS,
    PROGRAM_LINKS,
    TAUGHT_DAYS,
)

BEFORE_THE_YEAR = date(2026, 8, 31)
MIDYEAR = date(2027, 1, 11)
A_MONDAY = date(2026, 9, 7)
# What Phase 3 leaves behind: nothing the generator got wrong, eleven lines the calendar
# does not afford, and one the source does not say (ADR-0011, ADR-0017).
CALENDAR_PROBLEMS = 11
SOURCE_PROBLEMS = 1
P1_SESSIONS = 338


@pytest.fixture
def _before_the_year() -> Iterator[None]:
    """Answer as if the pupils had not come back yet, so no jour is in the past."""
    app.dependency_overrides[today] = lambda: BEFORE_THE_YEAR
    yield
    app.dependency_overrides.pop(today, None)


@pytest.mark.usefixtures("_before_the_year")
async def test_no_periode_is_under_way_before_the_year_starts(client: AsyncClient) -> None:
    """§7 écran 5 only asks before overwriting; on 31/08/2026 there is nothing to overwrite."""
    response = await client.get("/api/generation")

    assert response.status_code == OK
    body = response.json()
    assert len(body["periods"]) == PERIODS
    assert body["session_count"] == PLANNED_SESSIONS
    assert all(period["is_started"] is False for period in body["periods"])
    assert sum(period["session_count"] for period in body["periods"]) == PLANNED_SESSIONS


async def test_a_periode_in_the_past_is_under_way(client: AsyncClient) -> None:
    """Midyear, P1 and P2 are behind: a re-generation of them needs the teacher's word."""
    app.dependency_overrides[today] = lambda: MIDYEAR
    try:
        body = (await client.get("/api/generation")).json()
    finally:
        app.dependency_overrides.pop(today, None)

    started = {period["code"] for period in body["periods"] if period["is_started"]}
    assert {"P1", "P2"} <= started
    assert "P5" not in started


@pytest.mark.usefixtures("_before_the_year")
async def test_a_cahier_journal_puts_its_periode_under_way(client: AsyncClient) -> None:
    """§10: a day the cahier journal holds is never written over, and its période says so."""
    await client.post(f"/api/journal/{A_MONDAY}/initialise")

    body = (await client.get("/api/generation")).json()

    p1 = next(period for period in body["periods"] if period["code"] == "P1")
    assert p1["is_started"] is True
    assert p1["protected_days"] == 1


@pytest.mark.usefixtures("_before_the_year")
async def test_a_run_writes_the_whole_year_and_reports_it(client: AsyncClient) -> None:
    """§8 Phase 3's acceptance, now over HTTP: 1740 séances and no erreur."""
    response = await client.post("/api/generation", json={})

    assert response.status_code == OK
    report = response.json()
    assert report["sessions_written"] == PLANNED_SESSIONS
    assert report["program_links"] == PROGRAM_LINKS
    assert report["days_written"] == TAUGHT_DAYS
    assert report["days_off"] == DAYS_OFF
    assert report["is_clean"] is True
    assert report["error_count"] == 0


@pytest.mark.usefixtures("_before_the_year")
async def test_the_report_keeps_every_line_and_its_nature(client: AsyncClient) -> None:
    """The rapport de validation separates what is wrong from what the year cannot afford."""
    report = (await client.post("/api/generation", json={})).json()

    kinds: dict[str, int] = {}
    for problem in report["problems"]:
        kinds[problem["kind"]] = kinds.get(problem["kind"], 0) + 1
    assert kinds == {"calendrier": CALENDAR_PROBLEMS, "source": SOURCE_PROBLEMS}
    assert all(problem["message"] for problem in report["problems"])


@pytest.mark.usefixtures("_before_the_year")
async def test_a_run_can_be_asked_for_one_periode(client: AsyncClient) -> None:
    """§8 Phase 3: « génération relançable par période »."""
    report = (await client.post("/api/generation", json={"periods": ["P1"]})).json()

    assert report["periods"] == ["P1"]
    assert report["sessions_written"] == P1_SESSIONS


@pytest.mark.usefixtures("_before_the_year")
async def test_a_periode_under_way_is_refused_without_a_confirmation(
    client: AsyncClient,
) -> None:
    """§7 écran 5: « confirmation explicite avant d'écraser une période déjà entamée »."""
    await client.post(f"/api/journal/{A_MONDAY}/initialise")

    response = await client.post("/api/generation", json={"periods": ["P1"]})

    assert response.status_code == CONFLICT
    assert "P1" in response.json()["detail"]


@pytest.mark.usefixtures("_before_the_year")
async def test_a_periode_under_way_runs_once_it_is_confirmed(client: AsyncClient) -> None:
    """Confirming runs it — and the day the cahier journal holds is still left alone."""
    await client.post(f"/api/journal/{A_MONDAY}/initialise")

    response = await client.post("/api/generation", json={"periods": ["P1"], "confirm": True})

    assert response.status_code == OK
    report = response.json()
    assert report["days_untouched"] == [A_MONDAY.isoformat()]
    assert report["sessions_written"] < P1_SESSIONS


@pytest.mark.usefixtures("_before_the_year")
async def test_a_periode_that_is_not_under_way_is_not_refused_with_one_that_is(
    client: AsyncClient,
) -> None:
    """Only the périodes actually targeted are weighed."""
    await client.post(f"/api/journal/{A_MONDAY}/initialise")

    response = await client.post("/api/generation", json={"periods": ["P3"]})

    assert response.status_code == OK
    assert response.json()["periods"] == ["P3"]


@pytest.mark.usefixtures("_before_the_year")
async def test_running_twice_leaves_the_same_year(client: AsyncClient) -> None:
    """The natural key of ADR-0009 makes a re-generation an update, not a second year."""
    first = (await client.post("/api/generation", json={})).json()
    second = (await client.post("/api/generation", json={"confirm": True})).json()

    assert second["sessions_written"] == first["sessions_written"]
    status = (await client.get("/api/generation")).json()
    assert status["session_count"] == PLANNED_SESSIONS
