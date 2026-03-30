from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.service import AnalyticsService
from app.auth.models import User
from app.jobs.models import Job
from app.pipeline.models import Application


async def _create_user(
    db_session: AsyncSession,
    email: str = "analytics-unit@example.com",
) -> User:
    user = User(email=email, password_hash="hashed-password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_overview_returns_empty_defaults(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    service = AnalyticsService(db_session)

    overview = await service.get_overview(user.id)

    assert overview.total_jobs == 0
    assert overview.total_applications == 0
    assert overview.response_rate == 0.0
    assert overview.applications_by_status == {}


@pytest.mark.asyncio
async def test_analytics_service_aggregates_jobs_and_applications(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, "analytics-data@example.com")
    now = datetime.now(UTC)
    db_session.add_all(
        [
            Job(
                id="analytics-job-1",
                user_id=user.id,
                source="greenhouse",
                title="Backend Engineer",
                company_name="DataCo",
                scraped_at=now,
                is_active=True,
                is_enriched=True,
                match_score=Decimal("0.8"),
                skills_required=["Python", "SQL"],
            ),
            Job(
                id="analytics-job-2",
                user_id=user.id,
                source="lever",
                title="Platform Engineer",
                company_name="DataCo",
                scraped_at=now - timedelta(days=1),
                is_active=True,
                match_score=Decimal("0.6"),
                skills_required=["Python"],
            ),
        ]
    )
    db_session.add_all(
        [
            Application(
                user_id=user.id,
                job_id="analytics-job-1",
                company_name="DataCo",
                position_title="Backend Engineer",
                source="greenhouse",
                status="applied",
                created_at=now,
            ),
            Application(
                user_id=user.id,
                job_id="analytics-job-2",
                company_name="DataCo",
                position_title="Platform Engineer",
                source="lever",
                status="screening",
                created_at=now - timedelta(days=1),
            ),
        ]
    )
    await db_session.commit()

    service = AnalyticsService(db_session)

    overview = await service.get_overview(user.id)
    daily = await service.get_daily_stats(user.id, days=2)
    sources = await service.get_source_stats(user.id)
    skills = await service.get_skills_stats(user.id)
    funnel = await service.get_funnel(user.id)

    assert overview.total_jobs == 2
    assert overview.total_applications == 2
    assert overview.total_interviews == 1
    assert overview.jobs_scraped_today == 1
    assert overview.enriched_jobs == 1
    assert overview.response_rate == 0.5
    assert len(daily) == 2
    assert {source.source for source in sources} == {"greenhouse", "lever"}
    assert skills[0].skill == "Python"
    assert skills[0].count == 2
    assert {item.stage: item.count for item in funnel}["Screening"] == 1


@pytest.mark.asyncio
async def test_analytics_service_get_patterns_delegates_to_detector(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, "analytics-patterns@example.com")
    payload = {
        "callback_rate_by_company_size": [
            {
                "size_bucket": "small",
                "total_applications": 3,
                "callbacks": 2,
                "callback_rate": 66.7,
            }
        ],
        "conversion_funnel": [{"stage": "applied", "count": 3}],
        "response_time_patterns": [
            {
                "avg_days_to_response": 2.5,
                "sample_size": 3,
                "warning": None,
            }
        ],
        "best_application_timing": [
            {
                "day_of_week": "Tuesday",
                "total_applications": 3,
                "callbacks": 2,
                "callback_rate": 66.7,
            }
        ],
        "company_ghosting_rate": [
            {
                "company": "Acme",
                "total_applications": 3,
                "ghosted": 1,
                "ghosting_rate": 33.3,
            }
        ],
        "skill_gap_detection": [{"skill": "GraphQL", "demand_count": 4}],
    }

    with patch(
        "app.analytics.service.PatternDetector.get_all_patterns",
        new=AsyncMock(return_value=payload),
    ) as mocked_get_all_patterns:
        service = AnalyticsService(db_session)
        patterns = await service.get_patterns(user.id)

    mocked_get_all_patterns.assert_awaited_once_with(user.id)
    assert patterns.callback_rate_by_company_size[0].size_bucket == "small"
    assert patterns.response_time_patterns[0].avg_days_to_response == 2.5
    assert patterns.skill_gap_detection[0].skill == "GraphQL"
