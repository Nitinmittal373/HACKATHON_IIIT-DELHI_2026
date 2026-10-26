"""Runs one check: every source, the event stream, storage and the score.

UP-RERA runs first because it confirms the project exists and names the
promoter the other sources search for. The rest run in parallel, at most
AGENT_CONCURRENCY at a time. A source that fails or is blocked only leaves
its checks unread; the check itself fails only when UP-RERA cannot be read,
because without it there is nothing to score.
"""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.cache import CachedRead, SourceCache, entity_for
from app.events import EventHub
from app.models import (
    Check,
    CheckKey,
    Event,
    EventType,
    FamilyTree,
    Finding,
    Project,
    SourceName,
    SourceRun,
)
from app.scoring.engine import score
from app.scoring.v2.from_runs import score_from_runs
from app.sources import build_sources
from app.sources.base import (
    Blocked,
    ChecksRead,
    FoundFinding,
    GroupTree,
    LiveUrl,
    Progress,
    ProjectDetails,
    Source,
    SourceContext,
    SourceError,
    SourceEvent,
    SourceUnavailable,
)
from app.sources.state_rera import StateReraSource
from app.states.names import DEFAULT_STATE
from app.states.registry import adapter_for
from app.store import Store
from app.tinyfish import WebClient, WebError

logger = logging.getLogger(__name__)
IST = timezone(timedelta(hours=5, minutes=30))  # records are dated in Indian time


def utc_now() -> datetime:
    return datetime.now(UTC)


