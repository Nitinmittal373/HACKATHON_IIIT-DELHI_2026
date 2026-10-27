"""The answers the browser tests replay must still be what the API says.

The fixtures are written by scripts/export_e2e_fixtures.py from the real app. Checking each one
against the API's own models means a model change cannot leave the browser tests running on a
shape the backend no longer sends.
"""

from pathlib import Path

import pytest
from pydantic import TypeAdapter

from app.compare import Comparison
from app.meta import Meta
from app.models import Check, CheckSummary, Report, SearchResponse
from app.sentinel.models import Alert
from app.stream_events import StreamEvent
from app.track_record import TrackRecord

FIXTURES = Path(__file__).resolve().parents[2] / "frontend" / "e2e" / "fixtures"

JSON_FIXTURES: list[tuple[str, type | TypeAdapter]] = [
    ("report.json", Report),
    ("report-flagged.json", Report),
    ("report-unrated.json", Report),
    ("check-created.json", Check),
    ("check-done.json", Check),
    ("summary-6742.json", CheckSummary),
    ("compare.json", Comparison),
    ("track-record.json", TrackRecord),
    ("search.json", SearchResponse),
    ("meta.json", Meta),
    ("alerts.json", TypeAdapter(list[Alert])),
]


@pytest.mark.parametrize(("name", "model"), JSON_FIXTURES, ids=[n for n, _ in JSON_FIXTURES])
def test_fixture_matches_its_model(name: str, model: type | TypeAdapter) -> None:
    text = (FIXTURES / name).read_text(encoding="utf-8")
    if isinstance(model, TypeAdapter):
        model.validate_json(text)
    else:
        model.model_validate_json(text)


def test_every_recorded_event_matches_its_model() -> None:
    adapter = TypeAdapter(StreamEvent)
    blocks = (FIXTURES / "events.sse").read_text(encoding="utf-8").strip().split("\n\n")
    data = [line.removeprefix("data: ") for block in blocks for line in block.split("\n")]
    events = [line for line in data if line.startswith("{")]
    assert events
    for event in events:
        adapter.validate_json(event)
