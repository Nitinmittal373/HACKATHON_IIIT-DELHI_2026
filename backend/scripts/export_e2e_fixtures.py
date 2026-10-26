"""Write the API answers the browser tests replay (frontend/e2e/fixtures/).

It runs the recorded check of UPRERAPRJ8334 through the real app, with no network, and saves
what the API said: the search result, the new check, the event stream, the finished check and
the report. Run from backend/:  python -m scripts.export_e2e_fixtures

`python -m scripts.export_e2e_fixtures extras` writes only the newer answers, keeping the check
id the other fixtures use: the comparison of that check with the recorded UP-RERA page of
UPRERAPRJ6742, the promoter's other projects from the recorded up-rera.in searches and the
Sentinel alert a changed record raises. `python -m scripts.export_e2e_fixtures states` writes
the state list and the Maharashtra flow from the recorded check_mh.json.
`python -m scripts.export_e2e_fixtures v2` rewrites the report with the v2 sources on, which is
the 300-900 score the report screens show.

backend/tests/test_e2e_fixtures.py checks every file against the API's own models.
"""

import json
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import FIXED_NOW, make_settings, make_web
from tests.fakes import FakeWebClient, load_recording, recorded_searches

OUT = Path(__file__).resolve().parents[2] / "frontend" / "e2e" / "fixtures"
SEARCH_QUERY = "Supertech Eco Village"
# Check ids are random, but the browser tests name this one, so it is kept across exports.
E2E_CHECK_ID = "4ad9752355f9455aa9d242c93950ea04"
RENAMED: dict[str, str] = {}


def save(name: str, content: str) -> None:
    for generated, kept in RENAMED.items():
        content = content.replace(generated, kept)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(content, encoding="utf-8")
    print(f"saved {name}")


