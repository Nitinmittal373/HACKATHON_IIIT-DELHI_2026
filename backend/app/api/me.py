"""The signed-in visitor's saved reports. Checking a project never needs these routes."""

import re
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.accounts import MAX_SAVED, UserReports
from app.api.auth import User, rate_limit
from app.api.deps import (
    CheckId,
    get_clock,
    get_monitors,
    get_sentinel_store,
    get_store,
)
from app.api.sentinel import stop_watch
from app.models import CheckSummary
from app.sentinel.monitors import MonitorGateway
from app.sentinel.store import SentinelStore
from app.store import Store

router = APIRouter(tags=["account"])

CHECK_ID = re.compile(r"^[0-9a-f]{32}$")


class SaveReports(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Newest first. Used for one check just started, and to move this browser's list in.
    ids: list[str] = Field(min_length=1, max_length=MAX_SAVED)


def get_user_reports(request: Request) -> UserReports:
    return request.app.state.user_reports


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
async def delete_account(
    user: User,
    reports: Reports,
    watches: Annotated[SentinelStore, Depends(get_sentinel_store)],
    gateway: Annotated[MonitorGateway | None, Depends(get_monitors)],
) -> None:
    """Deletes the account's saved reports, its watches and their alerts."""
    # Watches made before accounts existed belong to this account if the email is the same.
    watches.adopt_unowned(user.sub, user.email.lower())
    for watch_id in watches.watch_ids_of(user.sub):
        await stop_watch(watch_id, watches, gateway)
    reports.delete_account(user.sub)
