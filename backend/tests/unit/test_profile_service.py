from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.profile.schemas import ProfileUpdate
from app.profile.service import ProfileService


async def _create_user(
    db_session: AsyncSession,
    email: str = "profile-unit@example.com",
) -> User:
    user = User(email=email, password_hash="hashed-password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_profile_creates_default_profile(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    service = ProfileService(db_session)

    profile = await service.get_profile(user.id)

    assert profile.user_id == user.id
    assert profile.theme == "dark"
    assert profile.answer_bank == {}


@pytest.mark.asyncio
async def test_generate_answers_returns_current_answer_bank(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, "profile-answers@example.com")
    service = ProfileService(db_session)
    profile = await service.get_profile(user.id)
    profile.answer_bank = {"why_company": "Because it fits."}
    await db_session.commit()

    result = await service.generate_answers(user.id)

    assert result["status"] == "pending"
    assert result["current_answers"] == {"why_company": "Because it fits."}


@pytest.mark.asyncio
async def test_update_profile_sets_fields_and_refreshes_timestamp(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, "profile-update@example.com")
    service = ProfileService(db_session)
    original = await service.get_profile(user.id)
    before_update = original.updated_at

    updated = await service.update_profile(
        ProfileUpdate(
            full_name="Test User",
            location="Chicago, IL",
            preferred_job_types=["full-time"],
            available_start=datetime(2026, 4, 1, tzinfo=UTC),
        ),
        user.id,
    )

    assert updated.full_name == "Test User"
    assert updated.location == "Chicago, IL"
    assert updated.preferred_job_types == ["full-time"]
    assert updated.available_start is not None
    assert updated.available_start.date() == datetime(2026, 4, 1, tzinfo=UTC).date()
    assert updated.updated_at is not None
    assert before_update is None or updated.updated_at >= before_update
