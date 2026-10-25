"""Small helpers shared by the source tests."""

import asyncio
from datetime import UTC, date, datetime
from typing import Any

from app.models import Project
from app.sources.base import FoundFinding, SourceContext, SourceEvent
from tests.fakes import FakeWebClient

TODAY = date(2026, 10, 25)
NOW = datetime(2026, 10, 25, 4, 0, tzinfo=UTC)
URL_8334 = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334"

ECO_VILLAGE_1 = Project(
    rera_id="UPRERAPRJ8334",
    name="SUPERTECH ECO VILLAGE-I PHASE I-C",
    promoter="SUPERTECH LIMITED",
    district="Gautam Buddha Nagar",
    details_url=URL_8334,
)


def context(project: Project = ECO_VILLAGE_1, web: FakeWebClient | None = None) -> SourceContext:
    return SourceContext(project=project, web=web or FakeWebClient(), today=TODAY, now=NOW)


def run_source(source: Any, ctx: SourceContext) -> list[SourceEvent]:
    async def collect() -> list[SourceEvent]:
        return [event async for event in source.run(ctx)]

    return asyncio.run(collect())


def titles(events: list[SourceEvent]) -> list[str]:
    return [e.finding.title for e in events if isinstance(e, FoundFinding)]
