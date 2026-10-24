import os

# app.main builds a module-level app on import; give it a dummy key so importing
# never depends on a real .env. Tests build their own apps with explicit settings.
os.environ.setdefault("TINYFISH_API_KEY", "test-key-not-real")

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


def make_settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "tinyfish_api_key": "test-key-not-real",
        "database_url": f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        "rate_limit_per_minute": 100,
        **overrides,
    }
    return Settings(_env_file=None, **values)  # type: ignore[arg-type, call-arg]


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return make_settings(tmp_path)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client
