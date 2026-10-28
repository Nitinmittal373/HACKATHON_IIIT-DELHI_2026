"""Neev Sentinel routes: watch a project, read alerts, and trigger a re-check run."""

import hashlib
import hmac
import json
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
)
from pydantic import BaseModel, ConfigDict, Field

from app.api.auth import User
from app.api.auth import rate_limit as account_rate_limit
from app.api.checks import rate_limit
from app.api.deps import (
    client_ip,
    get_clock,
    get_monitors,
    get_sentinel,
    get_sentinel_store,
    get_settings,
    get_store,
)
from app.config import Settings
from app.models import Project
from app.ratelimit import RateLimiter
from app.sentinel.models import (
    MAX_WATCHES_PER_ACCOUNT,
    Alert,
    Watch,
    WatchCreate,
)
from app.sentinel.monitors import MonitorError, MonitorGateway
from app.sentinel.service import Sentinel
from app.sentinel.store import SentinelStore
from app.store import Store
from app.uprera_links import project_details_url

MAX_WEBHOOK_BYTES = 200_000
logger = logging.getLogger(__name__)
router = APIRouter(tags=["sentinel"])


WATCH_LIMITS = [Depends(account_rate_limit), Depends(rate_limit)]


@router.post("/api/sentinel", status_code=201, dependencies=WATCH_LIMITS)
async def create_watch(
    body: WatchCreate,
    user: User,
    response: Response,
    store: Annotated[Store, Depends(get_store)],
    watches: Annotated[SentinelStore, Depends(get_sentinel_store)],
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
    settings: Annotated[Settings, Depends(get_settings)],
    gateway: Annotated[MonitorGateway | None, Depends(get_monitors)],
) -> Watch:
    email = user.email.lower()
    watches.adopt_unowned(user.sub, email)
    existing = watches.find_watch(user.sub, body.rera_id)
    if existing:
        response.status_code = 200  # watching twice is not an error
        return existing
    if watches.count_watches(user.sub) >= MAX_WATCHES_PER_ACCOUNT:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "watch_limit",
                "message": f"One account can watch up to {MAX_WATCHES_PER_ACCOUNT} projects",
            },
        )
    # The page search confirmed for this number; a number sent alone gets its stable page.
    details_url = project_details_url(body.rera_id, body.details_url or "")
    if store.get_project(body.rera_id) is None:
        store.save_project(Project(rera_id=body.rera_id, details_url=details_url))
    latest = store.latest_completed_check(body.rera_id)
    watch = watches.add_watch(
        user_id=user.sub,
        email=email,
        rera_id=body.rera_id,
        language=body.language,
        created_at=clock(),
        baseline_check_id=latest.id if latest else None,
    )
    if gateway and settings.sentinel_monitors:
        project = store.get_project(body.rera_id)
        await add_monitors(
            gateway, watches, watch, details_url, project and project.promoter, settings
        )
    return watch


async def add_monitors(
    gateway: MonitorGateway,
    watches: SentinelStore,
    watch: Watch,
    details_url: str | None,
    promoter: str | None,
    settings: Settings,
) -> None:
    """Best effort: if a monitor cannot be made, Sentinel's own schedule still covers the watch."""
    assert settings.public_base_url and settings.webhook_secret  # a gateway exists only then
    secret = settings.webhook_secret.get_secret_value()
    hook = f"{settings.public_base_url.rstrip('/')}/api/sentinel/webhook?secret={secret}"
    try:
        if details_url:
            page = await gateway.create_page_monitor(details_url, hook)
            watches.add_monitor(watch.id, page.monitor_id, page.kind)
        if promoter:
            topic = await gateway.create_topic_monitor(promoter, hook)
            watches.add_monitor(watch.id, topic.monitor_id, topic.kind)
    except MonitorError as error:
        logger.warning("Monitors for a watch were not fully created: %s", error)


@router.delete(
    "/api/sentinel/{watch_id}", status_code=204, dependencies=[Depends(account_rate_limit)]
)
async def remove_watch(
    watch_id: Annotated[str, Path(pattern=r"^[0-9a-f]{32}$", description="Watch id")],
    user: User,
    watches: Annotated[SentinelStore, Depends(get_sentinel_store)],
    gateway: Annotated[MonitorGateway | None, Depends(get_monitors)],
) -> Response:
    """Stop watching. Only the account that owns the watch can; for any other watch the answer
    is the same 404 as for one that does not exist."""
    if watches.get_owned_watch(user.sub, watch_id) is None:
        raise HTTPException(status_code=404, detail="No watch with this id")
    await stop_watch(watch_id, watches, gateway)
    return Response(status_code=204)


