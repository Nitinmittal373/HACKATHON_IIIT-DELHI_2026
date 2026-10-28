"""Saved search answers and the daily search limit per visitor.

Search costs TinyFish credit, so an answer is kept for SEARCH_CACHE_DAYS and the same question
never calls Search twice in that time. A saved answer is free and never counts toward the limit;
only a search that really runs does. The limit is per IP address and per Indian day: 15 when
signed out, 40 when signed in. The whole site has a daily cap too (SITE_SEARCHES_PER_DAY), so
many visitors together cannot spend more credit than that.
"""

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker

from app.api_model import ApiModel
from app.config import Settings
from app.db import SearchCacheRow
from app.matching import normalize
from app.ratelimit import DailyLimiter

SITE_KEY = "site"
SITE_SEARCH_MESSAGE = (
    "Today's searches are used up. Saved reports and earlier searches still open; "
    "new searches open again tomorrow."
)


class SavedSearches:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def get(self, key: str, now: datetime, days: int) -> dict[str, object] | None:
        if days <= 0:
            return None
        with self._sessions() as session:
            row = session.get(SearchCacheRow, key)
            if row is None or row.created_at < now - timedelta(days=days):
                return None
            return row.payload

    def put(self, key: str, now: datetime, payload: dict[str, object], days: int) -> None:
        if days <= 0:
            return
        with self._sessions.begin() as session:
            expired = SearchCacheRow.created_at < now - timedelta(days=days)
            session.execute(delete(SearchCacheRow).where(expired))
            session.merge(SearchCacheRow(key=key, created_at=now, payload=payload))


def cache_key(kind: str, *parts: str | None) -> str:
    return kind + ":" + "|".join(normalize(part) for part in parts if part)


class SearchGate:
    def __init__(
        self,
        cache: SavedSearches,
        limiter: DailyLimiter,
        settings: Settings,
        clock: Callable[[], datetime],
    ) -> None:
        self._cache = cache
        self._limiter = limiter
        self._site_limiter = DailyLimiter()
        self._settings = settings
        self._clock = clock

    async def serve[M: ApiModel](
        self,
        key: str,
        ip: str,
        signed_in: bool,
        model: type[M],
        produce: Callable[[], Awaitable[M]],
        keep: Callable[[M], bool] = lambda _: True,
    ) -> M:
        """The saved answer if there is one; otherwise run the search within the daily limit.

        An answer `keep` refuses (an empty one) is not saved, so a later try can find more.
        """
        now = self._clock()
        days = self._settings.search_cache_days
        saved = self._cache.get(key, now, days)
        if saved is not None:
            return model.model_validate(saved)
        self._count(ip, signed_in, now)
        answer = await produce()
        if keep(answer):
            self._cache.put(key, now, answer.model_dump(mode="json"), days)
        return answer

    def _count(self, ip: str, signed_in: bool, now: datetime) -> None:
        settings = self._settings
        limit = (
            settings.searches_per_ip_per_day_signed_in
            if signed_in
            else settings.searches_per_ip_per_day
        )
        wait = self._limiter.retry_after(ip, limit, now)
        if wait is not None:
            advice = "Sign in for more, or come back tomorrow."
            if signed_in:
                advice = "They come back tomorrow."
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "search_limit",
                    "message": f"You have used today's {limit} searches. {advice}",
                },
                headers={"Retry-After": str(wait)},
            )
        # After the visitor's own limit, so a refused visitor does not use up the site's searches.
        wait = self._site_limiter.retry_after(SITE_KEY, settings.site_searches_per_day, now)
        if wait is not None:
            raise HTTPException(
                status_code=429,
                detail={"code": "site_search_limit", "message": SITE_SEARCH_MESSAGE},
                headers={"Retry-After": str(wait)},
            )
