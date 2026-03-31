from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.runtime import telemetry
from app.runtime.queue import QueueSnapshot


class _FakeRedis:
    def __init__(self) -> None:
        self.hashes: dict[str, dict[str, str]] = {}
        self.streams: dict[str, list[tuple[str, dict[str, str]]]] = {}

    async def xadd(self, key: str, payload: dict[str, str], **_kwargs: object) -> str:
        stream = self.streams.setdefault(key, [])
        stream_id = f"{len(stream) + 1}-0"
        stream.append((stream_id, payload))
        return stream_id

    async def xrevrange(
        self,
        key: str,
        _max: str,
        _min: str,
        *,
        count: int,
    ) -> list[tuple[str, dict[str, str]]]:
        stream = self.streams.get(key, [])
        return list(reversed(stream))[:count]

    async def hgetall(self, key: str) -> dict[str, str]:
        return self.hashes.get(key, {})

    async def hset(self, key: str, mapping: dict[str, str]) -> None:
        self.hashes.setdefault(key, {}).update(mapping)


def _snapshot(
    queue_name: str,
    *,
    depth: int,
    pressure: str,
    age: int,
    alert: str,
) -> QueueSnapshot:
    return QueueSnapshot(
        queue_name=queue_name,
        queue_depth=depth,
        queue_pressure=pressure,
        oldest_job_age_seconds=age,
        queue_alert=alert,
    )


@pytest.mark.asyncio
async def test_record_queue_telemetry_writes_samples_and_alert_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = _FakeRedis()
    monkeypatch.setattr(
        telemetry,
        "settings",
        SimpleNamespace(
            queue_telemetry_stream_key="jobradar:queue-telemetry",
            queue_telemetry_stream_maxlen=2000,
            queue_alert_stream_key="jobradar:queue-alerts",
            queue_alert_stream_maxlen=1000,
            queue_alert_state_key="jobradar:queue-alert-state",
            queue_alert_webhook_url="",
            queue_alert_webhook_timeout_seconds=5.0,
        ),
    )

    await telemetry.record_queue_telemetry(
        redis,
        {
            "arq:queue:scraping": _snapshot(
                "arq:queue:scraping",
                depth=0,
                pressure="nominal",
                age=0,
                alert="clear",
            )
        },
        captured_at="2026-03-31T12:00:00+00:00",
    )
    await telemetry.record_queue_telemetry(
        redis,
        {
            "arq:queue:scraping": _snapshot(
                "arq:queue:scraping",
                depth=12,
                pressure="elevated",
                age=480,
                alert="watch",
            )
        },
        captured_at="2026-03-31T12:05:00+00:00",
    )

    samples = await telemetry.read_queue_telemetry(limit=2, queue_pool=redis)
    alerts = await telemetry.read_queue_alerts(limit=4, queue_pool=redis)

    assert len(samples) == 2
    assert samples[0]["captured_at"] == "2026-03-31T12:05:00+00:00"
    assert samples[0]["queues"][0]["queue_alert"] == "watch"
    assert alerts[0]["scope"] == "queue"
    assert alerts[0]["current_alert"] == "watch"
    assert alerts[1]["scope"] == "overall"
    assert alerts[1]["current_pressure"] == "elevated"


@pytest.mark.asyncio
async def test_record_queue_telemetry_posts_webhook_on_transition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = _FakeRedis()
    webhook_calls: list[tuple[str, dict[str, object], float]] = []

    class _FakeResponse:
        def raise_for_status(self) -> None:
            return None

    class _FakeAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> "_FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

        async def post(self, url: str, *, json: dict[str, object]) -> _FakeResponse:
            webhook_calls.append((url, json, self.timeout))
            return _FakeResponse()

    monkeypatch.setattr(telemetry.httpx, "AsyncClient", _FakeAsyncClient)
    monkeypatch.setattr(
        telemetry,
        "settings",
        SimpleNamespace(
            queue_telemetry_stream_key="jobradar:queue-telemetry",
            queue_telemetry_stream_maxlen=2000,
            queue_alert_stream_key="jobradar:queue-alerts",
            queue_alert_stream_maxlen=1000,
            queue_alert_state_key="jobradar:queue-alert-state",
            queue_alert_webhook_url="https://alerts.example.com/jobradar",
            queue_alert_webhook_timeout_seconds=7.5,
        ),
    )

    await telemetry.record_queue_telemetry(
        redis,
        {
            "arq:queue:ops": _snapshot(
                "arq:queue:ops",
                depth=0,
                pressure="nominal",
                age=0,
                alert="clear",
            )
        },
        captured_at="2026-03-31T12:00:00+00:00",
    )
    await telemetry.record_queue_telemetry(
        redis,
        {
            "arq:queue:ops": _snapshot(
                "arq:queue:ops",
                depth=16,
                pressure="saturated",
                age=900,
                alert="stalled",
            )
        },
        captured_at="2026-03-31T12:10:00+00:00",
    )

    assert webhook_calls
    assert webhook_calls[0][0] == "https://alerts.example.com/jobradar"
    assert webhook_calls[0][2] == 7.5
    assert webhook_calls[0][1]["current_alert"] in {"backlog", "stalled"}
