"""Record real TinyFish responses as test fixtures.

Tests never touch the network, so they replay what this script saves. It
goes through the app's own client and selectors, so fixtures match what a
live check reads. Run it by hand from backend/ when a parser needs a fresh
page:

    python -m scripts.capture_fixtures                          # pages and searches
    python -m scripts.capture_fixtures uprera_summary_8334.html  # named files only
    python -m scripts.capture_fixtures check_8334.json          # one full live check

The full check runs every source of UPRERAPRJ8334 for real, so it uses paid
agent runs. It is never part of the default run: ask for it by name.

Pages found through search are captured after their search, which they
read from the saved fixture. The script reads TINYFISH_API_KEY like the app
does and refuses to write a file that contains the key.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, load_settings
from app.main import create_app
from app.sources.uprera import selectors_for
from app.tinyfish import LiveWebClient, SearchHit
from app.uprera_links import UPRERA_DOMAIN, rera_ids_in, summary_url
from scripts.recorder import RecordingWebClient, scrub

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
PURPOSE = "Record a UP-RERA response as a parser test fixture"
CHECK_FIXTURE = "check_8334.json"
# One full live check per fixture; the number is the one to check .
LIVE_CHECKS = {
    CHECK_FIXTURE: "UPRERAPRJ8334",
}

SEARCHES = {
    "search_gaur_city.json": "Gaur City UP RERA project",
    "search_supertech_eco_village.json": "Supertech Eco Village UP RERA project",
    "search_uprera_8334.json": "UPRERAPRJ8334 UP RERA project",
    "search_uprera_2634.json": "UPRERAPRJ2634 UP RERA project",
    # A name whose up-rera.in pages carry no numbers, and a project outside UP.
    "search_supertech_hues.json": "Supertech Hues UP RERA project",
    "search_lodha_palava.json": "Lodha Palava Mumbai UP RERA project",
}
# The same kind of search limited to up-rera.in, as the resolver sends it.
DOMAIN_SEARCHES = {
    "search_up_gaur_city.json": "Gaur City UP RERA project",
    "search_up_ats_pristine.json": "ATS Pristine UP RERA project",
    "search_up_396176.json": "UPRERAPRJ396176 UP RERA project",
    "search_up_188811.json": "UPRERAPRJ188811/08/2024 UP RERA project",
    "search_up_supertech_hues.json": "Supertech Hues UP RERA project",
    "search_up_lodha_palava.json": "Lodha Palava Mumbai UP RERA project",
    # The two searches behind a promoter's other projects (app/track_record.py).
    "search_up_supertech_limited.json": "SUPERTECH LIMITED UP RERA project",
    "search_up_supertech_limited_promoter.json": "SUPERTECH LIMITED promoter UP RERA registration",
}
PAGES = {
    "uprera_8334.html": "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334",
    "uprera_6742.html": "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=6742",
    "uprera_2875.html": "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=2875",
    # A number other sites print for "Supertech Hues"; it is a different project.
    "uprera_6819.html": "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=6819",
}
# Projectsummary pages have no stable address: (search fixture, RERA number) to find them.
SUMMARY_PAGES = {
    "uprera_summary_188811.html": ("search_up_188811.json", "UPRERAPRJ188811/08/2024"),
    "uprera_summary_8334.html": ("search_uprera_8334.json", "UPRERAPRJ8334"),
    # Completed (certificate uploaded) and with one ordinary plus one COVID-19 extension.
    "uprera_summary_2634.html": ("search_uprera_2634.json", "UPRERAPRJ2634"),
    # A six-digit number without a date suffix: it has no stable details page.
    "uprera_summary_396176.html": ("search_up_396176.json", "UPRERAPRJ396176"),
}


def save(name: str, content: str, key: str) -> None:
    # A fixture is committed, so it must never carry the key, even inside a URL.
    if key in content:
        sys.exit(f"Refusing to write {name}: it contains the API key")
    (FIXTURES / name).write_text(content, encoding="utf-8")
    print(f"saved {name} ({len(content):,} chars)")


def summary_link(search_fixture: str, rera_id: str) -> str:
    payload = json.loads((FIXTURES / search_fixture).read_text(encoding="utf-8"))
    for raw in payload["results"]:
        hit = SearchHit.model_validate(raw)
        if (url := summary_url(hit.url)) and rera_id in rera_ids_in(hit):
            return url
    sys.exit(f"No Projectsummary link for {rera_id} in {search_fixture}")


def capture_check(settings: Settings, fixture: str) -> None:
    """Run every source for one project against the real sites and record what they answered."""
    rera_id = LIVE_CHECKS[fixture]
    key = settings.tinyfish_api_key.get_secret_value()
    recorder = RecordingWebClient(
        LiveWebClient(
            settings.tinyfish_api_key,
            fetch_timeout=settings.fetch_timeout_seconds,
            agent_timeout=settings.agent_timeout_seconds,
            send_max_steps=settings.agent_send_max_steps,
        )
    )
    with tempfile.TemporaryDirectory() as folder:
        database = f"sqlite:///{Path(folder, 'capture.db').as_posix()}"
        app = create_app(settings.model_copy(update={"database_url": database}), web=recorder)
        with TestClient(app) as client:
            check_id = client.post("/api/checks", json={"rera_id": rera_id}).json()["id"]
            events = follow_events(client, check_id)
            report = client.get(f"/api/checks/{check_id}/report").json()
    payload = {
        "rera_id": rera_id,
        "captured_at": events[0]["ts"],
        **recorder.recording(),
        "outcome": {
            "score": report["score"]["value"],
            "band": report["score"]["band"],
            "confidence": report["score"]["confidence"],
            "display_score": report["display_score"],
            "reasons": [r["label"] for r in report["score_v2"]["reason_codes"]][:5],
            "sources": {run["source"]: run["status"] for run in report["check"]["sources"]},
        },
    }
    save(fixture, scrub(json.dumps(payload, indent=2, ensure_ascii=False)), key)


def follow_events(client: TestClient, check_id: str) -> list[dict[str, str]]:
    events = []
    with client.stream("GET", f"/api/checks/{check_id}/events") as response:
        for line in response.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line.removeprefix("data: ")))
    return events


async def main(wanted: set[str]) -> None:
    def chosen(name: str) -> bool:
        return not wanted or name in wanted

    settings = load_settings()
    key = settings.tinyfish_api_key.get_secret_value()
    web = LiveWebClient(
        settings.tinyfish_api_key,
        fetch_timeout=settings.fetch_timeout_seconds,
        agent_timeout=settings.agent_timeout_seconds,
    )
    FIXTURES.mkdir(parents=True, exist_ok=True)
    try:
        searches = [(n, q, None) for n, q in SEARCHES.items()]
        searches += [(n, q, UPRERA_DOMAIN) for n, q in DOMAIN_SEARCHES.items()]
        for name, query, domains in searches:
            if chosen(name):
                hits = await web.search(query, purpose=PURPOSE, include_domains=domains)
                payload = {
                    "query": query,
                    "include_domains": domains,
                    "results": [hit.model_dump() for hit in hits],
                }
                save(name, json.dumps(payload, indent=2, ensure_ascii=False), key)

        pages = PAGES | {
            name: summary_link(*found) for name, found in SUMMARY_PAGES.items() if chosen(name)
        }
        for name, url in pages.items():
            if chosen(name):
                page = await web.fetch_html(url, selectors=selectors_for(url), purpose=PURPOSE)
                save(name, page.html, key)
    finally:
        await web.aclose()


if __name__ == "__main__":
    names = set(sys.argv[1:])
    for fixture in LIVE_CHECKS:
        if fixture in names:
            capture_check(load_settings(), fixture)
            names.discard(fixture)
    if not names and len(sys.argv) > 1:
        sys.exit(0)
    asyncio.run(main(names))
