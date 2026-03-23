from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.errors import NotFoundError
from app.source_health.models import SourceCheckLog, SourceRegistry

logger = structlog.get_logger()


class SourceHealthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_sources(self) -> list[SourceRegistry]:
        result = await self.db.scalars(select(SourceRegistry).order_by(SourceRegistry.source_name))
        return list(result.all())

    async def get_source_health(
        self, source_id: uuid.UUID
    ) -> tuple[SourceRegistry, list[SourceCheckLog]]:
        result = await self.db.execute(
            select(SourceRegistry).where(SourceRegistry.id == source_id)
        )
        source = result.scalar_one_or_none()
        if source is None:
            raise NotFoundError(f"Source {source_id} not found")

        logs_result = await self.db.scalars(
            select(SourceCheckLog)
            .where(SourceCheckLog.source_id == source_id)
            .order_by(SourceCheckLog.checked_at.desc())
            .limit(20)
        )
        return source, list(logs_result.all())

    async def record_check(
        self,
        source_name: str,
        status: str,
        jobs_found: int,
        error: str | None = None,
    ) -> None:
        # Find or create registry entry
        result = await self.db.execute(
            select(SourceRegistry).where(SourceRegistry.source_name == source_name)
        )
        registry = result.scalar_one_or_none()
        if registry is None:
            registry = SourceRegistry(source_name=source_name)
            self.db.add(registry)
            await self.db.flush()

        # Create check log entry
        check_log = SourceCheckLog(
            source_id=registry.id,
            check_status=status,
            jobs_found=jobs_found,
            error_message=error,
        )
        self.db.add(check_log)

        # Update registry stats
        now = datetime.now(timezone.utc)
        registry.last_check_at = now
        registry.total_jobs_found = (registry.total_jobs_found or 0) + jobs_found

        if status == "success":
            registry.health_state = "healthy"
            registry.failure_count = 0
        else:
            registry.failure_count = (registry.failure_count or 0) + 1
            registry.health_state = "degraded"

        await self.db.commit()
        logger.info(
            "source_check_recorded",
            source_name=source_name,
            status=status,
            jobs_found=jobs_found,
        )
