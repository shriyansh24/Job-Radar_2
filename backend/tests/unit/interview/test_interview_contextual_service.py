from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.interview.schemas import InterviewPrepRequest
from app.interview.service import InterviewService


@pytest.mark.asyncio
async def test_prepare_interview_returns_contextual_sections() -> None:
    router = MagicMock()
    router.complete_json = AsyncMock(
        return_value={
            "likely_questions": [
                {
                    "question": "Tell me about a system you designed.",
                    "category": "technical",
                }
            ],
            "star_stories": [],
            "technical_topics": ["System design"],
            "company_talking_points": ["Fast growth"],
            "questions_to_ask": ["What does success look like in 90 days?"],
            "red_flag_responses": [],
            "company_research": {
                "overview": "Acme builds workflow software.",
                "recent_news": ["Launched new platform"],
                "culture_values": ["Ownership"],
                "interview_style": "Structured technical loop",
            },
            "role_analysis": {
                "key_requirements": ["Python", "FastAPI"],
                "skill_gaps": ["Kubernetes"],
                "talking_points": ["API scaling experience"],
                "seniority_expectations": "Hands-on senior IC",
            },
        }
    )
    db = MagicMock()

    with patch("app.interview.service._build_router", return_value=router):
        service = InterviewService(db)

    response = await service.prepare_interview(
        InterviewPrepRequest(
            job_id="job-123",
            stage="technical",
            resume_text="Experienced backend engineer with Python and FastAPI." * 4,
            job_title="Senior Backend Engineer",
            company_name="Acme",
            job_description="Build APIs and system design",
            required_skills=["Python", "FastAPI"],
        ),
        user_id=uuid.uuid4(),
    )

    assert response.company_research is not None
    assert response.company_research.overview == "Acme builds workflow software."
    assert response.role_analysis is not None
    assert response.role_analysis.key_requirements == ["Python", "FastAPI"]
    assert response.technical_topics == ["System design"]


@pytest.mark.asyncio
async def test_prepare_interview_uses_db_skills_and_default_stage() -> None:
    router = MagicMock()
    router.complete_json = AsyncMock(
        return_value={
            "likely_questions": [],
            "star_stories": [],
            "technical_topics": [],
            "company_talking_points": [],
            "questions_to_ask": [],
            "red_flag_responses": [],
        }
    )
    db = MagicMock()

    with patch("app.interview.service._build_router", return_value=router):
        service = InterviewService(db)

    service._load_job_context = AsyncMock(
        return_value=(
            "Senior Backend Engineer",
            "Acme",
            "Build APIs",
            ["Python", "FastAPI"],
        )
    )

    await service.prepare_interview(
        InterviewPrepRequest(
            job_id="job-123",
            resume_text="Experienced backend engineer with Python and FastAPI." * 4,
        ),
        user_id=uuid.uuid4(),
    )

    call_kwargs = router.complete_json.await_args.kwargs
    user_message = call_kwargs["messages"][1]["content"]
    assert "Tailor the prep to the interview stage: general" in user_message
    assert "REQUIRED SKILLS: Python, FastAPI" in user_message
