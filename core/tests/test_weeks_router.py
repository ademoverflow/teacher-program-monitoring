"""The semaine as the grid of §4.1: every créneau of every jour, filled or not.

These tests need Postgres — ``conftest.py`` skips them where none answers.
"""

from core.models.level import Level
from core.models.weekday import Weekday
from httpx import AsyncClient

from tests.expected import (
    NOT_FOUND,
    OK,
    SESSIONS_IN_A_FULL_WEEK,
    SESSIONS_IN_FIRST_WEEK,
    SLOTS_PER_WEEKDAY,
    WEEKS,
)

# The semaine holding lundi de Pâques (29/03/2027), P4-S6.
EASTER_MONDAY_WEEK = 25
JOURS_IN_A_FULL_WEEK = 4
SPLIT_CELL_SESSIONS = 2


def _sessions(week: dict) -> list[dict]:
    """Every séance of a rendered semaine, whatever cell it sits in."""
    return [
        session for day in week["days"] for cell in day["cells"] for session in cell["sessions"]
    ]


async def test_the_first_semaine_has_no_lundi(client: AsyncClient) -> None:
    """§4.2: the year opens on mardi 01/09/2026, so S1 is three jours and 38 séances."""
    response = await client.get("/api/weeks/1")

    assert response.status_code == OK
    week = response.json()
    assert [day["day_of_week"] for day in week["days"]] == [
        Weekday.TUESDAY,
        Weekday.THURSDAY,
        Weekday.FRIDAY,
    ]
    assert len(_sessions(week)) == SESSIONS_IN_FIRST_WEEK


async def test_a_full_semaine_has_four_jours_and_fifty_seances(client: AsyncClient) -> None:
    """1532 couples (jour, créneau) plus the 208 split by niveau make 50 a week."""
    week = (await client.get("/api/weeks/2")).json()

    assert len(week["days"]) == JOURS_IN_A_FULL_WEEK
    assert len(_sessions(week)) == SESSIONS_IN_A_FULL_WEEK


async def test_the_last_semaine_is_full_too(client: AsyncClient) -> None:
    """ADR-0010: the marge changes what the maths créneaux say, not the shape of the grid."""
    week = (await client.get("/api/weeks/36")).json()

    assert len(_sessions(week)) == SESSIONS_IN_A_FULL_WEEK
    assert any("révisions" in session["title"] for session in _sessions(week))


async def test_every_jour_carries_every_creneau_of_its_weekday(client: AsyncClient) -> None:
    """The grid keeps its shape: 10 cells on a lundi, 12 on a mardi (§4.1)."""
    week = (await client.get("/api/weeks/2")).json()

    assert {day["day_of_week"]: len(day["cells"]) for day in week["days"]} == SLOTS_PER_WEEKDAY


async def test_a_jour_chome_keeps_its_cells_and_says_why(client: AsyncClient) -> None:
    """ADR-0001: a lost day keeps its place so the plan can account for it."""
    week = (await client.get(f"/api/weeks/{EASTER_MONDAY_WEEK}")).json()

    monday = next(day for day in week["days"] if day["day_of_week"] == Weekday.MONDAY)
    assert monday["is_off"] is True
    assert monday["off_reason"]
    assert len(monday["cells"]) == SLOTS_PER_WEEKDAY[Weekday.MONDAY]
    assert all(cell["sessions"] == [] for cell in monday["cells"])


async def test_a_split_creneau_puts_two_seances_in_one_cell(client: AsyncClient) -> None:
    """ADR-0010: the mardi conjugaison créneau is commun and carries a CM1 and a CM2 séance."""
    week = (await client.get("/api/weeks/2")).json()

    tuesday = next(day for day in week["days"] if day["day_of_week"] == Weekday.TUESDAY)
    cell = next(cell for cell in tuesday["cells"] if cell["slot"]["starts_at"] == "09:10:00")
    assert cell["slot"]["level"] == Level.COMMUN
    assert len(cell["sessions"]) == SPLIT_CELL_SESSIONS
    assert [session["level"] for session in cell["sessions"]] == [Level.CM1, Level.CM2]


async def test_two_creneaux_at_one_hour_are_two_cells_not_one(client: AsyncClient) -> None:
    """Mardi 11h30 is two créneaux — CM1 lecture, CM2 histoire ou géographie — not a split.

    The distinction matters to the grid: one cell with two séances is drawn stacked inside
    a créneau, two cells are drawn side by side.
    """
    week = (await client.get("/api/weeks/2")).json()

    tuesday = next(day for day in week["days"] if day["day_of_week"] == Weekday.TUESDAY)
    at_1130 = [cell for cell in tuesday["cells"] if cell["slot"]["starts_at"] == "11:30:00"]
    assert len(at_1130) == SPLIT_CELL_SESSIONS
    assert [cell["slot"]["level"] for cell in at_1130] == [Level.CM1, Level.CM2]
    assert all(len(cell["sessions"]) == 1 for cell in at_1130)


async def test_a_semaine_knows_the_ones_on_either_side(client: AsyncClient) -> None:
    """§7 écran 2 navigates semaine par semaine and stops at the ends of the year."""
    first = (await client.get("/api/weeks/1")).json()
    middle = (await client.get("/api/weeks/2")).json()
    last = (await client.get(f"/api/weeks/{WEEKS}")).json()

    assert (first["previous_week_number"], first["next_week_number"]) == (None, 2)
    assert (middle["previous_week_number"], middle["next_week_number"]) == (1, 3)
    assert (last["previous_week_number"], last["next_week_number"]) == (WEEKS - 1, None)


async def test_a_semaine_names_its_periode(client: AsyncClient) -> None:
    """S9 is the second semaine of P2."""
    week = (await client.get("/api/weeks/9")).json()

    assert week["period"]["code"] == "P2"
    assert week["number_in_period"] == SPLIT_CELL_SESSIONS


async def test_a_semaine_the_year_does_not_have_is_a_404(client: AsyncClient) -> None:
    """The year has 36 semaines and says so rather than answering an empty grid."""
    assert (await client.get("/api/weeks/37")).status_code == NOT_FOUND
    assert (await client.get("/api/weeks/0")).status_code == NOT_FOUND
