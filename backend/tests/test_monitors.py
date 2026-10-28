"""Watching a project with TinyFish monitors: creation, cancel, and the webhook."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.sentinel.monitors import CreatedMonitor, MonitorError
from tests.conftest import FIXED_NOW, make_settings, make_web
from tests.test_accounts import SECRET as BRIDGE_SECRET
from tests.test_accounts import auth
from tests.test_sentinel import (
    EMAIL,
    RECORDING,
    SECRET,
    alerts,
    insolvency_answer,
    run_check,
    watch,
)

BASE = "https://api.example.org"


class FakeMonitors:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.created: list[tuple[str, str, str]] = []
        self.cancelled: list[str] = []

    async def create_page_monitor(self, url: str, webhook_url: str) -> CreatedMonitor:
        return self._make("page", url, webhook_url)

    async def create_topic_monitor(self, builder: str, webhook_url: str) -> CreatedMonitor:
        return self._make("topic", builder, webhook_url)

    def _make(self, kind: str, target: str, hook: str) -> CreatedMonitor:
        if self.fail:
            raise MonitorError("Monitor not created (APIError)")
        self.created.append((kind, target, hook))
        return CreatedMonitor(f"mon-{kind}", kind)  # type: ignore[arg-type]

    async def cancel(self, monitor_id: str) -> None:
        self.cancelled.append(monitor_id)

    async def aclose(self) -> None:
        return None


def build(tmp_path: Path, monitors: FakeMonitors, **settings: object) -> TestClient:
    values = {
        "webhook_secret": SECRET,
        "public_base_url": BASE,
        "sentinel_monitors": True,
        "sentinel_interval_hours": 0,
        "auth_bridge_secret": BRIDGE_SECRET,
        **settings,
    }
    app = create_app(
        make_settings(tmp_path, **values),
        web=make_web().replay(RECORDING),
        clock=lambda: FIXED_NOW,
        cache_dir=None,
        monitors=monitors,
    )
    return TestClient(app, headers=auth())


def hook(client: TestClient, body: dict[str, object], secret: str | None = SECRET):
    params = {"secret": secret} if secret else {}
    return client.post("/api/sentinel/webhook", params=params, json=body)


def test_watching_creates_a_page_and_a_topic_monitor_that_call_back(tmp_path: Path) -> None:
    monitors = FakeMonitors()
    with build(tmp_path, monitors) as client:
        run_check(client)
        assert watch(client).status_code == 201

    assert [kind for kind, _, _ in monitors.created] == ["page", "topic"]
    assert monitors.created[0][1].startswith("https://www.up-rera.in/")
    assert monitors.created[1][1] == "SUPERTECH LIMITED"
    assert all(h == f"{BASE}/api/sentinel/webhook?secret={SECRET}" for _, _, h in monitors.created)


def test_without_a_public_address_no_monitor_is_made(tmp_path: Path) -> None:
    app = create_app(
        make_settings(
            tmp_path,
            webhook_secret=SECRET,
            sentinel_interval_hours=0,
            auth_bridge_secret=BRIDGE_SECRET,
        ),
        web=make_web().replay(RECORDING),
        clock=lambda: FIXED_NOW,
        cache_dir=None,
    )
    with TestClient(app, headers=auth()) as client:
        run_check(client)
        assert watch(client).status_code == 201
        assert client.app.state.monitors is None  # type: ignore[attr-defined]


def test_a_failed_monitor_does_not_fail_the_watch(tmp_path: Path) -> None:
    with build(tmp_path, FakeMonitors(fail=True)) as client:
        run_check(client)
        assert watch(client).status_code == 201


def test_removing_a_watch_cancels_its_monitors(tmp_path: Path) -> None:
    monitors = FakeMonitors()
    with build(tmp_path, monitors) as client:
        run_check(client)
        watch_id = watch(client).json()["id"]
        assert client.delete(f"/api/sentinel/{watch_id}").status_code == 204
        assert client.delete(f"/api/sentinel/{watch_id}").status_code == 404

    assert sorted(monitors.cancelled) == ["mon-page", "mon-topic"]


def test_the_webhook_needs_the_secret(tmp_path: Path) -> None:
    with build(tmp_path, FakeMonitors()) as client:
        assert hook(client, {"monitor_id": "mon-page"}, secret=None).status_code == 401
        assert hook(client, {"monitor_id": "mon-page"}, secret="wrong").status_code == 401
        header = client.post(
            "/api/sentinel/webhook",
            headers={"X-Webhook-Secret": SECRET},
            json={"monitor_id": "unknown"},
        )
        assert header.json() == {"status": "ignored"}


def test_a_delivery_rechecks_the_project_once_and_alerts_with_the_diff(tmp_path: Path) -> None:
    monitors = FakeMonitors()
    web = make_web().replay(RECORDING)
    app = create_app(
        make_settings(
            tmp_path,
            webhook_secret=SECRET,
            public_base_url=BASE,
            sentinel_monitors=True,
            sentinel_interval_hours=0,
            auth_bridge_secret=BRIDGE_SECRET,
        ),
        web=web,
        clock=lambda: FIXED_NOW,
        cache_dir=None,
        monitors=monitors,
    )
    with TestClient(app, headers=auth()) as client:
        run_check(client)
        watch(client)
        page = next(a["url"] for a in RECORDING["agents"] if "fortuneindia" in a["url"])
        web.agent_runs[page] = insolvency_answer(admitted_on="April 1, 2022")

        first = hook(client, {"monitor_id": "mon-page", "run_id": "run-1"})
        again = hook(client, {"monitor_id": "mon-page", "run_id": "run-1"})

        assert first.json() == {"status": "accepted"}
        assert again.json() == {"status": "duplicate"}
        found = alerts(client)
        assert len(found) == 1
        assert [c["title"] for c in found[0]["changed"]]  # type: ignore[union-attr]
        assert found[0]["rera_id"] == "UPRERAPRJ8334"
    assert EMAIL
