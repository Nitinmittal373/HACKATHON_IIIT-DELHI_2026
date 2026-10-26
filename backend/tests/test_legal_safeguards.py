"""Facts, not verdicts; no source, no claim; and the right of reply."""

import json
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import create_app
from app.models import Finding
from tests.conftest import FIXED_NOW, make_settings, make_web, read_events
from tests.fakes import load_recording
from tests.test_recorded_check import check

SECRET = "s3cret-value"  # noqa: S105
# Words that accuse. Titles state what a record says and leave the judgement to the reader.
BANNED = (
    "fraud", "scam", "cheat", "crook", "thief", "loot", "criminal", "swindl", "con man",
    "rogue", "dishonest", "liar", "ponzi", "cheater",
)  # fmt: skip


def test_no_finding_title_of_the_recorded_check_accuses_anyone(tmp_path: Path) -> None:
    titles = [f["title"] for f in check(tmp_path)["report"]["findings"]]
    assert titles
    for title in titles:
        assert not [w for w in BANNED if w in title.lower()], title


def test_the_e2e_fixture_titles_are_factual_too() -> None:
    fixtures = Path(__file__).resolve().parents[2] / "frontend" / "e2e" / "fixtures"
    for path in fixtures.glob("report*.json"):
        for finding in json.loads(path.read_text(encoding="utf-8"))["findings"]:
            assert not [w for w in BANNED if w in finding["title"].lower()], finding["title"]


def make_finding(url: str) -> Finding:
    return Finding(
        id="f1",
        source="uprera",
        kind="x",
        title="A fact",
        verdict="review",
        reliability="primary",
        source_url=url,
        read_on=date(2026, 10, 25),
    )


@pytest.mark.parametrize("url", ["", "   ", "not a link", "javascript:alert(1)"])
def test_a_finding_without_a_web_source_cannot_exist(url: str) -> None:
    with pytest.raises(ValidationError):
        make_finding(url)


def test_a_finding_with_a_web_source_is_accepted() -> None:
    assert make_finding("https://www.up-rera.in/x").source_url


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    app = create_app(
        make_settings(tmp_path, webhook_secret=SECRET),
        web=make_web().replay(load_recording("check_8334.json")),
        clock=lambda: FIXED_NOW,
        cache_dir=None,
    )
    return TestClient(app)


def start_check(client: TestClient) -> str:
    check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
    read_events(client, check_id)
    return check_id


def test_a_correction_is_stored_and_only_the_operator_can_read_the_log(client: TestClient) -> None:
    with client:
        report_id = start_check(client)
        sent = client.post(
            "/api/corrections",
            json={"report_id": report_id, "finding_id": "f-1", "message": "The date is wrong."},
        )
        assert sent.status_code == 201

        assert client.get("/api/corrections").status_code == 401
        assert client.get("/api/corrections", headers={"X-Webhook-Secret": "no"}).status_code == 401
        log = client.get("/api/corrections", headers={"X-Webhook-Secret": SECRET}).json()
        assert [(c["report_id"], c["finding_id"], c["message"]) for c in log] == [
            (report_id, "f-1", "The date is wrong.")
        ]


def test_a_correction_needs_a_real_report_and_a_message(client: TestClient) -> None:
    with client:
        missing = client.post("/api/corrections", json={"report_id": "a" * 32, "message": "wrong!"})
        assert missing.status_code == 404
        report_id = start_check(client)
        assert (
            client.post(
                "/api/corrections", json={"report_id": report_id, "message": ""}
            ).status_code
            == 422
        )
        extra = {"report_id": report_id, "message": "wrong!", "admin": True}
        assert client.post("/api/corrections", json=extra).status_code == 422


def test_corrections_are_rate_limited(tmp_path: Path) -> None:
    app = create_app(
        make_settings(tmp_path, rate_limit_per_minute=1),
        web=make_web().replay(load_recording("check_8334.json")),
        clock=lambda: FIXED_NOW,
        cache_dir=None,
    )
    with TestClient(app) as client:
        body = {"report_id": "a" * 32, "message": "wrong!"}
        client.post("/api/corrections", json=body)
        assert client.post("/api/corrections", json=body).status_code == 429
