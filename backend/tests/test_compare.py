"""Comparing checks, replayed from the recorded check of UPRERAPRJ8334 and the 6742 page."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.compare import best_on_records, compared
from app.main import create_app
from app.models import Project, Report
from tests.conftest import make_settings, make_web, read_events
from tests.fakes import load_recording

RECORDING = load_recording("check_8334.json")
CAPTURED_AT = datetime.fromisoformat(RECORDING["captured_at"])


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    web = make_web().replay(RECORDING)
    app = create_app(make_settings(tmp_path), web=web, clock=lambda: CAPTURED_AT, cache_dir=None)
    with TestClient(app) as test_client:
        yield test_client


def finished_check(client: TestClient, rera_id: str, fresh: bool = False) -> str:
    body = {"rera_id": rera_id, "fresh": fresh}
    check_id = client.post("/api/checks", json=body).json()["id"]
    read_events(client, check_id)
    return check_id


def test_rows_come_from_the_records_and_unread_stays_unknown(client: TestClient) -> None:
    eco, avenue = finished_check(client, "UPRERAPRJ8334"), finished_check(client, "UPRERAPRJ6742")

    response = client.get("/api/checks/compare", params={"ids": f"{eco},{avenue}"})
    assert response.status_code == 200
    first, second = response.json()["projects"]

    assert first["project"]["name"] == "SUPERTECH ECO VILLAGE-I PHASE I-C"
    assert (first["score"], first["band"], first["confidence"]) == (68, "Moderate", 0.71)
    assert first["delay_months"] == 105
    assert (first["project_complaints"], first["promoter_complaints"]) == (15, 2803)
    # A news report alone: shown for checking, never scored as a verified insolvency.
    assert first["insolvency"] == "unverified"
    assert first["company_status"] == "Active"
    assert first["unread"] == ["land_dues", "consumer_cases"]
    assert [f["points"] for f in first["top_findings"]] == [-14.0, -9.0, -6.0]
    assert all(f["source_url"].startswith("https://") for f in first["top_findings"])
    execution = next(a for a in first["areas"] if a["area"] == "execution")
    assert (execution["lost"], execution["max"]) == (14.0, 20.0)

    assert second["project"]["rera_id"] == "UPRERAPRJ6742"
    assert second["delay_months"] is not None
    # Nothing was recorded for this promoter's company, so the row says unknown, not clean.
    assert second["company_status"] is None


def test_a_thin_check_is_never_ranked_against_a_full_one(client: TestClient) -> None:
    eco, avenue = finished_check(client, "UPRERAPRJ8334"), finished_check(client, "UPRERAPRJ6742")
    body = client.get("/api/checks/compare", params={"ids": f"{eco},{avenue}"}).json()

    confidences = {p["project"]["rera_id"]: p["confidence"] for p in body["projects"]}
    assert confidences["UPRERAPRJ6742"] < 0.5
    assert (body["best"], body["reason"]) == (None, "not_enough_evidence")


def test_equal_scores_are_a_tie(client: TestClient) -> None:
    first = finished_check(client, "UPRERAPRJ8334")
    again = finished_check(client, "UPRERAPRJ8334", fresh=True)
    body = client.get("/api/checks/compare", params={"ids": f"{first},{again}"}).json()
    assert (body["best"], body["reason"]) == (None, "tie")


def test_the_best_score_wins_among_checks_read_well_enough(client: TestClient) -> None:
    eco = finished_check(client, "UPRERAPRJ8334")
    report = Report.model_validate(client.get(f"/api/checks/{eco}/report").json())
    base = compared(report)
    better = base.model_copy(update={"check_id": "b" * 32, "score": 81})
    thin = {"check_id": "c" * 32, "score": 95, "confidence": 0.29}
    higher_but_thin = base.model_copy(update=thin)

    assert best_on_records([base, better, higher_but_thin]) == ("b" * 32, "best_score")


@pytest.mark.parametrize("ids", ["a" * 32, ",".join(f"{n:032x}" for n in range(4)), "x,y"])
def test_compare_needs_two_or_three_valid_ids(client: TestClient, ids: str) -> None:
    assert client.get("/api/checks/compare", params={"ids": ids}).status_code == 422


def test_unknown_and_unfinished_checks_are_refused(client: TestClient) -> None:
    eco = finished_check(client, "UPRERAPRJ8334")
    assert client.get("/api/checks/compare", params={"ids": f"{eco},{'e' * 32}"}).status_code == 404

    store = client.app.state.store  # type: ignore[attr-defined]
    store.save_project(Project(rera_id="UPRERAPRJ1", details_url="https://www.up-rera.in/x?id=1"))
    store.create_check("f" * 32, "UPRERAPRJ1", datetime(2026, 10, 25, tzinfo=UTC))
    response = client.get("/api/checks/compare", params={"ids": f"{eco},{'f' * 32}"})
    assert response.status_code == 409
