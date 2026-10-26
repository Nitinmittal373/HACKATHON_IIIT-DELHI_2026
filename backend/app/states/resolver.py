"""Turn what a buyer types into project candidates from any state.

- A registration number names its state by its format, so only that state's portal is searched.
- A name is searched on every state portal with one combined Search first (TinyFish allows 30
  searches a minute); only the states that answered then get a search of their own.
- A buyer who picked a state searches only that state.
- Beside the portals, the open web is searched and its numbers voted on (app.states.openweb),
  because many portals cannot be read but the builder and listing sites print the number.
"""

import asyncio
from dataclasses import dataclass, field

from app.models import OrderLead, PreReraNote, Project
from app.states.builder import identify_builder
from app.states.confirm import confirm_on_portals
from app.states.names import DEFAULT_STATE
from app.states.openweb import (
    NAME_SHARE,
    candidates_from,
    domain_of,
    hits_by_state,
    name_words,
    open_web_hits,
    share_of,
)
from app.states.orders import find_in_orders
from app.states.places import state_of_place
from app.states.prerera import pre_rera_notes
from app.states.registry import ADAPTERS, BY_CODE, detect_state
from app.states.search_adapter import SearchStateAdapter
from app.states.text import rank, squash
from app.tinyfish import SearchHit, WebClient, WebError

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
    pre_rera: list[PreReraNote] = field(default_factory=list)
    order_leads: list[OrderLead] = field(default_factory=list)


async def resolve_any(
    query: str, web: WebClient, state: str | None = None, locality: str | None = None
) -> Resolved:
    """Portal candidates and open-web candidates together, each number once.

    A locality ("Sector 43 Noida") narrows the portals to its state when that is known, and is
    added to the open-web search; it never counts as part of the project's name.
    """
    state = state or (state_of_place(locality) if locality else None)
    asked = f"{query} {locality}" if locality else query
    portals, hits = await asyncio.gather(
        resolve_on_portals(query, web, state),
        open_web_hits(asked, web),
        return_exceptions=True,
    )
    if isinstance(portals, BaseException):
        raise portals
    if isinstance(hits, WebError) and not portals.candidates:
        raise hits
    if isinstance(hits, BaseException):
        if not isinstance(hits, WebError):
            raise hits
        hits = []  # The portals answered; a failed open-web search only means fewer candidates.
    found = candidates_from(hits, query) + portal_pages_in(hits, query)
    wanted = [p for p in found if wanted_state(p, state) and wanted_number(p, query)]
    notes = pre_rera_notes(hits, query)
    leads: list[OrderLead] = []
    if not portals.candidates and not wanted and not notes:
        wanted, leads = await orders_candidates(query, web)
    merged = merge(portals.candidates, wanted, query)
    merged = ordered(await confirm_on_portals(merged, web), query)
    merged = await name_the_builder_of_a_typed_number(merged, query, web)
    return Resolved(merged, portals.detected_state, portals.searched_states, notes, leads)


async def orders_candidates(query: str, web: WebClient) -> tuple[list[Project], list[OrderLead]]:
    """Last resort: public orders that name the project. A failure here is just 'nothing'."""
    try:
        found = await find_in_orders(query, web)
    except WebError:
        return [], []
    return found.projects, found.leads


def wanted_state(project: Project, state: str | None) -> bool:
    return state not in BY_CODE or project.state == state


def wanted_number(project: Project, query: str) -> bool:
    """A typed number keeps only itself; a name keeps every number found."""
    typed = detect_state(query)
    number = typed[0].canonical_id(query) if typed else None
    return number is None or squash(project.rera_id) == squash(number)


def portal_pages_in(hits: list[SearchHit], query: str) -> list[Project]:
    """Numbers on a portal's own pages that Search surfaced, read from their snippets."""
    words = name_words(query)
    found = []
    for code, state_hits in hits_by_state(hits).items():
        adapter = BY_CODE[code]
        if not isinstance(adapter, SearchStateAdapter):
            continue
        for project in adapter.candidates_from_hits(state_hits):
            held = f"{project.name or ''} {project.promoter or ''}".lower()
            if words and share_of(words, held) >= NAME_SHARE:
                found.append(
                    project.model_copy(
                        update={"status": "confirmed", "sources": [domain_of(project.details_url)]}
                    )
                )
    return found


async def name_the_builder_of_a_typed_number(
    candidates: list[Project], query: str, web: WebClient
) -> list[Project]:
    """A number typed alone gets its builder from public listings when no portal page named one."""
    typed = detect_state(query)
    if typed is None or len(candidates) != 1 or candidates[0].promoter:
        return candidates
    try:
        identity = await identify_builder(candidates[0].rera_id, web)
    except WebError:
        return candidates
    if identity is None:
        return candidates
    return [candidates[0].model_copy(update={"promoter": identity.name})]


def merge(portal: list[Project], open_web: list[Project], query: str) -> list[Project]:
    """Portal candidates are confirmed by their own page; open-web ones add what they found."""
    by_number: dict[str, Project] = {}
    for project in portal:
        by_number[squash(project.rera_id)] = project.model_copy(
            update={"status": "confirmed", "sources": [domain_of(project.details_url)]}
        )
    for project in open_web:
        known = by_number.get(squash(project.rera_id))
        if known is None:
            by_number[squash(project.rera_id)] = project
            continue
        gaps = {k: v for k, v in project.model_dump().items() if getattr(known, k) is None}
        sources = list(dict.fromkeys([*known.sources, *project.sources]))
        by_number[squash(project.rera_id)] = known.model_copy(update={**gaps, "sources": sources})
    return ordered(list(by_number.values()), query)[:MAX_CANDIDATES]


def ordered(projects: list[Project], query: str) -> list[Project]:
    """A place in the query puts its state first, then confirmed numbers, then the closest name."""
    place = state_of_place(query)

    def other_state(project: Project) -> bool:
        return place is not None and project.state != place

    ranked = rank(projects, query)
    return sorted(ranked, key=lambda p: (other_state(p), p.status != "confirmed"))


async def resolve_on_portals(query: str, web: WebClient, state: str | None = None) -> Resolved:
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
