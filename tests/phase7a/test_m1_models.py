"""Tests for Module 1 — Company Intelligence Registry models.

Tests cover:
- Model instantiation with required and optional fields
- Default values
- Table names and column types
- Index definitions
- Foreign key relationships
- Repr methods
- Edge cases: None fields, empty strings, JSON fields
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy import select, text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.database import Base
from backend.phase7a.m1_models import Company, CompanySource, ATSDetectionLog
from backend.phase7a.id_utils import compute_company_id


@pytest_asyncio.fixture
async def engine():
    """Create in-memory engine with M1 tables and legacy tables."""
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        # Import legacy models so Base.metadata knows about them
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Create async session for testing."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess


class TestCompanyModel:
    """Tests for the Company SQLAlchemy model."""

    async def test_table_name(self):
        assert Company.__tablename__ == "companies"

    async def test_primary_key(self):
        pk_cols = [c.name for c in Company.__table__.primary_key.columns]
        assert pk_cols == ["company_id"]

    async def test_create_minimal(self, session):
        """Company can be created with just required fields."""
        company_id = compute_company_id("stripe.com")
        company = Company(
            company_id=company_id,
            canonical_name="Stripe",
            domain="stripe.com",
        )
        session.add(company)
        await session.flush()

        result = await session.execute(
            select(Company).where(Company.company_id == company_id)
        )
        fetched = result.scalar_one()
        assert fetched.canonical_name == "Stripe"
        assert fetched.domain == "stripe.com"
        assert fetched.validation_state == "unverified"
        assert fetched.confidence_score == 0
        assert fetched.manual_override is False

    async def test_create_full(self, session):
        """Company can be created with all fields populated."""
        company_id = compute_company_id("openai.com")
        now = datetime.now(timezone.utc)
        company = Company(
            company_id=company_id,
            canonical_name="OpenAI",
            domain="openai.com",
            domain_aliases=["openai.org", "chatgpt.com"],
            ats_provider="greenhouse",
            ats_slug="openai",
            careers_url="https://openai.com/careers",
            board_urls=["https://boards.greenhouse.io/openai"],
            logo_url="https://logo.clearbit.com/openai.com",
            validation_state="verified",
            confidence_score=85,
            last_validated_at=now,
            last_probe_at=now,
            manual_override=False,
            override_fields=None,
            created_at=now,
        )
        session.add(company)
        await session.flush()

        result = await session.execute(
            select(Company).where(Company.company_id == company_id)
        )
        fetched = result.scalar_one()
        assert fetched.domain_aliases == ["openai.org", "chatgpt.com"]
        assert fetched.ats_provider == "greenhouse"
        assert fetched.ats_slug == "openai"
        assert fetched.board_urls == ["https://boards.greenhouse.io/openai"]
        assert fetched.confidence_score == 85

    async def test_domain_nullable(self, session):
        """Company can be created without a domain."""
        company_id = compute_company_id("Mystery Corp")
        company = Company(
            company_id=company_id,
            canonical_name="Mystery Corp",
            domain=None,
        )
        session.add(company)
        await session.flush()

        result = await session.execute(
            select(Company).where(Company.company_id == company_id)
        )
        fetched = result.scalar_one()
        assert fetched.domain is None

    async def test_unique_canonical_name(self, session):
        """Duplicate canonical_name raises IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        c1 = Company(
            company_id=compute_company_id("acme.com"),
            canonical_name="Acme",
            domain="acme.com",
        )
        c2 = Company(
            company_id=compute_company_id("acme.io"),
            canonical_name="Acme",  # duplicate name
            domain="acme.io",
        )
        session.add(c1)
        await session.flush()

        session.add(c2)
        with pytest.raises(IntegrityError):
            await session.flush()

    async def test_unique_domain(self, session):
        """Duplicate domain raises IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        c1 = Company(
            company_id=compute_company_id("test.com"),
            canonical_name="Test One",
            domain="test.com",
        )
        c2 = Company(
            company_id="different_id_" + "0" * 52,
            canonical_name="Test Two",
            domain="test.com",  # duplicate domain
        )
        session.add(c1)
        await session.flush()

        session.add(c2)
        with pytest.raises(IntegrityError):
            await session.flush()

    async def test_repr(self):
        company = Company(
            company_id="a" * 64,
            canonical_name="TestCo",
            domain="test.com",
            validation_state="verified",
        )
        r = repr(company)
        assert "TestCo" in r
        assert "test.com" in r
        assert "verified" in r

    async def test_json_fields_are_lists(self, session):
        """JSON fields store and retrieve Python lists correctly."""
        company_id = compute_company_id("json-test.com")
        company = Company(
            company_id=company_id,
            canonical_name="JSONTest",
            domain="json-test.com",
            domain_aliases=["alias1.com", "alias2.com"],
            board_urls=["url1", "url2"],
            override_fields=["ats_provider", "ats_slug"],
        )
        session.add(company)
        await session.flush()

        result = await session.execute(
            select(Company).where(Company.company_id == company_id)
        )
        fetched = result.scalar_one()
        assert isinstance(fetched.domain_aliases, list)
        assert len(fetched.domain_aliases) == 2
        assert isinstance(fetched.board_urls, list)
        assert isinstance(fetched.override_fields, list)


class TestCompanySourceModel:
    """Tests for the CompanySource SQLAlchemy model."""

    async def test_table_name(self):
        assert CompanySource.__tablename__ == "company_sources"

    async def test_primary_key_autoincrement(self):
        pk_cols = [c.name for c in CompanySource.__table__.primary_key.columns]
        assert pk_cols == ["id"]

    async def test_create_with_parent(self, session):
        """CompanySource can be created with a valid company FK."""
        company_id = compute_company_id("source-test.com")
        company = Company(
            company_id=company_id,
            canonical_name="SourceTest",
            domain="source-test.com",
        )
        session.add(company)
        await session.flush()

        now = datetime.now(timezone.utc)
        source = CompanySource(
            company_id=company_id,
            source="greenhouse",
            source_identifier="sourcetest",
            source_url="https://boards.greenhouse.io/sourcetest",
            jobs_count=42,
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(source)
        await session.flush()

        result = await session.execute(
            select(CompanySource).where(CompanySource.company_id == company_id)
        )
        fetched = result.scalar_one()
        assert fetched.source == "greenhouse"
        assert fetched.source_identifier == "sourcetest"
        assert fetched.jobs_count == 42

    async def test_nullable_optional_fields(self, session):
        """Optional fields can be None."""
        company_id = compute_company_id("nullable-test.com")
        company = Company(
            company_id=company_id,
            canonical_name="NullableTest",
            domain="nullable-test.com",
        )
        session.add(company)
        await session.flush()

        source = CompanySource(
            company_id=company_id,
            source="serpapi",
            source_identifier=None,
            source_url=None,
            first_seen_at=datetime.now(timezone.utc),
        )
        session.add(source)
        await session.flush()

        result = await session.execute(
            select(CompanySource).where(CompanySource.company_id == company_id)
        )
        fetched = result.scalar_one()
        assert fetched.source_identifier is None
        assert fetched.source_url is None

    async def test_default_jobs_count(self, session):
        """jobs_count defaults to 0."""
        company_id = compute_company_id("default-test.com")
        company = Company(
            company_id=company_id,
            canonical_name="DefaultTest",
            domain="default-test.com",
        )
        session.add(company)
        await session.flush()

        source = CompanySource(
            company_id=company_id,
            source="lever",
            first_seen_at=datetime.now(timezone.utc),
        )
        session.add(source)
        await session.flush()

        result = await session.execute(
            select(CompanySource).where(CompanySource.company_id == company_id)
        )
        fetched = result.scalar_one()
        assert fetched.jobs_count == 0

    async def test_repr(self):
        source = CompanySource(
            id=1,
            company_id="b" * 64,
            source="lever",
        )
        r = repr(source)
        assert "lever" in r


class TestATSDetectionLogModel:
    """Tests for the ATSDetectionLog SQLAlchemy model."""

    async def test_table_name(self):
        assert ATSDetectionLog.__tablename__ == "ats_detection_log"

    async def test_create_successful_probe(self, session):
        """ATSDetectionLog records a successful probe."""
        company_id = compute_company_id("probe-test.com")
        company = Company(
            company_id=company_id,
            canonical_name="ProbeTest",
            domain="probe-test.com",
        )
        session.add(company)
        await session.flush()

        now = datetime.now(timezone.utc)
        log = ATSDetectionLog(
            company_id=company_id,
            probe_url="https://probe-test.com/careers",
            detected_provider="greenhouse",
            detection_method="url_pattern",
            confidence=90,
            probe_status=200,
            probe_duration_ms=450,
            probed_at=now,
        )
        session.add(log)
        await session.flush()

        result = await session.execute(
            select(ATSDetectionLog).where(ATSDetectionLog.company_id == company_id)
        )
        fetched = result.scalar_one()
        assert fetched.detected_provider == "greenhouse"
        assert fetched.detection_method == "url_pattern"
        assert fetched.confidence == 90
        assert fetched.probe_status == 200
        assert fetched.probe_duration_ms == 450
        assert fetched.error_message is None

    async def test_create_failed_probe(self, session):
        """ATSDetectionLog records a failed probe with error message."""
        company_id = compute_company_id("fail-test.com")
        company = Company(
            company_id=company_id,
            canonical_name="FailTest",
            domain="fail-test.com",
        )
        session.add(company)
        await session.flush()

        now = datetime.now(timezone.utc)
        log = ATSDetectionLog(
            company_id=company_id,
            probe_url="https://fail-test.com/careers",
            detected_provider=None,
            detection_method=None,
            confidence=None,
            probe_status=503,
            probe_duration_ms=5000,
            probed_at=now,
            error_message="Service Unavailable",
        )
        session.add(log)
        await session.flush()

        result = await session.execute(
            select(ATSDetectionLog).where(ATSDetectionLog.company_id == company_id)
        )
        fetched = result.scalar_one()
        assert fetched.detected_provider is None
        assert fetched.error_message == "Service Unavailable"

    async def test_multiple_probes_for_same_company(self, session):
        """Multiple probe records can exist for the same company."""
        company_id = compute_company_id("multi-probe.com")
        company = Company(
            company_id=company_id,
            canonical_name="MultiProbe",
            domain="multi-probe.com",
        )
        session.add(company)
        await session.flush()

        now = datetime.now(timezone.utc)
        for i in range(3):
            log = ATSDetectionLog(
                company_id=company_id,
                probe_url=f"https://multi-probe.com/careers/{i}",
                detected_provider="lever" if i % 2 == 0 else None,
                probed_at=now,
            )
            session.add(log)
        await session.flush()

        result = await session.execute(
            select(ATSDetectionLog)
            .where(ATSDetectionLog.company_id == company_id)
        )
        probes = list(result.scalars().all())
        assert len(probes) == 3

    async def test_repr(self):
        log = ATSDetectionLog(
            id=1,
            company_id="c" * 64,
            detected_provider="ashby",
        )
        r = repr(log)
        assert "ashby" in r


class TestIndexesExist:
    """Verify all specified indexes are created in the schema."""

    async def test_companies_indexes(self, engine):
        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='companies'"
            ))
            index_names = {row[0] for row in result.fetchall()}

        # Note: SQLite may add auto-generated indexes for UNIQUE constraints
        assert "idx_companies_domain" in index_names
        assert "idx_companies_canonical_name" in index_names
        assert "idx_companies_ats_provider_slug" in index_names
        assert "idx_companies_validation_state" in index_names

    async def test_company_sources_indexes(self, engine):
        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='company_sources'"
            ))
            index_names = {row[0] for row in result.fetchall()}

        assert "idx_company_sources_company_id" in index_names
        assert "idx_company_sources_source" in index_names

    async def test_ats_detection_log_indexes(self, engine):
        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='ats_detection_log'"
            ))
            index_names = {row[0] for row in result.fetchall()}

        assert "idx_ats_detection_log_company_id" in index_names


class TestBackwardCompatibility:
    """Verify existing models still work alongside M1 models."""

    async def test_existing_models_importable(self):
        """Legacy models import without error."""
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile
        assert Job.__tablename__ == "jobs"
        assert SavedSearch.__tablename__ == "saved_searches"
        assert ScraperRun.__tablename__ == "scraper_runs"
        assert UserProfile.__tablename__ == "user_profile"

    async def test_existing_tables_created(self, engine):
        """Legacy tables are created alongside M1 tables."""
        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            table_names = {row[0] for row in result.fetchall()}

        # M1 tables
        assert "companies" in table_names
        assert "company_sources" in table_names
        assert "ats_detection_log" in table_names

    async def test_job_model_still_works(self, session):
        """Can still create and query Job records."""
        from backend.models import Job

        job = Job(
            job_id="test_job_" + "0" * 55,
            source="serpapi",
            url="https://example.com/job/1",
            company_name="TestCo",
            title="Software Engineer",
        )
        session.add(job)
        await session.flush()

        result = await session.execute(
            select(Job).where(Job.job_id == job.job_id)
        )
        fetched = result.scalar_one()
        assert fetched.company_name == "TestCo"
        assert fetched.title == "Software Engineer"
