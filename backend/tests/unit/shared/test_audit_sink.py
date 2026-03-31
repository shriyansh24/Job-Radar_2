from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.shared import audit_sink


class _FakeRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str], dict[str, object]]] = []

    async def xadd(self, key: str, payload: dict[str, str], **kwargs: object) -> str:
        self.calls.append((key, payload, kwargs))
        return "stream-id"


@pytest.mark.asyncio
async def test_publish_auth_audit_event_writes_to_redis_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = _FakeRedis()

    async def _fake_get_queue_pool() -> _FakeRedis:
        return redis

    monkeypatch.setattr(audit_sink, "get_queue_pool", _fake_get_queue_pool)
    monkeypatch.setattr(
        audit_sink,
        "settings",
        SimpleNamespace(
            auth_audit_stream_enabled=True,
            auth_audit_stream_key="jobradar:auth-audit",
            auth_audit_stream_maxlen=1000,
        ),
    )

    await audit_sink.publish_auth_audit_event(
        "auth_login_succeeded",
        user_id="user-1",
        token_version=2,
        auth_source="password",
    )

    assert len(redis.calls) == 1
    key, payload, kwargs = redis.calls[0]
    assert key == "jobradar:auth-audit"
    assert payload["event"] == "auth_login_succeeded"
    assert payload["audit_stream"] == "auth"
    assert payload["user_id"] == "user-1"
    assert payload["token_version"] == "2"
    assert payload["auth_source"] == "password"
    assert "timestamp" in payload
    assert kwargs == {"maxlen": 1000, "approximate": True}


@pytest.mark.asyncio
async def test_publish_auth_audit_event_is_noop_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = _FakeRedis()

    async def _fake_get_queue_pool() -> _FakeRedis:
        return redis

    monkeypatch.setattr(audit_sink, "get_queue_pool", _fake_get_queue_pool)
    monkeypatch.setattr(
        audit_sink,
        "settings",
        SimpleNamespace(
            auth_audit_stream_enabled=False,
            auth_audit_stream_key="jobradar:auth-audit",
            auth_audit_stream_maxlen=1000,
        ),
    )

    await audit_sink.publish_auth_audit_event("auth_login_succeeded", user_id="user-1")

    assert redis.calls == []
