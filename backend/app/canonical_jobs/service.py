from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.canonical_jobs.models import CanonicalJob, RawJobSource
from app.shared.errors import NotFoundError

logger = structlog.get_logger()

STALE_THRESHOLD_DAYS = 14


class CanonicalJobService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_canonical_jobs(
        self,
        user_id: uuid.UUID,
        *,
        status: str | None = None,
        stale_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CanonicalJob]:
        query = (
            select(CanonicalJob)
            .where(CanonicalJob.user_id == user_id)
            .order_by(CanonicalJob.last_refreshed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            query = query.where(CanonicalJob.status == status)
        if stale_only:
            query = query.where(CanonicalJob.is_stale == True)  # noqa: E712

        result = await self.db.scalars(query)
        return list(result.all())

    async def get_canonical_job(
        self, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> CanonicalJob:
        query = (
            select(CanonicalJob)
            .options(selectinload(CanonicalJob.sources))
            .where(CanonicalJob.id == job_id, CanonicalJob.user_id == user_id)
        )
        job = await self.db.scalar(query)
        if job is None:
            raise NotFoundError(detail=f"Canonical job {job_id} not found")
        return job

    async def close_job(self, job_id: uuid.UUID, user_id: uuid.UUID) -> CanonicalJob:
        job = await self.get_canonical_job(job_id, user_id)
        job.status = "closed"
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def reactivate_job(self, job_id: uuid.UUID, user_id: uuid.UUID) -> CanonicalJob:
        job = await self.get_canonical_job(job_id, user_id)
        job.status = "open"
        job.is_stale = False
        job.last_refreshed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def run_staleness_sweep(self, user_id: uuid.UUID) -> int:
        """Mark canonical jobs not refreshed in STALE_THRESHOLD_DAYS as stale."""
        threshold = datetime.now(timezone.utc) - timedelta(days=STALE_THRESHOLD_DAYS)
        stmt = (
            update(CanonicalJob)
            .where(
                CanonicalJob.user_id == user_id,
                CanonicalJob.status == "open",
                CanonicalJob.last_refreshed_at < threshold,
                CanonicalJob.is_stale == False,  # noqa: E712
            )
            .values(is_stale=True)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        count = result.rowcount or 0
        if count:
            logger.info("canonical_jobs.staleness_sweep", marked_stale=count)
        return count
