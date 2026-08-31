"""The cahier journal: filled once from the day's séances, then lived in.

These tests need Postgres — ``conftest.py`` skips them where none answers.
"""

from datetime import date

from httpx import AsyncClient

from tests.expected import (
    BAD_REQUEST,
    CREATED,
    NO_CONTENT,
    NOT_FOUND,
    OK,
    SESSIONS_ON_A_MONDAY,
)

A_MONDAY = date(2026, 9, 7)
A_MONDAY_WEEK = 2
EASTER_MONDAY = date(2027, 3, 29)
A_WEDNESDAY = date(2026, 9, 2)
ACCUEIL_MINUTES = 10
CRENEAU_MINUTES = 45


async def test_a_day_starts_with_no_cahier_journal(client: AsyncClient) -> None:
    """There are zero ``journal_entries`` until a day is opened for the first time."""
    response = await client.get(f"/api/journal/{A_MONDAY}")

    assert response.status_code == OK
    journal = response.json()
    assert journal["initialised"] is False
    assert journal["entries"] == []
    assert journal["week_number"] == A_MONDAY_WEEK
    assert journal["period_code"] == "P1"


async def test_initialising_copies_the_day_s_seances_in_order(client: AsyncClient) -> None:
    """§8 Phase 4: « initialisation du cahier journal d'un jour depuis ses séances »."""
    response = await client.post(f"/api/journal/{A_MONDAY}/initialise")

    assert response.status_code == CREATED
    journal = response.json()
    assert journal["initialised"] is True
    assert len(journal["entries"]) == SESSIONS_ON_A_MONDAY
    assert [entry["position"] for entry in journal["entries"]] == list(
        range(1, SESSIONS_ON_A_MONDAY + 1)
    )
    assert all(entry["planned_session_id"] for entry in journal["entries"])


async def test_a_ligne_takes_the_creneau_s_duration_and_a_bilan_left_blank(
    client: AsyncClient,
) -> None:
    """ADR-0003: the cahier journal prints a durée, so it takes ``duration_minutes``."""
    journal = (await client.post(f"/api/journal/{A_MONDAY}/initialise")).json()

    assert journal["entries"][0]["duration_minutes"] == ACCUEIL_MINUTES
    assert journal["entries"][1]["duration_minutes"] == CRENEAU_MINUTES
    assert all(entry["bilan"] is None for entry in journal["entries"])


async def test_a_split_creneau_gives_two_lignes_that_name_their_niveau(
    client: AsyncClient,
) -> None:
    """ADR-0010: two séances at 09h10 become two lignes the teacher can tell apart."""
    journal = (await client.post(f"/api/journal/{A_MONDAY}/initialise")).json()

    grammaire = [
        entry
        for entry in journal["entries"]
        if entry["discipline"].startswith("Étude de la langue — Grammaire")
    ]
    assert [entry["discipline"] for entry in grammaire] == [
        "Étude de la langue — Grammaire (CM1)",
        "Étude de la langue — Grammaire (CM2)",
    ]


async def test_an_alternating_creneau_names_the_matiere_it_landed_on(
    client: AsyncClient,
) -> None:
    """ADR-0002: « Arts plastiques / Éducation musicale » names a pair, not what is taught."""
    journal = (await client.post(f"/api/journal/{A_MONDAY}/initialise")).json()

    assert journal["entries"][-1]["discipline"] == "Arts plastiques"


async def test_a_ligne_says_what_is_taught_above_what_it_aims_at(client: AsyncClient) -> None:
    """The example prints both in the « Objectif(s) et compétence(s) » column."""
    journal = (await client.post(f"/api/journal/{A_MONDAY}/initialise")).json()

    sciences = next(
        entry for entry in journal["entries"] if entry["discipline"] == "Sciences et technologie"
    )
    assert sciences["objectives"].startswith("États et constitution de la matière")
    assert "\n" in sciences["objectives"]


async def test_a_cahier_journal_is_never_initialised_twice(client: AsyncClient) -> None:
    """§10: « les cahiers journaux … ne sont jamais écrasés »."""
    filled = await client.post(f"/api/journal/{A_MONDAY}/initialise")
    assert filled.status_code == CREATED
    first = filled.json()
    edited = await client.patch(
        f"/api/journal/entries/{first['entries'][0]['id']}",
        json={"bilan": "Bien passé", "discipline": "Accueil"},
    )
    assert edited.status_code == OK

    response = await client.post(f"/api/journal/{A_MONDAY}/initialise")

    # 200, not 201: this call found the day filled and wrote nothing.
    assert response.status_code == OK
    again = response.json()
    assert len(again["entries"]) == len(first["entries"])
    assert again["entries"][0]["bilan"] == "Bien passé"
    assert again["entries"][0]["discipline"] == "Accueil"


