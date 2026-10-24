"""A small sliding-window rate limiter, kept in memory per client IP.

Good enough for one backend process. Each check spends TinyFish credit,
so check creation is limited per minute.
"""

import math
import time
from collections import deque
from collections.abc import Callable


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
