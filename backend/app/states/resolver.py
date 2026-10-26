"""Turn what a buyer types into project candidates from any state.

- A registration number names its state by its format, so only that state's portal is searched.
- A name is searched on every state portal with one combined Search first (TinyFish allows 30
  searches a minute); only the states that answered then get a search of their own.
- A buyer who picked a state searches only that state.
"""

import asyncio
from dataclasses import dataclass
from urllib.parse import urlsplit

from app.models import Project
from app.states.names import DEFAULT_STATE
from app.states.registry import ADAPTERS, BY_CODE, detect_state
from app.states.search_adapter import SearchStateAdapter
from app.states.text import rank
from app.tinyfish import SearchHit, WebClient

COMBINED_PURPOSE = "Find a housing project a homebuyer named on any state's RERA portal"
# States whose own portal gets a second, focused search after the combined one.
TOP_STATES = 3
MAX_CANDIDATES = 12


@dataclass(frozen=True)
class Resolved:
    candidates: list[Project]
    # The state the number's format pointed at, when the text was a registration number.
    detected_state: str | None
    searched_states: list[str]


async def resolve_any(query: str, web: WebClient, state: str | None = None) -> Resolved:
    if state in BY_CODE:
        adapter = BY_CODE[state]
        return Resolved(await adapter.resolve(query, web), None, [adapter.code])
    detected = detect_state(query)
    if detected:
        adapter = detected[0]
        return Resolved(await adapter.resolve(query, web), adapter.code, [adapter.code])
    return await resolve_name_everywhere(query, web)


async def resolve_name_everywhere(query: str, web: WebClient) -> Resolved:
    hits = await web.search(
        f"{query} RERA registered project",
        purpose=COMBINED_PURPOSE,
        include_domains=",".join(domain for adapter in ADAPTERS for domain in adapter.domains),
    )
    by_state = hits_by_state(hits)
    top = sorted(by_state, key=lambda code: len(by_state[code]), reverse=True)[:TOP_STATES]
    if DEFAULT_STATE not in top:
        top.append(DEFAULT_STATE)  # UP is where NeevCheck started; its search is always run
    focused = await asyncio.gather(*(BY_CODE[code].resolve(query, web) for code in top))

    found: dict[str, Project] = {}
    for adapter in ADAPTERS:
        if isinstance(adapter, SearchStateAdapter):
            for project in adapter.candidates_from_hits(by_state.get(adapter.code, [])):
                found.setdefault(project.rera_id, project)
    for projects in focused:
        for project in projects:
            found[project.rera_id] = project
    ranked = rank(list(found.values()), query)[:MAX_CANDIDATES]
    return Resolved(ranked, None, top)


def hits_by_state(hits: list[SearchHit]) -> dict[str, list[SearchHit]]:
    grouped: dict[str, list[SearchHit]] = {}
    for hit in hits:
        host = urlsplit(hit.url).hostname or ""
        for adapter in ADAPTERS:
            if any(host == d or host.endswith("." + d) for d in adapter.domains):
                grouped.setdefault(adapter.code, []).append(hit)
                break
    return grouped
