"""
Tests for Module 3 — Validated Source Cache: ORM Models.

Covers:
  - SourceRegistry creation with defaults
  - SourceCheckLog creation
  - Column types and defaults
  - Model repr
  - Round-trip CRUD through async session
  - Table index existence
  - Backward compatibility with existing models
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.database import Base
from backend.phase7a.m3_models import SourceCheckLog, SourceRegistry
from backend.phase7a.constants import HealthState, SourceType, CheckType, CheckStatus
from backend.phase7a.id_utils import compute_source_id


@pytest_asyncio.fixture
async def db_engine():
    """Create in-memory engine with all ORM tables."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    # Import all models so Base.metadata knows about them
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


class TestSourceRegistryModel:
    """Tests for the SourceRegistry ORM model."""

    async def test_create_source_registry_defaults(self, db_session: AsyncSession):
        """Verify default values are applied on insert."""
        source = SourceRegistry(
            source_id="abc123" * 10 + "abcd",  # 64 chars
            source_type=SourceType.GREENHOUSE.value,
            url="https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(source)
        await db_session.flush()

        assert source.health_state == "unknown"
        assert source.quality_score == 50
        assert source.success_count == 0
        assert source.failure_count == 0
        assert source.consecutive_failures == 0
        assert source.rate_limit_hits == 0
        assert source.robots_compliant is True
        assert source.manual_enabled is None
        assert source.company_id is None
        assert source.last_success_at is None
        assert source.last_failure_at is None
        assert source.last_check_at is None
        assert source.next_check_at is None
        assert source.backoff_until is None
        assert source.avg_job_yield is None
        assert source.avg_response_time_ms is None

    async def test_create_source_registry_full(self, db_session: AsyncSession):
        """Create a fully populated SourceRegistry row."""
        now = datetime.now(timezone.utc)
        sid = compute_source_id("greenhouse", "https://example.com/jobs")

        source = SourceRegistry(
            source_id=sid,
            source_type=SourceType.GREENHOUSE.value,
            url="https://example.com/jobs",
            company_id="company_abc123",
            health_state=HealthState.HEALTHY.value,
            quality_score=87,
            success_count=145,
            failure_count=3,
            consecutive_failures=0,
            last_success_at=now,
            last_failure_at=now,
            last_check_at=now,
            next_check_at=now,
            backoff_until=None,
            avg_job_yield=127.5,
            avg_response_time_ms=450,
            robots_compliant=True,
            rate_limit_hits=2,
            manual_enabled=None,
            created_at=now,
            updated_at=now,
        )
        db_session.add(source)
        await db_session.flush()

        assert source.source_id == sid
        assert source.quality_score == 87
        assert source.avg_job_yield == 127.5
        assert source.avg_response_time_ms == 450

    async def test_source_registry_round_trip(self, db_session: AsyncSession):
        """Insert, read back, and verify a SourceRegistry row."""
        from sqlalchemy import select

        sid = compute_source_id("lever", "https://api.lever.co/v0/postings/stripe")
        now = datetime.now(timezone.utc)

        source = SourceRegistry(
            source_id=sid,
            source_type="lever",
            url="https://api.lever.co/v0/postings/stripe",
            health_state="healthy",
            quality_score=92,
            success_count=50,
            failure_count=1,
            consecutive_failures=0,
            created_at=now,
        )
        db_session.add(source)
        await db_session.commit()

        result = await db_session.execute(
            select(SourceRegistry).where(SourceRegistry.source_id == sid)
        )
        loaded = result.scalar_one()

        assert loaded.source_type == "lever"
        assert loaded.url == "https://api.lever.co/v0/postings/stripe"
        assert loaded.health_state == "healthy"
        assert loaded.quality_score == 92

    async def test_source_registry_update(self, db_session: AsyncSession):
        """Verify field updates persist."""
        sid = compute_source_id("ashby", "https://api.ashbyhq.com/test")
        now = datetime.now(timezone.utc)

        source = SourceRegistry(
            source_id=sid,
            source_type="ashby",
            url="https://api.ashbyhq.com/test",
            health_state="unknown",
            created_at=now,
        )
        db_session.add(source)
        await db_session.flush()

        source.health_state = "degraded"
        source.consecutive_failures = 5
        source.quality_score = 30
        await db_session.flush()

        assert source.health_state == "degraded"
        assert source.consecutive_failures == 5
        assert source.quality_score == 30

    async def test_source_registry_repr(self, db_session: AsyncSession):
        """Verify the __repr__ output."""
        source = SourceRegistry(
            source_id="test_repr_id",
            source_type="serpapi",
            url="https://serpapi.com/search",
            health_state="healthy",
            created_at=datetime.now(timezone.utc),
        )
        repr_str = repr(source)
        assert "test_repr_id" in repr_str
        assert "serpapi" in repr_str
        assert "healthy" in repr_str

    async def test_source_registry_all_source_types(self, db_session: AsyncSession):
        """Verify all SourceType enum values can be stored."""
        now = datetime.now(timezone.utc)
        for st in SourceType:
            sid = compute_source_id(st.value, f"https://example.com/{st.value}")
            source = SourceRegistry(
                source_id=sid,
                source_type=st.value,
                url=f"https://example.com/{st.value}",
                created_at=now,
            )
            db_session.add(source)
        await db_session.flush()

        from sqlalchemy import select
        result = await db_session.execute(select(SourceRegistry))
        all_sources = result.scalars().all()
        assert len(all_sources) == len(SourceType)


class TestSourceCheckLogModel:
    """Tests for the SourceCheckLog ORM model."""

    async def test_create_check_log(self, db_session: AsyncSession):
        """Create a basic check log entry."""
        now = datetime.now(timezone.utc)

        # First create a source (FK target)
        sid = compute_source_id("greenhouse", "https://example.com/jobs")
        source = SourceRegistry(
            source_id=sid,
            source_type="greenhouse",
            url="https://example.com/jobs",
            created_at=now,
        )
        db_session.add(source)
        await db_session.flush()

        log = SourceCheckLog(
            source_id=sid,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.SUCCESS.value,
            http_status=200,
            jobs_found=45,
            duration_ms=380,
            checked_at=now,
        )
        db_session.add(log)
        await db_session.flush()

        assert log.id is not None
        assert log.source_id == sid
        assert log.check_type == "scrape"
        assert log.status == "success"
        assert log.http_status == 200
        assert log.jobs_found == 45
        assert log.duration_ms == 380
        assert log.error_message is None

    async def test_create_check_log_failure(self, db_session: AsyncSession):
        """Create a failure check log entry with error message."""
        now = datetime.now(timezone.utc)
        sid = compute_source_id("serpapi", "https://serpapi.com/search")

        source = SourceRegistry(
            source_id=sid,
            source_type="serpapi",
            url="https://serpapi.com/search",
            created_at=now,
        )
        db_session.add(source)
        await db_session.flush()

        log = SourceCheckLog(
            source_id=sid,
            check_type=CheckType.SCRAPE.value,
            status=CheckStatus.FAILURE.value,
            http_status=500,
            error_message="Internal server error",
            checked_at=now,
        )
        db_session.add(log)
        await db_session.flush()

        assert log.status == "failure"
        assert log.error_message == "Internal server error"
        assert log.http_status == 500
        assert log.jobs_found is None

    async def test_create_check_log_rate_limited(self, db_session: AsyncSession):
        """Create a rate-limited check log entry."""
        now = datetime.now(timezone.utc)
        sid = compute_source_id("lever", "https://api.lever.co/v0/postings/test")

        source = SourceRegistry(
            source_id=sid,
            source_type="lever",
            url="https://api.lever.co/v0/postings/test",
            created_at=now,
        )
        db_session.add(source)
        await db_session.flush()

        log = SourceCheckLog(
            source_id=sid,
            check_type=CheckType.PROBE.value,
            status=CheckStatus.RATE_LIMITED.value,
            http_status=429,
            duration_ms=50,
            error_message="Too many requests",
            checked_at=now,
        )
        db_session.add(log)
        await db_session.flush()

        assert log.status == "rate_limited"
        assert log.http_status == 429

    async def test_check_log_repr(self, db_session: AsyncSession):
        """Verify the __repr__ output."""
        now = datetime.now(timezone.utc)
        log = SourceCheckLog(
            source_id="test_source_id",
            check_type="health",
            status="success",
            checked_at=now,
        )
        repr_str = repr(log)
        assert "test_source_id" in repr_str
        assert "success" in repr_str

    async def test_multiple_check_logs_per_source(self, db_session: AsyncSession):
        """Verify multiple check logs can exist for a single source."""
        from sqlalchemy import select

        now = datetime.now(timezone.utc)
        sid = compute_source_id("greenhouse", "https://example.com/multi")

        source = SourceRegistry(
            source_id=sid,
            source_type="greenhouse",
            url="https://example.com/multi",
            created_at=now,
        )
        db_session.add(source)
        await db_session.flush()

        for i in range(5):
            log = SourceCheckLog(
                source_id=sid,
                check_type=CheckType.SCRAPE.value,
                status=CheckStatus.SUCCESS.value if i % 2 == 0 else CheckStatus.FAILURE.value,
                jobs_found=10 * i if i % 2 == 0 else None,
                checked_at=now,
            )
            db_session.add(log)
        await db_session.flush()

        result = await db_session.execute(
            select(SourceCheckLog).where(SourceCheckLog.source_id == sid)
        )
        logs = result.scalars().all()
        assert len(logs) == 5


class TestBackwardCompatibility:
    """Verify that Phase 7A M3 tables do not break existing models."""

    async def test_existing_job_model_still_works(self, db_session: AsyncSession):
        """Verify the Job model can still be created alongside M3 tables."""
        from backend.models import Job
        from sqlalchemy import select

        job = Job(
            job_id="test_job_123",
            source="greenhouse",
            url="https://boards.greenhouse.io/test/jobs/123",
            company_name="Test Corp",
            title="Software Engineer",
        )
        db_session.add(job)
        await db_session.flush()

        result = await db_session.execute(
            select(Job).where(Job.job_id == "test_job_123")
        )
        loaded = result.scalar_one()
        assert loaded.title == "Software Engineer"
        assert loaded.company_name == "Test Corp"

    async def test_existing_saved_search_model_still_works(self, db_session: AsyncSession):
        """Verify SavedSearch model works alongside M3 tables."""
        from backend.models import SavedSearch

        search = SavedSearch(
            name="AI Engineer Remote",
            query_params={"q": "AI Engineer", "location": "Remote"},
        )
        db_session.add(search)
        await db_session.flush()
        assert search.id is not None

    async def test_existing_scraper_run_model_still_works(self, db_session: AsyncSession):
        """Verify ScraperRun model works alongside M3 tables."""
        from backend.models import ScraperRun

        run = ScraperRun(
            source="greenhouse",
            status="completed",
            jobs_found=50,
            jobs_new=10,
        )
        db_session.add(run)
        await db_session.flush()
        assert run.id is not None

    async def test_existing_user_profile_model_still_works(self, db_session: AsyncSession):
        """Verify UserProfile model works alongside M3 tables."""
        from backend.models import UserProfile

        profile = UserProfile(
            id=1,
            resume_filename="resume.pdf",
        )
        db_session.add(profile)
        await db_session.flush()
        assert profile.id == 1
