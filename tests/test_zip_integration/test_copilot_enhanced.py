"""Tests for enhanced copilot router — Task 9.1.

Covers:
- tailorResume tool existence + placeholders
- NLP delegation (returns None on ImportError, returns structured result when available)
- Unknown tool → 400
- Missing API key → 400
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Task 9.1.1 — tailorResume tool must exist in TOOL_PROMPTS
# ---------------------------------------------------------------------------

class TestTailorResumeTool:
    def test_tailor_resume_tool_exists(self):
        """'tailorResume' must be present in TOOL_PROMPTS."""
        from backend.routers.copilot import TOOL_PROMPTS
        assert "tailorResume" in TOOL_PROMPTS

    def test_tailor_resume_prompt_has_placeholders(self):
        """The tailorResume prompt must contain required format placeholders."""
        from backend.routers.copilot import TOOL_PROMPTS
        prompt = TOOL_PROMPTS["tailorResume"]
        assert "{title}" in prompt
        assert "{company_name}" in prompt
        assert "{skills_required}" in prompt
        assert "{description}" in prompt
        assert "{resume_context}" in prompt

    def test_all_original_tools_still_exist(self):
        """Ensure original tools are not accidentally removed."""
        from backend.routers.copilot import TOOL_PROMPTS
        for tool in ("coverLetter", "interviewPrep", "gapAnalysis"):
            assert tool in TOOL_PROMPTS, f"Original tool '{tool}' was removed!"


# ---------------------------------------------------------------------------
# Task 9.1.2 — NLP delegation helper
# ---------------------------------------------------------------------------

class TestNlpDelegation:
    @pytest.mark.asyncio
    async def test_nlp_delegation_returns_none_on_import_error(self):
        """_try_nlp_delegation returns None when the NLP module cannot be imported."""
        from backend.routers.copilot import _try_nlp_delegation

        mock_job = MagicMock()
        mock_job.title = "ML Engineer"
        mock_job.company_name = "Acme"
        mock_job.skills_required = ["Python"]
        mock_job.skills_nice_to_have = []
        mock_job.description_clean = "We need Python skills."

        mock_settings = MagicMock()
        mock_settings.OPENROUTER_API_KEY = "sk-test"

        # Patch the import inside the function to raise ImportError
        with patch.dict("sys.modules", {"backend.nlp.gap_analyzer": None}):
            result = await _try_nlp_delegation(
                "gapAnalysis", mock_job, "Resume: Python developer", mock_settings
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_nlp_delegation_gap_analysis_returns_structured(self):
        """_try_nlp_delegation returns structured dict when gap_analyzer is available."""
        from backend.routers.copilot import _try_nlp_delegation
        from backend.nlp.gap_analyzer import GapAnalysis

        mock_job = MagicMock()
        mock_job.title = "ML Engineer"
        mock_job.company_name = "Acme"
        mock_job.skills_required = ["Python", "TensorFlow"]
        mock_job.skills_nice_to_have = ["Kubernetes"]
        mock_job.description_clean = "We need a Python ML engineer."

        mock_settings = MagicMock()
        mock_settings.OPENROUTER_API_KEY = "sk-test"

        fake_result = GapAnalysis(
            matched_skills=[{"skill": "python", "confidence": 1.0}],
            missing_skills=["tensorflow"],
            keyword_density=0.5,
            experience_fit=0.8,
        )

        with patch("backend.nlp.gap_analyzer.analyze_gaps", return_value=fake_result):
            result = await _try_nlp_delegation(
                "gapAnalysis", mock_job, "Resume: Python developer", mock_settings
            )

        assert result is not None
        assert result["tool"] == "gapAnalysis"
        assert result["structured"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_nlp_delegation_non_gap_tool_returns_none(self):
        """_try_nlp_delegation returns None for tools without NLP module support."""
        from backend.routers.copilot import _try_nlp_delegation

        mock_job = MagicMock()
        mock_settings = MagicMock()

        result = await _try_nlp_delegation(
            "coverLetter", mock_job, "Resume: Some text", mock_settings
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_nlp_delegation_tailor_resume_returns_none(self):
        """tailorResume falls through to LLM (no NLP module delegation yet)."""
        from backend.routers.copilot import _try_nlp_delegation

        mock_job = MagicMock()
        mock_settings = MagicMock()

        result = await _try_nlp_delegation(
            "tailorResume", mock_job, "Resume: Some text", mock_settings
        )
        assert result is None


# ---------------------------------------------------------------------------
# Task 9.1.3 — Endpoint-level checks (FastAPI TestClient)
# ---------------------------------------------------------------------------

class TestCopilotEndpointGuards:
    @pytest.fixture
    def app(self):
        """Return the FastAPI app with DB dependency overridden."""
        from fastapi.testclient import TestClient
        from backend.main import app

        return app

    def test_copilot_requires_api_key(self, app):
        """Returns 400 when OPENROUTER_API_KEY is empty."""
        from fastapi.testclient import TestClient
        from backend.config import get_settings
        from backend.database import get_db

        mock_db = AsyncMock()

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            with patch.object(get_settings(), "OPENROUTER_API_KEY", ""):
                with patch("backend.routers.copilot.get_settings") as mock_gs:
                    mock_settings = MagicMock()
                    mock_settings.OPENROUTER_API_KEY = ""
                    mock_gs.return_value = mock_settings

                    client = TestClient(app, raise_server_exceptions=False)
                    resp = client.post(
                        "/api/copilot",
                        json={"tool": "coverLetter", "job_id": "job-abc"},
                    )
            assert resp.status_code == 400
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_copilot_unknown_tool_returns_400(self, app):
        """Returns 400 for an unrecognised tool name."""
        from fastapi.testclient import TestClient
        from backend.database import get_db

        mock_db = AsyncMock()

        async def override_get_db():
            yield mock_db

        # Fake job returned by DB
        mock_job = MagicMock()
        mock_job.title = "Engineer"
        mock_job.company_name = "Corp"
        mock_job.skills_required = []
        mock_job.skills_nice_to_have = []
        mock_job.description_clean = "Description"

        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_job))
        )

        app.dependency_overrides[get_db] = override_get_db

        try:
            with patch("backend.routers.copilot.get_settings") as mock_gs:
                mock_settings = MagicMock()
                mock_settings.OPENROUTER_API_KEY = "sk-valid-key"
                mock_settings.OPENROUTER_PRIMARY_MODEL = "anthropic/claude-3-5-haiku"
                mock_gs.return_value = mock_settings

                client = TestClient(app, raise_server_exceptions=False)
                resp = client.post(
                    "/api/copilot",
                    json={"tool": "nonExistentTool", "job_id": "job-abc"},
                )
            assert resp.status_code == 400
        finally:
            app.dependency_overrides.pop(get_db, None)
