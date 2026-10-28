"""Sentinel's automatic schedule: no monitors by default, and paced re-checks on request."""

import asyncio
from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import make_engine, make_session_factory
from app.main import create_app
from app.sentinel.service import SENTINEL_STARTER, RunSummary
from app.sentinel.store import SentinelStore
from tests.conftest import FIXED_NOW, make_settings, make_web
from tests.test_accounts import SECRET as BRIDGE_SECRET
from tests.test_accounts import auth
from tests.test_monitors import BASE, FakeMonitors
from tests.test_sentinel import RECORDING, SECRET, run_check, watch


def build(tmp_path: Path, now: list, monitors: FakeMonitors | None = None, **settings: object):
    values = {
        "webhook_secret": SECRET,
        "public_base_url": BASE,
        "auth_bridge_secret": BRIDGE_SECRET,
        "sentinel_interval_hours": 24,
        **settings,
    }
    app = create_app(
        make_settings(tmp_path, **values),
        web=make_web().replay(RECORDING),
        clock=lambda: now[0],
        cache_dir=None,
        monitors=monitors,
    )
    return TestClient(app, headers=auth())


def run_due(client: TestClient) -> RunSummary:
    return client.portal.call(client.app.state.sentinel.run_due)  # type: ignore[union-attr, attr-defined]


def sentinel_checks(client: TestClient) -> int:
    store = client.app.state.store  # type: ignore[attr-defined]
    return store.count_checks_since(FIXED_NOW - timedelta(days=30), started_by=SENTINEL_STARTER)


def test_a_watch_makes_no_monitor_calls_by_default(tmp_path: Path) -> None:
    monitors = FakeMonitors()
    with build(tmp_path, [FIXED_NOW], monitors) as client:
        run_check(client)
        assert watch(client).status_code == 201

    assert monitors.created == []


def test_monitors_left_by_an_earlier_version_are_cancelled_at_startup(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now, FakeMonitors(), sentinel_monitors=True) as client:
        run_check(client)
        watch(client)
        assert client.app.state.sentinel_store.monitor_ids() == ["mon-page", "mon-topic"]  # type: ignore[attr-defined]

    monitors = FakeMonitors()
    with build(tmp_path, now, monitors) as client:
        assert sorted(monitors.cancelled) == ["mon-page", "mon-topic"]
        assert client.app.state.sentinel_store.monitor_ids() == []  # type: ignore[attr-defined]


def test_monitors_stay_when_they_are_switched_on(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now, FakeMonitors(), sentinel_monitors=True) as client:
        run_check(client)
        watch(client)

    monitors = FakeMonitors()
    with build(tmp_path, now, monitors, sentinel_monitors=True):
        assert monitors.cancelled == []


def test_a_project_is_rechecked_only_once_its_last_check_is_older_than_the_interval(
    tmp_path: Path,
) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now) as client:
        run_check(client)
        watch(client)

        now[0] = FIXED_NOW + timedelta(hours=2)
        assert run_due(client).projects_checked == 0
        now[0] = FIXED_NOW + timedelta(days=2)
        assert run_due(client).projects_checked == 1
        assert sentinel_checks(client) == 1


def test_only_one_recheck_a_day_and_the_next_day_picks_up_the_rest(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now) as client:
        run_check(client)
        watch(client)
        watch(client, rera_id="UPRERAPRJ1001")

        now[0] = FIXED_NOW + timedelta(days=8)
        assert run_due(client).projects_checked == 1
        now[0] += timedelta(hours=2)
        assert run_due(client).projects_checked == 0
        now[0] += timedelta(days=1)
        assert run_due(client).projects_checked == 1
        assert sentinel_checks(client) == 2


def test_sentinel_never_spends_what_the_site_budget_has_used_up(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now, sentinel_interval_hours=1, site_checks_per_day=1) as client:
        run_check(client)  # the day's only live check
        watch(client)

        now[0] = FIXED_NOW + timedelta(hours=2)
        summary = run_due(client)

        assert summary.stopped_by_daily_cap and summary.projects_checked == 0
        assert sentinel_checks(client) == 0


def test_a_request_starts_a_due_recheck_once_an_hour_at_most(tmp_path: Path) -> None:
    now = [FIXED_NOW]

    async def settle(client: TestClient) -> None:
        task = client.app.state.sentinel._background  # type: ignore[attr-defined]
        if task is not None:
            await task

    with build(tmp_path, now, sentinel_checks_per_day=5) as client:
        run_check(client)
        watch(client)
        assert sentinel_checks(client) == 0  # nothing is due yet

        now[0] = FIXED_NOW + timedelta(days=8)
        client.get("/api/health")
        client.portal.call(settle, client)
        assert sentinel_checks(client) == 1

        now[0] += timedelta(minutes=10)
        client.get("/api/health")
        client.portal.call(settle, client)
        assert sentinel_checks(client) == 1


def test_the_last_run_survives_a_restart(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'state.db').as_posix()}"
    hour = timedelta(hours=1)

    def open_store() -> SentinelStore:
        return SentinelStore(make_session_factory(make_engine(url)))

    assert open_store().claim_run(FIXED_NOW, hour)
    assert not open_store().claim_run(FIXED_NOW + timedelta(minutes=30), hour)
    assert open_store().claim_run(FIXED_NOW + timedelta(minutes=61), hour)


def test_the_schedule_is_off_when_the_interval_is_zero(tmp_path: Path) -> None:
    now = [FIXED_NOW]
    with build(tmp_path, now, sentinel_interval_hours=0) as client:
        run_check(client)
        watch(client)
        now[0] = FIXED_NOW + timedelta(days=30)
        client.get("/api/health")
        client.portal.call(asyncio.sleep, 0.05)
        assert sentinel_checks(client) == 0
