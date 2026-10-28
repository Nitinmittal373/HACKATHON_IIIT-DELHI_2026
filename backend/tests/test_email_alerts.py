"""Alert email through an HTTPS email API, with SMTP as the fallback."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.sentinel.models import Alert, FindingChange
from app.sentinel.notify import email_configured, send_alert
from tests.conftest import FIXED_NOW, make_settings

KEY = "email-key-not-real"
ALERT = Alert(
    id="b" * 32,
    watch_id="w" * 32,
    rera_id="UPRERAPRJ8334",
    check_id="a" * 32,
    created_at=FIXED_NOW,
    old_score=None,
    new_score=None,
    added=[FindingChange(title="New complaint")],
    removed=[],
    changed=[],
)


def email_api(monkeypatch: pytest.MonkeyPatch, status: int = 200) -> list[httpx.Request]:
    """Answer the email API with `status` and keep what was sent."""
    seen: list[httpx.Request] = []
    real = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json={})

    monkeypatch.setattr(
        "app.sentinel.notify.httpx.AsyncClient",
        lambda **kw: real(transport=httpx.MockTransport(handler), **kw),
    )
    return seen


def test_brevo_gets_the_key_in_a_header_and_the_alert_as_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = email_api(monkeypatch)
    settings = make_settings(
        tmp_path, email_provider="brevo", email_api_key=KEY, email_from="NeevCheck <a@b.c>"
    )

    assert asyncio.run(send_alert(settings, "me@example.com", "en", ALERT, "https://x/stop"))

    [request] = seen
    body = json.loads(request.content)
    assert str(request.url) == "https://api.brevo.com/v3/smtp/email"
    assert request.headers["api-key"] == KEY
    assert body["sender"] == {"email": "a@b.c", "name": "NeevCheck"}
    assert body["to"] == [{"email": "me@example.com"}]
    assert "New complaint" in body["textContent"] and "https://x/stop" in body["textContent"]


def test_resend_gets_a_bearer_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen = email_api(monkeypatch)
    settings = make_settings(
        tmp_path, email_provider="resend", email_api_key=KEY, email_from="a@b.c"
    )

    assert asyncio.run(send_alert(settings, "me@example.com", "hi", ALERT))

    [request] = seen
    body = json.loads(request.content)
    assert str(request.url) == "https://api.resend.com/emails"
    assert request.headers["authorization"] == f"Bearer {KEY}"
    assert body["from"] == "a@b.c" and body["to"] == ["me@example.com"]


def test_a_refused_api_call_falls_back_to_smtp_and_never_logs_the_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    email_api(monkeypatch, status=401)
    smtp: list[object] = []
    monkeypatch.setattr("app.sentinel.notify._send", lambda settings, message: smtp.append(message))
    settings = make_settings(
        tmp_path, email_api_key=KEY, email_from="a@b.c", smtp_host="smtp.example.org"
    )

    assert asyncio.run(send_alert(settings, "me@example.com", "en", ALERT))

    assert len(smtp) == 1
    assert KEY not in caplog.text


def test_a_refused_api_call_with_no_fallback_is_a_quiet_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    email_api(monkeypatch, status=500)
    settings = make_settings(tmp_path, email_api_key=KEY, email_from="a@b.c")
    assert asyncio.run(send_alert(settings, "me@example.com", "en", ALERT)) is False


def test_smtp_alone_still_works(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen = email_api(monkeypatch)
    smtp: list[object] = []
    monkeypatch.setattr("app.sentinel.notify._send", lambda settings, message: smtp.append(message))
    settings = make_settings(tmp_path, smtp_host="smtp.example.org", smtp_from="a@b.c")

    assert asyncio.run(send_alert(settings, "me@example.com", "en", ALERT))
    assert len(smtp) == 1 and seen == []


def test_an_api_key_without_a_sender_is_not_a_setup(tmp_path: Path) -> None:
    assert not email_configured(make_settings(tmp_path, email_api_key=KEY))
    assert not email_configured(make_settings(tmp_path))
    assert email_configured(make_settings(tmp_path, email_api_key=KEY, email_from="a@b.c"))


def test_meta_says_whether_alerts_are_emailed(tmp_path: Path) -> None:
    def email_alerts(**settings: object) -> bool:
        app = create_app(make_settings(tmp_path, **settings), cache_dir=None)
        with TestClient(app) as client:
            return client.get("/api/meta").json()["email_alerts"]

    assert email_alerts() is False
    assert email_alerts(email_api_key=KEY, email_from="a@b.c") is True
