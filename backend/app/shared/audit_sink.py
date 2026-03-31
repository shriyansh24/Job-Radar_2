from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import structlog

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
    if value is None:
        return ""
    return str(value)


async def publish_auth_audit_event(event: str, **fields: object) -> None:
    if not settings.auth_audit_stream_enabled:
        return

    payload: dict[str, str] = {
        "event": event,
        "audit_stream": "auth",
        "timestamp": datetime.now(UTC).isoformat(),
    }
    for key, value in fields.items():
        serialized = _serialize_audit_value(value)
        if serialized:
            payload[key] = serialized

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
