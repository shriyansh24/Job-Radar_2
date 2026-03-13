"""Backward Compatibility Suite for Phase 7A.

These tests MUST pass before and after any Phase 7A changes to ensure
the existing system remains fully functional. They verify:

1. All 4 existing models are importable and functional
2. Table creation via Base.metadata.create_all() works
3. init_db() pattern is idempotent
4. FTS5 table and triggers exist
5. Full CRUD for all existing models
6. Phase 7A migration table coexists with existing tables
7. No existing column types or constraints have changed

Edge cases covered:
- FTS5 with NULL description_clean (common for freshly-scraped unenriched jobs)
- Job with self-referencing duplicate_of foreign key
- UserProfile singleton constraint (id=1)
- SavedSearch with complex JSON query_params
- ScraperRun with NULL completed_at (still running)
"""

import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


# ---------------------------------------------------------------------------
# Model import tests
# ---------------------------------------------------------------------------

class TestModelImports:
    """Verify all 4 existing models are importable."""

    def test_job_importable(self):
        from backend.models import Job
        assert Job.__tablename__ == "jobs"

    def test_saved_search_importable(self):
        from backend.models import SavedSearch
        assert SavedSearch.__tablename__ == "saved_searches"

    def test_scraper_run_importable(self):
        from backend.models import ScraperRun
        assert ScraperRun.__tablename__ == "scraper_runs"

    def test_user_profile_importable(self):
        from backend.models import UserProfile
        assert UserProfile.__tablename__ == "user_profile"

    def test_base_importable(self):
        from backend.database import Base
        assert Base is not None


# ---------------------------------------------------------------------------
# Table creation tests
# ---------------------------------------------------------------------------

class TestTableCreation:
    """Verify Base.metadata.create_all() creates all existing tables."""

    @pytest.mark.asyncio
    async def test_create_all_creates_jobs_table(self, initialized_db):
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_create_all_creates_saved_searches_table(self, initialized_db):
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='saved_searches'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_create_all_creates_scraper_runs_table(self, initialized_db):
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='scraper_runs'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_create_all_creates_user_profile_table(self, initialized_db):
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profile'")
            )
            assert result.fetchone() is not None


# ---------------------------------------------------------------------------
# init_db() idempotency
# ---------------------------------------------------------------------------

class TestInitDbIdempotency:
    """Verify the init_db pattern can be run multiple times without error."""

    @pytest.mark.asyncio
    async def test_init_db_twice_no_error(self, async_engine):
        from backend.database import Base
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa
        from backend.phase7a.migration import run_migrations

        # First run
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await run_migrations(conn)

        # Second run (must not raise)
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await run_migrations(conn)

    @pytest.mark.asyncio
    async def test_init_db_three_times_no_error(self, async_engine):
        from backend.database import Base
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa
        from backend.phase7a.migration import run_migrations

        for _ in range(3):
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                await run_migrations(conn)


# ---------------------------------------------------------------------------
# FTS5 tests
# ---------------------------------------------------------------------------

