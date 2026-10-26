"""Record a v2 source of UPRERAPRJ8334 as a test fixture (group_8334.json, sarfaesi_8334.json).

They use only free Search and Fetch, no browser agent. Run from backend/:

    python -m scripts.capture_group            # group companies
    python -m scripts.capture_group sarfaesi   # lender auction notices
"""

import asyncio
import json
import sys
from datetime import UTC, datetime

from app.config import load_settings
from app.models import Project
from app.sources.base import FoundFinding, Progress, SourceContext
from app.sources.group import GroupSource
from app.sources.sarfaesi import SarfaesiSource
from app.tinyfish import LiveWebClient
from scripts.capture_fixtures import FIXTURES, save
from scripts.recorder import RecordingWebClient, scrub

PROJECT = Project(
    rera_id="UPRERAPRJ8334",
    name="Supertech Eco Village-I Phase I-C",
    promoter="SUPERTECH LIMITED",
    district="Gautam Buddha Nagar",
    details_url="https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334",
)


SOURCES = {"group": GroupSource, "sarfaesi": SarfaesiSource}


async def main(name: str) -> None:
    settings = load_settings()
    live = LiveWebClient(
        settings.tinyfish_api_key,
        fetch_timeout=settings.fetch_timeout_seconds,
        agent_timeout=settings.agent_timeout_seconds,
    )
    web = RecordingWebClient(live)
    now = datetime.now(UTC)
    ctx = SourceContext(project=PROJECT, web=web, today=now.date(), now=now)
    findings = []
    try:
        async for event in SOURCES[name]().run(ctx):
            if isinstance(event, Progress):
                print("·", event.text)
            elif isinstance(event, FoundFinding):
                findings.append(event.finding)
                print("finding:", event.finding.kind, event.finding.title)
    finally:
        await live.aclose()
    recording = {"captured_at": now.isoformat(), "project": PROJECT.model_dump(mode="json")}
    recording |= web.recording()
    key = settings.tinyfish_api_key.get_secret_value()
    save(f"{name}_8334.json", scrub(json.dumps(recording, ensure_ascii=False, indent=1)), key)
    print(f"saved {FIXTURES / (name + '_8334.json')} with {len(findings)} findings")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "group"))
