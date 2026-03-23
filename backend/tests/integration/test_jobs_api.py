from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job


async def _register_and_login(client: AsyncClient) -> str:
    """Helper to register a user and return access token."""
    email = f"jobs-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_jobs_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/jobs")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_jobs_empty(client: AsyncClient):
    token = await _register_and_login(client)
    resp = await client.get("/api/v1/jobs", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_job_not_found(client: AsyncClient):
    token = await _register_and_login(client)
    resp = await client.get("/api/v1/jobs/nonexistent", headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_job_crud_cycle(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_login(client)

    # Get user ID from /me
    me_resp = await client.get("/api/v1/auth/me", headers=_auth(token))
    user_id = me_resp.json()["id"]

    # Create a job directly in DB (scraper would normally do this)
    job = Job(
        id="api-test-job-001",
        user_id=uuid.UUID(user_id),
        source="test",
        title="API Test Engineer",
        company_name="TestCo",
        status="new",
        freshness_score=0.7,
    )
    db_session.add(job)
    await db_session.commit()

    # List jobs
    resp = await client.get("/api/v1/jobs", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["title"] == "API Test Engineer"
    assert resp.json()["items"][0]["freshness_score"] == pytest.approx(0.7)

    # Get single job
    resp = await client.get("/api/v1/jobs/api-test-job-001", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["id"] == "api-test-job-001"
    assert resp.json()["freshness_score"] == pytest.approx(0.7)

    # Update job (star it)
    resp = await client.patch(
        "/api/v1/jobs/api-test-job-001",
        headers=_auth(token),
        json={"is_starred": True},
    )
    assert resp.status_code == 200
    assert resp.json()["is_starred"] is True

    # Delete job (soft delete)
    resp = await client.delete("/api/v1/jobs/api-test-job-001", headers=_auth(token))
    assert resp.status_code == 204

    # Verify job no longer appears in listing
    resp = await client.get("/api/v1/jobs", headers=_auth(token))
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_list_jobs_with_filters(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_login(client)
    me_resp = await client.get("/api/v1/auth/me", headers=_auth(token))
    user_id = uuid.UUID(me_resp.json()["id"])

    # Create jobs with different sources
    for i, source in enumerate(["linkedin", "indeed", "linkedin"]):
        job = Job(
            id=f"filter-test-{i}",
            user_id=user_id,
            source=source,
            title=f"Engineer {i}",
            company_name="FilterCo",
        )
        db_session.add(job)
    await db_session.commit()

    # Filter by source
    resp = await client.get("/api/v1/jobs?source=linkedin", headers=_auth(token))
    assert resp.json()["total"] == 2

    resp = await client.get("/api/v1/jobs?source=indeed", headers=_auth(token))
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_export_jobs_json(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_login(client)
    me_resp = await client.get("/api/v1/auth/me", headers=_auth(token))
    user_id = uuid.UUID(me_resp.json()["id"])

    job = Job(
        id="export-test-001",
        user_id=user_id,
        source="test",
        title="Export Test",
        company_name="ExportCo",
    )
    db_session.add(job)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/jobs/export",
        headers=_auth(token),
        json={"format": "json"},
    )
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
