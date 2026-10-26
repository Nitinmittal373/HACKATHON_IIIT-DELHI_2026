"""The checked-in API contract must describe every route the app serves."""

import json
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.main import create_app
from app.stream_events import StreamEvent
from tests.conftest import make_settings, make_web, read_events
from tests.fakes import load_recording

CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "openapi.json"
# Server-Sent Events have no JSON body to describe; their payload models are in the schema.
STREAMING = {"/api/checks/{check_id}/events"}


@pytest.fixture
def routes(tmp_path: Path) -> list[APIRoute]:
    app = create_app(make_settings(tmp_path), cache_dir=None)
    return [route for route in app.routes if isinstance(route, APIRoute)]


def test_every_route_is_in_the_contract(routes: list[APIRoute]) -> None:
    paths = json.loads(CONTRACT.read_text(encoding="utf-8"))["paths"]
    missing = [
        f"{method} {route.path}"
        for route in routes
        for method in route.methods
        if method.lower() not in paths.get(route.path, {})
    ]
    assert missing == [], "API contract out of date: run make contract"


def test_every_json_route_declares_its_response(routes: list[APIRoute]) -> None:
    bare = [
        route.path
        for route in routes
        if route.status_code != 204 and route.path not in STREAMING and route.response_model is None
    ]
    assert bare == []


def test_every_streamed_event_matches_its_contract_model(tmp_path: Path) -> None:
    web = make_web().replay(load_recording("check_8334.json"))
    with TestClient(create_app(make_settings(tmp_path), web=web, cache_dir=None)) as client:
        check_id = client.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
        events = read_events(client, check_id)

    adapter = TypeAdapter(StreamEvent)
    assert {event["type"] for event in events} >= {"source.started", "check.completed"}
    for event in events:
        adapter.validate_python(event)
