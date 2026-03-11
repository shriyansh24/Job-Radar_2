"""Tests for Module 4 Canonical Jobs Pipeline: SQLAlchemy models.

Verifies that both M4 tables (raw_job_sources, canonical_jobs) can be
created and used via the ORM, with proper defaults, nullable fields,
and backward compatibility with existing tables.
"""

import json
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.database import Base
from backend.phase7a.m4_models import CanonicalJob, RawJobSource
from backend.phase7a.id_utils import compute_canonical_job_id, compute_raw_job_id


@pytest_asyncio.fixture
async def m4_engine():
    """In-memory SQLite engine with M4 tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def m4_session(m4_engine):
    """Async session bound to the M4 test engine."""
    factory = async_sessionmaker(
        m4_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as session:
        yield session


class TestRawJobSourceModel:
    """Tests for the RawJobSource ORM model."""

    @pytest.mark.asyncio
    async def test_table_exists(self, m4_engine):
        async with m4_engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='raw_job_sources'"
                )
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_insert_and_read(self, m4_session):
        now = datetime.now(timezone.utc)
        raw_id = compute_raw_job_id("greenhouse", "job-123")

        record = RawJobSource(
            raw_id=raw_id,
            source="greenhouse",
            source_job_id="job-123",
            source_url="https://boards.greenhouse.io/acme/jobs/123",
            title_raw="Software Engineer",
            company_name_raw="Acme Corp",
            location_raw="San Francisco, CA",
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
            scrape_count=1,
        )
        m4_session.add(record)
        await m4_session.commit()

        result = await m4_session.execute(
            text("SELECT * FROM raw_job_sources WHERE raw_id = :rid"),
            {"rid": raw_id},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == raw_id  # raw_id

    @pytest.mark.asyncio
    async def test_primary_key_unique(self, m4_session):
        now = datetime.now(timezone.utc)
        raw_id = compute_raw_job_id("lever", "lev-456")

        r1 = RawJobSource(
            raw_id=raw_id,
            source="lever",
            source_job_id="lev-456",
            first_seen_at=now,
            last_seen_at=now,
        )
        m4_session.add(r1)
        await m4_session.commit()

        r2 = RawJobSource(
            raw_id=raw_id,
            source="lever",
            source_job_id="lev-456",
            first_seen_at=now,
            last_seen_at=now,
        )
        m4_session.add(r2)
        with pytest.raises(Exception):
            await m4_session.commit()

    @pytest.mark.asyncio
    async def test_default_values(self, m4_session):
        now = datetime.now(timezone.utc)
        raw_id = compute_raw_job_id("ashby", "ash-789")

        record = RawJobSource(
            raw_id=raw_id,
            source="ashby",
            source_job_id="ash-789",
            first_seen_at=now,
            last_seen_at=now,
        )
        m4_session.add(record)
        await m4_session.commit()

        result = await m4_session.execute(
            text(
                "SELECT is_active, scrape_count FROM raw_job_sources "
                "WHERE raw_id = :rid"
            ),
            {"rid": raw_id},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1  # is_active = True
        assert row[1] == 1  # scrape_count = 1

    @pytest.mark.asyncio
    async def test_nullable_fields(self, m4_session):
        now = datetime.now(timezone.utc)
        raw_id = compute_raw_job_id("serpapi", "serp-001")

        record = RawJobSource(
            raw_id=raw_id,
            source="serpapi",
            source_job_id="serp-001",
            first_seen_at=now,
            last_seen_at=now,
            # All optional fields left as None
            canonical_job_id=None,
            source_url=None,
            source_id=None,
            raw_payload=None,
            title_raw=None,
            company_name_raw=None,
            location_raw=None,
            salary_raw=None,
            description_raw=None,
        )
        m4_session.add(record)
        await m4_session.commit()

        result = await m4_session.execute(
            text(
                "SELECT canonical_job_id, source_url, source_id, "
                "title_raw, company_name_raw, location_raw, salary_raw, "
                "description_raw FROM raw_job_sources WHERE raw_id = :rid"
            ),
            {"rid": raw_id},
        )
        row = result.fetchone()
        assert row is not None
        assert all(v is None for v in row)

    @pytest.mark.asyncio
    async def test_json_payload(self, m4_session):
        now = datetime.now(timezone.utc)
        raw_id = compute_raw_job_id("greenhouse", "gh-json")
        payload = {
            "id": 12345,
            "title": "ML Engineer",
            "departments": [{"name": "Engineering"}],
        }

        record = RawJobSource(
            raw_id=raw_id,
            source="greenhouse",
            source_job_id="gh-json",
            raw_payload=payload,
            first_seen_at=now,
            last_seen_at=now,
        )
        m4_session.add(record)
        await m4_session.commit()

        result = await m4_session.execute(
            text(
                "SELECT raw_payload FROM raw_job_sources "
                "WHERE raw_id = :rid"
            ),
            {"rid": raw_id},
        )
        row = result.fetchone()
        assert row is not None
        stored = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        assert stored["id"] == 12345
        assert stored["title"] == "ML Engineer"

    @pytest.mark.asyncio
    async def test_canonical_job_id_link(self, m4_session):
        """Raw job source can be linked to a canonical job."""
        now = datetime.now(timezone.utc)
        raw_id = compute_raw_job_id("lever", "lev-linked")
        canonical_id = "abc" * 21 + "a"  # 64 chars

        record = RawJobSource(
            raw_id=raw_id,
            source="lever",
            source_job_id="lev-linked",
            canonical_job_id=canonical_id,
            first_seen_at=now,
            last_seen_at=now,
        )
        m4_session.add(record)
        await m4_session.commit()

        result = await m4_session.execute(
            text(
                "SELECT canonical_job_id FROM raw_job_sources "
                "WHERE raw_id = :rid"
            ),
            {"rid": raw_id},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == canonical_id


class TestCanonicalJobModel:
    """Tests for the CanonicalJob ORM model."""

    @pytest.mark.asyncio
    async def test_table_exists(self, m4_engine):
        async with m4_engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='canonical_jobs'"
                )
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_insert_and_read(self, m4_session):
        now = datetime.now(timezone.utc)
        company_id = "c" * 64
        canonical_id = compute_canonical_job_id(
            company_id, "ML Engineer", "San Francisco, CA"
        )

        job = CanonicalJob(
            canonical_job_id=canonical_id,
            company_id=company_id,
            company_name="Acme Corp",
            title="ML Engineer",
            title_normalized="ml engineer",
            location_city="san francisco",
            location_raw="San Francisco, CA",
            remote_type="hybrid",
            job_type="full-time",
            experience_level="mid",
            description_markdown="Great ML role.",
            apply_url="https://acme.com/apply/123",
            source_count=1,
            primary_source="greenhouse",
            quality_score=55,
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
            created_at=now,
        )
        m4_session.add(job)
        await m4_session.commit()

        result = await m4_session.execute(
            text(
                "SELECT * FROM canonical_jobs "
                "WHERE canonical_job_id = :cid"
            ),
            {"cid": canonical_id},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == canonical_id  # canonical_job_id

    @pytest.mark.asyncio
    async def test_primary_key_unique(self, m4_session):
        now = datetime.now(timezone.utc)
        canonical_id = "unique_pk_test_" + "0" * 50

        j1 = CanonicalJob(
            canonical_job_id=canonical_id,
            company_name="Acme",
            title="Engineer",
            first_seen_at=now,
            last_seen_at=now,
            created_at=now,
        )
        m4_session.add(j1)
        await m4_session.commit()

        j2 = CanonicalJob(
            canonical_job_id=canonical_id,
            company_name="Beta",
            title="Dev",
            first_seen_at=now,
            last_seen_at=now,
            created_at=now,
        )
        m4_session.add(j2)
        with pytest.raises(Exception):
            await m4_session.commit()

    @pytest.mark.asyncio
    async def test_default_values(self, m4_session):
        now = datetime.now(timezone.utc)
        canonical_id = "defaults_test_" + "0" * 50

        job = CanonicalJob(
            canonical_job_id=canonical_id,
            company_name="TestCo",
            title="Tester",
            first_seen_at=now,
            last_seen_at=now,
            created_at=now,
        )
        m4_session.add(job)
        await m4_session.commit()

        result = await m4_session.execute(
            text(
                "SELECT is_active, source_count, salary_currency "
                "FROM canonical_jobs WHERE canonical_job_id = :cid"
            ),
            {"cid": canonical_id},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1  # is_active = True
        assert row[1] == 1  # source_count = 1
        assert row[2] == "USD"  # salary_currency

    @pytest.mark.asyncio
    async def test_nullable_fields(self, m4_session):
        now = datetime.now(timezone.utc)
        canonical_id = "nullable_test_" + "0" * 50

        job = CanonicalJob(
            canonical_job_id=canonical_id,
            company_name="NullCo",
            title="NullRole",
            first_seen_at=now,
            last_seen_at=now,
            created_at=now,
            # All optional fields left as None
            company_id=None,
            title_normalized=None,
            location_city=None,
            location_state=None,
            location_country=None,
            location_raw=None,
            remote_type=None,
            job_type=None,
            experience_level=None,
            salary_min=None,
            salary_max=None,
            description_markdown=None,
            apply_url=None,
            primary_source=None,
            quality_score=None,
            closed_at=None,
            updated_at=None,
        )
        m4_session.add(job)
        await m4_session.commit()

        result = await m4_session.execute(
            text(
                "SELECT company_id, title_normalized, location_city, "
                "location_state, location_country, remote_type, "
                "job_type, experience_level, salary_min, salary_max, "
                "description_markdown, apply_url, primary_source, "
                "quality_score, closed_at, updated_at "
                "FROM canonical_jobs WHERE canonical_job_id = :cid"
            ),
            {"cid": canonical_id},
        )
        row = result.fetchone()
        assert row is not None
        assert all(v is None for v in row)

    @pytest.mark.asyncio
    async def test_salary_fields(self, m4_session):
        now = datetime.now(timezone.utc)
        canonical_id = "salary_test_" + "0" * 52

        job = CanonicalJob(
            canonical_job_id=canonical_id,
            company_name="PayCo",
            title="Paid Role",
            salary_min=100000,
            salary_max=180000,
            salary_currency="USD",
            first_seen_at=now,
            last_seen_at=now,
            created_at=now,
        )
        m4_session.add(job)
        await m4_session.commit()

        result = await m4_session.execute(
            text(
                "SELECT salary_min, salary_max, salary_currency "
                "FROM canonical_jobs WHERE canonical_job_id = :cid"
            ),
            {"cid": canonical_id},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == 100000
        assert row[1] == 180000
        assert row[2] == "USD"

    @pytest.mark.asyncio
    async def test_lifecycle_fields(self, m4_session):
        now = datetime.now(timezone.utc)
        canonical_id = "lifecycle_test_" + "0" * 49

        job = CanonicalJob(
            canonical_job_id=canonical_id,
            company_name="LifeCo",
            title="Living Role",
            is_active=False,
            closed_at=now,
            first_seen_at=now,
            last_seen_at=now,
            created_at=now,
        )
        m4_session.add(job)
        await m4_session.commit()

        result = await m4_session.execute(
            text(
                "SELECT is_active, closed_at "
                "FROM canonical_jobs WHERE canonical_job_id = :cid"
            ),
            {"cid": canonical_id},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == 0  # is_active = False
        assert row[1] is not None  # closed_at set


class TestBackwardCompatibility:
    """Verify M4 models coexist with existing tables without interference."""

    @pytest.mark.asyncio
    async def test_existing_tables_unaffected(self, m4_engine):
        """Creating M4 tables should not affect existing Job/SavedSearch/etc tables."""
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa

        async with m4_engine.begin() as conn:
            for table_name in [
                "jobs",
                "saved_searches",
                "scraper_runs",
                "user_profile",
            ]:
                result = await conn.execute(
                    text(
                        f"SELECT name FROM sqlite_master "
                        f"WHERE type='table' AND name='{table_name}'"
                    )
                )
                assert result.fetchone() is not None, (
                    f"Existing table {table_name} should still exist"
                )

    @pytest.mark.asyncio
    async def test_m4_tables_are_new(self, m4_engine):
        """All M4 tables should be created alongside existing ones."""
        async with m4_engine.begin() as conn:
            for table_name in ["raw_job_sources", "canonical_jobs"]:
                result = await conn.execute(
                    text(
                        f"SELECT name FROM sqlite_master "
                        f"WHERE type='table' AND name='{table_name}'"
                    )
                )
                assert result.fetchone() is not None, (
                    f"M4 table {table_name} should exist"
                )

    @pytest.mark.asyncio
    async def test_can_insert_into_both_jobs_and_m4(self, m4_session):
        """Inserting into existing jobs table and M4 tables simultaneously should work."""
        now = datetime.now(timezone.utc)

        # Insert into existing jobs table
        await m4_session.execute(
            text(
                "INSERT INTO jobs (job_id, source, url, company_name, title, status, "
                "scraped_at, last_updated, is_active, is_enriched, is_starred) "
                "VALUES ('legacy1', 'greenhouse', 'https://example.com', "
                "'TestCo', 'Dev', 'new', :now, :now, 1, 0, 0)"
            ),
            {"now": now.isoformat()},
        )

        # Insert into M4 raw_job_sources
        raw_id = compute_raw_job_id("greenhouse", "raw-compat")
        await m4_session.execute(
            text(
                "INSERT INTO raw_job_sources (raw_id, source, source_job_id, "
                "first_seen_at, last_seen_at, is_active, scrape_count) "
                "VALUES (:rid, 'greenhouse', 'raw-compat', :now, :now, 1, 1)"
            ),
            {"rid": raw_id, "now": now.isoformat()},
        )

        await m4_session.commit()

        # Verify both exist
        result = await m4_session.execute(
            text("SELECT job_id FROM jobs WHERE job_id = 'legacy1'")
        )
        assert result.fetchone() is not None

        result = await m4_session.execute(
            text(
                "SELECT raw_id FROM raw_job_sources WHERE raw_id = :rid"
            ),
            {"rid": raw_id},
        )
        assert result.fetchone() is not None
