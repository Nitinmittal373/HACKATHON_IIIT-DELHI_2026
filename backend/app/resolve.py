"""Turn what a buyer types into UP-RERA project candidates.

- A number from 2017-18 (UPRERAPRJ8334) opens its stable details page directly.
- Later numbers (UPRERAPRJ188811/08/2024, or six digits such as UPRERAPRJ396176)
  have no stable page, so Search on up-rera.in finds their Projectsummary link.
  Either way the number counts only if its own page shows it with a name and a promoter.
- A project or promoter name goes through Search limited to up-rera.in. If that finds
  no numbers, a second Search without the limit is read for UPRERAPRJ numbers; each
  one is confirmed on up-rera.in and kept only if its name or promoter shares a word
  with the query, because other sites print numbers of unrelated projects too.
Candidates from search are completed from their own pages, within a time budget.
"""

import asyncio
import re
from datetime import date, datetime

from app.models import Project, is_uprera_url, normalize_rera_id
from app.sources.uprera import describe_project
from app.tinyfish import SearchHit, WebClient, WebError
from app.uprera_links import (
    UPRERA_DOMAIN,
    details_url_for,
    find_summary_url,
    https,
    rera_ids_in,
    summary_url,
)

MAX_CANDIDATES = 8
SEARCH_PURPOSE = "Find the UP-RERA registration page of a housing project a homebuyer named"
# Pages are read in parallel to fill in district and promoter; slow ones keep what search said.
FILL_IN_SECONDS = 35
FILL_IN_CONCURRENCY = 4

NAME = re.compile(
    r"Project Name\s*[:.,]?\s*:?\s*(?P<name>.+?)"
    r"(?=\s+Project Id|\s+Registration Number|\.\s|,\s|\s*\.\.\.|\s*$)"
)
REGISTERED = re.compile(r"Registration Date\s*[:.]?\s*(?P<date>\d{2}-\d{2}-\d{4})")
PROMOTER = re.compile(r"Promoter Name\s*[:.]?\s*(?P<name>.+?)(?=\s+Promoter Id|\.\s|\s*\.\.\.|$)")
# Search engines append their own link text to some snippets.
SNIPPET_TAIL = re.compile(r"\s*(Read more|More)\s*$", re.IGNORECASE)
# Words that do not tell one project from another.
COMMON_WORDS = {"up", "rera", "project", "projects", "phase", "the", "and", "by", "of", "in"}


async def resolve(query: str, web: WebClient) -> list[Project]:
    rera_id = normalize_rera_id(query)
    if rera_id:
        project = await resolve_number(rera_id, web)
        return [project] if project else []
    return await resolve_name(query.strip(), web)


async def resolve_number(rera_id: str, web: WebClient) -> Project | None:
    """The project as its own up-rera.in page shows it, or None if no page confirms it."""
    stable = details_url_for(rera_id)
    if stable:
        try:
            if project := await read_project(rera_id, stable, web):
                return project
        except WebError:
            pass  # Later numbers have no such page; Fetch cannot read the error UP-RERA shows.
    summary = await find_summary_url(rera_id, web)
    return await read_project(rera_id, summary, web) if summary else None


async def read_project(rera_id: str, url: str, web: WebClient) -> Project | None:
    """The project on this page, only if the page shows this number, a name and a promoter."""
    project = await describe_project(Project(rera_id=rera_id, details_url=url), web)
    if project is None or not (project.name and project.promoter):
        return None
    return project


async def resolve_name(query: str, web: WebClient) -> list[Project]:
    hits = await web.search(
        f"{query} UP RERA project", purpose=SEARCH_PURPOSE, include_domains=UPRERA_DOMAIN
    )
    candidates = rank(candidates_from_hits(hits), query)[:MAX_CANDIDATES]
    if candidates:
        return await fill_in(candidates, web)
    elsewhere = await numbers_named_elsewhere(query, web)
    return rank([project for project in elsewhere if overlap(project, query)], query)


