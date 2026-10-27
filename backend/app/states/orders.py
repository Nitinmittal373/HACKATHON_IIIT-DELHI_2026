"""Find a project through public orders and judgments that name it.

Used last, when the portals, the open web and the buyer's documents gave nothing. A RERA order,
a consumer-court judgment or an NCLT list that names the project also names its builder
("Tajinder Singh vs Mahagun India Pvt. Ltd.") and sometimes its number. Both are used only to
find the project: the builder's registered projects are searched, and the ones whose name matches
the buyer's words come back as candidates with the order's link, so the buyer can read it. The
order itself is never a finding in a report.

Fetch cannot read every court site, so a page it fails to read falls back to its Search snippet.
"""

import asyncio
import re
from dataclasses import dataclass

from app.models import OrderLead, Project
from app.states.openweb import (
    CACHE,
    NAME_SHARE,
    SearchCache,
    cached_search,
    domain_of,
    name_words,
    names_project,
    numbers_in,
    prepare,
    share_of,
)
from app.states.text import squash
from app.tinyfish import SearchHit, WebClient, WebError
from app.uprera_links import project_details_url

ORDER_SEARCHES: tuple[tuple[str, str | None], ...] = (
    ("{q} RERA order", None),
    ("{q} judgment", "indiankanoon.org"),
    ("{q} NCLT order", "nclt.gov.in"),
)
ORDER_DOMAIN_ENDINGS = (".gov.in", "indiankanoon.org", "nclt.gov.in")
# Pages worth opening for a number: orders published as documents.
MAX_FETCHES = 2
MAX_LEADS = 2
FETCH_PURPOSE = "Read a public order that names a project, to find its RERA number"
LEGAL_SUFFIX = r"(?:Private Limited|Pvt\.? ?Ltd\.?|Limited|LLP)"
# "vs M/s Mahagun India Pvt. Ltd.": the respondent of a buyer's complaint is the builder.
BUILDER_IN_TITLE = re.compile(
    rf"\bvs\.?\s+(?:M/s\.?\s+)?(?P<name>[A-Z][\w&'.\- ]{{2,60}}?{LEGAL_SUFFIX})", re.IGNORECASE
)


@dataclass(frozen=True)
class OrdersResult:
    projects: list[Project]
    leads: list[OrderLead]


async def find_in_orders(query: str, web: WebClient, cache: SearchCache = CACHE) -> OrdersResult:
    groups = await asyncio.gather(
        *(cached_search(t.format(q=query), web, cache, domains) for t, domains in ORDER_SEARCHES)
    )
    words = name_words(query)
    named = [
        hit
        for group in groups
        for hit in group
        if share_of(words, f"{hit.title} {hit.snippet}".lower()) >= NAME_SHARE
    ]
    projects = await numbers_in_orders([hit for hit in named if is_order(hit)], query, web)
    return OrdersResult(projects, [] if projects else builder_leads(named))


async def numbers_in_orders(hits: list[SearchHit], query: str, web: WebClient) -> list[Project]:
    words = name_words(query)
    found: dict[str, Project] = {}
    texts = await asyncio.gather(*(order_text(hit, web, fetch) for hit, fetch in fetchable(hits)))
    for hit, text in zip(hits, texts, strict=True):
        readable = prepare(text)
        numbers = numbers_in(readable)
        for index, (rera_id, _, _) in enumerate(numbers):
            if names_project(readable, numbers, index, words, hit):
                found.setdefault(rera_id, project_from_order(rera_id, hit))
    return list(found.values())


def is_order(hit: SearchHit) -> bool:
    """An order or judgment: a PDF, or a page of a court, tribunal or government site.

    Listing and tracker pages also answer "RERA order" searches, but they are not orders.
    """
    domain = domain_of(hit.url)
    return hit.url.lower().endswith(".pdf") or domain.endswith(ORDER_DOMAIN_ENDINGS)


def fetchable(hits: list[SearchHit]) -> list[tuple[SearchHit, bool]]:
    """Each hit with whether its page is opened: only the first few orders published as PDFs."""
    opened = 0
    result = []
    for hit in hits:
        fetch = hit.url.lower().endswith(".pdf") and opened < MAX_FETCHES
        opened += fetch
        result.append((hit, fetch))
    return result


async def order_text(hit: SearchHit, web: WebClient, fetch: bool) -> str:
    snippet = f"{hit.title}. {hit.snippet}"
    if not fetch:
        return snippet
    try:
        return (await web.fetch_text(hit.url, purpose=FETCH_PURPOSE)).text
    except WebError:
        return snippet


def builder_leads(hits: list[SearchHit]) -> list[OrderLead]:
    """Each builder an order names as the respondent, with the order that says so."""
    leads: dict[str, OrderLead] = {}
    for hit in hits:
        found = BUILDER_IN_TITLE.search(f"{hit.title}. {hit.snippet}")
        if found is None:
            continue
        builder = re.sub(r"\s+", " ", found.group("name")).strip(" .,")
        leads.setdefault(
            squash(builder), OrderLead(builder=builder, order_title=hit.title, order_url=hit.url)
        )
    return list(leads.values())[:MAX_LEADS]


def project_from_order(rera_id: str, hit: SearchHit) -> Project:
    return Project(
        rera_id=rera_id,
        details_url=project_details_url(rera_id),
        status="from_order",
        found_in=hit.url,
        sources=[domain_of(hit.url)],
    )
