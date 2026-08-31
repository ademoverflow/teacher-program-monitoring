"""Launching the generation of the programmation, and its rapport de validation."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.clock import today
from core.database import get_session
from core.schemas import GenerationReportOut, GenerationStatus
from core.services.generation import (
    ConfirmationRequiredError,
    generation_status,
    run_generation,
)

generation_router = APIRouter(prefix="/generation", tags=["Génération"])


class GenerationRequest(BaseModel):
    """What to generate, and whether the teacher has agreed to overwrite.

    ``periods`` empty or absent means the whole year. ``confirm`` is §7 écran 5's explicit
    confirmation: without it, a période already under way is refused rather than rewritten.
    """

    periods: list[str] | None = None
    confirm: bool = False


@generation_router.get("")
async def read_generation_status(
    session: Annotated[AsyncSession, Depends(get_session)],
    on: Annotated[date, Depends(today)],
) -> GenerationStatus:
    """Say, période by période, what a generation would find and what it would not touch.

    A période is « déjà entamée » when it holds jours the generation refuses to write over
    — those in the past and those a cahier journal already holds (§10).
    """
    return await generation_status(session, on)


@generation_router.post("")
async def run(
    body: GenerationRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    on: Annotated[date, Depends(today)],
) -> GenerationReportOut:
    """Generate the year, or the given périodes, and return the rapport de validation.

    Synchronous: the whole year is 1740 séances and half a second, so there is nothing for
    a background task to buy (ADR-0020). Answers 409 when a targeted période is already
    under way and `confirm` is false.
    """
    try:
        return await run_generation(
            session, reference_date=on, periods=body.periods or None, confirm=body.confirm
        )
    except ConfirmationRequiredError as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Périodes déjà entamées : "
            + ", ".join(error.periods)
            + ". Confirmez pour les régénérer.",
        ) from error
