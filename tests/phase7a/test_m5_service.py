"""
Tests for Module 5 — Application Tracker: Service layer.

Covers:
  - create_application: valid creation, edge cases, validation
  - get_application: found and not found
  - list_applications: filtering, pagination
  - update_application: user-owned fields, disallowed fields
  - update_status: valid transitions, invalid transitions, auto-timestamps
  - get_status_history: ordering
  - archive/unarchive
  - reminders and follow-ups
  - link_canonical_job
  - duplicate detection
  - concurrent-safe behavior
"""

from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.database import Base
from backend.models import Job
from backend.phase7a.m5_service import (
    ApplicationService,
    ApplicationNotFoundError,
    ApplicationCreateError,
    DuplicateApplicationError,
    InvalidStatusTransitionError,
)


pytestmark = pytest.mark.asyncio


# ------------------------------------------------------------------
# Local fixtures
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


@pytest_asyncio.fixture
def svc() -> ApplicationService:
    """Provide an ApplicationService instance."""
    return ApplicationService()


# ------------------------------------------------------------------
# create_application
# ------------------------------------------------------------------


class TestCreateApplication:
    """Tests for ApplicationService.create_application."""

    async def test_create_with_legacy_job_id(self, db_session: AsyncSession, svc: ApplicationService):
        """Create an application linked to a legacy job."""
        job = await seed_job(db_session, job_id="create_legacy")

        app = await svc.create_application(
            db_session,
            legacy_job_id="create_legacy",
            status="saved",
            notes="Looking good!",
        )

        assert app.application_id is not None
        assert len(app.application_id) == 32
        assert app.legacy_job_id == "create_legacy"
        assert app.canonical_job_id is None
        assert app.status == "saved"
        assert app.notes == "Looking good!"
        assert app.is_archived is False
        assert app.created_at is not None

    async def test_create_with_canonical_job_id(self, db_session: AsyncSession, svc: ApplicationService):
        """Create an application linked to a canonical job (future M4)."""
        app = await svc.create_application(
            db_session,
            canonical_job_id="canon_new_001",
        )

        assert app.canonical_job_id == "canon_new_001"
        assert app.legacy_job_id is None

    async def test_create_with_both_ids(self, db_session: AsyncSession, svc: ApplicationService):
        """Create with both legacy and canonical IDs."""
        job = await seed_job(db_session, job_id="create_both")

        app = await svc.create_application(
            db_session,
            legacy_job_id="create_both",
            canonical_job_id="canon_both_001",
        )

        assert app.legacy_job_id == "create_both"
        assert app.canonical_job_id == "canon_both_001"

    async def test_create_with_no_job_link_raises(self, db_session: AsyncSession, svc: ApplicationService):
        """Must provide at least one job link."""
        with pytest.raises(ApplicationCreateError, match="at least one"):
            await svc.create_application(db_session)

    async def test_create_with_invalid_status_raises(self, db_session: AsyncSession, svc: ApplicationService):
        """Invalid status value should raise."""
        with pytest.raises(ApplicationCreateError, match="Invalid status"):
            await svc.create_application(
                db_session,
                canonical_job_id="canon_bad",
                status="nonexistent_status",
            )

    async def test_create_records_initial_status_history(self, db_session: AsyncSession, svc: ApplicationService):
        """Creating an application should record initial status in history."""
        job = await seed_job(db_session, job_id="create_history")

        app = await svc.create_application(
            db_session,
            legacy_job_id="create_history",
            status="saved",
        )

        history = await svc.get_status_history(db_session, app.application_id)
        assert len(history) == 1
        assert history[0].old_status is None
        assert history[0].new_status == "saved"
        assert history[0].change_source == "user"

    async def test_create_with_tags_and_custom_fields(self, db_session: AsyncSession, svc: ApplicationService):
        """Tags and custom_fields are stored correctly."""
        app = await svc.create_application(
            db_session,
            canonical_job_id="canon_tags",
            tags=["dream-job", "referral"],
            custom_fields={"referrer": "Jane", "priority": "high"},
        )

        assert app.tags == ["dream-job", "referral"]
        assert app.custom_fields["referrer"] == "Jane"

    async def test_create_with_applied_at(self, db_session: AsyncSession, svc: ApplicationService):
        """applied_at and applied_via can be set at creation."""
        now = datetime.now(timezone.utc)
        app = await svc.create_application(
            db_session,
            canonical_job_id="canon_applied",
            status="applied",
            applied_at=now,
            applied_via="manual",
        )

        assert app.applied_at == now
        assert app.applied_via == "manual"

    async def test_create_duplicate_legacy_raises(self, db_session: AsyncSession, svc: ApplicationService):
        """Cannot create two applications for the same legacy job."""
        job = await seed_job(db_session, job_id="dup_legacy")

        await svc.create_application(
            db_session,
            legacy_job_id="dup_legacy",
        )

        with pytest.raises(DuplicateApplicationError):
            await svc.create_application(
                db_session,
                legacy_job_id="dup_legacy",
            )

    async def test_create_duplicate_canonical_raises(self, db_session: AsyncSession, svc: ApplicationService):
        """Cannot create two applications for the same canonical job."""
        await svc.create_application(
            db_session,
            canonical_job_id="dup_canon",
        )

        with pytest.raises(DuplicateApplicationError):
            await svc.create_application(
                db_session,
                canonical_job_id="dup_canon",
            )

    async def test_create_duplicate_allowed_if_archived(self, db_session: AsyncSession, svc: ApplicationService):
        """Can create a new application for a job if the old one is archived."""
        job = await seed_job(db_session, job_id="dup_arch")

        app1 = await svc.create_application(
            db_session,
            legacy_job_id="dup_arch",
        )
        await svc.archive_application(db_session, app1.application_id)

        # Should succeed since the old one is archived
        app2 = await svc.create_application(
            db_session,
            legacy_job_id="dup_arch",
        )
        assert app2.application_id != app1.application_id


