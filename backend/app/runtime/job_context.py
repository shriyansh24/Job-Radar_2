from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, cast

JOB_METADATA_KEY_PREFIX = "jobradar:queue-job-metadata"
JOB_METADATA_TTL_SECONDS = 3600
QUEUE_CORRELATION_METADATA_FIELD = "_queue_correlation_id"


def build_job_metadata_key(job_id: str) -> str:
    return f"{JOB_METADATA_KEY_PREFIX}:{job_id}"


def build_job_metadata_payload(
    *,
    correlation_id: str | None,
    job_kwargs: dict[str, object],
) -> dict[str, object]:
    payload = dict(job_kwargs)
    if correlation_id is not None:
        payload[QUEUE_CORRELATION_METADATA_FIELD] = correlation_id
    return payload


async def store_job_metadata(
    redis: Any,
    *,
    job_id: str,
    correlation_id: str | None,
    job_kwargs: dict[str, object],
) -> None:
    payload = build_job_metadata_payload(
        correlation_id=correlation_id,
        job_kwargs=job_kwargs,
    )
    if not payload:
        return
    await cast(Any, redis).set(
        build_job_metadata_key(job_id),
        json.dumps(payload, separators=(",", ":"), sort_keys=True),
        ex=JOB_METADATA_TTL_SECONDS,
    )


async def load_job_metadata(
    ctx: Mapping[str, Any] | None = None,
    *,
    logger: Any | None = None,
    invalid_event: str = "queue_job_metadata_invalid",
    unavailable_event: str = "queue_job_metadata_unavailable",
) -> dict[str, Any]:
    context = dict(ctx or {})
    redis = cast(Any, context.get("redis"))
    queue_job_id = context.get("job_id")
    if redis is None or not isinstance(queue_job_id, str):
        return {}

    try:
        raw_metadata = await redis.get(build_job_metadata_key(queue_job_id))
    except Exception:
        if logger is not None:
            logger.warning(unavailable_event, queue_job_id=queue_job_id)
        return {}
    if raw_metadata is None:
        return {}
    if isinstance(raw_metadata, bytes):
        raw_metadata = raw_metadata.decode()
    if not isinstance(raw_metadata, str):
        return {}
    try:
        parsed = json.loads(raw_metadata)
    except json.JSONDecodeError:
        if logger is not None:
            logger.warning(invalid_event, queue_job_id=queue_job_id)
        return {}
    return parsed if isinstance(parsed, dict) else {}


async def clear_job_metadata(ctx: Mapping[str, Any] | None = None) -> None:
    context = dict(ctx or {})
    redis = cast(Any, context.get("redis"))
    queue_job_id = context.get("job_id")
    if redis is None or not isinstance(queue_job_id, str):
        return
    await redis.delete(build_job_metadata_key(queue_job_id))


async def resolve_queue_correlation_id(
    ctx: Mapping[str, Any] | None = None,
    *,
    logger: Any | None = None,
) -> str | None:
    context = dict(ctx or {})
    explicit_correlation_id = context.get("queue_correlation_id")
    if isinstance(explicit_correlation_id, str) and explicit_correlation_id.strip():
        return explicit_correlation_id

    metadata = await load_job_metadata(context, logger=logger)
    metadata_correlation_id = metadata.get(QUEUE_CORRELATION_METADATA_FIELD)
    if isinstance(metadata_correlation_id, str) and metadata_correlation_id.strip():
        return metadata_correlation_id

    queue_job_id = context.get("job_id")
    if isinstance(queue_job_id, str) and queue_job_id.strip():
        return queue_job_id
    return None
