import re
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from app.accounts import UserReports
from app.api.auth import MaybeUser
from app.api.deps import (
    CheckId,
    client_ip,
    find_check,
    get_clock,
    get_limiter,
    get_orchestrator,
    get_settings,
    get_store,
    get_user_reports,
)
from app.bridge_token import BridgeUser
from app.budget import REUSE_WINDOW, seconds_until_cap_resets
from app.config import Settings
from app.models import Check, CheckCreate, Project, RecentCheck
from app.orchestrator import Orchestrator
from app.ratelimit import RateLimiter
from app.store import Store
from app.uprera_links import project_details_url

router = APIRouter(tags=["checks"])

# A visitor's history lives in their browser; it asks for at most this many checks at once.
MAX_LISTED = 50
CHECK_ID = re.compile(r"^[0-9a-f]{32}$")


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
    reports: Annotated[UserReports, Depends(get_user_reports)],
    user: MaybeUser,
) -> Check:
    """Starts a check. With a sign-in token the check is also saved to that account."""
    now = clock()
    if not body.fresh:
        recent = store.latest_completed_check(body.rera_id, since=now - REUSE_WINDOW)
        if recent:
            response.status_code = 200
            response.headers["Location"] = f"/api/checks/{recent.id}"
            _save_for(user, recent.id, reports, now)
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
    asked = Project(
        rera_id=body.rera_id,
        details_url=project_details_url(body.rera_id, body.details_url or ""),
    )
    check = orchestrator.start(asked, fresh=body.fresh)
    response.headers["Location"] = f"/api/checks/{check.id}"
    _save_for(user, check.id, reports, now)
    return check


def _save_for(user: BridgeUser | None, check_id: str, reports: UserReports, now: datetime) -> None:
    if user is not None:
        reports.add(user.sub, [check_id], now)


@router.get("/api/checks", responses={422: {"description": "A malformed id, or more than 50"}})
def list_checks(
    # 50 ids of 32 characters and their commas.
    ids: Annotated[str, Query(max_length=MAX_LISTED * 33, description="Comma-separated ids")],
    store: Annotated[Store, Depends(get_store)],
) -> list[RecentCheck]:
    """The checks a browser kept, by id. Ids the server no longer has are left out."""
    wanted = list(dict.fromkeys(part.strip() for part in ids.split(",") if part.strip()))
    if len(wanted) > MAX_LISTED or not all(CHECK_ID.match(check_id) for check_id in wanted):
        raise HTTPException(status_code=422, detail=f"ids must be up to {MAX_LISTED} check ids")
    return store.recents(wanted)


@router.get("/api/checks/{check_id}")
def get_check(check_id: CheckId, store: Annotated[Store, Depends(get_store)]) -> Check:
    return find_check(store, check_id)
