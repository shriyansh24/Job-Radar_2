from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job


async def _register_and_login(
    client: AsyncClient,
    *,
    email_prefix: str,
) -> tuple[uuid.UUID, str]:
    client.cookies.clear()
    email = f"{email_prefix}-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    token = login_response.cookies["jr_access_token"]
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    return uuid.UUID(me_response.json()["id"]), token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _job(job_id: str, *, user_id: uuid.UUID, title: str, company_name: str) -> Job:
    return Job(
        id=job_id,
        user_id=user_id,
        source="manual",
        title=title,
        company_name=company_name,
        status="new",
    )


@pytest.mark.asyncio
async def test_dedup_feedback_rejects_jobs_outside_current_workspace(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user_id, token = await _register_and_login(client, email_prefix="dedup-owner")
    other_user_id, _ = await _register_and_login(client, email_prefix="dedup-other")
    db_session.add_all(
        [
            _job(
                "dedup-owned-a",
                user_id=user_id,
                title="Backend Engineer",
                company_name="Acme",
            ),
            _job(
                "dedup-foreign-b",
                user_id=other_user_id,
                title="Backend Developer",
                company_name="Acme",
            ),
        ]
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/scraper/dedup/feedback",
        headers=_auth(token),
        json={
            "job_a_id": "dedup-owned-a",
            "job_b_id": "dedup-foreign-b",
            "decision": "same",
        },
    )

    assert response.status_code == 404
    assert "current workspace" in response.json()["detail"]


@pytest.mark.asyncio
async def test_dedup_accuracy_is_scoped_to_current_user(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    primary_user_id, primary_token = await _register_and_login(
        client,
        email_prefix="dedup-primary",
    )
    secondary_user_id, secondary_token = await _register_and_login(
        client,
        email_prefix="dedup-secondary",
    )
    db_session.add_all(
        [
            _job(
                "dedup-primary-a",
                user_id=primary_user_id,
                title="Backend Engineer",
                company_name="Acme",
            ),
            _job(
                "dedup-primary-b",
                user_id=primary_user_id,
                title="Backend Developer",
                company_name="Acme Corp",
            ),
            _job(
                "dedup-secondary-a",
                user_id=secondary_user_id,
                title="Data Analyst",
                company_name="Globex",
            ),
            _job(
                "dedup-secondary-b",
                user_id=secondary_user_id,
                title="Data Scientist",
                company_name="Globex Corp",
            ),
        ]
    )
    await db_session.commit()

    primary_feedback = await client.post(
        "/api/v1/scraper/dedup/feedback",
        headers=_auth(primary_token),
        json={
            "job_a_id": "dedup-primary-a",
            "job_b_id": "dedup-primary-b",
            "decision": "same",
        },
    )
    secondary_feedback = await client.post(
        "/api/v1/scraper/dedup/feedback",
        headers=_auth(secondary_token),
        json={
            "job_a_id": "dedup-secondary-a",
            "job_b_id": "dedup-secondary-b",
            "decision": "different",
        },
    )
    assert primary_feedback.status_code == 201
    assert secondary_feedback.status_code == 201

    primary_accuracy = await client.get(
        "/api/v1/scraper/dedup/accuracy",
        headers=_auth(primary_token),
    )
    secondary_accuracy = await client.get(
        "/api/v1/scraper/dedup/accuracy",
        headers=_auth(secondary_token),
    )

    assert primary_accuracy.status_code == 200
    assert primary_accuracy.json()["total_feedback"] == 1
    assert primary_accuracy.json()["confirmed_duplicates"] == 1
    assert primary_accuracy.json()["confirmed_different"] == 0
    assert secondary_accuracy.status_code == 200
    assert secondary_accuracy.json()["total_feedback"] == 1
    assert secondary_accuracy.json()["confirmed_duplicates"] == 0
    assert secondary_accuracy.json()["confirmed_different"] == 1


@pytest.mark.asyncio
async def test_dedup_review_only_returns_pairs_from_current_workspace(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user_id, token = await _register_and_login(client, email_prefix="dedup-review")
    other_user_id, _ = await _register_and_login(client, email_prefix="dedup-review-other")
    db_session.add_all(
        [
            _job(
                "dedup-review-a",
                user_id=user_id,
                title="Product Designer",
                company_name="Acme",
            ),
            _job(
                "dedup-review-b",
                user_id=user_id,
                title="Product Design Engineer",
                company_name="Acme Labs",
            ),
            _job(
                "dedup-review-other-a",
                user_id=other_user_id,
                title="Data Engineer",
                company_name="Globex",
            ),
            _job(
                "dedup-review-other-b",
                user_id=other_user_id,
                title="Data Platform Engineer",
                company_name="Globex Labs",
            ),
        ]
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/scraper/dedup/review?limit=10",
        headers=_auth(token),
    )

    assert response.status_code == 200
    job_ids = {
        job_id
        for item in response.json()
        for job_id in (item["job_a_id"], item["job_b_id"])
    }
    assert "dedup-review-a" in job_ids
    assert "dedup-review-b" in job_ids
    assert "dedup-review-other-a" not in job_ids
    assert "dedup-review-other-b" not in job_ids
