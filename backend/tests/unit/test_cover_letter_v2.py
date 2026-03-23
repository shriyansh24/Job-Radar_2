"""Tests for Cover Letter with Company Research Integration (B6)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.nlp.cover_letter import (
    _COVER_LETTER_PROMPT,
    VALID_STYLES,
    CoverLetterResult,
    generate_cover_letter,
)
from app.resume.schemas import VALID_TONES, CoverLetterGenerateRequest

# ---------------------------------------------------------------------------
# Schema / validation tests
# ---------------------------------------------------------------------------


class TestCoverLetterSchemas:
    def test_valid_tones(self) -> None:
        assert "formal" in VALID_TONES
        assert "conversational" in VALID_TONES
        assert "enthusiastic" in VALID_TONES

    def test_generate_request_defaults(self) -> None:
        req = CoverLetterGenerateRequest(job_id="abc123")
        assert req.tone == "formal"
        assert req.template is None
        assert req.resume_version_id is None

    def test_generate_request_custom(self) -> None:
        req = CoverLetterGenerateRequest(
            job_id="abc123",
            tone="enthusiastic",
            template="startup",
        )
        assert req.tone == "enthusiastic"
        assert req.template == "startup"


# ---------------------------------------------------------------------------
# Prompt template tests
# ---------------------------------------------------------------------------


class TestPromptTemplate:
    def test_company_context_placeholder_present(self) -> None:
        assert "{company_context_section}" in _COVER_LETTER_PROMPT

    def test_prompt_formats_with_company_context(self) -> None:
        prompt = _COVER_LETTER_PROMPT.format(
            style_instructions="Test style",
            template_section="",
            company_context_section="COMPANY RESEARCH:\nTestCo - AI company\n\n",
            resume_text="I am a developer",
            job_title="Engineer",
            company_name="TestCo",
            job_description="Build things",
            required_skills="python",
        )
        assert "COMPANY RESEARCH:" in prompt
        assert "TestCo - AI company" in prompt

    def test_prompt_formats_without_company_context(self) -> None:
        prompt = _COVER_LETTER_PROMPT.format(
            style_instructions="Test style",
            template_section="",
            company_context_section="",
            resume_text="I am a developer",
            job_title="Engineer",
            company_name="TestCo",
            job_description="Build things",
            required_skills="python",
        )
        assert "COMPANY RESEARCH:" not in prompt


# ---------------------------------------------------------------------------
# Generate function tests (mocked LLM)
# ---------------------------------------------------------------------------


class TestGenerateCoverLetter:
    @pytest.mark.asyncio
    async def test_invalid_style_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid style"):
            await generate_cover_letter(
                resume_parsed={"text": "hello"},
                job_data={"title": "eng"},
                style="invalid_style",
            )

    @pytest.mark.asyncio
    async def test_empty_resume_raises(self) -> None:
        with pytest.raises(ValueError, match="Resume text is required"):
            await generate_cover_letter(
                resume_parsed={"text": ""},
                job_data={"title": "eng"},
                style="professional",
            )

    @pytest.mark.asyncio
    async def test_invalid_template_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid template"):
            await generate_cover_letter(
                resume_parsed={"text": "hello world developer"},
                job_data={"title": "eng"},
                style="professional",
                template="nonexistent",
            )

    @pytest.mark.asyncio
    async def test_successful_generation_with_company_context(self) -> None:
        mock_result: dict[str, Any] = {
            "content": "Dear Hiring Manager, ...",
            "key_points_addressed": ["python expertise"],
            "skills_highlighted": ["python", "ml"],
            "company_research_notes": ["AI-focused company"],
            "word_count": 250,
            "reading_level": "professional",
        }

        mock_router = AsyncMock()
        mock_router.complete_json = AsyncMock(return_value=mock_result)

        mock_llm = AsyncMock()
        mock_router._llm = mock_llm

        with patch(
            "app.nlp.cover_letter._get_model_router", return_value=mock_router
        ):
            result = await generate_cover_letter(
                resume_parsed={"text": "Python developer with ML experience"},
                job_data={
                    "title": "ML Engineer",
                    "description_clean": "Build ML systems",
                    "skills_required": ["python"],
                    "company_name": "TestCorp",
                    "company_context": "Company: TestCorp\nDomain: testcorp.com",
                },
                style="professional",
            )

        assert isinstance(result, CoverLetterResult)
        assert result.content == "Dear Hiring Manager, ..."
        assert result.word_count == 250

        # Verify company context was included in the prompt
        call_args = mock_router.complete_json.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        user_msg = messages[1]["content"]
        assert "COMPANY RESEARCH:" in user_msg
        assert "TestCorp" in user_msg

    @pytest.mark.asyncio
    async def test_successful_generation_without_company_context(self) -> None:
        mock_result: dict[str, Any] = {
            "content": "Dear Hiring Manager, ...",
            "key_points_addressed": [],
            "skills_highlighted": [],
            "company_research_notes": [],
            "word_count": 200,
            "reading_level": "professional",
        }

        mock_router = AsyncMock()
        mock_router.complete_json = AsyncMock(return_value=mock_result)

        mock_llm = AsyncMock()
        mock_router._llm = mock_llm

        with patch(
            "app.nlp.cover_letter._get_model_router", return_value=mock_router
        ):
            result = await generate_cover_letter(
                resume_parsed={"text": "Python developer"},
                job_data={
                    "title": "Engineer",
                    "description_clean": "Build things",
                    "skills_required": ["python"],
                    "company_name": "SomeCo",
                },
                style="conversational",
            )

        assert isinstance(result, CoverLetterResult)

        # Verify company context section was empty
        call_args = mock_router.complete_json.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        user_msg = messages[1]["content"]
        assert "COMPANY RESEARCH:" not in user_msg

    @pytest.mark.asyncio
    async def test_all_styles_valid(self) -> None:
        for style in VALID_STYLES:
            mock_result: dict[str, Any] = {
                "content": f"Letter in {style}",
                "key_points_addressed": [],
                "skills_highlighted": [],
                "company_research_notes": [],
                "word_count": 100,
                "reading_level": style,
            }

            mock_router = AsyncMock()
            mock_router.complete_json = AsyncMock(return_value=mock_result)
            mock_router._llm = AsyncMock()

            with patch(
                "app.nlp.cover_letter._get_model_router",
                return_value=mock_router,
            ):
                result = await generate_cover_letter(
                    resume_parsed={"text": "Python developer experience"},
                    job_data={"title": "Engineer", "description_clean": "Build"},
                    style=style,
                )
            assert result.content == f"Letter in {style}"
