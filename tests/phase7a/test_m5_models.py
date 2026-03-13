"""
Tests for Module 5 — Application Tracker: ORM models.

Covers:
  - Application model creation with defaults
  - Application model creation with all fields
  - ApplicationStatusHistory model creation
  - Required field validation
  - Backward compatibility: Job, SavedSearch, ScraperRun, UserProfile still work
"""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.database import Base
from backend.models import Job, SavedSearch, ScraperRun, UserProfile
from backend.phase7a.m5_models import Application, ApplicationStatusHistory
from backend.phase7a.id_utils import generate_application_id


pytestmark = pytest.mark.asyncio


# ------------------------------------------------------------------
# Local fixtures for ORM model tests
# ------------------------------------------------------------------


@pytest_asyncio.fixture
async def db_engine():
    """In-memory engine with all tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Create applications and status_history tables
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS applications (
                application_id   TEXT(64) PRIMARY KEY,
                canonical_job_id TEXT(64),
                legacy_job_id    TEXT(64) REFERENCES jobs(job_id),
                status           TEXT(32) NOT NULL DEFAULT 'saved',
                status_changed_at DATETIME,
                notes            TEXT,
                tags             JSON,
                custom_fields    JSON,
                applied_at       DATETIME,
                applied_via      TEXT(64),
                response_at      DATETIME,
                interview_at     DATETIME,
                offer_at         DATETIME,
                rejected_at      DATETIME,
                follow_up_at     DATETIME,
                reminder_at      DATETIME,
                reminder_note    TEXT,
                is_archived      BOOLEAN NOT NULL DEFAULT 0,
                created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at       DATETIME
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS application_status_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id  TEXT(64) NOT NULL
                                REFERENCES applications(application_id) ON DELETE CASCADE,
                old_status      TEXT(32),
                new_status      TEXT(32) NOT NULL,
                changed_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                change_source   TEXT(16),
                note            TEXT
            )
        """))
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Async session bound to the test engine."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


async def seed_job(session: AsyncSession, job_id: str, **overrides) -> Job:
    """Insert a minimal Job record for FK constraints."""
    now = datetime.now(timezone.utc)
    job = Job(
        job_id=job_id,
        source=overrides.get("source", "test"),
        url=overrides.get("url", f"https://example.com/jobs/{job_id}"),
        company_name=overrides.get("company_name", "Test Corp"),
        title=overrides.get("title", "Test Role"),
        status=overrides.get("status", "new"),
        scraped_at=now,
        last_updated=now,
        is_active=True,
        is_enriched=False,
        is_starred=False,
    )
    session.add(job)
    await session.flush()
    return job


# ------------------------------------------------------------------
# Application model tests
# ------------------------------------------------------------------


