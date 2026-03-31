from __future__ import annotations

import json
import platform
import sys
import uuid
from datetime import UTC, datetime
from importlib import import_module
from typing import Any, cast

import structlog
from sqlalchemy import delete, func, inspect, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import Base
from app.jobs.models import Job
from app.pipeline.models import Application, ApplicationStatusHistory
from app.runtime.queue import (
    derive_overall_alert,
    derive_overall_pressure,
    get_queue_pool,
    get_queue_snapshots,
)
from app.runtime.worker_metrics import COUNTER_FIELDS, worker_metrics_key
from app.scraping.models import ScrapeAttempt, ScraperRun, ScrapeTarget

logger = structlog.get_logger()

USER_DATA_MODEL_MODULES = (
    "app.analytics.models",
    "app.auto_apply.form_learning",
    "app.auto_apply.models",
    "app.canonical_jobs.models",
    "app.copilot.models",
    "app.email.models",
    "app.interview.models",
    "app.jobs.models",
    "app.networking.models",
    "app.notifications.models",
    "app.outcomes.models",
    "app.pipeline.models",
    "app.profile.models",
    "app.resume.archetypes",
    "app.resume.models",
    "app.salary.models",
    "app.scraping.dedup_feedback",
    "app.scraping.models",
    "app.search_expansion.models",
    "app.settings.models",
)


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def health_check(self) -> dict:
        try:
            await self.db.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False

        return {
            "status": "ok" if db_ok else "degraded",
            "database": "connected" if db_ok else "disconnected",
        }

    async def diagnostics(self) -> dict:
        job_count = await self.db.scalar(select(func.count()).select_from(Job)) or 0
        app_count = await self.db.scalar(select(func.count()).select_from(Application)) or 0

        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "job_count": job_count,
            "application_count": app_count,
        }

    async def runtime_status(self) -> dict:
        captured_at = datetime.now(UTC).isoformat()
        runtime: dict[str, object] = {
            "status": "ok",
            "captured_at": captured_at,
            "redis_connected": False,
            "queue_summary": {
                "overall_pressure": "nominal",
                "overall_alert": "clear",
                "queues": [],
            },
            "worker_metrics": [],
            "auth_audit_sink": {
                "enabled": settings.auth_audit_stream_enabled,
                "stream_key": settings.auth_audit_stream_key,
                "maxlen": settings.auth_audit_stream_maxlen,
            },
        }

        try:
            queue_pool = await get_queue_pool()
            await queue_pool.ping()
            runtime["redis_connected"] = True

            snapshots = await get_queue_snapshots(queue_pool)
            queue_rows = [
                {
                    "queue_name": snapshot.queue_name,
                    "queue_depth": snapshot.queue_depth,
                    "queue_pressure": snapshot.queue_pressure,
                    "oldest_job_age_seconds": snapshot.oldest_job_age_seconds,
                    "queue_alert": snapshot.queue_alert,
                }
                for snapshot in snapshots.values()
            ]
            queue_pressures = {
                snapshot.queue_name: snapshot.queue_pressure for snapshot in snapshots.values()
            }
            queue_alerts = {
                snapshot.queue_name: snapshot.queue_alert for snapshot in snapshots.values()
            }
            runtime["queue_summary"] = {
                "overall_pressure": derive_overall_pressure(queue_pressures),
                "overall_alert": derive_overall_alert(queue_alerts),
                "queues": queue_rows,
            }

            worker_rows: list[dict[str, object]] = []
            for role in ("scraping", "analysis", "ops"):
                raw_fields = cast(
                    dict[object, object],
                    await cast(Any, queue_pool).hgetall(worker_metrics_key(role)),
                )
                if not raw_fields:
                    continue
                worker_row: dict[str, object] = {
                    "role": role,
                    "available": True,
                }
                for field_name in ("queue_name", "queue_pressure", "queue_alert"):
                    if field_name in raw_fields:
                        value = raw_fields[field_name]
                        worker_row[field_name] = (
                            value.decode() if isinstance(value, bytes) else value
                        )
                for field_name in ("queue_depth", "oldest_job_age_seconds", *COUNTER_FIELDS):
                    if field_name in raw_fields:
                        value = raw_fields[field_name]
                        worker_row[field_name] = int(
                            value.decode() if isinstance(value, bytes) else value
                        )
                worker_rows.append(worker_row)
            runtime["worker_metrics"] = worker_rows
        except Exception as exc:
            runtime["status"] = "degraded"
            runtime["runtime_error"] = str(exc)
            logger.warning("admin_runtime_status_degraded", error=str(exc))

        return runtime

    async def reindex(self, user_id: uuid.UUID) -> dict:
        count = (
            await self.db.scalar(
                select(func.count()).select_from(
                    select(Job).where(Job.user_id == user_id).subquery()
                )
            )
            or 0
        )
        return {"status": "complete", "jobs_reindexed": count}

    async def export_data(self, user_id: uuid.UUID) -> bytes:
        jobs_result = await self.db.scalars(select(Job).where(Job.user_id == user_id))
        apps_result = await self.db.scalars(
            select(Application).where(Application.user_id == user_id)
        )

        from app.jobs.schemas import JobResponse
        from app.pipeline.schemas import ApplicationResponse

        data = {
            "jobs": [JobResponse.model_validate(j).model_dump(mode="json") for j in jobs_result],
            "applications": [
                ApplicationResponse.model_validate(a).model_dump(mode="json") for a in apps_result
            ],
        }
        return json.dumps(data, indent=2).encode()

    async def import_data(self, data: dict, user_id: uuid.UUID) -> dict:
        imported_jobs = 0
        imported_apps = 0
        return {
            "status": "complete",
            "jobs_imported": imported_jobs,
            "applications_imported": imported_apps,
        }

    async def clear_data(self, user_id: uuid.UUID, *, commit: bool = True) -> dict:
        self._ensure_user_data_models_loaded()
        existing_tables = await self.db.run_sync(
            lambda sync_session: set(inspect(sync_session.bind).get_table_names())
        )

        rows_deleted = 0
        application_ids = select(Application.id).where(Application.user_id == user_id)
        application_history_result = await self.db.execute(
            delete(ApplicationStatusHistory).where(
                ApplicationStatusHistory.application_id.in_(application_ids)
            )
        )
        rows_deleted += max(application_history_result.rowcount or 0, 0)

        run_ids = select(ScraperRun.id).where(ScraperRun.user_id == user_id)
        target_ids = select(ScrapeTarget.id).where(ScrapeTarget.user_id == user_id)
        scrape_attempt_result = await self.db.execute(
            delete(ScrapeAttempt).where(
                or_(
                    ScrapeAttempt.run_id.in_(run_ids),
                    ScrapeAttempt.target_id.in_(target_ids),
                )
            )
        )
        rows_deleted += max(scrape_attempt_result.rowcount or 0, 0)

        for table in reversed(Base.metadata.sorted_tables):
            if (
                table.name == "users"
                or table.name not in existing_tables
                or "user_id" not in table.c
            ):
                continue
            result = await self.db.execute(delete(table).where(table.c.user_id == user_id))
            rows_deleted += max(result.rowcount or 0, 0)

        if commit:
            await self.db.commit()

        logger.info("admin_data_cleared", user_id=str(user_id), rows_deleted=rows_deleted)
        return {"status": "ok", "rows_deleted": rows_deleted}

    def _ensure_user_data_models_loaded(self) -> None:
        for module_name in USER_DATA_MODEL_MODULES:
            import_module(module_name)
