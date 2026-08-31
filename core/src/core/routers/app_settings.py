"""The réglages the teacher can change — today, the two alternances."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.models.app_setting import AppSetting
from core.models.base import table_of
from core.schemas import SettingOut
from core.services.planning.inputs import ALTERNATION_PREFIX
from core.services.seed_files import AlternationSeed

settings_router = APIRouter(prefix="/settings", tags=["Réglages"])


class SettingUpdate(BaseModel):
    """A new value for one réglage."""

    value: Any


def _rendered(row: Any) -> SettingOut:  # noqa: ANN401 - a SQLAlchemy row, not a model
    """Render one réglage, saying whether the generation is what reads it."""
    return SettingOut(
        key=row.key,
        label=row.label,
        value=row.value,
        # The alternances are read when the year is generated, not when a page is drawn:
        # changing one moves nothing until the generation is re-run (ADR-0013).
        requires_generation=row.key.startswith(ALTERNATION_PREFIX),
    )


@settings_router.get("")
async def read_settings(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[SettingOut]:
    """Return the réglages, in a stable order."""
    settings = table_of(AppSetting)
    rows = (await session.execute(select(settings).order_by(settings.c.key))).all()
    return [_rendered(row) for row in rows]


@settings_router.put("/{key}")
async def edit_setting(
    key: str,
    body: SettingUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SettingOut:
    """Change one réglage, validated against the vocabulary that réglage is written in.

    An `alternance.*` value goes through the same model the seed loader uses, so
    `AlternationMode` stays spelled once and a value the generator could not read is
    refused here rather than at the next generation (ADR-0013).

    An unknown key is a 404 rather than a create: the réglages are the ones the
    application defines, not a free-form key/value store.
    """
    settings = table_of(AppSetting)
    existing = (await session.execute(select(settings).where(settings.c.key == key))).one_or_none()
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Aucun réglage « {key} »")

    if key.startswith(ALTERNATION_PREFIX):
        try:
            AlternationSeed.model_validate(body.value)
        except ValidationError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"Valeur d'alternance invalide : {error.error_count()} erreur(s)",
            ) from error

    await session.execute(update(settings).where(settings.c.key == key).values(value=body.value))
    await session.commit()
    row = (await session.execute(select(settings).where(settings.c.key == key))).one()
    return _rendered(row)
