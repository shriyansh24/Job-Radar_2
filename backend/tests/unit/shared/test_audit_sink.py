from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.shared import audit_sink


class _FakeRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str], dict[str, object]]] = []
        self.stream_entries: list[tuple[str, dict[str, str]]] = []

    async def xadd(self, key: str, payload: dict[str, str], **kwargs: object) -> str:
        self.calls.append((key, payload, kwargs))
        stream_id = f"{len(self.stream_entries) + 1}-0"
        self.stream_entries.append((stream_id, payload))
        return stream_id

    async def xrevrange(
        self,
        key: str,
        _max: str,
        _min: str,
        *,
        count: int,
    ) -> list[tuple[str, dict[str, str]]]:
        if key != "jobradar:auth-audit":
            return []
        return list(reversed(self.stream_entries))[:count]


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


@pytest.mark.asyncio
async def test_read_auth_audit_events_returns_recent_entries(
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
        auth_source="password",
    )
    await audit_sink.publish_auth_audit_event(
        "auth_refresh_failed",
        user_id="user-1",
        reason="token_revoked",
    )

    entries = await audit_sink.read_auth_audit_events(limit=2, queue_pool=redis)

    assert entries[0]["event"] == "auth_refresh_failed"
    assert entries[0]["reason"] == "token_revoked"
    assert entries[1]["event"] == "auth_login_succeeded"
    assert entries[1]["auth_source"] == "password"


@pytest.mark.asyncio
async def test_emit_auth_audit_event_schedules_publish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publish = asyncio.Event()

    async def _fake_publish(event: str, **fields: object) -> None:
        assert event == "auth_login_succeeded"
        assert fields["user_id"] == "user-1"
        publish.set()

    monkeypatch.setattr(audit_sink, "publish_auth_audit_event", _fake_publish)
    monkeypatch.setattr(
        audit_sink,
        "settings",
        SimpleNamespace(
            auth_audit_stream_enabled=True,
            auth_audit_stream_key="jobradar:auth-audit",
            auth_audit_stream_maxlen=1000,
        ),
    )

    audit_sink.emit_auth_audit_event("auth_login_succeeded", user_id="user-1")
    await asyncio.wait_for(publish.wait(), timeout=1)
