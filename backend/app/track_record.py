"""A promoter's other UP-RERA projects, found with TinyFish Search on up-rera.in.

Search only, no page reads, so it is free and quick. A result counts only when it carries the
promoter's full legal name: "Supertech Limited" never collects Supertech Realtors' projects.
Snippets are often cut short, so the list can be incomplete, and the app says so.
"""

import asyncio
import time
from collections.abc import Callable
from datetime import datetime

from pydantic import BaseModel

from app.matching import blob, legal_name_in, normalize
from app.models import Project
from app.resolve import candidates_from_hits
from app.tinyfish import SearchHit, WebClient
from app.uprera_links import UPRERA_DOMAIN

MAX_PROJECTS = 10
CACHE_SECONDS = 24 * 60 * 60
# A bound on memory: past it the cache starts afresh rather than growing forever.
MAX_CACHED = 2000
PURPOSE = "List the other UP-RERA registered projects of one promoter company"


class TrackRecord(BaseModel):
    promoter: str
    projects: list[Project]
    searched_at: datetime


def queries(promoter: str) -> list[str]:
    # Two phrasings find different pages; together they list more of the promoter's projects.
    return [f"{promoter} UP RERA project", f"{promoter} promoter UP RERA registration"]


def projects_of(promoter: str, hits: list[SearchHit]) -> list[Project]:
    """Projects on result pages that name the promoter's full legal name, one per number."""
    named = [hit for hit in hits if legal_name_in(promoter, blob(hit))]
    return candidates_from_hits(named)


class TrackRecords:
    """Finds and remembers each promoter's projects for a day, per process."""

    def __init__(
        self,
        web: WebClient,
        now: Callable[[], datetime],
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._web = web
        self._now = now
        self._clock = clock
        self._cache: dict[str, tuple[float, TrackRecord]] = {}

    async def find(self, promoter: str, exclude: str | None = None) -> TrackRecord:
        key = normalize(promoter)
        cached = self._cache.get(key)
        if cached is None or self._clock() - cached[0] > CACHE_SECONDS:
            found = await asyncio.gather(
                *(
                    self._web.search(query, purpose=PURPOSE, include_domains=UPRERA_DOMAIN)
                    for query in queries(promoter)
                )
            )
            hits = [hit for group in found for hit in group]
            record = TrackRecord(
                promoter=promoter, projects=projects_of(promoter, hits), searched_at=self._now()
            )
            if len(self._cache) >= MAX_CACHED:
                self._cache.clear()
            cached = (self._clock(), record)
            self._cache[key] = cached
        others = [p for p in cached[1].projects if p.rera_id != exclude]
        return cached[1].model_copy(update={"projects": others[:MAX_PROJECTS]})
