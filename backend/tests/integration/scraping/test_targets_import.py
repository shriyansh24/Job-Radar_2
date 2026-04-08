from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.scraping.models import ScrapeTarget


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


@pytest.mark.asyncio
async def test_import_targets_bulk_success(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user_id, token = await _register_and_login(client, email_prefix="targets-import-bulk")

    items = [
        {"url": "https://boards.greenhouse.io/acme", "company_name": "Acme"},
        {"url": "https://jobs.lever.co/globex", "company_name": "Globex"},
        {"url": "https://example.com/careers", "company_name": "Generic"},
    ]

    response = await client.post(
        "/api/v1/scraper/targets/import",
        headers=_auth(token),
        json=items,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["imported"] == 3
    assert data["skipped"] == 0
    assert data["errors"] == []

    # Verify they exist in DB
    result = await db_session.scalars(
        select(ScrapeTarget).where(ScrapeTarget.user_id == user_id)
    )
    targets = result.all()
    assert len(targets) == 3
    urls = {t.url for t in targets}
    assert "https://boards.greenhouse.io/acme" in urls
    assert "https://jobs.lever.co/globex" in urls
    assert "https://example.com/careers" in urls


@pytest.mark.asyncio
async def test_import_targets_with_skips_and_errors(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user_id, token = await _register_and_login(client, email_prefix="targets-import-mixed")

    # Add one existing target
    db_session.add(
        ScrapeTarget(
            user_id=user_id,
            url="https://existing.com",
            company_name="Existing",
            source_kind="career_page",
            priority_class="cool",
            schedule_interval_m=720,
        )
    )
    await db_session.commit()

    items = [
        {"url": "https://existing.com", "company_name": "Existing"},  # Should be skipped
        {"url": "not-a-url", "company_name": "Invalid"},              # Should be error
        {"url": "https://new.com", "company_name": "New"},            # Should be imported
    ]

    response = await client.post(
        "/api/v1/scraper/targets/import",
        headers=_auth(token),
        json=items,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["imported"] == 1
    assert data["skipped"] == 1
    assert len(data["errors"]) == 1
    assert "Invalid URL" in data["errors"][0]

    # Verify only the new one was added (total 2)
    result = await db_session.scalars(
        select(ScrapeTarget).where(ScrapeTarget.user_id == user_id)
    )
    targets = result.all()
    assert len(targets) == 2
