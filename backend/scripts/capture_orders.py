"""Record the Search answers of the public-orders path for the tests.

    python -m scripts.capture_orders

Only free Search and Fetch are used.
"""

import asyncio
import json
import sys
from pathlib import Path

from app.config import load_settings
from app.states.openweb import SearchCache
from app.states.orders import find_in_orders
from app.tinyfish import LiveWebClient
from scripts.recorder import RecordingWebClient, scrub

OUTPUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "find_orders_mywoods.json"


async def main() -> None:
    settings = load_settings()
    key = settings.tinyfish_api_key.get_secret_value()
    live = LiveWebClient(settings.tinyfish_api_key, fetch_timeout=45, agent_timeout=60)
    web = RecordingWebClient(live)
    try:
        found = await find_in_orders("Mahagun Mywoods", web, SearchCache())
    finally:
        await web.aclose()
    print(found)
    save(web.recording(), key)


def save(recording: dict, key: str) -> None:
    text = scrub(json.dumps(recording, indent=2, ensure_ascii=False))
    if key in text:
        sys.exit("Refusing to write the fixture: it contains the API key")
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"saved {OUTPUT.name} ({len(text):,} chars)")


if __name__ == "__main__":
    asyncio.run(main())