async def numbers_named_elsewhere(query: str, web: WebClient) -> list[Project]:
    """UPRERAPRJ numbers that other sites print for this name, each confirmed on up-rera.in."""
    hits = await web.search(f"{query} UP RERA project", purpose=SEARCH_PURPOSE)
    ids = list(dict.fromkeys(rera_id for hit in hits for rera_id in rera_ids_in(hit)))
    found = await asyncio.gather(
        *(_confirmed(rera_id, web) for rera_id in ids[:MAX_CANDIDATES])
    )
    return [project for project in found if project]


async def _confirmed(rera_id: str, web: WebClient) -> Project | None:
    # One unreadable page must not sink the whole search; that number is simply not shown.
    try:
        return await resolve_number(rera_id, web)
    except WebError:
        return None


async def fill_in(candidates: list[Project], web: WebClient) -> list[Project]:
    """Complete each candidate from its own page and settle which page a check should read.

    The stable details page is tried first, as it holds the most dates; then the page search
    returned. A candidate whose pages were read but never showed it is dropped; one whose pages
    could not be read at all keeps what search said, since it came from up-rera.in itself.
    """
    gate = asyncio.Semaphore(FILL_IN_CONCURRENCY)

    async def complete(candidate: Project) -> Project | None:
        pages = [details_url_for(candidate.rera_id), candidate.details_url]
        unreadable = True
        async with gate:
            for url in dict.fromkeys(page for page in pages if page):
                try:
                    project = await read_project(candidate.rera_id, url, web)
                except WebError:
                    continue
                if project:
                    return project
                unreadable = False
        return candidate if unreadable else None

    tasks = [asyncio.ensure_future(complete(c)) for c in candidates]
    done, pending = await asyncio.wait(tasks, timeout=FILL_IN_SECONDS)
    for task in pending:
        task.cancel()
    results = [
        task.result() if task in done else candidate
        for task, candidate in zip(tasks, candidates, strict=True)
    ]
    return [project for project in results if project]


def candidates_from_hits(hits: list[SearchHit]) -> list[Project]:
    """One candidate per RERA number, in search order, filling gaps from later hits."""
    by_id: dict[str, Project] = {}
    for hit in hits:
        candidate = _candidate(hit)
        if candidate is None:
            continue
        known = by_id.get(candidate.rera_id)
        if known is None:
            by_id[candidate.rera_id] = candidate
        else:
            missing = {k: v for k, v in candidate.model_dump().items() if getattr(known, k) is None}
            by_id[candidate.rera_id] = known.model_copy(update=missing)
    return list(by_id.values())


def rank(candidates: list[Project], query: str) -> list[Project]:
    """Projects whose name holds more of the query's words come first; ties keep search order."""
    return sorted(candidates, key=lambda project: overlap(project, query), reverse=True)


def overlap(project: Project, query: str) -> int:
    """How many of the query's distinguishing words the project's name or promoter holds."""
    return len(set(_words(query)) & set(_words(f"{project.name or ''} {project.promoter or ''}")))


def _candidate(hit: SearchHit) -> Project | None:
    if not is_uprera_url(https(hit.url)):
        return None
    ids = rera_ids_in(hit)
    if not ids:
        return None
    rera_id = ids[0]
    # A Projectsummary hit is this number's own page; fill_in() still tries the stable one.
    url = summary_url(hit.url) or details_url_for(rera_id)
    if url is None:
        return None
    return Project(
        rera_id=rera_id,
        name=_match(NAME, hit.snippet, "name"),
        promoter=_match(PROMOTER, hit.snippet, "name"),
        registered_on=_date(_match(REGISTERED, hit.snippet, "date")),
        details_url=url,
    )


def _match(pattern: re.Pattern[str], text: str, group: str) -> str | None:
    found = pattern.search(text)
    if found is None:
        return None
    value = SNIPPET_TAIL.sub("", found.group(group)).strip(" .,:")
    # A value cut off by the search engine ("Gaursons Promoters Private ...") is not trusted.
    if text[found.end() :].lstrip().startswith("..."):
        return None
    return value or None


def _date(text: str | None) -> date | None:
    return datetime.strptime(text, "%d-%m-%Y").date() if text else None


def _words(text: str) -> list[str]:
    words = re.split(r"[^a-z0-9]+", text.lower())
    return [w for w in words if len(w) > 1 and w not in COMMON_WORDS]
