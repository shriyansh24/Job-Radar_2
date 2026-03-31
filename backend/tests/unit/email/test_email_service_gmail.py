from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.email.inbound import InboundEmailMessage
from app.email.models import EmailLog
from app.email.service import EmailService
from app.jobs.models import Job
from app.notifications.models import Notification
from app.pipeline.models import Application
from app.pipeline.schemas import ApplicationCreate, StatusTransition
from app.pipeline.service import PipelineService


async def _create_user(db_session: AsyncSession, email: str) -> User:
    user = User(email=email, password_hash="hashed-password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_applied_application(
    db_session: AsyncSession,
    *,
    user_id: uuid.UUID,
    company_name: str,
) -> Application:
    job = Job(
        id=f"gmail-email-{uuid.uuid4().hex[:8]}",
        user_id=user_id,
        source="manual",
        title="Backend Engineer",
        company_name=company_name,
    )
    db_session.add(job)
    await db_session.commit()

    pipeline = PipelineService(db_session)
    application = await pipeline.create_application(
        ApplicationCreate(
            job_id=job.id,
            company_name=company_name,
            position_title="Backend Engineer",
            source="manual",
        ),
        user_id,
    )
    return await pipeline.transition_status(
        application.id,
        StatusTransition(new_status="applied", change_source="user"),
        user_id,
    )


@pytest.mark.asyncio
async def test_process_inbound_message_deduplicates_gmail_messages(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, "email-gmail-duplicate@example.com")
    application = await _create_applied_application(
        db_session,
        user_id=user.id,
        company_name="Acme Corp",
    )
    service = EmailService(db_session)
    message = InboundEmailMessage(
        sender="recruiting@acme-corp.com",
        from_address="recruiting@acme-corp.com",
        to_address="owner@jobradar.dev",
        subject="Interview Invitation",
        text="We would like to schedule an interview with you.",
        html="",
        source_provider="google",
        source_message_id="gmail-message-1",
        source_thread_id="gmail-thread-1",
    )

    first = await service.process_inbound_message(message, user.id)
    second = await service.process_inbound_message(message, user.id)

    assert first.status == "updated"
    assert first.application_id == application.id
    assert second.status == "duplicate"
    assert second.application_id == application.id

    logs = list(
        (
            await db_session.scalars(
                select(EmailLog)
                .where(EmailLog.user_id == user.id)
                .order_by(EmailLog.created_at.asc())
            )
        ).all()
    )
    assert len(logs) == 1
    assert logs[0].source_provider == "google"
    assert logs[0].source_message_id == "gmail-message-1"
    assert logs[0].source_thread_id == "gmail-thread-1"
    assert logs[0].matched_application_id == application.id


@pytest.mark.asyncio
async def test_process_inbound_message_requires_review_below_transition_threshold(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, "email-gmail-review@example.com")
    await _create_applied_application(
        db_session,
        user_id=user.id,
        company_name="Acme Corp",
    )
    service = EmailService(db_session)
    message = InboundEmailMessage(
        sender="recruiting@acme-corp.com",
        from_address="recruiting@acme-corp.com",
        to_address="owner@jobradar.dev",
        subject="Interview Invitation",
        text="We would like to schedule an interview with you.",
        html="",
        source_provider="google",
        source_message_id="gmail-message-2",
    )

    result = await service.process_inbound_message(
        message,
        user.id,
        auto_transition_min_confidence=0.85,
    )

    assert result.status == "review_required"
    notification = await db_session.scalar(
        select(Notification).where(Notification.user_id == user.id)
    )
    assert notification is not None
    assert notification.notification_type == "email_review"
    assert notification.link == "/email"
