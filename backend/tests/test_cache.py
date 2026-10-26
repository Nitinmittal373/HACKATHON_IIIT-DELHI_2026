"""The per-day source cache: reused reads keep their real time; blocked reads are never kept."""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from app.cache import SourceCache, entity_for
from app.db import make_engine, make_session_factory
from app.events import EventHub
from app.models import Finding, Project
from app.orchestrator import Orchestrator
from app.sources.base import (
    Blocked,
    ChecksRead,
    FoundFinding,
    SourceContext,
    SourceEvent,
)
from app.sources.findings import build_finding
from app.store import Store
from tests.fakes import FakeWebClient

NOW = datetime(2026, 10, 26, 4, 0, tzinfo=UTC)
PROJECT = Project(
    rera_id="UPRERAPRJ8334",
    name="Eco Village",
    promoter="SUPERTECH LIMITED",
    district="Gautam Buddha Nagar",
    details_url="https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334",
)


class Uprera:
    name = "uprera"
    checks = ("registration",)

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        yield ChecksRead(("registration",))


class Registry:
    """Counts how often it really reads, and can be told to be blocked."""

    name = "registry"
    checks = ("company_status",)

    def __init__(self, blocked: bool = False) -> None:
        self.runs = 0
        self.blocked = blocked

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        self.runs += 1
        if self.blocked:
            yield Blocked("CAPTCHA")
            return
        yield FoundFinding(
            build_finding(
                source="registry",
                reliability="secondary",
                kind="company_status",
                area="financial",
                title="Company status: Active",
                verdict="ok",
                url="https://example.test/company",
                today=ctx.today,
                now=ctx.now,
            )
        )
        yield ChecksRead(("company_status",))


def make(tmp_path: Path, registry: Registry, clock: list[datetime]) -> tuple[Orchestrator, Store]:
    engine = make_engine(f"sqlite:///{(tmp_path / 'cache.db').as_posix()}")
    sessions = make_session_factory(engine)
    store = Store(sessions)
    orchestrator = Orchestrator(
        store,
        EventHub(),
        FakeWebClient(),
        concurrency=2,
        source_timeout=5,
        clock=lambda: clock[0],
        sources=lambda: [Uprera(), registry],  # type: ignore[list-item]
        source_cache=SourceCache(sessions),
    )
    return orchestrator, store


async def check(orchestrator: Orchestrator, fresh: bool = False) -> str:
    started = orchestrator.start(PROJECT, fresh=fresh)
    await orchestrator.finished(started.id)
    return started.id


def registry_finding(store: Store, check_id: str) -> Finding:
    return next(f for f in store.list_findings(check_id) if f.source == "registry")


def test_a_second_check_the_same_day_reuses_the_read_with_its_real_time(tmp_path: Path) -> None:
    registry = Registry()
    clock = [NOW]
    orchestrator, store = make(tmp_path, registry, clock)

    async def scenario() -> tuple[str, str]:
        first = await check(orchestrator)
        clock[0] = NOW + timedelta(hours=5)
        return first, await check(orchestrator)

    first, second = asyncio.run(scenario())

    assert registry.runs == 1
    assert registry_finding(store, second).read_at == NOW  # not the later check's time
    assert registry_finding(store, second).id != registry_finding(store, first).id
    assert store.get_score_v2(second) is not None


def test_a_recheck_now_reads_again(tmp_path: Path) -> None:
    registry = Registry()
    orchestrator, _ = make(tmp_path, registry, [NOW])

    async def scenario() -> None:
        await check(orchestrator)
        await check(orchestrator, fresh=True)

    asyncio.run(scenario())

    assert registry.runs == 2


def test_the_next_day_reads_again(tmp_path: Path) -> None:
    registry = Registry()
    clock = [NOW]
    orchestrator, _ = make(tmp_path, registry, clock)

    async def scenario() -> None:
        await check(orchestrator)
        clock[0] = NOW + timedelta(days=1)
        await check(orchestrator)

    asyncio.run(scenario())

    assert registry.runs == 2


def test_a_blocked_read_is_not_remembered(tmp_path: Path) -> None:
    registry = Registry(blocked=True)
    orchestrator, _ = make(tmp_path, registry, [NOW])

    async def scenario() -> None:
        await check(orchestrator)
        await check(orchestrator)

    asyncio.run(scenario())

    assert registry.runs == 2


def test_group_results_are_kept_for_a_week(tmp_path: Path) -> None:
    sessions = make_session_factory(make_engine(f"sqlite:///{(tmp_path / 'week.db').as_posix()}"))
    cache = SourceCache(sessions)
    cache.put("group", "supertech limited", date(2026, 10, 20), NOW, [], ())

    assert cache.get("group", "supertech limited", date(2026, 10, 26)) is not None
    assert cache.get("group", "supertech limited", date(2026, 10, 27)) is None
    cache.put("news", "x", date(2026, 10, 25), NOW, [], ())
    assert cache.get("news", "x", date(2026, 10, 26)) is None


def test_which_sources_are_cached_and_for_what() -> None:
    assert entity_for("group", PROJECT) == "supertech limited"
    assert entity_for("news", PROJECT) == "supertech limited|UPRERAPRJ8334"
    assert entity_for("land", PROJECT) == "supertech limited|gautam buddha nagar"
    assert entity_for("uprera", PROJECT) is None
    assert entity_for("consumer", PROJECT) is None
    assert entity_for("group", PROJECT.model_copy(update={"promoter": None})) is None
