from __future__ import annotations

import argparse
import asyncio
from typing import Any, cast

import structlog
from sqlalchemy import text

from app.config import settings, validate_runtime_settings
from app.database import engine
from app.runtime.arq_worker import _healthcheck_key_for_role
from app.runtime.job_registry import get_queue_names
from app.runtime.queue import (
    VALID_QUEUE_ALERTS,
    VALID_QUEUE_PRESSURES,
    classify_queue_alert,
    derive_overall_alert,
    derive_overall_pressure,
    shutdown_queue_pool,
    startup_queue_pool,
)
from app.runtime.scheduler import _scheduler_healthcheck_key
from app.runtime.worker_metrics import COUNTER_FIELDS, worker_metrics_key
from app.shared.logging import setup_logging

logger = structlog.get_logger()


def _parse_health_fields(raw_value: bytes | str) -> dict[str, str]:
    text_value = raw_value.decode() if isinstance(raw_value, bytes) else raw_value
    fields: dict[str, str] = {}
    for token in text_value.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        fields[key] = value
    return fields


def _parse_non_negative_int(value: str, *, field_name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(
            f"Runtime health payload field '{field_name}' must be an integer."
        ) from exc
    if parsed < 0:
        raise RuntimeError(f"Runtime health payload field '{field_name}' cannot be negative.")
    return parsed


async def _assert_database_ready() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def _assert_redis_health_key(key: str) -> bytes | str:
    queue_pool = await startup_queue_pool()
    await queue_pool.ping()
    value = cast(bytes | str | None, await queue_pool.get(key))
    if not value:
        raise RuntimeError(f"Missing or expired runtime health key '{key}'.")
    return value


async def _assert_redis_hash_fields(key: str) -> dict[str, str]:
    queue_pool = await startup_queue_pool()
    await queue_pool.ping()
    raw_fields = cast(dict[object, object], await cast(Any, queue_pool).hgetall(key))
    if not raw_fields:
        raise RuntimeError(f"Missing or expired runtime health hash '{key}'.")

    fields: dict[str, str] = {}
    for raw_key, raw_value in raw_fields.items():
        key_text = raw_key.decode() if isinstance(raw_key, bytes) else str(raw_key)
        value_text = raw_value.decode() if isinstance(raw_value, bytes) else str(raw_value)
        fields[key_text] = value_text
    return fields


async def _check_scheduler() -> None:
    await _assert_database_ready()
    fields = _parse_health_fields(await _assert_redis_health_key(_scheduler_healthcheck_key()))
    if fields.get("scheduler_running") != "1":
        raise RuntimeError("Scheduler health payload is missing scheduler_running=1.")
    overall_pressure = fields.get("overall_pressure")
    if overall_pressure is None:
        raise RuntimeError("Scheduler health payload is missing overall_pressure.")
    if overall_pressure not in VALID_QUEUE_PRESSURES:
        raise RuntimeError("Scheduler health payload has invalid overall_pressure.")
    overall_alert = fields.get("overall_alert")
    if overall_alert is None:
        raise RuntimeError("Scheduler health payload is missing overall_alert.")
    if overall_alert not in VALID_QUEUE_ALERTS:
        raise RuntimeError("Scheduler health payload has invalid overall_alert.")

    queue_pressures: dict[str, str] = {}
    queue_alerts: dict[str, str] = {}
    for queue_name in get_queue_names():
        if queue_name not in fields:
            raise RuntimeError(f"Scheduler health payload is missing depth for '{queue_name}'.")
        _parse_non_negative_int(fields[queue_name], field_name=queue_name)

        pressure_field = f"{queue_name}.pressure"
        queue_pressure = fields.get(pressure_field)
        if queue_pressure is None:
            raise RuntimeError(f"Scheduler health payload is missing pressure for '{queue_name}'.")
        if queue_pressure not in VALID_QUEUE_PRESSURES:
            raise RuntimeError(
                f"Scheduler health payload has invalid pressure for '{queue_name}'."
            )
        queue_pressures[queue_name] = queue_pressure

        oldest_age_field = f"{queue_name}.oldest_job_age_seconds"
        oldest_job_age_seconds = fields.get(oldest_age_field)
        if oldest_job_age_seconds is None:
            raise RuntimeError(
                f"Scheduler health payload is missing oldest age for '{queue_name}'."
            )
        parsed_oldest_job_age_seconds = _parse_non_negative_int(
            oldest_job_age_seconds,
            field_name=oldest_age_field,
        )

        alert_field = f"{queue_name}.alert"
        queue_alert = fields.get(alert_field)
        if queue_alert is None:
            raise RuntimeError(f"Scheduler health payload is missing alert for '{queue_name}'.")
        if queue_alert not in VALID_QUEUE_ALERTS:
            raise RuntimeError(f"Scheduler health payload has invalid alert for '{queue_name}'.")
        derived_queue_alert = classify_queue_alert(
            queue_name,
            pressure=queue_pressure,
            oldest_job_age_seconds=parsed_oldest_job_age_seconds,
        )
        if queue_alert != derived_queue_alert:
            raise RuntimeError(
                f"Scheduler health payload has inconsistent alert for '{queue_name}'."
            )
        queue_alerts[queue_name] = queue_alert

    derived_overall_pressure = derive_overall_pressure(queue_pressures)
    if overall_pressure != derived_overall_pressure:
        raise RuntimeError(
            "Scheduler health payload overall_pressure does not match queue pressures."
        )
    derived_overall_alert = derive_overall_alert(queue_alerts)
    if overall_alert != derived_overall_alert:
        raise RuntimeError("Scheduler health payload overall_alert does not match queue alerts.")


async def _check_worker(role: str) -> None:
    await _assert_database_ready()
    fields = _parse_health_fields(await _assert_redis_health_key(_healthcheck_key_for_role(role)))
    required_fields = {"j_complete", "j_failed", "j_retried", "j_ongoing", "queued"}
    missing_fields = sorted(required_fields - fields.keys())
    if missing_fields:
        raise RuntimeError(f"Worker health payload is missing {', '.join(missing_fields)}.")
    for field_name in sorted(required_fields):
        _parse_non_negative_int(fields[field_name], field_name=field_name)

    metrics = await _assert_redis_hash_fields(worker_metrics_key(role))
    queue_name = metrics.get("queue_name")
    if not queue_name:
        raise RuntimeError("Worker metrics hash is missing queue_name.")

    queue_depth = _parse_non_negative_int(
        metrics.get("queue_depth", ""),
        field_name="queue_depth",
    )
    if queue_depth != _parse_non_negative_int(fields["queued"], field_name="queued"):
        raise RuntimeError("Worker metrics queue_depth does not match queued heartbeat depth.")

    queue_pressure = metrics.get("queue_pressure")
    if queue_pressure not in VALID_QUEUE_PRESSURES:
        raise RuntimeError("Worker metrics queue_pressure is invalid.")

    oldest_job_age_seconds = _parse_non_negative_int(
        metrics.get("oldest_job_age_seconds", ""),
        field_name="oldest_job_age_seconds",
    )

    queue_alert = metrics.get("queue_alert")
    if queue_alert not in VALID_QUEUE_ALERTS:
        raise RuntimeError("Worker metrics queue_alert is invalid.")
    derived_queue_alert = classify_queue_alert(
        queue_name,
        pressure=queue_pressure,
        oldest_job_age_seconds=oldest_job_age_seconds,
    )
    if queue_alert != derived_queue_alert:
        raise RuntimeError("Worker metrics queue_alert does not match queue state.")

    for counter_name in COUNTER_FIELDS:
        if counter_name not in metrics:
            raise RuntimeError(f"Worker metrics hash is missing {counter_name}.")
        _parse_non_negative_int(metrics[counter_name], field_name=counter_name)


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
