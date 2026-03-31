from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arq.connections import ArqRedis
from structlog.contextvars import get_contextvars

from app.config import settings
from app.runtime.queue import get_queue_pool

logger = structlog.get_logger()


def _serialize_audit_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(item) for item in value if item is not None)
    if value is None:
        return ""
    return str(value)


def _build_auth_audit_payload(event: str, **fields: object) -> dict[str, str]:
    payload: dict[str, str] = {
        "event": event,
        "audit_stream": "auth",
        "timestamp": datetime.now(UTC).isoformat(),
    }
    request_id = get_contextvars().get("request_id")
    if request_id is not None:
        payload["request_id"] = str(request_id)
    for key, value in fields.items():
        serialized = _serialize_audit_value(value)
        if serialized:
            payload[key] = serialized
    return payload


async def publish_auth_audit_event(event: str, **fields: object) -> None:
    if not settings.auth_audit_stream_enabled:
        return

    payload = _build_auth_audit_payload(event, **fields)

    try:
        queue_pool = await get_queue_pool()
        await cast(Any, queue_pool).xadd(
            settings.auth_audit_stream_key,
            payload,
            maxlen=settings.auth_audit_stream_maxlen,
            approximate=True,
        )
    except Exception:
        logger.warning(
            "auth_audit_sink_failed",
            audit_event=event,
            sink_key=settings.auth_audit_stream_key,
        )


def _log_audit_task_failure(task: asyncio.Task[None], *, event: str) -> None:
    try:
        task.result()
    except Exception:
        logger.warning("auth_audit_task_failed", audit_event=event)


def emit_auth_audit_event(event: str, **fields: object) -> None:
    if not settings.auth_audit_stream_enabled:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    task = loop.create_task(publish_auth_audit_event(event, **fields))
    task.add_done_callback(lambda completed: _log_audit_task_failure(completed, event=event))


async def read_auth_audit_events(
    limit: int = 20,
    *,
    queue_pool: ArqRedis | None = None,
) -> list[dict[str, object]]:
    if not settings.auth_audit_stream_enabled:
        return []

    active_queue_pool = queue_pool or await get_queue_pool()
    raw_entries = cast(
        list[tuple[object, dict[object, object]]],
        await cast(Any, active_queue_pool).xrevrange(
            settings.auth_audit_stream_key,
            "+",
            "-",
            count=limit,
        ),
    )
    entries: list[dict[str, object]] = []
    for raw_stream_id, raw_payload in raw_entries:
        payload = {
            (
                key.decode() if isinstance(key, bytes) else str(key)
            ): value.decode() if isinstance(value, bytes) else str(value)
            for key, value in raw_payload.items()
        }
        entries.append(
            {
                "stream_id": raw_stream_id.decode()
                if isinstance(raw_stream_id, bytes)
                else str(raw_stream_id),
                **payload,
            }
        )
    return entries
