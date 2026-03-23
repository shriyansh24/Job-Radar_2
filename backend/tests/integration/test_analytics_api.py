from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

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
