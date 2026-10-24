"""Turn what a buyer types into UP-RERA project candidates.

- An old-format RERA number maps straight to its details page, which is
  read to show the buyer the project's name before anything runs.
- A new-format number, a project name or a promoter name goes through
  TinyFish Search; only up-rera.in results count, and the number, name and
  date are read from each result's title and snippet.
"""

import re
from datetime import date, datetime
from urllib.parse import urlsplit

from app.models import Project, is_new_format, is_uprera_url, normalize_rera_id
from app.sources.uprera import describe_project
from app.tinyfish import SearchHit, WebClient

MAX_CANDIDATES = 8
DETAILS_URL = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id={digits}"
SEARCH_PURPOSE = "Find the UP-RERA registration page of a housing project a homebuyer named"

RERA_IN_TEXT = re.compile(r"UPRERAPRJ\d{1,7}(?:/\d{2}/\d{4})?", re.IGNORECASE)
NAME = re.compile(
    r"Project Name\s*[:.,]?\s*:?\s*(?P<name>.+?)"
    r"(?=\s+Project Id|\s+Registration Number|\.\s|,\s|\s*\.\.\.|\s*$)"
)
REGISTERED = re.compile(r"Registration Date\s*[:.]?\s*(?P<date>\d{2}-\d{2}-\d{4})")
PROMOTER = re.compile(r"Promoter Name\s*[:.]?\s*(?P<name>.+?)(?=\s+Promoter Id|\.\s|\s*\.\.\.|$)")


def details_url_for(rera_id: str) -> str | None:
    """Old-format numbers have a stable details page; new-format ones do not."""
    if is_new_format(rera_id):
        return None
    return DETAILS_URL.format(digits=rera_id.removeprefix("UPRERAPRJ"))


async def resolve(query: str, web: WebClient) -> list[Project]:
    rera_id = normalize_rera_id(query)
    if rera_id and (url := details_url_for(rera_id)):
        project = await describe_project(Project(rera_id=rera_id, details_url=url), web)
        return [project] if project else []

    hits = await web.search(f"{query.strip()} UP RERA project", purpose=SEARCH_PURPOSE)
    candidates = candidates_from_hits(hits)
    if rera_id:
        return [c for c in candidates if c.rera_id == rera_id]
    return rank(candidates, query)[:MAX_CANDIDATES]


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
    words = set(_words(query))

    def overlap(project: Project) -> int:
        return len(words & set(_words(f"{project.name or ''} {project.promoter or ''}")))

    return sorted(candidates, key=overlap, reverse=True)


def _candidate(hit: SearchHit) -> Project | None:
    if not is_uprera_url(_https(hit.url)):
        return None
    text = f"{hit.title} {hit.snippet}"
    found = RERA_IN_TEXT.search(text)
    if found is None:
        return None
    rera_id = found.group(0).upper()
    url = details_url_for(rera_id) or _summary_url(hit.url)
    if url is None:
        return None
    return Project(
        rera_id=rera_id,
        name=_match(NAME, hit.snippet, "name"),
        promoter=_match(PROMOTER, hit.snippet, "name"),
        registered_on=_date(_match(REGISTERED, hit.snippet, "date")),
        details_url=url,
    )


def _summary_url(url: str) -> str | None:
    """New-format numbers are only reachable through the Projectsummary link search returns."""
    url = _https(url)
    return url if urlsplit(url).path.lower() == "/projectsummary" else None


def _https(url: str) -> str:
    return re.sub(r"^http://", "https://", url.strip())


def _match(pattern: re.Pattern[str], text: str, group: str) -> str | None:
    found = pattern.search(text)
    if found is None:
        return None
    value = found.group(group).strip(" .,:")
    # A value cut off by the search engine ("Gaursons Promoters Private ...") is not trusted.
    if text[found.end() :].lstrip().startswith("..."):
        return None
    return value or None


def _date(text: str | None) -> date | None:
    return datetime.strptime(text, "%d-%m-%Y").date() if text else None


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^a-z0-9]+", text.lower()) if len(w) > 1]
