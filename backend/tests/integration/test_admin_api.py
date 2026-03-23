from __future__ import annotations

import json
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job
from app.pipeline.models import Application


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"admin-api-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    token = login_resp.json()["access_token"]
    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me_resp.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_health_is_public(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_admin_diagnostics_and_reindex_require_auth(client: AsyncClient) -> None:
    diagnostics = await client.get("/api/v1/admin/diagnostics")
    reindex = await client.post("/api/v1/admin/reindex")

    assert diagnostics.status_code == 401
    assert reindex.status_code == 401


@pytest.mark.asyncio
async def test_admin_export_and_reindex_only_include_current_user(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token, user_id = await _register_and_login(client)
    db_session.add(
        Job(
            id="admin-api-job",
            user_id=uuid.UUID(user_id),
            source="manual",
            title="Ops",
        )
    )
    db_session.add(
        Application(
            user_id=uuid.UUID(user_id),
            job_id="admin-api-job",
            company_name="OpsCo",
            position_title="Ops",
            source="manual",
        )
    )
    await db_session.commit()

    diagnostics = await client.get("/api/v1/admin/diagnostics", headers=_auth(token))
    reindex = await client.post("/api/v1/admin/reindex", headers=_auth(token))
    export_response = await client.post("/api/v1/admin/export", headers=_auth(token))

    assert diagnostics.status_code == 200
    assert diagnostics.json()["job_count"] >= 1
    assert reindex.status_code == 200
    assert reindex.json()["jobs_reindexed"] == 1
    payload = json.loads(export_response.text)
    assert [job["id"] for job in payload["jobs"]] == ["admin-api-job"]
    assert [app["company_name"] for app in payload["applications"]] == ["OpsCo"]
