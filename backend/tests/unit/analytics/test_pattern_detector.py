from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.pattern_detector import PatternDetector
from app.auth.models import User
from app.jobs.models import Job
from app.pipeline.models import Application
from app.profile.models import UserProfile


async def _create_user(
    db_session: AsyncSession,
    email: str = "pattern-detector@example.com",
) -> User:
    user = User(email=email, password_hash="hashed-password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_pattern_detector_returns_operator_patterns(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    db_session.add(
        UserProfile(
            user_id=user.id,
            resume_text="React TypeScript systems engineer",
        )
    )
    db_session.add_all(
        [
            Job(
                id="pattern-job-1",
                user_id=user.id,
                source="greenhouse",
                title="Frontend Engineer",
                company_name="Acme",
                is_active=True,
                skills_required=["React", "TypeScript", "GraphQL"],
            ),
            Job(
                id="pattern-job-2",
                user_id=user.id,
                source="lever",
                title="Platform Engineer",
                company_name="Acme",
                is_active=True,
                skills_required=["React", "TypeScript", "GraphQL"],
            ),
            Job(
                id="pattern-job-3",
                user_id=user.id,
                source="workday",
                title="Product Engineer",
                company_name="Acme",
                is_active=True,
                skills_required=["React", "GraphQL"],
            ),
            Application(
                user_id=user.id,
                job_id="pattern-job-1",
                company_name="Acme",
                position_title="Frontend Engineer",
                source="greenhouse",
                status="applied",
                applied_at=now - timedelta(days=3),
                created_at=now - timedelta(days=3),
            ),
            Application(
                user_id=user.id,
                job_id="pattern-job-2",
                company_name="Acme",
                position_title="Platform Engineer",
                source="lever",
                status="screening",
                applied_at=now - timedelta(days=2),
                created_at=now - timedelta(days=2),
            ),
            Application(
                user_id=user.id,
                job_id="pattern-job-3",
                company_name="Acme",
                position_title="Product Engineer",
                source="workday",
                status="applied",
                applied_at=now - timedelta(days=20),
                created_at=now - timedelta(days=20),
            ),
        ]
    )
    await db_session.commit()

    detector = PatternDetector(db_session)
    patterns = await detector.get_all_patterns(user.id)

    assert patterns["conversion_funnel"][1] == {"stage": "applied", "count": 2}
    assert patterns["callback_rate_by_company_size"][0]["size_bucket"] == "small"
    assert patterns["company_ghosting_rate"][0]["company"] == "Acme"
    assert patterns["skill_gap_detection"][0]["skill"] == "GraphQL"