class TestApplicationModel:
    """Tests for the Application ORM model."""

    async def test_create_application_minimal(self, db_session: AsyncSession):
        """Create an application with only required fields."""
        app_id = generate_application_id()
        now = datetime.now(timezone.utc)

        await seed_job(db_session, job_id="job_minimal")

        app = Application(
            application_id=app_id,
            legacy_job_id="job_minimal",
            status="saved",
            created_at=now,
        )
        db_session.add(app)
        await db_session.flush()

        result = await db_session.execute(
            select(Application).where(Application.application_id == app_id)
        )
        fetched = result.scalar_one()

        assert fetched.application_id == app_id
        assert fetched.legacy_job_id == "job_minimal"
        assert fetched.canonical_job_id is None
        assert fetched.status == "saved"
        assert fetched.is_archived is False
        assert fetched.notes is None
        assert fetched.tags is None
        assert fetched.custom_fields is None

    async def test_create_application_all_fields(self, db_session: AsyncSession):
        """Create an application with all fields populated."""
        app_id = generate_application_id()
        now = datetime.now(timezone.utc)

        await seed_job(db_session, job_id="job_full")

        app = Application(
            application_id=app_id,
            canonical_job_id="canon_xyz789",
            legacy_job_id="job_full",
            status="interviewing",
            status_changed_at=now,
            notes="Great conversation with the hiring manager.",
            tags=["dream-job", "referral"],
            custom_fields={"referrer": "John Smith", "salary_expectation": 220000},
            applied_at=now,
            applied_via="referral",
            response_at=now,
            interview_at=now,
            offer_at=None,
            rejected_at=None,
            follow_up_at=now,
            reminder_at=now,
            reminder_note="Follow up on interview feedback",
            is_archived=False,
            created_at=now,
            updated_at=now,
        )
        db_session.add(app)
        await db_session.flush()

        result = await db_session.execute(
            select(Application).where(Application.application_id == app_id)
        )
        fetched = result.scalar_one()

        assert fetched.canonical_job_id == "canon_xyz789"
        assert fetched.status == "interviewing"
        assert fetched.notes == "Great conversation with the hiring manager."
        assert fetched.tags == ["dream-job", "referral"]
        assert fetched.custom_fields["referrer"] == "John Smith"
        assert fetched.applied_via == "referral"
        assert fetched.reminder_note == "Follow up on interview feedback"

    async def test_application_with_canonical_only(self, db_session: AsyncSession):
        """Create an application linked only to canonical_job_id (no legacy)."""
        app_id = generate_application_id()
        now = datetime.now(timezone.utc)

        app = Application(
            application_id=app_id,
            canonical_job_id="canon_only_123",
            legacy_job_id=None,
            status="saved",
            created_at=now,
        )
        db_session.add(app)
        await db_session.flush()

        result = await db_session.execute(
            select(Application).where(Application.application_id == app_id)
        )
        fetched = result.scalar_one()
        assert fetched.canonical_job_id == "canon_only_123"
        assert fetched.legacy_job_id is None

    async def test_application_id_length(self, db_session: AsyncSession):
        """generate_application_id returns a 32-char hex string."""
        app_id = generate_application_id()
        assert len(app_id) == 32
        assert all(c in "0123456789abcdef" for c in app_id)

    async def test_application_repr(self, db_session: AsyncSession):
        """Application __repr__ is readable."""
        app = Application(
            application_id="abc123",
            legacy_job_id="job_001",
            status="saved",
            created_at=datetime.now(timezone.utc),
        )
        r = repr(app)
        assert "abc123" in r
        assert "saved" in r
        assert "job_001" in r

    async def test_is_archived_defaults_to_false(self, db_session: AsyncSession):
        """is_archived should default to False."""
        await seed_job(db_session, job_id="job_archive_test")
        app = Application(
            application_id=generate_application_id(),
            legacy_job_id="job_archive_test",
            status="saved",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(app)
        await db_session.flush()
        assert app.is_archived is False


# ------------------------------------------------------------------
# ApplicationStatusHistory model tests
# ------------------------------------------------------------------


class TestApplicationStatusHistoryModel:
    """Tests for the ApplicationStatusHistory ORM model."""

    async def test_create_history_record(self, db_session: AsyncSession):
        """Create a status history record."""
        await seed_job(db_session, job_id="job_history")
        app_id = generate_application_id()
        now = datetime.now(timezone.utc)

        app = Application(
            application_id=app_id,
            legacy_job_id="job_history",
            status="saved",
            created_at=now,
        )
        db_session.add(app)
        await db_session.flush()

        history = ApplicationStatusHistory(
            application_id=app_id,
            old_status=None,
            new_status="saved",
            changed_at=now,
            change_source="user",
            note="Initial creation",
        )
        db_session.add(history)
        await db_session.flush()

        result = await db_session.execute(
            select(ApplicationStatusHistory).where(
                ApplicationStatusHistory.application_id == app_id
            )
        )
        fetched = result.scalar_one()

        assert fetched.old_status is None
        assert fetched.new_status == "saved"
        assert fetched.change_source == "user"
        assert fetched.note == "Initial creation"

    async def test_history_auto_increment_id(self, db_session: AsyncSession):
        """History records have auto-incrementing IDs."""
        await seed_job(db_session, job_id="job_history_inc")
        app_id = generate_application_id()
        now = datetime.now(timezone.utc)

        app = Application(
            application_id=app_id,
            legacy_job_id="job_history_inc",
            status="saved",
            created_at=now,
        )
        db_session.add(app)
        await db_session.flush()

        h1 = ApplicationStatusHistory(
            application_id=app_id,
            old_status=None,
            new_status="saved",
            changed_at=now,
            change_source="user",
        )
        h2 = ApplicationStatusHistory(
            application_id=app_id,
            old_status="saved",
            new_status="applied",
            changed_at=now,
            change_source="user",
        )
        db_session.add_all([h1, h2])
        await db_session.flush()

        assert h1.id is not None
        assert h2.id is not None
        assert h2.id > h1.id

    async def test_history_repr(self, db_session: AsyncSession):
        """StatusHistory __repr__ is readable."""
        h = ApplicationStatusHistory(
            application_id="app_test",
            old_status="saved",
            new_status="applied",
            changed_at=datetime.now(timezone.utc),
        )
        r = repr(h)
        assert "app_test" in r
        assert "saved" in r
        assert "applied" in r


# ------------------------------------------------------------------
# Backward compatibility tests
# ------------------------------------------------------------------


class TestBackwardCompatibility:
    """Ensure existing models still work with the new tables present."""

    async def test_job_model_still_works(self, db_session: AsyncSession):
        """Existing Job model can still be created and queried."""
        await seed_job(db_session, job_id="compat_job_001")

        result = await db_session.execute(
            select(Job).where(Job.job_id == "compat_job_001")
        )
        fetched = result.scalar_one()
        assert fetched.company_name == "Test Corp"
        assert fetched.status == "new"

    async def test_job_status_field_still_exists(self, db_session: AsyncSession):
        """jobs.status field still exists and is writable."""
        await seed_job(db_session, job_id="compat_job_002", status="applied")

        result = await db_session.execute(
            select(Job).where(Job.job_id == "compat_job_002")
        )
        fetched = result.scalar_one()
        assert fetched.status == "applied"

        # Update it
        fetched.status = "interviewing"
        await db_session.flush()

        result2 = await db_session.execute(
            select(Job).where(Job.job_id == "compat_job_002")
        )
        assert result2.scalar_one().status == "interviewing"

    async def test_saved_search_model_still_works(self, db_session: AsyncSession):
        """SavedSearch model still works."""
        ss = SavedSearch(
            name="test search",
            query_params={"q": "AI Engineer"},
            alert_enabled=False,
        )
        db_session.add(ss)
        await db_session.flush()
        assert ss.id is not None

    async def test_scraper_run_model_still_works(self, db_session: AsyncSession):
        """ScraperRun model still works."""
        sr = ScraperRun(
            source="test",
            status="completed",
            jobs_found=10,
            jobs_new=5,
            jobs_updated=3,
        )
        db_session.add(sr)
        await db_session.flush()
        assert sr.id is not None

    async def test_user_profile_model_still_works(self, db_session: AsyncSession):
        """UserProfile model still works."""
        up = UserProfile(id=1)
        db_session.add(up)
        await db_session.flush()

        result = await db_session.execute(
            select(UserProfile).where(UserProfile.id == 1)
        )
        assert result.scalar_one().id == 1

    async def test_tables_coexist(self, db_session: AsyncSession):
        """All tables can be queried simultaneously without error."""
        await db_session.execute(select(Job).limit(0))
        await db_session.execute(select(SavedSearch).limit(0))
        await db_session.execute(select(ScraperRun).limit(0))
        await db_session.execute(select(UserProfile).limit(0))
        await db_session.execute(select(Application).limit(0))
        await db_session.execute(select(ApplicationStatusHistory).limit(0))
