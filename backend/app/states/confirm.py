"""Check a number the open web found against the state's own portal.

The exact number is searched on the state's RERA domain (the adapter's own resolve). A page that
prints it makes the candidate "confirmed" and brings the portal's page and facts; when nothing
there prints it, the candidate stays "listings_only" and says so.
"""

import asyncio

from app.models import Project
from app.states.openweb import domain_of
from app.states.registry import BY_CODE
from app.states.text import squash
from app.tinyfish import WebClient, WebError

# TinyFish allows 30 searches a minute; confirming more than this would starve the buyer's next try.
MAX_CONFIRMATIONS = 4
# Numbers no portal page has printed yet: from listing sites, a buyer's file or a public order.
UNCONFIRMED = ("listings_only", "from_document", "from_order")


async def confirm_on_portals(candidates: list[Project], web: WebClient) -> list[Project]:
    """The candidates, with each listings-only number checked on its portal (best first)."""
    pending = [p for p in candidates if p.status in UNCONFIRMED][:MAX_CONFIRMATIONS]
    answers = await asyncio.gather(*(confirmed(p, web) for p in pending))
    replaced = {squash(p.rera_id): answer for p, answer in zip(pending, answers, strict=True)}
    updated = [replaced.get(squash(p.rera_id)) or p for p in candidates]
    return sorted(updated, key=lambda p: p.status != "confirmed")


async def confirmed(project: Project, web: WebClient) -> Project | None:
    try:
        found = await BY_CODE[project.state].resolve(project.rera_id, web)
    except WebError:
        return None  # An unreachable portal leaves the number as listings-only, not removed.
    portal = next((p for p in found if squash(p.rera_id) == squash(project.rera_id)), None)
    if portal is None:
        return None
    gaps = {k: v for k, v in project.model_dump().items() if getattr(portal, k) is None}
    sources = list(dict.fromkeys([domain_of(portal.details_url), *project.sources]))
    return portal.model_copy(update={**gaps, **{"status": "confirmed", "sources": sources}})
