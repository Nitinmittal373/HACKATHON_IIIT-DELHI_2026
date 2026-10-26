"""Record the Search answers of a builder search and a locality search for the tests.

    python -m scripts.capture_find

Only free Search is used.
"""

import asyncio
import json
import sys
from pathlib import Path

from app.config import load_settings
from app.states.openweb import SearchCache
from app.states.promoter_search import search_promoter
from app.states.resolver import resolve_any
from app.tinyfish import LiveWebClient
from scripts.recorder import RecordingWebClient, scrub

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


async def main() -> None:
    settings = load_settings()
    key = settings.tinyfish_api_key.get_secret_value()

    def client() -> RecordingWebClient:
        live = LiveWebClient(settings.tinyfish_api_key, fetch_timeout=45, agent_timeout=60)
        return RecordingWebClient(live)

    web = client()
    try:
        await search_promoter("Lodha Developers", web, cache=SearchCache())
    finally:
        await web.aclose()
    save("find_builder_lodha.json", web.recording(), key)

    web = client()
    try:
        await resolve_any("Eureka Park", web, locality="Sector 150 Noida")
    finally:
        await web.aclose()
    save("find_locality_eureka.json", web.recording(), key)


def save(name: str, recording: dict, key: str) -> None:
    text = scrub(json.dumps(recording, indent=2, ensure_ascii=False))
    if key in text:
        sys.exit(f"Refusing to write {name}: it contains the API key")
    (FIXTURES / name).write_text(text, encoding="utf-8")
    print(f"saved {name} ({len(text):,} chars)")


if __name__ == "__main__":
    asyncio.run(main())
