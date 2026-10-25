import asyncio
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.db import make_engine, make_session_factory
from app.events import EventHub
from app.models import CheckKey, Finding, Project
from app.orchestrator import Orchestrator
from app.sources.agent import CAPTCHA_FIELD, AgentSource, AgentTask
from app.sources.base import Source, SourceContext
from app.sources.uprera import UpreraSource
from app.store import Store
from app.tinyfish import AgentDone, AgentLiveUrl
from tests.conftest import FIXED_NOW, URL_8334, make_web, read_events

SOURCES = {"uprera", "registry", "insolvency", "land", "consumer", "news"}


def test_stream_covers_every_source_and_ends_with_check_completed(client: TestClient) -> None:
    check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
    events = read_events(client, check_id)

    started = [e["source"] for e in events if e["type"] == "source.started"]
    assert set(started) == SOURCES and len(started) == 6
    assert started[0] == "uprera"
    assert sum(e["type"] == "finding.added" for e in events) == 4
    completed = {
        e["source"]: e["data"]["status"] for e in events if e["type"] == "source.completed"
    }
    assert completed["uprera"] == "completed"
    assert all(e["check_id"] == check_id and e["ts"] for e in events)

    last = events[-1]
    assert last["type"] == "check.completed"
    assert last["data"]["status"] == "completed"
    assert last["data"]["score"]["value"] == 71
    assert last["data"]["score"]["provisional"] is True


def test_a_late_listener_still_gets_the_whole_run(client: TestClient) -> None:
    check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
    first = read_events(client, check_id)
    again = read_events(client, check_id)
    assert again == first


class EJagritiLikeSource(AgentSource):
    """An agent source whose site answers with a CAPTCHA, as e-Jagriti does."""

    name = "consumer"
    checks: tuple[CheckKey, ...] = ("consumer_cases",)

    async def task(self, ctx: SourceContext) -> AgentTask | None:
        schema = {"type": "object", "properties": {"cases": {"type": "integer", "nullable": True}}}
        return AgentTask(url="https://e-jagriti.gov.in/", goal="Count cases.", output_schema=schema)

    def to_findings(
        self, result: dict[str, Any], ctx: SourceContext, task: AgentTask
    ) -> list[Finding]:
        return []


def test_a_captcha_is_streamed_as_source_blocked(tmp_path: Path) -> None:
    web = make_web()
    web.agent_runs["https://e-jagriti.gov.in/"] = [
        AgentLiveUrl("wss://live.example/consumer"),
        AgentDone("COMPLETED", {"cases": None, CAPTCHA_FIELD: True}),
    ]
    store = Store(make_session_factory(make_engine(f"sqlite:///{(tmp_path / 'e.db').as_posix()}")))
    hub = EventHub()

    def sources() -> list[Source]:
        return [UpreraSource(), EJagritiLikeSource()]

    async def run() -> tuple[str, list[str]]:
        orchestrator = Orchestrator(
            store,
            hub,
            web,
            concurrency=2,
            source_timeout=30,
            clock=lambda: FIXED_NOW,
            sources=sources,
        )
        check = orchestrator.start(Project(rera_id="UPRERAPRJ8334", details_url=URL_8334))
        log = hub.get(check.id)
        assert log is not None
        return check.id, [event.type async for event in log.follow(heartbeat=5) if event]

    check_id, types = asyncio.run(run())

    assert "source.live_url" in types
    assert "source.blocked" in types
    assert types[-1] == "check.completed"
    check = store.get_check(check_id)
    assert check is not None
    consumer = next(run for run in check.sources if run.source == "consumer")
    assert consumer.status == "blocked"
    assert consumer.live_url == "wss://live.example/consumer"
    assert consumer.checks_read == []
