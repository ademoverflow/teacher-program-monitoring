"""Writing the year back: the same plan, upserted, and never over a day that is spoken for.

These tests need Postgres. On the host (and in CI) there is none, so they skip; inside
the core container ``make test-core`` runs them for real. Everything happens in a
transaction that is rolled back, so the dev database is left untouched.
"""

from collections.abc import AsyncIterator
from datetime import date

import pytest
from core.database import async_db_url
from core.services.programmation import plan_input_from_seeds, plan_year
from core.services.programmation.writer import generate_year, load_plan_input
from core.services.seed_files import load_program_items
from core.services.seeding import seed_database
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

# Before the pupils' first day, so nothing of the year is in the past.
BEFORE_THE_YEAR = date(2026, 8, 31)
EXPECTED_SESSIONS = 1740
EXPECTED_LINKS = 4040
TAUGHT_DAYS = 139
# P1: 6 lundis + 7 mardis + 7 jeudis + 7 vendredis of the grid, plus the créneaux
# split by niveau — 6*10 + 7*12 + 7*12 + 7*10 + 2*6 + 2*7 + 7 + 7.
P1_SESSIONS = 338


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Open a seeded session whose work is always rolled back, or skip without a database."""
    test_engine = create_async_engine(async_db_url, poolclass=NullPool)
    try:
        probe = await test_engine.connect()
    except Exception as error:  # noqa: BLE001 - anything at all here means "no database"
        pytest.skip(f"no database reachable: {error}")
    await probe.close()

    async with AsyncSession(test_engine) as open_session:
        try:
            # The dev database already holds a generated year; these tests count rows,
            # so they start from an empty programmation and the rollback puts it back.
            await open_session.execute(text("DELETE FROM journal_entries"))
            await open_session.execute(text("DELETE FROM planned_sessions"))
            await seed_database(open_session)
            yield open_session
        finally:
            await open_session.rollback()
    await test_engine.dispose()


async def _count(session: AsyncSession, table: str) -> int:
    """Count the rows of one table."""
    result = await session.execute(text(f"SELECT count(*) FROM {table}"))  # noqa: S608
    return int(result.scalar_one())


async def test_the_database_and_the_seeds_plan_the_same_year(session: AsyncSession) -> None:
    """The planner is fed the same shape either way — that is what CI's tests cover."""
    from_database = await load_plan_input(session)

    assert plan_year(from_database) == plan_year(plan_input_from_seeds())


async def test_a_generation_writes_every_seance_of_the_year(session: AsyncSession) -> None:
    """§8 Phase 3: the ~139 jours de classe filled, every créneau covered."""
    report = await generate_year(session, reference_date=BEFORE_THE_YEAR)

    assert report.sessions_written == EXPECTED_SESSIONS
    assert report.days_written == TAUGHT_DAYS
    assert not report.days_untouched
    assert await _count(session, "planned_sessions") == EXPECTED_SESSIONS
    assert await _count(session, "planned_session_program_items") == EXPECTED_LINKS


async def test_generating_twice_leaves_the_same_year(session: AsyncSession) -> None:
    """The natural key is what makes a re-generation an update rather than a second year."""
    await generate_year(session, reference_date=BEFORE_THE_YEAR)
    first = await session.execute(
        text("""
            SELECT school_day_id, timetable_slot_id, level, title, position
            FROM planned_sessions ORDER BY id
        """)
    )
    before = sorted(tuple(row) for row in first.all())

    await generate_year(session, reference_date=BEFORE_THE_YEAR)
    second = await session.execute(
        text("""
            SELECT school_day_id, timetable_slot_id, level, title, position
            FROM planned_sessions ORDER BY id
        """)
    )

    assert sorted(tuple(row) for row in second.all()) == before
    assert await _count(session, "planned_sessions") == EXPECTED_SESSIONS
    assert await _count(session, "planned_session_program_items") == EXPECTED_LINKS


async def test_no_seance_lands_on_a_jour_chome(session: AsyncSession) -> None:
    """§8 Phase 3: « aucune séance hors créneau/jour off »."""
    await generate_year(session, reference_date=BEFORE_THE_YEAR)

    stray = await session.execute(
        text("""
            SELECT count(*) FROM planned_sessions
            JOIN school_days ON school_days.id = planned_sessions.school_day_id
            WHERE school_days.is_off
        """)
    )

    assert stray.scalar_one() == 0


