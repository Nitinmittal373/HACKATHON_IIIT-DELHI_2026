"""Settings read from the environment and the repo-root .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, ValidationError, field_validator
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

    # Every live check spends TinyFish credit, Sentinel's included. These limits keep the bill
    # predictable; a day and a month are counted in Indian time.
    site_checks_per_day: int = Field(default=5, ge=1)
    site_checks_per_month: int = Field(default=60, ge=1)
    require_signin_for_checks: bool = True
    checks_per_account_per_day: int = Field(default=2, ge=1)
    # A finished check this recent is returned instead of starting another, for everyone.
    reuse_report_days: int = Field(default=7, ge=0)
    # "Re-check now" works once per project in this many days.
    recheck_min_days: int = Field(default=7, ge=0)
    # Search results (names, builders, localities, RERA numbers) are kept this many days.
    search_cache_days: int = Field(default=7, ge=0)
    searches_per_ip_per_day: int = Field(default=15, ge=1)
    searches_per_ip_per_day_signed_in: int = Field(default=40, ge=1)
    # Searches that really run (a saved answer is free) across the whole site in an Indian day.
    site_searches_per_day: int = Field(default=200, ge=1)
    # Only these signed-in e-mails (comma separated) may start live checks when invite_only is on.
    invite_only: bool = False
    allowed_emails: str = ""
    # Sent as the X-Admin-Token header to read GET /api/admin/usage; without it that route is off.
    admin_token: SecretStr | None = None
    # UP-RERA numbers (comma separated) shown in the home page gallery when a check is saved.
    featured_rera_ids: str = ""
    # A watched project is re-checked when its last check is older than this; 0 turns the
    # built-in schedule off (an external cron can still call POST /api/sentinel/run).
    sentinel_interval_hours: float = Field(default=168, ge=0)
    # Re-checks the built-in schedule may start in one Indian day. Each one is a paid live check.
    sentinel_checks_per_day: int = Field(default=1, ge=1)
    # TinyFish Monitors bill on their own clock, outside the site budget, so they are off.
    sentinel_monitors: bool = False
    webhook_secret: SecretStr | None = None
    # Shared with the web app, which signs the short-lived sign-in token; without it the
    # account routes answer 503 and everything else works as before.
    auth_bridge_secret: SecretStr | None = None
    # This API's public address. With it, WEBHOOK_SECRET and SENTINEL_MONITORS=true, watching a
    # project also creates TinyFish monitors that call back here.
    public_base_url: str | None = None
    # The web app's public address, used for the stop-alerts link in every alert email.
    site_url: str | None = Field(
        default=None, validation_alias=AliasChoices("SITE_URL", "NEXT_PUBLIC_SITE_URL")
    )
    # Optional email delivery of alerts, through an HTTPS email API (preferred, because many
    # hosts block SMTP) or SMTP. With neither, alerts are only stored and shown in the app.
    email_provider: Literal["brevo", "resend"] = "brevo"
    email_api_key: SecretStr | None = None
    email_from: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from: str | None = None

    @field_validator(
        "webhook_secret",
        "auth_bridge_secret",
        "admin_token",
        "public_base_url",
        "site_url",
        "email_api_key",
        "email_from",
        "smtp_host",
        "smtp_user",
        "smtp_password",
        "smtp_from",
        mode="before",
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
    def allowed_email_set(self) -> frozenset[str]:
        return frozenset(e.strip().lower() for e in self.allowed_emails.split(",") if e.strip())

    @property
    def featured_ids(self) -> list[str]:
        return [i.strip().upper() for i in self.featured_rera_ids.split(",") if i.strip()]

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