class Orchestrator:
    def __init__(
        self,
        store: Store,
        hub: EventHub,
        web: WebClient,
        *,
        concurrency: int,
        source_timeout: float,
        clock: Callable[[], datetime] = utc_now,
        sources: Callable[[], list[Source]] = build_sources,
        cache_dir: Path | None = None,
        source_cache: SourceCache | None = None,
    ) -> None:
        self._store = store
        self._hub = hub
        self._web = web
        self._slots = asyncio.Semaphore(concurrency)
        self._source_timeout = source_timeout
        self._clock = clock
        self._sources = sources
        self._cache_dir = cache_dir
        self._source_cache = source_cache
        self._tasks: dict[str, asyncio.Task[None]] = {}
        # The family tree a check's group source drew, kept until its score is saved.
        self._families: dict[str, FamilyTree] = {}

    def start(self, project: Project, fresh: bool = False) -> Check:
        """Create the check and run it in the background; returns at once."""
        check_id = uuid.uuid4().hex
        self._store.save_project(_merge(self._store.get_project(project.rera_id), project))
        self._store.create_check(check_id, project.rera_id, self._clock())
        self._hub.open(check_id)
        task = asyncio.create_task(self._run(check_id, project, fresh))
        self._tasks[check_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(check_id, None))
        check = self._store.get_check(check_id)
        assert check is not None
        return check

    async def finished(self, check_id: str) -> Check:
        """Wait for a started check to end and return it as stored (used by Sentinel)."""
        task = self._tasks.get(check_id)
        if task is not None:
            await asyncio.shield(task)
        check = self._store.get_check(check_id)
        assert check is not None
        return check

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run(self, check_id: str, project: Project, fresh: bool = False) -> None:
        self._store.set_check_status(check_id, "running")
        try:
            primary, *others = self._sources()
            adapter = adapter_for(project.state)
            if project.state != DEFAULT_STATE:
                primary = StateReraSource(adapter)
            now = self._clock()
            ctx = SourceContext(
                project=project,
                web=self._web,
                today=now.astimezone(IST).date(),
                now=now,
                check_id=check_id,
                cache_dir=self._cache_dir,
            )
            ctx, primary_read = await self._run_source(check_id, primary, ctx, fresh)
            if "registration" not in primary_read:
                message = f"{adapter.rera_name} could not be read, so no score"
                self._finish(check_id, "failed", message=message)
                return
            others_read = await asyncio.gather(
                *(self._run_source(check_id, s, ctx, fresh) for s in others)
            )
            read = set(primary_read).union(*(checks for _, checks in others_read))
            findings = self._store.list_findings(check_id)
            result = score(findings, read)
            self._store.save_score(check_id, result)
            self._save_score_v2(check_id, findings)
            family = self._families.pop(check_id, None)
            if family is not None:
                self._store.save_family(check_id, family)
            scored = self._store.get_check(check_id)
            display = scored.display_score if scored else None
            self._finish(
                check_id,
                "completed",
                score=result.model_dump(mode="json", include=SUMMARY),
                display_score=display.model_dump(mode="json") if display else None,
            )
        except asyncio.CancelledError:
            self._finish(check_id, "failed", message="The server stopped before the check finished")
            raise
        except Exception:
            logger.exception("check %s failed", check_id)
            self._finish(check_id, "failed", message="Something went wrong while running the check")

    async def _run_source(
        self, check_id: str, source: Source, ctx: SourceContext, fresh: bool = False
    ) -> tuple[SourceContext, tuple[CheckKey, ...]]:
        async with self._slots:
            run = SourceRun(source=source.name, status="running")
            self._store.save_source_run(check_id, run)
            self._emit(check_id, "source.started", source.name)
            read: tuple[CheckKey, ...] = ()
            entity = entity_for(source.name, ctx.project) if self._source_cache else None
            cached = None if fresh else self._cached(source, entity, ctx)
            collected: list[Finding] = []
            family: FamilyTree | None = None
            try:
                async with asyncio.timeout(self._source_timeout):
                    events = replay(cached) if cached else source.run(ctx)
                    async for event in events:
                        match event:
                            case LiveUrl(url=url):
                                run = run.model_copy(update={"live_url": url})
                                self._store.save_source_run(check_id, run)
                                self._emit(check_id, "source.live_url", source.name, url=url)
                            case Progress(text=text):
                                self._emit(check_id, "source.progress", source.name, text=text)
                            case FoundFinding(finding=finding):
                                collected.append(finding)
                                self._store.add_finding(check_id, finding)
                                data = finding.model_dump(mode="json")
                                self._emit(check_id, "finding.added", source.name, finding=data)
                            case Blocked(reason=reason):
                                run = run.model_copy(
                                    update={"status": "blocked", "message": reason}
                                )
                                self._emit(check_id, "source.blocked", source.name, reason=reason)
                            case ChecksRead(checks=checks):
                                read = tuple(c for c in checks if c in source.checks)
                            case GroupTree(tree=tree):
                                family = tree
                                self._families[check_id] = tree
                            case ProjectDetails(project=project):
                                self._store.save_project(project)
                                ctx = replace(ctx, project=project)
                status = "blocked" if run.status == "blocked" else "completed"
                run = run.model_copy(update={"status": status})
                if status == "completed" and cached is None and entity and (read or collected):
                    self._remember(source, entity, ctx, collected, read, family)
            except SourceUnavailable as error:
                run = run.model_copy(update={"status": "unavailable", "message": str(error)})
            except (SourceError, WebError) as error:
                run = run.model_copy(update={"status": "failed", "message": str(error)})
            except TimeoutError:
                message = f"No answer within {self._source_timeout:.0f} seconds"
                run = run.model_copy(update={"status": "blocked", "message": message})
                self._emit(check_id, "source.blocked", source.name, reason="timeout")
            except Exception:
                logger.exception("source %s failed in check %s", source.name, check_id)
                message = "Unexpected error while reading this source"
                run = run.model_copy(update={"status": "failed", "message": message})

            if run.status != "completed":
                read = ()
            run = run.model_copy(update={"checks_read": list(read)})
            self._store.save_source_run(check_id, run)
            self._emit(
                check_id,
                "source.completed",
                source.name,
                status=run.status,
                message=run.message,
                checks_read=list(read),
            )
            return ctx, read

    def _cached(self, source: Source, entity: str | None, ctx: SourceContext) -> CachedRead | None:
        if self._source_cache is None or entity is None:
            return None
        return self._source_cache.get(source.name, entity, ctx.today)

    def _remember(
        self,
        source: Source,
        entity: str,
        ctx: SourceContext,
        findings: list[Finding],
        read: tuple[CheckKey, ...],
        family: FamilyTree | None,
    ) -> None:
        assert self._source_cache is not None
        self._source_cache.put(source.name, entity, ctx.today, ctx.now, findings, read, family)

    def _save_score_v2(self, check_id: str, findings: list[Finding]) -> None:
        """v2 sits next to v1; if it ever fails the v1 report must still be delivered."""
        try:
            check = self._store.get_check(check_id)
            runs = check.sources if check else []
            self._store.save_score_v2(check_id, score_from_runs(findings, runs))
        except Exception:
            logger.exception("v2 score failed for check %s", check_id)

    def _finish(self, check_id: str, status: str, **data: Any) -> None:
        self._store.set_check_status(check_id, status, self._clock())  # type: ignore[arg-type]
        self._emit(check_id, "check.completed", "check", status=status, **data)

    def _emit(self, check_id: str, type_: EventType, source: SourceName | str, **data: Any) -> None:
        event = Event.model_validate(
            {
                "type": type_,
                "check_id": check_id,
                "source": source,
                "ts": self._clock(),
                "data": data,
            }
        )
        self._hub.publish(event)


async def replay(cached: CachedRead) -> AsyncIterator[SourceEvent]:
    """A cached read as the same events a live read would give, with its real read time."""
    stamp = cached.read_at.astimezone(IST).strftime("%d %b %Y, %H:%M IST")
    yield Progress(f"Reusing the read made on {stamp}; nothing was fetched again")
    for finding in cached.fresh_copies():
        yield FoundFinding(finding)
    if cached.family is not None:
        yield GroupTree(cached.family)
    yield ChecksRead(cached.checks_read)


SUMMARY = {"value", "band", "band_label", "confidence", "provisional", "hard_stop"}


def _merge(known: Project | None, new: Project) -> Project:
    """Keep what we already know about a project when a new check names fewer fields."""
    if known is None:
        return new
    filled = {k: v for k, v in new.model_dump().items() if v is not None}
    return known.model_copy(update=filled)
