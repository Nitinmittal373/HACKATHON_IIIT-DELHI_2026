"""The open-web search: numbers found in unrestricted Search results and the vote on them.

openweb_famous.json is the live Search answer of 27 Oct 2026 (scripts/capture_openweb.py).
"""

import asyncio

import pytest

from app.states.openweb import (
    CACHE,
    SearchCache,
    brand_tokens,
    candidates_from,
    numbers_in,
    prepare,
    search_open_web,
)
from app.tinyfish import SearchHit
from tests.fakes import FakeWebClient, load_recording

MH_A = "P51900008345"
MH_B = "P51900008962"


@pytest.fixture(autouse=True)
def fresh_cache() -> None:
    CACHE.clear()


def hit(url: str, text: str, title: str = "Page") -> SearchHit:
    return SearchHit(title=title, url=url, snippet=text)


def famous(query: str) -> list:
    web = FakeWebClient().replay(load_recording("openweb_famous.json"))
    return asyncio.run(search_open_web(query, web))


def test_lodha_world_towers_gives_its_two_maharera_numbers() -> None:
    found = famous("Lodha World Towers")
    assert {p.rera_id for p in found} == {MH_A, MH_B}
    assert {p.state for p in found} == {"MH"}
    assert all(p.status == "listings_only" for p in found)
    assert all("lodhagroup.com" in p.sources for p in found)


def test_prestige_is_confirmed_by_the_karnataka_portal() -> None:
    found = famous("Prestige Lakeside Habitat")
    assert [p.rera_id for p in found] == ["PRM/KA/RERA/1251/446/PR/170915/000176"]
    assert found[0].status == "confirmed"
    assert found[0].sources[0] == "rera.karnataka.gov.in"
    assert found[0].name == "Prestige Lakeside Habitat"


def test_a_number_printed_by_one_other_site_is_not_kept() -> None:
    # The Quora answer prints a Prestige number of a different project.
    ids = [p.rera_id for p in famous("Prestige Lakeside Habitat")]
    assert "PRM/KA/RERA/1251/310/PR/170913/000114" not in ids


def test_a_phrase_that_only_looks_like_a_number_is_rejected() -> None:
    # "112 of 2021" is on a Gurgaon sales page and fits Andhra Pradesh's plain format.
    assert famous("M3M Golf Estate") == []


def test_a_number_beside_another_project_is_not_this_projects() -> None:
    hits = [
        hit("https://a.example/1", f"Sunrise Heights RERA {MH_A}. Moon Park RERA {MH_B}."),
        hit("https://b.example/2", f"Sunrise Heights RERA {MH_A}."),
        hit("https://c.example/3", f"Moon Park RERA {MH_B}."),
    ]
    assert [p.rera_id for p in candidates_from(hits, "Sunrise Heights")] == [MH_A]


def test_one_listing_alone_is_not_enough() -> None:
    hits = [hit("https://listing.example/x", f"Sunrise Heights RERA {MH_A}")]
    assert candidates_from(hits, "Sunrise Heights") == []


def test_two_domains_that_name_the_project_are_enough() -> None:
    hits = [
        hit("https://a.example/x", f"Sunrise Heights RERA {MH_A}"),
        hit("https://b.example/y", f"Sunrise Heights RERA {MH_A}"),
    ]
    [found] = candidates_from(hits, "Sunrise Heights")
    assert found.rera_id == MH_A
    assert found.status == "listings_only"


def test_the_builders_own_site_and_one_listing_score_enough() -> None:
    hits = [hit("https://www.sunrisebuilders.com/x", f"Sunrise Heights {MH_A}")]
    assert candidates_from(hits, "Sunrise Heights") == []  # builder alone: 2 points, one domain
    hits.append(hit("https://listing.example/y", f"Sunrise Heights {MH_A}"))
    assert [p.rera_id for p in candidates_from(hits, "Sunrise Heights")] == [MH_A]


def test_a_portal_page_alone_keeps_a_number_that_names_the_project() -> None:
    hits = [hit("https://maharera.maharashtra.gov.in/p", f"Sunrise Heights {MH_A}")]
    [found] = candidates_from(hits, "Sunrise Heights")
    assert found.status == "confirmed"


def test_a_portal_page_that_does_not_name_the_project_is_not_kept() -> None:
    hits = [hit("https://maharera.maharashtra.gov.in/p", f"Moon Park {MH_A}")]
    assert candidates_from(hits, "Sunrise Heights") == []


def test_spaces_and_ack_noise_do_not_hide_a_number() -> None:
    text = prepare("Sunrise Heights RERA ACK No P 51900 008345 and RERA ACK123")
    assert [n[1] for n in numbers_in(text)] == [MH_A]


def test_brand_tokens_are_the_first_words() -> None:
    assert brand_tokens("Lodha World Towers") == {"lodha", "lodhaworld"}
    assert brand_tokens("My Home Bhooja") == {"myhome"}


def test_search_answers_are_kept_for_a_day() -> None:
    now = [0.0]
    cache = SearchCache(clock=lambda: now[0])
    web = FakeWebClient(searches={"Q RERA": [hit("https://a.example", "x")]})
    asyncio.run(search_open_web("Q", web, cache))
    asyncio.run(search_open_web("Q", web, cache))
    assert len(web.calls) == 2  # two templates, searched once
    now[0] = 24 * 3600 + 1
    asyncio.run(search_open_web("Q", web, cache))
    assert len(web.calls) == 4


def test_resolve_any_adds_open_web_numbers_to_the_portal_ones() -> None:
    from app.states.resolver import resolve_any

    web = FakeWebClient().replay(load_recording("openweb_famous.json"))
    resolved = asyncio.run(resolve_any("Lodha World Towers", web))
    assert {p.rera_id for p in resolved.candidates} >= {MH_A, MH_B}
    assert all(p.status for p in resolved.candidates if p.rera_id in {MH_A, MH_B})


def test_a_typed_number_keeps_only_that_number() -> None:
    from app.states.resolver import resolve_any

    web = FakeWebClient(
        searches={
            f"{MH_A} RERA": [
                hit("https://a.example/1", f"Lodha World Towers {MH_A} {MH_B}"),
                hit("https://b.example/2", f"Lodha World Towers {MH_A}"),
            ]
        }
    )
    resolved = asyncio.run(resolve_any(MH_A, web))
    assert [p.rera_id for p in resolved.candidates] == [MH_A]
