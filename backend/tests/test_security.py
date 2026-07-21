import json
import logging

import pytest

from app.core.logging import JsonFormatter
from app.core.security import rate_limiter
from app.core.settings import Settings


def test_api_authentication_can_protect_private_routes(client, monkeypatch):
    monkeypatch.setattr("app.core.security.settings.AUTH_ENABLED", True)
    monkeypatch.setattr("app.core.security.settings.API_ACCESS_KEY", "a" * 32)

    unauthorized = client.get("/notes/")
    authorized = client.get(
        "/notes/",
        headers={"Authorization": f"Bearer {'a' * 32}"},
    )
    health = client.get("/health")

    assert unauthorized.status_code == 401
    assert "X-Request-ID" in unauthorized.headers
    assert unauthorized.headers["X-Content-Type-Options"] == "nosniff"
    assert authorized.status_code == 200
    assert health.status_code == 200


def test_rate_limit_returns_retry_after(client, monkeypatch):
    rate_limiter.clear()
    monkeypatch.setattr("app.core.security.settings.RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr("app.core.security.settings.RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr("app.core.security.settings.RATE_LIMIT_WINDOW_SECONDS", 60)

    first = client.get("/notes/")
    second = client.get("/notes/")

    assert first.status_code == 200
    assert second.status_code == 429
    assert int(second.headers["Retry-After"]) >= 1
    rate_limiter.clear()


def test_security_headers_and_request_id_are_returned(client):
    response = client.get("/health", headers={"X-Request-ID": "build-week-1"})

    assert response.headers["X-Request-ID"] == "build-week-1"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_invalid_request_id_is_replaced(client):
    response = client.get("/health", headers={"X-Request-ID": "invalid id with spaces"})

    assert response.headers["X-Request-ID"] != "invalid id with spaces"


def test_json_formatter_emits_structured_fields():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="faran.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-1"

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "request completed"
    assert payload["request_id"] == "request-1"


def test_production_settings_reject_unsafe_configuration():
    config = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        DEBUG=True,
        AUTO_CREATE_TABLES=True,
        AUTH_ENABLED=False,
        API_ACCESS_KEY="",
        ALLOWED_HOSTS="*",
        AI_PROVIDER="groq",
        GROQ_API_KEY="",
    )

    with pytest.raises(RuntimeError) as exc_info:
        config.validate_runtime()

    assert "Invalid production configuration" in str(exc_info.value)


def test_production_settings_accept_explicit_secure_configuration():
    config = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        DEBUG=False,
        AUTO_CREATE_TABLES=False,
        AUTH_ENABLED=True,
        API_ACCESS_KEY="a" * 32,
        ALLOWED_HOSTS="faran.example.com",
        AI_PROVIDER="openai",
        AGENT_RUNTIME="openai",
        EMBEDDING_PROVIDER="openai",
        OPENAI_API_KEY="test-key",
    )

    config.validate_runtime()
