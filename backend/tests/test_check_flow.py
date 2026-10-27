"""How a check carries on when UP-RERA is read only in part, and how stored checks are re-scored."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi.testclient import TestClient

from app.events import EventHub
from app.main import create_app
from app.models import Project
from app.orchestrator import Orchestrator
from app.sources.base import (
    ChecksRead,
    Progress,
    SourceContext,
    SourceError,
    SourceEvent,
)
from app.sources.uprera import UpreraSource
from app.store import Store
from tests.conftest import FIXED_NOW, URL_8334, make_settings, make_web, read_events
from tests.fakes import FakeWebClient, load_page
from tests.sourcekit import ECO_VILLAGE_1, context, run_source


def test_uprera_reports_what_it_read_before_the_slow_summary_pages() -> None:
    web = FakeWebClient(pages={URL_8334: load_page("uprera_8334.html")})
    events = run_source(UpreraSource(), context(web=web))

    reads = [i for i, e in enumerate(events) if isinstance(e, ChecksRead)]
    summary_step = next(
        i for i, e in enumerate(events) if isinstance(e, Progress) and "complaint counts" in e.text
    )
    assert reads[0] < summary_step
    assert set(events[reads[0]].checks) == {"registration", "completion_date"}  # type: ignore[union-attr]


class Slow:
    """A source that reports one read and then takes longer than the check allows."""

    name = "uprera"
    checks = ("registration", "completion_date", "extensions")

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        yield ChecksRead(("registration", "completion_date"))
        await asyncio.sleep(5)
        yield ChecksRead(self.checks)  # type: ignore[arg-type]


class Broken:
    name = "uprera"
    checks = ("registration",)

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        raise SourceError("The UP-RERA page could not be parsed")
        yield  # pragma: no cover  (makes this an async generator)


class Quiet:
    name = "news"
    checks = ("registration",)

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        yield Progress("nothing to say")


def run_check(tmp_path: Path, project: Project, sources: list[object]) -> tuple[Store, str]:
    app = create_app(make_settings(tmp_path), web=FakeWebClient(), clock=lambda: FIXED_NOW)
    with TestClient(app) as client:
        store: Store = app.state.store
        orchestrator = Orchestrator(
            store,
            EventHub(),
            FakeWebClient(),
            concurrency=2,
            source_timeout=0.2,
            clock=lambda: FIXED_NOW,
            sources=lambda: sources,  # type: ignore[arg-type, return-value]
        )

        async def go() -> str:
            check = orchestrator.start(project)
            await orchestrator.finished(check.id)
            return check.id

        check_id = client.portal.call(go)  # type: ignore[attr-defined]
        return store, check_id


def test_a_lane_that_times_out_keeps_what_it_read_and_is_partial(tmp_path: Path) -> None:
    store, check_id = run_check(tmp_path, ECO_VILLAGE_1, [Slow(), Quiet()])

    check = store.get_check(check_id)
    assert check is not None and check.status == "completed"
    uprera = next(run for run in check.sources if run.source == "uprera")
    assert uprera.status == "partial"
    assert uprera.checks_read == ["registration", "completion_date"]
    assert "No answer within" in (uprera.message or "")


def test_a_partly_read_uprera_does_not_stop_the_other_lanes(tmp_path: Path) -> None:
    store, check_id = run_check(tmp_path, ECO_VILLAGE_1, [Broken(), Quiet()])

    check = store.get_check(check_id)
    assert check is not None and check.status == "completed"
    assert {run.source: run.status for run in check.sources} == {
        "uprera": "failed",
        "news": "completed",
    }


def test_no_record_and_no_builder_is_the_only_way_to_fail(tmp_path: Path) -> None:
    bare = Project(rera_id="UPRERAPRJ8334", details_url=URL_8334)
    store, check_id = run_check(tmp_path, bare, [Broken(), Quiet()])

    check = store.get_check(check_id)
    assert check is not None and check.status == "failed"


def test_stored_checks_are_scored_again_at_startup(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    with TestClient(create_app(settings, web=make_web(), clock=lambda: FIXED_NOW)) as client:
        check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
        read_events(client, check_id)
        before = client.get(f"/api/checks/{check_id}").json()["display_score"]
        store: Store = client.app.state.store  # type: ignore[attr-defined]
        stale = store.get_score_v2(check_id)
        assert stale is not None
        store.save_score_v2(check_id, stale.model_copy(update={"value": 300}))

    with TestClient(create_app(settings, web=make_web(), clock=lambda: FIXED_NOW)) as client:
        after = client.get(f"/api/checks/{check_id}").json()["display_score"]
        again = client.app.state.store.rescore_all()  # type: ignore[attr-defined]
        twice = client.get(f"/api/checks/{check_id}").json()["display_score"]
    assert after == before == twice
    assert again == 1
