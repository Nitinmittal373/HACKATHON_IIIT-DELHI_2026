"""Settings read from the environment and the repo-root .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_DIR / 'data' / 'neevcheck.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    tinyfish_api_key: SecretStr
    agent_concurrency: int = Field(default=2, ge=1, le=10)
    frontend_origins: str = "http://localhost:3000"
    rate_limit_per_minute: int = Field(default=6, ge=1)
    # Only enable behind a proxy you control; otherwise clients could fake their IP.
    trust_forwarded_for: bool = False
    database_url: str = DEFAULT_DATABASE_URL
    fetch_timeout_seconds: float = Field(default=60, gt=0)
    agent_timeout_seconds: float = Field(default=300, gt=0)
    # TinyFish only accepts a step limit on accounts in its beta; every run is still capped
    # by agent_timeout_seconds. Turn this on once the account is enabled.
    agent_send_max_steps: bool = False

    # Every live check costs money, Sentinel's included; past this many a day none may start.
    max_checks_per_day: int = Field(default=30, ge=1)
    # How often Sentinel re-checks watched projects; 0 turns the built-in schedule off (an
    # external cron can still call POST /api/sentinel/run).
    sentinel_interval_hours: float = Field(default=168, ge=0)
    webhook_secret: SecretStr | None = None
    # Optional email delivery of alerts; without smtp_host alerts are only stored.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from: str | None = None

    @field_validator(
        "webhook_secret", "smtp_host", "smtp_user", "smtp_password", "smtp_from", mode="before"
    )
    @classmethod
    def blank_means_unset(cls, value: object) -> object:
        # .env.example lists these with no value; that must read as "not configured".
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("tinyfish_api_key")
    @classmethod
    def key_not_blank(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("TINYFISH_API_KEY is empty")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


class MissingSettingError(RuntimeError):
    pass


@lru_cache
def load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]  # values come from the environment
    except ValidationError as error:
        names = ", ".join(str(e["loc"][0]).upper() for e in error.errors())
        raise MissingSettingError(
            f"Invalid or missing setting(s): {names}. "
            "Set them in the repo-root .env file (see .env.example)."
        ) from None
