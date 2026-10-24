"""Record real TinyFish responses as test fixtures.

Tests never touch the network, so they replay what this script saves. It
goes through the app's own client and selectors, so fixtures match what a
live check reads. Run it by hand from backend/ when a parser needs a fresh
page:

    python -m scripts.capture_fixtures            # searches and pages
    python -m scripts.capture_fixtures pages      # pages only

It reads TINYFISH_API_KEY like the app does and refuses to write a file
that contains the key.
"""

import asyncio
import json
import sys
from pathlib import Path

from app.config import load_settings
from app.sources.uprera import selectors_for
from app.tinyfish import LiveWebClient

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
# A new-format project, reachable only through the Projectsummary link search returned.
NEW_FORMAT_ID = "UPRERAPRJ188811/08/2024"

PAGES = {
    "uprera_8334.html": "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334",
    "uprera_6742.html": "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=6742",
}
SEARCHES = {
    "search_gaur_city.json": "Gaur City UP RERA project",
    "search_supertech_eco_village.json": "Supertech Eco Village UP RERA project",
}
PURPOSE = "Record a UP-RERA response as a parser test fixture"


def save(name: str, content: str, key: str) -> None:
    # A fixture is committed, so it must never carry the key, even inside a URL.
    if key in content:
        sys.exit(f"Refusing to write {name}: it contains the API key")
    (FIXTURES / name).write_text(content, encoding="utf-8")
    print(f"saved {name} ({len(content):,} chars)")


def summary_url(search_fixture: str, rera_id: str) -> str:
    payload = json.loads((FIXTURES / search_fixture).read_text(encoding="utf-8"))
    for hit in payload["results"]:
        if rera_id in f"{hit['title']} {hit['snippet']}".upper() and "Projectsummary" in hit["url"]:
            return hit["url"]
    sys.exit(f"No Projectsummary link for {rera_id} in {search_fixture}")


async def main(what: str) -> None:
    settings = load_settings()
    key = settings.tinyfish_api_key.get_secret_value()
    web = LiveWebClient(
        settings.tinyfish_api_key,
        fetch_timeout=settings.fetch_timeout_seconds,
        agent_timeout=settings.agent_timeout_seconds,
    )
    FIXTURES.mkdir(parents=True, exist_ok=True)
    try:
        for name, query in SEARCHES.items() if what in ("all", "searches") else ():
            hits = await web.search(query, purpose=PURPOSE)
            payload = {"query": query, "results": [hit.model_dump() for hit in hits]}
            save(name, json.dumps(payload, indent=2, ensure_ascii=False), key)

        new_format = summary_url("search_gaur_city.json", NEW_FORMAT_ID)
        pages = PAGES | {"uprera_summary_188811.html": new_format}
        for name, url in pages.items() if what in ("all", "pages") else ():
            page = await web.fetch_html(url, selectors=selectors_for(url), purpose=PURPOSE)
            save(name, page.html, key)
    finally:
        await web.aclose()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
