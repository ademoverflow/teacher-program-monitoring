"""Running the generation from the API, and asking before it overwrites.

The generation itself is Phase 3's (``services/planning``): it is pure, deterministic and
takes half a second for 1740 séances, which fits inside a request — so this is a call, not
a background task (ADR-0020).

What is new here is the question §7 écran 5 asks: « confirmation explicite avant d'écraser
une période déjà entamée ». A période is under way when it holds jours the generator would
refuse to touch — the past ones and the ones a cahier journal already holds (§10). Those
days are safe either way; the confirmation is about the rest of the période, which a
re-generation does rewrite.
"""

import datetime
import time
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.base import table_of
from core.models.calendar import Period, SchoolDay, Week
from core.models.journal import JournalEntry
from core.models.planning import PlannedSession
from core.schemas import (
    GenerationReportOut,
    GenerationStatus,
    PeriodGenerationState,
    ProblemOut,
)
from core.services.planning.writer import GenerationReport, generate_year


@dataclass(frozen=True, slots=True)
class ConfirmationRequiredError(Exception):
    """Périodes already under way that the caller has not said to overwrite."""

    periods: tuple[str, ...]


async def _protected_days(session: AsyncSession, reference_date: datetime.date) -> dict[str, int]:
    """Count, per période, the jours a re-generation would leave exactly as they are."""
    days, weeks, periods, entries = (
        table_of(SchoolDay),
        table_of(Week),
        table_of(Period),
        table_of(JournalEntry),
    )
    held = select(entries.c.school_day_id).distinct()
    rows = (
        await session.execute(
            select(periods.c.code, func.count().label("protected"))
            .select_from(days)
            .join(weeks, weeks.c.id == days.c.week_id)
            .join(periods, periods.c.id == weeks.c.period_id)
            .where(or_(days.c.date < reference_date, days.c.id.in_(held)))
            .group_by(periods.c.code)
        )
    ).all()
    return {row.code: row.protected for row in rows}


async def _sessions_per_period(session: AsyncSession) -> dict[str, int]:
    """Count the séances already written, per période."""
    sessions, days, weeks, periods = (
        table_of(PlannedSession),
        table_of(SchoolDay),
        table_of(Week),
        table_of(Period),
    )
    rows = (
        await session.execute(
            select(periods.c.code, func.count().label("written"))
            .select_from(sessions)
            .join(days, days.c.id == sessions.c.school_day_id)
            .join(weeks, weeks.c.id == days.c.week_id)
            .join(periods, periods.c.id == weeks.c.period_id)
            .group_by(periods.c.code)
        )
    ).all()
    return {row.code: row.written for row in rows}


async def generation_status(
    session: AsyncSession, reference_date: datetime.date
) -> GenerationStatus:
    """Say what a generation would find if it ran now, période by période.

    §7 écran 5 asks the teacher before overwriting a période already under way, and this is
    what lets the question be asked before the request rather than after a refusal.
    """
    periods = table_of(Period)
    protected = await _protected_days(session, reference_date)
    written = await _sessions_per_period(session)
    rows = (await session.execute(select(periods).order_by(periods.c.code))).all()
    return GenerationStatus(
        reference_date=reference_date,
        session_count=sum(written.values()),
        periods=[
            PeriodGenerationState(
                code=row.code,
                label=row.label,
                starts_on=row.starts_on,
                ends_on=row.ends_on,
                session_count=written.get(row.code, 0),
                protected_days=protected.get(row.code, 0),
                is_started=protected.get(row.code, 0) > 0,
            )
            for row in rows
        ],
    )


def _rendered(report: GenerationReport, seconds: float) -> GenerationReportOut:
    """Render a rapport de validation for the API, keeping every line and its nature."""
    return GenerationReportOut(
        periods=list(report.periods),
        sessions_planned=report.sessions_planned,
        sessions_written=report.sessions_written,
        days_written=report.days_written,
        days_untouched=list(report.days_untouched),
        days_off=report.days_off,
        program_links=report.program_links,
        sequences_placed=report.sequences_placed,
        alternations=report.alternations,
        problems=[
            ProblemOut(kind=problem.kind.value, message=problem.message)
            for problem in report.problems
        ],
        error_count=len(report.errors),
        is_clean=report.is_clean,
        seconds=round(seconds, 3),
    )


async def run_generation(
    session: AsyncSession,
    *,
    reference_date: datetime.date,
    periods: Sequence[str] | None,
    confirm: bool,
) -> GenerationReportOut:
    """Generate the year, or the given périodes, and return the rapport de validation.

    Raises ``ConfirmationRequired`` when a targeted période is already under way and the
    caller did not confirm. The jours passés and the cahiers journaux are never written
    over either way — that is the generator's own rule (§10); the confirmation is about
    the rest of the période, which a re-generation does rewrite.
    """
    if not confirm:
        status = await generation_status(session, reference_date)
        wanted = set(periods) if periods else {state.code for state in status.periods}
        started = tuple(
            sorted(
                state.code for state in status.periods if state.is_started and state.code in wanted
            )
        )
        if started:
            raise ConfirmationRequiredError(periods=started)

    started_at = time.perf_counter()
    report = await generate_year(session, reference_date=reference_date, periods=periods)
    await session.commit()
    return _rendered(report, time.perf_counter() - started_at)
