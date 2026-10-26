"""How many well-known projects the portal-only resolver finds, replayed from a recording.

The recording is the live answer of 27 Oct 2026 (scripts/baseline_famous.py). This number is
the starting point that the open-web search has to beat; see docs/baseline-famous.md.
"""

import asyncio

from app.states.resolver import resolve_on_portals
from scripts.famous_projects import FAMOUS
from tests.fakes import FakeWebClient, load_recording

BASELINE_FOUND = {
    "Prestige Lakeside Habitat",
    "Godrej Woods Noida",
    "Sobha Dream Acres",
    "Brigade Utopia",
    "Tata Housing Eureka Park",
    "Mahagun Mywoods",
    "ATS Pristine",
    "Gaur City",
    "Puravankara Purva Atmosphere",
}


def test_portal_only_resolver_finds_nine_of_fifteen() -> None:
    web = FakeWebClient().replay(load_recording("baseline_famous.json"))
    found = set()
    for famous in FAMOUS:
        resolved = asyncio.run(resolve_on_portals(famous.query, web))
        if any(famous.matches(project) for project in resolved.candidates):
            found.add(famous.query)
    assert found == BASELINE_FOUND
