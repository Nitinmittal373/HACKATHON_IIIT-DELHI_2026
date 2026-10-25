"""The daily cap on live checks and the reuse window for finished ones.

Every check runs live agents that cost money, and Sentinel's re-checks count too. Two guards
keep the bill predictable: a cap on checks started per UTC day, and reuse of a check of the same
project that finished in the last 24 hours instead of starting another.
"""

from datetime import datetime, timedelta

from app.store import Store

REUSE_WINDOW = timedelta(hours=24)


def seconds_until_cap_resets(store: Store, max_per_day: int, now: datetime) -> int | None:
    """None while checks may start; otherwise how long until the UTC day rolls over."""
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if store.count_checks_since(day_start) < max_per_day:
        return None
    return max(1, int((day_start + timedelta(days=1) - now).total_seconds()))