async def test_a_seance_never_runs_on_the_wrong_day_of_the_week(session: AsyncSession) -> None:
    """The EDT is immutable (§10): a séance sits in the créneau it belongs to."""
    await generate_year(session, reference_date=BEFORE_THE_YEAR)

    misplaced = await session.execute(
        text("""
            SELECT count(*) FROM planned_sessions
            JOIN school_days ON school_days.id = planned_sessions.school_day_id
            JOIN timetable_slots ON timetable_slots.id = planned_sessions.timetable_slot_id
            WHERE school_days.day_of_week <> timetable_slots.day_of_week
        """)
    )

    assert misplaced.scalar_one() == 0


async def test_a_generation_of_one_periode_touches_only_that_periode(
    session: AsyncSession,
) -> None:
    """§8 Phase 3: « génération relançable par période »."""
    report = await generate_year(session, reference_date=BEFORE_THE_YEAR, periods=["P1"])

    written = await session.execute(
        text("""
            SELECT DISTINCT periods.code FROM planned_sessions
            JOIN school_days ON school_days.id = planned_sessions.school_day_id
            JOIN weeks ON weeks.id = school_days.week_id
            JOIN periods ON periods.id = weeks.period_id
        """)
    )

    assert report.periods == ("P1",)
    assert {row.code for row in written.all()} == {"P1"}
    assert await _count(session, "planned_sessions") == P1_SESSIONS


async def test_a_day_in_the_past_is_never_written_over(session: AsyncSession) -> None:
    """§10: « les jours passés ne sont jamais écrasés »."""
    midyear = date(2027, 1, 11)

    report = await generate_year(session, reference_date=midyear)

    earliest = await session.execute(
        text("""
            SELECT min(school_days.date) FROM planned_sessions
            JOIN school_days ON school_days.id = planned_sessions.school_day_id
        """)
    )

    assert report.days_untouched
    assert max(report.days_untouched) < midyear
    assert earliest.scalar_one() >= midyear


async def test_a_day_that_already_has_a_cahier_journal_is_left_alone(
    session: AsyncSession,
) -> None:
    """§10: « les cahiers journaux … ne sont jamais écrasés » — the rule, before Phase 6."""
    held = date(2026, 9, 1)
    await session.execute(
        text("""
            INSERT INTO journal_entries (school_day_id, discipline, position)
            SELECT id, 'Accueil', 1 FROM school_days WHERE date = :held
        """),
        {"held": held},
    )

    report = await generate_year(session, reference_date=BEFORE_THE_YEAR)

    written = await session.execute(
        text("""
            SELECT count(*) FROM planned_sessions
            JOIN school_days ON school_days.id = planned_sessions.school_day_id
            WHERE school_days.date = :held
        """),
        {"held": held},
    )

    assert report.days_untouched == (held,)
    assert report.days_written == TAUGHT_DAYS - 1
    assert written.scalar_one() == 0


async def test_the_creneaux_of_a_day_are_numbered_in_the_order_they_run(
    session: AsyncSession,
) -> None:
    """``position`` is what the cahier journal is printed in (§7 écran 3)."""
    await generate_year(session, reference_date=BEFORE_THE_YEAR)

    out_of_order = await session.execute(
        text("""
            SELECT count(*) FROM (
                SELECT planned_sessions.position,
                       lag(timetable_slots.starts_at) OVER window_of_day AS previous,
                       timetable_slots.starts_at
                FROM planned_sessions
                JOIN timetable_slots ON timetable_slots.id = planned_sessions.timetable_slot_id
                WINDOW window_of_day AS (
                    PARTITION BY planned_sessions.school_day_id
                    ORDER BY planned_sessions.position
                )
            ) AS ordered
            WHERE previous IS NOT NULL AND previous > starts_at
        """)
    )

    assert out_of_order.scalar_one() == 0


async def test_a_seance_never_links_an_item_of_another_matiere(session: AsyncSession) -> None:
    """A link is a claim about the programme; a wrong one is worse than none."""
    await generate_year(session, reference_date=BEFORE_THE_YEAR)

    crossed = await session.execute(
        text("""
            SELECT count(*) FROM planned_session_program_items AS link
            JOIN planned_sessions ON planned_sessions.id = link.planned_session_id
            JOIN program_items ON program_items.id = link.program_item_id
            WHERE planned_sessions.subject_id IS DISTINCT FROM program_items.subject_id
        """)
    )

    assert crossed.scalar_one() == 0


async def test_the_programme_keeps_the_order_the_source_prints_it_in(
    session: AsyncSession,
) -> None:
    """Without ``source_order`` the progression would follow ``gen_random_uuid()``."""
    stored = await session.execute(text("SELECT title FROM program_items ORDER BY source_order"))

    assert [row.title for row in stored.all()] == [item.title for item in load_program_items()]
