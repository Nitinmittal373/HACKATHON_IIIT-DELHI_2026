from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import Project
from tests.conftest import FIXED_NOW, make_settings, make_web, read_events


def start_check(client: TestClient, rera_id: str = "UPRERAPRJ8334") -> str:
    response = client.post("/api/checks", json={"rera_id": rera_id})
    assert response.status_code == 202
    return response.json()["id"]


def test_create_check_returns_202_with_an_id(client: TestClient) -> None:
    response = client.post("/api/checks", json={"rera_id": " upreraprj8334"})

    assert response.status_code == 202
    body = response.json()
    assert len(body["id"]) == 32
    assert body["rera_id"] == "UPRERAPRJ8334"
    assert body["details_url"] == "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334"
    assert response.headers["Location"] == f"/api/checks/{body['id']}"


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"rera_id": "not a number"},
        {"rera_id": "UPRERAPRJ8334", "unexpected": True},
        {"rera_id": "UPRERAPRJ188811/08/2024"},
        {"rera_id": "UPRERAPRJ188811/08/2024", "details_url": "https://evil.example/x"},
    ],
)
def test_bad_input_is_rejected_with_422(client: TestClient, body: dict[str, object]) -> None:
    assert client.post("/api/checks", json=body).status_code == 422


def test_report_for_8334_is_scored_from_the_recorded_page(client: TestClient) -> None:
    check_id = start_check(client)
    read_events(client, check_id)

    response = client.get(f"/api/checks/{check_id}/report")
    assert response.status_code == 200
    report = response.json()
    assert report["check"]["status"] == "completed"
    assert report["project"]["name"] == "SUPERTECH ECO VILLAGE-I PHASE I-C"
    assert report["project"]["promoter"] == "SUPERTECH LIMITED"
    assert report["project"]["district"] == "Gautam Buddha Nagar"
    keys = ("value", "band", "band_label", "confidence", "provisional", "hard_stop")
    assert {k: report["score"][k] for k in keys} == {
        "value": 71,
        "band": "insufficient_evidence",
        "band_label": "Not enough evidence yet",
        "confidence": 0.43,
        "provisional": True,
        "hard_stop": False,
    }
    points = {f["kind"]: f for f in report["findings"]}
    assert set(points) == {
        "registration",
        "past_end_date",
        "promoter_complaints",
        "project_complaints",
    }
    assert [d["points"] for d in report["score"]["drivers"]] == [-14.0, -9.0, -6.0]
    assert all(
        f["source_url"].startswith(("https://www.up-rera.in/", "https://up-rera.in/"))
        for f in report["findings"]
    )
    dates = [f["occurred_on"] for f in report["timeline"]]
    assert dates == sorted(dates)


def test_report_for_6742_counts_the_delay(client: TestClient) -> None:
    check_id = start_check(client, "UPRERAPRJ6742")
    read_events(client, check_id)

    score = client.get(f"/api/checks/{check_id}/report").json()["score"]
    assert score["value"] == 86
    assert score["drivers"][0]["points"] == -14.0


def test_check_shows_every_source_and_why_it_was_not_read(client: TestClient) -> None:
    check_id = start_check(client)
    read_events(client, check_id)

    check = client.get(f"/api/checks/{check_id}").json()
    statuses = {run["source"]: run["status"] for run in check["sources"]}
    assert statuses == {
        "uprera": "completed",
        "registry": "completed",
        "group": "failed",  # nor does it name any company for the group lane to read
        "sarfaesi": "completed",
        "insolvency": "completed",
        "land": "completed",
        "consumer": "failed",  # the fake web client gives the agent nothing to answer with
        "news": "completed",
    }


def test_an_unreadable_uprera_page_fails_the_check_without_a_score(tmp_path: Path) -> None:
    web = make_web()
    web.pages.clear()
    with TestClient(create_app(make_settings(tmp_path), web=web)) as client:
        check_id = start_check(client)
        events = read_events(client, check_id)

        assert events[-1]["data"]["status"] == "failed"
        assert client.get(f"/api/checks/{check_id}").json()["status"] == "failed"
        assert client.get(f"/api/checks/{check_id}/report").status_code == 409


def test_report_is_409_while_the_check_runs(client: TestClient) -> None:
    store = client.app.state.store  # type: ignore[attr-defined]
    check_id = "a" * 32
    store.save_project(Project(rera_id="UPRERAPRJ1", details_url="https://www.up-rera.in/x?id=1"))
    store.create_check(check_id, "UPRERAPRJ1", datetime(2026, 10, 25, tzinfo=UTC))
    response = client.get(f"/api/checks/{check_id}/report")
    assert response.status_code == 409
    assert response.json()["detail"] == "The check is still running"


def test_unknown_and_malformed_check_ids(client: TestClient) -> None:
    assert client.get(f"/api/checks/{'b' * 32}").status_code == 404
    assert client.get(f"/api/checks/{'b' * 32}/report").status_code == 404
    assert client.get("/api/checks/not-an-id").status_code == 422


