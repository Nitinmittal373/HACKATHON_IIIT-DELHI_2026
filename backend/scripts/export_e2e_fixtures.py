"""Write the API answers the browser tests replay (frontend/e2e/fixtures/).

It runs the recorded check of UPRERAPRJ8334 through the real app, with no network, and saves
what the API said: the search result, the new check, the event stream, the finished check and
the report. Run from backend/:  python -m scripts.export_e2e_fixtures

`python -m scripts.export_e2e_fixtures extras` writes only the newer answers, keeping the check
id the other fixtures use: the comparison of that check with the recorded UP-RERA page of
UPRERAPRJ6742, and the promoter's other projects from the recorded up-rera.in searches.
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


def save(name: str, content: str) -> None:
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
            save_json("check-created.json", check)
            with client.stream("GET", f"/api/checks/{check['id']}/events") as response:
                save("events.sse", "\n".join(response.iter_lines()) + "\n")
            save_json("check-done.json", client.get(f"/api/checks/{check['id']}").json())
            save_json("report.json", client.get(f"/api/checks/{check['id']}/report").json())


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


if __name__ == "__main__":
    if sys.argv[1:] == ["extras"]:
        export_compare()
        export_track_record()
    else:
        main()
