"""SQL Pattern Detector – Feature D1.

Aggregates application data into actionable insights using SQL queries.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Integer, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job
from app.pipeline.models import Application, ApplicationStatusHistory
from app.profile.models import UserProfile

# Statuses that indicate the employer responded
_RESPONDED_STATUSES = frozenset(
    {"screening", "interviewing", "offer", "accepted", "rejected"}
)

# Minimum sample size before we report a pattern
_MIN_SAMPLE = 3


class PatternDetector:
    """Runs aggregate SQL queries to surface application patterns."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _dialect_name(self) -> str:
        bind = self.db.get_bind()
        return bind.dialect.name if bind is not None else ""

    def _elapsed_days_expr(self, end_ts, start_ts):
        if self._dialect_name() == "postgresql":
            return func.extract("epoch", end_ts - start_ts) / 86400.0
        return func.julianday(end_ts) - func.julianday(start_ts)

    def _day_of_week_expr(self, column):
        if self._dialect_name() == "postgresql":
            return cast(func.extract("dow", column), Integer)
        return cast(func.strftime("%w", column), Integer)

    # ------------------------------------------------------------------
    # a) Callback rate by company size (approximated by job_count in jobs)
    # ------------------------------------------------------------------
    async def callback_rate_by_company_size(
        self, user_id: uuid.UUID
    ) -> list[dict]:
        """Which company-size buckets get the most callbacks?

        We approximate company size by counting how many jobs we have
        scraped from that company.  Buckets: small (<10), medium (10-99),
        large (100+).
        """
        # Sub-query: job count per company_name
        company_sizes = (
            select(
                Job.company_name,
                func.count().label("job_count"),
            )
            .where(Job.user_id == user_id, Job.company_name.isnot(None))
            .group_by(Job.company_name)
            .subquery("company_sizes")
        )

        size_label = case(
            (company_sizes.c.job_count < 10, "small"),
            (company_sizes.c.job_count < 100, "medium"),
            else_="large",
        ).label("size_bucket")

        responded = case(
            (Application.status.in_(_RESPONDED_STATUSES), 1),
            else_=0,
        )

        stmt = (
            select(
                size_label,
                func.count().label("total"),
                func.sum(responded).label("callbacks"),
            )
            .select_from(Application)
            .outerjoin(
                company_sizes,
                Application.company_name == company_sizes.c.company_name,
            )
            .where(
                Application.user_id == user_id,
                Application.status != "saved",
            )
            .group_by(size_label)
            .having(func.count() >= _MIN_SAMPLE)
        )

        rows = await self.db.execute(stmt)
        return [
            {
                "size_bucket": row.size_bucket or "unknown",
                "total_applications": row.total,
                "callbacks": int(row.callbacks or 0),
                "callback_rate": round(
                    int(row.callbacks or 0) / row.total * 100, 1
                )
                if row.total
                else 0.0,
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # b) Conversion funnel
    # ------------------------------------------------------------------
    async def conversion_funnel(self, user_id: uuid.UUID) -> list[dict]:
        """Count applications at each pipeline stage."""
        stages = [
            "saved",
            "applied",
            "screening",
            "interviewing",
            "offer",
            "accepted",
            "rejected",
            "withdrawn",
        ]
        rows = await self.db.execute(
            select(Application.status, func.count().label("cnt"))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        counts = {r[0]: r[1] for r in rows}
        return [
            {"stage": stage, "count": counts.get(stage, 0)} for stage in stages
        ]

    # ------------------------------------------------------------------
    # c) Response time patterns
    # ------------------------------------------------------------------
    async def response_time_patterns(self, user_id: uuid.UUID) -> list[dict]:
        """Average days from 'applied' to first response, grouped by month.

        We find the earliest status-history entry that moved an application
        OUT of 'applied' into a response status.
        """
        # For each application, find the applied_at and the first response
        # event in status_history.
        first_response = (
            select(
                ApplicationStatusHistory.application_id,
                func.min(ApplicationStatusHistory.changed_at).label(
                    "first_response_at"
                ),
            )
            .where(
                ApplicationStatusHistory.new_status.in_(_RESPONDED_STATUSES),
            )
            .group_by(ApplicationStatusHistory.application_id)
            .subquery("first_response")
        )

        stmt = (
            select(
                func.avg(
                    self._elapsed_days_expr(
                        first_response.c.first_response_at,
                        Application.applied_at,
                    )
                ).label("avg_days"),
                func.count().label("sample_size"),
            )
            .select_from(Application)
            .join(
                first_response,
                Application.id == first_response.c.application_id,
            )
            .where(
                Application.user_id == user_id,
                Application.applied_at.isnot(None),
            )
        )

        row = (await self.db.execute(stmt)).first()
        if row and row.sample_size and row.sample_size >= _MIN_SAMPLE:
            return [
                {
                    "avg_days_to_response": round(float(row.avg_days or 0), 1),
                    "sample_size": row.sample_size,
                }
            ]
        warning = (
            "Not enough data"
            if (row and row.sample_size and row.sample_size < _MIN_SAMPLE)
            else "No response data"
        )
        return [
            {
                "avg_days_to_response": 0.0,
                "sample_size": row.sample_size if row and row.sample_size else 0,
                "warning": warning,
            }
        ]

    # ------------------------------------------------------------------
    # d) Best application timing
    # ------------------------------------------------------------------
    async def best_application_timing(self, user_id: uuid.UUID) -> list[dict]:
        """Day-of-week correlation with callbacks.

        SQLite: strftime('%w', ...) returns 0=Sunday..6=Saturday.
        """
        responded = case(
            (Application.status.in_(_RESPONDED_STATUSES), 1),
            else_=0,
        )

        dow_expr = self._day_of_week_expr(Application.applied_at).label("dow")

        stmt = (
            select(
                dow_expr,
                func.count().label("total"),
                func.sum(responded).label("callbacks"),
            )
            .where(
                Application.user_id == user_id,
                Application.applied_at.isnot(None),
                Application.status != "saved",
            )
            .group_by(dow_expr)
            .having(func.count() >= _MIN_SAMPLE)
            .order_by(dow_expr)
        )

        day_names = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]

        rows = await self.db.execute(stmt)
        return [
            {
                "day_of_week": day_names[row.dow] if row.dow is not None else "Unknown",
                "total_applications": row.total,
                "callbacks": int(row.callbacks or 0),
                "callback_rate": round(
                    int(row.callbacks or 0) / row.total * 100, 1
                )
                if row.total
                else 0.0,
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # e) Company ghosting rate
    # ------------------------------------------------------------------
    async def company_ghosting_rate(self, user_id: uuid.UUID) -> list[dict]:
        """Percentage of applications with no response after 14 days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)

        ghosted = case(
            (
                Application.status == "applied",
                case(
                    (Application.applied_at <= cutoff, 1),
                    else_=0,
                ),
            ),
            else_=0,
        )

        stmt = (
            select(
                Application.company_name,
                func.count().label("total"),
                func.sum(ghosted).label("ghosted"),
            )
            .where(
                Application.user_id == user_id,
                Application.status != "saved",
                Application.company_name.isnot(None),
            )
            .group_by(Application.company_name)
            .having(func.count() >= _MIN_SAMPLE)
            .order_by(func.sum(ghosted).desc())
        )

        rows = await self.db.execute(stmt)
        return [
            {
                "company": row.company_name,
                "total_applications": row.total,
                "ghosted": int(row.ghosted or 0),
                "ghosting_rate": round(
                    int(row.ghosted or 0) / row.total * 100, 1
                )
                if row.total
                else 0.0,
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # f) Skill gap detection
    # ------------------------------------------------------------------
    async def skill_gap_detection(self, user_id: uuid.UUID) -> list[dict]:
        """JD-required skills NOT present in the user's resume text.

        We pull skills_required from jobs linked to the user's applications,
        then compare against the resume text in user_profiles.
        """
        # Get user resume text
        profile = await self.db.scalar(
            select(UserProfile.resume_text).where(
                UserProfile.user_id == user_id
            )
        )
        resume_lower = (profile or "").lower()

        # Get skills_required from jobs this user applied to
        rows = await self.db.scalars(
            select(Job.skills_required)
            .join(Application, Application.job_id == Job.id)
            .where(
                Application.user_id == user_id,
                Job.skills_required.isnot(None),
            )
        )

        skill_demand: dict[str, int] = {}
        for skills_list in rows:
            if not isinstance(skills_list, list):
                continue
            for skill in skills_list:
                skill_demand[skill] = skill_demand.get(skill, 0) + 1

        # Find gaps: skills that don't appear in the resume
        gaps = [
            {"skill": skill, "demand_count": count}
            for skill, count in skill_demand.items()
            if skill.lower() not in resume_lower and count >= _MIN_SAMPLE
        ]
        gaps.sort(key=lambda g: g["demand_count"], reverse=True)
        return gaps[:20]

    # ------------------------------------------------------------------
    # g) Aggregate all patterns
    # ------------------------------------------------------------------
    async def get_all_patterns(self, user_id: uuid.UUID) -> dict:
        """Return all 6 pattern analyses in one payload."""
        return {
            "callback_rate_by_company_size": await self.callback_rate_by_company_size(
                user_id
            ),
            "conversion_funnel": await self.conversion_funnel(user_id),
            "response_time_patterns": await self.response_time_patterns(
                user_id
            ),
            "best_application_timing": await self.best_application_timing(
                user_id
            ),
            "company_ghosting_rate": await self.company_ghosting_rate(user_id),
            "skill_gap_detection": await self.skill_gap_detection(user_id),
        }
