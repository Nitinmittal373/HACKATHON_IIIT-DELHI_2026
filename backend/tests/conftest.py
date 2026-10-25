import os

# app.main builds a module-level app on import; give it a dummy key so importing
# never depends on a real .env. Tests build their own apps with explicit settings.
os.environ.setdefault("TINYFISH_API_KEY", "test-key-not-real")

import json  # noqa: E402
from collections.abc import Iterator  # noqa: E402
from datetime import UTC, datetime  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.uprera_links import rera_ids_in, summary_url  # noqa: E402
from tests.fakes import FakeWebClient, load_page, load_search  # noqa: E402

URL_8334 = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334"
URL_6742 = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=6742"
# The day the fixtures were recorded, so months-past-end-date never drift.
FIXED_NOW = datetime(2026, 10, 25, 4, 0, tzinfo=UTC)


def make_settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "tinyfish_api_key": "test-key-not-real",
        "database_url": f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        "rate_limit_per_minute": 100,
        **overrides,
    }
    return Settings(_env_file=None, **values)  # type: ignore[arg-type, call-arg]


def make_web() -> FakeWebClient:
    return FakeWebClient(
        searches={
            "Gaur City UP RERA project": load_search("search_gaur_city.json"),
            "Supertech Eco Village UP RERA project": load_search(
                "search_supertech_eco_village.json"
            ),
            "UPRERAPRJ8334 UP RERA project": load_search("search_uprera_8334.json"),
        },
        pages={
            URL_8334: load_page("uprera_8334.html"),
            URL_6742: load_page("uprera_6742.html"),
            summary_url_8334(): load_page("uprera_summary_8334.html"),
        },
    )


def summary_url_8334() -> str:
    """The Projectsummary link recorded in search_uprera_8334.json."""
    for hit in load_search("search_uprera_8334.json"):
        if (url := summary_url(hit.url)) and "UPRERAPRJ8334" in rera_ids_in(hit):
            return url
    raise AssertionError("search_uprera_8334.json has no Projectsummary link for 8334")


def read_events(client: TestClient, check_id: str) -> list[dict[str, object]]:
    """Follow a check's event stream to its end and return each event's JSON."""
    events = []
    with client.stream("GET", f"/api/checks/{check_id}/events") as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        for line in response.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line.removeprefix("data: ")))
    return events


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return make_settings(tmp_path)


@pytest.fixture
def web() -> FakeWebClient:
    return make_web()


@pytest.fixture
def client(settings: Settings, web: FakeWebClient) -> Iterator[TestClient]:
    with TestClient(create_app(settings, web=web, clock=lambda: FIXED_NOW)) as test_client:
        yield test_client
