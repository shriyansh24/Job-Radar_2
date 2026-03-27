from __future__ import annotations

import argparse
import asyncio

import structlog
from sqlalchemy import text

from app.config import settings, validate_runtime_settings
from app.database import engine
from app.runtime.arq_worker import _healthcheck_key_for_role
from app.runtime.queue import shutdown_queue_pool, startup_queue_pool
from app.runtime.scheduler import _scheduler_healthcheck_key
from app.shared.logging import setup_logging

logger = structlog.get_logger()


async def _assert_database_ready() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def _assert_redis_health_key(key: str) -> None:
    queue_pool = await startup_queue_pool()
    await queue_pool.ping()
    value = await queue_pool.get(key)
    if not value:
        raise RuntimeError(f"Missing or expired runtime health key '{key}'.")


async def _check_scheduler() -> None:
    await _assert_database_ready()
    await _assert_redis_health_key(_scheduler_healthcheck_key())


async def _check_worker(role: str) -> None:
    await _assert_database_ready()
    await _assert_redis_health_key(_healthcheck_key_for_role(role))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run JobRadar runtime health checks.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    subparsers.add_parser("scheduler", help="Check scheduler DB/Redis heartbeat state.")

    worker_parser = subparsers.add_parser(
        "worker", help="Check a queue worker DB/Redis heartbeat state."
    )
    worker_parser.add_argument("role", choices=("scraping", "analysis", "ops"))

    return parser.parse_args()


async def _run_async(args: argparse.Namespace) -> int:
    try:
        if args.mode == "scheduler":
            await _check_scheduler()
            logger.info(
                "runtime_healthcheck_ok",
                mode="scheduler",
                health_check_key=_scheduler_healthcheck_key(),
            )
            return 0

        await _check_worker(args.role)
        logger.info(
            "runtime_healthcheck_ok",
            mode="worker",
            worker_role=args.role,
            health_check_key=_healthcheck_key_for_role(args.role),
        )
        return 0
    except Exception:
        logger.exception("runtime_healthcheck_failed", mode=args.mode)
        return 1
    finally:
        await shutdown_queue_pool()
        await engine.dispose()


def main() -> int:
    setup_logging(debug=settings.debug)
    validate_runtime_settings(settings)
    return asyncio.run(_run_async(_parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
