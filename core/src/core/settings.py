from functools import lru_cache

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

    # Anthropic API (AI feedback on the daily journal — wired in Phase 7)
    # An empty key means the AI feature is disabled.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    # Development mode (uvicorn reload)
    dev_mode: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Get settings cached."""
    return Settings()
