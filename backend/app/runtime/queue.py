from __future__ import annotations

import asyncio
from urllib.parse import unquote, urlparse

import structlog
from arq.connections import ArqRedis, RedisSettings, create_pool

from app.config import settings
from app.runtime.job_registry import get_registered_job

logger = structlog.get_logger()

_queue_pool: ArqRedis | None = None
_queue_pool_lock = asyncio.Lock()


def build_redis_settings() -> RedisSettings:
    parsed = urlparse(settings.redis_url)
    if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
        raise RuntimeError(
            "JR_REDIS_URL must use redis:// or rediss:// with an explicit host."
        )

    database = int((parsed.path or "/0").lstrip("/") or "0")
    ssl_enabled = settings.redis_use_tls or parsed.scheme == "rediss"

    return RedisSettings(
        host=parsed.hostname,
        port=parsed.port or 6379,
        database=database,
        username=unquote(parsed.username) if parsed.username else None,
        password=unquote(parsed.password) if parsed.password else None,
        ssl=ssl_enabled,
    )


async def startup_queue_pool() -> ArqRedis:
    global _queue_pool
    async with _queue_pool_lock:
        if _queue_pool is None:
            redis_settings = build_redis_settings()
            _queue_pool = await create_pool(redis_settings)
            await _queue_pool.ping()
            logger.info(
                "queue_pool_ready",
                redis_host=redis_settings.host,
                redis_port=redis_settings.port,
                redis_database=redis_settings.database,
                redis_tls=redis_settings.ssl,
            )
    return _queue_pool


async def get_queue_pool() -> ArqRedis:
    if _queue_pool is not None:
        return _queue_pool
    return await startup_queue_pool()


async def shutdown_queue_pool() -> None:
    global _queue_pool
    async with _queue_pool_lock:
        if _queue_pool is not None:
            await _queue_pool.close(close_connection_pool=True)
            _queue_pool = None
            logger.info("queue_pool_stopped")


async def enqueue_registered_job(job_name: str) -> str | None:
    job = get_registered_job(job_name)
    queue_pool = await get_queue_pool()
    job_ref = await queue_pool.enqueue_job(job.name, _queue_name=job.queue_name)
    enqueued_job_id = getattr(job_ref, "job_id", None)
    logger.info(
        "scheduler_job_enqueued",
        job_name=job.name,
        queue_name=job.queue_name,
        enqueued_job_id=enqueued_job_id,
    )
    return enqueued_job_id
