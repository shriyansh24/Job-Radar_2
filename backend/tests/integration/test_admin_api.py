from __future__ import annotations

import json
import uuid
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_operator_user
from app.jobs.models import Job
from app.pipeline.models import Application


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    client.cookies.clear()
    email = f"admin-api-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    token = login_resp.cookies["jr_access_token"]
    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me_resp.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _not_configured_integration(provider: str, *, auth_type: str = "api_key") -> dict[str, object]:
    return {
        "provider": provider,
        "auth_type": auth_type,
        "connected": False,
        "status": "not_configured",
        "masked_value": None,
        "account_email": None,
        "scopes": [],
        "updated_at": None,
        "last_validated_at": None,
        "last_synced_at": None,
        "last_error": None,
    }


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
async def test_admin_diagnostics_require_operator_access(client: AsyncClient) -> None:
    token, _ = await _register_and_login(client)

    diagnostics = await client.get("/api/v1/admin/diagnostics", headers=_auth(token))

    assert diagnostics.status_code == 403
    assert diagnostics.json() == {"detail": "Operator access required"}


@pytest.mark.asyncio
async def test_admin_operator_can_view_diagnostics(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from app.main import app

    token, user_id = await _register_and_login(client)
    db_session.add(
        Job(
            id="admin-diagnostics-job",
            user_id=uuid.UUID(user_id),
            source="manual",
            title="Ops",
        )
    )
    await db_session.commit()
    app.dependency_overrides[get_current_operator_user] = lambda: SimpleNamespace(id=user_id)

    try:
        diagnostics = await client.get("/api/v1/admin/diagnostics", headers=_auth(token))
    finally:
        app.dependency_overrides.pop(get_current_operator_user, None)

    assert diagnostics.status_code == 200
    assert diagnostics.json()["job_count"] >= 1


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

    reindex = await client.post("/api/v1/admin/reindex", headers=_auth(token))
    export_response = await client.post("/api/v1/admin/export", headers=_auth(token))

    assert reindex.status_code == 200
    assert reindex.json()["jobs_reindexed"] == 1
    payload = json.loads(export_response.text)
    assert [job["id"] for job in payload["jobs"]] == ["admin-api-job"]
    assert [app["company_name"] for app in payload["applications"]] == ["OpsCo"]


@pytest.mark.asyncio
async def test_admin_clear_data_only_wipes_current_user_data(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token, user_id = await _register_and_login(client)
    other_token, other_user_id = await _register_and_login(client)

    await client.post(
        "/api/v1/settings/searches",
        headers=_auth(token),
        json={"name": "Remote Roles", "filters": {"remote": True}, "alert_enabled": True},
    )
    await client.put(
        "/api/v1/settings/integrations/openrouter",
        headers=_auth(token),
        json={"api_key": "sk-test-1234567890"},
    )

    db_session.add(
        Job(
            id="wipe-job-1",
            user_id=uuid.UUID(user_id),
            source="manual",
            title="To Wipe",
        )
    )
    db_session.add(
        Application(
            user_id=uuid.UUID(user_id),
            job_id="wipe-job-1",
            company_name="WipeCo",
            position_title="Engineer",
            source="manual",
        )
    )
    db_session.add(
        Job(
            id="keep-job-1",
            user_id=uuid.UUID(other_user_id),
            source="manual",
            title="To Keep",
        )
    )
    await db_session.commit()

    cleared = await client.delete("/api/v1/admin/data", headers=_auth(token))
    my_searches = await client.get("/api/v1/settings/searches", headers=_auth(token))
    my_integrations = await client.get("/api/v1/settings/integrations", headers=_auth(token))
    my_export = await client.post("/api/v1/admin/export", headers=_auth(token))
    my_profile = await client.get("/api/v1/auth/me", headers=_auth(token))
    other_export = await client.post("/api/v1/admin/export", headers=_auth(other_token))

    assert cleared.status_code == 200
    assert cleared.json()["status"] == "ok"
    assert cleared.json()["rows_deleted"] >= 1
    assert my_searches.json() == []
    assert my_integrations.json() == [
        _not_configured_integration("openrouter"),
        _not_configured_integration("serpapi"),
        _not_configured_integration("theirstack"),
        _not_configured_integration("apify"),
        _not_configured_integration("google", auth_type="oauth"),
    ]
    assert json.loads(my_export.text) == {"jobs": [], "applications": []}
    assert my_profile.status_code == 200
    assert [job["id"] for job in json.loads(other_export.text)["jobs"]] == ["keep-job-1"]
