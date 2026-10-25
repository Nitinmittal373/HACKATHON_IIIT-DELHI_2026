from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import (
    CheckId,
    client_ip,
    find_check,
    get_clock,
    get_limiter,
    get_orchestrator,
    get_settings,
    get_store,
)
from app.budget import REUSE_WINDOW, seconds_until_cap_resets
from app.config import Settings
from app.models import Check, CheckCreate, Project
from app.orchestrator import Orchestrator
from app.ratelimit import RateLimiter
from app.store import Store
from app.uprera_links import details_url_for

router = APIRouter(tags=["checks"])


def rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    limiter: Annotated[RateLimiter, Depends(get_limiter)],
) -> None:
    wait = limiter.retry_after(client_ip(request, settings))
    if wait is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many checks from this address, please wait a minute",
            headers={"Retry-After": str(wait)},
        )


@router.post(
    "/api/checks",
    status_code=202,
    dependencies=[Depends(rate_limit)],
    responses={200: {"description": "A check from the last 24 hours was reused"}},
)
async def create_check(
    body: CheckCreate,
    response: Response,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
    store: Annotated[Store, Depends(get_store)],
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
) -> Check:
    now = clock()
    if not body.fresh:
        recent = store.latest_completed_check(body.rera_id, since=now - REUSE_WINDOW)
        if recent:
            response.status_code = 200
            response.headers["Location"] = f"/api/checks/{recent.id}"
            return recent.model_copy(update={"reused": True})

    wait = seconds_until_cap_resets(store, settings.max_checks_per_day, now)
    if wait is not None:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "daily_cap",
                "message": "NeevCheck has reached its limit of live checks for today",
            },
            headers={"Retry-After": str(wait)},
        )
    # The page search confirmed for this number; a number sent alone gets its stable page.
    details_url = body.details_url or details_url_for(body.rera_id)
    assert details_url is not None  # CheckCreate requires a link for new-format numbers
    check = orchestrator.start(Project(rera_id=body.rera_id, details_url=details_url))
    response.headers["Location"] = f"/api/checks/{check.id}"
    return check


@router.get("/api/checks/{check_id}")
def get_check(check_id: CheckId, store: Annotated[Store, Depends(get_store)]) -> Check:
    return find_check(store, check_id)
