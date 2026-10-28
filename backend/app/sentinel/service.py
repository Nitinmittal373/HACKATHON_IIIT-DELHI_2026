"""Neev Sentinel: re-check watched projects and raise an alert only when a record changed."""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.budget import site_wait
from app.config import Settings
from app.indian_time import day_start
from app.orchestrator import Orchestrator
from app.sentinel.diff import diff_findings
from app.sentinel.models import Watch
from app.sentinel.monitors import MonitorError, MonitorGateway
from app.sentinel.notify import send_alert, smtp_configured, stop_link
from app.sentinel.store import SentinelStore
from app.store import Store

logger = logging.getLogger(__name__)
# Recorded as the starter of every Sentinel check, so its share of the day's credit can be counted.
SENTINEL_STARTER = "sentinel"
# However many requests arrive, the automatic schedule looks at most this often.
MIN_GAP = timedelta(hours=1)


@dataclass
class RunSummary:
    projects_checked: int = 0
    alerts_created: int = 0
    stopped_by_daily_cap: bool = False


class Sentinel:
    def __init__(
        self,
        store: Store,
        watches: SentinelStore,
        orchestrator: Orchestrator,
        settings: Settings,
        clock: Callable[[], datetime],
    ) -> None:
        self._store = store
        self._watches = watches
        self._orchestrator = orchestrator
        self._settings = settings
        self._clock = clock
        self._running = asyncio.Lock()
        self._background: asyncio.Task[RunSummary] | None = None
        self._last_poke: datetime | None = None

    def start_run(self) -> bool:
        """Begin a run in the background; False if one is already going."""
        if self._running.locked():
            return False
        self._background = asyncio.create_task(self.run_once())
        return True

    def poke(self) -> None:
        """Called at startup and on every request: look for due re-checks, at most hourly.

        There is no timer. A free host sleeps when idle, and a sleeping process cannot count
        168 hours, so the next visit is what wakes Sentinel up.
        """
        now = self._clock()
        if self._settings.sentinel_interval_hours <= 0 or self._running.locked():
            return
        if self._last_poke is not None and now - self._last_poke < MIN_GAP:
            return
        self._last_poke = now
        self._background = asyncio.create_task(self._run_due_safely())

    def stop(self) -> None:
        if self._background is not None:
            self._background.cancel()

    async def _run_due_safely(self) -> RunSummary:
        try:
            return await self.run_due()
        except Exception:
            logger.exception("Sentinel run failed")
            return RunSummary()

    async def run_due(self) -> RunSummary:
        """Re-check watched projects whose last check is older than the interval.

        Bounded three ways: one look an hour (kept in the database, so a restart does not reset
        it), SENTINEL_CHECKS_PER_DAY re-checks a day, and never past the site's own budget.
        """
        summary = RunSummary()
        async with self._running:
            now = self._clock()
            if not self._watches.claim_run(now, MIN_GAP):
                return summary
            today = self._store.count_checks_since(day_start(now), started_by=SENTINEL_STARTER)
            room = self._settings.sentinel_checks_per_day - today
            for rera_id in self._due_projects(now)[: max(0, room)]:
                if site_wait(self._store, self._settings, self._clock()) is not None:
                    summary.stopped_by_daily_cap = True
                    logger.info("Sentinel stopped: the site check budget is used up")
                    break
                summary.alerts_created += await self._recheck(rera_id)
                summary.projects_checked += 1
        return summary

    def _due_projects(self, now: datetime) -> list[str]:
        """Watched projects never checked first, then the one checked longest ago."""
        oldest = now - timedelta(hours=self._settings.sentinel_interval_hours)
        watched = self._watches.watched_projects()
        last = {id_: self._store.latest_check_started(id_) for id_ in watched}
        due = [id_ for id_, started in last.items() if started is None or started < oldest]
        return sorted(due, key=lambda id_: (last[id_] is not None, last[id_] or now))

    async def cancel_monitors(self, gateway: MonitorGateway) -> None:
        """Monitors bill outside the site budget, so with them off none should keep running."""
        for monitor_id in self._watches.monitor_ids():
            try:
                await gateway.cancel(monitor_id)
            except MonitorError as error:
                logger.warning("A monitor was not cancelled, will retry at next start: %s", error)
                continue
            self._watches.forget_monitor(monitor_id)

    async def run_once(self) -> RunSummary:
        summary = RunSummary()
        async with self._running:
            for rera_id in self._watches.watched_projects():
                wait = site_wait(self._store, self._settings, self._clock())
                if wait is not None:
                    summary.stopped_by_daily_cap = True
                    logger.info("Sentinel stopped: the daily check cap was reached")
                    break
                summary.alerts_created += await self._recheck(rera_id)
                summary.projects_checked += 1
        return summary

    async def recheck_project(self, rera_id: str) -> int:
        """Re-check one project now, as a monitor's webhook asks. 0 when the daily cap is hit."""
        async with self._running:
            wait = site_wait(self._store, self._settings, self._clock())
            if wait is not None:
                logger.info("Webhook re-check skipped: the daily check cap was reached")
                return 0
            return await self._recheck(rera_id)

    async def _recheck(self, rera_id: str) -> int:
        project = self._store.get_project(rera_id)
        if project is None:
            return 0
        # A re-check exists to see what changed, so it must not reuse a read made earlier today.
        started = self._orchestrator.start(project, fresh=True, started_by=SENTINEL_STARTER)
        check = await self._orchestrator.finished(started.id)
        if check.status != "completed":
            return 0
        created = 0
        for watch in self._watches.watches_for_project(rera_id):
            created += await self._compare(watch, check.id)
        return created

    async def _compare(self, watch: Watch, new_check_id: str) -> int:
        baseline_id = watch.baseline_check_id
        self._watches.set_baseline(watch.id, new_check_id)
        if baseline_id is None:
            return 0  # the first finished check is the baseline, not a change
        old_check = self._store.get_check(baseline_id)
        new_check = self._store.get_check(new_check_id)
        old_score = self._store.get_score(baseline_id)
        new_score = self._store.get_score(new_check_id)
        if old_check is None or new_check is None:
            return 0
        diff = diff_findings(
            self._store.list_findings(baseline_id),
            self._store.list_findings(new_check_id),
            old_check,
            new_check,
        )
        if diff.is_empty:
            return 0
        alert_id = self._watches.add_alert(
            watch=watch,
            check_id=new_check_id,
            created_at=self._clock(),
            old_score=old_score.value if old_score else None,
            new_score=new_score.value if new_score else None,
            old_display=old_check.display_score,
            new_display=new_check.display_score,
            diff=diff,
        )
        await self._deliver(watch, alert_id)
        return 1

    async def _deliver(self, watch: Watch, alert_id: str) -> None:
        alert = self._watches.get_alert(alert_id)
        if alert is None or not smtp_configured(self._settings):
            return
        token = self._watches.new_unsubscribe_token(watch.id, self._clock())
        stop_url = stop_link(self._settings, token)
        if await send_alert(self._settings, watch.email, watch.language, alert, stop_url):
            self._watches.mark_emailed(alert_id)
