"""
Module 3 — Validated Source Cache: Service Layer.

Provides SourceCacheService with:
  - Source registration (idempotent)
  - Health state machine transitions
  - Exponential backoff with persistent state
  - Quality scoring
  - Priority queue for scheduler integration
  - Manual override support
  - Check log querying and stats

All database operations use the supplied AsyncSession. The caller is
responsible for committing or rolling back. Write operations are designed
to be batched where possible for SQLite safety.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func as sa_func, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.phase7a.constants import (
    BACKOFF_SCHEDULE,
    CheckStatus,
    CheckType,
    HEALTH_DEAD_THRESHOLD,
    HEALTH_DEGRADED_THRESHOLD,
    HEALTH_FAILING_THRESHOLD,
    HealthState,
    SourceType,
)
from backend.phase7a.id_utils import compute_source_id
from backend.phase7a.m3_models import SourceCheckLog, SourceRegistry

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


class SourceCacheService:
    """Service layer for the Validated Source Cache (Module 3).

    All methods accept an AsyncSession and return model instances or
    computed values. The session is NOT committed automatically — callers
    must manage transaction boundaries.
    """

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    async def register_source(
        self,
        session: AsyncSession,
        source_type: str,
        url: str,
        company_id: Optional[str] = None,
    ) -> SourceRegistry:
        """Register a new source or return the existing one (idempotent).

        Args:
            session: Active async session.
            source_type: One of SourceType values.
            url: Base URL or endpoint.
            company_id: Optional soft FK to companies table.

        Returns:
            The existing or newly created SourceRegistry row.
        """
        sid = compute_source_id(source_type, url)

        existing = await self.get_source(session, sid)
        if existing is not None:
            return existing

        now = _utcnow()
        source = SourceRegistry(
            source_id=sid,
            source_type=source_type,
            url=url,
            company_id=company_id,
            health_state=HealthState.UNKNOWN.value,
            quality_score=50,
            success_count=0,
            failure_count=0,
            consecutive_failures=0,
            rate_limit_hits=0,
            robots_compliant=True,
            created_at=now,
        )
        session.add(source)
        await session.flush()
        return source

    async def get_source(
        self,
        session: AsyncSession,
        source_id: str,
    ) -> Optional[SourceRegistry]:
        """Retrieve a single source by its ID.

        Returns None if not found.
        """
        result = await session.execute(
            select(SourceRegistry).where(SourceRegistry.source_id == source_id)
        )
        return result.scalar_one_or_none()

    async def list_sources(
        self,
        session: AsyncSession,
        source_type: Optional[str] = None,
        health_state: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> list[SourceRegistry]:
        """List sources with optional filters.

        Args:
            session: Active async session.
            source_type: Filter by source type (e.g. "greenhouse").
            health_state: Filter by health state (e.g. "healthy").
            company_id: Filter by company ID.

        Returns:
            List of matching SourceRegistry rows.
        """
        stmt = select(SourceRegistry)

        if source_type is not None:
            stmt = stmt.where(SourceRegistry.source_type == source_type)
        if health_state is not None:
            stmt = stmt.where(SourceRegistry.health_state == health_state)
        if company_id is not None:
            stmt = stmt.where(SourceRegistry.company_id == company_id)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_source(
        self,
        session: AsyncSession,
        source_id: str,
        **fields,
    ) -> Optional[SourceRegistry]:
        """Update arbitrary fields on a source.

        Args:
            source_id: The source to update.
            **fields: Column name -> value pairs.

        Returns:
            Updated SourceRegistry or None if not found.
        """
        source = await self.get_source(session, source_id)
        if source is None:
            return None

        for key, value in fields.items():
            if hasattr(source, key):
                setattr(source, key, value)

        source.updated_at = _utcnow()
        await session.flush()
        return source

    # ------------------------------------------------------------------
    # Health Tracking
    # ------------------------------------------------------------------

    async def record_check(
        self,
        session: AsyncSession,
        source_id: str,
        check_type: str,
        status: str,
        http_status: Optional[int] = None,
        jobs_found: Optional[int] = None,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> tuple[SourceCheckLog, SourceRegistry]:
        """Record a check result and update source health.

        This is the main entry point for scrapers to report outcomes.
        It creates a SourceCheckLog entry, updates counters and averages
        on the SourceRegistry, and transitions the health state machine.

        Args:
            source_id: The source being checked.
            check_type: One of CheckType values.
            status: One of CheckStatus values.
            http_status: HTTP response code, if applicable.
            jobs_found: Number of jobs found (success only).
            duration_ms: Elapsed time in milliseconds.
            error_message: Error details (failure/timeout only).

        Returns:
            Tuple of (created SourceCheckLog, updated SourceRegistry).

        Raises:
            ValueError: If source_id does not exist.
        """
        source = await self.get_source(session, source_id)
        if source is None:
            raise ValueError(f"Source not found: {source_id}")

        now = _utcnow()

        # Create check log entry
        log_entry = SourceCheckLog(
            source_id=source_id,
            check_type=check_type,
            status=status,
            http_status=http_status,
            jobs_found=jobs_found,
            duration_ms=duration_ms,
            error_message=error_message,
            checked_at=now,
        )
        session.add(log_entry)

        # Update source based on check outcome
        source.last_check_at = now

        if status == CheckStatus.SUCCESS.value:
            self._handle_success(source, now, jobs_found, duration_ms)
        elif status == CheckStatus.RATE_LIMITED.value:
            self._handle_rate_limited(source, now, error_message)
        else:
            # FAILURE or TIMEOUT
            self._handle_failure(source, now, error_message)

        # Transition health state
        self._update_health_state(source)

        source.updated_at = now
        await session.flush()
        return log_entry, source

    def _handle_success(
        self,
        source: SourceRegistry,
        now: datetime,
        jobs_found: Optional[int],
        duration_ms: Optional[int],
    ) -> None:
        """Update source counters for a successful check."""
        source.success_count += 1
        source.consecutive_failures = 0
        source.last_success_at = now
        source.backoff_until = None

        # Rolling average for job yield
        if jobs_found is not None and jobs_found >= 0:
            n = source.success_count
            if source.avg_job_yield is None or n <= 1:
                source.avg_job_yield = float(jobs_found)
            else:
                source.avg_job_yield = (
                    (source.avg_job_yield * (n - 1) + jobs_found) / n
                )

        # Rolling average for response time
        if duration_ms is not None and duration_ms >= 0:
            n = source.success_count
            if source.avg_response_time_ms is None or n <= 1:
                source.avg_response_time_ms = duration_ms
            else:
                source.avg_response_time_ms = int(
                    (source.avg_response_time_ms * (n - 1) + duration_ms) / n
                )

    def _handle_failure(
        self,
        source: SourceRegistry,
        now: datetime,
        error_message: Optional[str],
    ) -> None:
        """Update source counters for a failed/timed-out check."""
        source.failure_count += 1
        source.consecutive_failures += 1
        source.last_failure_at = now
        source.backoff_until = self._calculate_backoff(
            source.consecutive_failures, rate_limited=False
        )

    def _handle_rate_limited(
        self,
        source: SourceRegistry,
        now: datetime,
        error_message: Optional[str],
    ) -> None:
        """Update source counters for a rate-limited check (429)."""
        source.failure_count += 1
        source.consecutive_failures += 1
        source.rate_limit_hits += 1
        source.last_failure_at = now
        source.backoff_until = self._calculate_backoff(
            source.consecutive_failures, rate_limited=True
        )

    def _update_health_state(self, source: SourceRegistry) -> str:
        """Transition the health state machine based on consecutive failures.

        State transitions:
          - On success (consecutive_failures == 0): always -> healthy
          - On failure:
            - consecutive_failures >= DEAD_THRESHOLD    -> dead
            - consecutive_failures >= FAILING_THRESHOLD  -> failing
            - consecutive_failures >= DEGRADED_THRESHOLD -> degraded

        Returns:
            The new health state value.
        """
        if source.consecutive_failures == 0:
            # Any single success transitions back to healthy
            source.health_state = HealthState.HEALTHY.value
        elif source.consecutive_failures >= HEALTH_DEAD_THRESHOLD:
            source.health_state = HealthState.DEAD.value
        elif source.consecutive_failures >= HEALTH_FAILING_THRESHOLD:
            source.health_state = HealthState.FAILING.value
        elif source.consecutive_failures >= HEALTH_DEGRADED_THRESHOLD:
            source.health_state = HealthState.DEGRADED.value
        # else: stay in current state (fewer than DEGRADED_THRESHOLD failures)

        return source.health_state

    # ------------------------------------------------------------------
    # Backoff Management
    # ------------------------------------------------------------------

    def _calculate_backoff(
        self,
        consecutive_failures: int,
        rate_limited: bool = False,
    ) -> datetime:
        """Calculate when a source should be retried.

        Uses BACKOFF_SCHEDULE from constants: finds the highest threshold
        that consecutive_failures meets, then uses that duration.
        Rate-limited checks get 2x the normal backoff.

        Args:
            consecutive_failures: Current failure streak.
            rate_limited: Whether this was a 429/rate-limit response.

        Returns:
            Datetime when the backoff period ends.
        """
        # BACKOFF_SCHEDULE is sorted ascending by threshold.
        # Walk backwards to find the highest matching threshold.
        duration_seconds = BACKOFF_SCHEDULE[0][1]  # Default: first entry
        for threshold, duration in reversed(BACKOFF_SCHEDULE):
            if consecutive_failures >= threshold:
                duration_seconds = duration
                break

        if rate_limited:
            duration_seconds *= 2

        return _utcnow() + timedelta(seconds=duration_seconds)

    async def is_in_backoff(
        self,
        session: AsyncSession,
        source_id: str,
    ) -> bool:
        """Check whether a source is currently in a backoff period.

        Returns False if the source doesn't exist or has no backoff set.
        """
        source = await self.get_source(session, source_id)
        if source is None:
            return False
        if source.backoff_until is None:
            return False
        backoff = source.backoff_until
        # Handle naive datetimes from SQLite storage
        if backoff.tzinfo is None:
            backoff = backoff.replace(tzinfo=timezone.utc)
        return backoff > _utcnow()

    async def clear_backoff(
        self,
        session: AsyncSession,
        source_id: str,
    ) -> Optional[SourceRegistry]:
        """Clear the backoff period for a source.

        Returns the updated source or None if not found.
        """
        source = await self.get_source(session, source_id)
        if source is None:
            return None

        source.backoff_until = None
        source.updated_at = _utcnow()
        await session.flush()
        return source

    # ------------------------------------------------------------------
    # Quality Scoring
    # ------------------------------------------------------------------

    async def calculate_quality_score(
        self,
        session: AsyncSession,
        source_id: str,
    ) -> int:
        """Calculate and persist the quality score for a source.

        Formula:
          quality_score = (success_rate * 40) + (freshness_score * 30)
                        + (yield_score * 20) + (latency_score * 10)

        Where:
          success_rate   = success_count / (success_count + failure_count)
          freshness_score = max(0, 1 - (hours_since_success / 168))
          yield_score    = min(1, avg_job_yield / 50)
          latency_score  = max(0, 1 - (avg_response_time_ms / 5000))

        Returns:
            The computed quality score (0-100), or 0 if source not found.
        """
        source = await self.get_source(session, source_id)
        if source is None:
            return 0

        score = self._compute_quality_score(source)
        source.quality_score = score
        source.updated_at = _utcnow()
        await session.flush()
        return score

    def _compute_quality_score(self, source: SourceRegistry) -> int:
        """Pure computation of quality score from source fields."""
        total_checks = source.success_count + source.failure_count

        # Success rate component (0-40 points)
        if total_checks == 0:
            success_rate = 0.5  # Neutral for unchecked sources
        else:
            success_rate = source.success_count / total_checks
        success_component = success_rate * 40

        # Freshness component (0-30 points)
        if source.last_success_at is not None:
            now = _utcnow()
            last_success = source.last_success_at
            # Make last_success timezone-aware if it isn't
            if last_success.tzinfo is None:
                last_success = last_success.replace(tzinfo=timezone.utc)
            hours_since = (now - last_success).total_seconds() / 3600
            freshness_score = max(0.0, 1.0 - (hours_since / 168.0))
        else:
            freshness_score = 0.0
        freshness_component = freshness_score * 30

        # Yield component (0-20 points)
        if source.avg_job_yield is not None and source.avg_job_yield > 0:
            yield_score = min(1.0, source.avg_job_yield / 50.0)
        else:
            yield_score = 0.0
        yield_component = yield_score * 20

        # Latency component (0-10 points)
        if source.avg_response_time_ms is not None and source.avg_response_time_ms >= 0:
            latency_score = max(0.0, 1.0 - (source.avg_response_time_ms / 5000.0))
        else:
            latency_score = 0.5  # Neutral if unknown
        latency_component = latency_score * 10

        total = success_component + freshness_component + yield_component + latency_component
        return max(0, min(100, int(round(total))))

    async def recalculate_all_quality_scores(
        self,
        session: AsyncSession,
    ) -> int:
        """Recalculate quality scores for all sources.

        Returns:
            Count of sources updated.
        """
        sources = await self.list_sources(session)
        count = 0
        for source in sources:
            score = self._compute_quality_score(source)
            if source.quality_score != score:
                source.quality_score = score
                source.updated_at = _utcnow()
                count += 1
        await session.flush()
        return count

    # ------------------------------------------------------------------
    # Priority Queue
    # ------------------------------------------------------------------

    async def get_priority_queue(
        self,
        session: AsyncSession,
        source_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[SourceRegistry]:
        """Get the priority-ordered queue of sources to scrape next.

        Returns sources ordered by:
          1. manual_enabled=TRUE first
          2. quality_score DESC

        Excludes:
          - Sources currently in backoff (backoff_until > now)
          - Sources with manual_enabled=FALSE
          - Dead sources (unless manual_enabled=TRUE)
          - Sources whose next_check_at is in the future

        Args:
            source_type: Optional filter by source type.
            limit: Maximum number of sources to return.

        Returns:
            Ordered list of SourceRegistry rows.
        """
        now = _utcnow()

        stmt = select(SourceRegistry)

        # Filter by source type
        if source_type is not None:
            stmt = stmt.where(SourceRegistry.source_type == source_type)

        # Exclude manually disabled sources
        stmt = stmt.where(
            or_(
                SourceRegistry.manual_enabled.is_(None),
                SourceRegistry.manual_enabled == True,  # noqa: E712
            )
        )

        # Exclude sources in backoff
        stmt = stmt.where(
            or_(
                SourceRegistry.backoff_until.is_(None),
                SourceRegistry.backoff_until <= now,
            )
        )

        # Exclude dead sources unless manually enabled
        stmt = stmt.where(
            or_(
                SourceRegistry.health_state != HealthState.DEAD.value,
                SourceRegistry.manual_enabled == True,  # noqa: E712
            )
        )

        # Respect next_check_at: only include if NULL or <= now
        stmt = stmt.where(
            or_(
                SourceRegistry.next_check_at.is_(None),
                SourceRegistry.next_check_at <= now,
            )
        )

        # Order: manual_enabled=TRUE first, then by quality_score DESC
        stmt = stmt.order_by(
            # TRUE (1) sorts after NULL/FALSE normally, so we use DESC
            # CASE to put manual_enabled=TRUE first
            case(
                (SourceRegistry.manual_enabled == True, 0),  # noqa: E712
                else_=1,
            ).asc(),
            SourceRegistry.quality_score.desc(),
        )

        stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Manual Override
    # ------------------------------------------------------------------

    async def set_manual_override(
        self,
        session: AsyncSession,
        source_id: str,
        enabled: bool,
    ) -> Optional[SourceRegistry]:
        """Set manual override on a source.

        If enabled=TRUE and source is dead, transitions to 'unknown'
        to give it another chance.

        Args:
            source_id: The source to override.
            enabled: True to force-enable, False to force-disable.

        Returns:
            Updated SourceRegistry or None if not found.
        """
        source = await self.get_source(session, source_id)
        if source is None:
            return None

        source.manual_enabled = enabled
        source.updated_at = _utcnow()

        # If re-enabling a dead source, give it another chance
        if enabled and source.health_state == HealthState.DEAD.value:
            source.health_state = HealthState.UNKNOWN.value
            source.backoff_until = None

        await session.flush()
        return source

    async def clear_manual_override(
        self,
        session: AsyncSession,
        source_id: str,
    ) -> Optional[SourceRegistry]:
        """Remove manual override, returning to auto behavior.

        Sets manual_enabled = NULL.
        """
        source = await self.get_source(session, source_id)
        if source is None:
            return None

        source.manual_enabled = None
        source.updated_at = _utcnow()
        await session.flush()
        return source

    # ------------------------------------------------------------------
    # Check Log Queries
    # ------------------------------------------------------------------

    async def get_recent_checks(
        self,
        session: AsyncSession,
        source_id: str,
        limit: int = 20,
    ) -> list[SourceCheckLog]:
        """Get the most recent check log entries for a source.

        Args:
            source_id: The source to query.
            limit: Maximum number of entries.

        Returns:
            List of SourceCheckLog rows, newest first.
        """
        stmt = (
            select(SourceCheckLog)
            .where(SourceCheckLog.source_id == source_id)
            .order_by(SourceCheckLog.checked_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_check_stats(
        self,
        session: AsyncSession,
        source_id: str,
        days: int = 7,
    ) -> dict:
        """Get aggregated check statistics for a source over a time window.

        Args:
            source_id: The source to query.
            days: Number of days to look back.

        Returns:
            Dict with keys: success_rate, avg_yield, avg_latency, total_checks.
        """
        cutoff = _utcnow() - timedelta(days=days)

        # Total checks in window
        total_result = await session.execute(
            select(sa_func.count(SourceCheckLog.id))
            .where(SourceCheckLog.source_id == source_id)
            .where(SourceCheckLog.checked_at >= cutoff)
        )
        total_checks = total_result.scalar() or 0

        # Successes in window
        success_result = await session.execute(
            select(sa_func.count(SourceCheckLog.id))
            .where(SourceCheckLog.source_id == source_id)
            .where(SourceCheckLog.checked_at >= cutoff)
            .where(SourceCheckLog.status == CheckStatus.SUCCESS.value)
        )
        success_count = success_result.scalar() or 0

        # Average yield for successes
        yield_result = await session.execute(
            select(sa_func.avg(SourceCheckLog.jobs_found))
            .where(SourceCheckLog.source_id == source_id)
            .where(SourceCheckLog.checked_at >= cutoff)
            .where(SourceCheckLog.status == CheckStatus.SUCCESS.value)
            .where(SourceCheckLog.jobs_found.isnot(None))
        )
        avg_yield = yield_result.scalar()

        # Average latency for successes
        latency_result = await session.execute(
            select(sa_func.avg(SourceCheckLog.duration_ms))
            .where(SourceCheckLog.source_id == source_id)
            .where(SourceCheckLog.checked_at >= cutoff)
            .where(SourceCheckLog.status == CheckStatus.SUCCESS.value)
            .where(SourceCheckLog.duration_ms.isnot(None))
        )
        avg_latency = latency_result.scalar()

        success_rate = (success_count / total_checks) if total_checks > 0 else 0.0

        return {
            "success_rate": round(success_rate, 4),
            "avg_yield": round(avg_yield, 2) if avg_yield is not None else None,
            "avg_latency": round(avg_latency, 2) if avg_latency is not None else None,
            "total_checks": total_checks,
        }
