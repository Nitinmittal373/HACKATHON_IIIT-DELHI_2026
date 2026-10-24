import asyncio
from datetime import date

from fastapi.testclient import TestClient

from app.resolve import candidates_from_hits, resolve
from tests.fakes import FakeWebClient, load_search


def test_gaur_city_search_keeps_only_up_rera_projects() -> None:
    candidates = candidates_from_hits(load_search("search_gaur_city.json"))
    ids = [c.rera_id for c in candidates]

    assert {"UPRERAPRJ6742", "UPRERAPRJ6934"} <= set(ids)
    assert "UPRERAPRJ188811/08/2024" in ids
    assert len(ids) == len(set(ids))
    # The azurewebsites mirror and the gaursplume.com page are not up-rera.in.
    assert "UPRERAPRJ950965/07/2026" not in ids
    assert all(c.details_url.startswith("https://") for c in candidates)


def test_old_format_numbers_use_the_stable_details_page() -> None:
    by_id = {c.rera_id: c for c in candidates_from_hits(load_search("search_gaur_city.json"))}

    avenue = by_id["UPRERAPRJ6742"]
    assert avenue.details_url == "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=6742"
    assert avenue.name == "14th Avenue (Group Housing) - Gaur City"
    assert avenue.registered_on == date(2017, 7, 31)
    # The snippet cuts the promoter off ("Gaursons Promoters Private ..."), so it is not used.
    assert avenue.promoter is None


def test_new_format_numbers_keep_the_projectsummary_link() -> None:
    by_id = {c.rera_id: c for c in candidates_from_hits(load_search("search_gaur_city.json"))}

    nyc = by_id["UPRERAPRJ188811/08/2024"]
    assert nyc.name == "GAUR NYC RESIDENCES"
    assert nyc.details_url.startswith("https://up-rera.in/Projectsummary?")


def test_ranking_prefers_names_that_match_the_query() -> None:
    web = FakeWebClient(
        searches={"Gaur City UP RERA project": load_search("search_gaur_city.json")}
    )
    candidates = asyncio.run(resolve("Gaur City", web))
    assert len(candidates) <= 8
    assert candidates[0].rera_id in {"UPRERAPRJ6742", "UPRERAPRJ6934"}


def test_supertech_search_finds_eco_village_phases() -> None:
    ids = [
        c.rera_id for c in candidates_from_hits(load_search("search_supertech_eco_village.json"))
    ]
    assert ids[0] == "UPRERAPRJ8334"
    assert "UPRERAPRJ4878" in ids


def test_old_format_number_skips_search() -> None:
    web = FakeWebClient()
    candidates = asyncio.run(resolve(" upreraprj8334 ", web))
    assert [c.rera_id for c in candidates] == ["UPRERAPRJ8334"]
    assert ("search", "UPRERAPRJ8334 UP RERA project") not in web.calls


def test_search_endpoint(client: TestClient) -> None:
    response = client.get("/api/projects/search", params={"q": "Gaur City"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "Gaur City"
    assert 1 <= len(body["candidates"]) <= 8


def test_search_rejects_a_too_short_query(client: TestClient) -> None:
    assert client.get("/api/projects/search", params={"q": "a"}).status_code == 422
