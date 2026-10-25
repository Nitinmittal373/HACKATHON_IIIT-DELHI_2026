"""A promoter's other projects, replayed from searches recorded on up-rera.in."""

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.matching import blob, legal_name_in
from app.tinyfish import WebError
from app.track_record import TrackRecords, projects_of
from app.uprera_links import rera_ids_in
from tests.conftest import FIXED_NOW, make_settings
from tests.fakes import FakeWebClient, load_search, recorded_searches

FIXTURES = ("search_up_supertech_limited.json", "search_up_supertech_limited_promoter.json")


def web() -> FakeWebClient:
    return FakeWebClient(searches=recorded_searches(*FIXTURES))


def test_only_pages_naming_the_full_legal_name_count() -> None:
    record = asyncio.run(TrackRecords(web(), lambda: FIXED_NOW).find("SUPERTECH LIMITED"))
    ids = {p.rera_id for p in record.projects}
    hits = [hit for name in FIXTURES for hit in load_search(name)]
    names_it = [h for h in hits if legal_name_in("SUPERTECH LIMITED", blob(h))]
    naming = {i for h in names_it for i in rera_ids_in(h)}
    assert ids and len(record.projects) == len(ids) <= 10
    assert ids <= naming


def test_another_companys_pages_never_join_the_list() -> None:
    gaur = load_search("search_up_gaur_city.json")
    mixed = [hit for name in FIXTURES for hit in load_search(name)] + gaur
    ids = {p.rera_id for p in projects_of("SUPERTECH LIMITED", mixed)}
    assert ids
    assert not ids & {i for hit in gaur for i in rera_ids_in(hit)}


def test_the_current_project_is_left_out_and_the_day_cache_is_used() -> None:
    fake = web()
    records = TrackRecords(fake, lambda: FIXED_NOW)
    first = asyncio.run(records.find("SUPERTECH LIMITED"))
    excluded = first.projects[0].rera_id
    again = asyncio.run(records.find("Supertech Ltd.", exclude=excluded))

    assert excluded not in [p.rera_id for p in again.projects]
    # "Supertech Ltd." is the same legal name, so the cached answer is reused.
    assert len([call for call in fake.calls if call[0] == "search"]) == 2


def test_the_cache_expires_after_a_day() -> None:
    fake, now = web(), [0.0]
    records = TrackRecords(fake, lambda: FIXED_NOW, clock=lambda: now[0])
    asyncio.run(records.find("SUPERTECH LIMITED"))
    now[0] = 24 * 60 * 60 + 1
    asyncio.run(records.find("SUPERTECH LIMITED"))
    assert len([call for call in fake.calls if call[0] == "search"]) == 4


def test_endpoint(tmp_path: Path) -> None:
    app = create_app(make_settings(tmp_path), web=web(), clock=lambda: FIXED_NOW)
    with TestClient(app) as client:
        params = {"name": "SUPERTECH LIMITED", "exclude": "UPRERAPRJ408"}
        response = client.get("/api/promoters/projects", params=params)
    assert response.status_code == 200
    body = response.json()
    assert body["promoter"] == "SUPERTECH LIMITED"
    assert "UPRERAPRJ408" not in [p["rera_id"] for p in body["projects"]]


def test_a_failed_search_names_the_reason(tmp_path: Path) -> None:
    fake = FakeWebClient(search_error=WebError("Search failed: no credit", "wallet_empty"))
    with TestClient(create_app(make_settings(tmp_path), web=fake)) as client:
        response = client.get("/api/promoters/projects", params={"name": "SUPERTECH LIMITED"})
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "wallet_empty"