# ------------------------------------------------------------------
# get_application
# ------------------------------------------------------------------


class TestGetApplication:
    """Tests for ApplicationService.get_application."""

    async def test_get_existing(self, db_session: AsyncSession, svc: ApplicationService):
        """Get an existing application."""
        app = await svc.create_application(
            db_session,
            canonical_job_id="get_test",
        )

        fetched = await svc.get_application(db_session, app.application_id)
        assert fetched is not None
        assert fetched.application_id == app.application_id

    async def test_get_nonexistent_returns_none(self, db_session: AsyncSession, svc: ApplicationService):
        """Get a nonexistent application returns None."""
        fetched = await svc.get_application(db_session, "nonexistent_id")
        assert fetched is None


# ------------------------------------------------------------------
# list_applications
# ------------------------------------------------------------------


class TestListApplications:
    """Tests for ApplicationService.list_applications."""

    async def test_list_active_only(self, db_session: AsyncSession, svc: ApplicationService):
        """By default, only active (non-archived) applications are returned."""
        app1 = await svc.create_application(
            db_session, canonical_job_id="list_active_1",
        )
        app2 = await svc.create_application(
            db_session, canonical_job_id="list_active_2",
        )
        app3 = await svc.create_application(
            db_session, canonical_job_id="list_active_3",
        )
        await svc.archive_application(db_session, app3.application_id)

        apps = await svc.list_applications(db_session)
        ids = {a.application_id for a in apps}
        assert app1.application_id in ids
        assert app2.application_id in ids
        assert app3.application_id not in ids

    async def test_list_archived(self, db_session: AsyncSession, svc: ApplicationService):
        """Can list archived applications."""
        app = await svc.create_application(
            db_session, canonical_job_id="list_arch_1",
        )
        await svc.archive_application(db_session, app.application_id)

        apps = await svc.list_applications(db_session, is_archived=True)
        ids = {a.application_id for a in apps}
        assert app.application_id in ids

    async def test_list_by_status(self, db_session: AsyncSession, svc: ApplicationService):
        """Filter by status."""
        app1 = await svc.create_application(
            db_session, canonical_job_id="list_status_1", status="saved",
        )
        app2 = await svc.create_application(
            db_session, canonical_job_id="list_status_2", status="applied",
        )

        saved = await svc.list_applications(db_session, status="saved")
        saved_ids = {a.application_id for a in saved}
        assert app1.application_id in saved_ids
        assert app2.application_id not in saved_ids

    async def test_list_pagination(self, db_session: AsyncSession, svc: ApplicationService):
        """Pagination works correctly."""
        for i in range(5):
            await svc.create_application(
                db_session, canonical_job_id=f"list_page_{i}",
            )

        page1 = await svc.list_applications(db_session, page=1, limit=2)
        page2 = await svc.list_applications(db_session, page=2, limit=2)
        page3 = await svc.list_applications(db_session, page=3, limit=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1

        # No overlap
        all_ids = {a.application_id for a in page1 + page2 + page3}
        assert len(all_ids) == 5

    async def test_list_by_tags(self, db_session: AsyncSession, svc: ApplicationService):
        """Filter by tags (any match)."""
        app1 = await svc.create_application(
            db_session,
            canonical_job_id="list_tags_1",
            tags=["dream-job", "remote"],
        )
        app2 = await svc.create_application(
            db_session,
            canonical_job_id="list_tags_2",
            tags=["referral"],
        )
        app3 = await svc.create_application(
            db_session,
            canonical_job_id="list_tags_3",
        )

        results = await svc.list_applications(db_session, tags=["dream-job"])
        ids = {a.application_id for a in results}
        assert app1.application_id in ids
        assert app2.application_id not in ids
        assert app3.application_id not in ids

    async def test_list_limit_capped_at_200(self, db_session: AsyncSession, svc: ApplicationService):
        """Limit is capped at 200."""
        # We just test that requesting 500 doesn't error and uses the cap
        results = await svc.list_applications(db_session, limit=500)
        # Should succeed even with high limit (no results is fine)
        assert isinstance(results, list)


# ------------------------------------------------------------------
# update_application
# ------------------------------------------------------------------


class TestUpdateApplication:
    """Tests for ApplicationService.update_application."""

    async def test_update_notes(self, db_session: AsyncSession, svc: ApplicationService):
        """Update notes field."""
        app = await svc.create_application(
            db_session, canonical_job_id="update_notes",
        )

        updated = await svc.update_application(
            db_session,
            app.application_id,
            notes="Updated notes",
        )

        assert updated.notes == "Updated notes"
        assert updated.updated_at is not None

    async def test_update_tags(self, db_session: AsyncSession, svc: ApplicationService):
        """Update tags field."""
        app = await svc.create_application(
            db_session, canonical_job_id="update_tags",
        )

        updated = await svc.update_application(
            db_session,
            app.application_id,
            tags=["high-priority", "referral"],
        )

        assert updated.tags == ["high-priority", "referral"]

    async def test_update_reminder(self, db_session: AsyncSession, svc: ApplicationService):
        """Update reminder fields."""
        now = datetime.now(timezone.utc)
        app = await svc.create_application(
            db_session, canonical_job_id="update_reminder",
        )

        updated = await svc.update_application(
            db_session,
            app.application_id,
            reminder_at=now + timedelta(days=3),
            reminder_note="Follow up with recruiter",
        )

        assert updated.reminder_at is not None
        assert updated.reminder_note == "Follow up with recruiter"

    async def test_update_disallowed_field_raises(self, db_session: AsyncSession, svc: ApplicationService):
        """Updating a disallowed field should raise."""
        app = await svc.create_application(
            db_session, canonical_job_id="update_disallowed",
        )

        with pytest.raises(ValueError, match="Cannot update"):
            await svc.update_application(
                db_session,
                app.application_id,
                status="applied",  # Must use update_status()
            )

    async def test_update_nonexistent_raises(self, db_session: AsyncSession, svc: ApplicationService):
        """Updating a nonexistent application raises."""
        with pytest.raises(ApplicationNotFoundError):
            await svc.update_application(
                db_session,
                "nonexistent_app_id",
                notes="Should fail",
            )

    async def test_update_multiple_fields(self, db_session: AsyncSession, svc: ApplicationService):
        """Update multiple fields at once."""
        now = datetime.now(timezone.utc)
        app = await svc.create_application(
            db_session, canonical_job_id="update_multi",
        )

        updated = await svc.update_application(
            db_session,
            app.application_id,
            notes="Multi-update",
            tags=["urgent"],
            follow_up_at=now + timedelta(days=7),
            custom_fields={"stage": "technical"},
        )

        assert updated.notes == "Multi-update"
        assert updated.tags == ["urgent"]
        assert updated.follow_up_at is not None
        assert updated.custom_fields["stage"] == "technical"


# ------------------------------------------------------------------
# update_status
# ------------------------------------------------------------------


class TestUpdateStatus:
    """Tests for ApplicationService.update_status."""

    async def test_valid_transition_saved_to_applied(self, db_session: AsyncSession, svc: ApplicationService):
        """Transition from saved to applied."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_s2a",
        )

        updated = await svc.update_status(
            db_session,
            app.application_id,
            "applied",
            change_source="user",
            note="Submitted via company website",
        )

        assert updated.status == "applied"
        assert updated.applied_at is not None  # Auto-set

    async def test_valid_transition_applied_to_phone_screen(self, db_session: AsyncSession, svc: ApplicationService):
        """Transition from applied to phone_screen."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_a2ps",
        )
        await svc.update_status(db_session, app.application_id, "applied")

        updated = await svc.update_status(
            db_session, app.application_id, "phone_screen",
        )

        assert updated.status == "phone_screen"
        assert updated.response_at is not None  # Auto-set

    async def test_valid_transition_interviewing_to_final_round(self, db_session: AsyncSession, svc: ApplicationService):
        """Full pipeline: saved -> applied -> phone_screen -> interviewing -> final_round."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_full_pipe",
        )
        await svc.update_status(db_session, app.application_id, "applied")
        await svc.update_status(db_session, app.application_id, "phone_screen")
        await svc.update_status(db_session, app.application_id, "interviewing")

        updated = await svc.update_status(
            db_session, app.application_id, "final_round",
        )

        assert updated.status == "final_round"
        assert updated.interview_at is not None  # Set during interviewing

    async def test_valid_transition_offer_to_accepted(self, db_session: AsyncSession, svc: ApplicationService):
        """Full pipeline to accepted."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_accept",
        )
        await svc.update_status(db_session, app.application_id, "applied")
        await svc.update_status(db_session, app.application_id, "phone_screen")
        await svc.update_status(db_session, app.application_id, "interviewing")
        await svc.update_status(db_session, app.application_id, "final_round")
        await svc.update_status(db_session, app.application_id, "offer")

        updated = await svc.update_status(
            db_session, app.application_id, "accepted",
        )

        assert updated.status == "accepted"
        assert updated.offer_at is not None  # Set during offer

    async def test_valid_transition_offer_to_declined(self, db_session: AsyncSession, svc: ApplicationService):
        """Offer -> declined."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_decline",
        )
        await svc.update_status(db_session, app.application_id, "applied")
        await svc.update_status(db_session, app.application_id, "phone_screen")
        await svc.update_status(db_session, app.application_id, "interviewing")
        await svc.update_status(db_session, app.application_id, "final_round")
        await svc.update_status(db_session, app.application_id, "offer")

        updated = await svc.update_status(
            db_session, app.application_id, "declined",
        )

        assert updated.status == "declined"

    async def test_valid_transition_to_rejected(self, db_session: AsyncSession, svc: ApplicationService):
        """Can be rejected from applied."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_reject",
        )
        await svc.update_status(db_session, app.application_id, "applied")

        updated = await svc.update_status(
            db_session, app.application_id, "rejected",
        )

        assert updated.status == "rejected"
        assert updated.rejected_at is not None  # Auto-set

    async def test_valid_transition_to_ghosted(self, db_session: AsyncSession, svc: ApplicationService):
        """Can be ghosted from applied."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_ghost",
        )
        await svc.update_status(db_session, app.application_id, "applied")

        updated = await svc.update_status(
            db_session, app.application_id, "ghosted",
        )

        assert updated.status == "ghosted"

    async def test_valid_transition_to_withdrawn(self, db_session: AsyncSession, svc: ApplicationService):
        """Can withdraw from any non-terminal state."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_withdraw",
        )

        updated = await svc.update_status(
            db_session, app.application_id, "withdrawn",
        )

        assert updated.status == "withdrawn"

    async def test_invalid_transition_saved_to_offer(self, db_session: AsyncSession, svc: ApplicationService):
        """Cannot jump from saved to offer."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_bad_jump",
        )

        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            await svc.update_status(db_session, app.application_id, "offer")

        assert exc_info.value.current == "saved"
        assert exc_info.value.requested == "offer"

    async def test_invalid_transition_from_terminal(self, db_session: AsyncSession, svc: ApplicationService):
        """Cannot transition from a terminal state."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_terminal",
        )
        await svc.update_status(db_session, app.application_id, "applied")
        await svc.update_status(db_session, app.application_id, "rejected")

        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            await svc.update_status(db_session, app.application_id, "applied")

        assert "none" in str(exc_info.value).lower()  # terminal state

    async def test_invalid_transition_accepted_to_anything(self, db_session: AsyncSession, svc: ApplicationService):
        """Accepted is terminal — no outgoing transitions."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_accepted_term",
        )
        await svc.update_status(db_session, app.application_id, "applied")
        await svc.update_status(db_session, app.application_id, "phone_screen")
        await svc.update_status(db_session, app.application_id, "interviewing")
        await svc.update_status(db_session, app.application_id, "final_round")
        await svc.update_status(db_session, app.application_id, "offer")
        await svc.update_status(db_session, app.application_id, "accepted")

        with pytest.raises(InvalidStatusTransitionError):
            await svc.update_status(db_session, app.application_id, "rejected")

    async def test_invalid_status_value(self, db_session: AsyncSession, svc: ApplicationService):
        """Invalid status string raises ValueError."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_invalid_val",
        )

        with pytest.raises(ValueError, match="Invalid status"):
            await svc.update_status(db_session, app.application_id, "banana")

    async def test_invalid_change_source(self, db_session: AsyncSession, svc: ApplicationService):
        """Invalid change_source raises ValueError."""
        app = await svc.create_application(
            db_session, canonical_job_id="status_bad_source",
        )

        with pytest.raises(ValueError, match="Invalid change_source"):
            await svc.update_status(
                db_session, app.application_id, "applied",
                change_source="invalid_source",
            )

    async def test_status_update_nonexistent_raises(self, db_session: AsyncSession, svc: ApplicationService):
        """Updating status of nonexistent app raises."""
        with pytest.raises(ApplicationNotFoundError):
            await svc.update_status(
                db_session, "nonexistent", "applied",
            )

    async def test_auto_timestamp_applied_at(self, db_session: AsyncSession, svc: ApplicationService):
        """applied_at is auto-set when transitioning to 'applied'."""
        app = await svc.create_application(
            db_session, canonical_job_id="auto_ts_applied",
        )

        assert app.applied_at is None

        updated = await svc.update_status(db_session, app.application_id, "applied")
        assert updated.applied_at is not None

    async def test_auto_timestamp_not_overwritten(self, db_session: AsyncSession, svc: ApplicationService):
        """Auto-timestamp is only set if the field is currently None."""
        now = datetime.now(timezone.utc)
        app = await svc.create_application(
            db_session,
            canonical_job_id="auto_ts_keep",
            status="saved",
            applied_at=now,  # Pre-set
        )

        updated = await svc.update_status(db_session, app.application_id, "applied")
        # Should keep the original applied_at, not overwrite
        assert updated.applied_at == now

    async def test_status_history_recorded(self, db_session: AsyncSession, svc: ApplicationService):
        """Each status change is recorded in history."""
        app = await svc.create_application(
            db_session, canonical_job_id="hist_record",
        )
        await svc.update_status(db_session, app.application_id, "applied")
        await svc.update_status(db_session, app.application_id, "phone_screen")

        history = await svc.get_status_history(db_session, app.application_id)
        # 3 records: creation + 2 transitions
        assert len(history) == 3

        # Most recent first (DESC order)
        assert history[0].new_status == "phone_screen"
        assert history[0].old_status == "applied"
        assert history[1].new_status == "applied"
        assert history[1].old_status == "saved"
        assert history[2].new_status == "saved"
        assert history[2].old_status is None

    async def test_system_change_source(self, db_session: AsyncSession, svc: ApplicationService):
        """Status change with system source is recorded."""
        app = await svc.create_application(
            db_session, canonical_job_id="sys_source",
        )

        await svc.update_status(
            db_session, app.application_id, "applied",
            change_source="system",
            note="Auto-detected from browser extension",
        )

        history = await svc.get_status_history(db_session, app.application_id)
        assert history[0].change_source == "system"
        assert history[0].note == "Auto-detected from browser extension"


