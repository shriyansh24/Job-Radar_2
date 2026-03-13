"""Test LLM-powered cover letter generation."""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from backend.nlp.cover_letter import generate_cover_letter, CoverLetter, VALID_STYLES


class TestCoverLetterDataclass:
    def test_create(self):
        cl = CoverLetter(
            content="Dear Hiring Manager...",
            key_points_addressed=["Python experience", "API design"],
            skills_highlighted=["Python", "FastAPI"],
            company_research_notes=["Growing startup in AI space"],
            word_count=250,
            reading_level="professional",
        )
        assert cl.word_count == 250


class TestValidStyles:
    def test_four_styles(self):
        assert len(VALID_STYLES) == 4
        assert "professional" in VALID_STYLES
        assert "conversational" in VALID_STYLES
        assert "technical" in VALID_STYLES
        assert "storytelling" in VALID_STYLES


@pytest.mark.asyncio
class TestGenerateCoverLetter:
    async def test_with_mocked_llm(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "content": "Dear Hiring Manager, I am excited to apply for the Senior Python Engineer role...",
            "key_points_addressed": ["Python expertise", "API development"],
            "skills_highlighted": ["Python", "FastAPI", "AWS"],
            "company_research_notes": ["Leading cloud platform"],
            "word_count": 280,
            "reading_level": "professional",
        })

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("backend.nlp.cover_letter._get_client", return_value=mock_client):
            result = await generate_cover_letter(
                resume_parsed={"text": "Python dev at Google", "skills": ["Python", "FastAPI"], "sections": {}},
                job_data={"title": "Senior Python Engineer", "description_clean": "Need Python expert", "skills_required": ["Python", "FastAPI"], "company_name": "Acme Corp"},
                gap_analysis=None,
                style="professional",
                api_key="test-key",
            )
            assert isinstance(result, CoverLetter)
            assert result.word_count > 0
            assert len(result.skills_highlighted) > 0

    async def test_invalid_style_raises(self):
        with pytest.raises(ValueError, match="style"):
            await generate_cover_letter(
                resume_parsed={"text": "Dev", "skills": [], "sections": {}},
                job_data={"title": "SWE", "description_clean": "Python", "skills_required": []},
                gap_analysis=None,
                style="invalid_style",
                api_key="key",
            )

    async def test_empty_resume_raises(self):
        with pytest.raises(ValueError):
            await generate_cover_letter(
                resume_parsed={"text": "", "skills": [], "sections": {}},
                job_data={"title": "SWE", "description_clean": "Python", "skills_required": []},
                gap_analysis=None,
                style="professional",
                api_key="key",
            )

    async def test_storytelling_style(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "content": "When I first started coding...",
            "key_points_addressed": ["passion"],
            "skills_highlighted": ["Python"],
            "company_research_notes": [],
            "word_count": 200,
            "reading_level": "conversational",
        })

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("backend.nlp.cover_letter._get_client", return_value=mock_client):
            result = await generate_cover_letter(
                resume_parsed={"text": "Dev with passion", "skills": ["Python"], "sections": {}},
                job_data={"title": "SWE", "description_clean": "Python", "skills_required": ["Python"]},
                gap_analysis=None,
                style="storytelling",
                api_key="key",
            )
            assert isinstance(result, CoverLetter)
