"""Neev Sentinel routes: watch a project, read alerts, and trigger a re-check run."""

import hmac
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response

from app.api.checks import rate_limit
from app.api.deps import get_clock, get_sentinel, get_sentinel_store, get_settings, get_store
from app.config import Settings
from app.models import Project
from app.sentinel.models import (
    EMAIL_PATTERN,
    MAX_WATCHES_PER_EMAIL,
    Alert,
    Watch,
    WatchCreate,
)
from app.sentinel.service import Sentinel
from app.sentinel.store import SentinelStore
from app.store import Store
from app.uprera_links import details_url_for

router = APIRouter(tags=["sentinel"])


@router.post("/api/sentinel", status_code=201, dependencies=[Depends(rate_limit)])
def create_watch(
    body: WatchCreate,
    response: Response,
    store: Annotated[Store, Depends(get_store)],
    watches: Annotated[SentinelStore, Depends(get_sentinel_store)],
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
) -> Watch:
    existing = watches.find_watch(body.email, body.rera_id)
    if existing:
        response.status_code = 200  # watching twice is not an error
        return existing
    if watches.count_watches(body.email) >= MAX_WATCHES_PER_EMAIL:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "watch_limit",
                "message": f"One email can watch up to {MAX_WATCHES_PER_EMAIL} projects",
            },
        )
    # The page search confirmed for this number; a number sent alone gets its stable page.
    details_url = body.details_url or details_url_for(body.rera_id)
    assert details_url is not None  # WatchCreate requires a link for new-format numbers
    if store.get_project(body.rera_id) is None:
        store.save_project(Project(rera_id=body.rera_id, details_url=details_url))
    latest = store.latest_completed_check(body.rera_id)
    return watches.add_watch(
        email=body.email,
        rera_id=body.rera_id,
        language=body.language,
        created_at=clock(),
        baseline_check_id=latest.id if latest else None,
    )


@router.get("/api/sentinel/alerts")
def list_alerts(
    email: Annotated[str, Query(max_length=254)],
    watches: Annotated[SentinelStore, Depends(get_sentinel_store)],
) -> list[Alert]:
    address = email.strip().lower()
    if not EMAIL_PATTERN.match(address):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    return watches.alerts_for_email(address)


@router.post("/api/sentinel/run", status_code=202)
async def run_sentinel(
    settings: Annotated[Settings, Depends(get_settings)],
    sentinel: Annotated[Sentinel, Depends(get_sentinel)],
    x_webhook_secret: Annotated[str | None, Header()] = None,
) -> dict[str, bool]:
    """For an external cron. Needs the WEBHOOK_SECRET; with none configured nobody gets in."""
    expected = settings.webhook_secret.get_secret_value() if settings.webhook_secret else None
    if expected is None or x_webhook_secret is None:
        raise HTTPException(status_code=401, detail="Missing or wrong secret")
    if not hmac.compare_digest(x_webhook_secret.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Missing or wrong secret")
    return {"started": sentinel.start_run()}