# ------------------------------------------------------------------
# archive / unarchive
# ------------------------------------------------------------------


class TestArchive:
    """Tests for archive and unarchive."""

    async def test_archive_application(self, db_session: AsyncSession, svc: ApplicationService):
        """Archive hides from active views."""
        app = await svc.create_application(
            db_session, canonical_job_id="archive_test",
        )

        archived = await svc.archive_application(db_session, app.application_id)
        assert archived.is_archived is True
        assert archived.updated_at is not None

    async def test_unarchive_application(self, db_session: AsyncSession, svc: ApplicationService):
        """Unarchive restores to active views."""
        app = await svc.create_application(
            db_session, canonical_job_id="unarchive_test",
        )
        await svc.archive_application(db_session, app.application_id)

        unarchived = await svc.unarchive_application(db_session, app.application_id)
        assert unarchived.is_archived is False

    async def test_archive_nonexistent_raises(self, db_session: AsyncSession, svc: ApplicationService):
        """Archiving nonexistent app raises."""
        with pytest.raises(ApplicationNotFoundError):
            await svc.archive_application(db_session, "nonexistent_arch")

    async def test_unarchive_nonexistent_raises(self, db_session: AsyncSession, svc: ApplicationService):
        """Unarchiving nonexistent app raises."""
        with pytest.raises(ApplicationNotFoundError):
            await svc.unarchive_application(db_session, "nonexistent_unarch")


