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
                json={"full_name": "John Doe", "email": "john@test.com"},
            )
            assert resp.status_code == 200

        auto_apply_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_save_profile_new_field_names(self, auto_apply_app, mock_db):
        """Verify the new field names (full_name, linkedin_url, etc.) are accepted."""
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
                json={
                    "full_name": "Jane Doe",
                    "email": "jane@test.com",
                    "linkedin_url": "https://linkedin.com/in/jane",
                    "github_url": "https://github.com/jane",
                    "portfolio_url": "https://jane.dev",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "profile" in data
            assert data["profile"]["full_name"] == "Jane Doe"
            assert data["profile"]["linkedin_url"] == "https://linkedin.com/in/jane"

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

    @pytest.mark.asyncio
    async def test_run_auto_apply(self, auto_apply_app, mock_db):
        """POST /auto-apply/run queues a task and returns status=queued."""
        from backend.database import get_db

        mock_job = MagicMock()
        mock_job.url = "https://boards.greenhouse.io/stripe/jobs/456"

        mock_user = MagicMock()
        mock_user.application_profile = {
            "full_name": "John Doe",
            "email": "john@test.com",
        }

        # Two execute calls: first for job lookup, second for user profile lookup
        mock_job_result = MagicMock()
        mock_job_result.scalar_one_or_none.return_value = mock_job
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user

        mock_db.execute = AsyncMock(side_effect=[mock_job_result, mock_user_result])
        auto_apply_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=auto_apply_app), base_url="http://test") as client:
            resp = await client.post(
                "/api/auto-apply/run",
                json={"job_id": "job-456", "submit": False},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "queued"
            assert data["job_id"] == "job-456"
            assert "ats_provider" in data

        auto_apply_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_run_auto_apply_job_not_found(self, auto_apply_app, mock_db):
        """POST /auto-apply/run returns 404 when job does not exist."""
        from backend.database import get_db

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        auto_apply_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=auto_apply_app), base_url="http://test") as client:
            resp = await client.post(
                "/api/auto-apply/run",
                json={"job_id": "nonexistent-job"},
            )
            assert resp.status_code == 404

        auto_apply_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_run_auto_apply_no_profile(self, auto_apply_app, mock_db):
        """POST /auto-apply/run returns 400 when no profile is configured."""
        from backend.database import get_db

        mock_job = MagicMock()
        mock_job.url = "https://boards.greenhouse.io/company/jobs/1"

        mock_job_result = MagicMock()
        mock_job_result.scalar_one_or_none.return_value = mock_job
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = None  # no user profile

        mock_db.execute = AsyncMock(side_effect=[mock_job_result, mock_user_result])
        auto_apply_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=auto_apply_app), base_url="http://test") as client:
            resp = await client.post(
                "/api/auto-apply/run",
                json={"job_id": "job-1"},
            )
            assert resp.status_code == 400

        auto_apply_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_pause_auto_apply(self, auto_apply_app):
        """POST /auto-apply/pause returns status=paused."""
        async with AsyncClient(transport=ASGITransport(app=auto_apply_app), base_url="http://test") as client:
            resp = await client.post("/api/auto-apply/pause")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "paused"

    @pytest.mark.asyncio
    async def test_pause_auto_apply_returns_message(self, auto_apply_app):
        """POST /auto-apply/pause includes a human-readable message."""
        async with AsyncClient(transport=ASGITransport(app=auto_apply_app), base_url="http://test") as client:
            resp = await client.post("/api/auto-apply/pause")
            assert resp.status_code == 200
            data = resp.json()
            assert "message" in data
            assert len(data["message"]) > 0
