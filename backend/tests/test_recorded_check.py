"""The full check of UPRERAPRJ8334 replayed from what the real sites answered on 25 Oct 2026.

The recording comes from `python -m scripts.capture_fixtures check_8334.json`. Nothing here
touches the network, and the clock is fixed to the moment of the recording, so the score never
drifts. A few tests change one agent's answer to show how a CAPTCHA, an empty answer or a
timeout is handled.
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app
from app.tinyfish import AgentDone
from tests.conftest import make_settings, make_web, read_events
from tests.fakes import FakeWebClient, load_recording

RECORDING = load_recording("check_8334.json")
CAPTURED_AT = datetime.fromisoformat(RECORDING["captured_at"])
INSOLVENCY_PAGE = next(a["url"] for a in RECORDING["agents"] if "fortuneindia" in a["url"])
CONSUMER_PAGE = "https://e-jagriti.gov.in/advance-case-search"


def check(tmp_path: Path, change: Callable[[FakeWebClient], None] | None = None) -> dict[str, Any]:
    """Run the recorded check, optionally changing what one source's agent answered."""
    web = make_web().replay(RECORDING)
    if change:
        change(web)
    app = create_app(make_settings(tmp_path), web=web, clock=lambda: CAPTURED_AT, cache_dir=None)
    with TestClient(app) as client:
        check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
        events = read_events(client, check_id)
        report = client.get(f"/api/checks/{check_id}/report").json()
    return {"report": report, "events": events, "web": web}


def finding_titles(report: dict[str, Any]) -> list[str]:
    return [f["title"] for f in report["findings"]]


def test_the_recorded_check_gives_a_stable_score(tmp_path: Path) -> None:
    score = check(tmp_path)["report"]["score"]

    assert (score["value"], score["band"], score["confidence"]) == (68, "Moderate", 0.71)
    assert score["hard_stop"] is False
    assert score["checks_unread"] == ["land_dues", "consumer_cases"]
    assert [d["points"] for d in score["drivers"]] == [-14.0, -9.0, -6.0, -1.0, -1.0, -1.0]


def test_e_jagriti_stops_at_its_captcha_and_the_other_sources_are_read(tmp_path: Path) -> None:
    result = check(tmp_path)

    statuses = {run["source"]: run["status"] for run in result["report"]["check"]["sources"]}
    assert statuses.pop("consumer") == "blocked"
    assert set(statuses.values()) == {"completed"}
    assert len(statuses) == 5
    assert result["events"][-1]["type"] == "check.completed"


def test_the_findings_are_exactly_these(tmp_path: Path) -> None:
    titles = finding_titles(check(tmp_path)["report"])

    assert "Registered on UP-RERA on 09 Aug 2017" in titles
    assert (
        "Completion date on record (30 Dec 2017) passed 105 months ago; "
        "project still listed as Ongoing"
    ) in titles
    assert "Company status: Active (CIN U74899DL1995PLC074422)" in titles
    assert "Insolvency application against SUPERTECH LIMITED was admitted on 25 Mar 2022" in titles
    assert not any("consumer case" in t for t in titles)
    assert sum(t.startswith("News on delays") for t in titles) == 3
    assert len(titles) == 11


def test_every_finding_names_its_source_and_when_it_was_read(tmp_path: Path) -> None:
    for finding in check(tmp_path)["report"]["findings"]:
        assert finding["source_url"].startswith("https://")
        assert finding["read_on"] == "2026-10-25"
        assert finding["read_at"]
        assert finding["reliability"] in ("primary", "secondary")


def test_a_news_report_alone_does_not_stop_the_score(tmp_path: Path) -> None:
    report = check(tmp_path)["report"]

    [unverified] = [f for f in report["findings"] if f["kind"] == "insolvency_scope_unverified"]
    assert unverified["reliability"] == "secondary"
    assert "No court order was read" in unverified["title"]
    assert not any(f["kind"] == "insolvency_scope" for f in report["findings"])
    assert report["score"]["hard_stop"] is False


def test_the_supreme_court_order_is_context_and_costs_nothing(tmp_path: Path) -> None:
    report = check(tmp_path)["report"]

    [order] = [f for f in report["findings"] if f["kind"] == "court_order"]
    assert order["verdict"] == "context"
    assert order["source_url"].startswith("https://api.sci.gov.in/")
    assert all(d["finding_id"] != order["id"] for d in report["score"]["drivers"])


def test_a_captcha_on_e_jagriti_lowers_confidence_and_leaves_the_score_alone(
    tmp_path: Path,
) -> None:
    def captcha(web: FakeWebClient) -> None:
        web.agent_runs[CONSUMER_PAGE] = [
            AgentDone("COMPLETED", {"total_cases": None, "cases": [], "captcha_seen": True})
        ]

    result = check(tmp_path, captcha)
    report = result["report"]

    consumer = next(r for r in report["check"]["sources"] if r["source"] == "consumer")
    assert (consumer["status"], consumer["message"]) == (
        "blocked",
        "This page asks for a CAPTCHA. We never bypass one",
    )
    assert any(
        e["type"] == "source.blocked" and e["source"] == "consumer" for e in result["events"]
    )
    assert (report["score"]["value"], report["score"]["confidence"]) == (68, 0.71)
    assert "consumer_cases" in report["score"]["checks_unread"]
    assert not any(f["source"] == "consumer" for f in report["findings"])


def test_an_empty_completed_answer_is_unread_not_clean(tmp_path: Path) -> None:
    def nothing_found(web: FakeWebClient) -> None:
        empty = {"admitted": None, "admitted_on": None, "covers_whole_company": None}
        web.agent_runs[INSOLVENCY_PAGE] = [
            AgentDone("COMPLETED", empty | {"projects_named": [], "captcha_seen": False})
        ]

    report = check(tmp_path, nothing_found)["report"]

    assert "insolvency" in report["score"]["checks_unread"]
    assert not any(f["source"] == "insolvency" for f in report["findings"])
    assert report["score"]["value"] == 68  # unread never moves the score


def test_a_run_that_times_out_is_blocked_as_a_timeout_and_never_retried(tmp_path: Path) -> None:
    def too_slow(web: FakeWebClient) -> None:
        web.agent_runs[INSOLVENCY_PAGE] = [AgentDone("FAILED", None, "Run exceeded max duration")]

    result = check(tmp_path, too_slow)

    blocked = [e for e in result["events"] if e["type"] == "source.blocked"]
    reasons = {e["source"]: e["data"]["reason"] for e in blocked}
    assert reasons["insolvency"] == "timeout"
    assert "insolvency" in result["report"]["score"]["checks_unread"]
    starts = [call for call in result["web"].calls if call == ("agent", INSOLVENCY_PAGE)]
    assert len(starts) == 1


def test_an_agent_that_types_a_captcha_is_stopped_even_when_it_says_it_saw_none(
    tmp_path: Path,
) -> None:
    result = check(tmp_path)

    notes = [e["data"]["text"] for e in result["events"] if e["type"] == "source.progress"]
    consumer_notes = [
        e["data"]["text"]
        for e in result["events"]
        if e["type"] == "source.progress" and e["source"] == "consumer"
    ]
    assert consumer_notes[-1] == "Check CAPTCHA text and form state"
    assert not any("Enter CAPTCHA text" in note for note in notes)
    assert not any(f["source"] == "consumer" for f in result["report"]["findings"])
