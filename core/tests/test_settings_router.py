"""The réglages: the two alternances, and what changing one costs.

These tests need Postgres — ``conftest.py`` skips them where none answers.
"""

from core.models.weekday import Weekday
from httpx import AsyncClient

from tests.expected import NOT_FOUND, OK, UNPROCESSABLE

HISTOIRE_GEOGRAPHIE = "alternance.histoire-geographie"
ARTS = "alternance.arts-plastiques-education-musicale"
SETTINGS = 2


async def test_the_two_alternances_are_the_reglages(client: AsyncClient) -> None:
    """ADR-0013: the §4.1 defaults, seeded once and owned by the teacher afterwards."""
    response = await client.get("/api/settings")

    assert response.status_code == OK
    settings = response.json()
    assert len(settings) == SETTINGS
    assert {setting["key"] for setting in settings} == {HISTOIRE_GEOGRAPHIE, ARTS}
    assert all(setting["label"] for setting in settings)


async def test_a_reglage_says_that_the_generation_is_what_reads_it(
    client: AsyncClient,
) -> None:
    """ADR-0013: changing an alternance moves nothing until the year is generated again."""
    settings = (await client.get("/api/settings")).json()

    assert all(setting["requires_generation"] is True for setting in settings)


async def test_changing_an_alternance_persists(client: AsyncClient) -> None:
    """§4.1 calls the alternances « à paramétrer, modifiable dans l'app »."""
    response = await client.put(
        f"/api/settings/{HISTOIRE_GEOGRAPHIE}",
        json={"value": {"mode": "hebdomadaire", "subjects": ["geographie", "histoire"]}},
    )

    assert response.status_code == OK
    assert response.json()["value"]["subjects"] == ["geographie", "histoire"]
    again = (await client.get("/api/settings")).json()
    changed = next(setting for setting in again if setting["key"] == HISTOIRE_GEOGRAPHIE)
    assert changed["value"]["subjects"] == ["geographie", "histoire"]


async def test_a_changed_alternance_moves_the_year_when_it_is_generated_again(
    client: AsyncClient,
) -> None:
    """ADR-0013: « le réglage est lu à la génération » — this is what makes it a paramètre."""
    before = (await client.get("/api/weeks/2")).json()
    monday = next(day for day in before["days"] if day["day_of_week"] == Weekday.MONDAY)
    arts = next(cell for cell in monday["cells"] if cell["slot"]["is_alternating"])
    assert arts["sessions"][0]["subject"]["code"] == "arts-plastiques"

    await client.put(
        f"/api/settings/{ARTS}",
        json={
            "value": {
                "mode": "par-creneau",
                "slots": [
                    {"day": "lundi", "starts_at": "15:45", "subject": "education-musicale"},
                    {"day": "jeudi", "starts_at": "14:15", "subject": "arts-plastiques"},
                ],
            }
        },
    )
    await client.post("/api/generation", json={"confirm": True})

    after = (await client.get("/api/weeks/2")).json()
    monday = next(day for day in after["days"] if day["day_of_week"] == Weekday.MONDAY)
    arts = next(cell for cell in monday["cells"] if cell["slot"]["is_alternating"])
    assert arts["sessions"][0]["subject"]["code"] == "education-musicale"


async def test_a_value_the_generator_could_not_read_is_refused(client: AsyncClient) -> None:
    """The value is validated against ``AlternationMode``, not stored and found broken later."""
    response = await client.put(
        f"/api/settings/{HISTOIRE_GEOGRAPHIE}",
        json={"value": {"mode": "tous-les-mardis", "subjects": ["histoire"]}},
    )

    assert response.status_code == UNPROCESSABLE
    unchanged = (await client.get("/api/settings")).json()
    kept = next(setting for setting in unchanged if setting["key"] == HISTOIRE_GEOGRAPHIE)
    assert kept["value"]["mode"] == "hebdomadaire"


async def test_a_reglage_the_application_does_not_define_is_a_404(client: AsyncClient) -> None:
    """The réglages are the ones the app defines: a PUT does not create one."""
    response = await client.put("/api/settings/couleur.preferee", json={"value": "bleu"})

    assert response.status_code == NOT_FOUND
    assert len((await client.get("/api/settings")).json()) == SETTINGS
