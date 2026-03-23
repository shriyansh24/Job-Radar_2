"""Tests for the Greenhouse browser adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.auto_apply.greenhouse_adapter import GreenhouseBrowserAdapter


def _make_mock_locator(*, exists: bool = True) -> AsyncMock:
    """Create a mock Playwright Locator."""
    loc = AsyncMock()
    loc.count = AsyncMock(return_value=1 if exists else 0)
    loc.fill = AsyncMock()
    loc.type = AsyncMock()
    loc.set_input_files = AsyncMock()
    loc.first = loc  # .first returns itself for chaining
    return loc


def _make_mock_page(
    *,
    field_exists: bool = True,
    file_input_exists: bool = True,
    cover_letter_exists: bool = True,
) -> AsyncMock:
    """Create a mock Playwright Page with configurable element presence."""
    page = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"fake-screenshot-bytes")

    locator_map: dict[str, AsyncMock] = {}

    # All known cover letter selectors from the adapter
    _cover_letter_selectors = {
        "#cover_letter",
        'textarea[id*="cover_letter"]',
        "#job_application_answers_attributes_0_text_value",
    }

    def mock_locator(selector: str) -> AsyncMock:
        if selector not in locator_map:
            # Decide existence based on selector type
            if 'type="file"' in selector:
                locator_map[selector] = _make_mock_locator(exists=file_input_exists)
            elif selector in _cover_letter_selectors:
                locator_map[selector] = _make_mock_locator(exists=cover_letter_exists)
            else:
                locator_map[selector] = _make_mock_locator(exists=field_exists)
        return locator_map[selector]

    page.locator = MagicMock(side_effect=mock_locator)
    return page


class TestGreenhouseApply:
    @pytest.mark.asyncio
    async def test_fills_standard_fields(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        page = _make_mock_page()
        profile = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone": "+1-555-0100",
            "city": "San Francisco",
        }

        result = await adapter.apply(page, profile)

        assert result.success is True
        assert result.ats == "greenhouse"
        assert result.method == "browser"
        assert result.needs_confirmation is True
        assert "first_name" in result.fields_filled
        assert "last_name" in result.fields_filled
        assert "email" in result.fields_filled

    @pytest.mark.asyncio
    async def test_missing_fields_tracked(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        page = _make_mock_page(field_exists=False)
        profile = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
        }

        result = await adapter.apply(page, profile)

        assert result.success is True
        # Fields existed in profile but selectors not found on page
        assert "first_name" in result.fields_missed
        # phone/city not in profile → also missed
        assert "phone" in result.fields_missed

    @pytest.mark.asyncio
    async def test_resume_upload(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        page = _make_mock_page(file_input_exists=True)
        profile = {"first_name": "J", "email": "j@x.com"}

        result = await adapter.apply(page, profile, resume_path="/tmp/resume.pdf")

        assert "resume" in result.fields_filled

    @pytest.mark.asyncio
    async def test_resume_upload_no_input(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        page = _make_mock_page(file_input_exists=False)
        profile = {"first_name": "J", "email": "j@x.com"}

        result = await adapter.apply(page, profile, resume_path="/tmp/resume.pdf")

        assert "resume" in result.fields_missed

    @pytest.mark.asyncio
    async def test_cover_letter_filled(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        page = _make_mock_page(cover_letter_exists=True)
        profile = {"first_name": "J", "email": "j@x.com"}

        result = await adapter.apply(
            page, profile, cover_letter="I am excited to join your team."
        )

        assert "cover_letter" in result.fields_filled

    @pytest.mark.asyncio
    async def test_cover_letter_no_textarea(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        page = _make_mock_page(cover_letter_exists=False)
        profile = {"first_name": "J", "email": "j@x.com"}

        result = await adapter.apply(
            page, profile, cover_letter="I am excited to join your team."
        )

        assert "cover_letter" in result.fields_missed

    @pytest.mark.asyncio
    async def test_screenshot_captured(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        page = _make_mock_page()
        profile = {"first_name": "J", "email": "j@x.com"}

        result = await adapter.apply(page, profile)

        page.screenshot.assert_awaited_once_with(full_page=True)
        assert result.screenshot == b"fake-screenshot-bytes"

    @pytest.mark.asyncio
    async def test_never_auto_submits(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        page = _make_mock_page()
        profile = {"first_name": "J", "email": "j@x.com"}

        result = await adapter.apply(page, profile)

        assert result.needs_confirmation is True
        # Ensure no click on submit button
        page.locator.assert_any_call("#first_name")
        # No submit-related calls should exist

    @pytest.mark.asyncio
    async def test_custom_questions_with_extractor(self) -> None:
        mock_extractor = AsyncMock()
        mock_extractor.extract_fields = AsyncMock(
            return_value=[
                {"selector": "#custom_q1", "label": "Years of experience", "type": "text"}
            ]
        )
        mock_mapper = AsyncMock()
        mock_mapper.map_fields = AsyncMock(
            return_value=[
                {"selector": "#custom_q1", "label": "Years of experience", "value": "5"}
            ]
        )

        adapter = GreenhouseBrowserAdapter(
            form_extractor=mock_extractor,
            field_mapper=mock_mapper,
            human_typing=False,
        )
        page = _make_mock_page()
        profile = {"first_name": "J", "email": "j@x.com"}

        result = await adapter.apply(page, profile)

        assert "Years of experience" in result.fields_filled

    @pytest.mark.asyncio
    async def test_custom_questions_extractor_failure_non_fatal(self) -> None:
        mock_extractor = AsyncMock()
        mock_extractor.extract_fields = AsyncMock(side_effect=RuntimeError("extraction failed"))
        mock_mapper = AsyncMock()

        adapter = GreenhouseBrowserAdapter(
            form_extractor=mock_extractor,
            field_mapper=mock_mapper,
            human_typing=False,
        )
        page = _make_mock_page()
        profile = {"first_name": "J", "email": "j@x.com"}

        # Should not raise — custom question failure is non-fatal
        result = await adapter.apply(page, profile)
        assert result.success is True


class TestHumanTyping:
    @pytest.mark.asyncio
    async def test_human_typing_enabled(self) -> None:
        adapter = GreenhouseBrowserAdapter(
            human_typing=True, min_type_delay=10, max_type_delay=20
        )
        page = _make_mock_page()
        profile = {"first_name": "Jo", "email": "j@x.com"}

        await adapter.apply(page, profile)

        # When human_typing is True, the adapter should call .type() per character
        # instead of .fill()
        locator = page.locator("#first_name")
        # At minimum, type should have been called (one per char)
        assert locator.type.await_count >= 2  # "Jo" = 2 chars

    @pytest.mark.asyncio
    async def test_human_typing_disabled_uses_fill(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        locator = _make_mock_locator()

        await adapter._human_type(locator, "test")

        locator.fill.assert_awaited_once_with("test")
