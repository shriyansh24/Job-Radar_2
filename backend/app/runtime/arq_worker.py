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
from app.runtime.queue import build_redis_settings
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


def _ready_marker_for_role(role: str) -> Path:
    env_marker = os.getenv("JR_WORKER_READY_MARKER")
    if env_marker:
        return Path(env_marker)
    return Path(tempfile.gettempdir()) / f"jobradar-worker-{role}.ready"


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

    ready_marker = _mark_ready(role)
    logger.info(
        "arq_worker_started",
        worker_role=role,
        queue_name=queue_name,
        ready_marker=str(ready_marker),
    )


async def _on_shutdown(ctx: dict[str, object]) -> None:
    role = str(ctx["worker_role"])
    queue_name = str(ctx["queue_name"])
    _clear_ready(role)
    await engine.dispose()
    logger.info("arq_worker_stopped", worker_role=role, queue_name=queue_name)


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

    return Worker(
        functions=functions,
        queue_name=queue_name,
        redis_settings=build_redis_settings(),
        on_startup=_on_startup,
        on_shutdown=_on_shutdown,
        ctx={"worker_role": role, "queue_name": queue_name},
        max_jobs=ROLE_TO_MAX_JOBS[role],
        job_completion_wait=5,
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