# ------------------------------------------------------------------
# Reminders and follow-ups
# ------------------------------------------------------------------


class TestRemindersFollowups:
    """Tests for reminder and follow-up queries."""

    async def test_get_due_reminders(self, db_session: AsyncSession, svc: ApplicationService):
        """Get applications with reminders due."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)
        future = now + timedelta(days=3)

        app1 = await svc.create_application(
            db_session, canonical_job_id="remind_due",
        )
        await svc.update_application(
            db_session, app1.application_id,
            reminder_at=past,
            reminder_note="Follow up",
        )

        app2 = await svc.create_application(
            db_session, canonical_job_id="remind_future",
        )
        await svc.update_application(
            db_session, app2.application_id,
            reminder_at=future,
        )

        due = await svc.get_due_reminders(db_session, before=now)
        ids = {a.application_id for a in due}
        assert app1.application_id in ids
        assert app2.application_id not in ids

    async def test_get_due_followups(self, db_session: AsyncSession, svc: ApplicationService):
        """Get applications with follow-ups due."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)

        app = await svc.create_application(
            db_session, canonical_job_id="followup_due",
        )
        await svc.update_application(
            db_session, app.application_id,
            follow_up_at=past,
        )

        due = await svc.get_due_followups(db_session, before=now)
        ids = {a.application_id for a in due}
        assert app.application_id in ids

    async def test_archived_excluded_from_reminders(self, db_session: AsyncSession, svc: ApplicationService):
        """Archived applications are excluded from reminder queries."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)

        app = await svc.create_application(
            db_session, canonical_job_id="remind_archived",
        )
        await svc.update_application(
            db_session, app.application_id,
            reminder_at=past,
        )
        await svc.archive_application(db_session, app.application_id)

        due = await svc.get_due_reminders(db_session, before=now)
        ids = {a.application_id for a in due}
        assert app.application_id not in ids

    async def test_reminder_in_past_is_returned(self, db_session: AsyncSession, svc: ApplicationService):
        """A reminder set in the past should appear as due."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=7)

        app = await svc.create_application(
            db_session, canonical_job_id="remind_past",
        )
        await svc.update_application(
            db_session, app.application_id,
            reminder_at=past,
        )

        due = await svc.get_due_reminders(db_session, before=now)
        ids = {a.application_id for a in due}
        assert app.application_id in ids


