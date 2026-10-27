"""The signed-in visitor's saved reports. Checking a project never needs these routes."""

import re
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.accounts import MAX_SAVED, UserReports
from app.api.deps import CheckId, client_ip, get_clock, get_settings, get_store
from app.bridge_token import BridgeUser, InvalidToken, verify_bridge_token
from app.config import Settings
from app.models import CheckSummary
from app.ratelimit import RateLimiter
from app.store import Store

router = APIRouter(tags=["account"])

CHECK_ID = re.compile(r"^[0-9a-f]{32}$")


class SaveReports(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Newest first. Used for one check just started, and to move this browser's list in.
    ids: list[str] = Field(min_length=1, max_length=MAX_SAVED)


def get_user_reports(request: Request) -> UserReports:
    return request.app.state.user_reports


def get_account_limiter(request: Request) -> RateLimiter:
    return request.app.state.account_limiter


def rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    limiter: Annotated[RateLimiter, Depends(get_account_limiter)],
) -> None:
    wait = limiter.retry_after(client_ip(request, settings))
    if wait is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many requests from this address, please wait a minute",
            headers={"Retry-After": str(wait)},
        )


def current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
    authorization: Annotated[str | None, Header()] = None,
) -> BridgeUser:
    if settings.auth_bridge_secret is None:
        raise HTTPException(status_code=503, detail="Accounts are not set up on this server")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Sign in to use saved reports")
    try:
        return verify_bridge_token(token, settings.auth_bridge_secret.get_secret_value(), clock())
    except InvalidToken:
        message = "Your sign-in expired; please sign in again"
        raise HTTPException(status_code=401, detail=message) from None


User = Annotated[BridgeUser, Depends(current_user)]
Reports = Annotated[UserReports, Depends(get_user_reports)]
Checks = Annotated[Store, Depends(get_store)]
Now = Annotated[Callable[[], datetime], Depends(get_clock)]


@router.get("/api/me/reports", dependencies=[Depends(rate_limit)])
def list_saved(user: User, reports: Reports, store: Checks) -> list[CheckSummary]:
    """The checks saved to this account, newest first. Ids the server no longer has are left out."""
    return store.summaries(reports.ids(user.sub))


@router.post("/api/me/reports", dependencies=[Depends(rate_limit)])
def save_reports(
    body: SaveReports, user: User, reports: Reports, store: Checks, clock: Now
) -> list[CheckSummary]:
    """Saves check ids (the first is the newest) and answers with the account's whole list."""
    ids = list(dict.fromkeys(body.ids))
    if not all(CHECK_ID.match(check_id) for check_id in ids):
        raise HTTPException(status_code=422, detail="ids must be check ids")
    existing = {summary.id for summary in store.summaries(ids)}
    reports.add(user.sub, [check_id for check_id in ids if check_id in existing], clock())
    return store.summaries(reports.ids(user.sub))


@router.delete("/api/me/reports/{check_id}", status_code=204, dependencies=[Depends(rate_limit)])
def forget_report(check_id: CheckId, user: User, reports: Reports) -> None:
    reports.remove(user.sub, check_id)


@router.delete("/api/me", status_code=204, dependencies=[Depends(rate_limit)])
def delete_account(user: User, reports: Reports) -> None:
    """Deletes the account's saved reports. Nothing else is stored about the account."""
    reports.delete_account(user.sub)
