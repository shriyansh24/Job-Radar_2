"""Test auto-apply REST API endpoints."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def auto_apply_app():
    from fastapi import FastAPI
    from backend.routers.auto_apply import router
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


class TestAutoApplyRouter:
    @pytest.mark.asyncio
    async def test_get_profile_empty(self, auto_apply_app, mock_db):
        from backend.database import get_db

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        auto_apply_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=auto_apply_app), base_url="http://test") as client:
            resp = await client.get("/api/auto-apply/profile")
            assert resp.status_code == 200

        auto_apply_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_save_profile(self, auto_apply_app, mock_db):
        from backend.database import get_db

        mock_profile = MagicMock()
        mock_profile.application_profile = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile
        mock_db.execute = AsyncMock(return_value=mock_result)
        auto_apply_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=auto_apply_app), base_url="http://test") as client:
            resp = await client.post(
                "/api/auto-apply/profile",
                json={"name": "John Doe", "email": "john@test.com"},
            )
            assert resp.status_code == 200

        auto_apply_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_analyze_job(self, auto_apply_app, mock_db):
        from backend.database import get_db

        mock_job = MagicMock()
        mock_job.url = "https://boards.greenhouse.io/company/jobs/123"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute = AsyncMock(return_value=mock_result)
        auto_apply_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=auto_apply_app), base_url="http://test") as client:
            resp = await client.post(
                "/api/auto-apply/analyze",
                json={"job_id": "test123"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "ats_provider" in data

        auto_apply_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_analyze_job_not_found(self, auto_apply_app, mock_db):
        from backend.database import get_db

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        auto_apply_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=auto_apply_app), base_url="http://test") as client:
            resp = await client.post(
                "/api/auto-apply/analyze",
                json={"job_id": "nonexistent"},
            )
            assert resp.status_code == 404

        auto_apply_app.dependency_overrides.clear()
