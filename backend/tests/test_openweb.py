"""The open-web search: numbers found in unrestricted Search results and the vote on them.

openweb_famous.json is the live Search answer of 27 Oct 2026 (scripts/capture_openweb.py).
"""

import asyncio

import pytest

from app.states.openweb import (
    CACHE,
    SEARCH_TEMPLATES,
    SearchCache,
    brand_tokens,
    candidates_from,
    numbers_in,
    prepare,
    search_open_web,
)
from app.tinyfish import SearchHit
from tests.fakes import FakeWebClient, load_recording

A = "UPRERAPRJ1001"
B = "UPRERAPRJ1002"
PORTAL = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=1001"


@pytest.fixture(autouse=True)
def fresh_cache() -> None:
    CACHE.clear()


def hit(url: str, text: str, title: str = "Page") -> SearchHit:
    return SearchHit(title=title, url=url, snippet=text)


def famous(query: str) -> list:
    web = FakeWebClient().replay(load_recording("openweb_famous.json"))
    return asyncio.run(search_open_web(query, web))


def test_mahagun_mywoods_is_confirmed_by_its_up_rera_page() -> None:
    [found] = famous("Mahagun Mywoods")
    assert found.rera_id == "UPRERAPRJ3330"
    assert found.status == "confirmed"
    assert found.sources[0] == "up-rera.in"
    assert found.name == "Mahagun Mywoods"


def test_a_number_printed_by_a_listing_alone_is_kept_only_when_two_domains_print_it() -> None:
    found = {p.rera_id: p for p in famous("ATS Pristine")}
    assert found["UPRERAPRJ2875"].status == "listings_only"
    assert found["UPRERAPRJ2875"].sources[:2] == ["ats-greens.co.in", "atsgreens.com"]


def test_a_number_beside_another_project_is_not_this_projects_in_a_listing_of_many() -> None:
    ids = [p.rera_id for p in famous("Godrej Woods Noida")]
    assert "UPRERAPRJ704730" in ids and "UPRERAPRJ773536" in ids


def test_a_number_beside_another_project_is_not_this_projects() -> None:
    hits = [
        hit("https://a.example/1", f"Sunrise Heights RERA {A}. Moon Park RERA {B}."),
        hit("https://b.example/2", f"Sunrise Heights RERA {A}."),
        hit("https://c.example/3", f"Moon Park RERA {B}."),
    ]
    assert [p.rera_id for p in candidates_from(hits, "Sunrise Heights")] == [A]


def test_one_listing_alone_is_not_enough() -> None:
    hits = [hit("https://listing.example/x", f"Sunrise Heights RERA {A}")]
    assert candidates_from(hits, "Sunrise Heights") == []


def test_two_domains_that_name_the_project_are_enough() -> None:
    hits = [
        hit("https://a.example/x", f"Sunrise Heights RERA {A}"),
        hit("https://b.example/y", f"Sunrise Heights RERA {A}"),
    ]
    [found] = candidates_from(hits, "Sunrise Heights")
    assert found.rera_id == A
    assert found.status == "listings_only"


def test_the_builders_own_site_and_one_listing_score_enough() -> None:
    hits = [hit("https://www.sunrisebuilders.com/x", f"Sunrise Heights {A}")]
    assert candidates_from(hits, "Sunrise Heights") == []  # builder alone: 2 points, one domain
    hits.append(hit("https://listing.example/y", f"Sunrise Heights {A}"))
    assert [p.rera_id for p in candidates_from(hits, "Sunrise Heights")] == [A]


def test_a_portal_page_alone_keeps_a_number_that_names_the_project() -> None:
    hits = [hit(PORTAL, f"Sunrise Heights {A}")]
    [found] = candidates_from(hits, "Sunrise Heights")
    assert found.status == "confirmed"


def test_a_portal_page_that_does_not_name_the_project_is_not_kept() -> None:
    hits = [hit(PORTAL, f"Moon Park {A}")]
    assert candidates_from(hits, "Sunrise Heights") == []


def test_ack_noise_does_not_hide_a_number_and_other_states_numbers_are_ignored() -> None:
    text = prepare("Sunrise Heights RERA ACK No UPRERAPRJ1001 and P51900008345 RERA ACK123")
    assert [n[0] for n in numbers_in(text)] == [A]


def test_brand_tokens_are_the_first_words() -> None:
    assert brand_tokens("Godrej Woods Noida") == {"godrej", "godrejwoods"}
    assert brand_tokens("My Home Bhooja") == {"myhome"}


def test_search_answers_are_kept_for_a_day() -> None:
    now = [0.0]
    cache = SearchCache(clock=lambda: now[0])
    web = FakeWebClient(searches={"Q RERA": [hit("https://a.example", "x")]})
    asyncio.run(search_open_web("Q", web, cache))
    asyncio.run(search_open_web("Q", web, cache))
    assert len(web.calls) == len(SEARCH_TEMPLATES)  # each wording searched once
    now[0] = 24 * 3600 + 1
    asyncio.run(search_open_web("Q", web, cache))
    assert len(web.calls) == 2 * len(SEARCH_TEMPLATES)


def test_resolve_any_adds_open_web_numbers_to_the_portal_ones() -> None:
    from app.states.resolver import resolve_any

    web = FakeWebClient().replay(load_recording("openweb_famous.json"))
    resolved = asyncio.run(resolve_any("Mahagun Mywoods", web))
    assert "UPRERAPRJ3330" in {p.rera_id for p in resolved.candidates}


def test_a_typed_number_keeps_only_that_number() -> None:
    from app.states.resolver import resolve_any

    web = FakeWebClient(
        searches={
            f"{A} RERA": [
                hit("https://a.example/1", f"Sunrise Heights {A} {B}"),
                hit("https://b.example/2", f"Sunrise Heights {A}"),
            ]
        }
    )
    resolved = asyncio.run(resolve_any(A, web))
    assert [p.rera_id for p in resolved.candidates] == [A]


def test_a_word_counts_whole_not_as_the_start_of_another_project() -> None:
    from app.states.openweb import share_of

    words = {"godrej", "woods"}
    assert share_of(words, "godrej woods phase 1") == 1.0
    assert share_of(words, "godrej woodscapes, bengaluru") == 0.5


def test_names_spelled_apart_or_together_match() -> None:
    from app.states.openweb import share_of

    assert share_of({"mahagun", "mywoods"}, "mahagun my wood, noida") == 1.0
    assert share_of({"m3m", "golf", "estate"}, "the rera number for m3m golfestate") == 1.0
    assert share_of({"godrej", "woods", "noida"}, "godrej woods, bengaluru") < 0.75


def test_confirmed_numbers_come_before_listing_only_ones() -> None:
    from app.models import Project
    from app.states.resolver import ordered

    def godrej(rera_id: str, status: str) -> Project:
        return Project(
            rera_id=rera_id, name="Godrej Woods", details_url="x", status=status
        )  # type: ignore[arg-type]

    listed = godrej("UPRERAPRJ145318", "listings_only")
    confirmed = godrej("UPRERAPRJ773536", "confirmed")
    assert [p.rera_id for p in ordered([listed, confirmed], "Godrej Woods Noida")] == [
        "UPRERAPRJ773536",
        "UPRERAPRJ145318",
    ]
