"""Unit tests for OutcomeService using an in-memory SQLite database."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure outcomes & pipeline tables are registered with Base.metadata
import app.outcomes.models  # noqa: F401
from app.jobs.models import Job
from app.outcomes.schemas import OutcomeCreate, OutcomeUpdate
from app.outcomes.service import OutcomeService
from app.pipeline.models import Application
from app.shared.errors import NotFoundError, ValidationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_application(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    company_name: str = "Acme Corp",
) -> Application:
    if user_id is None:
        user_id = uuid.uuid4()
    app = Application(
        user_id=user_id,
        company_name=company_name,
        position_title="Engineer",
        source="manual",
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


async def _make_job(db: AsyncSession, *, user_id: uuid.UUID) -> Job:
    job = Job(
        id=f"job-{uuid.uuid4().hex[:16]}",
        user_id=user_id,
        source="test",
        title="Engineer",
        company_name="Acme Corp",
    )
    db.add(job)
    await db.commit()
    return job


# ---------------------------------------------------------------------------
# record_outcome
# ---------------------------------------------------------------------------


class TestRecordOutcome:
    @pytest.mark.asyncio
    async def test_happy_path(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        app_obj = await _make_application(db_session, user_id=user_id, company_name="Acme")
        svc = OutcomeService(db_session)
        data = OutcomeCreate(stage_reached="interviewing", days_to_response=7)

        outcome = await svc.record_outcome(app_obj.id, user_id, data)

        assert outcome.application_id == app_obj.id
        assert outcome.user_id == user_id
        assert outcome.stage_reached == "interviewing"
        assert outcome.days_to_response == 7
        assert isinstance(outcome.id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_missing_application_raises_not_found(self, db_session: AsyncSession):
        svc = OutcomeService(db_session)
        with pytest.raises(NotFoundError):
            await svc.record_outcome(uuid.uuid4(), uuid.uuid4(), OutcomeCreate())

    @pytest.mark.asyncio
    async def test_wrong_user_raises_not_found(self, db_session: AsyncSession):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        app_obj = await _make_application(db_session, user_id=user_a)
        svc = OutcomeService(db_session)
        with pytest.raises(NotFoundError):
            await svc.record_outcome(app_obj.id, user_b, OutcomeCreate())

    @pytest.mark.asyncio
    async def test_duplicate_outcome_raises_validation_error(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        app_obj = await _make_application(db_session, user_id=user_id)
        svc = OutcomeService(db_session)
        await svc.record_outcome(app_obj.id, user_id, OutcomeCreate())
        with pytest.raises(ValidationError, match="Outcome already exists"):
            await svc.record_outcome(app_obj.id, user_id, OutcomeCreate())

    @pytest.mark.asyncio
    async def test_stage_reached_falls_back_to_application_status(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        app_obj = await _make_application(db_session, user_id=user_id)
        # Default application status is "saved"
        svc = OutcomeService(db_session)
        # No stage_reached provided → should use application.status
        outcome = await svc.record_outcome(app_obj.id, user_id, OutcomeCreate())
        assert outcome.stage_reached == app_obj.status

    @pytest.mark.asyncio
    async def test_ghosted_flag_updates_company_insight(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        app_obj = await _make_application(db_session, user_id=user_id, company_name="GhostCo")
        svc = OutcomeService(db_session)
        await svc.record_outcome(app_obj.id, user_id, OutcomeCreate(was_ghosted=True))
        # Should not raise; company insight created with ghosted_count = 1
        insight = await svc.get_company_insights("GhostCo", user_id)
        assert insight.ghosted_count == 1


# ---------------------------------------------------------------------------
# update_outcome
# ---------------------------------------------------------------------------


class TestUpdateOutcome:
    @pytest.mark.asyncio
    async def test_update_fields(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        app_obj = await _make_application(db_session, user_id=user_id)
        svc = OutcomeService(db_session)
        await svc.record_outcome(app_obj.id, user_id, OutcomeCreate())

        updated = await svc.update_outcome(
            app_obj.id, user_id, OutcomeUpdate(rejection_reason="budget", days_to_response=14)
        )
        assert updated.rejection_reason == "budget"
        assert updated.days_to_response == 14

    @pytest.mark.asyncio
    async def test_update_missing_outcome_raises_not_found(self, db_session: AsyncSession):
        svc = OutcomeService(db_session)
        with pytest.raises(NotFoundError):
            await svc.update_outcome(uuid.uuid4(), uuid.uuid4(), OutcomeUpdate())

    @pytest.mark.asyncio
    async def test_empty_update_does_not_change_data(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        app_obj = await _make_application(db_session, user_id=user_id)
        svc = OutcomeService(db_session)
        await svc.record_outcome(app_obj.id, user_id, OutcomeCreate(days_to_response=5))

        outcome = await svc.update_outcome(app_obj.id, user_id, OutcomeUpdate())
        assert outcome.days_to_response == 5


# ---------------------------------------------------------------------------
# get_outcome
# ---------------------------------------------------------------------------


class TestGetOutcome:
    @pytest.mark.asyncio
    async def test_returns_existing_outcome(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        app_obj = await _make_application(db_session, user_id=user_id)
        svc = OutcomeService(db_session)
        created = await svc.record_outcome(app_obj.id, user_id, OutcomeCreate(offer_amount=100000))

        fetched = await svc.get_outcome(app_obj.id, user_id)
        assert fetched.id == created.id
        assert fetched.offer_amount == 100000

    @pytest.mark.asyncio
    async def test_missing_raises_not_found(self, db_session: AsyncSession):
        svc = OutcomeService(db_session)
        with pytest.raises(NotFoundError):
            await svc.get_outcome(uuid.uuid4(), uuid.uuid4())


# ---------------------------------------------------------------------------
# get_user_stats
# ---------------------------------------------------------------------------


class TestGetUserStats:
    @pytest.mark.asyncio
    async def test_empty_user_returns_zero_stats(self, db_session: AsyncSession):
        svc = OutcomeService(db_session)
        stats = await svc.get_user_stats(uuid.uuid4())
        assert stats.total_applications == 0
        assert stats.total_outcomes == 0
        assert stats.ghosting_rate == 0.0
        assert stats.response_rate == 0.0
        assert stats.offer_rate == 0.0
        assert stats.avg_days_to_response is None
        assert stats.avg_offer_amount is None

    @pytest.mark.asyncio
    async def test_stats_with_data(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        app1 = await _make_application(db_session, user_id=user_id)
        app2 = await _make_application(db_session, user_id=user_id)
        svc = OutcomeService(db_session)
        await svc.record_outcome(
            app1.id, user_id, OutcomeCreate(days_to_response=5, offer_amount=90000)
        )
        await svc.record_outcome(app2.id, user_id, OutcomeCreate(was_ghosted=True))

        stats = await svc.get_user_stats(user_id)
        assert stats.total_applications == 2
        assert stats.total_outcomes == 2
        assert stats.avg_days_to_response == 5.0
        assert stats.ghosting_rate == 0.5
        # 1 out of 2 responded
        assert stats.response_rate == 0.5
        assert stats.offer_rate == 0.5
        assert stats.avg_offer_amount == 90000.0


# ---------------------------------------------------------------------------
# get_company_insights
# ---------------------------------------------------------------------------


class TestGetCompanyInsights:
    @pytest.mark.asyncio
    async def test_no_data_raises_not_found(self, db_session: AsyncSession):
        svc = OutcomeService(db_session)
        with pytest.raises(NotFoundError):
            await svc.get_company_insights("NoSuchCo", uuid.uuid4())

    @pytest.mark.asyncio
    async def test_insight_computed_from_outcomes(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        app_obj = await _make_application(db_session, user_id=user_id, company_name="TechCorp")
        svc = OutcomeService(db_session)
        await svc.record_outcome(
            app_obj.id,
            user_id,
            OutcomeCreate(offer_amount=120000, days_to_response=10),
        )

        insight = await svc.get_company_insights("TechCorp", user_id)
        assert insight.company_name == "TechCorp"
        assert insight.total_applications == 1
        assert insight.offers_received == 1
        assert insight.offer_rate == 1.0
        assert insight.avg_offer_amount == 120000.0
