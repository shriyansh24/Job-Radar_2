from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.scraping.models import ScrapeAttempt, ScrapeTarget


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
async def test_create_career_page_normalizes_url_and_applies_import_classification(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user_id, token = await _register_and_login(client, email_prefix="career-page-create")

    response = await client.post(
        "/api/v1/scraper/career-pages",
        headers=_auth(token),
        json={
            "url": " https://boards.greenhouse.io/acme/jobs/12345 ",
            "company_name": "Acme",
        },
    )

    assert response.status_code == 201
    assert response.json()["url"] == "https://boards.greenhouse.io/acme/jobs/12345"

    target = await db_session.scalar(
        select(ScrapeTarget).where(
            ScrapeTarget.user_id == user_id,
            ScrapeTarget.url == "https://boards.greenhouse.io/acme/jobs/12345",
        )
    )
    assert target is not None
    assert target.company_name == "Acme"
    assert target.source_kind == "ats_board"
    assert target.ats_vendor == "greenhouse"
    assert target.ats_board_token == "acme"
    assert target.start_tier == 0
    assert target.priority_class == "cool"
    assert target.schedule_interval_m == 720
    assert target.next_scheduled_at is not None


@pytest.mark.asyncio
async def test_update_career_page_reclassifies_url_changes(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user_id, token = await _register_and_login(client, email_prefix="career-page-update")
    created = await client.post(
        "/api/v1/scraper/career-pages",
        headers=_auth(token),
        json={
            "url": "https://jobs.example.com/careers",
            "company_name": "ExampleCo",
        },
    )
    page_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/scraper/career-pages/{page_id}",
        headers=_auth(token),
        json={
            "url": " https://jobs.lever.co/exampleco/platform ",
            "company_name": "ExampleCo",
        },
    )

    assert response.status_code == 200
    assert response.json()["url"] == "https://jobs.lever.co/exampleco/platform"

    target = await db_session.scalar(
        select(ScrapeTarget).where(
            ScrapeTarget.user_id == user_id,
            ScrapeTarget.id == uuid.UUID(page_id),
        )
    )
    assert target is not None
    assert target.source_kind == "ats_board"
    assert target.ats_vendor == "lever"
    assert target.ats_board_token == "exampleco"
    assert target.start_tier == 0


@pytest.mark.asyncio
async def test_create_career_page_rejects_non_http_urls(client: AsyncClient) -> None:
    _, token = await _register_and_login(client, email_prefix="career-page-invalid")

    response = await client.post(
        "/api/v1/scraper/career-pages",
        headers=_auth(token),
        json={
            "url": "javascript:alert(1)",
            "company_name": "Acme",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_career_page_rejects_duplicate_normalized_urls(
    client: AsyncClient,
) -> None:
    _, token = await _register_and_login(client, email_prefix="career-page-duplicate")

    first = await client.post(
        "/api/v1/scraper/career-pages",
        headers=_auth(token),
        json={
            "url": "https://careers.acme.example",
            "company_name": "Acme",
        },
    )
    second = await client.post(
        "/api/v1/scraper/career-pages",
        headers=_auth(token),
        json={
            "url": "https://careers.acme.example/",
            "company_name": "Acme",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 422
    assert second.json() == {"detail": "Career page target already exists for this URL."}


@pytest.mark.asyncio
async def test_delete_career_page_rejects_targets_with_scrape_history(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user_id, token = await _register_and_login(client, email_prefix="career-page-delete-guard")
    created = await client.post(
        "/api/v1/scraper/career-pages",
        headers=_auth(token),
        json={
            "url": "https://careers.acme.example/delete-me",
            "company_name": "Acme",
        },
    )
    target_id = uuid.UUID(created.json()["id"])

    db_session.add(
        ScrapeAttempt(
            run_id=None,
            target_id=target_id,
            selected_tier=1,
            actual_tier_used=1,
            scraper_name="test-scraper",
            status="success",
        )
    )
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/scraper/career-pages/{target_id}",
        headers=_auth(token),
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Career page targets with scrape history cannot be deleted. "
        "Disable or release the target instead."
    }
    target = await db_session.scalar(
        select(ScrapeTarget).where(
            ScrapeTarget.user_id == user_id,
            ScrapeTarget.id == target_id,
        )
    )
    assert target is not None
