from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections.abc import Awaitable, Callable

import structlog

from app.config import settings, validate_runtime_settings
from app.database import engine
from app.shared.logging import setup_logging
from app.workers.alert_worker import check_saved_search_alerts
from app.workers.auto_apply_worker import run_auto_apply_batch
from app.workers.enrichment_worker import (
    run_embedding_batch,
    run_enrichment_batch,
    run_tfidf_scoring,
)
from app.workers.maintenance_worker import run_cleanup, run_source_health_check
from app.workers.phase7a_worker import (
    run_followup_reminders,
    run_staleness_sweep,
)
from app.workers.phase7a_worker import (
    run_source_health_checks as run_phase7a_source_health,
)
from app.workers.scraping_worker import (
    run_career_page_scrape,
    run_scheduled_scrape,
    run_target_batch_job,
)

logger = structlog.get_logger()
WorkerJob = Callable[[], Awaitable[None]]


async def _run_scheduled_scrape() -> None:
    await run_scheduled_scrape(ctx={})


async def _run_career_page_scrape() -> None:
    await run_career_page_scrape(ctx={})


async def _run_enrichment_batch() -> None:
    await run_enrichment_batch(ctx={})


async def _run_embedding_batch() -> None:
    await run_embedding_batch(ctx={})


async def _run_tfidf_scoring() -> None:
    await run_tfidf_scoring(ctx={})


async def _run_cleanup() -> None:
    await run_cleanup(ctx={})


async def _run_source_health_check() -> None:
    await run_source_health_check(ctx={})


async def _run_auto_apply_batch() -> None:
    await run_auto_apply_batch(ctx={})


async def _run_target_batch_career_page() -> None:
    await run_target_batch_job(source_kind="career_page", batch_size=50)


async def _run_target_batch_watchlist() -> None:
    await run_target_batch_job(source_kind="watchlist", batch_size=25)


JOB_REGISTRY: dict[str, WorkerJob] = {
    "scheduled_scrape": _run_scheduled_scrape,
    "career_page_scrape": _run_career_page_scrape,
    "enrichment_batch": _run_enrichment_batch,
    "embedding_batch": _run_embedding_batch,
    "tfidf_scoring": _run_tfidf_scoring,
    "cleanup": _run_cleanup,
    "source_health": _run_source_health_check,
    "auto_apply_batch": _run_auto_apply_batch,
    "saved_search_alerts": check_saved_search_alerts,
    "staleness_sweep": run_staleness_sweep,
    "phase7a_source_health": run_phase7a_source_health,
    "followup_reminders": run_followup_reminders,
    "target_batch_career_page": _run_target_batch_career_page,
    "target_batch_watchlist": _run_target_batch_watchlist,
}


def get_registered_job_ids() -> list[str]:
    return sorted(JOB_REGISTRY)


async def run_registered_job(job_name: str) -> None:
    try:
        job = JOB_REGISTRY[job_name]
    except KeyError as exc:
        raise ValueError(f"Unknown worker job '{job_name}'") from exc

    setup_logging(debug=settings.debug)
    validate_runtime_settings(settings)
    logger.info("worker_starting", app=settings.app_name, job_name=job_name, pid=os.getpid())

    try:
        await job()
    except Exception:
        logger.exception("worker_failed", job_name=job_name, pid=os.getpid())
        raise
    finally:
        await engine.dispose()

    logger.info("worker_completed", job_name=job_name, pid=os.getpid())


async def spawn_worker_process(job_name: str) -> None:
    logger.info("worker_subprocess_starting", job_name=job_name)
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "app.runtime.worker",
        job_name,
    )
    return_code = await process.wait()
    if return_code != 0:
        raise RuntimeError(f"worker process for '{job_name}' exited with code {return_code}")
    logger.info("worker_subprocess_completed", job_name=job_name, return_code=return_code)


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
