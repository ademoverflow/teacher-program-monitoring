"""Settings tests: the app must boot with a minimal ``.env``."""

import pytest
from core.settings import Settings

ENV_KEYS = (
    "CORE_SERVER_HOST",
    "CORE_SERVER_PORT",
    "DATABASE_URL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
    "DEV_MODE",
)
DEFAULT_PORT = 80


def test_settings_boot_without_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every setting has a default: no environment variable is required."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    assert settings.core_server_host == "0.0.0.0"
    assert settings.core_server_port == DEFAULT_PORT
    assert settings.database_url.startswith("postgresql://")
    assert settings.anthropic_api_key == ""
    assert settings.anthropic_model == "claude-sonnet-5"
    assert settings.dev_mode is False


def test_settings_read_anthropic_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Anthropic settings are overridable through the environment."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-5")

    settings = Settings(_env_file=None)

    assert settings.anthropic_api_key == "sk-test"
    assert settings.anthropic_model == "claude-opus-5"
