"""Neev Sentinel: watches, change detection, alerts, the webhook and the cost guards."""

from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import Check, Finding, SourceRun
from app.sentinel.diff import diff_findings
from app.tinyfish import AgentDone
from tests.conftest import FIXED_NOW, make_settings, make_web, read_events
from tests.fakes import FakeWebClient, load_recording

RECORDING = load_recording("check_8334.json")
INSOLVENCY_PAGE = next(a["url"] for a in RECORDING["agents"] if "fortuneindia" in a["url"])
EMAIL = "buyer@example.com"
SECRET = "s3cret-value"  # noqa: S105


def finding(kind: str, source: str = "uprera", **facts: object) -> Finding:
    values: dict[str, object] = {
        "id": f"{source}-{kind}",
        "source": source,
        "kind": kind,
        "title": f"{kind} title",
        "verdict": "review",
        "reliability": "primary",
        "source_url": f"https://example.org/{kind}",
        "read_on": date(2026, 10, 25),
        **facts,
    }
    return Finding.model_validate(values)


def check_reading(*sources: str, blocked: tuple[str, ...] = ()) -> Check:
    runs = [
        SourceRun(source=s, status="completed", checks_read=["registration"])  # type: ignore[arg-type]
        for s in sources
    ] + [SourceRun(source=s, status="blocked") for s in blocked]  # type: ignore[arg-type]
    return Check(
        id="a" * 32,
        rera_id="UPRERAPRJ8334",
        details_url="https://www.up-rera.in/x",
        status="completed",
        started_at=FIXED_NOW,
        sources=runs,
    )


def test_identical_findings_are_no_change() -> None:
    findings = [finding("project_complaints", count=15)]
    check = check_reading("uprera")
    assert diff_findings(findings, list(findings), check, check).is_empty


def test_a_title_that_only_counts_months_differently_is_no_change() -> None:
    old = [finding("past_end_date", months=104, title="passed 104 months ago")]
    new = [finding("past_end_date", months=105, title="passed 105 months ago")]
    check = check_reading("uprera")
    assert diff_findings(old, new, check, check).is_empty


def test_a_new_finding_is_added_and_new_facts_are_changed() -> None:
    old = [finding("project_complaints", count=15)]
    new = [finding("project_complaints", count=22), finding("land_dues", "land")]
    diff = diff_findings(old, new, check_reading("uprera", "land"), check_reading("uprera", "land"))

    assert [c.title for c in diff.changed] == ["project_complaints title"]
    assert [c.title for c in diff.added] == ["land_dues title"]
    assert diff.removed == []


def test_a_source_that_went_unread_is_not_a_removal_and_unread_twice_is_nothing() -> None:
    old = [finding("land_dues", "land")]
    went_dark = check_reading("uprera", blocked=("land",))
    assert diff_findings(old, [], check_reading("uprera", "land"), went_dark).is_empty
    assert diff_findings([], [], went_dark, went_dark).is_empty


def test_a_source_read_for_the_first_time_is_not_an_addition() -> None:
    new = [finding("land_dues", "land")]
    before = check_reading("uprera", blocked=("land",))
    diff = diff_findings([], new, before, check_reading("uprera", "land"))
    assert diff.is_empty


@pytest.fixture
def sentinel_client(tmp_path: Path) -> TestClient:
    return build_client(tmp_path)


def build_client(
    tmp_path: Path, web: FakeWebClient | None = None, **settings: object
) -> TestClient:
    values = {"webhook_secret": SECRET, "sentinel_interval_hours": 0, **settings}
    web = web or make_web().replay(RECORDING)
    settings_ = make_settings(tmp_path, **values)
    app = create_app(settings_, web=web, clock=lambda: FIXED_NOW, cache_dir=None)
    return TestClient(app)


def run_check(client: TestClient, **body: object) -> str:
    response = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334", **body})
    check_id = response.json()["id"]
    read_events(client, check_id)
    return check_id


def watch(client: TestClient, email: str = EMAIL, rera_id: str = "UPRERAPRJ8334"):
    return client.post("/api/sentinel", json={"rera_id": rera_id, "email": email, "language": "en"})


def recheck(client: TestClient) -> None:
    client.portal.call(client.app.state.sentinel.run_once)  # type: ignore[union-attr, attr-defined]


def alerts(client: TestClient) -> list[dict[str, object]]:
    return client.get("/api/sentinel/alerts", params={"email": EMAIL}).json()


def insolvency_answer(**changes: object) -> list[AgentDone]:
    answer = next(a for a in RECORDING["agents"] if a["url"] == INSOLVENCY_PAGE)["events"][-1]
    return [AgentDone("COMPLETED", {**answer["result"], **changes})]


def test_no_change_means_no_alert(sentinel_client: TestClient) -> None:
    with sentinel_client as client:
        run_check(client)
        assert watch(client).status_code == 201
        recheck(client)
        recheck(client)

        assert alerts(client) == []


