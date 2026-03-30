from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from typing import Any, cast

import structlog
from arq.worker import Worker, func
from sqlalchemy import text

from app.config import settings, validate_runtime_settings
from app.database import engine
from app.runtime.job_registry import (
    ANALYSIS_QUEUE,
    OPS_QUEUE,
    SCRAPING_QUEUE,
    get_registered_jobs,
)
from app.runtime.queue import build_redis_settings, capture_queue_snapshot
from app.runtime.worker_metrics import sync_worker_queue_metrics
from app.shared.logging import setup_logging

logger = structlog.get_logger()

ROLE_TO_QUEUE = {
    "scraping": SCRAPING_QUEUE,
    "analysis": ANALYSIS_QUEUE,
    "ops": OPS_QUEUE,
}

ROLE_TO_MAX_JOBS = {
    "scraping": 2,
    "analysis": 4,
    "ops": 1,
}

ROLE_TO_QUEUE_READ_LIMIT = {
    "scraping": 2,
    "analysis": 4,
    "ops": 1,
}

ROLE_TO_HEALTHCHECK_KEY = {
    "scraping": "jobradar:worker-health:scraping",
    "analysis": "jobradar:worker-health:analysis",
    "ops": "jobradar:worker-health:ops",
}

DEFAULT_WORKER_HEALTH_INTERVAL_SECONDS = 15


def _ready_marker_for_role(role: str) -> Path:
    env_marker = os.getenv("JR_WORKER_READY_MARKER")
    if env_marker:
        return Path(env_marker)
    return Path(tempfile.gettempdir()) / f"jobradar-worker-{role}.ready"


def _healthcheck_key_for_role(role: str) -> str:
    return os.getenv("JR_WORKER_HEALTHCHECK_KEY", ROLE_TO_HEALTHCHECK_KEY[role])


def _healthcheck_interval_seconds() -> int:
    return int(
        os.getenv(
            "JR_WORKER_HEALTHCHECK_INTERVAL_SECONDS",
            str(DEFAULT_WORKER_HEALTH_INTERVAL_SECONDS),
        )
    )


def _mark_ready(role: str) -> Path:
    ready_marker = _ready_marker_for_role(role)
    ready_marker.parent.mkdir(parents=True, exist_ok=True)
    ready_marker.write_text("ready\n", encoding="utf-8")
    return ready_marker


def _clear_ready(role: str) -> None:
    _ready_marker_for_role(role).unlink(missing_ok=True)


async def _on_startup(ctx: dict[str, object]) -> None:
    role = str(ctx["worker_role"])
    queue_name = str(ctx["queue_name"])

    setup_logging(debug=settings.debug)
    validate_runtime_settings(settings)

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    redis = cast(Any, ctx.get("redis"))
    if redis is not None:
        await redis.ping()
        queue_snapshot = await capture_queue_snapshot(queue_name, redis)
        await sync_worker_queue_metrics(
            redis,
            role=role,
            snapshot=queue_snapshot,
            health_interval_seconds=int(cast(int | str, ctx["health_check_interval_seconds"])),
        )
    else:
        queue_snapshot = None

    ready_marker = _mark_ready(role)
    logger.info(
        "arq_worker_started",
        worker_role=role,
        queue_name=queue_name,
        job_count=ctx["job_count"],
        job_names=ctx["job_names"],
        max_jobs=ctx["max_jobs"],
        queue_read_limit=ctx["queue_read_limit"],
        health_check_key=ctx["health_check_key"],
        health_check_interval_seconds=ctx["health_check_interval_seconds"],
        queue_depth=queue_snapshot.queue_depth if queue_snapshot is not None else None,
        queue_pressure=queue_snapshot.queue_pressure if queue_snapshot is not None else None,
        oldest_job_age_seconds=(
            queue_snapshot.oldest_job_age_seconds if queue_snapshot is not None else None
        ),
        queue_alert=queue_snapshot.queue_alert if queue_snapshot is not None else None,
        ready_marker=str(ready_marker),
    )


async def _on_shutdown(ctx: dict[str, object]) -> None:
    role = str(ctx["worker_role"])
    queue_name = str(ctx["queue_name"])
    _clear_ready(role)
    await engine.dispose()
    logger.info(
        "arq_worker_stopped",
        worker_role=role,
        queue_name=queue_name,
        health_check_key=ctx["health_check_key"],
    )


