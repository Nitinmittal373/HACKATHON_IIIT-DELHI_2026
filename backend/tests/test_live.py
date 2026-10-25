"""One end-to-end check against the real TinyFish API.

Deselected by default (it costs credit and needs the network). Run it with:

    pytest -m live
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app
from tests.conftest import read_events

DUMMY_KEY = "test-key-not-real"


def live_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    # conftest sets a dummy key for imports; drop it so the real one (env or .env) is used.
    if os.environ.get("TINYFISH_API_KEY") == DUMMY_KEY:
        monkeypatch.delenv("TINYFISH_API_KEY")
    try:
        return Settings(database_url=f"sqlite:///{(tmp_path / 'live.db').as_posix()}")  # type: ignore[call-arg]
    except ValidationError:
        pytest.skip("TINYFISH_API_KEY is not set")


@pytest.mark.live
def test_live_check_for_8334(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = live_settings(tmp_path, monkeypatch)

    with TestClient(create_app(settings)) as client:
        search = client.get("/api/projects/search", params={"q": "UPRERAPRJ8334"}).json()
        assert search["candidates"][0]["promoter"] == "SUPERTECH LIMITED"

        check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
        events = read_events(client, check_id)
        assert events[-1]["data"]["status"] == "completed"

        report = client.get(f"/api/checks/{check_id}/report").json()
        assert "registration" in {f["kind"] for f in report["findings"]}

        # What the other sources find changes from day to day; what must hold is the honesty rules.
        sources = {run["source"]: run["status"] for run in report["check"]["sources"]}
        assert sources["uprera"] == "completed"
        assert report["score"]["confidence"] > 0.5
        for finding in report["findings"]:
            assert finding["source_url"].startswith("https://")
            assert finding["read_on"] and finding["reliability"]
