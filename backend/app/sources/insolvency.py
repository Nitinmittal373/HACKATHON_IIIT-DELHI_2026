"""Insolvency: has the promoter been admitted to insolvency, and for which projects?

Search finds a page about the case (an order or a report). An agent reads
it and returns the facts; Python then decides what they mean for THIS project:

- the whole company, or this project  -> 100 points and a hard stop
- another project of the promoter     -> 60 points, marked for review
- admitted but scope not stated       -> shown for review, 0 points

The admission and its scope are two findings, and only the scope is scored,
so the same case is never counted twice.
"""

import re
from typing import Any
from urllib.parse import urlsplit

from app.matching import blob, legal_name_in, mentions_project, project_pattern
from app.models import CheckKey, Finding, InsolvencyScope, Project, Reliability, Verdict
from app.sources.agent import AgentSource, AgentTask
from app.sources.base import SourceContext
from app.sources.findings import build_finding, parse_day
from app.tinyfish import SearchHit

SEARCH_PURPOSE = "Find an order or report on a builder's insolvency case"
OFFICIAL_HOSTS = ("nclt.gov.in", "nclat.nic.in", "ibbi.gov.in", "sci.gov.in")
TOPIC = re.compile(r"insolvency|cirp|nclt|nclat", re.IGNORECASE)

GOAL = (
    "This page reports on the insolvency case of {promoter} before the NCLT or NCLAT. Read it "
    "and answer from the page only. admitted: true if the page says the NCLT admitted an "
    "insolvency application against {promoter}. admitted_on: the date of that admission. "
    "covers_whole_company: true only if the page says the whole company is under the "
    "insolvency process and does not say it was limited to particular projects. "
    "projects_named: the names of the projects the insolvency process is limited to or "
    "concerns, exactly as written (empty if none are named). order_url: the address of an "
    "NCLT, NCLAT or Supreme Court order linked on the page, if any. Return null for anything "
    "the page does not state."
)
OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "admitted": {"type": ["boolean", "null"]},
        "admitted_on": {"type": ["string", "null"]},
        "covers_whole_company": {"type": ["boolean", "null"]},
        "projects_named": {"type": "array", "items": {"type": "string"}},
        "order_url": {"type": ["string", "null"]},
    },
    "required": ["admitted", "admitted_on", "covers_whole_company", "projects_named", "order_url"],
}


class InsolvencySource(AgentSource):
    name = "insolvency"
    checks: tuple[CheckKey, ...] = ("insolvency",)
    no_task_message = "No page about this promoter's insolvency case was found"

    async def task(self, ctx: SourceContext) -> AgentTask | None:
        promoter = ctx.project.promoter
        if not promoter:
            return None
        hits = await ctx.web.search(f"{promoter} NCLT insolvency admitted", purpose=SEARCH_PURPOSE)
        page = pick_case_page(hits, promoter)
        if page is None:
            return None
        return AgentTask(
            url=page.url,
            goal=GOAL.format(promoter=promoter),
            output_schema=OUTPUT_SCHEMA,
            max_steps=20,
        )

    def to_findings(
        self, result: dict[str, Any], ctx: SourceContext, task: AgentTask
    ) -> list[Finding]:
        return to_findings(result, ctx.project, task.url, ctx)

    def checks_read(self, result: dict[str, Any], ctx: SourceContext) -> tuple[CheckKey, ...]:
        # A page that does not say "admitted" proves nothing about the absence of a case.
        return self.checks if result.get("admitted") is True else ()


def pick_case_page(hits: list[SearchHit], promoter: str) -> SearchHit | None:
    """The best page about the promoter's case that an agent can open.

    Official sites come first. PDFs are skipped: an agent browsing a PDF viewer returns little.
    """
    usable = [
        hit
        for hit in hits
        if not is_pdf(hit.url) and legal_name_in(promoter, blob(hit)) and TOPIC.search(blob(hit))
    ]
    return min(usable, key=lambda hit: not is_official(hit.url), default=None)


def is_pdf(url: str) -> bool:
    return ".pdf" in url.lower() or "gen_pdf" in url.lower()


def is_official(url: str) -> bool:
    host = urlsplit(url).hostname or ""
    return any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS)


def decide_scope(result: dict[str, Any], project: Project) -> InsolvencyScope | None:
    """What the admitted case covers, from the facts the agent read; None when not stated."""
    named = [name for name in result.get("projects_named") or [] if name]
    if named:
        pattern = project_pattern(project.name, project.promoter)
        if pattern is None:
            return None
        hit = any(mentions_project(pattern, name) for name in named)
        return "this_project" if hit else "other_project"
    return "company" if result.get("covers_whole_company") is True else None


def to_findings(
    result: dict[str, Any], project: Project, url: str, ctx: SourceContext
) -> list[Finding]:
    if result.get("admitted") is not True:
        return []
    reliability: Reliability = "primary" if is_official(url) else "secondary"
    order_url = result.get("order_url") or ""
    # An address the agent read off the page is only trusted on an official court site.
    proof_url = order_url if order_url.startswith("https://") and is_official(order_url) else url
    admitted_on = parse_day(result.get("admitted_on"))

    def make(kind: str, title: str, verdict: Verdict, **facts: object) -> Finding:
        return build_finding(
            source="insolvency",
            reliability=reliability,
            kind=kind,
            area="financial",
            title=title,
            verdict=verdict,
            url=proof_url,
            today=ctx.today,
            now=ctx.now,
            **facts,
        )

    when = f" on {admitted_on.strftime('%d %b %Y')}" if admitted_on else ""
    findings = [
        make(
            "insolvency_admitted",
            f"Insolvency application against {project.promoter} was admitted{when}",
            "review",
            occurred_on=admitted_on,
        )
    ]
    scope = decide_scope(result, project)
    named = ", ".join(n for n in result.get("projects_named") or [] if n)
    if scope == "other_project":
        title = f"Insolvency is limited to another project ({named}); this project is not named"
        findings.append(make("insolvency_scope", title, "review", scope=scope))
    elif scope == "this_project":
        title = f"Insolvency covers this project (named: {named})"
        findings.append(make("insolvency_scope", title, "red_flag", scope=scope))
    elif scope == "company":
        title = "Insolvency covers the whole company"
        findings.append(make("insolvency_scope", title, "red_flag", scope=scope))
    return findings