async def _on_job_start(ctx: dict[str, object]) -> None:
    redis = cast(Any, ctx.get("redis"))
    queue_name = str(ctx["queue_name"])
    queue_snapshot = await capture_queue_snapshot(queue_name, redis) if redis is not None else None
    if queue_snapshot is not None:
        await sync_worker_queue_metrics(
            redis,
            role=str(ctx["worker_role"]),
            snapshot=queue_snapshot,
            health_interval_seconds=int(cast(int | str, ctx["health_check_interval_seconds"])),
        )
    queue_job_id = ctx["job_id"]
    logger.info(
        "arq_worker_job_starting",
        worker_role=ctx["worker_role"],
        queue_name=queue_name,
        job_id=queue_job_id,
        queue_job_id=queue_job_id,
        queue_correlation_id=queue_job_id,
        job_try=ctx["job_try"],
        queue_depth=queue_snapshot.queue_depth if queue_snapshot is not None else None,
        queue_pressure=queue_snapshot.queue_pressure if queue_snapshot is not None else None,
        oldest_job_age_seconds=(
            queue_snapshot.oldest_job_age_seconds if queue_snapshot is not None else None
        ),
        queue_alert=queue_snapshot.queue_alert if queue_snapshot is not None else None,
    )


async def _on_job_end(ctx: dict[str, object]) -> None:
    redis = cast(Any, ctx.get("redis"))
    queue_name = str(ctx["queue_name"])
    queue_snapshot = await capture_queue_snapshot(queue_name, redis) if redis is not None else None
    if queue_snapshot is not None:
        await sync_worker_queue_metrics(
            redis,
            role=str(ctx["worker_role"]),
            snapshot=queue_snapshot,
            health_interval_seconds=int(cast(int | str, ctx["health_check_interval_seconds"])),
        )
    queue_job_id = ctx["job_id"]
    logger.info(
        "arq_worker_job_finished",
        worker_role=ctx["worker_role"],
        queue_name=queue_name,
        job_id=queue_job_id,
        queue_job_id=queue_job_id,
        queue_correlation_id=queue_job_id,
        job_try=ctx["job_try"],
        queue_depth=queue_snapshot.queue_depth if queue_snapshot is not None else None,
        queue_pressure=queue_snapshot.queue_pressure if queue_snapshot is not None else None,
        oldest_job_age_seconds=(
            queue_snapshot.oldest_job_age_seconds if queue_snapshot is not None else None
        ),
        queue_alert=queue_snapshot.queue_alert if queue_snapshot is not None else None,
    )


def build_worker(role: str) -> Worker:
    try:
        queue_name = ROLE_TO_QUEUE[role]
    except KeyError as exc:
        raise ValueError(f"Unknown worker role '{role}'") from exc

    registered_jobs = get_registered_jobs(queue_name=queue_name)
    if not registered_jobs:
        raise RuntimeError(f"No registered jobs exist for queue '{queue_name}'.")

    functions = [
        func(
            cast(Any, job.runner),
            name=job.name,
            timeout=job.timeout_seconds,
            max_tries=job.max_tries,
        )
        for job in registered_jobs
    ]

    max_jobs = ROLE_TO_MAX_JOBS[role]
    queue_read_limit = ROLE_TO_QUEUE_READ_LIMIT[role]
    health_check_key = _healthcheck_key_for_role(role)
    health_check_interval_seconds = _healthcheck_interval_seconds()

    return Worker(
        functions=functions,
        queue_name=queue_name,
        redis_settings=build_redis_settings(),
        on_startup=_on_startup,
        on_shutdown=_on_shutdown,
        on_job_start=_on_job_start,
        on_job_end=_on_job_end,
        ctx={
            "worker_role": role,
            "queue_name": queue_name,
            "job_count": len(registered_jobs),
            "job_names": [job.name for job in registered_jobs],
            "max_jobs": max_jobs,
            "queue_read_limit": queue_read_limit,
            "health_check_key": health_check_key,
            "health_check_interval_seconds": health_check_interval_seconds,
        },
        max_jobs=max_jobs,
        queue_read_limit=queue_read_limit,
        health_check_key=health_check_key,
        health_check_interval=health_check_interval_seconds,
        job_completion_wait=5,
        retry_jobs=True,
        allow_abort_jobs=False,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an ARQ worker queue for JobRadar.")
    parser.add_argument(
        "worker_role",
        choices=sorted(ROLE_TO_QUEUE),
        help="Queue family to consume.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    setup_logging(debug=settings.debug)
    validate_runtime_settings(settings)
    logger.info("arq_worker_booting", worker_role=args.worker_role)

    worker = build_worker(args.worker_role)
    try:
        worker.run()
    except KeyboardInterrupt:
        logger.info("arq_worker_interrupted", worker_role=args.worker_role)
        return 0
    except Exception:
        logger.exception("arq_worker_failed", worker_role=args.worker_role)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
