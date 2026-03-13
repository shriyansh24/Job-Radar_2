"""Test that new columns exist on Job and UserProfile models."""
import pytest
from sqlalchemy import inspect
from backend.database import engine, Base
from backend.models import Job, UserProfile, ResumeVersion, ApplicationAttempt


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestJobNewColumns:
    async def test_dedup_hash_column_exists(self):
        assert hasattr(Job, "dedup_hash")

    async def test_tfidf_score_column_exists(self):
        assert hasattr(Job, "tfidf_score")

    async def test_council_scores_column_exists(self):
        assert hasattr(Job, "council_scores")

    async def test_apply_questions_column_exists(self):
        assert hasattr(Job, "apply_questions")


class TestUserProfileNewColumns:
    async def test_resume_parsed_column_exists(self):
        assert hasattr(UserProfile, "resume_parsed")

    async def test_application_profile_column_exists(self):
        assert hasattr(UserProfile, "application_profile")


class TestNewModels:
    async def test_resume_version_table_created(self):
        async with engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        assert "resume_versions" in tables

    async def test_application_attempt_table_created(self):
        async with engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        assert "application_attempts" in tables

    async def test_resume_version_fields(self):
        assert hasattr(ResumeVersion, "id")
        assert hasattr(ResumeVersion, "filename")
        assert hasattr(ResumeVersion, "format")
        assert hasattr(ResumeVersion, "file_path")
        assert hasattr(ResumeVersion, "parsed_text")
        assert hasattr(ResumeVersion, "is_default")

    async def test_application_attempt_fields(self):
        assert hasattr(ApplicationAttempt, "job_id")
        assert hasattr(ApplicationAttempt, "ats_provider")
        assert hasattr(ApplicationAttempt, "fields_filled")
        assert hasattr(ApplicationAttempt, "status")
