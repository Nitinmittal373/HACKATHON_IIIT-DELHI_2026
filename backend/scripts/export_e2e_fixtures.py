"""Write the API answers the browser tests replay (frontend/e2e/fixtures/).

It runs the recorded check of UPRERAPRJ8334 through the real app, with no network, and saves
what the API said: the search result, the new check, the event stream, the finished check and
the report. Run from backend/:  python -m scripts.export_e2e_fixtures
"""

import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import FIXED_NOW, make_settings, make_web
from tests.fakes import load_recording

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


if __name__ == "__main__":
    main()
