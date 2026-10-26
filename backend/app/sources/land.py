"""Land authority dues: is the promoter on a published list of unpaid dues?

Which authority applies depends on where the project is, so the project's
district picks the lists to read. These lists are usually PDFs, which Fetch
turns into text and Python searches for the promoter's exact legal name.

- found, with an amount on the same line  -> Financial area penalty
- list read, promoter not in it           -> shown as "not found", 0 points
- list missing or unreadable              -> the check stays unread

Absence from a list never adds points, and it only counts as a read check
when every list for the district was actually read.
"""

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from urllib.parse import urlsplit

from app.matching import blob, legal_name_in, normalize
from app.models import CheckKey, Verdict
from app.sources.base import (
    ChecksRead,
    FoundFinding,
    Progress,
    SourceContext,
    SourceEvent,
)
from app.sources.findings import build_finding
from app.tinyfish import SearchHit, WebError

SEARCH_PURPOSE = "Find the land authority's published list of builders with unpaid dues"
FETCH_PURPOSE = "Read a land authority's published list of builders with unpaid dues"
MAX_TRIES_PER_AUTHORITY = 3
LIST_WORDS = re.compile(r"defaulter|dues|outstanding", re.IGNORECASE)
# A row in a dues list carries an amount; a scheme brochure that names a builder does not.
AMOUNT = re.compile(r"\d[\d,.]{3,}|crore|lakh", re.IGNORECASE)


@dataclass(frozen=True)
class Authority:
    name: str
    hosts: tuple[str, ...]


NOIDA = Authority("Noida Authority", ("noidaauthorityonline.in", "noidaauthority.in"))
GREATER_NOIDA = Authority(
    "Greater Noida Industrial Development Authority",
    ("greaternoidaauthority.in", "investgnida.in", "gnida.in"),
)
YEIDA = Authority(
    "Yamuna Expressway Industrial Development Authority", ("yamunaexpresswayauthority.com",)
)

# One district can fall under several authorities; the project record does not say which.
AUTHORITIES_BY_DISTRICT: dict[str, tuple[Authority, ...]] = {
    "gautam buddha nagar": (NOIDA, GREATER_NOIDA, YEIDA),
    "mathura": (YEIDA,),
    "aligarh": (YEIDA,),
    "agra": (YEIDA,),
    "hathras": (YEIDA,),
}


class LandSource:
    name = "land"
    checks: tuple[CheckKey, ...] = ("land_dues",)

    async def run(self, ctx: SourceContext) -> AsyncIterator[SourceEvent]:
        if ctx.project.state != "UP":
            # The lists are Noida, Greater Noida and Yamuna Expressway dues: UP only.
            yield Progress("Land dues lists exist for Uttar Pradesh only; not read here")
            return
        promoter, district = ctx.project.promoter, normalize(ctx.project.district)
        authorities = AUTHORITIES_BY_DISTRICT.get(district)
        if not promoter or not authorities:
            yield Progress("No land authority list is connected for this district")
            return

        lists_read = 0
        for authority in authorities:
            yield Progress(f"Looking for the {authority.name} dues list")
            found = await self._read_list(authority, ctx)
            if found is None:
                yield Progress(f"The {authority.name} list could not be read")
                continue
            lists_read += 1
            url, text = found
            listed = promoter_listed(promoter, text)
            title = (
                f"{promoter} is on the {authority.name} list of unpaid dues"
                if listed
                else f"{promoter} was not found in the {authority.name} list read today"
            )
            verdict: Verdict = "fail" if listed else "not_found"
            yield FoundFinding(
                build_finding(
                    source="land",
                    reliability="primary",
                    kind="land_dues" if listed else "land_dues_check",
                    area="financial",
                    title=title,
                    verdict=verdict,
                    url=url,
                    today=ctx.today,
                    now=ctx.now,
                )
            )
            if listed:
                yield ChecksRead(self.checks)
                return
        if lists_read == len(authorities):
            yield ChecksRead(self.checks)

    async def _read_list(self, authority: Authority, ctx: SourceContext) -> tuple[str, str] | None:
        """The first dues list of this authority that Fetch can read, as (url, text)."""
        query = f"{authority.name} builders dues defaulter list group housing"
        hits = await ctx.web.search(query, purpose=SEARCH_PURPOSE)
        candidates = [hit for hit in hits if on_authority_site(hit, authority)]
        for hit in candidates[:MAX_TRIES_PER_AUTHORITY]:
            if not LIST_WORDS.search(blob(hit)):
                continue
            try:
                page = await ctx.web.fetch_text(hit.url, purpose=FETCH_PURPOSE)
            except WebError:
                continue
            if LIST_WORDS.search(page.text):
                return hit.url, page.text
        return None


def on_authority_site(hit: SearchHit, authority: Authority) -> bool:
    host = (urlsplit(hit.url).hostname or "").removeprefix("www.")
    return any(host == h or host.endswith("." + h) for h in authority.hosts)


def promoter_listed(promoter: str, text: str) -> bool:
    """True when a line of the list names the promoter exactly and carries an amount."""
    return any(
        legal_name_in(promoter, normalize(line)) and AMOUNT.search(line)
        for line in text.splitlines()
    )