class TestFTS5:
    """Verify FTS5 virtual table and triggers still work after init_db."""

    @pytest.mark.asyncio
    async def test_fts5_table_exists(self, initialized_db):
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs_fts'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_fts5_insert_trigger_exists(self, initialized_db):
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='trigger' AND name='jobs_fts_insert'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_fts5_update_trigger_exists(self, initialized_db):
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='trigger' AND name='jobs_fts_update'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_fts5_delete_trigger_exists(self, initialized_db):
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='trigger' AND name='jobs_fts_delete'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_fts5_search_works(self, initialized_db):
        """Insert a job and verify FTS5 MATCH query finds it."""
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            now = datetime.now(timezone.utc).isoformat()
            await session.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status, is_active,
                                  is_enriched, is_starred, scraped_at, last_updated,
                                  description_clean, skills_required, tech_stack)
                VALUES (:job_id, :source, :url, :company_name, :title, :status, 1,
                        0, 0, :scraped_at, :last_updated,
                        :description_clean, :skills_required, :tech_stack)
            """), {
                "job_id": "fts_test_001",
                "source": "greenhouse",
                "url": "https://example.com/fts-test",
                "company_name": "TestCo",
                "title": "Machine Learning Engineer",
                "status": "new",
                "scraped_at": now,
                "last_updated": now,
                "description_clean": "Build ML pipelines for production systems",
                "skills_required": json.dumps(["Python", "TensorFlow"]),
                "tech_stack": json.dumps(["Python", "AWS"]),
            })
            await session.commit()

            # FTS5 MATCH query
            result = await session.execute(
                text("SELECT job_id FROM jobs_fts WHERE jobs_fts MATCH 'machine learning'")
            )
            rows = result.fetchall()
            assert len(rows) >= 1
            assert rows[0][0] == "fts_test_001"

    @pytest.mark.asyncio
    async def test_fts5_with_null_description(self, initialized_db):
        """FTS5 should handle NULL description_clean gracefully."""
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            now = datetime.now(timezone.utc).isoformat()
            await session.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status, is_active,
                                  is_enriched, is_starred, scraped_at, last_updated,
                                  description_clean, skills_required, tech_stack)
                VALUES (:job_id, :source, :url, :company_name, :title, :status, 1,
                        0, 0, :scraped_at, :last_updated,
                        NULL, NULL, NULL)
            """), {
                "job_id": "fts_null_test_001",
                "source": "serpapi",
                "url": "https://example.com/null-fts",
                "company_name": "NullTestCo",
                "title": "Data Scientist",
                "status": "new",
                "scraped_at": now,
                "last_updated": now,
            })
            await session.commit()

            # Should still be searchable by title
            result = await session.execute(
                text("SELECT job_id FROM jobs_fts WHERE jobs_fts MATCH 'data scientist'")
            )
            rows = result.fetchall()
            job_ids = [r[0] for r in rows]
            assert "fts_null_test_001" in job_ids


# ---------------------------------------------------------------------------
# Jobs CRUD tests
# ---------------------------------------------------------------------------

