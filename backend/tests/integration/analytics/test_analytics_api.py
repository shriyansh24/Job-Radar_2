from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job
from app.pipeline.models import Application


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"analytics-api-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    token = login.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_analytics_overview_daily_and_funnel(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token, user_id = await _register_and_login(client)
    now = datetime.now(UTC)
    db_session.add_all(
        [
            Job(
                id="analytics-api-job-1",
                user_id=uuid.UUID(user_id),
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
                id="analytics-api-job-2",
                user_id=uuid.UUID(user_id),
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
                user_id=uuid.UUID(user_id),
                job_id="analytics-api-job-1",
                company_name="DataCo",
                position_title="Backend Engineer",
                source="greenhouse",
                status="applied",
                created_at=now,
            ),
            Application(
                user_id=uuid.UUID(user_id),
                job_id="analytics-api-job-2",
                company_name="DataCo",
                position_title="Platform Engineer",
                source="lever",
                status="screening",
                created_at=now - timedelta(days=1),
            ),
        ]
    )
    await db_session.commit()

    overview = await client.get("/api/v1/analytics/overview", headers=_auth(token))
    daily = await client.get("/api/v1/analytics/daily?days=2", headers=_auth(token))
    funnel = await client.get("/api/v1/analytics/funnel", headers=_auth(token))

    assert overview.status_code == 200
    assert overview.json()["total_jobs"] == 2
    assert overview.json()["total_applications"] == 2
    assert overview.json()["response_rate"] == 0.5
    assert daily.status_code == 200
    assert len(daily.json()) == 2
    assert funnel.status_code == 200
    funnel_counts = {item["stage"]: item["count"] for item in funnel.json()}
    assert funnel_counts["Applied"] == 1
    assert funnel_counts["Screening"] == 1


@pytest.mark.asyncio
async def test_analytics_patterns_returns_pattern_contract(
    client: AsyncClient,
) -> None:
    token, user_id = await _register_and_login(client)
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
        response = await client.get("/api/v1/analytics/patterns", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == payload
    mocked_get_all_patterns.assert_awaited_once_with(uuid.UUID(user_id))
