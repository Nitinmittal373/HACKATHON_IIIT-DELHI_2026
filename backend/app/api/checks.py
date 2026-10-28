import re
from collections.abc import Callable
from datetime import datetime, timedelta
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
    with_recheck,
)
from app.bridge_token import BridgeUser
from app.budget import Refusal, account_refusal, recheck_opens_at, site_refusal
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
    responses={
        200: {"description": "A recent report of this project was returned; no credit was spent"},
        401: {"description": "Sign in to start a live check (`detail.code` is `signin_required`)"},
        403: {"description": "Live checks are invite-only right now (`invite_only`)"},
        429: {
            "description": "A limit is used up: `detail.code` is `account_limit`, `site_budget`, "
            "or `recheck_wait`; `Retry-After` says how long"
        },
    },
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
    """Starts a live check, or returns a recent report of the project at no cost.

    A report finished in the last REUSE_REPORT_DAYS is returned to anyone, signed in or not.
    A new live check needs a sign-in and stays within the account's and the site's budgets.
    """
    now = clock()
    recent = store.latest_completed_check(
        body.rera_id, since=now - timedelta(days=settings.reuse_report_days)
    )
    if recent and not body.fresh:
        response.status_code = 200
        response.headers["Location"] = f"/api/checks/{recent.id}"
        _save_for(user, recent.id, reports, now)
        return with_recheck(recent.model_copy(update={"reused": True}), store, settings, now)

    _refuse_unless_allowed(user, body, store, settings, now)
    # The page search confirmed for this number; a number sent alone gets its stable page.
    asked = Project(
        rera_id=body.rera_id,
        details_url=project_details_url(body.rera_id, body.details_url or ""),
    )
    check = orchestrator.start(asked, fresh=body.fresh, started_by=user.sub if user else None)
    response.headers["Location"] = f"/api/checks/{check.id}"
    _save_for(user, check.id, reports, now)
    return check


def _refuse_unless_allowed(
    user: BridgeUser | None, body: CheckCreate, store: Store, settings: Settings, now: datetime
) -> None:
    """Raises the reason a new live check may not start; returns when it may."""
    if settings.require_signin_for_checks and user is None:
        raise _refusal(
            401,
            "signin_required",
            "Sign in to run a live check. Saved reports are open to everyone.",
        )
    invited = user is not None and user.email.lower() in settings.allowed_email_set
    if settings.invite_only and not invited:
        raise _refusal(403, "invite_only", "Live checks are invite-only right now.")
    if body.fresh and (opens := recheck_opens_at(store, body.rera_id, settings, now)):
        message = f"This project was checked recently. Next re-check possible on {opens:%d %b %Y}."
        raise _refusal(429, "recheck_wait", message, Refusal("recheck_wait", message, opens), now)
    refusal = site_refusal(store, settings, now)
    if refusal is None and user is not None:
        refusal = account_refusal(store, user.sub, settings, now)
    if refusal is not None:
        raise _refusal(429, refusal.code, refusal.message, refusal, now)


def _refusal(
    status: int,
    code: str,
    message: str,
    limit: Refusal | None = None,
    now: datetime | None = None,
) -> HTTPException:
    detail: dict[str, str] = {"code": code, "message": message}
    headers = None
    if limit is not None and now is not None:
        detail["resets_at"] = limit.resets_at.isoformat()
        headers = {"Retry-After": str(limit.retry_after(now))}
    return HTTPException(status_code=status, detail=detail, headers=headers)


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
def get_check(
    check_id: CheckId,
    store: Annotated[Store, Depends(get_store)],
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
) -> Check:
    return with_recheck(find_check(store, check_id), store, settings, clock())
