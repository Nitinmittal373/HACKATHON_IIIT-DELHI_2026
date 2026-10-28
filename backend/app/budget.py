"""The limits that protect TinyFish credit: the whole site, each account, and re-checks.

Every live check runs paid agents and searches, and Sentinel's re-checks count too. A day and a
month are counted in Indian time, because that is when the people using the site wake up.
Each function answers with a `Refusal` while a limit is used up and None while a check may start.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.config import Settings
from app.indian_time import day_start, month_start, next_day, next_month
from app.store import Store

SITE_DAY_MESSAGE = (
    "Today's live checks are used up. Saved reports are still open; "
    "new checks open again tomorrow."
)
SITE_MONTH_MESSAGE = (
    "This month's live checks are used up. Saved reports are still open; "
    "new checks open again next month."
)


@dataclass(frozen=True)
class Refusal:
    code: str
    message: str
    # When the limit lets a new check start again.
    resets_at: datetime

    def retry_after(self, now: datetime) -> int:
        return max(1, int((self.resets_at - now).total_seconds()))


def site_refusal(store: Store, settings: Settings, now: datetime) -> Refusal | None:
    """Used up for today or for the month, whichever applies first."""
    if store.count_checks_since(day_start(now)) >= settings.site_checks_per_day:
        return Refusal("site_budget", SITE_DAY_MESSAGE, next_day(now))
    if store.count_checks_since(month_start(now)) >= settings.site_checks_per_month:
        return Refusal("site_budget", SITE_MONTH_MESSAGE, next_month(now))
    return None


def checks_left_today(store: Store, user_id: str, settings: Settings, now: datetime) -> int:
    used = store.count_checks_since(day_start(now), started_by=user_id)
    return max(0, settings.checks_per_account_per_day - used)


def account_refusal(
    store: Store, user_id: str, settings: Settings, now: datetime
) -> Refusal | None:
    if checks_left_today(store, user_id, settings, now) > 0:
        return None
    limit = settings.checks_per_account_per_day
    resets = next_day(now)
    message = (
        f"You have used your {limit} live checks for today. "
        f"They come back at midnight IST ({resets:%d %b}, 12:00 am)."
    )
    return Refusal("account_limit", message, resets)


def recheck_opens_at(
    store: Store, rera_id: str, settings: Settings, now: datetime
) -> datetime | None:
    """When "Re-check now" opens for this project; None while it is open."""
    last = store.latest_check_started(rera_id)
    if last is None:
        return None
    opens = last + timedelta(days=settings.recheck_min_days)
    return opens if opens > now else None


def site_wait(store: Store, settings: Settings, now: datetime) -> int | None:
    """Seconds until the site budget lets a check start; None while it does."""
    refusal = site_refusal(store, settings, now)
    return refusal.retry_after(now) if refusal else None
