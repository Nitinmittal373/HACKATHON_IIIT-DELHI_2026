"""Saved reports per account: the token check, the three routes and their limits."""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.bridge_token import InvalidToken, verify_bridge_token
from app.main import create_app
from tests.conftest import FIXED_NOW, make_settings, make_web, read_events

SECRET = "bridge-secret-for-tests-only-0123456789"


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def token(
    sub: str = "google-123",
    email: str = "buyer@example.com",
    secret: str = SECRET,
    expires: datetime = FIXED_NOW + timedelta(minutes=10),
    alg: str = "HS256",
) -> str:
    head = b64(json.dumps({"alg": alg, "typ": "JWT"}).encode())
    body = b64(json.dumps({"sub": sub, "email": email, "exp": int(expires.timestamp())}).encode())
    signature = hmac.new(secret.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{b64(signature)}"


def test_a_good_token_names_the_account() -> None:
    user = verify_bridge_token(token(), SECRET, FIXED_NOW)
    assert (user.sub, user.email) == ("google-123", "buyer@example.com")


@pytest.mark.parametrize(
    "bad",
    [
        token(secret="another-secret"),
        token(expires=FIXED_NOW - timedelta(seconds=1)),
        token(alg="none"),
        "abc",
        token()[:-3] + "xyz",
    ],
    ids=["wrong-secret", "expired", "wrong-alg", "malformed", "tampered"],
)
def test_a_bad_token_is_refused(bad: str) -> None:
    with pytest.raises(InvalidToken):
        verify_bridge_token(bad, SECRET, FIXED_NOW)


def client(tmp_path: Path, **settings: object) -> TestClient:
    values = {"auth_bridge_secret": SECRET, **settings}
    app = create_app(make_settings(tmp_path, **values), web=make_web(), clock=lambda: FIXED_NOW)
    return TestClient(app)


def auth(**kwargs: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(**kwargs)}"}  # type: ignore[arg-type]


def finished_check(http: TestClient) -> str:
    check_id = http.post("/api/checks", json={"rera_id": "UPRERAPRJ8334"}).json()["id"]
    read_events(http, check_id)
    return check_id


def test_saved_reports_need_a_valid_token(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        assert http.get("/api/me/reports").status_code == 401
        assert http.get("/api/me/reports", headers=auth(secret="x")).status_code == 401


def test_without_a_secret_accounts_are_off_and_checks_still_work(tmp_path: Path) -> None:
    with client(tmp_path, auth_bridge_secret=None) as http:
        assert http.get("/api/me/reports", headers=auth()).status_code == 503
        assert finished_check(http)


def test_a_check_is_saved_listed_and_forgotten(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        check_id = finished_check(http)
        assert http.get("/api/me/reports", headers=auth()).json() == []

        saved = http.post("/api/me/reports", json={"ids": [check_id]}, headers=auth())
        assert [c["id"] for c in saved.json()] == [check_id]
        # Saving twice is harmless, and ids the server never had are ignored.
        again = http.post("/api/me/reports", json={"ids": [check_id, "c" * 32]}, headers=auth())
        assert [c["id"] for c in again.json()] == [check_id]

        assert http.delete(f"/api/me/reports/{check_id}", headers=auth()).status_code == 204
        assert http.get("/api/me/reports", headers=auth()).json() == []


def test_each_account_sees_only_its_own_reports(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        check_id = finished_check(http)
        http.post("/api/me/reports", json={"ids": [check_id]}, headers=auth(sub="one"))
        assert http.get("/api/me/reports", headers=auth(sub="two")).json() == []
        assert len(http.get("/api/me/reports", headers=auth(sub="one")).json()) == 1


def test_bad_ids_are_refused(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        response = http.post("/api/me/reports", json={"ids": ["nope"]}, headers=auth())
        assert response.status_code == 422


def test_the_account_routes_are_rate_limited(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        answers = [http.get("/api/me/reports", headers=auth()).status_code for _ in range(32)]
    assert answers.count(429) == 2


def test_the_browser_may_send_the_token(tmp_path: Path) -> None:
    with client(tmp_path) as http:
        response = http.options(
            "/api/me/reports",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


