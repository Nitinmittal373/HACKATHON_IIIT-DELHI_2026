"""A builder's name in, the registered projects and company pages found for it out.

For buyers whose project has no website to search: they know the builder (from a hoarding, an
agent or a brochure) and want to see what that builder has registered. Three Searches run:

1. the state RERA domains (the named state, the state of the named city, or all of them),
2. company-registry pages that mirror MCA data (name and CIN only),
3. the open web, whose numbers are voted on like any project name's.

A result counts only when the builder's distinctive words stand in its text. Everything here is
for finding; the report scores only what a check reads from the sources.
"""

import asyncio
import re
from collections.abc import Iterable

from app.api_model import ApiModel
from app.models import Project
from app.states.names import DEFAULT_STATE
from app.states.openweb import (
    CACHE,
    NAME_SHARE,
    SearchCache,
    cached_search,
    candidates_from,
    domain_of,
    hits_by_state,
    name_words,
    share_of,
)
from app.states.places import state_of_place
from app.states.registry import ADAPTERS, BY_CODE
from app.states.search_adapter import SearchStateAdapter
from app.states.text import clean, squash
from app.tinyfish import SearchHit, WebClient

REGISTRY_DOMAINS = "zaubacorp.com,tofler.in,thecompanycheck.com,economictimes.indiatimes.com"
CIN = re.compile(r"\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b")
LEGAL_SUFFIX = r"(?:Private Limited|Pvt\.? Ltd\.?|Limited|LLP)"
COMPANY = re.compile(
    rf"([A-Z][A-Za-z0-9&'.\-]*(?: [A-Za-z0-9&'.\-]+){{0,6}} {LEGAL_SUFFIX})", re.IGNORECASE
)
# Parts of nearly every company name; they say nothing about which builder it is.
GENERIC_COMPANY_WORDS = {
    "limited", "ltd", "pvt", "private", "llp", "developers", "developer", "builders",
    "builder", "realty", "properties", "group", "constructions", "construction", "infra",
    "infrastructure", "housing", "projects", "india", "company", "co", "corp", "estates",
}  # fmt: skip
MAX_PROJECTS = 25
MAX_COMPANIES = 5


class CompanyHit(ApiModel):
    """A company-registry page that names a company like the builder's."""

    name: str
    cin: str | None = None
    source_url: str


class PromoterSearchResponse(ApiModel):
    query: str
    # The state the search was limited to, from the request or from the named city.
    state: str | None = None
    companies: list[CompanyHit]
    projects: list[Project]
    searched_states: list[str]


async def search_promoter(
    builder: str,
    web: WebClient,
    state: str | None = None,
    city: str | None = None,
    cache: SearchCache = CACHE,
) -> PromoterSearchResponse:
    chosen = state if state in BY_CODE else state_of_place(city or "") or state_of_place(builder)
    adapters = [BY_CODE[chosen]] if chosen in BY_CODE else list(ADAPTERS)
    domains = ",".join(domain for adapter in adapters for domain in adapter.domains)
    places = f" {city}" if city else ""
    portal, registry, open_web = await asyncio.gather(
        cached_search(f"{builder}{places} promoter RERA registered projects", web, cache, domains),
        cached_search(f"{builder} company CIN", web, cache, REGISTRY_DOMAINS),
        cached_search(f"{builder}{places} RERA registered projects", web, cache),
    )
    words = builder_words(builder)
    named = [hit for hit in portal if share_of(words, hit_text(hit).lower()) >= NAME_SHARE]
    voted = candidates_from(open_web, " ".join(sorted(words)) or builder)
    projects = [*portal_projects(named), *voted]
    return PromoterSearchResponse(
        query=builder,
        state=chosen if chosen in BY_CODE else None,
        companies=companies_in(registry, words),
        projects=one_each(projects)[:MAX_PROJECTS],
        searched_states=[adapter.code for adapter in adapters],
    )


def builder_words(builder: str) -> set[str]:
    """The words that tell this builder from others: "Limited" and "Developers" do not."""
    return (name_words(builder) - GENERIC_COMPANY_WORDS) or name_words(builder)


def hit_text(hit: SearchHit) -> str:
    return clean(f"{hit.title}. {hit.snippet}")


def portal_projects(hits: list[SearchHit]) -> list[Project]:
    # Imported here: app.resolve and app.sources import each other, so it must come second.
    from app.resolve import candidates_from_hits as up_candidates_from_hits

    found: list[Project] = []
    for code, state_hits in hits_by_state(hits).items():
        adapter = BY_CODE[code]
        projects = (
            up_candidates_from_hits(state_hits)
            if code == DEFAULT_STATE
            else adapter.candidates_from_hits(state_hits)
            if isinstance(adapter, SearchStateAdapter)
            else []
        )
        found += [
            p.model_copy(update={"status": "confirmed", "sources": [domain_of(p.details_url)]})
            for p in projects
        ]
    return found


def companies_in(hits: Iterable[SearchHit], words: set[str]) -> list[CompanyHit]:
    found: dict[str, CompanyHit] = {}
    for hit in hits:
        text = hit_text(hit)
        for match in COMPANY.finditer(text):
            name = match.group(1).strip()
            if share_of(words, name.lower()) < NAME_SHARE:
                continue
            cin = CIN.search(text)
            company = CompanyHit(name=name, cin=cin.group(0) if cin else None, source_url=hit.url)
            found.setdefault(squash(name), company)
    return list(found.values())[:MAX_COMPANIES]


def one_each(projects: list[Project]) -> list[Project]:
    """One entry per number; the portal's own entry wins, and sources are joined."""
    by_number: dict[str, Project] = {}
    for project in projects:
        key = squash(project.rera_id)
        known = by_number.get(key)
        if known is None:
            by_number[key] = project
            continue
        sources = list(dict.fromkeys([*known.sources, *project.sources]))
        gaps = {k: v for k, v in project.model_dump().items() if getattr(known, k) is None}
        by_number[key] = known.model_copy(update={**gaps, "sources": sources})
    return sorted(by_number.values(), key=lambda p: p.status != "confirmed")
