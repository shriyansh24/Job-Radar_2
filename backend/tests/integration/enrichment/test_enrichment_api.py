from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.jobs.models import Job


async def _register_and_login(client: AsyncClient) -> tuple[uuid.UUID, str]:
    email = f"enrichment-api-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    token = login_response.json()["access_token"]
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    return uuid.UUID(me_response.json()["id"]), token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_enrich_job_runs_against_owned_job(
    client: AsyncClient,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, token = await _register_and_login(client)
    job = Job(
        id="enrichment-job-001",
        user_id=user_id,
        source="manual",
        title="Backend Engineer",
        company_name="Acme",
        description_raw="<p>Build APIs.</p>",
        status="new",
    )
    db_session.add(job)
    await db_session.commit()

    async def _fake_enrich(self, enriched_job: Job) -> Job:
        enriched_job.is_enriched = True
        enriched_job.enriched_at = datetime(2026, 3, 27, tzinfo=UTC)
        return enriched_job

    monkeypatch.setattr(
        "app.enrichment.router.EnrichmentService.enrich_job",
        _fake_enrich,
    )
    monkeypatch.setattr(
        "app.enrichment.router.LLMClient.close",
        AsyncMock(return_value=None),
    )

    response = await client.post(
        f"/api/v1/enrichment/enrich/{job.id}",
        headers=_auth(token),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "job_id": job.id,
        "is_enriched": True,
        "enriched_at": "2026-03-27T00:00:00",
    }


@pytest.mark.asyncio
async def test_enrich_job_rejects_missing_job(
    client: AsyncClient,
) -> None:
    _, token = await _register_and_login(client)

    response = await client.post(
        "/api/v1/enrichment/enrich/missing-job",
        headers=_auth(token),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Job missing-job not found"}


@pytest.mark.asyncio
async def test_batch_enrich_enqueues_runtime_job_with_request_correlation(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, token = await _register_and_login(client)
    fake_dispatch = SimpleNamespace(
        job_name="enrichment_batch",
        queue_name="arq:queue:analysis",
        enqueued_job_id="req-correlation-123",
        queue_depth_after=4,
        queue_pressure_after="nominal",
        queue_alert_after="clear",
    )
    mocked_enqueue = AsyncMock(return_value=fake_dispatch)
    monkeypatch.setattr("app.enrichment.router.enqueue_registered_job", mocked_enqueue)

    response = await client.post(
        "/api/v1/enrichment/batch",
        headers={**_auth(token), "X-Request-ID": "req-correlation-123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "queued",
        "job_name": "enrichment_batch",
        "queue_name": "arq:queue:analysis",
        "enqueued_job_id": "req-correlation-123",
        "request_id": "req-correlation-123",
        "queue_depth_after": 4,
        "queue_pressure_after": "nominal",
        "queue_alert_after": "clear",
    }
    mocked_enqueue.assert_awaited_once_with(
        "enrichment_batch",
        correlation_id="req-correlation-123",
    )
