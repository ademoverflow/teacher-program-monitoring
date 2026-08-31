"""The calendrier, the gabarit and the matières, over HTTP.

These tests need Postgres — ``conftest.py`` skips them where none answers.
"""

from collections.abc import Iterator
from datetime import date

import pytest
from core.clock import today
from core.main import app
from core.models.weekday import Weekday
from httpx import AsyncClient

from tests.expected import (
    ALTERNATING_SLOTS,
    DOMAINS,
    HOLIDAYS,
    OK,
    SLOTS_PER_WEEKDAY,
    SUBJECTS,
    TIMETABLE_SLOTS,
    WEEKS,
    WEEKS_PER_PERIOD,
)

# 2027-03-29 is lundi de Pâques; the semaine holding it is the only one of P4 with a hole.
EASTER_MONDAY_WEEK = 25
# Mardi 10/11/2026 falls in P2, second semaine of it — S9 of the year.
IN_P2 = date(2026, 11, 10)
IN_P2_WEEK = 9


@pytest.fixture
def _in_the_year() -> Iterator[None]:
    """Answer as if today were a jour de classe of P2, whatever day the suite runs on."""
    app.dependency_overrides[today] = lambda: IN_P2
    yield
    app.dependency_overrides.pop(today, None)


async def test_the_year_lists_its_five_periodes_and_their_semaines(client: AsyncClient) -> None:
    """§4.2: 36 semaines, 7/7/5/6/11 — the counts, recomputed rather than assumed."""
    response = await client.get("/api/calendar")

    assert response.status_code == OK
    year = response.json()
    assert year["label"] == "2026-2027"
    assert year["zone"] == "C"
    counts = {period["code"]: len(period["weeks"]) for period in year["periods"]}
    assert counts == WEEKS_PER_PERIOD
    assert sum(counts.values()) == WEEKS


async def test_the_year_lists_the_vacances(client: AsyncClient) -> None:
    """The five stretches of vacances, the summer one open-ended."""
    year = (await client.get("/api/calendar")).json()

    assert len(year["holidays"]) == HOLIDAYS
    assert year["holidays"][-1]["ends_on"] is None


async def test_a_semaine_says_how_many_of_its_jours_are_chomes(client: AsyncClient) -> None:
    """§7 écran 1 shows the hole in P4-S6 without opening the semaine (ADR-0001)."""
    year = (await client.get("/api/calendar")).json()
    weeks = {week["number"]: week for period in year["periods"] for week in period["weeks"]}

    assert weeks[EASTER_MONDAY_WEEK]["days_off"] == 1
    assert weeks[1]["days_off"] == 0


@pytest.mark.usefixtures("_in_the_year")
async def test_the_year_points_at_the_semaine_courante(client: AsyncClient) -> None:
    """Mardi 10/11/2026 falls in P2, second semaine — S9."""
    year = (await client.get("/api/calendar")).json()

    assert year["current_week_number"] == IN_P2_WEEK
    assert year["today"] == "2026-11-10"


@pytest.mark.usefixtures("_in_the_year")
async def test_today_is_a_jour_de_classe_when_it_is_one(client: AsyncClient) -> None:
    """Mardi 10/11/2026 is taught, so « Aujourd'hui » opens it."""
    response = await client.get("/api/calendar/today")

    assert response.status_code == OK
    body = response.json()
    assert body["school_day"]["date"] == "2026-11-10"
    assert body["school_day"]["day_of_week"] == Weekday.TUESDAY
    assert body["school_day"]["week_number"] == IN_P2_WEEK
    assert body["school_day"]["period_code"] == "P2"
    assert body["next_school_day"]["date"] == "2026-11-10"


async def test_today_points_at_the_next_jour_de_classe_when_it_is_not_one(
    client: AsyncClient,
) -> None:
    """A jour chômé is still a jour de classe (ADR-0001) — and is not the one to open.

    Lundi 29/03/2027 is lundi de Pâques: it has a row, it is chômé, and the next taught
    day is the mardi.
    """
    app.dependency_overrides[today] = lambda: date(2027, 3, 29)
    try:
        body = (await client.get("/api/calendar/today")).json()
    finally:
        app.dependency_overrides.pop(today, None)

    assert body["school_day"] is None
    assert body["next_school_day"]["date"] == "2027-03-30"


async def test_today_has_no_jour_de_classe_left_after_the_year(client: AsyncClient) -> None:
    """The year ends: the home page has nothing to open, and says so rather than failing."""
    app.dependency_overrides[today] = lambda: date(2027, 8, 1)
    try:
        body = (await client.get("/api/calendar/today")).json()
    finally:
        app.dependency_overrides.pop(today, None)

    assert body["school_day"] is None
    assert body["next_school_day"] is None


async def test_the_gabarit_has_its_forty_four_creneaux(client: AsyncClient) -> None:
    """§4.1: 10 lundi, 12 mardi, 12 jeudi, 10 vendredi, and never a mercredi."""
    response = await client.get("/api/timetable")

    assert response.status_code == OK
    slots = response.json()
    assert len(slots) == TIMETABLE_SLOTS
    per_day: dict[int, int] = {}
    for slot in slots:
        per_day[slot["day_of_week"]] = per_day.get(slot["day_of_week"], 0) + 1
    assert per_day == SLOTS_PER_WEEKDAY


async def test_a_creneau_keeps_the_duration_its_cell_prints(client: AsyncClient) -> None:
    """ADR-0003: the vendredi calcul mental is 9h55-10h15 in the grid and lasts 15 minutes."""
    slots = (await client.get("/api/timetable")).json()

    friday = next(
        slot
        for slot in slots
        if slot["day_of_week"] == Weekday.FRIDAY and slot["label"] == "Calcul mental"
    )
    monday = next(
        slot
        for slot in slots
        if slot["day_of_week"] == Weekday.MONDAY and slot["label"] == "Calcul mental"
    )
    assert friday["starts_at"] == monday["starts_at"] == "09:55:00"
    assert friday["ends_at"] == monday["ends_at"] == "10:15:00"
    assert (friday["duration_minutes"], monday["duration_minutes"]) == (15, 20)


async def test_an_alternating_creneau_names_a_pair_and_no_matiere(client: AsyncClient) -> None:
    """ADR-0002: six créneaux carry an ``alternation_group`` instead of a matière."""
    slots = (await client.get("/api/timetable")).json()

    alternating = [slot for slot in slots if slot["is_alternating"]]
    assert len(alternating) == ALTERNATING_SLOTS
    assert all(slot["subject"] is None for slot in alternating)
    assert {slot["alternation_group"] for slot in alternating} == {
        "histoire-geographie",
        "arts-plastiques-education-musicale",
    }


async def test_the_matieres_come_with_their_domaines_and_their_colour(
    client: AsyncClient,
) -> None:
    """12 matières, 45 domaines — what the filters and the grid's colours are built from."""
    response = await client.get("/api/subjects")

    assert response.status_code == OK
    subjects = response.json()
    assert len(subjects) == SUBJECTS
    assert sum(len(subject["domains"]) for subject in subjects) == DOMAINS
    assert all(subject["color"] for subject in subjects)


async def test_poesie_is_a_matiere_with_no_domaine(client: AsyncClient) -> None:
    """ADR-0014: poésie keeps its row and its colour, and has no programme of its own."""
    subjects = (await client.get("/api/subjects")).json()

    poesie = next(subject for subject in subjects if subject["code"] == "poesie")
    assert poesie["domains"] == []