def save_json(name: str, payload: object) -> None:
    save(name, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    web = make_web().replay(load_recording("check_8334.json"))
    with tempfile.TemporaryDirectory() as folder:
        settings = make_settings(Path(folder))
        app = create_app(settings, web=web, clock=lambda: FIXED_NOW, cache_dir=None)
        with TestClient(app) as client:
            search = client.get("/api/projects/search", params={"q": SEARCH_QUERY})
            save_json("search.json", search.json())
            created = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"})
            check = created.json()
            RENAMED[check["id"]] = E2E_CHECK_ID
            save_json("check-created.json", check)
            with client.stream("GET", f"/api/checks/{check['id']}/events") as response:
                save("events.sse", "\n".join(response.iter_lines()) + "\n")
            save_json("check-done.json", client.get(f"/api/checks/{check['id']}").json())
            save_json("report.json", client.get(f"/api/checks/{check['id']}/report").json())
            save_json("meta.json", client.get("/api/meta").json())


def export_compare() -> None:
    """compare.json and summary-6742.json, from the real compare and list endpoints."""
    e2e_id = json.loads((OUT / "check-created.json").read_text(encoding="utf-8"))["id"]
    web = make_web().replay(load_recording("check_8334.json"))
    with tempfile.TemporaryDirectory() as folder:
        settings = make_settings(Path(folder))
        app = create_app(settings, web=web, clock=lambda: FIXED_NOW, cache_dir=None)
        with TestClient(app) as client:
            ids = []
            for rera_id in ("UPRERAPRJ8334", "UPRERAPRJ6742"):
                check_id = client.post("/api/checks", json={"rera_id": rera_id}).json()["id"]
                with client.stream("GET", f"/api/checks/{check_id}/events") as response:
                    response.read()
                ids.append(check_id)
            comparison = client.get("/api/checks/compare", params={"ids": ",".join(ids)}).json()
            summary = client.get("/api/checks", params={"ids": ids[1]}).json()[0]
    # The 8334 check here is a replay of the one the other fixtures hold; use that one's id.
    text = json.dumps(comparison, indent=2, ensure_ascii=False).replace(ids[0], e2e_id)
    save("compare.json", text + "\n")
    save_json("summary-6742.json", summary)


def export_track_record() -> None:
    """track-record.json: what GET /api/promoters/projects answers for the recorded searches."""
    searches = ("search_up_supertech_limited.json", "search_up_supertech_limited_promoter.json")
    web = FakeWebClient(searches=recorded_searches(*searches))
    with tempfile.TemporaryDirectory() as folder:
        app = create_app(make_settings(Path(folder)), web=web, clock=lambda: FIXED_NOW)
        with TestClient(app) as client:
            params = {"name": "SUPERTECH LIMITED", "exclude": "UPRERAPRJ8334"}
            record = client.get("/api/promoters/projects", params=params).json()
    save_json("track-record.json", record)


def export_v2_report() -> None:
    """report.json again, with the v2 sources on: the 300-900 score, reason codes and the group.

    The check keeps the id the other fixtures use, so every page still finds its report.
    """
    path = OUT / "report.json"
    e2e_id = json.loads(path.read_text(encoding="utf-8"))["check"]["id"]
    web = make_web().replay(load_recording("check_8334.json"))
    web.replay(load_recording("group_8334.json")).replay(load_recording("sarfaesi_8334.json"))
    with tempfile.TemporaryDirectory() as folder:
        settings = make_settings(Path(folder), v2_sources=True)
        app = create_app(settings, web=web, clock=lambda: FIXED_NOW, cache_dir=None)
        with TestClient(app) as client:
            check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
            with client.stream("GET", f"/api/checks/{check_id}/events") as response:
                response.read()
            report = client.get(f"/api/checks/{check_id}/report").json()
    text = json.dumps(report, indent=2, ensure_ascii=False).replace(check_id, e2e_id)
    save("report.json", text + "\n")


def export_alerts() -> None:
    """alerts.json: the alert Sentinel raises when the insolvency page changes after a watch."""
    from tests.test_sentinel import (  # the same flow the Sentinel tests run
        INSOLVENCY_PAGE,
        alerts,
        build_client,
        insolvency_answer,
        recheck,
        run_check,
        watch,
    )

    e2e_id = json.loads((OUT / "check-created.json").read_text(encoding="utf-8"))["id"]
    web = make_web().replay(load_recording("check_8334.json"))
    with tempfile.TemporaryDirectory() as folder, build_client(Path(folder), web) as client:
        run_check(client)
        watch(client)
        web.agent_runs[INSOLVENCY_PAGE] = insolvency_answer(admitted_on="April 1, 2022")
        recheck(client)
        found = alerts(client)
    text = json.dumps(found, indent=2, ensure_ascii=False)
    for alert in found:
        text = text.replace(str(alert["check_id"]), e2e_id)
    save("alerts.json", text + "\n")


FLAGGED_ID = "f" * 32
MH_CHECK_ID = "a1" * 16
MH_NUMBER = "P99000055716"
GROUPED_QUERY = "Prestige Lakeside Habitat"


def export_states() -> None:
    """states.json (GET /api/states) and the Maharashtra flow: search, check, events, report."""
    with tempfile.TemporaryDirectory() as folder:
        grouped = FakeWebClient().replay(load_recording("states_name_prestige.json"))
        with TestClient(create_app(make_settings(Path(folder)), web=grouped)) as client:
            found = client.get("/api/projects/search", params={"q": GROUPED_QUERY})
            save_json("search-grouped.json", found.json())
    with tempfile.TemporaryDirectory() as folder:
        web = FakeWebClient().replay(load_recording("check_mh.json"))
        settings = make_settings(Path(folder), v2_sources=True)
        app = create_app(settings, web=web, clock=lambda: FIXED_NOW, cache_dir=None)
        with TestClient(app) as client:
            save_json("states.json", client.get("/api/states").json())
            search = client.get("/api/projects/search", params={"q": MH_NUMBER})
            save_json("search-mh.json", search.json())
            created = client.post("/api/checks", json={"rera_id": MH_NUMBER}).json()
            RENAMED[created["id"]] = MH_CHECK_ID
            save_json("check-created-mh.json", created)
            with client.stream("GET", f"/api/checks/{created['id']}/events") as response:
                save("events-mh.sse", "\n".join(response.iter_lines()) + "\n")
            save_json("check-done-mh.json", client.get(f"/api/checks/{created['id']}").json())
            save_json("report-mh.json", client.get(f"/api/checks/{created['id']}/report").json())


def export_flagged_report() -> None:
    """report-flagged.json: the real report with two tree nodes marked, for a rendering test.

    The real recording has no insolvent or struck-off company, so the red outline and its text
    label could not be tested. This copy is only ever served by the browser-test mock, under its
    own id; no visitor can reach it.
    """
    report = json.loads((OUT / "report.json").read_text(encoding="utf-8"))
    report["check"]["id"] = FLAGGED_ID
    family = report["family"]
    family["companies"][0] |= {"status": "Under CIRP", "flag": "cirp"}
    family["promoter_projects"][0]["state"] = "lapsed"
    save_json("report-flagged.json", report)


if __name__ == "__main__":
    if sys.argv[1:] == ["flagged"]:
        export_flagged_report()
    elif sys.argv[1:] == ["v2"]:
        export_v2_report()
    elif sys.argv[1:] == ["states"]:
        export_states()
    elif sys.argv[1:] == ["extras"]:
        export_compare()
        export_track_record()
        export_alerts()
    else:
        main()
