from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.tinyfish import WebError
from tests.conftest import make_settings
from tests.fakes import FakeWebClient


def search_with(tmp_path: Path, error: WebError) -> tuple[int, dict, dict]:
    app = create_app(make_settings(tmp_path), web=FakeWebClient(search_error=error))
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/projects/search", params={"q": "Gaur City"})
    return response.status_code, response.json(), dict(response.headers)


@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("tinyfish_key", 502),
        ("wallet_empty", 502),
        ("unreachable", 502),
        ("upstream", 502),
        ("timeout", 504),
    ],
)
def test_a_failed_search_names_the_reason(tmp_path: Path, code: str, status: int) -> None:
    got, body, _ = search_with(tmp_path, WebError("Search failed: something", code))  # type: ignore[arg-type]
    assert got == status
    assert body["detail"]["code"] == code
    assert body["detail"]["message"] == "Search failed: something"


def test_a_tinyfish_rate_limit_passes_on_the_wait(tmp_path: Path) -> None:
    error = WebError("Search failed: rate limit", "rate_limited", retry_after=42)
    status, body, headers = search_with(tmp_path, error)
    assert status == 429
    assert body["detail"]["code"] == "rate_limited"
    assert headers["retry-after"] == "42"


def test_the_error_message_never_holds_the_key(tmp_path: Path) -> None:
    _, body, _ = search_with(tmp_path, WebError("Search failed: could not reach TinyFish"))
    assert "test-key-not-real" not in str(body)
