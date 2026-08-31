"""The jour de classe and the CRUD of its séances.

These tests need Postgres — ``conftest.py`` skips them where none answers.
"""

from datetime import date

from core.models.level import Level
from core.models.status import SessionStatus
from core.models.weekday import Weekday
from httpx import AsyncClient

from tests.expected import (
    CONFLICT,
    CREATED,
    NO_CONTENT,
    NOT_FOUND,
    OK,
    SESSIONS_ON_A_MONDAY,
)

A_MONDAY = date(2026, 9, 7)
A_MONDAY_WEEK = 2
# The two durations §4.1 prints on the créneaux this lundi opens with.
ACCUEIL_MINUTES = 10
CRENEAU_MINUTES = 45
EASTER_MONDAY = date(2027, 3, 29)
# 02/09/2026 is a Wednesday: there is never class on a Wednesday (§2).
A_WEDNESDAY = date(2026, 9, 2)


async def test_a_jour_lists_its_seances_in_the_order_they_run(client: AsyncClient) -> None:
    """A lundi of P1: 10 créneaux, two of which are split by niveau — 12 séances."""
    response = await client.get(f"/api/days/{A_MONDAY}")

    assert response.status_code == OK
    day = response.json()
    assert day["day_of_week"] == Weekday.MONDAY
    assert day["week_number"] == A_MONDAY_WEEK
    assert day["period"]["code"] == "P1"
    assert len(day["sessions"]) == SESSIONS_ON_A_MONDAY
    positions = [session["position"] for session in day["sessions"]]
    assert positions == sorted(positions)


async def test_a_seance_carries_its_creneau_and_what_it_teaches(client: AsyncClient) -> None:
    """§7 écran 3 needs the durée, the objectifs and the items in one request."""
    day = (await client.get(f"/api/days/{A_MONDAY}")).json()

    accueil = day["sessions"][0]
    assert accueil["slot"]["duration_minutes"] == ACCUEIL_MINUTES
    grammaire = next(
        session for session in day["sessions"] if session["slot"]["starts_at"] == "09:10:00"
    )
    assert grammaire["sequence"]["method"] == "retz-cm1"
    assert grammaire["level"] == Level.CM1
    assert grammaire["slot"]["duration_minutes"] == CRENEAU_MINUTES


async def test_a_seance_lists_the_items_de_programme_it_works(client: AsyncClient) -> None:
    """ADR-0015: a créneau with no méthodo works its matière's programme."""
    day = (await client.get(f"/api/days/{A_MONDAY}")).json()

    sciences = next(
        session for session in day["sessions"] if session["slot"]["label"].startswith("Sciences")
    )
    assert sciences["program_items"]
    assert all(item["title"] for item in sciences["program_items"])


async def test_a_jour_chome_answers_with_no_seance_and_a_motif(client: AsyncClient) -> None:
    """ADR-0001: lundi de Pâques keeps its row, and the vue jour renders it empty."""
    response = await client.get(f"/api/days/{EASTER_MONDAY}")

    assert response.status_code == OK
    day = response.json()
    assert day["is_off"] is True
    assert day["off_reason"]
    assert day["sessions"] == []


async def test_a_jour_knows_the_ones_on_either_side(client: AsyncClient) -> None:
    """There is never class on a Wednesday, so the jeudi follows the mardi."""
    day = (await client.get("/api/days/2026-09-08")).json()

    assert day["previous_day"] == "2026-09-07"
    assert day["next_day"] == "2026-09-10"


async def test_a_day_that_is_not_a_jour_de_classe_is_a_404(client: AsyncClient) -> None:
    """A Wednesday, a weekend and the vacances have no row at all (ADR-0001)."""
    assert (await client.get(f"/api/days/{A_WEDNESDAY}")).status_code == NOT_FOUND
    assert (await client.get("/api/days/2026-10-20")).status_code == NOT_FOUND


async def test_a_seance_reads_back_on_its_own(client: AsyncClient) -> None:
    """The séance editor opens one séance without the whole day."""
    day = (await client.get(f"/api/days/{A_MONDAY}")).json()
    wanted = day["sessions"][3]

    response = await client.get(f"/api/planned-sessions/{wanted['id']}")

    assert response.status_code == OK
    assert response.json() == wanted