def test_a_changed_record_creates_one_alert_with_the_diff(tmp_path: Path) -> None:
    web = make_web().replay(RECORDING)
    with build_client(tmp_path, web) as client:
        run_check(client)
        watch(client)
        web.agent_runs[INSOLVENCY_PAGE] = insolvency_answer(admitted_on="April 1, 2022")
        recheck(client)

        [alert] = alerts(client)
        assert alert["old_score"] == alert["new_score"] == 68
        assert [c["title"] for c in alert["changed"]] == [
            "Insolvency application against SUPERTECH LIMITED was admitted on 01 Apr 2022"
        ]
        assert alert["added"] == [] and alert["removed"] == []
        recheck(client)
        assert len(alerts(client)) == 1  # nothing changed since, so nothing new


def test_a_new_finding_is_listed_as_added_and_a_new_scope_as_changed(tmp_path: Path) -> None:
    web = make_web().replay(RECORDING)
    quiet = insolvency_answer(covers_whole_company=False, scope_quote=None)
    web.agent_runs[INSOLVENCY_PAGE] = quiet
    with build_client(tmp_path, web) as client:
        run_check(client)
        watch(client)
        web.agent_runs[INSOLVENCY_PAGE] = insolvency_answer()
        recheck(client)

        [alert] = alerts(client)
        assert [c["title"][:40] for c in alert["added"]] == [  # type: ignore[index]
            "A news report says the insolvency covers"
        ]
        assert alert["changed"] == [] and alert["removed"] == []

        web.agent_runs[INSOLVENCY_PAGE] = insolvency_answer(
            projects_named=["Supertech Eco Village-I Phase I-C"]
        )
        recheck(client)
        both = alerts(client)
        assert len(both) == 2
        assert any(len(a["changed"]) == 1 for a in both)  # type: ignore[arg-type]


def test_the_first_finished_check_is_a_baseline_not_a_change(sentinel_client: TestClient) -> None:
    with sentinel_client as client:
        assert watch(client).json()["baseline_check_id"] is None
        recheck(client)
        recheck(client)

        assert alerts(client) == []


def test_the_webhook_needs_the_right_secret(sentinel_client: TestClient) -> None:
    with sentinel_client as client:
        assert client.post("/api/sentinel/run").status_code == 401
        wrong = client.post("/api/sentinel/run", headers={"X-Webhook-Secret": "nope"})
        assert wrong.status_code == 401
        right = client.post("/api/sentinel/run", headers={"X-Webhook-Secret": SECRET})
        assert right.status_code == 202


def test_the_webhook_is_closed_when_no_secret_is_configured(tmp_path: Path) -> None:
    with build_client(tmp_path, webhook_secret=None) as client:
        response = client.post("/api/sentinel/run", headers={"X-Webhook-Secret": ""})
        assert response.status_code == 401


def test_one_email_can_watch_three_projects_and_a_bad_email_is_refused(
    sentinel_client: TestClient,
) -> None:
    with sentinel_client as client:
        for number in (1001, 1002, 1003):
            assert watch(client, rera_id=f"UPRERAPRJ{number}").status_code == 201
        assert watch(client, rera_id="UPRERAPRJ1003").status_code == 200  # same watch again
        fourth = watch(client, rera_id="UPRERAPRJ1004")
        assert fourth.status_code == 409
        assert fourth.json()["detail"]["code"] == "watch_limit"
        assert watch(client, email="not-an-email").status_code == 422


def test_the_daily_cap_refuses_new_checks_with_429(tmp_path: Path) -> None:
    with build_client(tmp_path, max_checks_per_day=1) as client:
        run_check(client)
        capped = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334", "fresh": True})

        assert capped.status_code == 429
        assert capped.json()["detail"]["code"] == "daily_cap"
        assert int(capped.headers["Retry-After"]) >= 1


def test_the_daily_cap_also_stops_sentinel(tmp_path: Path) -> None:
    with build_client(tmp_path, max_checks_per_day=1) as client:
        run_check(client)
        watch(client)
        before = len(client.app.state.web.calls)  # type: ignore[attr-defined]
        recheck(client)

        assert len(client.app.state.web.calls) == before  # type: ignore[attr-defined]


def test_a_check_from_the_last_day_is_reused_unless_a_fresh_one_is_asked_for(
    sentinel_client: TestClient,
) -> None:
    with sentinel_client as client:
        first = run_check(client)
        again = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"})

        assert again.status_code == 200
        assert again.json()["id"] == first
        assert again.json()["reused"] is True
        fresh = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334", "fresh": True})
        assert fresh.status_code == 202
        assert fresh.json()["id"] != first


def test_a_check_older_than_a_day_is_not_reused(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    app = create_app(
        make_settings(tmp_path, webhook_secret=SECRET),
        web=make_web().replay(RECORDING),
        clock=lambda: now[0],
        cache_dir=None,
    )
    with TestClient(app) as client:
        first = run_check(client)
        now[0] = FIXED_NOW + timedelta(hours=25)
        later = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"})

        assert later.status_code == 202
        assert later.json()["id"] != first
