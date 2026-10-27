"""Turn what a buyer types into UP-RERA project candidates.

- A registration number opens its own up-rera.in page (app.resolve).
- A name is searched on up-rera.in first; the open web is searched beside it and its numbers
  are voted on (app.states.openweb), because builder and listing sites print the number of
  projects whose UP-RERA page Search cannot find.
- A number of another state's RERA, or a name that only a city outside Uttar Pradesh explains,
  is answered with `outside_up` and nothing is searched for the number.
"""

import asyncio
from dataclasses import dataclass, field

from app.models import OrderLead, Project, is_other_state_number, normalize_rera_id
from app.resolve import fill_in, resolve
from app.resolve import rank as rank_by_name
from app.states.builder import identify_builder
from app.states.confirm import confirm_on_portals
from app.states.openweb import candidates_from, domain_of, open_web_hits
from app.states.orders import find_in_orders
from app.states.places import names_place_outside_up
from app.states.text import squash
from app.tinyfish import WebClient, WebError

MAX_CANDIDATES = 12


@dataclass(frozen=True)
class Resolved:
    candidates: list[Project]
    # True when nothing was found and the text points outside Uttar Pradesh.
    outside_up: bool = False
    order_leads: list[OrderLead] = field(default_factory=list)


async def resolve_any(query: str, web: WebClient, locality: str | None = None) -> Resolved:
    """Portal candidates and open-web candidates together, each number once.

    A locality ("Sector 43 Noida") is added to the open-web search; it never counts as part of
    the project's name.
    """
    if is_other_state_number(query):
        return Resolved([], outside_up=True)
    asked = f"{query} {locality}" if locality else query
    portal, hits = await asyncio.gather(
        resolve(query, web), open_web_hits(asked, web), return_exceptions=True
    )
    if isinstance(portal, BaseException):
        raise portal
    if isinstance(hits, WebError) and not portal:
        raise hits
    if isinstance(hits, BaseException):
        if not isinstance(hits, WebError):
            raise hits
        hits = []  # The portal answered; a failed open-web search only means fewer candidates.
    wanted = [p for p in candidates_from(hits, query) if wanted_number(p, query)]
    leads: list[OrderLead] = []
    if not portal and not wanted:
        wanted, leads = await orders_candidates(query, web)
    merged = merge(portal, wanted, query)
    merged = ordered(await confirm_on_portals(merged, web), query)
    merged = await complete_from_pages(merged, web)
    merged = await name_the_builder_of_a_typed_number(merged, query, web)
    outside = not merged and names_place_outside_up(asked)
    return Resolved(merged, outside, leads)


async def orders_candidates(query: str, web: WebClient) -> tuple[list[Project], list[OrderLead]]:
    """Last resort: public orders that name the project. A failure here is just 'nothing'."""
    try:
        found = await find_in_orders(query, web)
    except WebError:
        return [], []
    return found.projects, found.leads


async def complete_from_pages(candidates: list[Project], web: WebClient) -> list[Project]:
    """A candidate found through listings has no name or registration date until its own page
    is read; fill those in so the buyer is asked about a named project, not a bare number."""
    gaps = [p for p in candidates if p.name is None or p.registered_on is None]
    if not gaps:
        return candidates
    read = {p.rera_id: p for p in await fill_in(gaps, web)}

    def completed(project: Project) -> Project:
        page = read.get(project.rera_id)
        if page is None:
            return project  # the page could not be read; the candidate stays as search saw it
        facts = {
            field: getattr(page, field)
            for field in ("name", "promoter", "registered_on", "district")
            if getattr(page, field) is not None
        }
        return project.model_copy(update=facts)

    return [completed(p) for p in candidates]


def wanted_number(project: Project, query: str) -> bool:
    """A typed number keeps only itself; a name keeps every number found."""
    number = normalize_rera_id(query)
    return number is None or squash(project.rera_id) == squash(number)


async def name_the_builder_of_a_typed_number(
    candidates: list[Project], query: str, web: WebClient
) -> list[Project]:
    """A number typed alone gets its builder from public listings when its page named none."""
    if normalize_rera_id(query) is None or len(candidates) != 1 or candidates[0].promoter:
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
    """Confirmed numbers first, then the closest name."""
    ranked = rank_by_name(projects, query)
    return sorted(ranked, key=lambda p: p.status != "confirmed")
