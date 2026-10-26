"""A promoter's other RERA projects in a state, found with TinyFish Search on its own portal.

Search only, no page reads, so it is free and quick. A result counts only when it carries the
promoter's full legal name: "Supertech Limited" never collects Supertech Realtors' projects.
Snippets are often cut short, so the list can be incomplete, and the app says so.
"""

import asyncio
import time
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING

from app.api_model import ApiModel
from app.matching import blob, legal_name_in, normalize
from app.models import DisplayScore, Project
from app.resolve import candidates_from_hits
from app.states.names import DEFAULT_STATE
from app.tinyfish import SearchHit, WebClient
from app.uprera_links import UPRERA_DOMAIN

if TYPE_CHECKING:
    from app.states.search_adapter import SearchStateAdapter

MAX_PROJECTS = 10
CACHE_SECONDS = 24 * 60 * 60
# A bound on memory: past it the cache starts afresh rather than growing forever.
MAX_CACHED = 2000
PURPOSE = "List the other UP-RERA registered projects of one promoter company"


class TrackedProject(Project):
    """A project from the search, with its NeevScore when NeevCheck has already checked it."""

    check_id: str | None = None
    display_score: DisplayScore | None = None


class TrackRecord(ApiModel):
    promoter: str
    projects: list[TrackedProject]
    searched_at: datetime


def queries(promoter: str, state: str = DEFAULT_STATE) -> list[str]:
    # Two phrasings find different pages; together they list more of the promoter's projects.
    if state == DEFAULT_STATE:
        return [f"{promoter} UP RERA project", f"{promoter} promoter UP RERA registration"]
    adapter = _search_adapter(state)
    return [
        f"{promoter} {adapter.spec.query_name} project",
        f"{promoter} promoter {adapter.rera_name} registration",
    ]


def projects_of(promoter: str, hits: list[SearchHit], state: str = DEFAULT_STATE) -> list[Project]:
    """Projects on result pages that name the promoter's full legal name, one per number."""
    named = [hit for hit in hits if legal_name_in(promoter, blob(hit))]
    if state == DEFAULT_STATE:
        return candidates_from_hits(named)
    return _search_adapter(state).candidates_from_hits(named)


def _search_adapter(state: str) -> "SearchStateAdapter":
    # Imported here: the state registry imports the UP source, which imports this module.
    from app.states.registry import adapter_for
    from app.states.search_adapter import SearchStateAdapter

    adapter = adapter_for(state)
    assert isinstance(adapter, SearchStateAdapter)
    return adapter


def _domains(state: str) -> str:
    return UPRERA_DOMAIN if state == DEFAULT_STATE else ",".join(_search_adapter(state).domains)


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

    async def find(
        self, promoter: str, exclude: str | None = None, state: str = DEFAULT_STATE
    ) -> TrackRecord:
        key = f"{state}|{normalize(promoter)}"
        cached = self._cache.get(key)
        if cached is None or self._clock() - cached[0] > CACHE_SECONDS:
            found = await asyncio.gather(
                *(
                    self._web.search(query, purpose=PURPOSE, include_domains=_domains(state))
                    for query in queries(promoter, state)
                )
            )
            hits = [hit for group in found for hit in group]
            projects = [
                TrackedProject(**p.model_dump()) for p in projects_of(promoter, hits, state)
            ]
            record = TrackRecord(promoter=promoter, projects=projects, searched_at=self._now())
            if len(self._cache) >= MAX_CACHED:
                self._cache.clear()
            cached = (self._clock(), record)
            self._cache[key] = cached
        others = [p for p in cached[1].projects if p.rera_id != exclude]
        return cached[1].model_copy(update={"projects": others[:MAX_PROJECTS]})
