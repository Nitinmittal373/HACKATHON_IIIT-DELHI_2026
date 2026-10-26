"""A whole check for a state other than UP, replayed from recorded Search results."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import make_settings, read_events
from tests.fakes import FIXTURES, FakeWebClient


def client_for(tmp_path: Path, fixture: str) -> TestClient:
    recording = json.loads((FIXTURES / fixture).read_text(encoding="utf-8"))
    app = create_app(make_settings(tmp_path), web=FakeWebClient().replay(recording))
    return TestClient(app)


def run_check(client: TestClient, body: dict[str, str]) -> dict:  # type: ignore[type-arg]
    started = client.post("/api/checks", json=body)
    assert started.status_code == 202
    check_id = started.json()["id"]
    read_events(client, check_id)
    return client.get(f"/api/checks/{check_id}/report").json()


def test_a_maharashtra_check_scores_with_unread_sources_not_penalties(tmp_path: Path) -> None:
    with client_for(tmp_path, "states_mh.json") as client:
        report = run_check(client, {"rera_id": "P99000055716"})

    assert (report["state"], report["state_name"]) == ("MH", "Maharashtra")
    assert report["project"]["state"] == "MH"
    assert report["check"]["state"] == "MH"
    score = report["score_v2"]
    # Too little was read to rate the project: provisional, low confidence, nothing taken off.
    assert score["provisional"] and score["confidence"] < 0.5
    assert score["value"] == 900
    codes = [r["code"] for r in score["reason_codes"]]
    assert "R12" in codes
    assert all(driver["points"] == 0 for driver in score["drivers"] if driver["code"] == "R12")
    assert "P5" in score["pillars_unread"]  # land dues exist for UP only


def test_search_snippet_findings_carry_the_portal_page_and_the_words(tmp_path: Path) -> None:
    with client_for(tmp_path, "states_mh.json") as client:
        report = run_check(client, {"rera_id": "P99000055716"})

    finding = next(f for f in report["findings"] if f["kind"] == "registration")
    assert finding["source_url"].startswith("https://maharera.maharashtra.gov.in/")
    assert finding["reliability"] == "primary"
    assert finding["via"] == "search_snippet"
    assert "P99000055716" in finding["snippet"]
    assert "MahaRERA" in finding["title"]


def test_a_number_the_portal_does_not_show_fails_the_check(tmp_path: Path) -> None:
    with client_for(tmp_path, "states_mh.json") as client:
        started = client.post("/api/checks", json={"rera_id": "P51800099999"}).json()
        events = read_events(client, started["id"])
        report = client.get(f"/api/checks/{started['id']}/report")

    assert events[-1]["data"]["status"] == "failed"
    assert report.status_code == 409


def test_states_endpoint_lists_every_portal_with_its_level(client: TestClient) -> None:
    states = client.get("/api/states").json()
    by_code = {s["code"]: s for s in states}
    assert by_code["UP"]["coverage"] == "full"
    assert by_code["MH"]["coverage"] == "search_only"
    assert by_code["MH"]["examples"] and by_code["TG"]["examples"] == []
    assert len(states) >= 20


def test_search_rejects_an_unknown_state_and_a_check_for_a_wrong_link(client: TestClient) -> None:
    assert (
        client.get("/api/projects/search", params={"q": "Gaur", "state": "ZZ"}).status_code == 422
    )
    wrong = {"rera_id": "P99000055716", "details_url": "https://evil.example/maharera"}
    assert client.post("/api/checks", json=wrong).status_code == 422
    assert (
        client.post("/api/checks", json={"rera_id": "P99000055716", "state": "UP"}).status_code
        == 422
    )
