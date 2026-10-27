"""Naming the builder from public listings, and showing no number when too little was read."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import DisplayScore
from app.states.builder import builder_in
from app.tinyfish import SearchHit
from tests.conftest import make_settings, make_web, read_events


def hit(url: str, snippet: str, title: str = "Listing") -> SearchHit:
    return SearchHit(title=title, url=url, snippet=snippet)


# Hand-written results (not recorded): they pin the rule itself.
NUMBER = "UPRERAPRJ6001"


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
        hit("https://a.example/1", "UPRERAPRJ9999 Developed by Acme Homes Limited"),
        hit("https://b.example/2", "UPRERAPRJ9999 Developed by Acme Homes Limited"),
    ]
    assert builder_in(NUMBER, hits) is None


def test_a_thin_check_shows_no_number(tmp_path: Path) -> None:
    # The recorded UP-RERA pages give the RERA record but no company page, so few records are read.
    with TestClient(create_app(make_settings(tmp_path), web=make_web())) as client:
        check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
        read_events(client, check_id)
        report = client.get(f"/api/checks/{check_id}/report").json()

    display = report["display_score"]
    assert display["value"] is None
    assert display["provisional"] is True and display["band"] == "insufficient_evidence"
    assert display["provisional_value"] == report["score_v2"]["value"]
    assert display["records_read"] < 4 and display["records_total"] == 6


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
