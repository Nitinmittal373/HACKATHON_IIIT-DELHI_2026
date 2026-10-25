"""News and court reports: a weak signal, so it is secondary and capped.

- Up to three stories about delays, NCLT or NBCC that name the project or its
  promoter: marked for review, 10 points each (news can never take more than 60).
- If the Supreme Court's NBCC order names this project, one context finding
  with 0 points: it explains what is happening, it is not a penalty.

Search is enough here; no browser agent is needed. This source reads none of
the seven key checks, so it never changes confidence.
"""

import re
from collections.abc import AsyncIterator
from datetime import date, timedelta
from urllib.parse import urlsplit

from app.matching import (
    blob,
    brand,
    dedupe_titles,
    distinctive_words,
    has_word,
    legal_name_in,
    mentions_project,
    normalize,
    project_pattern,
)
from app.models import CheckKey, Finding, Project, Reliability
from app.sources.base import FoundFinding, Progress, SourceContext, SourceEvent
from app.sources.findings import build_finding, parse_day
from app.tinyfish import SearchHit, WebError

SEARCH_PURPOSE = "Find news about delays or insolvency affecting a housing project"
COURT_PURPOSE = "Find a Supreme Court order about the NBCC completing stalled projects"
FETCH_PURPOSE = "Read a Supreme Court order to see which projects it names"
MAX_STORIES = 3
TOPIC = re.compile(r"delay|stalled|nclt|nclat|nbcc|insolven|possession|homebuyer", re.IGNORECASE)
URL_DATE = re.compile(r"\d{2}-[A-Za-z]{3}-\d{4}")
AGO = re.compile(r"(?P<n>\d+)\s+(?P<unit>day|week|month|year)s?\s+ago", re.IGNORECASE)
DAYS_PER_UNIT = {"day": 1, "week": 7, "month": 30, "year": 365}
COURT_HOST = "sci.gov.in"
COURT_REPORT_HOSTS = ("livelaw.in", "barandbench.com", "scconline.com", "indiankanoon.org")


class NewsSource:
    name = "news"
    checks: tuple[CheckKey, ...] = ()

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        project = ctx.project
        if not project.name:
            yield Progress("The project name is not known, so news was not searched")
            return

        yield Progress("Searching news for delay coverage")
        hits = await ctx.web.search(news_query(project), purpose=SEARCH_PURPOSE, domain_type="news")
        for finding in story_findings(hits, project, ctx):
            yield FoundFinding(finding)

        yield Progress("Checking whether the Supreme Court's NBCC order names this project")
        order = await self._court_order(ctx)
        if order:
            yield FoundFinding(order)

    async def _court_order(self, ctx: SourceContext) -> Finding | None:
        project = ctx.project
        promoter = project.promoter or ""
        query = f"Supreme Court NBCC {promoter} stalled projects order"
        hits = await ctx.web.search(query, purpose=COURT_PURPOSE)
        pattern = project_pattern(project.name, project.promoter)
        for hit in hits:
            if is_court_order(hit.url):
                try:
                    page = await ctx.web.fetch_text(hit.url, purpose=FETCH_PURPOSE)
                except WebError:
                    continue
                if legal_name_in(promoter, normalize(page.text)) and mentions_project(
                    pattern, page.text
                ):
                    return court_finding(hit, ctx, "primary")
            elif is_court_report(hit.url) and reports_nbcc_order(hit, pattern):
                return court_finding(hit, ctx, "secondary")
        return None


def news_query(project: Project) -> str:
    """Brand and project words without the phase or numeral: long exact names find nothing."""
    words = [w for w in distinctive_words(project.name, project.promoter) if not w.isdigit()]
    return f"{brand(project.promoter)} {' '.join(words)} delay OR NCLT OR NBCC".replace("  ", " ")


def published_on(text: str | None, today: date) -> tuple[date | None, str]:
    """A story's date and how to say it: news search often reports only '4 weeks ago'."""
    exact = parse_day(text)
    if exact:
        return exact, ""
    found = AGO.match((text or "").strip())
    if not found:
        return None, ""
    days = int(found.group("n")) * DAYS_PER_UNIT[found.group("unit")]
    return today - timedelta(days=days), f" (published about {text.strip()})"  # type: ignore[union-attr]


def story_findings(hits: list[SearchHit], project: Project, ctx: SourceContext) -> list[Finding]:
    pattern = project_pattern(project.name, project.promoter)
    word = brand(project.promoter)
    findings = []
    for hit in dedupe_titles(hits):
        text = f"{hit.title} {hit.snippet}"
        names_project = mentions_project(pattern, text)
        names_promoter = has_word(word, text)
        if not (names_project or names_promoter) or not TOPIC.search(text):
            continue
        about = "this project" if names_project else "the promoter"
        published, ago = published_on(hit.date, ctx.today)
        findings.append(
            build_finding(
                source="news",
                reliability="secondary",
                kind="news_story",
                area="news",
                title=f"News on delays, about {about}: {hit.title}{ago}",
                verdict="review",
                url=hit.url,
                today=ctx.today,
                now=ctx.now,
                occurred_on=published,
            )
        )
        if len(findings) == MAX_STORIES:
            break
    return findings


def court_finding(hit: SearchHit, ctx: SourceContext, reliability: Reliability) -> Finding:
    found = URL_DATE.search(hit.url)
    day = parse_day(hit.date) or (parse_day(found.group(0)) if found else None)
    when = f" of {day.strftime('%d %b %Y')}" if day else ""
    return build_finding(
        source="news",
        reliability=reliability,
        kind="court_order",
        area="legal",
        title=f"Supreme Court order{when} names this project among the stalled "
        f"{ctx.project.promoter} projects the NBCC is to complete",
        verdict="context",
        url=hit.url,
        today=ctx.today,
        now=ctx.now,
        occurred_on=day,
    )


def reports_nbcc_order(hit: SearchHit, pattern: re.Pattern[str] | None) -> bool:
    text = blob(hit)
    return "supreme court" in text and "nbcc" in text and mentions_project(pattern, text)


def is_court_order(url: str) -> bool:
    host = urlsplit(url).hostname or ""
    return host == COURT_HOST or host.endswith("." + COURT_HOST)


def is_court_report(url: str) -> bool:
    host = (urlsplit(url).hostname or "").removeprefix("www.")
    return host in COURT_REPORT_HOSTS
