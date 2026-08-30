from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core settings.

    Every field has a default so the app boots with a minimal ``.env`` (this is a
    local, single-user application without login).
    """

    # Server settings
    core_server_host: str = "0.0.0.0"
    core_server_port: int = 80
    database_url: str = "postgresql://admin:admin@db:5432/db"

    # JWT / cookie settings — unused by the app (no login), kept for the security helpers
    core_jwt_algorithm: str = "HS256"
    core_jwt_type: str = "Bearer"
    core_jwt_secret_key: str = "local-no-login-secret"  # noqa: S105
    core_jwt_expiration_timedelta_minutes: int = 1440
    webapp_url: str = "http://localhost:12108"
    cookie_domain: str = "localhost"

    # Anthropic API (AI feedback on the daily journal — wired in Phase 7)
    # An empty key means the AI feature is disabled.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    # Development mode (controls cookie security settings + uvicorn reload)
    dev_mode: bool = False

    @property
    def cookie_secure(self) -> bool:
        """Return True for HTTPS-only cookies in production."""
        return not self.dev_mode

    @property
    def cookie_samesite(self) -> Literal["lax", "strict", "none"] | None:
        """Return 'none' for cross-origin in production, 'lax' for dev."""
        return "lax" if self.dev_mode else "none"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Get settings cached."""
    return Settings()
