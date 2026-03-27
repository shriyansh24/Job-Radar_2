from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.jobs.models import Job
from tests.edge_cases._api_helpers import auth_headers, register_and_login


@pytest.mark.asyncio
async def test_jobs_list_preserves_unicode_fields(
    client: AsyncClient,
    db_session,
) -> None:
    _, tokens = await register_and_login(client)
    me_response = await client.get("/api/v1/auth/me", headers=auth_headers(tokens["access_token"]))
    user_id = uuid.UUID(me_response.json()["id"])

    job = Job(
        id="unicode-job-001",
        user_id=user_id,
        source="test",
        title="Senior D\u00e9veloppeur \U0001f680",
        company_name="\u6771\u4eac\u30c7\u30fc\u30bf",
        location="M\u00fcnchen, DE",
    )
    db_session.add(job)
    await db_session.commit()

    response = await client.get("/api/v1/jobs", headers=auth_headers(tokens["access_token"]))

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["title"] == "Senior D\u00e9veloppeur \U0001f680"
    assert item["company_name"] == "\u6771\u4eac\u30c7\u30fc\u30bf"
    assert item["location"] == "M\u00fcnchen, DE"


@pytest.mark.asyncio
async def test_traversal_like_job_id_is_treated_as_opaque_identifier(
    client: AsyncClient,
) -> None:
    _, tokens = await register_and_login(client)

    response = await client.get(
        "/api/v1/jobs/%2E%2E",
        headers=auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job .. not found"