async def test_editing_a_seance_persists(client: AsyncClient) -> None:
    """§8 Phase 4: « CRUD planned_sessions »."""
    day = (await client.get(f"/api/days/{A_MONDAY}")).json()
    wanted = day["sessions"][0]

    response = await client.patch(
        f"/api/planned-sessions/{wanted['id']}",
        json={"title": "Accueil — rentrée", "status": SessionStatus.FAITE},
    )

    assert response.status_code == OK
    assert response.json()["title"] == "Accueil — rentrée"
    again = (await client.get(f"/api/planned-sessions/{wanted['id']}")).json()
    assert again["title"] == "Accueil — rentrée"
    assert again["status"] == SessionStatus.FAITE


async def test_a_seance_can_be_removed_and_put_back(client: AsyncClient) -> None:
    """A deletion is the teacher's, and a re-generation is what puts the séance back."""
    day = (await client.get(f"/api/days/{A_MONDAY}")).json()
    wanted = day["sessions"][0]

    removed = await client.delete(f"/api/planned-sessions/{wanted['id']}")

    assert removed.status_code == NO_CONTENT
    assert (await client.get(f"/api/planned-sessions/{wanted['id']}")).status_code == NOT_FOUND

    added = await client.post(
        "/api/planned-sessions",
        json={
            "date": A_MONDAY.isoformat(),
            "timetable_slot_id": wanted["timetable_slot_id"],
            "level": wanted["level"],
            "title": wanted["title"],
        },
    )
    assert added.status_code == CREATED
    assert added.json()["title"] == wanted["title"]


async def test_a_creneau_already_taken_at_that_niveau_is_a_409(client: AsyncClient) -> None:
    """ADR-0009: one séance per (jour, créneau, niveau), and the API says so."""
    day = (await client.get(f"/api/days/{A_MONDAY}")).json()
    wanted = day["sessions"][0]

    response = await client.post(
        "/api/planned-sessions",
        json={
            "date": A_MONDAY.isoformat(),
            "timetable_slot_id": wanted["timetable_slot_id"],
            "level": wanted["level"],
            "title": "Un deuxième accueil",
        },
    )

    assert response.status_code == CONFLICT
    assert "déjà" in response.json()["detail"]


async def test_a_creneau_of_another_weekday_is_a_409(client: AsyncClient) -> None:
    """§10: the EDT is immutable, so a créneau du mardi does not run on a lundi."""
    tuesday = (await client.get("/api/days/2026-09-08")).json()
    slot = tuesday["sessions"][0]["timetable_slot_id"]

    response = await client.post(
        "/api/planned-sessions",
        json={
            "date": A_MONDAY.isoformat(),
            "timetable_slot_id": slot,
            "level": Level.COMMUN,
            "title": "Un accueil déplacé",
        },
    )

    assert response.status_code == CONFLICT
    assert "emploi du temps" in response.json()["detail"]


async def test_a_jour_chome_takes_no_seance(client: AsyncClient) -> None:
    """A day the calendar has taken away is not a place to plan (ADR-0001)."""
    day = (await client.get(f"/api/days/{A_MONDAY}")).json()

    response = await client.post(
        "/api/planned-sessions",
        json={
            "date": EASTER_MONDAY.isoformat(),
            "timetable_slot_id": day["sessions"][0]["timetable_slot_id"],
            "level": Level.COMMUN,
            "title": "Une séance le lundi de Pâques",
        },
    )

    assert response.status_code == CONFLICT
    assert "chômé" in response.json()["detail"]


async def test_a_creneau_of_one_niveau_takes_no_other(client: AsyncClient) -> None:
    """A créneau printed « CM1 » in the EDT teaches CM1; a CM2 séance in it is refused."""
    tuesday = (await client.get("/api/days/2026-09-08")).json()
    cm1_only = next(
        session
        for session in tuesday["sessions"]
        if session["slot"]["level"] == Level.CM1 and session["slot"]["starts_at"] == "11:30:00"
    )
    await client.delete(f"/api/planned-sessions/{cm1_only['id']}")

    response = await client.post(
        "/api/planned-sessions",
        json={
            "date": "2026-09-08",
            "timetable_slot_id": cm1_only["timetable_slot_id"],
            "level": Level.CM2,
            "title": "Une séance CM2 dans un créneau CM1",
        },
    )

    assert response.status_code == CONFLICT
    assert "CM1" in response.json()["detail"]