async def test_a_jour_chome_initialises_to_nothing(client: AsyncClient) -> None:
    """Lundi de Pâques has no séance, so it has no cahier journal to fill (ADR-0001)."""
    response = await client.post(f"/api/journal/{EASTER_MONDAY}/initialise")

    # 200, not 201: there was nothing to fill it with.
    assert response.status_code == OK
    journal = response.json()
    assert journal["is_off"] is True
    assert journal["entries"] == []


async def test_a_date_that_is_not_a_jour_de_classe_is_a_404(client: AsyncClient) -> None:
    """There is never class on a Wednesday (§2)."""
    assert (await client.get(f"/api/journal/{A_WEDNESDAY}")).status_code == NOT_FOUND
    assert (await client.post(f"/api/journal/{A_WEDNESDAY}/initialise")).status_code == NOT_FOUND


async def test_a_ligne_can_be_added_edited_and_removed(client: AsyncClient) -> None:
    """§7 écran 3: « ajout/suppression de lignes », « édition inline »."""
    await client.post(f"/api/journal/{A_MONDAY}/initialise")

    added = await client.post(
        f"/api/journal/{A_MONDAY}/entries",
        json={"discipline": "Conseil de classe", "duration_minutes": 20},
    )
    assert added.status_code == CREATED
    entry = added.json()
    assert entry["position"] == SESSIONS_ON_A_MONDAY + 1
    assert entry["planned_session_id"] is None

    edited = await client.patch(
        f"/api/journal/entries/{entry['id']}",
        json={"bilan": "Reporté au vendredi"},
    )
    assert edited.status_code == OK
    assert edited.json()["bilan"] == "Reporté au vendredi"
    assert edited.json()["discipline"] == "Conseil de classe"

    removed = await client.delete(f"/api/journal/entries/{entry['id']}")
    assert removed.status_code == NO_CONTENT

    journal = (await client.get(f"/api/journal/{A_MONDAY}")).json()
    assert len(journal["entries"]) == SESSIONS_ON_A_MONDAY


async def test_the_lignes_can_be_reordered(client: AsyncClient) -> None:
    """§7 écran 3: « réordonnancement »."""
    journal = (await client.post(f"/api/journal/{A_MONDAY}/initialise")).json()
    order = [entry["id"] for entry in journal["entries"]]
    reversed_order = list(reversed(order))

    response = await client.put(
        f"/api/journal/{A_MONDAY}/order", json={"entry_ids": reversed_order}
    )

    assert response.status_code == OK
    assert [entry["id"] for entry in response.json()["entries"]] == reversed_order
    again = (await client.get(f"/api/journal/{A_MONDAY}")).json()
    assert [entry["id"] for entry in again["entries"]] == reversed_order


async def test_a_partial_order_is_refused(client: AsyncClient) -> None:
    """A cahier journal is a list: an order that drops a ligne would leave two at one rank."""
    journal = (await client.post(f"/api/journal/{A_MONDAY}/initialise")).json()
    order = [entry["id"] for entry in journal["entries"]][:-1]

    response = await client.put(f"/api/journal/{A_MONDAY}/order", json={"entry_ids": order})

    assert response.status_code == BAD_REQUEST
    again = (await client.get(f"/api/journal/{A_MONDAY}")).json()
    assert [entry["id"] for entry in again["entries"]] == [
        entry["id"] for entry in journal["entries"]
    ]


async def test_a_regeneration_leaves_a_cahier_journal_alone(client: AsyncClient) -> None:
    """§10, from the other side: the generator refuses a day the cahier journal holds."""
    journal = (await client.post(f"/api/journal/{A_MONDAY}/initialise")).json()
    await client.patch(
        f"/api/journal/entries/{journal['entries'][0]['id']}", json={"bilan": "Fait"}
    )

    run = await client.post("/api/generation", json={"periods": ["P1"], "confirm": True})

    assert run.status_code == OK
    assert A_MONDAY.isoformat() in run.json()["days_untouched"]
    again = (await client.get(f"/api/journal/{A_MONDAY}")).json()
    assert again["entries"][0]["bilan"] == "Fait"
