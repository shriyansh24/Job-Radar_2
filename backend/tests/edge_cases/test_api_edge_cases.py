from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_db
from app.jobs.models import Job
from tests.conftest import test_session_factory as session_factory


async def _register_and_login(
    client: AsyncClient,
    *,
    email: str | None = None,
    display_name: str | None = None,
) -> tuple[str, dict[str, str]]:
    email = email or f"edge-{uuid.uuid4().hex[:12]}@example.com"
    payload: dict[str, str] = {
        "email": email,
        "password": "securepassword123",
    }
    if display_name is not None:
        payload["display_name"] = display_name

    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepassword123"},
    )
    assert login_response.status_code == 200
    return email, login_response.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def isolated_client() -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unicode_display_name_roundtrip(client: AsyncClient) -> None:
    display_name = "Renée 🚀 東京"
    _, tokens = await _register_and_login(client, display_name=display_name)

    response = await client.get("/api/v1/auth/me", headers=_auth(tokens["access_token"]))

    assert response.status_code == 200
    assert response.json()["display_name"] == display_name


@pytest.mark.asyncio
async def test_jobs_list_preserves_unicode_fields(
    client: AsyncClient,
    db_session,
) -> None:
    _, tokens = await _register_and_login(client)
    me_response = await client.get("/api/v1/auth/me", headers=_auth(tokens["access_token"]))
    user_id = uuid.UUID(me_response.json()["id"])

    job = Job(
        id="unicode-job-001",
        user_id=user_id,
        source="test",
        title="Senior Développeur 🚀",
        company_name="東京データ",
        location="München, DE",
    )
    db_session.add(job)
    await db_session.commit()

    response = await client.get("/api/v1/jobs", headers=_auth(tokens["access_token"]))

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["title"] == "Senior Développeur 🚀"
    assert item["company_name"] == "東京データ"
    assert item["location"] == "München, DE"


@pytest.mark.asyncio
async def test_empty_vault_lists_return_empty_arrays(client: AsyncClient) -> None:
    _, tokens = await _register_and_login(client)
    headers = _auth(tokens["access_token"])

    resumes = await client.get("/api/v1/vault/resumes", headers=headers)
    cover_letters = await client.get("/api/v1/vault/cover-letters", headers=headers)

    assert resumes.status_code == 200
    assert resumes.json() == []
    assert cover_letters.status_code == 200
    assert cover_letters.json() == []


@pytest.mark.asyncio
async def test_duplicate_registration_returns_validation_error(client: AsyncClient) -> None:
    email = f"dupe-{uuid.uuid4().hex[:12]}@example.com"
    payload = {"email": email, "password": "securepassword123"}

    first = await client.post("/api/v1/auth/register", json=payload)
    second = await client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 422
    assert second.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_traversal_like_job_id_is_treated_as_opaque_identifier(
    client: AsyncClient,
) -> None:
    _, tokens = await _register_and_login(client)

    response = await client.get("/api/v1/jobs/%2E%2E", headers=_auth(tokens["access_token"]))

    assert response.status_code == 404
    assert response.json()["detail"] == "Job .. not found"


@pytest.mark.asyncio
async def test_concurrent_health_requests_succeed_with_unique_request_ids(
    isolated_client: AsyncClient,
) -> None:
    responses = await asyncio.gather(
        *[isolated_client.get("/api/v1/admin/health") for _ in range(8)]
    )

    assert all(response.status_code == 200 for response in responses)
    request_ids = [response.headers["X-Request-ID"] for response in responses]
    assert len(set(request_ids)) == len(request_ids)
