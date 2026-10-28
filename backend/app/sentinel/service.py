"""Neev Sentinel: re-check watched projects and raise an alert only when a record changed."""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from app.budget import site_wait
from app.config import Settings
from app.orchestrator import Orchestrator
from app.sentinel.diff import diff_findings
from app.sentinel.models import Watch
from app.sentinel.notify import send_alert, smtp_configured, stop_link
from app.sentinel.store import SentinelStore
from app.store import Store

logger = logging.getLogger(__name__)
HOUR_SECONDS = 3600


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

    def start_run(self) -> bool:
        """Begin a run in the background; False if one is already going."""
        if self._running.locked():
            return False
        self._background = asyncio.create_task(self.run_once())
        return True

    async def loop(self) -> None:
        """Re-check on the configured schedule until the app stops."""
        interval = self._settings.sentinel_interval_hours * HOUR_SECONDS
        while True:
            await asyncio.sleep(interval)
            try:
                await self.run_once()
            except Exception:
                logger.exception("Sentinel run failed")

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
        started = self._orchestrator.start(project, fresh=True)
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
