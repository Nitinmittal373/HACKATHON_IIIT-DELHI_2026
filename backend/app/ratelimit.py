"""A small sliding-window rate limiter, kept in memory per client IP.

Good enough for one backend process. Each check spends TinyFish credit,
so check creation is limited per minute.
"""

import math
import time
from collections import deque
from collections.abc import Callable
from datetime import date, datetime

from app.indian_time import IST, next_day


class RateLimiter:
    def __init__(
        self, limit: int, window_seconds: float = 60, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}

    def retry_after(self, key: str) -> int | None:
        """Record a hit; return seconds to wait if the key is over its limit, else None."""
        now = self._clock()
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] >= self._window:
            hits.popleft()
        if len(hits) >= self._limit:
            return max(1, math.ceil(self._window - (now - hits[0])))
        hits.append(now)
        self._forget_idle_keys(now)
        return None

    def _forget_idle_keys(self, now: float) -> None:
        if len(self._hits) < 10_000:
            return
        idle = [
            key for key, hits in self._hits.items() if not hits or now - hits[-1] >= self._window
        ]
        for key in idle:
            del self._hits[key]


class DailyLimiter:
    """Counts hits per key in the current Indian day, in memory.

    Nothing outlives the day: when the date changes the counts are dropped, so an address is
    never remembered for longer than one day.
    """

    def __init__(self) -> None:
        self._day: date | None = None
        self._counts: dict[str, int] = {}

    def retry_after(self, key: str, limit: int, now: datetime) -> int | None:
        """Record a hit; return seconds until midnight IST if the key is over its limit."""
        today = now.astimezone(IST).date()
        if today != self._day:
            self._day, self._counts = today, {}
        if self._counts.get(key, 0) >= limit:
            return max(1, int((next_day(now) - now).total_seconds()))
        self._counts[key] = self._counts.get(key, 0) + 1
        return None
