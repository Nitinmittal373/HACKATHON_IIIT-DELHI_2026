import asyncio
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.resolve import candidates_from_hits, resolve
from app.uprera_links import rera_ids_in, summary_url
from tests.fakes import FakeWebClient, load_page, load_search, recorded_searches

URL_8334 = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=8334"


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


def test_old_format_number_reads_the_page_instead_of_searching() -> None:
    web = FakeWebClient(pages={URL_8334: load_page("uprera_8334.html")})
    candidates = asyncio.run(resolve(" upreraprj8334 ", web))

    assert [c.rera_id for c in candidates] == ["UPRERAPRJ8334"]
    assert candidates[0].name == "SUPERTECH ECO VILLAGE-I PHASE I-C"
    assert candidates[0].promoter == "SUPERTECH LIMITED"
    assert candidates[0].district == "Gautam Buddha Nagar"
    assert web.calls == [("fetch", URL_8334)]


def test_number_whose_page_shows_another_project_gives_no_candidate() -> None:
    url = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=6742"
    web = FakeWebClient(pages={url: load_page("uprera_8334.html")})
    assert asyncio.run(resolve("UPRERAPRJ6742", web)) == []


def test_search_endpoint(client: TestClient) -> None:
    response = client.get("/api/projects/search", params={"q": "Gaur City"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "Gaur City"
    assert 1 <= len(body["candidates"]) <= 8


def test_search_rejects_a_too_short_query(client: TestClient) -> None:
    assert client.get("/api/projects/search", params={"q": "a"}).status_code == 422


# The resolver's cases, replayed from searches and pages recorded on 25 Oct 2026.

URL_2875 = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=2875"
URL_6742 = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=6742"
URL_6819 = "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=6819"


def summary_link(search_fixture: str, rera_id: str) -> str:
    for hit in load_search(search_fixture):
        if (url := summary_url(hit.url)) and rera_id in rera_ids_in(hit):
            return url
    raise AssertionError(f"{search_fixture} has no Projectsummary link for {rera_id}")


@pytest.mark.parametrize("typed", ["UPRERA PRJ 8334", "uprera-prj-8334", "UPRERAPRJ8334."])
def test_a_and_d_any_spelling_of_an_old_number_opens_its_page(typed: str) -> None:
    web = FakeWebClient(pages={URL_8334: load_page("uprera_8334.html")})
    [project] = asyncio.run(resolve(typed, web))
    assert project.rera_id == "UPRERAPRJ8334"
    assert project.promoter == "SUPERTECH LIMITED"
    assert web.calls == [("fetch", URL_8334)]


def test_a_a_number_no_page_confirms_is_not_found() -> None:
    # No details page and nothing on up-rera.in for this number.
    assert asyncio.run(resolve("UPRERAPRJ99999", FakeWebClient())) == []


def test_b_a_new_format_number_is_found_through_its_summary_page() -> None:
    url = summary_link("search_up_188811.json", "UPRERAPRJ188811/08/2024")
    web = FakeWebClient(
        searches=recorded_searches("search_up_188811.json"),
        pages={url: load_page("uprera_summary_188811.html")},
    )
    [project] = asyncio.run(resolve("UPRERAPRJ188811/08/2024", web))
    assert project.name == "GAUR NYC RESIDENCES"
    assert project.district == "Ghaziabad"
    assert project.details_url == url


def test_b_a_six_digit_number_without_a_stable_page_uses_its_summary_page() -> None:
    url = summary_link("search_up_396176.json", "UPRERAPRJ396176")
    web = FakeWebClient(
        searches=recorded_searches("search_up_396176.json"),
        pages={url: load_page("uprera_summary_396176.html")},
    )
    [project] = asyncio.run(resolve("UPRERAPRJ396176", web))
    assert project.name == "ATS Picturesque Reprieves Phase 2"
    assert project.promoter == "ATS HOMES PRIVATE LIMITED"
    assert project.registered_on == date(2019, 2, 27)
    assert project.details_url == url
    # The stable page was tried first; UP-RERA has none for this number.
    assert web.calls[0] == ("fetch", "https://www.up-rera.in/Frm_View_Project_Details.aspx?id=396176")


def test_c_a_name_lists_up_rera_projects_completed_from_their_pages() -> None:
    url_396176 = summary_link("search_up_ats_pristine.json", "UPRERAPRJ396176")
    web = FakeWebClient(
        searches=recorded_searches("search_up_ats_pristine.json"),
        pages={
            URL_2875: load_page("uprera_2875.html"),
            url_396176: load_page("uprera_summary_396176.html"),
        },
    )
    candidates = asyncio.run(resolve("ATS Pristine", web))
    by_id = {c.rera_id: c for c in candidates}

    assert candidates[0].rera_id == "UPRERAPRJ2875"
    assert by_id["UPRERAPRJ2875"].district == "Gautam Buddha Nagar"
    assert by_id["UPRERAPRJ2875"].details_url == URL_2875
    assert by_id["UPRERAPRJ396176"].details_url == url_396176
    assert len(candidates) <= 8
    assert all(c.details_url.startswith("https://") for c in candidates)


def test_c_a_page_that_cannot_be_read_keeps_what_search_said() -> None:
    web = FakeWebClient(
        searches=recorded_searches("search_up_gaur_city.json"),
        pages={URL_6742: load_page("uprera_6742.html")},
    )
    candidates = asyncio.run(resolve("Gaur City", web))
    by_id = {c.rera_id: c for c in candidates}

    assert 1 <= len(candidates) <= 8
    assert by_id["UPRERAPRJ6742"].district == "Gautam Buddha Nagar"  # read from its page
    assert by_id["UPRERAPRJ4780"].name == "Gaur City Center"  # its page was unreadable
    assert len(by_id) == len(candidates)


def test_c_without_up_rera_numbers_other_sites_are_read_and_each_number_confirmed() -> None:
    web = FakeWebClient(
        searches={
            "Gaur City UP RERA project @up-rera.in": [],
            "Gaur City UP RERA project": load_search("search_gaur_city.json"),
        },
        pages={URL_6742: load_page("uprera_6742.html")},
    )
    candidates = asyncio.run(resolve("Gaur City", web))

    # Only the number whose own page could be read is shown, with what that page says.
    assert [c.rera_id for c in candidates] == ["UPRERAPRJ6742"]
    assert candidates[0].promoter == "Gaursons Promoters Private Limited"


def test_c_numbers_other_sites_print_for_unrelated_projects_are_dropped() -> None:
    web = FakeWebClient(
        searches=recorded_searches("search_up_supertech_hues.json", "search_supertech_hues.json"),
        pages={URL_6819: load_page("uprera_6819.html")},
    )
    # Supertech Hues is in Gurugram; the numbers near it on the web belong to other projects.
    assert asyncio.run(resolve("Supertech Hues", web)) == []
    assert ("fetch", URL_6819) in web.calls


def test_e_a_project_outside_up_finds_nothing() -> None:
    web = FakeWebClient(
        searches=recorded_searches("search_up_lodha_palava.json", "search_lodha_palava.json")
    )
    assert asyncio.run(resolve("Lodha Palava Mumbai", web)) == []


def test_e_the_endpoint_answers_an_empty_list_not_an_error(client: TestClient) -> None:
    response = client.get("/api/projects/search", params={"q": "Lodha Palava Mumbai"})
    assert response.status_code == 200
    assert response.json()["candidates"] == []
    # Mumbai is not in Uttar Pradesh, so the page can say so calmly.
    assert response.json()["outside_up"] is True


def test_search_engine_link_text_is_not_part_of_a_promoter() -> None:
    hits = [h for h in load_search("search_uprera_8334.json") if "Read more" in h.snippet]
    assert hits, "the fixture has a snippet ending in 'Read more'"
    assert all("Read more" not in (c.promoter or "") for c in candidates_from_hits(hits))
