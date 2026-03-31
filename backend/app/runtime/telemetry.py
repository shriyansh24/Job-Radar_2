from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import urlparse

import httpx
import structlog
from arq.connections import ArqRedis

from app.config import settings
from app.runtime.queue import (
    QueueSnapshot,
    derive_overall_alert,
    derive_overall_pressure,
    get_queue_pool,
)

logger = structlog.get_logger()


def _serialize_stream_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _decode_stream_value(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode()
    return str(value)


def _queue_rows(snapshots: dict[str, QueueSnapshot]) -> list[dict[str, object]]:
    return [
        {
            "queue_name": snapshot.queue_name,
            "queue_depth": snapshot.queue_depth,
            "queue_pressure": snapshot.queue_pressure,
            "oldest_job_age_seconds": snapshot.oldest_job_age_seconds,
            "queue_alert": snapshot.queue_alert,
        }
        for snapshot in snapshots.values()
    ]


def _current_state_mapping(snapshots: dict[str, QueueSnapshot]) -> dict[str, str]:
    queue_pressures = {
        queue_name: snapshot.queue_pressure for queue_name, snapshot in snapshots.items()
    }
    queue_alerts = {queue_name: snapshot.queue_alert for queue_name, snapshot in snapshots.items()}
    state = {
        "overall_pressure": derive_overall_pressure(queue_pressures),
        "overall_alert": derive_overall_alert(queue_alerts),
    }
    for queue_name, snapshot in snapshots.items():
        state[f"{queue_name}:pressure"] = snapshot.queue_pressure
        state[f"{queue_name}:alert"] = snapshot.queue_alert
    return state


async def _read_current_state(redis: ArqRedis) -> dict[str, str]:
    raw_state = cast(
        dict[object, object],
        await cast(Any, redis).hgetall(settings.queue_alert_state_key),
    )
    return {
        _decode_stream_value(key): _decode_stream_value(value)
        for key, value in raw_state.items()
    }


async def _post_alert_webhook(payload: dict[str, object]) -> None:
    if not settings.queue_alert_webhook_url.strip():
        return

    try:
        async with httpx.AsyncClient(
            timeout=settings.queue_alert_webhook_timeout_seconds
        ) as client:
            response = await client.post(settings.queue_alert_webhook_url, json=payload)
            response.raise_for_status()
    except Exception:
        logger.warning(
            "queue_alert_webhook_failed",
            webhook_host=urlparse(settings.queue_alert_webhook_url).netloc,
            queue_name=payload.get("queue_name"),
            current_alert=payload.get("current_alert"),
        )


async def _publish_alert_transition(
    redis: ArqRedis,
    payload: dict[str, object],
) -> None:
    stream_payload: dict[str, str] = {}
    for key, value in payload.items():
        serialized = _serialize_stream_value(value)
        if serialized:
            stream_payload[key] = serialized
    await cast(Any, redis).xadd(
        settings.queue_alert_stream_key,
        stream_payload,
        maxlen=settings.queue_alert_stream_maxlen,
        approximate=True,
    )
    await _post_alert_webhook(payload)


async def record_queue_telemetry(
    redis: ArqRedis,
    snapshots: dict[str, QueueSnapshot],
    *,
    captured_at: str | None = None,
) -> None:
    if not snapshots:
        return

    captured_at_value = captured_at or datetime.now(UTC).isoformat()
    queue_rows = _queue_rows(snapshots)
    queue_pressures = {
        queue_name: snapshot.queue_pressure for queue_name, snapshot in snapshots.items()
    }
    queue_alerts = {queue_name: snapshot.queue_alert for queue_name, snapshot in snapshots.items()}
    telemetry_payload = {
        "captured_at": captured_at_value,
        "overall_pressure": derive_overall_pressure(queue_pressures),
        "overall_alert": derive_overall_alert(queue_alerts),
        "queues_json": json.dumps(queue_rows, separators=(",", ":"), sort_keys=True),
    }
    await cast(Any, redis).xadd(
        settings.queue_telemetry_stream_key,
        telemetry_payload,
        maxlen=settings.queue_telemetry_stream_maxlen,
        approximate=True,
    )

    previous_state = await _read_current_state(redis)
    current_state = _current_state_mapping(snapshots)

    if previous_state:
        overall_payload = {
            "captured_at": captured_at_value,
            "scope": "overall",
            "queue_name": "",
            "previous_pressure": previous_state.get("overall_pressure", ""),
            "current_pressure": current_state["overall_pressure"],
            "previous_alert": previous_state.get("overall_alert", ""),
            "current_alert": current_state["overall_alert"],
            "queue_depth": sum(snapshot.queue_depth for snapshot in snapshots.values()),
            "oldest_job_age_seconds": max(
                (snapshot.oldest_job_age_seconds for snapshot in snapshots.values()),
                default=0,
            ),
        }
        if (
            overall_payload["previous_pressure"] != overall_payload["current_pressure"]
            or overall_payload["previous_alert"] != overall_payload["current_alert"]
        ):
            await _publish_alert_transition(redis, overall_payload)

        for snapshot in snapshots.values():
            previous_pressure = previous_state.get(f"{snapshot.queue_name}:pressure", "")
            previous_alert = previous_state.get(f"{snapshot.queue_name}:alert", "")
            if (
                previous_pressure == snapshot.queue_pressure
                and previous_alert == snapshot.queue_alert
            ):
                continue
            await _publish_alert_transition(
                redis,
                {
                    "captured_at": captured_at_value,
                    "scope": "queue",
                    "queue_name": snapshot.queue_name,
                    "previous_pressure": previous_pressure,
                    "current_pressure": snapshot.queue_pressure,
                    "previous_alert": previous_alert,
                    "current_alert": snapshot.queue_alert,
                    "queue_depth": snapshot.queue_depth,
                    "oldest_job_age_seconds": snapshot.oldest_job_age_seconds,
                },
            )

    await cast(Any, redis).hset(settings.queue_alert_state_key, mapping=current_state)


def _parse_json_field(raw_value: str) -> object:
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value


async def _read_stream(
    redis: ArqRedis,
    *,
    key: str,
    limit: int,
) -> list[dict[str, object]]:
    raw_entries = cast(
        list[tuple[object, dict[object, object]]],
        await cast(Any, redis).xrevrange(key, "+", "-", count=limit),
    )
    entries: list[dict[str, object]] = []
    for raw_stream_id, raw_payload in raw_entries:
        payload = {
            _decode_stream_value(field): _decode_stream_value(value)
            for field, value in raw_payload.items()
        }
        entries.append(
            {
                "stream_id": _decode_stream_value(raw_stream_id),
                **payload,
            }
        )
    return entries


async def read_queue_telemetry(
    limit: int = 12,
    *,
    queue_pool: ArqRedis | None = None,
) -> list[dict[str, object]]:
    redis = queue_pool or await get_queue_pool()
    entries = await _read_stream(redis, key=settings.queue_telemetry_stream_key, limit=limit)
    for entry in entries:
        raw_queues = entry.get("queues_json")
        if isinstance(raw_queues, str):
            parsed = _parse_json_field(raw_queues)
            entry["queues"] = parsed if isinstance(parsed, list) else []
        entry.pop("queues_json", None)
    return entries


async def read_queue_alerts(
    limit: int = 20,
    *,
    queue_pool: ArqRedis | None = None,
) -> list[dict[str, object]]:
    redis = queue_pool or await get_queue_pool()
    entries = await _read_stream(redis, key=settings.queue_alert_stream_key, limit=limit)
    for entry in entries:
        for numeric_field in ("queue_depth", "oldest_job_age_seconds"):
            raw_value = entry.get(numeric_field)
            if isinstance(raw_value, str) and raw_value.isdigit():
                entry[numeric_field] = int(raw_value)
    return entries
