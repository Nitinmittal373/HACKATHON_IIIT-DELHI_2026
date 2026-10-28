from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.auth import MaybeUser
from app.api.deps import get_clock, get_settings, get_store
from app.api_model import ApiModel
from app.budget import checks_left_today, site_refusal
from app.config import Settings
from app.store import Store

router = APIRouter(tags=["meta"])


class Limits(ApiModel):
    """What a live check costs a visitor, so the pages can say it before they start one."""

    require_signin: bool
    invite_only: bool
    checks_per_account_per_day: int
    reuse_report_days: int
    recheck_min_days: int
    # False while the site's own budget for today or this month is used up.
    live_checks_open: bool
    # Set only for a signed-in account: its live checks left today.
    checks_left_today: int | None
    # Set only for a signed-in account: whether its e-mail may start live checks.
    invited: bool | None


@router.get("/api/limits")
def get_limits(
    store: Annotated[Store, Depends(get_store)],
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
    user: MaybeUser,
) -> Limits:
    now = clock()
    invited = None
    if user is not None:
        invited = not settings.invite_only or user.email.lower() in settings.allowed_email_set
    return Limits(
        require_signin=settings.require_signin_for_checks,
        invite_only=settings.invite_only,
        checks_per_account_per_day=settings.checks_per_account_per_day,
        reuse_report_days=settings.reuse_report_days,
        recheck_min_days=settings.recheck_min_days,
        live_checks_open=site_refusal(store, settings, now) is None,
        checks_left_today=checks_left_today(store, user.sub, settings, now) if user else None,
        invited=invited,
    )
