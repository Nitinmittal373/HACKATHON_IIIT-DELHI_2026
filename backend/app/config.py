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