# ------------------------------------------------------------------
# link_canonical_job
# ------------------------------------------------------------------


class TestLinkCanonicalJob:
    """Tests for linking canonical job IDs (future M4 integration)."""

    async def test_link_canonical(self, db_session: AsyncSession, svc: ApplicationService):
        """Link a canonical_job_id to an existing application."""
        job = await seed_job(db_session, job_id="link_legacy")

        app = await svc.create_application(
            db_session, legacy_job_id="link_legacy",
        )

        assert app.canonical_job_id is None

        updated = await svc.link_canonical_job(
            db_session, app.application_id, "canon_linked_001",
        )

        assert updated.canonical_job_id == "canon_linked_001"
        assert updated.legacy_job_id == "link_legacy"

    async def test_link_canonical_nonexistent_raises(self, db_session: AsyncSession, svc: ApplicationService):
        """Linking to a nonexistent application raises."""
        with pytest.raises(ApplicationNotFoundError):
            await svc.link_canonical_job(
                db_session, "nonexistent_link", "canon_orphan",
            )

    async def test_link_canonical_overwrites(self, db_session: AsyncSession, svc: ApplicationService):
        """Linking a new canonical_job_id overwrites the old one."""
        app = await svc.create_application(
            db_session, canonical_job_id="canon_old",
        )

        updated = await svc.link_canonical_job(
            db_session, app.application_id, "canon_new",
        )

        assert updated.canonical_job_id == "canon_new"
