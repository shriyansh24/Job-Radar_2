"""Test LLM-powered resume tailoring."""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from backend.nlp.resume_tailor import tailor_resume, TailoredResume


class TestTailoredResumeDataclass:
    def test_create(self):
        tr = TailoredResume(
            summary="Experienced Python dev...",
            reordered_experience=[{"company": "Google", "bullets": ["Built APIs"]}],
            enhanced_bullets=[{"original": "Built APIs", "enhanced": "Led API redesign serving 1M users"}],
            skills_section=["Python", "FastAPI", "AWS"],
            ats_score_before=60,
            ats_score_after=85,
        )
        assert tr.ats_score_after > tr.ats_score_before


@pytest.mark.asyncio
class TestTailorResume:
    async def test_with_mocked_llm(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "summary": "Experienced Python engineer with strong API development skills",
            "reordered_experience": [{"company": "Google", "bullets": ["Led API redesign"]}],
            "enhanced_bullets": [{"original": "Built APIs", "enhanced": "Led API redesign serving 1M+ requests/day"}],
            "skills_section": ["Python", "FastAPI", "PostgreSQL", "AWS"],
            "ats_score_before": 55,
            "ats_score_after": 82,
        })

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("backend.nlp.resume_tailor._get_client", return_value=mock_client):
            result = await tailor_resume(
                resume_parsed={"text": "Python dev at Google. Built APIs.", "skills": ["Python"], "sections": {"experience": "Google"}},
                job_data={"title": "Senior Python Engineer", "description_clean": "Need FastAPI expert", "skills_required": ["Python", "FastAPI"]},
                gap_analysis=None,
                api_key="test-key",
            )
            assert isinstance(result, TailoredResume)
            assert result.ats_score_after >= result.ats_score_before

    async def test_empty_resume_raises(self):
        with pytest.raises(ValueError):
            await tailor_resume(
                resume_parsed={"text": "", "skills": [], "sections": {}},
                job_data={"title": "SWE", "description_clean": "Python", "skills_required": ["Python"]},
                gap_analysis=None,
                api_key="key",
            )

    async def test_returns_enhanced_bullets(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "summary": "Dev",
            "reordered_experience": [],
            "enhanced_bullets": [{"original": "Did stuff", "enhanced": "Delivered impactful features"}],
            "skills_section": ["Python"],
            "ats_score_before": 40,
            "ats_score_after": 70,
        })

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("backend.nlp.resume_tailor._get_client", return_value=mock_client):
            result = await tailor_resume(
                resume_parsed={"text": "Did stuff at company", "skills": ["Python"], "sections": {}},
                job_data={"title": "SWE", "description_clean": "Python dev", "skills_required": ["Python"]},
                gap_analysis=None,
                api_key="key",
            )
            assert len(result.enhanced_bullets) >= 1
