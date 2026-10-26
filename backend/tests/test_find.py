"""Finding projects with no website: by builder, by locality, and the city-to-state table.

Recordings are the live Search answers of 27 Oct 2026 (scripts/capture_find.py).
"""

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.states.openweb import SearchCache
from app.states.places import PLACES, place_in, state_of_place, without_places
from app.states.promoter_search import search_promoter
from app.states.registry import BY_CODE
from app.states.resolver import resolve_any
from tests.conftest import make_settings
from tests.fakes import FakeWebClient, load_recording

LODHA = "find_builder_lodha.json"
EUREKA = "find_locality_eureka.json"


def lodha_search():
    web = FakeWebClient().replay(load_recording(LODHA))
    return asyncio.run(search_promoter("Lodha Developers", web, cache=SearchCache()))


def test_a_builder_search_lists_registered_projects_with_their_portal() -> None:
    found = lodha_search()
    [project] = found.projects
    assert project.rera_id == "P51700020128"
    assert project.state == "MH"
    assert project.status == "confirmed"
    assert project.sources == ["maharera.maharashtra.gov.in"]


def test_a_builder_search_names_the_company_and_its_cin() -> None:
    names = {c.name.lower(): c.cin for c in lodha_search().companies}
    assert names["lodha developers limited"] == "L45200MH1995PLC093041"
    # Other Lodha companies are listed apart, never merged into this one.
    assert "lodha foundation" not in names


def test_a_builder_search_without_a_city_looks_in_every_state() -> None:
    assert lodha_search().searched_states == list(BY_CODE)


def test_a_city_limits_a_builder_search_to_its_state() -> None:
    web = FakeWebClient()
    found = asyncio.run(search_promoter("Mahagun", web, city="Noida", cache=SearchCache()))
    assert found.state == "UP"
    assert found.searched_states == ["UP"]


def test_a_locality_search_puts_the_closest_name_first_and_uses_one_state() -> None:
    web = FakeWebClient().replay(load_recording(EUREKA))
    resolved = asyncio.run(resolve_any("Eureka Park", web, locality="Sector 150 Noida"))
    assert resolved.searched_states == ["UP"]
    assert resolved.candidates[0].rera_id == "UPRERAPRJ5448"


@pytest.mark.parametrize(
    ("text", "state"),
    [
        ("Sector 150 Noida", "UP"),
        ("greater noida west", "UP"),
        ("Whitefield, Bengaluru", "KA"),
        ("Gurgaon sector 65", "HR"),
        ("Navi Mumbai", "MH"),
        ("Hinjewadi Pune", "MH"),
        ("OMR Chennai", "TN"),
        ("Kolkata", "WB"),
        ("Zirakpur", "PB"),
        ("an unknown village", None),
    ],
)
def test_a_city_names_its_state(text: str, state: str | None) -> None:
    assert state_of_place(text) == state


def test_every_place_points_at_a_supported_state() -> None:
    assert set(PLACES.values()) <= set(BY_CODE)


def test_the_longest_place_wins() -> None:
    assert place_in("flats in greater noida") == "greater noida"


def test_places_are_removed_from_a_name_but_never_all_of_it() -> None:
    assert without_places("Godrej Woods Noida") == "Godrej Woods"


def test_the_promoter_endpoint_answers_with_a_builder_search(tmp_path: Path) -> None:
    web = FakeWebClient().replay(load_recording(LODHA))
    with TestClient(create_app(make_settings(tmp_path), web=web)) as client:
        response = client.get("/api/promoters/search", params={"q": "Lodha Developers"})
    assert response.status_code == 200
    body = response.json()
    assert body["projects"][0]["rera_id"] == "P51700020128"
    assert body["companies"][0]["cin"].startswith("L45200MH")


def test_the_promoter_endpoint_refuses_an_unknown_state(tmp_path: Path) -> None:
    with TestClient(create_app(make_settings(tmp_path), web=FakeWebClient())) as client:
        response = client.get("/api/promoters/search", params={"q": "Lodha", "state": "ZZ"})
    assert response.status_code == 422


def test_the_search_endpoint_takes_a_locality(tmp_path: Path) -> None:
    web = FakeWebClient().replay(load_recording(EUREKA))
    with TestClient(create_app(make_settings(tmp_path), web=web)) as client:
        response = client.get(
            "/api/projects/search", params={"q": "Eureka Park", "locality": "Sector 150 Noida"}
        )
    assert response.status_code == 200
    assert response.json()["searched_states"] == ["UP"]


def test_every_state_says_where_to_report_a_project_without_a_number() -> None:
    for adapter in BY_CODE.values():
        assert adapter.unregistered_url.startswith("https://"), adapter.code
    assert BY_CODE["UP"].unregistered_url == "https://www.up-rera.in/NonRegistration"
    assert BY_CODE["MH"].unregistered_url.endswith("/complaint-against-unregistered-project")


def test_the_states_endpoint_carries_those_links(tmp_path: Path) -> None:
    with TestClient(create_app(make_settings(tmp_path), web=FakeWebClient())) as client:
        states = client.get("/api/states").json()
    assert all(state["unregistered_url"].startswith("https://") for state in states)


def test_a_company_name_repeated_by_its_title_is_listed_once() -> None:
    from app.states.promoter_search import companies_in
    from app.tinyfish import SearchHit

    hit = SearchHit(
        title="LODHA DEVELOPERS LIMITED",
        url="https://www.zaubacorp.com/x",
        snippet="LODHA DEVELOPERS LIMITED's CIN is L45200MH1995PLC093041",
    )
    [company] = companies_in([hit], {"lodha"})
    assert company.name == "LODHA DEVELOPERS LIMITED"
    assert company.cin == "L45200MH1995PLC093041"
