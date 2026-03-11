"""Shared test fixtures for Phase 7A tests.

Provides:
- In-memory async SQLite engine and session for isolated testing (Agent A)
- seeded_db: initialized DB with golden dataset loaded
- company_factory: Factory function to create test Company records
- job_factory: Factory function to create test Job records
- application_factory: Factory function to create test Application records
"""

import hashlib
from datetime import datetime, timezone
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


# ---------------------------------------------------------------------------
# Core fixtures (Agent A originals — DO NOT MODIFY)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def async_engine():
    """Create an in-memory async SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create an async session factory bound to the test engine."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def initialized_db(async_engine):
    """Create all tables (existing + migration table + FTS5) in the test database.

    This simulates what init_db() does, but against the test engine.
    Includes FTS5 virtual table and triggers for full backward compatibility testing.
    """
    from backend.database import Base
    from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Create FTS5 virtual table (mirrors init_db)
        await conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts USING fts5(
                job_id UNINDEXED,
                title,
                company_name,
                description_clean,
                skills_required,
                tech_stack,
                content='jobs',
                content_rowid='rowid'
            )
        """))

        # FTS triggers (mirrors init_db)
        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS jobs_fts_insert AFTER INSERT ON jobs BEGIN
                INSERT INTO jobs_fts(job_id, title, company_name, description_clean, skills_required, tech_stack)
                VALUES (new.job_id, new.title, new.company_name, new.description_clean,
                        new.skills_required, new.tech_stack);
            END
        """))

        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS jobs_fts_update AFTER UPDATE ON jobs BEGIN
                DELETE FROM jobs_fts WHERE job_id = old.job_id;
                INSERT INTO jobs_fts(job_id, title, company_name, description_clean, skills_required, tech_stack)
                VALUES (new.job_id, new.title, new.company_name, new.description_clean,
                        new.skills_required, new.tech_stack);
            END
        """))

        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS jobs_fts_delete AFTER DELETE ON jobs BEGIN
                DELETE FROM jobs_fts WHERE job_id = old.job_id;
            END
        """))

        # Run Phase 7A migrations
        from backend.phase7a.migration import run_migrations
        await run_migrations(conn)

    yield async_engine


# ---------------------------------------------------------------------------
# Extended fixtures (Agent F — integration test harness)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def seeded_db(initialized_db):
    """Initialized DB with golden dataset loaded into the jobs table.

    Inserts all 50 golden dataset jobs into the database.
    Depends on initialized_db so all tables and migrations exist first.

    Yields the engine for further queries.
    """
    from tests.golden_dataset import get_test_jobs

    session_factory = async_sessionmaker(
        initialized_db, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        jobs_data = get_test_jobs()
        for job_dict in jobs_data:
            # Build column list and values for raw INSERT
            # (using raw SQL avoids needing the ORM model to have all fields nullable)
            columns = list(job_dict.keys())
            placeholders = [f":{col}" for col in columns]
            sql = f"INSERT INTO jobs ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

            # Convert lists/dicts to JSON strings for SQLite
            params = {}
            for k, v in job_dict.items():
                if isinstance(v, (list, dict)):
                    import json
                    params[k] = json.dumps(v)
                elif isinstance(v, datetime):
                    params[k] = v.isoformat()
                elif isinstance(v, bool):
                    params[k] = 1 if v else 0
                else:
                    params[k] = v
            await session.execute(text(sql), params)

        await session.commit()

    yield initialized_db


@pytest.fixture
def company_factory():
    """Factory function to create test Company record dicts.

    Returns a callable that produces company dicts with sensible defaults.
    All fields can be overridden via keyword arguments.

    Usage:
        company = company_factory(domain="example.com", canonical_name="Example")
    """
    from backend.phase7a.id_utils import compute_company_id
    from backend.phase7a.constants import ATSProvider, ValidationState

    _counter = [0]

    def _make_company(**overrides: Any) -> dict:
        _counter[0] += 1
        idx = _counter[0]
        domain = overrides.pop("domain", f"company{idx}.com")
        name = overrides.pop("canonical_name", f"Company {idx}")

        defaults = {
            "company_id": compute_company_id(domain) if domain else compute_company_id(name),
            "canonical_name": name,
            "domain": domain,
            "domain_aliases": None,
            "ats_provider": ATSProvider.GREENHOUSE.value,
            "ats_slug": f"company{idx}",
            "careers_url": f"https://{domain}/careers" if domain else None,
            "board_urls": None,
            "logo_url": None,
            "validation_state": ValidationState.UNVERIFIED.value,
            "confidence_score": 0,
            "last_validated_at": None,
            "last_probe_at": None,
            "probe_error": None,
            "manual_override": False,
            "override_fields": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        defaults.update(overrides)
        return defaults

    return _make_company


@pytest.fixture
def job_factory():
    """Factory function to create test Job record dicts compatible with the jobs table.

    Returns a callable that produces job dicts with sensible defaults.
    All fields can be overridden via keyword arguments.

    Usage:
        job = job_factory(title="ML Engineer", company_name="Stripe")
    """
    _counter = [0]

    def _make_job(**overrides: Any) -> dict:
        _counter[0] += 1
        idx = _counter[0]

        source = overrides.pop("source", "greenhouse")
        company = overrides.pop("company_name", f"TestCompany{idx}")
        title = overrides.pop("title", f"Test Role {idx}")

        # Compute job_id the same way BaseScraper does
        key = f"{source}:{company.lower().strip()}:{title.lower().strip()}"
        job_id = hashlib.sha256(key.encode()).hexdigest()[:64]

        defaults = {
            "job_id": job_id,
            "source": source,
            "url": f"https://example.com/jobs/{idx}",
            "posted_at": datetime.now(timezone.utc),
            "scraped_at": datetime.now(timezone.utc),
            "is_active": True,
            "duplicate_of": None,
            "company_name": company,
            "company_domain": None,
            "company_logo_url": None,
            "title": title,
            "location_city": "San Francisco",
            "location_state": "CA",
            "location_country": "US",
            "remote_type": "hybrid",
            "job_type": "full-time",
            "experience_level": "mid",
            "department": None,
            "industry": "Technology",
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "USD",
            "salary_period": None,
            "description_raw": f"<p>Job description for {title} at {company}.</p>",
            "description_clean": f"Job description for {title} at {company}.",
            "description_markdown": f"Job description for **{title}** at **{company}**.",
            "skills_required": None,
            "skills_nice_to_have": None,
            "tech_stack": None,
            "seniority_score": None,
            "remote_score": None,
            "match_score": None,
            "summary_ai": None,
            "red_flags": None,
            "green_flags": None,
            "is_enriched": False,
            "enriched_at": None,
            "status": "new",
            "notes": None,
            "applied_at": None,
            "last_updated": datetime.now(timezone.utc),
            "is_starred": False,
            "tags": None,
        }
        defaults.update(overrides)
        # Re-assign job_id if caller overrode source/company/title but not job_id
        if "job_id" not in overrides:
            key = f"{defaults['source']}:{defaults['company_name'].lower().strip()}:{defaults['title'].lower().strip()}"
            defaults["job_id"] = hashlib.sha256(key.encode()).hexdigest()[:64]
        return defaults

    return _make_job


@pytest.fixture
def application_factory():
    """Factory function to create test Application record dicts.

    Returns a callable that produces application dicts with sensible defaults.
    Designed for the future applications table (M5).

    Usage:
        app = application_factory(job_id="abc123", status="applied")
    """
    from backend.phase7a.id_utils import generate_application_id
    from backend.phase7a.constants import ApplicationStatus

    _counter = [0]

    def _make_application(**overrides: Any) -> dict:
        _counter[0] += 1

        defaults = {
            "application_id": generate_application_id(),
            "job_id": overrides.pop("job_id", f"placeholder_job_{_counter[0]}"),
            "canonical_job_id": None,
            "status": ApplicationStatus.SAVED.value,
            "applied_at": None,
            "status_updated_at": datetime.now(timezone.utc),
            "notes": None,
            "resume_version": "v1.0",
            "cover_letter_used": False,
            "source_url": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        defaults.update(overrides)
        return defaults

    return _make_application
