import hmac
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import get_clock, get_settings, get_store
from app.api_model import ApiModel
from app.config import Settings
from app.indian_time import day_start, month_start
from app.store import Store

router = APIRouter(tags=["admin"])


class CallCounts(ApiModel):
    checks: int
    search: int
    fetch: int
    agent: int


class CallAverages(ApiModel):
    search: float
    fetch: float
    agent: float


class Usage(ApiModel):
    """TinyFish calls the checks made (only checks that were metered), per day and month."""

    today: CallCounts
    this_month: CallCounts
    # This month's calls divided by this month's checks; zero before the first check.
    average_per_check: CallAverages


def require_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    if settings.admin_token is None:
        raise HTTPException(status_code=404, detail="Not found")
    expected = settings.admin_token.get_secret_value().encode()
    if not hmac.compare_digest((x_admin_token or "").encode(), expected):
        raise HTTPException(status_code=401, detail="A valid X-Admin-Token header is needed")


@router.get(
    "/api/admin/usage",
    dependencies=[Depends(require_admin)],
    responses={
        401: {"description": "Missing or wrong `X-Admin-Token`"},
        404: {"description": "ADMIN_TOKEN is not set, so this route is off"},
    },
)
def get_usage(
    store: Annotated[Store, Depends(get_store)],
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
) -> Usage:
    now = clock()
    today = totals(store.usage_since(day_start(now)))
    month = totals(store.usage_since(month_start(now)))
    return Usage(today=today, this_month=month, average_per_check=average(month))


def totals(usages: list[dict[str, int]]) -> CallCounts:
    return CallCounts(
        checks=len(usages),
        search=sum(u.get("search", 0) for u in usages),
        fetch=sum(u.get("fetch", 0) for u in usages),
        agent=sum(u.get("agent", 0) for u in usages),
    )


def average(month: CallCounts) -> CallAverages:
    n = month.checks or 1
    return CallAverages(
        search=round(month.search / n, 1),
        fetch=round(month.fetch / n, 1),
        agent=round(month.agent / n, 1),
    )
