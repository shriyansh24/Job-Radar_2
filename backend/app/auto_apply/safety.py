"""Safety layer for auto-apply — all checks must pass before any adapter executes.

Implements 5 safety checks:
1. Duplicate application check (already applied to this job?)
2. Rate limiting (max N applications per hour/day)
3. Blacklist check (excluded companies/roles)
4. Budget check (paid API credit usage)
5. Human-in-the-loop confirmation for first-time ATS types
"""

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
    """Result of a single safety check."""

    name: str
    passed: bool
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass
class SafetyResult:
    """Aggregate result of all safety checks."""

    passed: bool
    checks: list[SafetyCheck] = field(default_factory=list)

    @property
    def failed_checks(self) -> list[str]:
        return [c.name for c in self.checks if not c.passed]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [c.as_dict() for c in self.checks],
            "failed": self.failed_checks,
        }


class SafetyLayer:
    """Pre-flight safety checks for auto-apply.

    All checks must pass before an adapter is allowed to execute.
    """

    DAILY_LIMIT: int = 25
    PER_ATS_LIMITS: dict[str, dict[str, int]] = {
        "lever": {"per_hour": 5, "cooldown_sec": 60},
        "greenhouse": {"per_hour": 10, "cooldown_sec": 30},
        "workday": {"per_hour": 3, "cooldown_sec": 300},
        "default": {"per_hour": 5, "cooldown_sec": 60},
    }
    SAME_COMPANY_COOLDOWN_DAYS: int = 7
    STALE_POSTING_DAYS: int = 30
    DAILY_BUDGET_LIMIT: float = 10.0  # Max spend per day in USD

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
        # ATS types the user has previously applied through
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
        """Run all 5 safety checks.

        Args:
            job_id: The job's SHA-256 ID.
            user_id: The user's UUID.
            db: Async database session.
            ats_provider: Detected ATS type (lever, greenhouse, etc.).
            company_name: Company name for cooldown/blacklist checks.
            first_seen_at: When the posting was first scraped.
            blacklisted_companies: User's excluded companies list.
            blacklisted_keywords: User's excluded role keyword list.
            job_title: Job title for keyword blacklist check.
            daily_spend: Current day's API credit spend.

        Returns:
            SafetyResult with all check outcomes.
        """
        checks: list[SafetyCheck] = []

        # 1. Duplicate application check
        checks.append(
            await self._check_duplicate(job_id, user_id, db)
        )

        # 2. Rate limiting (daily + per-ATS hourly)
        checks.append(
            await self._check_daily_limit(user_id, db)
        )
        checks.append(
            await self._check_ats_hourly_limit(user_id, ats_provider or "default", db)
        )

        # 3. Company cooldown
        if company_name:
            checks.append(
                await self._check_company_cooldown(user_id, company_name, db)
            )

        # 3b. Blacklist check
        checks.append(
            self._check_blacklist(
                company_name,
                job_title,
                blacklisted_companies or [],
                blacklisted_keywords or [],
            )
        )

        # 4. Budget check
        checks.append(
            self._check_budget(daily_spend)
        )

        # 5. Stale posting check
        checks.append(
            self._check_freshness(first_seen_at)
        )

        # 6. Human-in-the-loop for first-time ATS
        checks.append(
            self._check_first_time_ats(ats_provider)
        )

        passed = all(c.passed for c in checks)

        if not passed:
            logger.info(
                "safety.blocked",
                job_id=job_id,
                user_id=str(user_id),
                failed=[c.name for c in checks if not c.passed],
            )

        return SafetyResult(passed=passed, checks=checks)

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    async def _check_duplicate(
        self, job_id: str, user_id: uuid.UUID, db: AsyncSession
    ) -> SafetyCheck:
        """Check 1: Has user already applied to this job?"""
        existing = await db.scalar(
            select(func.count()).select_from(Application).where(
                Application.user_id == user_id,
                Application.job_id == job_id,
            )
        )
        count = existing or 0
        return SafetyCheck(
            name="duplicate",
            passed=count == 0,
            detail="Already applied" if count > 0 else "Not applied",
        )

    async def _check_daily_limit(
        self, user_id: uuid.UUID, db: AsyncSession
    ) -> SafetyCheck:
        """Check 2a: Daily application limit."""
        now = datetime.now(UTC)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        today_count_result = await db.scalar(
            select(func.count()).select_from(AutoApplyRun).where(
                AutoApplyRun.user_id == user_id,
                AutoApplyRun.started_at >= start_of_day,
                AutoApplyRun.status.in_(["filled", "submitted", "running"]),
            )
        )
        today_count = today_count_result or 0

        return SafetyCheck(
            name="daily_limit",
            passed=today_count < self.DAILY_LIMIT,
            detail=f"{today_count}/{self.DAILY_LIMIT} today",
        )

    async def _check_ats_hourly_limit(
        self, user_id: uuid.UUID, ats: str, db: AsyncSession
    ) -> SafetyCheck:
        """Check 2b: Per-ATS hourly rate limit."""
        limits = self.PER_ATS_LIMITS.get(ats, self.PER_ATS_LIMITS["default"])
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)

        hour_count_result = await db.scalar(
            select(func.count()).select_from(AutoApplyRun).where(
                AutoApplyRun.user_id == user_id,
                AutoApplyRun.ats_provider == ats,
                AutoApplyRun.started_at >= one_hour_ago,
                AutoApplyRun.status.in_(["filled", "submitted", "running"]),
            )
        )
        hour_count = hour_count_result or 0
        per_hour = limits["per_hour"]

        return SafetyCheck(
            name="ats_hourly_limit",
            passed=hour_count < per_hour,
            detail=f"{ats}: {hour_count}/{per_hour} this hour",
        )

    async def _check_company_cooldown(
        self, user_id: uuid.UUID, company_name: str, db: AsyncSession
    ) -> SafetyCheck:
        """Check: Same-company cooldown period."""
        cutoff = datetime.now(UTC) - timedelta(days=self.SAME_COMPANY_COOLDOWN_DAYS)
        company_lower = company_name.lower()

        recent_count_result = await db.scalar(
            select(func.count()).select_from(Application).where(
                Application.user_id == user_id,
                func.lower(Application.company_name) == company_lower,
                Application.created_at >= cutoff,
            )
        )
        recent_count = recent_count_result or 0

        return SafetyCheck(
            name="company_cooldown",
            passed=recent_count == 0,
            detail=(
                f"Applied to {recent_count} roles at {company_name} "
                f"in last {self.SAME_COMPANY_COOLDOWN_DAYS} days"
                if recent_count > 0
                else f"No recent applications to {company_name}"
            ),
        )

    def _check_blacklist(
        self,
        company_name: str | None,
        job_title: str | None,
        blacklisted_companies: list[str],
        blacklisted_keywords: list[str],
    ) -> SafetyCheck:
        """Check 3: Company or role keyword blacklist."""
        if company_name and blacklisted_companies:
            company_lower = company_name.lower()
            for blocked in blacklisted_companies:
                if blocked.lower() in company_lower:
                    return SafetyCheck(
                        name="blacklist",
                        passed=False,
                        detail=f"Company '{company_name}' is blacklisted",
                    )

        if job_title and blacklisted_keywords:
            title_lower = job_title.lower()
            for keyword in blacklisted_keywords:
                if keyword.lower() in title_lower:
                    return SafetyCheck(
                        name="blacklist",
                        passed=False,
                        detail=f"Job title contains blacklisted keyword '{keyword}'",
                    )

        return SafetyCheck(
            name="blacklist",
            passed=True,
            detail="Not blacklisted",
        )

    def _check_budget(self, daily_spend: float) -> SafetyCheck:
        """Check 4: Budget/API credit limit."""
        return SafetyCheck(
            name="budget",
            passed=daily_spend < self.DAILY_BUDGET_LIMIT,
            detail=f"${daily_spend:.2f}/${self.DAILY_BUDGET_LIMIT:.2f} spent today",
        )

    def _check_freshness(self, first_seen_at: datetime | None) -> SafetyCheck:
        """Check: Stale posting detection."""
        if not first_seen_at:
            return SafetyCheck(
                name="freshness",
                passed=True,
                detail="No first_seen_at — assuming fresh",
            )

        now = datetime.now(UTC)
        # Handle naive datetimes by assuming UTC
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
        """Check 5: Human-in-the-loop for ATS types the user hasn't used before."""
        if not ats_provider:
            return SafetyCheck(
                name="first_time_ats",
                passed=True,
                detail="No ATS detected — generic flow",
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
            detail=f"First time using ATS '{ats_provider}' — requires confirmation",
        )

    def mark_ats_known(self, ats_provider: str) -> None:
        """Mark an ATS type as known (user has confirmed it)."""
        self._known_ats_types.add(ats_provider)