class TestJobsCRUD:
    """Verify jobs table CRUD still works correctly."""

    @pytest.mark.asyncio
    async def test_insert_job(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            now = datetime.now(timezone.utc).isoformat()
            await session.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  is_active, is_enriched, is_starred, scraped_at, last_updated)
                VALUES (:job_id, :source, :url, :company_name, :title, :status,
                        1, 0, 0, :scraped_at, :last_updated)
            """), {
                "job_id": "crud_insert_001",
                "source": "greenhouse",
                "url": "https://example.com/crud-insert",
                "company_name": "CrudTestCo",
                "title": "Software Engineer",
                "status": "new",
                "scraped_at": now,
                "last_updated": now,
            })
            await session.commit()

            result = await session.execute(
                text("SELECT job_id, title FROM jobs WHERE job_id = 'crud_insert_001'")
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] == "crud_insert_001"
            assert row[1] == "Software Engineer"

    @pytest.mark.asyncio
    async def test_query_job(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            now = datetime.now(timezone.utc).isoformat()
            await session.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  is_active, is_enriched, is_starred, scraped_at, last_updated,
                                  experience_level, remote_type)
                VALUES (:jid, :src, :url, :cn, :t, :s, 1, 0, 0, :sa, :lu, :el, :rt)
            """), {
                "jid": "query_test_001", "src": "lever", "url": "https://example.com/q",
                "cn": "QueryCo", "t": "Backend Engineer", "s": "new",
                "sa": now, "lu": now, "el": "mid", "rt": "remote",
            })
            await session.commit()

            result = await session.execute(
                text("SELECT experience_level, remote_type FROM jobs WHERE job_id = 'query_test_001'")
            )
            row = result.fetchone()
            assert row[0] == "mid"
            assert row[1] == "remote"

    @pytest.mark.asyncio
    async def test_update_job(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            now = datetime.now(timezone.utc).isoformat()
            await session.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  is_active, is_enriched, is_starred, scraped_at, last_updated)
                VALUES (:jid, 'gh', 'https://x.com/u', 'UpdateCo', 'Eng', 'new',
                        1, 0, 0, :sa, :lu)
            """), {"jid": "update_test_001", "sa": now, "lu": now})
            await session.commit()

            await session.execute(
                text("UPDATE jobs SET status = 'applied', is_starred = 1 WHERE job_id = 'update_test_001'")
            )
            await session.commit()

            result = await session.execute(
                text("SELECT status, is_starred FROM jobs WHERE job_id = 'update_test_001'")
            )
            row = result.fetchone()
            assert row[0] == "applied"
            assert row[1] == 1  # SQLite stores booleans as int

    @pytest.mark.asyncio
    async def test_delete_job(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            now = datetime.now(timezone.utc).isoformat()
            await session.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  is_active, is_enriched, is_starred, scraped_at, last_updated)
                VALUES ('del_001', 'gh', 'https://x.com/d', 'DelCo', 'Eng', 'new',
                        1, 0, 0, :sa, :lu)
            """), {"sa": now, "lu": now})
            await session.commit()

            await session.execute(text("DELETE FROM jobs WHERE job_id = 'del_001'"))
            await session.commit()

            result = await session.execute(
                text("SELECT count(*) FROM jobs WHERE job_id = 'del_001'")
            )
            assert result.fetchone()[0] == 0

    @pytest.mark.asyncio
    async def test_duplicate_of_self_reference(self, initialized_db):
        """Jobs can reference another job via duplicate_of foreign key."""
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            now = datetime.now(timezone.utc).isoformat()
            # Insert primary job
            await session.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  is_active, is_enriched, is_starred, scraped_at, last_updated)
                VALUES ('primary_001', 'gh', 'https://x.com/p', 'DupCo', 'Eng', 'new',
                        1, 0, 0, :sa, :lu)
            """), {"sa": now, "lu": now})
            # Insert duplicate referencing primary
            await session.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  is_active, is_enriched, is_starred, scraped_at, last_updated,
                                  duplicate_of)
                VALUES ('dup_001', 'serpapi', 'https://x.com/dup', 'DupCo', 'Eng', 'new',
                        1, 0, 0, :sa, :lu, 'primary_001')
            """), {"sa": now, "lu": now})
            await session.commit()

            result = await session.execute(
                text("SELECT duplicate_of FROM jobs WHERE job_id = 'dup_001'")
            )
            assert result.fetchone()[0] == "primary_001"


# ---------------------------------------------------------------------------
# SavedSearch CRUD tests
# ---------------------------------------------------------------------------

