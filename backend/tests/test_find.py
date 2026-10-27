"""Finding projects with no website: by locality and builder, and the outside-UP answers.

The Eureka Park recording is the live Search answer of 27 Oct 2026.
"""

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import OUTSIDE_UP_MESSAGE
from app.states.openweb import SearchCache
from app.states.places import names_place_outside_up, place_in, without_places
from app.states.promoter_search import companies_in, search_promoter
from app.states.resolver import resolve_any
from app.tinyfish import SearchHit
from tests.conftest import make_settings
from tests.fakes import FakeWebClient, load_recording

EUREKA = "find_locality_eureka.json"


def test_a_locality_search_puts_the_closest_name_first() -> None:
    web = FakeWebClient().replay(load_recording(EUREKA))
    resolved = asyncio.run(resolve_any("Eureka Park", web, locality="Sector 150 Noida"))
    assert resolved.candidates[0].rera_id == "UPRERAPRJ5448"
    assert not resolved.outside_up


@pytest.mark.parametrize(
    ("text", "outside"),
    [
        ("Sector 150 Noida", False),
        ("greater noida west", False),
        ("Whitefield, Bengaluru", True),
        ("Gurgaon sector 65", True),
        ("Navi Mumbai", True),
        ("an unknown village", False),
    ],
)
def test_a_city_outside_up_is_recognised(text: str, outside: bool) -> None:
    assert names_place_outside_up(text) is outside


def test_the_longest_place_wins() -> None:
    assert place_in("flats in greater noida") == "greater noida"


def test_places_are_removed_from_a_name_but_never_all_of_it() -> None:
    assert without_places("Godrej Woods Noida") == "Godrej Woods"


def test_a_number_of_another_state_is_answered_without_searching() -> None:
    web = FakeWebClient(search_error=AssertionError("must not search"))  # type: ignore[arg-type]
    for number in ("P51800000937", "PRM/KA/RERA/1251/446/PR/170915/000176"):
        resolved = asyncio.run(resolve_any(number, web))
        assert resolved.outside_up and resolved.candidates == []


def test_the_search_endpoint_says_calmly_that_another_state_is_not_covered(
    tmp_path: Path,
) -> None:
    with TestClient(create_app(make_settings(tmp_path), web=FakeWebClient())) as client:
        response = client.get("/api/projects/search", params={"q": "P51800000937"})
    assert response.status_code == 200
    assert response.json()["outside_up"] is True
    assert response.json()["candidates"] == []


def test_a_check_for_another_states_number_is_refused_with_the_same_message(
    tmp_path: Path,
) -> None:
    with TestClient(create_app(make_settings(tmp_path), web=FakeWebClient())) as client:
        response = client.post("/api/checks", json={"rera_id": "P51800000937"})
    assert response.status_code == 422
    assert OUTSIDE_UP_MESSAGE in response.text


def test_the_search_endpoint_takes_a_locality(tmp_path: Path) -> None:
    web = FakeWebClient().replay(load_recording(EUREKA))
    with TestClient(create_app(make_settings(tmp_path), web=web)) as client:
        response = client.get(
            "/api/projects/search", params={"q": "Eureka Park", "locality": "Sector 150 Noida"}
        )
    assert response.status_code == 200
    assert response.json()["candidates"][0]["rera_id"] == "UPRERAPRJ5448"


def test_a_builder_in_another_city_with_no_hits_is_outside_up() -> None:
    found = asyncio.run(search_promoter("Prestige", FakeWebClient(), "Bengaluru", SearchCache()))
    assert found.projects == [] and found.outside_up


def test_a_company_name_repeated_by_its_title_is_listed_once() -> None:
    hit = SearchHit(
        title="SUPERTECH LIMITED",
        url="https://www.zaubacorp.com/x",
        snippet="SUPERTECH LIMITED's CIN is U74899DL1995PLC074422",
    )
    [company] = companies_in([hit], {"supertech"})
    assert company.name == "SUPERTECH LIMITED"
    assert company.cin == "U74899DL1995PLC074422"


def test_a_candidate_found_through_listings_is_named_from_its_own_page() -> None:
    from app.models import Project
    from app.states.resolver import complete_from_pages
    from tests.conftest import URL_8334
    from tests.fakes import load_page

    bare = Project(
        rera_id="UPRERAPRJ8334",
        details_url=URL_8334,
        status="listings_only",
        sources=["listing.example"],
    )
    web = FakeWebClient(pages={URL_8334: load_page("uprera_8334.html")})
    [found] = asyncio.run(complete_from_pages([bare], web))
    assert found.name == "SUPERTECH ECO VILLAGE-I PHASE I-C"
    assert found.registered_on is not None
    assert (found.status, found.sources) == ("listings_only", ["listing.example"])
