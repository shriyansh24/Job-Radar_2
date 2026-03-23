from __future__ import annotations

import json
import platform
import sys
import uuid
from importlib import import_module

import structlog
from sqlalchemy import delete, func, inspect, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base
from app.jobs.models import Job
from app.pipeline.models import Application, ApplicationStatusHistory
from app.scraping.models import ScrapeAttempt, ScrapeTarget, ScraperRun

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
            if table.name == "users" or table.name not in existing_tables or "user_id" not in table.c:
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
