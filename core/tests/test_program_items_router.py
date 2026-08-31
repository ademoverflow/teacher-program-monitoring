"""Browsing and searching the programmes officiels.

These tests need Postgres — ``conftest.py`` skips them where none answers.
"""

from core.models.level import Level
from httpx import AsyncClient

from tests.expected import NOT_FOUND, OK, PROGRAM_ITEMS

MISSING_ITEM = "00000000-0000-0000-0000-000000000000"
PAGE_OF_TEN = 10


async def test_the_whole_programme_is_there(client: AsyncClient) -> None:
    """220 items de programme, and a page of them at a time."""
    response = await client.get("/api/program-items", params={"limit": PAGE_OF_TEN})

    assert response.status_code == OK
    page = response.json()
    assert page["total"] == PROGRAM_ITEMS
    assert len(page["items"]) == PAGE_OF_TEN


async def test_items_come_back_in_the_order_the_source_prints_them(client: AsyncClient) -> None:
    """ADR-0015: ``source_order`` is the only order the items have — the id is a UUID."""
    page = (await client.get("/api/program-items", params={"limit": 50})).json()

    orders = [item["source_order"] for item in page["items"]]
    assert orders == sorted(orders)


async def test_a_search_finds_the_fractions(client: AsyncClient) -> None:
    """§8 Phase 5's own example, and §6's requirement: ``websearch_to_tsquery``, not ILIKE.

    The French dictionary stems, so the singular « fraction » is found by « fractions ».
    """
    page = (await client.get("/api/program-items", params={"q": "fractions"})).json()

    assert page["total"] > 0
    haystack = " ".join(
        f"{item['title']} {item['description'] or ''}".lower() for item in page["items"]
    )
    assert "fraction" in haystack
    assert all(item["subject"]["code"] == "mathematiques" for item in page["items"])


async def test_a_search_that_matches_nothing_says_so(client: AsyncClient) -> None:
    """An empty result is a result, not a 404."""
    page = (await client.get("/api/program-items", params={"q": "hippopotame"})).json()

    assert page["total"] == 0
    assert page["items"] == []


async def test_the_filters_compose(client: AsyncClient) -> None:
    """§7 écran 4: niveau, matière and domaine narrow the list together."""
    whole = (await client.get("/api/program-items", params={"limit": 1})).json()
    cm1 = (await client.get("/api/program-items", params={"level": Level.CM1, "limit": 1})).json()
    narrowed = (
        await client.get(
            "/api/program-items",
            params={"level": Level.CM1, "subject": "mathematiques", "limit": 200},
        )
    ).json()

    assert whole["total"] == PROGRAM_ITEMS
    assert 0 < cm1["total"] < whole["total"]
    assert 0 < narrowed["total"] < cm1["total"]
    assert all(item["level"] == Level.CM1 for item in narrowed["items"])
    assert all(item["subject"]["code"] == "mathematiques" for item in narrowed["items"])


async def test_a_search_can_be_narrowed_by_a_filter(client: AsyncClient) -> None:
    """A search and a filter are ANDed, not ORed."""
    both = (
        await client.get(
            "/api/program-items", params={"q": "fractions", "level": Level.CM2, "limit": 200}
        )
    ).json()

    assert both["total"] > 0
    assert all(item["level"] == Level.CM2 for item in both["items"])


async def test_an_item_carries_the_page_it_was_read_from(client: AsyncClient) -> None:
    """ADR-0007: every item is traceable back to the source PDF."""
    page = (await client.get("/api/program-items", params={"limit": 1})).json()
    identifier = page["items"][0]["id"]

    response = await client.get(f"/api/program-items/{identifier}")

    assert response.status_code == OK
    item = response.json()
    assert item["source_file"].endswith(".pdf")
    assert item["source_page"]


async def test_an_item_that_does_not_exist_is_a_404(client: AsyncClient) -> None:
    """A well-formed id that names nothing is still nothing."""
    assert (await client.get(f"/api/program-items/{MISSING_ITEM}")).status_code == NOT_FOUND


async def test_an_item_lists_the_seances_that_work_it(client: AsyncClient) -> None:
    """§7 écran 4: « voir les séances liées », and the séance that led here is one of them."""
    day = (await client.get("/api/days/2026-09-07")).json()
    sciences = next(
        session for session in day["sessions"] if session["slot"]["label"].startswith("Sciences")
    )
    identifier = sciences["program_items"][0]["id"]

    response = await client.get("/api/sessions", params={"program_item_id": identifier})

    assert response.status_code == OK
    linked = response.json()
    assert linked["total"] > 0
    assert sciences["id"] in {session["id"] for session in linked["sessions"]}
    dates = [session["date"] for session in linked["sessions"]]
    assert dates == sorted(dates)


async def test_a_rituel_links_the_same_items_all_year_and_the_list_is_paged(
    client: AsyncClient,
) -> None:
    """ADR-0015: the dictée du jour works its three orthographe items on every occurrence."""
    day = (await client.get("/api/days/2026-09-07")).json()
    dictee = next(
        session for session in day["sessions"] if session["slot"]["label"] == "Dictée du jour"
    )
    identifier = dictee["program_items"][0]["id"]

    page = (
        await client.get(
            "/api/sessions", params={"program_item_id": identifier, "limit": PAGE_OF_TEN}
        )
    ).json()

    assert page["total"] > PAGE_OF_TEN
    assert len(page["sessions"]) == PAGE_OF_TEN


async def test_an_item_no_seance_works_lists_nothing(client: AsyncClient) -> None:
    """A well-formed id nothing links answers an empty list, not a 404."""
    response = await client.get("/api/sessions", params={"program_item_id": MISSING_ITEM})

    assert response.status_code == OK
    assert response.json() == {"total": 0, "sessions": []}