def test_rate_limit_returns_429_after_the_limit(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, rate_limit_per_minute=2)
    app = create_app(settings, web=make_web(), clock=lambda: FIXED_NOW)
    with TestClient(app) as client:
        body = {"rera_id": "UPRERAPRJ8334", "fresh": True}
        assert client.post("/api/checks", json=body).status_code == 202
        assert client.post("/api/checks", json=body).status_code == 202
        blocked = client.post("/api/checks", json=body)

    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1


def test_a_check_reads_the_page_search_confirmed(client: TestClient) -> None:
    # Six-digit numbers have no stable details page, so the link search confirmed is kept.
    url = "https://up-rera.in/Projectsummary?UI0aPA1ISD=nffnnE2PJOk="
    response = client.post("/api/checks", json={"rera_id": "UPRERAPRJ396176", "details_url": url})
    assert response.status_code == 202
    assert response.json()["details_url"] == url


def test_a_number_sent_alone_gets_its_stable_page(client: TestClient) -> None:
    response = client.post("/api/checks", json={"rera_id": "UPRERAPRJ6742"})
    assert response.json()["details_url"].endswith("Frm_View_Project_Details.aspx?id=6742")


# The summary every list carries; the card facts (drivers, reasons) come on top.
SUMMARY_FIELDS = (
    "id",
    "rera_id",
    "details_url",
    "project",
    "promoter",
    "status",
    "score",
    "band",
    "confidence",
    "display_score",
    "created_at",
    "completed_at",
)


def test_my_reports_lists_known_checks_in_the_order_asked(client: TestClient) -> None:
    first, second = start_check(client), start_check(client, "UPRERAPRJ6742")
    read_events(client, first)
    read_events(client, second)
    unknown = "c" * 32

    response = client.get("/api/checks", params={"ids": f"{second},{unknown},{first}"})
    assert response.status_code == 200
    listed = response.json()
    assert [c["id"] for c in listed] == [second, first]
    assert {k: listed[1][k] for k in SUMMARY_FIELDS} == {
        "id": first,
        "rera_id": "UPRERAPRJ8334",
        "details_url": "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334",
        "project": "SUPERTECH ECO VILLAGE-I PHASE I-C",
        "promoter": "SUPERTECH LIMITED",
        "status": "completed",
        "score": 71,
        "band": "insufficient_evidence",
        "confidence": 0.43,
        "display_score": {
            # The UP-RERA complaint counts read two more pillars, so four of six: it is banded.
            "value": 576,
            "provisional_value": None,
            "band": "Elevated",
            "hard_stop": False,
            "confidence": 0.67,
            "provisional": False,
            "records_read": 4,
            "records_total": 6,
        },
        "created_at": listed[1]["created_at"],
        "completed_at": listed[1]["completed_at"],
    }


@pytest.mark.parametrize("ids", ["not-an-id", ",".join(["a" * 32] * 51)])
def test_my_reports_rejects_bad_ids(client: TestClient, ids: str) -> None:
    unique = ids if "," not in ids else ",".join(f"{n:032x}" for n in range(51))
    assert client.get("/api/checks", params={"ids": unique}).status_code == 422


def test_there_is_no_public_feed_of_other_visitors_checks(client: TestClient) -> None:
    read_events(client, start_check(client, "UPRERAPRJ8334"))
    # "recent" is read as a malformed check id, never as a list of everyone's checks.
    assert client.get("/api/checks/recent").status_code == 422


def test_listing_by_id_carries_the_card_facts_and_no_personal_data(client: TestClient) -> None:
    ids = [start_check(client, rera_id) for rera_id in ("UPRERAPRJ8334", "UPRERAPRJ6742")]
    for check_id in ids:
        read_events(client, check_id)

    listed = client.get("/api/checks", params={"ids": ",".join(ids)}).json()
    assert [r["id"] for r in listed] == ids
    eco = listed[0]
    assert eco["drivers"][0]["points"] == -14.0
    assert len(eco["drivers"]) <= 3
    assert eco["sources_read"] >= 1
    assert eco["registered_on"] == "2017-08-09"
    assert not {"email", "ip", "client", "user"} & set(eco)


def test_checks_cut_off_by_a_restart_are_failed_on_startup(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    with TestClient(create_app(settings, web=make_web(), clock=lambda: FIXED_NOW)) as client:
        store = client.app.state.store  # type: ignore[attr-defined]
        url = "https://www.up-rera.in/x?id=1"
        store.save_project(Project(rera_id="UPRERAPRJ1", details_url=url))
        store.create_check("a" * 32, "UPRERAPRJ1", FIXED_NOW)

    with TestClient(create_app(settings, web=make_web(), clock=lambda: FIXED_NOW)) as client:
        check = client.get(f"/api/checks/{'a' * 32}").json()
        events = read_events(client, "a" * 32)
    assert check["status"] == "failed"
    assert events[-1]["data"]["status"] == "failed"
