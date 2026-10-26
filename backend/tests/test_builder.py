"""Naming the builder from public listings, and showing no number when too little was read."""

import asyncio
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import DisplayScore
from app.states.builder import builder_in, identify_builder
from app.tinyfish import SearchHit
from tests.conftest import make_settings, read_events
from tests.fakes import FIXTURES, FakeWebClient

AGREED = "HRERA-PKL-JJR-867-2026"
GODREJ = "RC/REP/HARERA/GGM/1059/791/2026/31"


def recording(*names: str) -> FakeWebClient:
    web = FakeWebClient()
    for name in names:
        web.replay(json.loads((FIXTURES / name).read_text(encoding="utf-8")))
    return web


def hit(url: str, snippet: str, title: str = "Listing") -> SearchHit:
    return SearchHit(title=title, url=url, snippet=snippet)


def test_two_listings_that_agree_name_the_builder() -> None:
    found = asyncio.run(identify_builder(AGREED, recording("states_builder.json")))
    assert found is not None
    assert found.name == "Flower Infracon LLP"
    assert len({url for url, _ in found.sources}) >= 2
    assert all(AGREED in near for _, near in found.sources)


def test_listings_that_print_the_project_but_not_the_builder_name_nobody() -> None:
    assert asyncio.run(identify_builder(GODREJ, recording("states_builder.json"))) is None


# Hand-written results (not recorded): they pin the rule itself.
NUMBER = "P51800012345"


def test_one_result_is_not_enough() -> None:
    hits = [hit("https://a.example/1", f"{NUMBER}. Developed by Acme Homes Limited. Sector 5")]
    assert builder_in(NUMBER, hits) is None


def test_a_name_far_from_the_number_does_not_count() -> None:
    far = f"Developed by Acme Homes Limited. {'filler words ' * 40} {NUMBER}"
    hits = [hit("https://a.example/1", far), hit("https://b.example/2", far)]
    assert builder_in(NUMBER, hits) is None


def test_two_agreeing_results_spelled_differently_are_one_name() -> None:
    hits = [
        hit("https://a.example/1", f"{NUMBER}. Developed by Acme Homes Pvt. Ltd. Sector 5"),
        hit("https://b.example/2", f"RERA {NUMBER} Builder: Acme Homes Private Limited"),
    ]
    found = builder_in(NUMBER, hits)
    assert found is not None and found.name.startswith("Acme Homes")


def test_two_different_names_each_agreed_are_a_conflict() -> None:
    hits = [
        hit("https://a.example/1", f"{NUMBER} Developed by Acme Homes Limited"),
        hit("https://b.example/2", f"{NUMBER} Developed by Acme Homes Limited"),
        hit("https://c.example/3", f"{NUMBER} Developed by Zenith Realty Limited"),
        hit("https://d.example/4", f"{NUMBER} Developed by Zenith Realty Limited"),
    ]
    assert builder_in(NUMBER, hits) is None


def test_another_number_in_the_result_is_ignored() -> None:
    hits = [
        hit("https://a.example/1", "P51800099999 Developed by Acme Homes Limited"),
        hit("https://b.example/2", "P51800099999 Developed by Acme Homes Limited"),
    ]
    assert builder_in(NUMBER, hits) is None


def check_report(tmp_path: Path, rera_id: str, *recordings: str) -> tuple[dict, FakeWebClient]:  # type: ignore[type-arg]
    web = recording(*recordings)
    app = create_app(make_settings(tmp_path), web=web)
    with TestClient(app) as client:
        check_id = client.post("/api/checks", json={"rera_id": rera_id}).json()["id"]
        read_events(client, check_id)
        return client.get(f"/api/checks/{check_id}/report").json(), web


def test_the_named_builder_is_searched_by_the_national_sources(tmp_path: Path) -> None:
    report, web = check_report(tmp_path, AGREED, "states_hr_pkl.json", "states_builder.json")

    assert report["project"]["promoter"] == "Flower Infracon LLP"
    identity = next(f for f in report["findings"] if f["kind"] == "builder_identity")
    assert identity["reliability"] == "secondary"
    assert "Verify on HRERA" in identity["title"]
    # It identifies the builder; it is never scored.
    assert all(d["finding_id"] != identity["id"] for d in report["score_v2"]["drivers"])
    # The company registry looked the builder up by the name found.
    searched = [query for kind, query in web.calls if kind == "search"]
    assert any("Flower Infracon LLP" in query for query in searched)


def test_a_builder_that_listings_do_not_name_stays_unnamed(tmp_path: Path) -> None:
    report, _ = check_report(tmp_path, GODREJ, "states_hr.json", "states_builder.json")
    assert report["project"]["promoter"] is None
    assert not any(f["kind"] == "builder_identity" for f in report["findings"])


def test_a_thin_check_shows_no_number(tmp_path: Path) -> None:
    for rera_id, fixture in (
        ("P99000055716", "check_mh.json"),
        ("RC/REP/HARERA/GGM/1059/791/2026/31", "check_hr.json"),
        ("PRM/KA/RERA/1251/446/PR/190723/006078", "check_ka.json"),
    ):
        report, _ = check_report(tmp_path / fixture[6:8], rera_id, fixture)
        display = report["display_score"]
        assert display["value"] is None, fixture
        assert display["provisional"] is True and display["band"] == "insufficient_evidence"
        assert display["provisional_value"] == report["score_v2"]["value"]
        assert display["records_read"] < 3 and display["records_total"] == 6


def test_an_old_stored_score_with_a_number_is_hidden_too() -> None:
    old = {
        "value": 900,
        "band": "insufficient_evidence",
        "hard_stop": False,
        "confidence": 0.33,
        "provisional": True,
    }
    shown = DisplayScore.model_validate(old)
    assert shown.value is None and shown.provisional_value == 900 and shown.records_read == 2


def test_a_rated_score_keeps_its_number() -> None:
    rated = DisplayScore.model_validate(
        {
            "value": 621,
            "band": "Watch",
            "hard_stop": False,
            "confidence": 0.83,
            "provisional": False,
        }
    )
    assert rated.value == 621 and rated.provisional_value is None and rated.records_read == 5
