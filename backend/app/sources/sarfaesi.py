"""SARFAESI auction notices: a lender selling the builder's assets to recover a loan.

Search only, no browser. A notice counts when its page names the promoter's exact legal name
and says SARFAESI or auction. A notice on an official or lender site is scored; a news report
of one is shown for review with no points, because news cannot prove the notice itself.
"""

import re
from collections.abc import AsyncIterator
from urllib.parse import urlsplit

from app.matching import blob, legal_name_in
from app.models import CheckKey, Finding
from app.sources.base import FoundFinding, Progress, SourceContext, SourceError, SourceEvent
from app.sources.findings import build_finding, parse_day
from app.tinyfish import SearchHit, WebError

SEARCH_PURPOSE = "Find SARFAESI auction notices naming a builder company"
NOTICE_WORDS = re.compile(r"sarfaesi|auction|possession notice|demand notice", re.IGNORECASE)
MAX_NOTICES = 3
# Lender and government sites whose notice pages are the notice itself.
OFFICIAL_SUFFIXES = (".gov.in", ".nic.in", ".bank.in")
LENDER_HOSTS = (
    "ibapi.in",
    "bankeauctions.com",
    "sbi.co.in",
    "pnbindia.in",
    "unionbankofindia.co.in",
    "bankofbaroda.in",
    "canarabank.com",
    "idbibank.in",
    "hdfcbank.com",
    "icicibank.com",
)


class SarfaesiSource:
    name = "sarfaesi"
    checks: tuple[CheckKey, ...] = ()

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        promoter = ctx.project.promoter
        if not promoter:
            raise SourceError(
                "The promoter's name is not known, so auction notices were not searched"
            )
        yield Progress(f"Searching for SARFAESI auction notices naming {promoter}")
        try:
            hits = await ctx.web.search(f"{promoter} SARFAESI auction", purpose=SEARCH_PURPOSE)
        except WebError as error:
            raise SourceError(str(error)) from None
        for finding in notice_findings(hits, promoter, ctx):
            yield FoundFinding(finding)


def is_official(url: str) -> bool:
    host = (urlsplit(url).hostname or "").removeprefix("www.")
    return host.endswith(OFFICIAL_SUFFIXES) or any(
        host == h or host.endswith("." + h) for h in LENDER_HOSTS
    )


def notice_findings(hits: list[SearchHit], promoter: str, ctx: SourceContext) -> list[Finding]:
    findings = []
    for hit in hits:
        if not (
            legal_name_in(promoter, blob(hit)) and NOTICE_WORDS.search(f"{hit.title} {hit.snippet}")
        ):
            continue
        official = is_official(hit.url)
        findings.append(
            build_finding(
                source="sarfaesi",
                reliability="primary" if official else "secondary",
                kind="sarfaesi_notice" if official else "sarfaesi_report",
                area="financial",
                title=(
                    f"A lender notice names {promoter}: {hit.title}"
                    if official
                    else f"A web page reports an auction notice naming {promoter}: {hit.title}"
                ),
                verdict="fail" if official else "review",
                url=hit.url,
                today=ctx.today,
                now=ctx.now,
                occurred_on=parse_day(hit.date),
                snippet=hit.snippet[:300] or None,
            )
        )
        if len(findings) == MAX_NOTICES:
            break
    return findings
