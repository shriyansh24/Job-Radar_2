from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    """Register user, login, return (token, user_id)."""
    email = f"pipeline-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    token = login_resp.json()["access_token"]
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    return token, me_resp.json()["id"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_applications_require_auth(client: AsyncClient):
    resp = await client.get("/api/v1/applications")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_and_list_application(
    client: AsyncClient, db_session: AsyncSession
):
    token, user_id = await _register_and_login(client)

    # Create a job first
    job = Job(
        id="pipeline-api-job",
        user_id=uuid.UUID(user_id),
        source="test",
        title="Pipeline Test",
        company_name="PipelineCo",
    )
    db_session.add(job)
    await db_session.commit()

    # Create application
    resp = await client.post(
        "/api/v1/applications",
        headers=_auth(token),
        json={
            "job_id": "pipeline-api-job",
            "company_name": "PipelineCo",
            "position_title": "Pipeline Test",
            "source": "manual",
        },
    )
    assert resp.status_code == 201
    app_data = resp.json()
    assert app_data["status"] == "saved"
    app_id = app_data["id"]

    # List applications
    resp = await client.get("/api/v1/applications", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_transition_and_history(
    client: AsyncClient, db_session: AsyncSession
):
    token, user_id = await _register_and_login(client)

    job = Job(
        id="transition-test-job",
        user_id=uuid.UUID(user_id),
        source="test",
        title="Transition Test",
        company_name="TransCo",
    )
    db_session.add(job)
    await db_session.commit()

    # Create application
    resp = await client.post(
        "/api/v1/applications",
        headers=_auth(token),
        json={
            "job_id": "transition-test-job",
            "company_name": "TransCo",
            "position_title": "Transition Test",
            "source": "manual",
        },
    )
    app_id = resp.json()["id"]

    # Transition: saved -> applied
    resp = await client.post(
        f"/api/v1/applications/{app_id}/transition",
        headers=_auth(token),
        json={"new_status": "applied", "change_source": "user"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "applied"

    # Transition: applied -> screening
    resp = await client.post(
        f"/api/v1/applications/{app_id}/transition",
        headers=_auth(token),
        json={"new_status": "screening", "change_source": "system"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "screening"

    # Get history
    resp = await client.get(
        f"/api/v1/applications/{app_id}/history",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 3  # saved, applied, screening


@pytest.mark.asyncio
async def test_invalid_transition_returns_422(
    client: AsyncClient, db_session: AsyncSession
):
    token, user_id = await _register_and_login(client)

    job = Job(
        id="invalid-trans-job",
        user_id=uuid.UUID(user_id),
        source="test",
        title="Invalid Test",
        company_name="InvalidCo",
    )
    db_session.add(job)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/applications",
        headers=_auth(token),
        json={
            "job_id": "invalid-trans-job",
            "company_name": "InvalidCo",
            "position_title": "Invalid Test",
            "source": "manual",
        },
    )
    app_id = resp.json()["id"]

    # saved -> offer is invalid
    resp = await client.post(
        f"/api/v1/applications/{app_id}/transition",
        headers=_auth(token),
        json={"new_status": "offer", "change_source": "user"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_pipeline_view(
    client: AsyncClient, db_session: AsyncSession
):
    token, user_id = await _register_and_login(client)

    job = Job(
        id="pipeline-view-job",
        user_id=uuid.UUID(user_id),
        source="test",
        title="View Test",
        company_name="ViewCo",
    )
    db_session.add(job)
    await db_session.commit()

    # Create application
    await client.post(
        "/api/v1/applications",
        headers=_auth(token),
        json={
            "job_id": "pipeline-view-job",
            "company_name": "ViewCo",
            "position_title": "View Test",
            "source": "manual",
        },
    )

    # Get pipeline view
    resp = await client.get("/api/v1/applications/pipeline", headers=_auth(token))
    assert resp.status_code == 200
    view = resp.json()
    assert len(view["saved"]) == 1
    assert len(view["applied"]) == 0
