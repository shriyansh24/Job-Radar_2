from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.outcomes.schemas import OutcomeCreate, OutcomeUpdate
from app.outcomes.service import OutcomeService
from app.pipeline.models import Application
from app.shared.errors import NotFoundError, ValidationError


async def _create_user(db: AsyncSession) -> User:
    from app.auth.service import hash_password

    user = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("password123"),
        display_name="Test User",
    )
    db.add(user)
    await db.flush()
    return user


async def _create_application(
    db: AsyncSession,
    user: User,
    company_name: str = "Acme Corp",
    status: str = "applied",
) -> Application:
    app = Application(
        id=uuid.uuid4(),
        user_id=user.id,
        company_name=company_name,
        position_title="Software Engineer",
        status=status,
    )
    db.add(app)
    await db.flush()
    return app


@pytest.mark.asyncio
async def test_record_outcome(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    application = await _create_application(db_session, user)

    svc = OutcomeService(db_session)
    outcome = await svc.record_outcome(
        application_id=application.id,
        user_id=user.id,
        data=OutcomeCreate(
            rejection_reason="underqualified",
            rejection_stage="screening",
            days_to_response=5,
            was_ghosted=False,
            stage_reached="rejected",
        ),
    )

    assert outcome.application_id == application.id
    assert outcome.rejection_reason == "underqualified"
    assert outcome.rejection_stage == "screening"
    assert outcome.days_to_response == 5
    assert outcome.stage_reached == "rejected"
    assert outcome.was_ghosted is False


@pytest.mark.asyncio
async def test_record_outcome_duplicate_raises(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    application = await _create_application(db_session, user)

    svc = OutcomeService(db_session)
    await svc.record_outcome(
        application_id=application.id,
        user_id=user.id,
        data=OutcomeCreate(stage_reached="applied"),
    )

    with pytest.raises(ValidationError, match="already exists"):
        await svc.record_outcome(
            application_id=application.id,
            user_id=user.id,
            data=OutcomeCreate(stage_reached="applied"),
        )


@pytest.mark.asyncio
async def test_record_outcome_wrong_user(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    other_user = await _create_user(db_session)
    application = await _create_application(db_session, user)

    svc = OutcomeService(db_session)
    with pytest.raises(NotFoundError):
        await svc.record_outcome(
            application_id=application.id,
            user_id=other_user.id,
            data=OutcomeCreate(stage_reached="applied"),
        )


@pytest.mark.asyncio
async def test_record_outcome_nonexistent_application(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)

    svc = OutcomeService(db_session)
    with pytest.raises(NotFoundError, match="Application not found"):
        await svc.record_outcome(
            application_id=uuid.uuid4(),
            user_id=user.id,
            data=OutcomeCreate(stage_reached="applied"),
        )


@pytest.mark.asyncio
async def test_update_outcome(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    application = await _create_application(db_session, user)

    svc = OutcomeService(db_session)
    await svc.record_outcome(
        application_id=application.id,
        user_id=user.id,
        data=OutcomeCreate(stage_reached="interviewing"),
    )

    updated = await svc.update_outcome(
        application_id=application.id,
        user_id=user.id,
        data=OutcomeUpdate(
            offer_amount=150000,
            offer_equity="0.5% over 4 years",
            final_decision="accepted",
            stage_reached="offer",
        ),
    )

    assert updated.offer_amount == 150000
    assert updated.offer_equity == "0.5% over 4 years"
    assert updated.final_decision == "accepted"
    assert updated.stage_reached == "offer"


@pytest.mark.asyncio
async def test_update_outcome_refreshes_company_insight(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    application = await _create_application(db_session, user, company_name="RefreshCo")

    svc = OutcomeService(db_session)
    await svc.record_outcome(
        application_id=application.id,
        user_id=user.id,
        data=OutcomeCreate(
            stage_reached="rejected",
            rejection_reason="timing",
            days_to_response=4,
        ),
    )

    await svc.update_outcome(
        application_id=application.id,
        user_id=user.id,
        data=OutcomeUpdate(
            offer_amount=140000,
            rejection_reason=None,
            stage_reached="offer",
        ),
    )

    insight = await svc.get_company_insights("RefreshCo", user.id)
    assert insight.total_applications == 1
    assert insight.offer_rate == 1.0
    assert insight.offers_received == 1
    assert insight.avg_offer_amount == 140000.0
    assert insight.rejection_rate == 0.0


@pytest.mark.asyncio
async def test_update_outcome_not_found(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)

    svc = OutcomeService(db_session)
    with pytest.raises(NotFoundError):
        await svc.update_outcome(
            application_id=uuid.uuid4(),
            user_id=user.id,
            data=OutcomeUpdate(offer_amount=100000),
        )


@pytest.mark.asyncio
async def test_get_outcome(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    application = await _create_application(db_session, user)

    svc = OutcomeService(db_session)
    created = await svc.record_outcome(
        application_id=application.id,
        user_id=user.id,
        data=OutcomeCreate(stage_reached="offer", offer_amount=120000),
    )

    fetched = await svc.get_outcome(application.id, user.id)
    assert fetched.id == created.id
    assert fetched.offer_amount == 120000


@pytest.mark.asyncio
async def test_get_user_stats_empty(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)

    svc = OutcomeService(db_session)
    stats = await svc.get_user_stats(user.id)

    assert stats.total_applications == 0
    assert stats.total_outcomes == 0
    assert stats.ghosting_rate == 0.0
    assert stats.offer_rate == 0.0
    assert stats.top_rejection_reasons == []
    assert stats.stage_distribution == {}


@pytest.mark.asyncio
async def test_get_user_stats_with_data(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    svc = OutcomeService(db_session)

    # Create several applications with outcomes
    app1 = await _create_application(db_session, user, company_name="Alpha Inc")
    await svc.record_outcome(
        app1.id,
        user.id,
        OutcomeCreate(
            stage_reached="rejected",
            rejection_reason="underqualified",
            days_to_response=3,
        ),
    )

    app2 = await _create_application(db_session, user, company_name="Beta Corp")
    await svc.record_outcome(
        app2.id,
        user.id,
        OutcomeCreate(
            stage_reached="offer",
            offer_amount=130000,
            days_to_response=10,
        ),
    )

    app3 = await _create_application(db_session, user, company_name="Gamma LLC")
    await svc.record_outcome(
        app3.id,
        user.id,
        OutcomeCreate(stage_reached="applied", was_ghosted=True),
    )

    stats = await svc.get_user_stats(user.id)

    assert stats.total_applications == 3
    assert stats.total_outcomes == 3
    assert stats.avg_days_to_response == 6.5  # (3 + 10) / 2
    assert stats.ghosting_rate == pytest.approx(0.33, abs=0.01)
    assert stats.response_rate == pytest.approx(0.67, abs=0.01)
    assert stats.offer_rate == pytest.approx(0.33, abs=0.01)
    assert stats.avg_offer_amount == 130000.0
    assert len(stats.top_rejection_reasons) == 1
    assert stats.top_rejection_reasons[0].reason == "underqualified"
    assert stats.stage_distribution["rejected"] == 1
    assert stats.stage_distribution["offer"] == 1
    assert stats.stage_distribution["applied"] == 1


@pytest.mark.asyncio
async def test_company_insight_created_on_record(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    application = await _create_application(db_session, user, company_name="TestCo")

    svc = OutcomeService(db_session)
    await svc.record_outcome(
        application.id,
        user.id,
        OutcomeCreate(
            stage_reached="rejected",
            rejection_reason="salary",
            days_to_response=7,
        ),
    )

    insight = await svc.get_company_insights("TestCo", user.id)
    assert insight.company_name == "TestCo"
    assert insight.total_applications == 1
    assert insight.callback_count == 1
    assert insight.avg_response_days == 7.0


@pytest.mark.asyncio
async def test_company_insight_aggregates_multiple_outcomes(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    svc = OutcomeService(db_session)

    app1 = await _create_application(db_session, user, company_name="BigCo")
    await svc.record_outcome(
        app1.id,
        user.id,
        OutcomeCreate(
            stage_reached="rejected",
            rejection_reason="culture_fit",
            days_to_response=5,
        ),
    )

    app2 = await _create_application(db_session, user, company_name="BigCo")
    await svc.record_outcome(
        app2.id,
        user.id,
        OutcomeCreate(
            stage_reached="offer",
            offer_amount=160000,
            days_to_response=15,
        ),
    )

    insight = await svc.get_company_insights("BigCo", user.id)
    assert insight.total_applications == 2
    assert insight.callback_count == 2
    assert insight.avg_response_days == 10.0  # (5 + 15) / 2
    assert insight.offers_received == 1
    assert insight.avg_offer_amount == 160000.0
    assert insight.offer_rate == 0.5


@pytest.mark.asyncio
async def test_company_insight_not_found(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    svc = OutcomeService(db_session)

    with pytest.raises(NotFoundError, match="No outcome data found"):
        await svc.get_company_insights("NonexistentCorp", user.id)


@pytest.mark.asyncio
async def test_record_outcome_defaults_stage_from_application(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    application = await _create_application(db_session, user, status="interviewing")

    svc = OutcomeService(db_session)
    outcome = await svc.record_outcome(
        application.id,
        user.id,
        OutcomeCreate(),  # No stage_reached provided
    )

    assert outcome.stage_reached == "interviewing"


@pytest.mark.asyncio
async def test_record_outcome_with_offer_data(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    application = await _create_application(db_session, user, status="offer")

    svc = OutcomeService(db_session)
    outcome = await svc.record_outcome(
        application.id,
        user.id,
        OutcomeCreate(
            stage_reached="offer",
            offer_amount=150000,
            offer_total_comp=200000,
            offer_equity="1% over 4 years",
            negotiated_amount=165000,
            final_decision="accepted",
            referral_used=True,
            cover_letter_used=True,
            application_method="manual",
        ),
    )

    assert outcome.offer_amount == 150000
    assert outcome.offer_total_comp == 200000
    assert outcome.negotiated_amount == 165000
    assert outcome.final_decision == "accepted"
    assert outcome.referral_used is True
    assert outcome.cover_letter_used is True
    assert outcome.application_method == "manual"


@pytest.mark.asyncio
async def test_ghosted_outcome_updates_company_insight(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    app1 = await _create_application(db_session, user, company_name="GhostCo")

    svc = OutcomeService(db_session)
    await svc.record_outcome(
        app1.id,
        user.id,
        OutcomeCreate(stage_reached="applied", was_ghosted=True),
    )

    insight = await svc.get_company_insights("GhostCo", user.id)
    assert insight.ghosted_count == 1
    assert insight.ghost_rate == 1.0
