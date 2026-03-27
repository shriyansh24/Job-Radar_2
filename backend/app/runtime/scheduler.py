from __future__ import annotations

import asyncio
import os
import signal
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import structlog
from sqlalchemy import text

from app.config import settings, validate_runtime_settings
from app.database import engine
from app.runtime.queue import get_queue_depths, shutdown_queue_pool, startup_queue_pool
from app.shared.logging import setup_logging
from app.workers.scheduler import create_scheduler

logger = structlog.get_logger()
DEFAULT_SCHEDULER_HEALTHCHECK_KEY = "jobradar:scheduler-health"
DEFAULT_SCHEDULER_HEALTHCHECK_INTERVAL_SECONDS = 15
READY_MARKER = Path(
    os.getenv(
        "JR_SCHEDULER_READY_MARKER",
        os.getenv(
            "JR_SCHEDULER_READY_FILE",
            str(Path(tempfile.gettempdir()) / "jobradar-scheduler.ready"),
        ),
    )
)


def _scheduler_healthcheck_key() -> str:
    return os.getenv("JR_SCHEDULER_HEALTHCHECK_KEY", DEFAULT_SCHEDULER_HEALTHCHECK_KEY)


def _scheduler_healthcheck_interval_seconds() -> int:
    return int(
        os.getenv(
            "JR_SCHEDULER_HEALTHCHECK_INTERVAL_SECONDS",
            str(DEFAULT_SCHEDULER_HEALTHCHECK_INTERVAL_SECONDS),
        )
    )


def _mark_ready() -> None:
    READY_MARKER.parent.mkdir(parents=True, exist_ok=True)
    READY_MARKER.write_text("ready\n", encoding="utf-8")


def _clear_ready() -> None:
    READY_MARKER.unlink(missing_ok=True)


async def _record_health() -> None:
    queue_pool = await startup_queue_pool()
    queue_depths = await get_queue_depths(queue_pool)
    payload = " ".join(
        [
            f"{datetime.now(UTC).isoformat()}",
            "scheduler_running=1",
            *[f"{queue_name}={queue_depth}" for queue_name, queue_depth in queue_depths.items()],
        ]
    )
    ttl_ms = (_scheduler_healthcheck_interval_seconds() + 5) * 1000
    await queue_pool.psetex(_scheduler_healthcheck_key(), ttl_ms, payload.encode())


async def _clear_health() -> None:
    queue_pool = await startup_queue_pool()
    await queue_pool.delete(_scheduler_healthcheck_key())


async def _health_loop(stop_event: asyncio.Event) -> None:
    interval_seconds = _scheduler_healthcheck_interval_seconds()
    while not stop_event.is_set():
        await _record_health()
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except TimeoutError:
            continue


async def _verify_dependencies() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    queue_pool = await startup_queue_pool()
    await queue_pool.ping()

    logger.info("scheduler_dependencies_ready", database="connected", redis="connected")


def _install_signal_handlers(stop_event: asyncio.Event) -> None:
    def _request_shutdown(signum: int, _frame: object) -> None:
        logger.info("scheduler_shutdown_requested", signal=signal.Signals(signum).name)
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _request_shutdown)


async def run() -> int:
    setup_logging(debug=settings.debug)
    validate_runtime_settings(settings)
    logger.info("scheduler_starting", app=settings.app_name)

    scheduler = create_scheduler()

    try:
        await _verify_dependencies()
        scheduler.start()
    except Exception:
        logger.exception("scheduler_startup_failed")
        await shutdown_queue_pool()
        await engine.dispose()
        return 1

    job_ids = [job.id for job in scheduler.get_jobs()]
    logger.info("scheduler_started", job_count=len(job_ids), job_ids=job_ids)
    _mark_ready()
    await _record_health()
    logger.info(
        "scheduler_ready",
        marker=str(READY_MARKER),
        health_check_key=_scheduler_healthcheck_key(),
        health_check_interval_seconds=_scheduler_healthcheck_interval_seconds(),
    )

    stop_event = asyncio.Event()
    _install_signal_handlers(stop_event)
    health_task = asyncio.create_task(_health_loop(stop_event))

    try:
        await stop_event.wait()
    finally:
        health_task.cancel()
        await asyncio.gather(health_task, return_exceptions=True)
        _clear_ready()
        await _clear_health()
        scheduler.shutdown(wait=False)
        await shutdown_queue_pool()
        await engine.dispose()
        logger.info("scheduler_stopped")

    return 0


def main() -> int:
    try:
        return asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("scheduler_interrupted")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
