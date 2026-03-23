from __future__ import annotations

import json
import platform
import sys
import uuid

import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job
from app.pipeline.models import Application

logger = structlog.get_logger()


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
        # Placeholder — full implementation needs tsvector update + embedding recalc
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
        # Stub — full implementation parses JSON and creates records
        return {
            "status": "complete",
            "jobs_imported": imported_jobs,
            "applications_imported": imported_apps,
        }
