"""
Tests for Module 3 — Validated Source Cache: Service Layer.

Covers:
  - Source registration (including idempotency)
  - Health state machine transitions (all paths)
  - Backoff calculation at each threshold
  - Rate-limited backoff multiplier
  - Quality scoring formula
  - Priority queue ordering and filtering
  - Manual override behavior
  - Check log and stats queries
  - Edge cases: nonexistent sources, zero checks, all sources in backoff, etc.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.database import Base
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
from backend.phase7a.m3_service import SourceCacheService


@pytest_asyncio.fixture
async def db_engine():
    """Create in-memory engine with all ORM tables."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    import backend.models  # noqa: F401
    import backend.phase7a.m3_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Provide an async session with rollback after each test."""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def service():
    """Provide a fresh SourceCacheService instance."""
    return SourceCacheService()


@pytest_asyncio.fixture
async def greenhouse_source(db_session: AsyncSession, service: SourceCacheService):
    """Create and return a test Greenhouse source."""
    return await service.register_source(
        db_session,
        source_type=SourceType.GREENHOUSE.value,
        url="https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
        company_id="stripe_company_id",
    )


# ======================================================================
# Registration
# ======================================================================


class TestRegisterSource:
    """Tests for register_source()."""

    async def test_register_new_source(self, db_session: AsyncSession, service: SourceCacheService):
        """Registering a new source creates it with correct defaults."""
        source = await service.register_source(
            db_session,
            source_type="greenhouse",
            url="https://boards-api.greenhouse.io/v1/boards/openai/jobs",
        )

        assert source is not None
        assert source.source_type == "greenhouse"
        assert source.url == "https://boards-api.greenhouse.io/v1/boards/openai/jobs"
        assert source.health_state == HealthState.UNKNOWN.value
        assert source.quality_score == 50
        assert source.success_count == 0
        assert source.failure_count == 0
        assert source.consecutive_failures == 0
        assert source.company_id is None
        assert source.manual_enabled is None

    async def test_register_source_with_company_id(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Registering with a company_id stores it as soft FK."""
        source = await service.register_source(
            db_session,
            source_type="lever",
            url="https://api.lever.co/v0/postings/stripe",
            company_id="stripe_123",
        )
        assert source.company_id == "stripe_123"

    async def test_register_source_idempotent(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Registering the same source twice returns the existing one."""
        source1 = await service.register_source(
            db_session,
            source_type="greenhouse",
            url="https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
        )
        source2 = await service.register_source(
            db_session,
            source_type="greenhouse",
            url="https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
        )
        assert source1.source_id == source2.source_id

    async def test_register_source_deterministic_id(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Source ID is deterministic based on source_type and url."""
        expected_id = compute_source_id(
            "greenhouse",
            "https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
        )
        source = await service.register_source(
            db_session,
            source_type="greenhouse",
            url="https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
        )
        assert source.source_id == expected_id


# ======================================================================
# CRUD
# ======================================================================


class TestCRUD:
    """Tests for get_source, list_sources, update_source."""

    async def test_get_source_exists(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Get an existing source by ID."""
        loaded = await service.get_source(db_session, greenhouse_source.source_id)
        assert loaded is not None
        assert loaded.source_id == greenhouse_source.source_id

    async def test_get_source_not_found(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Get a nonexistent source returns None."""
        result = await service.get_source(db_session, "nonexistent_id")
        assert result is None

    async def test_list_sources_no_filter(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """List all sources without filters."""
        await service.register_source(db_session, "greenhouse", "https://a.com")
        await service.register_source(db_session, "lever", "https://b.com")
        await service.register_source(db_session, "ashby", "https://c.com")

        sources = await service.list_sources(db_session)
        assert len(sources) == 3

    async def test_list_sources_filter_by_type(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """List sources filtered by source_type."""
        await service.register_source(db_session, "greenhouse", "https://a.com")
        await service.register_source(db_session, "greenhouse", "https://b.com")
        await service.register_source(db_session, "lever", "https://c.com")

        sources = await service.list_sources(db_session, source_type="greenhouse")
        assert len(sources) == 2
        assert all(s.source_type == "greenhouse" for s in sources)

    async def test_list_sources_filter_by_health(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """List sources filtered by health_state."""
        s1 = await service.register_source(db_session, "greenhouse", "https://a.com")
        s2 = await service.register_source(db_session, "lever", "https://b.com")

        # Make one healthy
        s1.health_state = HealthState.HEALTHY.value
        await db_session.flush()

        sources = await service.list_sources(db_session, health_state="healthy")
        assert len(sources) == 1
        assert sources[0].source_id == s1.source_id

    async def test_list_sources_filter_by_company(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """List sources filtered by company_id."""
        await service.register_source(
            db_session, "greenhouse", "https://a.com", company_id="stripe"
        )
        await service.register_source(
            db_session, "lever", "https://b.com", company_id="openai"
        )

        sources = await service.list_sources(db_session, company_id="stripe")
        assert len(sources) == 1
        assert sources[0].company_id == "stripe"

    async def test_update_source(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Update arbitrary fields on a source."""
        updated = await service.update_source(
            db_session,
            greenhouse_source.source_id,
            quality_score=95,
            robots_compliant=False,
        )
        assert updated is not None
        assert updated.quality_score == 95
        assert updated.robots_compliant is False

    async def test_update_source_not_found(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Updating a nonexistent source returns None."""
        result = await service.update_source(
            db_session, "nonexistent_id", quality_score=10
        )
        assert result is None


# ======================================================================
# Health State Machine
# ======================================================================


class TestHealthStateMachine:
    """Tests for record_check() and _update_health_state()."""

    async def test_success_transitions_to_healthy(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """A successful check transitions any state to healthy."""
        log, source = await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.SUCCESS.value,
            jobs_found=45,
            duration_ms=380,
        )

        assert source.health_state == HealthState.HEALTHY.value
        assert source.consecutive_failures == 0
        assert source.success_count == 1
        assert source.backoff_until is None

    async def test_success_from_dead_transitions_to_healthy(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """A single success from dead state transitions to healthy."""
        # Force to dead
        greenhouse_source.health_state = HealthState.DEAD.value
        greenhouse_source.consecutive_failures = 20
        await db_session.flush()

        log, source = await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.SUCCESS.value,
            jobs_found=10,
        )

        assert source.health_state == HealthState.HEALTHY.value
        assert source.consecutive_failures == 0

    async def test_failures_to_degraded(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """3 consecutive failures transition unknown -> degraded."""
        for i in range(HEALTH_DEGRADED_THRESHOLD):
            _, source = await service.record_check(
                db_session,
                greenhouse_source.source_id,
                check_type=CheckType.SCRAPE.value,
                status=CheckStatus.FAILURE.value,
                error_message=f"Error {i+1}",
            )

        assert source.health_state == HealthState.DEGRADED.value
        assert source.consecutive_failures == HEALTH_DEGRADED_THRESHOLD

    async def test_failures_to_failing(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """8 consecutive failures transition -> failing."""
        for i in range(HEALTH_FAILING_THRESHOLD):
            _, source = await service.record_check(
                db_session,
                greenhouse_source.source_id,
                check_type=CheckType.SCRAPE.value,
                status=CheckStatus.FAILURE.value,
                error_message=f"Error {i+1}",
            )

        assert source.health_state == HealthState.FAILING.value
        assert source.consecutive_failures == HEALTH_FAILING_THRESHOLD

    async def test_failures_to_dead(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """18 consecutive failures transition -> dead."""
        for i in range(HEALTH_DEAD_THRESHOLD):
            _, source = await service.record_check(
                db_session,
                greenhouse_source.source_id,
                check_type=CheckType.SCRAPE.value,
                status=CheckStatus.FAILURE.value,
                error_message=f"Error {i+1}",
            )

        assert source.health_state == HealthState.DEAD.value
        assert source.consecutive_failures == HEALTH_DEAD_THRESHOLD

    async def test_fewer_than_threshold_stays_in_current_state(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Fewer than DEGRADED_THRESHOLD failures keep state unchanged."""
        for i in range(HEALTH_DEGRADED_THRESHOLD - 1):
            _, source = await service.record_check(
                db_session,
                greenhouse_source.source_id,
                check_type=CheckType.SCRAPE.value,
                status=CheckStatus.FAILURE.value,
            )

        # Still unknown (not enough failures for degraded)
        assert source.health_state == HealthState.UNKNOWN.value
        assert source.consecutive_failures == HEALTH_DEGRADED_THRESHOLD - 1

    async def test_success_resets_consecutive_failures(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """A success after failures resets consecutive_failures to 0."""
        # Accumulate some failures
        for i in range(5):
            await service.record_check(
                db_session,
                greenhouse_source.source_id,
                check_type=CheckType.SCRAPE.value,
                status=CheckStatus.FAILURE.value,
            )

        assert greenhouse_source.consecutive_failures == 5

        # One success resets
        _, source = await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.SUCCESS.value,
            jobs_found=20,
        )

        assert source.consecutive_failures == 0
        assert source.health_state == HealthState.HEALTHY.value

    async def test_timeout_treated_as_failure(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Timeout checks increment failure counters."""
        _, source = await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.TIMEOUT.value,
            error_message="Connection timed out",
        )

        assert source.failure_count == 1
        assert source.consecutive_failures == 1
        assert source.backoff_until is not None

    async def test_record_check_nonexistent_source_raises(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Recording a check for a nonexistent source raises ValueError."""
        with pytest.raises(ValueError, match="Source not found"):
            await service.record_check(
                db_session,
                "nonexistent_source_id",
                check_type=CheckType.SCRAPE.value,
                status=CheckStatus.SUCCESS.value,
            )

    async def test_record_check_creates_log_entry(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """record_check creates a SourceCheckLog entry."""
        log, _ = await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.SUCCESS.value,
            http_status=200,
            jobs_found=30,
            duration_ms=500,
        )

        assert log.id is not None
        assert log.source_id == greenhouse_source.source_id
        assert log.check_type == "scrape"
        assert log.status == "success"
        assert log.http_status == 200
        assert log.jobs_found == 30
        assert log.duration_ms == 500


# ======================================================================
# Rolling Averages
# ======================================================================


class TestRollingAverages:
    """Tests for rolling average calculations in record_check."""

    async def test_first_success_sets_avg_directly(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """First success sets avg_job_yield and avg_response_time_ms directly."""
        _, source = await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.SUCCESS.value,
            jobs_found=40,
            duration_ms=500,
        )

        assert source.avg_job_yield == 40.0
        assert source.avg_response_time_ms == 500

    async def test_rolling_average_calculation(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Multiple successes produce rolling average."""
        # First success: yield=40, latency=500
        await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.SUCCESS.value,
            jobs_found=40,
            duration_ms=500,
        )

        # Second success: yield=60, latency=300
        _, source = await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.SUCCESS.value,
            jobs_found=60,
            duration_ms=300,
        )

        # Rolling avg: (40*1 + 60) / 2 = 50
        assert source.avg_job_yield == 50.0
        # Rolling avg: (500*1 + 300) / 2 = 400
        assert source.avg_response_time_ms == 400

    async def test_rolling_average_with_none_jobs_found(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Success with None jobs_found doesn't update avg_job_yield."""
        await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.SUCCESS.value,
            jobs_found=40,
            duration_ms=500,
        )

        _, source = await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.SUCCESS.value,
            jobs_found=None,  # No yield data
            duration_ms=300,
        )

        # avg_job_yield should remain unchanged from first success
        assert source.avg_job_yield == 40.0


# ======================================================================
# Rate Limiting
# ======================================================================


class TestRateLimiting:
    """Tests for rate-limited check handling."""

    async def test_rate_limited_increments_counters(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Rate-limited status increments rate_limit_hits and failure counters."""
        _, source = await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.RATE_LIMITED.value,
            http_status=429,
            error_message="Too many requests",
        )

        assert source.rate_limit_hits == 1
        assert source.failure_count == 1
        assert source.consecutive_failures == 1
        assert source.backoff_until is not None

    async def test_rate_limited_gets_double_backoff(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Rate-limited checks get 2x the normal backoff duration."""
        # Record a normal failure
        normal_source = await service.register_source(
            db_session, "lever", "https://api.lever.co/normal"
        )
        _, normal_after = await service.record_check(
            db_session,
            normal_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.FAILURE.value,
        )
        normal_backoff = normal_after.backoff_until

        # Record a rate-limited failure
        rl_source = await service.register_source(
            db_session, "lever", "https://api.lever.co/ratelimited"
        )
        _, rl_after = await service.record_check(
            db_session,
            rl_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.RATE_LIMITED.value,
        )
        rl_backoff = rl_after.backoff_until

        # Rate limited backoff should be further in the future
        assert rl_backoff > normal_backoff


# ======================================================================
# Backoff Management
# ======================================================================


class TestBackoffManagement:
    """Tests for backoff calculation and management."""

    def test_backoff_at_threshold_1(self, service: SourceCacheService):
        """1 failure -> 300s (5 min) backoff."""
        result = service._calculate_backoff(1, rate_limited=False)
        # Should be ~300 seconds from now
        expected_min = datetime.now(timezone.utc) + timedelta(seconds=295)
        expected_max = datetime.now(timezone.utc) + timedelta(seconds=310)
        assert expected_min <= result <= expected_max

    def test_backoff_at_threshold_3(self, service: SourceCacheService):
        """3 failures -> 1800s (30 min) backoff."""
        result = service._calculate_backoff(3, rate_limited=False)
        expected_min = datetime.now(timezone.utc) + timedelta(seconds=1795)
        expected_max = datetime.now(timezone.utc) + timedelta(seconds=1810)
        assert expected_min <= result <= expected_max

    def test_backoff_at_threshold_5(self, service: SourceCacheService):
        """5 failures -> 7200s (2h) backoff."""
        result = service._calculate_backoff(5, rate_limited=False)
        expected_min = datetime.now(timezone.utc) + timedelta(seconds=7195)
        expected_max = datetime.now(timezone.utc) + timedelta(seconds=7210)
        assert expected_min <= result <= expected_max

    def test_backoff_at_threshold_10(self, service: SourceCacheService):
        """10 failures -> 43200s (12h) backoff."""
        result = service._calculate_backoff(10, rate_limited=False)
        expected_min = datetime.now(timezone.utc) + timedelta(seconds=43195)
        expected_max = datetime.now(timezone.utc) + timedelta(seconds=43210)
        assert expected_min <= result <= expected_max

    def test_backoff_at_threshold_20(self, service: SourceCacheService):
        """20 failures -> 604800s (7 days) backoff."""
        result = service._calculate_backoff(20, rate_limited=False)
        expected_min = datetime.now(timezone.utc) + timedelta(seconds=604795)
        expected_max = datetime.now(timezone.utc) + timedelta(seconds=604810)
        assert expected_min <= result <= expected_max

    def test_backoff_between_thresholds(self, service: SourceCacheService):
        """7 failures (between 5 and 10) -> uses threshold 5 duration (7200s)."""
        result = service._calculate_backoff(7, rate_limited=False)
        expected_min = datetime.now(timezone.utc) + timedelta(seconds=7195)
        expected_max = datetime.now(timezone.utc) + timedelta(seconds=7210)
        assert expected_min <= result <= expected_max

    def test_backoff_rate_limited_doubles(self, service: SourceCacheService):
        """Rate-limited backoff is 2x normal."""
        normal = service._calculate_backoff(1, rate_limited=False)
        rate_limited = service._calculate_backoff(1, rate_limited=True)
        # rate_limited should be ~300s further than normal
        diff = (rate_limited - normal).total_seconds()
        assert 295 <= diff <= 310  # Approximately 300s difference

    async def test_is_in_backoff_true(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """is_in_backoff returns True when backoff_until is in the future."""
        greenhouse_source.backoff_until = datetime.now(timezone.utc) + timedelta(hours=1)
        await db_session.flush()

        assert await service.is_in_backoff(db_session, greenhouse_source.source_id) is True

    async def test_is_in_backoff_false_when_expired(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """is_in_backoff returns False when backoff_until is in the past."""
        greenhouse_source.backoff_until = datetime.now(timezone.utc) - timedelta(hours=1)
        await db_session.flush()

        assert await service.is_in_backoff(db_session, greenhouse_source.source_id) is False

    async def test_is_in_backoff_false_when_none(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """is_in_backoff returns False when backoff_until is None."""
        assert await service.is_in_backoff(db_session, greenhouse_source.source_id) is False

    async def test_is_in_backoff_nonexistent_source(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """is_in_backoff returns False for nonexistent source."""
        assert await service.is_in_backoff(db_session, "nonexistent") is False

    async def test_clear_backoff(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """clear_backoff removes the backoff_until value."""
        greenhouse_source.backoff_until = datetime.now(timezone.utc) + timedelta(hours=1)
        await db_session.flush()

        source = await service.clear_backoff(db_session, greenhouse_source.source_id)
        assert source is not None
        assert source.backoff_until is None

    async def test_clear_backoff_nonexistent_returns_none(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """clear_backoff returns None for nonexistent source."""
        result = await service.clear_backoff(db_session, "nonexistent")
        assert result is None


# ======================================================================
# Quality Scoring
# ======================================================================


class TestQualityScoring:
    """Tests for quality score calculation."""

    async def test_quality_score_with_zero_checks(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Quality score for a source with no checks uses neutral defaults."""
        score = await service.calculate_quality_score(
            db_session, greenhouse_source.source_id
        )
        # success_rate=0.5*40=20, freshness=0*30=0, yield=0*20=0, latency=0.5*10=5
        assert score == 25

    async def test_quality_score_perfect_source(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Quality score for a high-performing source."""
        now = datetime.now(timezone.utc)
        greenhouse_source.success_count = 100
        greenhouse_source.failure_count = 0
        greenhouse_source.last_success_at = now
        greenhouse_source.avg_job_yield = 100.0  # > 50 cap
        greenhouse_source.avg_response_time_ms = 200
        await db_session.flush()

        score = await service.calculate_quality_score(
            db_session, greenhouse_source.source_id
        )
        # success_rate=1.0*40=40, freshness=1.0*30=30, yield=1.0*20=20, latency=0.96*10=9.6
        # Total: ~99.6 -> 100
        assert score >= 95

    async def test_quality_score_failing_source(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Quality score for a poorly performing source."""
        now = datetime.now(timezone.utc)
        greenhouse_source.success_count = 5
        greenhouse_source.failure_count = 95
        greenhouse_source.last_success_at = now - timedelta(days=10)  # Stale
        greenhouse_source.avg_job_yield = 2.0
        greenhouse_source.avg_response_time_ms = 4500
        await db_session.flush()

        score = await service.calculate_quality_score(
            db_session, greenhouse_source.source_id
        )
        # Low success rate, stale, low yield, high latency
        assert score < 20

    async def test_quality_score_nonexistent_returns_zero(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Quality score for nonexistent source returns 0."""
        score = await service.calculate_quality_score(db_session, "nonexistent")
        assert score == 0

    async def test_quality_score_clamped_to_0_100(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Quality score is always between 0 and 100."""
        # Edge: all zeroes
        greenhouse_source.success_count = 0
        greenhouse_source.failure_count = 1000
        greenhouse_source.last_success_at = None
        greenhouse_source.avg_job_yield = 0.0
        greenhouse_source.avg_response_time_ms = 10000
        await db_session.flush()

        score = await service.calculate_quality_score(
            db_session, greenhouse_source.source_id
        )
        assert 0 <= score <= 100

    async def test_recalculate_all_quality_scores(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """recalculate_all_quality_scores updates all sources."""
        s1 = await service.register_source(db_session, "greenhouse", "https://a.com")
        s2 = await service.register_source(db_session, "lever", "https://b.com")

        # Make them different
        s1.success_count = 100
        s1.failure_count = 0
        s1.last_success_at = datetime.now(timezone.utc)
        s1.avg_job_yield = 50.0
        s1.avg_response_time_ms = 200

        s2.success_count = 5
        s2.failure_count = 95
        await db_session.flush()

        count = await service.recalculate_all_quality_scores(db_session)
        assert count >= 1  # At least one score changed

        assert s1.quality_score != s2.quality_score


# ======================================================================
# Priority Queue
# ======================================================================


class TestPriorityQueue:
    """Tests for get_priority_queue()."""

    async def test_priority_queue_ordered_by_quality(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Priority queue is ordered by quality_score DESC."""
        s1 = await service.register_source(db_session, "greenhouse", "https://a.com")
        s2 = await service.register_source(db_session, "lever", "https://b.com")
        s3 = await service.register_source(db_session, "ashby", "https://c.com")

        s1.quality_score = 90
        s2.quality_score = 50
        s3.quality_score = 75
        await db_session.flush()

        queue = await service.get_priority_queue(db_session)
        assert len(queue) == 3
        assert queue[0].quality_score >= queue[1].quality_score
        assert queue[1].quality_score >= queue[2].quality_score

    async def test_priority_queue_excludes_backoff(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Sources in backoff are excluded from the queue."""
        s1 = await service.register_source(db_session, "greenhouse", "https://a.com")
        s2 = await service.register_source(db_session, "lever", "https://b.com")

        s1.backoff_until = datetime.now(timezone.utc) + timedelta(hours=1)
        await db_session.flush()

        queue = await service.get_priority_queue(db_session)
        source_ids = [s.source_id for s in queue]
        assert s1.source_id not in source_ids
        assert s2.source_id in source_ids

    async def test_priority_queue_excludes_manually_disabled(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Sources with manual_enabled=FALSE are excluded."""
        s1 = await service.register_source(db_session, "greenhouse", "https://a.com")
        s2 = await service.register_source(db_session, "lever", "https://b.com")

        s1.manual_enabled = False
        await db_session.flush()

        queue = await service.get_priority_queue(db_session)
        source_ids = [s.source_id for s in queue]
        assert s1.source_id not in source_ids
        assert s2.source_id in source_ids

    async def test_priority_queue_excludes_dead_unless_manual(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Dead sources are excluded unless manual_enabled=TRUE."""
        s1 = await service.register_source(db_session, "greenhouse", "https://a.com")
        s2 = await service.register_source(db_session, "lever", "https://b.com")

        s1.health_state = HealthState.DEAD.value
        s2.health_state = HealthState.DEAD.value
        s2.manual_enabled = True
        await db_session.flush()

        queue = await service.get_priority_queue(db_session)
        source_ids = [s.source_id for s in queue]
        assert s1.source_id not in source_ids
        assert s2.source_id in source_ids

    async def test_priority_queue_manual_enabled_first(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Manually enabled sources appear before auto sources."""
        s1 = await service.register_source(db_session, "greenhouse", "https://a.com")
        s2 = await service.register_source(db_session, "lever", "https://b.com")

        s1.quality_score = 90
        s1.manual_enabled = None  # auto
        s2.quality_score = 50
        s2.manual_enabled = True
        await db_session.flush()

        queue = await service.get_priority_queue(db_session)
        assert queue[0].source_id == s2.source_id  # manual first despite lower score

    async def test_priority_queue_respects_next_check_at(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Sources with next_check_at in the future are excluded."""
        s1 = await service.register_source(db_session, "greenhouse", "https://a.com")
        s2 = await service.register_source(db_session, "lever", "https://b.com")

        s1.next_check_at = datetime.now(timezone.utc) + timedelta(hours=1)  # Future
        s2.next_check_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Past
        await db_session.flush()

        queue = await service.get_priority_queue(db_session)
        source_ids = [s.source_id for s in queue]
        assert s1.source_id not in source_ids
        assert s2.source_id in source_ids

    async def test_priority_queue_filter_by_source_type(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Priority queue can filter by source_type."""
        await service.register_source(db_session, "greenhouse", "https://a.com")
        await service.register_source(db_session, "lever", "https://b.com")

        queue = await service.get_priority_queue(db_session, source_type="greenhouse")
        assert len(queue) == 1
        assert queue[0].source_type == "greenhouse"

    async def test_priority_queue_limit(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Priority queue respects limit parameter."""
        for i in range(5):
            await service.register_source(
                db_session, "greenhouse", f"https://example.com/{i}"
            )

        queue = await service.get_priority_queue(db_session, limit=3)
        assert len(queue) == 3

    async def test_priority_queue_all_in_backoff_returns_empty(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """If all sources are in backoff, queue is empty."""
        s1 = await service.register_source(db_session, "greenhouse", "https://a.com")
        s2 = await service.register_source(db_session, "lever", "https://b.com")

        future = datetime.now(timezone.utc) + timedelta(hours=1)
        s1.backoff_until = future
        s2.backoff_until = future
        await db_session.flush()

        queue = await service.get_priority_queue(db_session)
        assert len(queue) == 0


# ======================================================================
# Manual Override
# ======================================================================


class TestManualOverride:
    """Tests for set_manual_override and clear_manual_override."""

    async def test_set_manual_override_enable(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Setting manual_enabled=True force-enables a source."""
        source = await service.set_manual_override(
            db_session, greenhouse_source.source_id, enabled=True
        )
        assert source.manual_enabled is True

    async def test_set_manual_override_disable(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Setting manual_enabled=False force-disables a source."""
        source = await service.set_manual_override(
            db_session, greenhouse_source.source_id, enabled=False
        )
        assert source.manual_enabled is False

    async def test_set_manual_override_dead_source_resets_to_unknown(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Enabling a dead source transitions it to 'unknown'."""
        greenhouse_source.health_state = HealthState.DEAD.value
        greenhouse_source.backoff_until = datetime.now(timezone.utc) + timedelta(days=7)
        await db_session.flush()

        source = await service.set_manual_override(
            db_session, greenhouse_source.source_id, enabled=True
        )
        assert source.health_state == HealthState.UNKNOWN.value
        assert source.backoff_until is None

    async def test_set_manual_override_nonexistent_returns_none(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Setting override on nonexistent source returns None."""
        result = await service.set_manual_override(
            db_session, "nonexistent", enabled=True
        )
        assert result is None

    async def test_clear_manual_override(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """Clearing manual override sets manual_enabled to None."""
        greenhouse_source.manual_enabled = True
        await db_session.flush()

        source = await service.clear_manual_override(
            db_session, greenhouse_source.source_id
        )
        assert source.manual_enabled is None

    async def test_clear_manual_override_nonexistent_returns_none(
        self, db_session: AsyncSession, service: SourceCacheService
    ):
        """Clearing override on nonexistent source returns None."""
        result = await service.clear_manual_override(db_session, "nonexistent")
        assert result is None


# ======================================================================
# Check Log Queries
# ======================================================================


class TestCheckLogQueries:
    """Tests for get_recent_checks and get_check_stats."""

    async def test_get_recent_checks(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """get_recent_checks returns check logs newest first."""
        for i in range(5):
            await service.record_check(
                db_session,
                greenhouse_source.source_id,
                check_type=CheckType.SCRAPE.value,
                status=CheckStatus.SUCCESS.value if i % 2 == 0 else CheckStatus.FAILURE.value,
                jobs_found=10 * i if i % 2 == 0 else None,
            )

        checks = await service.get_recent_checks(
            db_session, greenhouse_source.source_id
        )
        assert len(checks) == 5

    async def test_get_recent_checks_limit(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """get_recent_checks respects limit."""
        for i in range(10):
            await service.record_check(
                db_session,
                greenhouse_source.source_id,
                check_type=CheckType.SCRAPE.value,
                status=CheckStatus.SUCCESS.value,
            )

        checks = await service.get_recent_checks(
            db_session, greenhouse_source.source_id, limit=3
        )
        assert len(checks) == 3

    async def test_get_check_stats(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """get_check_stats returns aggregated stats."""
        # 3 successes with jobs_found and duration
        for _ in range(3):
            await service.record_check(
                db_session,
                greenhouse_source.source_id,
                check_type=CheckType.SCRAPE.value,
                status=CheckStatus.SUCCESS.value,
                jobs_found=30,
                duration_ms=400,
            )

        # 1 failure
        await service.record_check(
            db_session,
            greenhouse_source.source_id,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.FAILURE.value,
        )

        stats = await service.get_check_stats(
            db_session, greenhouse_source.source_id, days=7
        )

        assert stats["total_checks"] == 4
        assert stats["success_rate"] == 0.75
        assert stats["avg_yield"] == 30.0
        assert stats["avg_latency"] == 400.0

    async def test_get_check_stats_no_checks(
        self, db_session: AsyncSession, service: SourceCacheService, greenhouse_source
    ):
        """get_check_stats with no checks returns zero/null stats."""
        stats = await service.get_check_stats(
            db_session, greenhouse_source.source_id, days=7
        )

        assert stats["total_checks"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_yield"] is None
        assert stats["avg_latency"] is None
