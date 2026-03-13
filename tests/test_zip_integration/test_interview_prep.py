"""Test LLM-powered interview preparation."""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from backend.nlp.interview_prep import generate_interview_prep, InterviewPrep


class TestInterviewPrepDataclass:
    def test_create(self):
        ip = InterviewPrep(
            likely_questions=[{"question": "Tell me about yourself", "category": "behavioral"}],
            star_stories=[{"situation": "...", "task": "...", "action": "...", "result": "..."}],
            technical_topics=["System Design", "API Design"],
            company_talking_points=["Growing startup"],
            questions_to_ask=["What does a typical day look like?"],
            red_flag_responses=[{"question": "Why are you leaving?", "avoid": "Badmouthing employer", "instead": "Focus on growth"}],
        )
        assert len(ip.likely_questions) == 1
        assert len(ip.star_stories) == 1


@pytest.mark.asyncio
class TestGenerateInterviewPrep:
    async def test_with_mocked_llm(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "likely_questions": [
                {"question": "Tell me about your Python experience", "category": "technical"},
                {"question": "Describe a time you led a project", "category": "behavioral"},
            ],
            "star_stories": [
                {"situation": "API was slow", "task": "Optimize performance", "action": "Implemented caching", "result": "50% latency reduction"},
            ],
            "technical_topics": ["Python async", "Database optimization", "System design"],
            "company_talking_points": ["Leading AI company", "Remote-first culture"],
            "questions_to_ask": ["What is the team structure?", "How do you measure success?"],
            "red_flag_responses": [
                {"question": "Why are you leaving?", "avoid": "Negative comments", "instead": "Seeking growth opportunities"},
            ],
        })

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("backend.nlp.interview_prep._get_client", return_value=mock_client):
            result = await generate_interview_prep(
                resume_parsed={"text": "Python dev at Google. Led API redesign.", "skills": ["Python", "FastAPI"], "sections": {}},
                job_data={"title": "Senior Python Engineer", "description_clean": "Need Python expert for API team", "skills_required": ["Python", "FastAPI"], "company_name": "Acme Corp"},
                gap_analysis=None,
                api_key="test-key",
            )
            assert isinstance(result, InterviewPrep)
            assert len(result.likely_questions) >= 1
            assert len(result.star_stories) >= 1
            assert len(result.technical_topics) >= 1
            assert len(result.questions_to_ask) >= 1

    async def test_empty_resume_raises(self):
        with pytest.raises(ValueError):
            await generate_interview_prep(
                resume_parsed={"text": "", "skills": [], "sections": {}},
                job_data={"title": "SWE", "description_clean": "Python", "skills_required": []},
                gap_analysis=None,
                api_key="key",
            )

    async def test_includes_star_format(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "likely_questions": [{"question": "Q?", "category": "behavioral"}],
            "star_stories": [{"situation": "S", "task": "T", "action": "A", "result": "R"}],
            "technical_topics": ["Python"],
            "company_talking_points": [],
            "questions_to_ask": ["Q?"],
            "red_flag_responses": [],
        })

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("backend.nlp.interview_prep._get_client", return_value=mock_client):
            result = await generate_interview_prep(
                resume_parsed={"text": "Dev", "skills": ["Python"], "sections": {}},
                job_data={"title": "SWE", "description_clean": "Python", "skills_required": ["Python"]},
                gap_analysis=None,
                api_key="key",
            )
            story = result.star_stories[0]
            assert "situation" in story
            assert "task" in story
            assert "action" in story
            assert "result" in story