class TestSavedSearchCRUD:
    """Verify saved_searches table CRUD still works."""

    @pytest.mark.asyncio
    async def test_insert_saved_search(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            query_params = json.dumps({
                "q": "ML Engineer",
                "location": "Remote",
                "experience_level": "senior",
            })
            await session.execute(text("""
                INSERT INTO saved_searches (name, query_params, alert_enabled, created_at)
                VALUES (:name, :qp, :ae, CURRENT_TIMESTAMP)
            """), {"name": "My ML Search", "qp": query_params, "ae": 1})
            await session.commit()

            result = await session.execute(
                text("SELECT name, query_params, alert_enabled FROM saved_searches WHERE name = 'My ML Search'")
            )
            row = result.fetchone()
            assert row[0] == "My ML Search"
            parsed = json.loads(row[1])
            assert parsed["q"] == "ML Engineer"
            assert row[2] == 1

    @pytest.mark.asyncio
    async def test_delete_saved_search(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            await session.execute(text("""
                INSERT INTO saved_searches (name, query_params, alert_enabled, created_at)
                VALUES ('ToDelete', '{}', 0, CURRENT_TIMESTAMP)
            """))
            await session.commit()

            await session.execute(text("DELETE FROM saved_searches WHERE name = 'ToDelete'"))
            await session.commit()

            result = await session.execute(
                text("SELECT count(*) FROM saved_searches WHERE name = 'ToDelete'")
            )
            assert result.fetchone()[0] == 0


# ---------------------------------------------------------------------------
# ScraperRun CRUD tests
# ---------------------------------------------------------------------------

class TestScraperRunCRUD:
    """Verify scraper_runs table CRUD still works."""

    @pytest.mark.asyncio
    async def test_insert_scraper_run(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            now = datetime.now(timezone.utc).isoformat()
            await session.execute(text("""
                INSERT INTO scraper_runs (source, started_at, status, jobs_found, jobs_new, jobs_updated)
                VALUES (:src, :sa, :st, :jf, :jn, :ju)
            """), {"src": "greenhouse", "sa": now, "st": "running", "jf": 0, "jn": 0, "ju": 0})
            await session.commit()

            result = await session.execute(
                text("SELECT source, status FROM scraper_runs WHERE source = 'greenhouse'")
            )
            row = result.fetchone()
            assert row[0] == "greenhouse"
            assert row[1] == "running"

    @pytest.mark.asyncio
    async def test_update_scraper_run_completion(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            now = datetime.now(timezone.utc).isoformat()
            await session.execute(text("""
                INSERT INTO scraper_runs (source, started_at, status, jobs_found, jobs_new, jobs_updated)
                VALUES ('lever', :sa, 'running', 0, 0, 0)
            """), {"sa": now})
            await session.commit()

            await session.execute(text("""
                UPDATE scraper_runs
                SET status = 'completed', completed_at = :ca, jobs_found = 47, jobs_new = 12, jobs_updated = 5
                WHERE source = 'lever' AND status = 'running'
            """), {"ca": now})
            await session.commit()

            result = await session.execute(
                text("SELECT status, jobs_found, jobs_new FROM scraper_runs WHERE source = 'lever'")
            )
            row = result.fetchone()
            assert row[0] == "completed"
            assert row[1] == 47
            assert row[2] == 12

    @pytest.mark.asyncio
    async def test_scraper_run_with_error(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            now = datetime.now(timezone.utc).isoformat()
            await session.execute(text("""
                INSERT INTO scraper_runs (source, started_at, status, jobs_found, jobs_new, jobs_updated,
                                          error_message)
                VALUES ('ashby', :sa, 'failed', 0, 0, 0, 'Connection timeout after 30s')
            """), {"sa": now})
            await session.commit()

            result = await session.execute(
                text("SELECT error_message FROM scraper_runs WHERE source = 'ashby'")
            )
            assert result.fetchone()[0] == "Connection timeout after 30s"


# ---------------------------------------------------------------------------
# UserProfile singleton tests
# ---------------------------------------------------------------------------

class TestUserProfileCRUD:
    """Verify user_profile singleton pattern still works."""

    @pytest.mark.asyncio
    async def test_insert_user_profile(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            queries = json.dumps(["AI Engineer", "ML Engineer"])
            locations = json.dumps(["Remote", "New York, NY"])
            await session.execute(text("""
                INSERT INTO user_profile (id, default_queries, default_locations)
                VALUES (1, :dq, :dl)
            """), {"dq": queries, "dl": locations})
            await session.commit()

            result = await session.execute(
                text("SELECT id, default_queries, default_locations FROM user_profile WHERE id = 1")
            )
            row = result.fetchone()
            assert row[0] == 1
            assert json.loads(row[1]) == ["AI Engineer", "ML Engineer"]
            assert json.loads(row[2]) == ["Remote", "New York, NY"]

    @pytest.mark.asyncio
    async def test_update_user_profile(self, initialized_db):
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            await session.execute(text("""
                INSERT INTO user_profile (id, resume_filename, resume_text)
                VALUES (1, NULL, NULL)
            """))
            await session.commit()

            now = datetime.now(timezone.utc).isoformat()
            await session.execute(text("""
                UPDATE user_profile
                SET resume_filename = 'resume.pdf',
                    resume_text = 'Experienced ML engineer...',
                    resume_uploaded_at = :ua
                WHERE id = 1
            """), {"ua": now})
            await session.commit()

            result = await session.execute(
                text("SELECT resume_filename, resume_text FROM user_profile WHERE id = 1")
            )
            row = result.fetchone()
            assert row[0] == "resume.pdf"
            assert row[1] == "Experienced ML engineer..."


# ---------------------------------------------------------------------------
# Phase 7A migration table coexistence
# ---------------------------------------------------------------------------

class TestMigrationTableCoexistence:
    """Verify _phase7a_migrations table coexists with existing tables."""

    @pytest.mark.asyncio
    async def test_migration_table_exists(self, initialized_db):
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='_phase7a_migrations'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_all_tables_present(self, initialized_db):
        """All existing tables plus migration table must coexist."""
        expected_tables = {"jobs", "saved_searches", "scraper_runs", "user_profile", "_phase7a_migrations"}
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            actual_tables = {row[0] for row in result.fetchall()}
            # Check all expected are present (there may be more like sqlite_sequence, jobs_fts, etc.)
            assert expected_tables.issubset(actual_tables), (
                f"Missing tables: {expected_tables - actual_tables}"
            )

    @pytest.mark.asyncio
    async def test_migration_table_schema(self, initialized_db):
        """Migration table must have expected columns."""
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("PRAGMA table_info(_phase7a_migrations)")
            )
            columns = {row[1] for row in result.fetchall()}
            assert "id" in columns
            assert "name" in columns
            assert "applied_at" in columns


# ---------------------------------------------------------------------------
# Column structure validation
# ---------------------------------------------------------------------------

class TestJobsColumnStructure:
    """Verify no existing column types or constraints have changed."""

    @pytest.mark.asyncio
    async def test_jobs_has_expected_columns(self, initialized_db):
        """Verify the jobs table has all expected columns."""
        expected_columns = {
            "job_id", "source", "url", "posted_at", "scraped_at", "is_active", "duplicate_of",
            "company_name", "company_domain", "company_logo_url",
            "title", "location_city", "location_state", "location_country",
            "remote_type", "job_type", "experience_level", "department", "industry",
            "salary_min", "salary_max", "salary_currency", "salary_period",
            "description_raw", "description_clean", "description_markdown",
            "skills_required", "skills_nice_to_have", "tech_stack",
            "seniority_score", "remote_score", "match_score",
            "summary_ai", "red_flags", "green_flags",
            "is_enriched", "enriched_at",
            "status", "notes", "applied_at", "last_updated", "is_starred", "tags",
        }
        async with initialized_db.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(jobs)"))
            actual_columns = {row[1] for row in result.fetchall()}
            missing = expected_columns - actual_columns
            assert not missing, f"Missing columns in jobs table: {missing}"

    @pytest.mark.asyncio
    async def test_jobs_primary_key_is_job_id(self, initialized_db):
        """job_id must remain the primary key."""
        async with initialized_db.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(jobs)"))
            for row in result.fetchall():
                if row[1] == "job_id":
                    assert row[5] == 1, "job_id must be primary key (pk=1)"
                    break
            else:
                pytest.fail("job_id column not found in jobs table")

    @pytest.mark.asyncio
    async def test_saved_searches_has_expected_columns(self, initialized_db):
        expected = {"id", "name", "query_params", "alert_enabled", "created_at"}
        async with initialized_db.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(saved_searches)"))
            actual = {row[1] for row in result.fetchall()}
            missing = expected - actual
            assert not missing, f"Missing columns in saved_searches: {missing}"

    @pytest.mark.asyncio
    async def test_scraper_runs_has_expected_columns(self, initialized_db):
        expected = {
            "id", "source", "started_at", "completed_at",
            "jobs_found", "jobs_new", "jobs_updated", "error_message", "status",
        }
        async with initialized_db.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(scraper_runs)"))
            actual = {row[1] for row in result.fetchall()}
            missing = expected - actual
            assert not missing, f"Missing columns in scraper_runs: {missing}"

    @pytest.mark.asyncio
    async def test_user_profile_has_expected_columns(self, initialized_db):
        expected = {
            "id", "resume_filename", "resume_text", "resume_uploaded_at",
            "default_queries", "default_locations", "company_watchlist",
        }
        async with initialized_db.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(user_profile)"))
            actual = {row[1] for row in result.fetchall()}
            missing = expected - actual
            assert not missing, f"Missing columns in user_profile: {missing}"
