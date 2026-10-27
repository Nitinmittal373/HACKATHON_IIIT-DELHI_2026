"""A builder's name in, the registered projects and company pages found for it out.

For buyers whose project has no website to search: they know the builder (from a hoarding, an
agent or a brochure) and want to see what that builder has registered. Three Searches run:

1. up-rera.in,
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
from app.resolve import candidates_from_hits
from app.states.openweb import (
    CACHE,
    NAME_SHARE,
    SearchCache,
    cached_search,
    candidates_from,
    domain_of,
    name_words,
    share_of,
)
from app.states.places import names_place_outside_up
from app.states.text import clean, squash
from app.tinyfish import SearchHit, WebClient
from app.uprera_links import UPRERA_DOMAIN

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
    companies: list[CompanyHit]
    projects: list[Project]
    # True when nothing was found and the city points outside Uttar Pradesh.
    outside_up: bool = False


async def search_promoter(
    builder: str,
    web: WebClient,
    city: str | None = None,
    cache: SearchCache = CACHE,
) -> PromoterSearchResponse:
    places = f" {city}" if city else ""
    portal, registry, open_web = await asyncio.gather(
        cached_search(
            f"{builder}{places} promoter RERA registered projects", web, cache, UPRERA_DOMAIN
        ),
        cached_search(f"{builder} company CIN", web, cache, REGISTRY_DOMAINS),
        cached_search(f"{builder}{places} RERA registered projects", web, cache),
    )
    words = builder_words(builder)
    named = [hit for hit in portal if share_of(words, hit_text(hit).lower()) >= NAME_SHARE]
    voted = candidates_from(open_web, " ".join(sorted(words)) or builder)
    projects = one_each([*portal_projects(named), *voted])[:MAX_PROJECTS]
    return PromoterSearchResponse(
        query=builder,
        companies=companies_in(registry, words),
        projects=projects,
        outside_up=not projects and names_place_outside_up(f"{builder}{places}"),
    )


def builder_words(builder: str) -> set[str]:
    """The words that tell this builder from others: "Limited" and "Developers" do not."""
    return (name_words(builder) - GENERIC_COMPANY_WORDS) or name_words(builder)


def hit_text(hit: SearchHit) -> str:
    return clean(f"{hit.title}. {hit.snippet}")


def portal_projects(hits: list[SearchHit]) -> list[Project]:
    return [
        p.model_copy(update={"status": "confirmed", "sources": [domain_of(p.details_url)]})
        for p in candidates_from_hits([hit for hit in hits if domain_of(hit.url) == UPRERA_DOMAIN])
    ]


def companies_in(hits: Iterable[SearchHit], words: set[str]) -> list[CompanyHit]:
    found: dict[str, CompanyHit] = {}
    for hit in hits:
        text = hit_text(hit)
        for match in COMPANY.finditer(text):
            name = _once(match.group(1).strip())
            if share_of(words, name.lower()) < NAME_SHARE:
                continue
            cin = CIN.search(text)
            company = CompanyHit(name=name, cin=cin.group(0) if cin else None, source_url=hit.url)
            found.setdefault(squash(name), company)
    return list(found.values())[:MAX_COMPANIES]


def _once(name: str) -> str:
    """A title and its first sentence repeat the name: "X LIMITED. X LIMITED" is "X LIMITED"."""
    repeated = re.fullmatch(r"(.+?)\.?\s+\1", name, re.IGNORECASE)
    return repeated.group(1) if repeated else name


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
