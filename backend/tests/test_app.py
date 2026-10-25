import pytest
from fastapi.testclient import TestClient

from app import config


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_security_headers(client: TestClient) -> None:
    headers = client.get("/api/health").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in headers["Content-Security-Policy"]


def test_docs_keep_working_without_strict_csp(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Content-Security-Policy" not in response.headers


def test_cors_allows_only_the_frontend(client: TestClient) -> None:
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    blocked = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in blocked.headers


def test_the_browser_may_read_retry_after(client: TestClient) -> None:
    response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert response.headers["access-control-expose-headers"] == "Retry-After"


def test_missing_api_key_fails_fast_with_a_clear_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TINYFISH_API_KEY", raising=False)
    monkeypatch.setitem(config.Settings.model_config, "env_file", None)
    config.load_settings.cache_clear()
    try:
        with pytest.raises(config.MissingSettingError, match="TINYFISH_API_KEY"):
            config.load_settings()
    finally:
        config.load_settings.cache_clear()


def test_settings_never_show_the_key(settings: config.Settings) -> None:
    assert "test-key-not-real" not in repr(settings)
    assert "test-key-not-real" not in str(settings.model_dump())
