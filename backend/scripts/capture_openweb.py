"""Record the unrestricted Search answers the open-web resolver tests replay.

    python -m scripts.capture_openweb

Only free Search is used. The two searches per project are exactly the ones the resolver asks
first, so a test can replay the resolver without touching the network.
"""

import asyncio
import json
import sys
from pathlib import Path

from app.config import load_settings
from app.states.openweb import SEARCH_TEMPLATES
from app.tinyfish import LiveWebClient, WebError
from scripts.famous_projects import FAMOUS
from scripts.recorder import RecordingWebClient, scrub

# Two seconds a search stays under the limit.
RATE_PAUSE_SECONDS = 2.2
OUTPUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "openweb_famous.json"


async def main() -> None:
    settings = load_settings()
    key = settings.tinyfish_api_key.get_secret_value()
    web = RecordingWebClient(
        LiveWebClient(settings.tinyfish_api_key, fetch_timeout=45, agent_timeout=60)
    )
    try:
        for famous in FAMOUS:
            for template in SEARCH_TEMPLATES:
                await search(web, template.format(q=famous.query))
                await asyncio.sleep(RATE_PAUSE_SECONDS)  # TinyFish allows 30 searches a minute
    finally:
        await web.aclose()
    save(web.recording(), key)


async def search(web: RecordingWebClient, text: str) -> None:
    """One Search; a rate-limit answer is waited out, as the answer says, and tried again."""
    for _ in range(5):
        try:
            await web.search(text, purpose="Record a fixture")
            return
        except WebError as error:
            if error.code != "rate_limited":
                raise
            await asyncio.sleep(error.retry_after or 20)
    raise WebError("Search stayed rate limited", "rate_limited")


def save(recording: dict, key: str) -> None:
    text = scrub(json.dumps(recording, indent=2, ensure_ascii=False))
    if key in text:
        sys.exit("Refusing to write the fixture: it contains the API key")
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"saved {OUTPUT.name} ({len(text):,} chars)")


if __name__ == "__main__":
    asyncio.run(main())
