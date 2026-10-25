"""Company registry: is the promoter's legal entity active, or in insolvency itself?

Search finds the company's page on MCA or a mirror of its data (Economic Times, zaubacorp).
Where plain Fetch can read the details table it is parsed in Python, which is free and gives
the same answer every time; otherwise a TinyFish agent reads the page. Either way the page is
kept only if it carries the promoter's exact legal name: "Supertech Limited" is not
"Supertech Realtors Limited", and a wrong-company claim is worse than none.
"""

import re
from typing import Any
from urllib.parse import urlsplit

from app.matching import blob, legal_name_in, normalize
from app.models import CheckKey, Finding, Reliability, Verdict
from app.sources.agent import AgentSource, AgentTask
from app.sources.base import SourceContext
from app.sources.findings import build_finding
from app.tinyfish import SearchHit, WebError

SEARCH_PURPOSE = "Find the public company-registry page of a builder's legal entity"
FETCH_PURPOSE = "Read the public company-registry page of a builder's legal entity"
# Host -> how far the page can be trusted, most readable first. Zaubacorp shows browsers a
# CAPTCHA, so a mirror that does not (Economic Times) is tried before it.
REGISTRY_HOSTS: dict[str, Reliability] = {
    "mca.gov.in": "primary",
    "economictimes.indiatimes.com": "secondary",
    "zaubacorp.com": "secondary",
}
CIN = re.compile(r"[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}")
PAGE_URL = "page_url"  # set when the answer came from a page other than the one searched
IN_INSOLVENCY = re.compile(r"cirp|insolvency|liquidat|resolution process", re.IGNORECASE)

GOAL = (
    "This is the public company page for {promoter}. Read three things exactly as the page "
    "shows them: the company's registered name, its CIN, and its current company status "
    "(for example Active, Strike Off, Under CIRP, Under Liquidation). Do not click links that "
    "ask you to sign in, pay or download anything. Return null for anything the page does "
    "not show."
)
OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "legal_name": {"type": "string", "nullable": True},
        "cin": {"type": "string", "nullable": True},
        "status": {"type": "string", "nullable": True},
    },
    "required": ["legal_name", "cin", "status"],
}


class RegistrySource(AgentSource):
    name = "registry"
    checks: tuple[CheckKey, ...] = ("company_status",)
    no_task_message = "No company page with the promoter's exact legal name was found"

    async def task(self, ctx: SourceContext) -> AgentTask | None:
        promoter = ctx.project.promoter
        if not promoter:
            return None
        query = f"{promoter} company CIN status zaubacorp"
        hits = await ctx.web.search(query, purpose=SEARCH_PURPOSE)
        page = pick_company_page(hits, promoter)
        if page is None:
            return None
        return AgentTask(
            url=page.url,
            goal=GOAL.format(promoter=promoter),
            output_schema=OUTPUT_SCHEMA,
            max_steps=15,
        )

    async def read_directly(self, task: AgentTask, ctx: SourceContext) -> dict[str, Any] | None:
        for url in readable_pages(task.url, ctx.project.promoter):
            try:
                page = await ctx.web.fetch_text(url, purpose=FETCH_PURPOSE)
            except WebError:
                continue
            found = parse_company_table(page.text)
            # Only a page that names exactly this company counts, wherever the address came from.
            if found["status"] and is_this_company(found, ctx.project.promoter):
                return {**found, PAGE_URL: url}
        return None

    def to_findings(
        self, result: dict[str, Any], ctx: SourceContext, task: AgentTask
    ) -> list[Finding]:
        url = result.get(PAGE_URL) or task.url
        return to_findings(result, ctx.project.promoter, url, ctx)

    def checks_read(self, result: dict[str, Any], ctx: SourceContext) -> tuple[CheckKey, ...]:
        usable = is_this_company(result, ctx.project.promoter) and bool(result.get("status"))
        return self.checks if usable else ()


def readable_pages(url: str, promoter: str | None) -> list[str]:
    """The chosen page, then the same company's page on a mirror that does not show a CAPTCHA.

    Zaubacorp addresses end in the CIN, and Economic Times pages are named by company and CIN,
    so the mirror can be worked out. It is only used if it names exactly the same company.
    """
    pages = [url]
    cin = CIN.search(url)
    slug = re.sub(r"[^a-z0-9]+", "-", normalize(promoter)).strip("-")
    if cin and slug and registry_host(url) == "zaubacorp.com":
        pages.insert(0, f"https://economictimes.indiatimes.com/company/{slug}/{cin.group(0)}")
    return pages


def parse_company_table(text: str) -> dict[str, str | None]:
    """Name, CIN and status from a company page's details table (as Fetch turns it into text)."""

    def cell(label: str, value: str) -> str | None:
        found = re.search(rf"\|\s*{label}\s*\|\s*({value})\s*\|", text)
        return found.group(1).strip() if found else None

    heading = re.search(r"^#+\s*(.+?)\s+Details\s*$", text, re.MULTILINE)
    return {
        "legal_name": heading.group(1).strip() if heading else None,
        "cin": cell("CIN", r"[A-Z0-9]{21}"),
        "status": cell("Status", r"[^|]+?"),
    }


def pick_company_page(hits: list[SearchHit], promoter: str) -> SearchHit | None:
    """The most readable registry page whose title, address or text holds the exact legal name."""
    hosts = list(REGISTRY_HOSTS)
    named = [h for h in hits if registry_reliability(h.url) and legal_name_in(promoter, blob(h))]
    return min(named, key=lambda hit: hosts.index(registry_host(hit.url)), default=None)


def registry_host(url: str) -> str:
    return (urlsplit(url).hostname or "").removeprefix("www.")


def registry_reliability(url: str) -> Reliability | None:
    return REGISTRY_HOSTS.get(registry_host(url))


def is_this_company(result: dict[str, Any], promoter: str | None) -> bool:
    return legal_name_in(promoter, normalize(result.get("legal_name")))


def to_findings(
    result: dict[str, Any], promoter: str | None, url: str, ctx: SourceContext
) -> list[Finding]:
    status = (result.get("status") or "").strip()
    if not status or not is_this_company(result, promoter):
        return []
    cin = f" (CIN {result['cin']})" if result.get("cin") else ""
    reliability = registry_reliability(url) or "secondary"

    def make(kind: str, title: str, verdict: Verdict, **facts: object) -> Finding:
        return build_finding(
            source="registry",
            reliability=reliability,
            kind=kind,
            area="financial",
            title=title,
            verdict=verdict,
            url=url,
            today=ctx.today,
            now=ctx.now,
            **facts,
        )

    if IN_INSOLVENCY.search(status):
        title = f"Company status: {status}{cin}. The promoter company itself is in insolvency"
        return [make("insolvency_scope", title, "red_flag", scope="company")]
    verdict: Verdict = "ok" if status.lower() == "active" else "review"
    return [make("company_status", f"Company status: {status}{cin}", verdict)]
