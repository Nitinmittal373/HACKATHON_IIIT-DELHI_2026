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
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from app.events import EventHub
from app.models import Check, CheckKey, Event, EventType, Project, SourceName, SourceRun
from app.scoring.engine import score
from app.sources import build_sources
from app.sources.base import (
    Blocked,
    ChecksRead,
    FoundFinding,
    LiveUrl,
    Progress,
    ProjectDetails,
    Source,
    SourceContext,
    SourceError,
    SourceUnavailable,
)
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
    ) -> None:
        self._store = store
        self._hub = hub
        self._web = web
        self._slots = asyncio.Semaphore(concurrency)
        self._source_timeout = source_timeout
        self._clock = clock
        self._sources = sources
        self._tasks: set[asyncio.Task[None]] = set()

    def start(self, project: Project) -> Check:
        """Create the check and run it in the background; returns at once."""
        check_id = uuid.uuid4().hex
        self._store.save_project(_merge(self._store.get_project(project.rera_id), project))
        self._store.create_check(check_id, project.rera_id, self._clock())
        self._hub.open(check_id)
        task = asyncio.create_task(self._run(check_id, project))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        check = self._store.get_check(check_id)
        assert check is not None
        return check

    async def shutdown(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _run(self, check_id: str, project: Project) -> None:
        self._store.set_check_status(check_id, "running")
        try:
            primary, *others = self._sources()
            now = self._clock()
            ctx = SourceContext(
                project=project, web=self._web, today=now.astimezone(IST).date(), now=now
            )
            ctx, primary_read = await self._run_source(check_id, primary, ctx)
            if "registration" not in primary_read:
                self._finish(check_id, "failed", message="UP-RERA could not be read, so no score")
                return
            others_read = await asyncio.gather(
                *(self._run_source(check_id, s, ctx) for s in others)
            )
            read = set(primary_read).union(*(checks for _, checks in others_read))
            result = score(self._store.list_findings(check_id), read)
            self._store.save_score(check_id, result)
            self._finish(
                check_id, "completed", score=result.model_dump(mode="json", include=SUMMARY)
            )
        except asyncio.CancelledError:
            self._finish(check_id, "failed", message="The server stopped before the check finished")
            raise
        except Exception:
            logger.exception("check %s failed", check_id)
            self._finish(check_id, "failed", message="Something went wrong while running the check")

    async def _run_source(
        self, check_id: str, source: Source, ctx: SourceContext
    ) -> tuple[SourceContext, tuple[CheckKey, ...]]:
        async with self._slots:
            run = SourceRun(source=source.name, status="running")
            self._store.save_source_run(check_id, run)
            self._emit(check_id, "source.started", source.name)
            read: tuple[CheckKey, ...] = ()
            try:
                async with asyncio.timeout(self._source_timeout):
                    async for event in source.run(ctx):
                        match event:
                            case LiveUrl(url=url):
                                run = run.model_copy(update={"live_url": url})
                                self._store.save_source_run(check_id, run)
                                self._emit(check_id, "source.live_url", source.name, url=url)
                            case Progress(text=text):
                                self._emit(check_id, "source.progress", source.name, text=text)
                            case FoundFinding(finding=finding):
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
                            case ProjectDetails(project=project):
                                self._store.save_project(project)
                                ctx = replace(ctx, project=project)
                status = "blocked" if run.status == "blocked" else "completed"
                run = run.model_copy(update={"status": status})
            except SourceUnavailable as error:
                run = run.model_copy(update={"status": "unavailable", "message": str(error)})
            except (SourceError, WebError) as error:
                run = run.model_copy(update={"status": "failed", "message": str(error)})
            except TimeoutError:
                message = f"No answer within {self._source_timeout:.0f} seconds"
                run = run.model_copy(update={"status": "failed", "message": message})
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


SUMMARY = {"value", "band", "band_label", "confidence", "provisional", "hard_stop"}


def _merge(known: Project | None, new: Project) -> Project:
    """Keep what we already know about a project when a new check names fewer fields."""
    if known is None:
        return new
    filled = {k: v for k, v in new.model_dump().items() if v is not None}
    return known.model_copy(update=filled)
