"""One display score: the 300-900 NeevScore appears on every response that shows a score."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.promoters import with_score
from app.db import ScoreRow
from app.main import create_app
from app.meta import build_meta
from app.models import DisplayScore
from app.scoring.v2 import weights as w
from app.scoring.v2.reasons import DATA_UNAVAILABLE, LABELS
from app.track_record import TrackedProject
from tests.conftest import make_settings, make_web, read_events
from tests.fakes import load_recording
from tests.test_sentinel import INSOLVENCY_PAGE, alerts, build_client, insolvency_answer, recheck
from tests.test_sentinel import run_check as run_sentinel_check
from tests.test_sentinel import watch as watch_project

RECORDING = load_recording("check_8334.json")
SCALE = range(w.SCALE_FLOOR, w.SCALE_TOP + 1)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    app = create_app(make_settings(tmp_path), web=make_web().replay(RECORDING), cache_dir=None)
    with TestClient(app) as test_client:
        yield test_client


def finished_check(client: TestClient, rera_id: str = "UPRERAPRJ8334", **body: object) -> str:
    check_id = client.post("/api/checks", json={"rera_id": rera_id, **body}).json()["id"]
    read_events(client, check_id)
    return check_id


def assert_display(display: dict[str, object]) -> None:
    assert display["value"] in SCALE
    assert display["band"] in {"Low", "Watch", "Elevated", "High", "insufficient_evidence"}
    assert set(display) == {
        "value",
        "provisional_value",
        "band",
        "hard_stop",
        "confidence",
        "provisional",
        "records_read",
        "records_total",
    }


def drop_v2(client: TestClient, check_id: str) -> None:
    """Make the check look like one stored before v2 existed."""
    store = client.app.state.store  # type: ignore[attr-defined]
    with store._sessions.begin() as session:  # noqa: SLF001
        row = session.get_one(ScoreRow, check_id)
        row.detail = {k: v for k, v in row.detail.items() if k != "v2"}


def test_the_report_and_the_check_carry_the_display_score(client: TestClient) -> None:
    check_id = finished_check(client)
    report = client.get(f"/api/checks/{check_id}/report").json()
    check = client.get(f"/api/checks/{check_id}").json()

    assert_display(report["display_score"])
    assert report["display_score"] == check["display_score"]
    assert report["display_score"]["value"] == report["score_v2"]["value"]
    # The classic score is still there for older clients.
    assert report["score"]["value"] == 68


def test_a_reused_check_carries_it_too(client: TestClient) -> None:
    first = finished_check(client)
    again = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"})
    assert again.status_code == 200
    assert again.json()["id"] == first
    assert_display(again.json()["display_score"])


def test_a_running_check_has_no_score_yet(client: TestClient) -> None:
    started = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()
    assert started["display_score"] is None
    read_events(client, started["id"])


def test_my_reports_and_the_home_page_carry_it(client: TestClient) -> None:
    check_id = finished_check(client)

    [listed] = client.get("/api/checks", params={"ids": check_id}).json()
    [recent] = client.get("/api/checks/recent").json()

    assert_display(listed["display_score"])
    assert listed["display_score"] == recent["display_score"]
    reasons = recent["reasons"]
    assert 0 < len(reasons) <= 3
    assert all(r["code"] != DATA_UNAVAILABLE and r["points"] < 0 for r in reasons)


def test_the_finished_event_carries_it(client: TestClient) -> None:
    check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
    events = read_events(client, check_id)
    done = events[-1]["data"]

    assert_display(done["display_score"])
    assert done["display_score"] == client.get(f"/api/checks/{check_id}").json()["display_score"]
    # A browser that joins after the run still gets the score from the replay.
    replay = read_events(client, check_id)[-1]["data"]
    assert replay["display_score"] == done["display_score"]


def test_compare_carries_it_and_ranks_by_it(client: TestClient) -> None:
    eco = finished_check(client)
    again = finished_check(client, fresh=True)
    body = client.get("/api/checks/compare", params={"ids": f"{eco},{again}"}).json()

    for project in body["projects"]:
        assert_display(project["display_score"])
        assert len(project["pillars"]) == len(w.PILLAR_WEIGHTS)
    # Equal 300-900 scores are a tie, whatever the classic scores say.
    assert (body["best"], body["reason"]) == (None, "tie")


def test_an_alert_carries_the_scores_before_and_after(tmp_path: Path) -> None:
    web = make_web().replay(RECORDING)
    with build_client(tmp_path, web) as client:
        run_sentinel_check(client)
        watch_project(client)
        web.agent_runs[INSOLVENCY_PAGE] = insolvency_answer(admitted_on="April 1, 2022")
        recheck(client)

        [alert] = alerts(client)
        assert_display(alert["old_display_score"])  # type: ignore[arg-type]
        assert_display(alert["new_display_score"])  # type: ignore[arg-type]
        # The classic fields stay for older clients.
        assert alert["old_score"] == alert["new_score"] == 68


def test_promoter_projects_show_the_score_of_a_check_we_hold(client: TestClient) -> None:
    check_id = finished_check(client)
    store = client.app.state.store  # type: ignore[attr-defined]
    expected = client.get(f"/api/checks/{check_id}").json()["display_score"]

    known = TrackedProject(rera_id="UPRERAPRJ8334", details_url="https://www.up-rera.in/x?id=8334")
    unknown = TrackedProject(rera_id="UPRERAPRJ1", details_url="https://www.up-rera.in/x?id=1")
    scored = with_score(known, store)

    assert scored.check_id == check_id
    assert scored.display_score == DisplayScore.model_validate(expected)
    assert with_score(unknown, store).display_score is None


def test_a_check_stored_before_v2_is_re_scored_from_its_findings(client: TestClient) -> None:
    check_id = finished_check(client)

    def read_everything() -> dict[str, object]:
        return {
            "report": client.get(f"/api/checks/{check_id}/report").json(),
            "listed": client.get("/api/checks", params={"ids": check_id}).json(),
            "recent": client.get("/api/checks/recent").json(),
            "check": client.get(f"/api/checks/{check_id}").json(),
        }

    before = read_everything()
    drop_v2(client, check_id)
    after = read_everything()

    # Same findings, same engine: the old check reads exactly like the new one.
    assert after == before
    # Reading did not write: the stored check is still the old shape.
    store = client.app.state.store  # type: ignore[attr-defined]
    with store._sessions() as session:  # noqa: SLF001
        detail = session.scalars(select(ScoreRow.detail)).one()
    assert "v2" not in detail


def test_meta_matches_the_scoring_constants(client: TestClient) -> None:
    meta = client.get("/api/meta").json()

    assert meta["scale"] == {"min": w.SCALE_FLOOR, "max": w.SCALE_TOP}
    assert meta["score_version"] == "v2"
    assert meta["bands"] == [
        {"key": "Low", "min": 750, "max": 900},
        {"key": "Watch", "min": 600, "max": 749},
        {"key": "Elevated", "min": 450, "max": 599},
        {"key": "High", "min": 300, "max": 449},
    ]
    assert {p["id"]: p["weight"] for p in meta["pillars"]} == w.PILLAR_WEIGHTS
    assert sum(p["weight"] for p in meta["pillars"]) == pytest.approx(1.0)
    codes = [c["code"] for c in meta["reason_codes"]]
    assert codes == sorted({*LABELS, DATA_UNAVAILABLE})
    assert meta == build_meta().model_dump(mode="json")
