"""Test auto-apply orchestrator routing."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.auto_apply.orchestrator import auto_apply, ApplicationResult


class TestApplicationResult:
    def test_create_success(self):
        r = ApplicationResult(
            success=True,
            fields_filled={"name": "John", "email": "j@test.com"},
            fields_missed=["cover_letter"],
            screenshots=[],
            ats_provider="greenhouse",
            error=None,
        )
        assert r.success is True
        assert r.ats_provider == "greenhouse"

    def test_create_failure(self):
        r = ApplicationResult(
            success=False,
            fields_filled={},
            fields_missed=[],
            screenshots=[],
            ats_provider="unknown",
            error="Form not found",
        )
        assert r.success is False
        assert r.error == "Form not found"


@pytest.mark.asyncio
class TestAutoApply:
    async def test_detects_greenhouse(self):
        mock_job = {"url": "https://boards.greenhouse.io/company/jobs/123", "job_id": "test123"}

        with patch("backend.auto_apply.orchestrator.detect_ats_provider", return_value="greenhouse"):
            with patch("backend.auto_apply.orchestrator._run_generic_fill", new_callable=AsyncMock) as mock_fill:
                mock_fill.return_value = ApplicationResult(
                    success=True, fields_filled={"name": "John"}, fields_missed=[],
                    screenshots=[], ats_provider="greenhouse", error=None,
                )
                result = await auto_apply(mock_job, profile=MagicMock(), submit=False)
                assert result.ats_provider == "greenhouse"

    async def test_detects_workday(self):
        mock_job = {"url": "https://company.myworkdayjobs.com/external/123", "job_id": "test456"}

        with patch("backend.auto_apply.orchestrator.detect_ats_provider", return_value="workday"):
            with patch("backend.auto_apply.orchestrator._run_workday_fill", new_callable=AsyncMock) as mock_fill:
                mock_fill.return_value = ApplicationResult(
                    success=True, fields_filled={"name": "John"}, fields_missed=[],
                    screenshots=[], ats_provider="workday", error=None,
                )
                result = await auto_apply(mock_job, profile=MagicMock(), submit=False)
                assert result.ats_provider == "workday"

    async def test_unknown_ats_returns_error(self):
        mock_job = {"url": "https://unknown-ats.com/apply", "job_id": "test789"}

        with patch("backend.auto_apply.orchestrator.detect_ats_provider", return_value=None):
            result = await auto_apply(mock_job, profile=MagicMock(), submit=False)
            assert result.success is False
            assert "unsupported" in result.error.lower() or "unknown" in result.error.lower()

    async def test_submit_false_default(self):
        mock_job = {"url": "https://boards.greenhouse.io/co/jobs/1", "job_id": "test"}

        with patch("backend.auto_apply.orchestrator.detect_ats_provider", return_value="greenhouse"):
            with patch("backend.auto_apply.orchestrator._run_generic_fill", new_callable=AsyncMock) as mock_fill:
                mock_fill.return_value = ApplicationResult(
                    success=True, fields_filled={}, fields_missed=[],
                    screenshots=[], ats_provider="greenhouse", error=None,
                )
                await auto_apply(mock_job, profile=MagicMock(), submit=False)
                call_args = mock_fill.call_args
                assert call_args is not None
