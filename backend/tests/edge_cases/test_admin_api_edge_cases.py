from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_db
from tests.conftest import test_session_factory as session_factory


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
async def test_concurrent_health_requests_succeed_with_unique_request_ids(
    isolated_client: AsyncClient,
) -> None:
    responses = await asyncio.gather(
        *[isolated_client.get("/api/v1/admin/health") for _ in range(8)]
    )

    assert all(response.status_code == 200 for response in responses)
    request_ids = [response.headers["X-Request-ID"] for response in responses]
    assert len(set(request_ids)) == len(request_ids)
