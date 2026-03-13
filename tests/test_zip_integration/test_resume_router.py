"""Test resume REST API endpoints."""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from backend.resume.document_manager import ResumeDocument


# Create a minimal FastAPI test app
@pytest.fixture
def resume_app():
    from fastapi import FastAPI
    from backend.routers.resume import router
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.delete = AsyncMock()
    return db


class TestResumeRouterEndpoints:
    @pytest.mark.asyncio
    async def test_list_versions_empty(self, resume_app, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        from backend.database import get_db
        resume_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=resume_app), base_url="http://test") as client:
            resp = await client.get("/api/resume/versions")
            assert resp.status_code == 200
            assert resp.json() == []

        resume_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_no_file(self, resume_app, mock_db):
        from backend.database import get_db
        resume_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=resume_app), base_url="http://test") as client:
            resp = await client.post("/api/resume/upload")
            assert resp.status_code == 422  # No file provided

        resume_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_unsupported_format(self, resume_app, mock_db):
        from backend.database import get_db
        resume_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=resume_app), base_url="http://test") as client:
            resp = await client.post(
                "/api/resume/upload",
                files={"file": ("resume.jpg", b"fake", "image/jpeg")},
            )
            assert resp.status_code == 400

        resume_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_txt_success(self, resume_app, mock_db):
        from backend.database import get_db
        resume_app.dependency_overrides[get_db] = lambda: mock_db

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.resume.document_manager.RESUME_DIR", tmpdir):
                # Mock the query to check for existing defaults
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None
                mock_db.execute = AsyncMock(return_value=mock_result)

                async with AsyncClient(transport=ASGITransport(app=resume_app), base_url="http://test") as client:
                    resp = await client.post(
                        "/api/resume/upload",
                        files={"file": ("resume.txt", b"John Doe\nSoftware Engineer", "text/plain")},
                    )
                    assert resp.status_code == 200
                    data = resp.json()
                    assert data["filename"] == "resume.txt"
                    assert data["format"] == "txt"
                    assert len(data["id"]) == 26

        resume_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, resume_app, mock_db):
        from backend.database import get_db
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        resume_app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(transport=ASGITransport(app=resume_app), base_url="http://test") as client:
            resp = await client.delete("/api/resume/versions/nonexistent")
            assert resp.status_code == 404

        resume_app.dependency_overrides.clear()
