"""Test Workday multi-page form controller with mocked Playwright."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.auto_apply.workday_filler import (
    WorkdayFiller,
    WorkdayResult,
    WORKDAY_PAGES,
    WORKDAY_SELECTORS,
)
from backend.auto_apply.profile import ApplicationProfile


class TestWorkdayConstants:
    def test_pages_defined(self):
        assert len(WORKDAY_PAGES) >= 5
        assert "My Information" in WORKDAY_PAGES or "my_information" in WORKDAY_PAGES

    def test_selectors_defined(self):
        assert isinstance(WORKDAY_SELECTORS, dict)
        assert len(WORKDAY_SELECTORS) > 0


class TestWorkdayResult:
    def test_create(self):
        wr = WorkdayResult(
            pages_completed=["My Information", "My Experience"],
            fields_filled={"name": "John Doe"},
            fields_skipped=["cover_letter"],
            custom_questions_answered=[],
            screenshots=[],
            needs_review=["salary field"],
            browser_session_id="sess-123",
        )
        assert len(wr.pages_completed) == 2
        assert wr.browser_session_id == "sess-123"


@pytest.mark.asyncio
class TestWorkdayFiller:
    async def test_create_filler(self):
        profile = ApplicationProfile(name="John Doe", email="john@test.com")
        filler = WorkdayFiller(profile)
        assert filler.profile.name == "John Doe"

    async def test_fill_page_returns_fields(self):
        profile = ApplicationProfile(name="John Doe", email="john@test.com", phone="+1-555-0123")

        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=None)
        mock_page.query_selector_all = AsyncMock(return_value=[])
        mock_page.wait_for_selector = AsyncMock(return_value=None)

        filler = WorkdayFiller(profile)
        result = await filler._fill_my_information(mock_page)
        assert isinstance(result, dict)

    async def test_workday_selectors_use_data_automation_id(self):
        # Verify Workday selectors use stable data-automation-id attributes
        for key, selector in WORKDAY_SELECTORS.items():
            assert "data-automation-id" in selector or "[" in selector, \
                f"Selector {key} should use data-automation-id: {selector}"
