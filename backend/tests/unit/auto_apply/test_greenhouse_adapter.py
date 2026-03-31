from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.auto_apply.form_extractor import FormField
from app.auto_apply.greenhouse_adapter import GreenhouseBrowserAdapter


def _make_mock_locator(*, exists: bool = True) -> AsyncMock:
    locator = AsyncMock()
    locator.count = AsyncMock(return_value=1 if exists else 0)
    locator.fill = AsyncMock()
    locator.type = AsyncMock()
    locator.set_input_files = AsyncMock()
    locator.check = AsyncMock()
    locator.select_option = AsyncMock()
    locator.first = locator
    return locator


def _make_mock_page(
    *,
    field_exists: bool = True,
    file_input_exists: bool = True,
    cover_letter_exists: bool = True,
    extra_selectors: dict[str, bool] | None = None,
) -> AsyncMock:
    page = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"fake-screenshot")
    locator_map: dict[str, AsyncMock] = {}
    extra_selectors = extra_selectors or {}

    cover_letter_selectors = {
        "#cover_letter",
        'textarea[id*="cover_letter"]',
        "#job_application_answers_attributes_0_text_value",
    }

    def locator_side_effect(selector: str) -> AsyncMock:
        if selector not in locator_map:
            if 'type="file"' in selector:
                locator_map[selector] = _make_mock_locator(exists=file_input_exists)
            elif selector in cover_letter_selectors:
                locator_map[selector] = _make_mock_locator(exists=cover_letter_exists)
            else:
                exists = extra_selectors.get(selector, field_exists)
                locator_map[selector] = _make_mock_locator(exists=exists)
        return locator_map[selector]

    page.locator = MagicMock(side_effect=locator_side_effect)
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
        assert result.needs_confirmation is True
        assert "first_name" in result.fields_filled
        assert "last_name" in result.fields_filled
        assert "email" in result.fields_filled

    @pytest.mark.asyncio
    async def test_tracks_missed_fields_when_selectors_absent(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        page = _make_mock_page(field_exists=False)
        profile = {"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"}

        result = await adapter.apply(page, profile)

        assert result.success is True
        assert "first_name" in result.fields_missed
        assert "phone" in result.fields_missed

    @pytest.mark.asyncio
    async def test_resume_upload(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        result = await adapter.apply(
            _make_mock_page(file_input_exists=True),
            {"first_name": "Jane", "email": "jane@example.com"},
            resume_path="/tmp/resume.pdf",
        )
        assert "resume" in result.fields_filled

    @pytest.mark.asyncio
    async def test_cover_letter_fill(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        result = await adapter.apply(
            _make_mock_page(cover_letter_exists=True),
            {"first_name": "Jane", "email": "jane@example.com"},
            cover_letter="I am excited to apply.",
        )
        assert "cover_letter" in result.fields_filled

    @pytest.mark.asyncio
    async def test_custom_questions_use_current_field_classifier(self) -> None:
        extractor = AsyncMock()
        extractor.extract_fields = AsyncMock(
            return_value=[
                FormField(
                    label="LinkedIn Profile",
                    field_type="text",
                    required=False,
                    aria_role="textbox",
                    locator_desc="#custom_q1",
                )
            ]
        )
        classifier = AsyncMock()
        classifier.classify = AsyncMock(return_value="linkedin")

        adapter = GreenhouseBrowserAdapter(
            form_extractor=extractor,
            field_mapper=classifier,
            human_typing=False,
        )
        page = _make_mock_page(extra_selectors={"#custom_q1": True})
        profile = {
            "first_name": "Jane",
            "email": "jane@example.com",
            "linkedin_url": "https://linkedin.com/in/jane",
        }

        result = await adapter.apply(page, profile)

        assert "LinkedIn Profile" in result.fields_filled
        classifier.classify.assert_awaited_once_with("LinkedIn Profile")

    @pytest.mark.asyncio
    async def test_custom_extractor_failure_is_non_fatal(self) -> None:
        extractor = AsyncMock()
        extractor.extract_fields = AsyncMock(side_effect=RuntimeError("boom"))
        classifier = AsyncMock()
        classifier.classify = AsyncMock()

        adapter = GreenhouseBrowserAdapter(
            form_extractor=extractor,
            field_mapper=classifier,
            human_typing=False,
        )
        result = await adapter.apply(
            _make_mock_page(),
            {"first_name": "Jane", "email": "jane@example.com"},
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_unclassified_custom_question_is_flagged_for_review(self) -> None:
        extractor = AsyncMock()
        extractor.extract_fields = AsyncMock(
            return_value=[
                FormField(
                    label="Do you now or will you in the future require sponsorship?",
                    field_type="text",
                    required=True,
                    aria_role="textbox",
                    locator_desc="#custom_q2",
                )
            ]
        )
        classifier = AsyncMock()
        classifier.classify = AsyncMock(return_value=None)

        adapter = GreenhouseBrowserAdapter(
            form_extractor=extractor,
            field_mapper=classifier,
            human_typing=False,
        )

        result = await adapter.apply(
            _make_mock_page(extra_selectors={"#custom_q2": True}),
            {"first_name": "Jane", "email": "jane@example.com"},
        )

        assert (
            "Review custom question "
            "'Do you now or will you in the future require sponsorship?'"
            in result.review_items
        )


class TestHumanTyping:
    @pytest.mark.asyncio
    async def test_human_typing_disabled_uses_fill(self) -> None:
        adapter = GreenhouseBrowserAdapter(human_typing=False)
        locator = _make_mock_locator()
        await adapter._human_type(locator, "test")
        locator.fill.assert_awaited_once_with("test")
