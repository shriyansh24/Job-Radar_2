from __future__ import annotations

import argparse
import asyncio
import os
import sys

import structlog

from app.config import settings, validate_runtime_settings
from app.database import engine
from app.runtime.job_registry import get_registered_job, get_registered_job_ids
from app.shared.logging import setup_logging

logger = structlog.get_logger()


async def run_registered_job(job_name: str) -> None:
    job = get_registered_job(job_name)

    setup_logging(debug=settings.debug)
    validate_runtime_settings(settings)
    logger.info(
        "manual_worker_starting",
        app=settings.app_name,
        job_name=job_name,
        queue_name=job.queue_name,
        pid=os.getpid(),
    )

    try:
        await job.runner({})
    except Exception:
        logger.exception("manual_worker_failed", job_name=job_name, pid=os.getpid())
        raise
    finally:
        await engine.dispose()

    logger.info("manual_worker_completed", job_name=job_name, pid=os.getpid())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single JobRadar worker job.")
    parser.add_argument("job_name", nargs="?", help="Registered worker job to execute")
    parser.add_argument(
        "--list-jobs",
        action="store_true",
        help="Print the registered worker job names and exit",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.list_jobs:
        for job_name in get_registered_job_ids():
            print(job_name)
        return 0
    if not args.job_name:
        print("A worker job name is required.", file=sys.stderr)
        return 2

    try:
        asyncio.run(run_registered_job(args.job_name))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
