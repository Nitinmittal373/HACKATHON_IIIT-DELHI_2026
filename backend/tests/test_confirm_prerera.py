"""Confirming open-web numbers on the portal, and projects that say RERA does not apply.

Search answers are the recordings of 27 Oct 2026 (tests/fixtures/openweb_famous.json).
"""

import asyncio

from app.models import Project
from app.states.confirm import MAX_CONFIRMATIONS, confirm_on_portals
from app.states.openweb import open_web_hits
from app.states.prerera import pre_rera_notes
from app.states.resolver import resolve_any
from app.tinyfish import SearchHit, WebError
from tests.fakes import FakeWebClient, load_recording, search_key

MH_A = "P51900008345"
PORTAL = "maharera.maharashtra.gov.in"


def listing(rera_id: str = MH_A) -> Project:
    return Project(
        state="MH",
        rera_id=rera_id,
        name="Lodha World Towers",
        details_url="https://maharera.maharashtra.gov.in/projects-search-result",
        status="listings_only",
        sources=["lodhagroup.com", "housing.com"],
    )


def portal_hit(rera_id: str = MH_A) -> SearchHit:
    return SearchHit(
        title="Projects search result",
        url=f"https://{PORTAL}/projects-search-result?certificate_no={rera_id}",
        snippet=f"{rera_id}. LODHA WORLD TOWERS. LODHA DEVELOPERS LIMITED. MUMBAI.",
    )


def web_with_portal(rera_id: str = MH_A) -> FakeWebClient:
    key = search_key(f"{rera_id} MahaRERA project", PORTAL)
    return FakeWebClient(searches={key: [portal_hit(rera_id)]})


def test_a_number_the_portal_prints_becomes_confirmed() -> None:
    [project] = asyncio.run(confirm_on_portals([listing()], web_with_portal()))
    assert project.status == "confirmed"
    assert project.sources[0] == PORTAL
    assert "lodhagroup.com" in project.sources
    assert project.promoter == "LODHA DEVELOPERS LIMITED"


def test_a_number_the_portal_does_not_print_stays_listings_only() -> None:
    [project] = asyncio.run(confirm_on_portals([listing()], FakeWebClient()))
    assert project.status == "listings_only"


def test_an_unreachable_portal_keeps_the_number() -> None:
    web = FakeWebClient(search_error=WebError("Search failed: TinyFish did not answer in time"))
    [project] = asyncio.run(confirm_on_portals([listing()], web))
    assert project.status == "listings_only"


def test_only_the_first_few_numbers_are_confirmed() -> None:
    web = FakeWebClient()
    many = [listing(f"P5190000{n:04d}") for n in range(MAX_CONFIRMATIONS + 3)]
    asyncio.run(confirm_on_portals(many, web))
    assert len(web.calls) == MAX_CONFIRMATIONS


def recorded_notes(query: str):
    web = FakeWebClient().replay(load_recording("openweb_famous.json"))
    hits = asyncio.run(open_web_hits(query, web))
    return pre_rera_notes(hits, query)


def test_dlf_camellias_is_a_pre_rera_project_with_the_pages_own_words() -> None:
    [note] = recorded_notes("DLF The Camellias")
    assert "does not apply to RERA" in note.statement
    assert note.source_url.startswith("https://www.luxuryresidences.in/")
    assert "Camellias" in note.name


def test_a_registered_project_has_no_pre_rera_note() -> None:
    assert recorded_notes("Prestige Lakeside Habitat") == []


def test_the_resolver_returns_the_note_and_no_invented_number() -> None:
    web = FakeWebClient().replay(load_recording("openweb_famous.json"))
    resolved = asyncio.run(resolve_any("DLF The Camellias", web))
    assert resolved.candidates == []
    assert len(resolved.pre_rera) == 1


def test_the_resolver_confirms_lodha_numbers_on_the_portal() -> None:
    web = FakeWebClient().replay(load_recording("openweb_famous.json"))
    web.searches[search_key(f"{MH_A} MahaRERA project", PORTAL)] = [portal_hit()]
    resolved = asyncio.run(resolve_any("Lodha World Towers", web))
    status = {p.rera_id: p.status for p in resolved.candidates}
    assert status[MH_A] == "confirmed"
    assert status["P51900008962"] == "listings_only"
    assert resolved.candidates[0].rera_id == MH_A  # confirmed first
