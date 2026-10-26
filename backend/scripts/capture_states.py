"""Record the free Search and Fetch answers the state adapter tests replay.

Run by hand from backend/ when a portal's pages change:

    python -m scripts.capture_states

Only free Search and Fetch are used. Each file is a recording in the format of
tests/fakes.py (FakeWebClient.replay), scrubbed of phone numbers and email addresses.
"""

import asyncio
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.config import load_settings
from app.models import Project
from app.states.registry import adapter_for, detect_state
from app.states.resolver import resolve_any
from app.tinyfish import LiveWebClient
from scripts.recorder import RecordingWebClient, scrub

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
# fixture name -> a number to read (and resolve) on its portal
READS = {
    "states_mh.json": "P99000055716",
    "states_ka.json": "PRM/KA/RERA/1251/446/PR/170915/000176",
    "states_hr.json": "RC/REP/HARERA/GGM/1059/791/2026/31",
    "states_wb.json": "WBRERA/P/KOL/2024/002005",
    "states_ga.json": "PRGO08242238",
    "states_br.json": "BRERAP00923-1/607/R-783/2019",
    "states_jh.json": "JHARERA/PROJECT/46/2018",
}
# Landline numbers of promoters that list pages print; the recorder's scrub only knows mobiles.
LANDLINE = re.compile(r"(?<!\d)0\d{2,4}-?\d{6,8}(?!\d)")
NAME_SEARCH = ("states_name_prestige.json", "Prestige Lakeside Habitat")


async def main() -> None:
    settings = load_settings()
    key = settings.tinyfish_api_key.get_secret_value()
    for name, rera_id in READS.items():
        web = RecordingWebClient(
            LiveWebClient(settings.tinyfish_api_key, fetch_timeout=45, agent_timeout=60)
        )
        try:
            adapter, _ = detect_state(rera_id) or sys.exit(f"{rera_id} fits no state")
            url = adapter.details_url(Project(rera_id=rera_id, state=adapter.code, details_url=""))
            project = Project(rera_id=rera_id, state=adapter.code, details_url=url)
            found = await adapter_for(adapter.code).resolve(rera_id, web)
            await adapter_for(adapter.code).read(found[0] if found else project, web, now())
        finally:
            await web.aclose()
        save(name, web.recording(), key)

    name, query = NAME_SEARCH
    web = RecordingWebClient(
        LiveWebClient(settings.tinyfish_api_key, fetch_timeout=45, agent_timeout=60)
    )
    try:
        await resolve_any(query, web)
    finally:
        await web.aclose()
    save(name, web.recording(), key)


def now() -> datetime:
    return datetime.now(UTC)


def save(name: str, recording: dict, key: str) -> None:
    text = LANDLINE.sub("[phone]", scrub(json.dumps(recording, indent=2, ensure_ascii=False)))
    if key in text:
        sys.exit(f"Refusing to write {name}: it contains the API key")
    (FIXTURES / name).write_text(text, encoding="utf-8")
    print(f"saved {name} ({len(text):,} chars)")


if __name__ == "__main__":
    asyncio.run(main())
