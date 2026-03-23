from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas import (
    DailyStats,
    FunnelStageData,
    OverviewStats,
    SkillStats,
    SourceStats,
)
from app.jobs.models import Job
from app.pipeline.models import Application


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, user_id: uuid.UUID) -> OverviewStats:
        # Total jobs
        total_jobs = (
            await self.db.scalar(
                select(func.count()).select_from(
                    select(Job).where(Job.user_id == user_id, Job.is_active.is_(True)).subquery()
                )
            )
            or 0
        )

        # Total applications
        total_apps = (
            await self.db.scalar(
                select(func.count()).select_from(
                    select(Application).where(Application.user_id == user_id).subquery()
                )
            )
            or 0
        )

        # Applications by status
        status_rows = await self.db.execute(
            select(Application.status, func.count())
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        apps_by_status = {row[0]: row[1] for row in status_rows}

        # Response rate (apps that moved past 'applied')
        responded = sum(v for k, v in apps_by_status.items() if k not in ("saved", "applied"))
        applied_total = sum(v for k, v in apps_by_status.items() if k != "saved")
        response_rate = (responded / applied_total * 100) if applied_total > 0 else 0.0

        # Jobs scraped today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        jobs_today = (
            await self.db.scalar(
                select(func.count()).select_from(
                    select(Job)
                    .where(
                        Job.user_id == user_id,
                        Job.scraped_at >= today_start,
                    )
                    .subquery()
                )
            )
            or 0
        )

        # Enriched
        enriched = (
            await self.db.scalar(
                select(func.count()).select_from(
                    select(Job)
                    .where(
                        Job.user_id == user_id,
                        Job.is_enriched.is_(True),
                    )
                    .subquery()
                )
            )
            or 0
        )

        total_interviews = apps_by_status.get("interviewing", 0) + apps_by_status.get(
            "screening", 0
        )
        total_offers = apps_by_status.get("offer", 0) + apps_by_status.get("accepted", 0)

        return OverviewStats(
            total_jobs=total_jobs,
            total_applications=total_apps,
            total_interviews=total_interviews,
            total_offers=total_offers,
            applications_by_status=apps_by_status,
            response_rate=response_rate / 100 if response_rate > 1 else response_rate,
            avg_days_to_response=0.0,
            jobs_scraped_today=jobs_today,
            enriched_jobs=enriched,
        )

    async def get_daily_stats(self, user_id: uuid.UUID, days: int = 30) -> list[DailyStats]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Jobs per day
        job_rows = await self.db.execute(
            select(
                func.date(Job.scraped_at).label("day"),
                func.count().label("cnt"),
            )
            .where(Job.user_id == user_id, Job.scraped_at >= cutoff)
            .group_by("day")
            .order_by("day")
        )
        jobs_by_day = {self._coerce_day(row.day): row.cnt for row in job_rows}

        # Apps per day
        app_rows = await self.db.execute(
            select(
                func.date(Application.created_at).label("day"),
                func.count().label("cnt"),
            )
            .where(Application.user_id == user_id, Application.created_at >= cutoff)
            .group_by("day")
            .order_by("day")
        )
        apps_by_day = {self._coerce_day(row.day): row.cnt for row in app_rows}

        all_days = sorted(set(list(jobs_by_day.keys()) + list(apps_by_day.keys())))
        return [
            DailyStats(
                date=d,
                jobs_scraped=jobs_by_day.get(d, 0),
                applications=apps_by_day.get(d, 0),
            )
            for d in all_days
        ]

    async def get_source_stats(self, user_id: uuid.UUID) -> list[SourceStats]:
        rows = await self.db.execute(
            select(
                Job.source,
                func.count().label("total"),
                func.avg(Job.match_score).label("avg_score"),
            )
            .where(Job.user_id == user_id, Job.is_active.is_(True))
            .group_by(Job.source)
            .order_by(func.count().desc())
        )
        return [
            SourceStats(
                source=row.source,
                total_jobs=row.total,
                quality_score=min(float(row.avg_score), 1.0) if row.avg_score else 0.0,
                avg_match_score=float(row.avg_score) if row.avg_score else None,
            )
            for row in rows
        ]

    async def get_skills_stats(self, user_id: uuid.UUID) -> list[SkillStats]:
        # Get all jobs with skills_required for this user
        result = await self.db.scalars(
            select(Job.skills_required).where(
                Job.user_id == user_id, Job.is_active.is_(True), Job.skills_required.isnot(None)
            )
        )
        # Count skills
        skill_counts: dict[str, int] = {}
        total_jobs = 0
        for skills in result:
            if isinstance(skills, list):
                total_jobs += 1
                for skill in skills:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:50]
        return [
            SkillStats(
                skill=skill,
                count=count,
                percentage=round(count / total_jobs * 100, 1) if total_jobs > 0 else 0,
            )
            for skill, count in sorted_skills
        ]

    async def get_funnel(self, user_id: uuid.UUID) -> list["FunnelStageData"]:
        rows = await self.db.execute(
            select(Application.status, func.count())
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        counts = {row[0]: row[1] for row in rows}
        stages = ["saved", "applied", "screening", "interviewing", "offer", "accepted"]
        return [
            FunnelStageData(stage=stage.capitalize(), count=counts.get(stage, 0))
            for stage in stages
        ]

    @staticmethod
    def _coerce_day(value: object) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            return date.fromisoformat(value)
        raise TypeError(f"Unsupported day value: {value!r}")