async def stop_watch(watch_id: str, watches: SentinelStore, gateway: MonitorGateway | None) -> None:
    for monitor_id in watches.remove_watch(watch_id):
        if gateway:
            try:
                await gateway.cancel(monitor_id)
            except MonitorError as error:
                logger.warning("A monitor was not cancelled: %s", error)


class Unsubscribe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1, max_length=200)


def unsubscribe_rate_limit(
    request: Request, settings: Annotated[Settings, Depends(get_settings)]
) -> None:
    limiter: RateLimiter = request.app.state.unsubscribe_limiter
    wait = limiter.retry_after(client_ip(request, settings))
    if wait is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many requests from this address, please wait a minute",
            headers={"Retry-After": str(wait)},
        )


@router.post(
    "/api/sentinel/unsubscribe", status_code=204, dependencies=[Depends(unsubscribe_rate_limit)]
)
async def unsubscribe(
    body: Unsubscribe,
    watches: Annotated[SentinelStore, Depends(get_sentinel_store)],
    gateway: Annotated[MonitorGateway | None, Depends(get_monitors)],
) -> Response:
    """The link in an alert email. Stops that watch; answers the same for any token, so it
    cannot be used to find out which tokens exist."""
    watch_id = watches.watch_for_token(body.token)
    if watch_id is not None:
        await stop_watch(watch_id, watches, gateway)
    return Response(status_code=204)


@router.get("/api/sentinel/alerts", dependencies=[Depends(account_rate_limit)])
def list_alerts(
    user: User,
    watches: Annotated[SentinelStore, Depends(get_sentinel_store)],
    store: Annotated[Store, Depends(get_store)],
) -> list[Alert]:
    """The signed-in account's alerts, newest first."""
    watches.adopt_unowned(user.sub, user.email.lower())
    return [with_new_score(alert, store) for alert in watches.alerts_for_user(user.sub)]


def with_new_score(alert: Alert, store: Store) -> Alert:
    """Alerts stored before v2 have no 300-900 scores; the new check can still be scored."""
    if alert.new_display_score is not None:
        return alert
    check = store.get_check(alert.check_id)
    return alert.model_copy(update={"new_display_score": check.display_score if check else None})


@router.post("/api/sentinel/run", status_code=202)
async def run_sentinel(
    settings: Annotated[Settings, Depends(get_settings)],
    sentinel: Annotated[Sentinel, Depends(get_sentinel)],
    x_webhook_secret: Annotated[str | None, Header()] = None,
) -> dict[str, bool]:
    """For an external cron. Needs the WEBHOOK_SECRET; with none configured nobody gets in."""
    require_secret(settings, x_webhook_secret)
    return {"started": sentinel.start_run()}


def require_secret(settings: Settings, given: str | None) -> None:
    expected = settings.webhook_secret.get_secret_value() if settings.webhook_secret else None
    if expected is None or given is None:
        raise HTTPException(status_code=401, detail="Missing or wrong secret")
    if not hmac.compare_digest(given.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Missing or wrong secret")


@router.post("/api/sentinel/webhook", status_code=202)
async def monitor_webhook(
    request: Request,
    background: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
    watches: Annotated[SentinelStore, Depends(get_sentinel_store)],
    sentinel: Annotated[Sentinel, Depends(get_sentinel)],
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
    x_webhook_secret: Annotated[str | None, Header()] = None,
    secret: Annotated[str | None, Query(max_length=200)] = None,
) -> dict[str, str]:
    """Called by a TinyFish monitor, which can only be given a URL, so the secret may come in
    the query string. A repeated delivery is acknowledged and ignored."""
    require_secret(settings, x_webhook_secret or secret)
    raw = await request.body()
    if len(raw) > MAX_WEBHOOK_BYTES:
        raise HTTPException(status_code=413, detail="Payload too large")
    monitor_id, run_id = monitor_and_run(raw)
    rera_id = watches.project_for_monitor(monitor_id) if monitor_id else None
    if rera_id is None:
        return {"status": "ignored"}
    key = f"{monitor_id}:{run_id or hashlib.sha256(raw).hexdigest()}"[:100]
    if not watches.claim_delivery(key, clock()):
        return {"status": "duplicate"}
    background.add_task(sentinel.recheck_project, rera_id)
    return {"status": "accepted"}


def monitor_and_run(raw: bytes) -> tuple[str | None, str | None]:
    """The monitor id and run id in a delivery, whichever of the two shapes it uses."""
    try:
        payload = json.loads(raw)
    except ValueError:
        return None, None
    if not isinstance(payload, dict):
        return None, None
    monitor = payload.get("monitor_id") or (payload.get("monitor") or {}).get("id")
    run = payload.get("run_id") or (payload.get("run") or {}).get("id")
    return (monitor if isinstance(monitor, str) else None, run if isinstance(run, str) else None)
