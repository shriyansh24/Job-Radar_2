from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import func, select

from app.auto_apply.models import AutoApplyRun
from app.pipeline.models import Application

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


@dataclass
class SafetyCheck:
    name: str
    passed: bool
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass
class SafetyResult:
    passed: bool
    checks: list[SafetyCheck] = field(default_factory=list)

    @property
    def failed_checks(self) -> list[str]:
        return [check.name for check in self.checks if not check.passed]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [check.as_dict() for check in self.checks],
            "failed": self.failed_checks,
        }


class SafetyLayer:
    """Pre-flight checks that must pass before auto-apply can continue."""

    DAILY_LIMIT: int = 25
    PER_ATS_LIMITS: dict[str, dict[str, int]] = {
        "lever": {"per_hour": 5, "cooldown_sec": 60},
        "greenhouse": {"per_hour": 10, "cooldown_sec": 30},
        "workday": {"per_hour": 3, "cooldown_sec": 300},
        "default": {"per_hour": 5, "cooldown_sec": 60},
    }
    SAME_COMPANY_COOLDOWN_DAYS: int = 7
    STALE_POSTING_DAYS: int = 30
    DAILY_BUDGET_LIMIT: float = 10.0

    def __init__(
        self,
        daily_limit: int | None = None,
        budget_limit: float | None = None,
        known_ats_types: set[str] | None = None,
    ) -> None:
        if daily_limit is not None:
            self.DAILY_LIMIT = daily_limit
        if budget_limit is not None:
            self.DAILY_BUDGET_LIMIT = budget_limit
        self._known_ats_types = known_ats_types or set()

    async def check_safety(
        self,
        job_id: str,
        user_id: uuid.UUID,
        db: AsyncSession,
        *,
        ats_provider: str | None = None,
        company_name: str | None = None,
        first_seen_at: datetime | None = None,
        blacklisted_companies: list[str] | None = None,
        blacklisted_keywords: list[str] | None = None,
        job_title: str | None = None,
        daily_spend: float = 0.0,
    ) -> SafetyResult:
        checks: list[SafetyCheck] = []
        checks.append(await self._check_duplicate(job_id, user_id, db))
        checks.append(await self._check_daily_limit(user_id, db))
        checks.append(await self._check_ats_hourly_limit(user_id, ats_provider or "default", db))

        if company_name:
            checks.append(await self._check_company_cooldown(user_id, company_name, db))

        checks.append(
            self._check_blacklist(
                company_name,
                job_title,
                blacklisted_companies or [],
                blacklisted_keywords or [],
            )
        )
        checks.append(self._check_budget(daily_spend))
        checks.append(self._check_freshness(first_seen_at))
        checks.append(self._check_first_time_ats(ats_provider))

        passed = all(check.passed for check in checks)
        if not passed:
            logger.info(
                "auto_apply_safety_blocked",
                job_id=job_id,
                user_id=str(user_id),
                failed=[check.name for check in checks if not check.passed],
            )

        return SafetyResult(passed=passed, checks=checks)

    async def _check_duplicate(
        self, job_id: str, user_id: uuid.UUID, db: AsyncSession
    ) -> SafetyCheck:
        count = await db.scalar(
            select(func.count()).select_from(Application).where(
                Application.user_id == user_id,
                Application.job_id == job_id,
            )
        )
        seen = count or 0
        return SafetyCheck(
            name="duplicate",
            passed=seen == 0,
            detail="Already applied" if seen > 0 else "Not applied",
        )

    async def _check_daily_limit(self, user_id: uuid.UUID, db: AsyncSession) -> SafetyCheck:
        now = datetime.now(UTC)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        count = await db.scalar(
            select(func.count()).select_from(AutoApplyRun).where(
                AutoApplyRun.user_id == user_id,
                AutoApplyRun.started_at >= start_of_day,
                AutoApplyRun.status.in_(("filled", "submitted", "running")),
            )
        )
        today_count = count or 0
        return SafetyCheck(
            name="daily_limit",
            passed=today_count < self.DAILY_LIMIT,
            detail=f"{today_count}/{self.DAILY_LIMIT} today",
        )

    async def _check_ats_hourly_limit(
        self, user_id: uuid.UUID, ats: str, db: AsyncSession
    ) -> SafetyCheck:
        limits = self.PER_ATS_LIMITS.get(ats, self.PER_ATS_LIMITS["default"])
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        count = await db.scalar(
            select(func.count()).select_from(AutoApplyRun).where(
                AutoApplyRun.user_id == user_id,
                AutoApplyRun.ats_provider == ats,
                AutoApplyRun.started_at >= one_hour_ago,
                AutoApplyRun.status.in_(("filled", "submitted", "running")),
            )
        )
        hourly_count = count or 0
        per_hour = limits["per_hour"]
        return SafetyCheck(
            name="ats_hourly_limit",
            passed=hourly_count < per_hour,
            detail=f"{ats}: {hourly_count}/{per_hour} this hour",
        )

    async def _check_company_cooldown(
        self, user_id: uuid.UUID, company_name: str, db: AsyncSession
    ) -> SafetyCheck:
        cutoff = datetime.now(UTC) - timedelta(days=self.SAME_COMPANY_COOLDOWN_DAYS)
        count = await db.scalar(
            select(func.count()).select_from(Application).where(
                Application.user_id == user_id,
                func.lower(Application.company_name) == company_name.lower(),
                Application.created_at >= cutoff,
            )
        )
        recent_count = count or 0
        if recent_count > 0:
            detail = (
                f"Applied to {recent_count} roles at {company_name} "
                f"in last {self.SAME_COMPANY_COOLDOWN_DAYS} days"
            )
        else:
            detail = f"No recent applications to {company_name}"
        return SafetyCheck(
            name="company_cooldown",
            passed=recent_count == 0,
            detail=detail,
        )

    def _check_blacklist(
        self,
        company_name: str | None,
        job_title: str | None,
        blacklisted_companies: list[str],
        blacklisted_keywords: list[str],
    ) -> SafetyCheck:
        if company_name:
            lowered_company = company_name.lower()
            for blocked in blacklisted_companies:
                if blocked.lower() in lowered_company:
                    return SafetyCheck(
                        name="blacklist",
                        passed=False,
                        detail=f"Company '{company_name}' is blacklisted",
                    )

        if job_title:
            lowered_title = job_title.lower()
            for keyword in blacklisted_keywords:
                if keyword.lower() in lowered_title:
                    return SafetyCheck(
                        name="blacklist",
                        passed=False,
                        detail=f"Job title contains blacklisted keyword '{keyword}'",
                    )

        return SafetyCheck(name="blacklist", passed=True, detail="Not blacklisted")

    def _check_budget(self, daily_spend: float) -> SafetyCheck:
        return SafetyCheck(
            name="budget",
            passed=daily_spend < self.DAILY_BUDGET_LIMIT,
            detail=f"${daily_spend:.2f}/${self.DAILY_BUDGET_LIMIT:.2f} spent today",
        )

    def _check_freshness(self, first_seen_at: datetime | None) -> SafetyCheck:
        if not first_seen_at:
            return SafetyCheck(
                name="freshness",
                passed=True,
                detail="No first_seen_at - assuming fresh",
            )

        now = datetime.now(UTC)
        if first_seen_at.tzinfo is None:
            age_days = (now.replace(tzinfo=None) - first_seen_at).days
        else:
            age_days = (now - first_seen_at).days

        return SafetyCheck(
            name="freshness",
            passed=age_days < self.STALE_POSTING_DAYS,
            detail=f"Posted {age_days} days ago",
        )

    def _check_first_time_ats(self, ats_provider: str | None) -> SafetyCheck:
        if not ats_provider:
            return SafetyCheck(
                name="first_time_ats",
                passed=True,
                detail="No ATS detected - generic flow",
            )

        if ats_provider in self._known_ats_types:
            return SafetyCheck(
                name="first_time_ats",
                passed=True,
                detail=f"ATS '{ats_provider}' previously used",
            )

        return SafetyCheck(
            name="first_time_ats",
            passed=False,
            detail=f"First time using ATS '{ats_provider}' - requires confirmation",
        )

    def mark_ats_known(self, ats_provider: str) -> None:
        self._known_ats_types.add(ats_provider)
