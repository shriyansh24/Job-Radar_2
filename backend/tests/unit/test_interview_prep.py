from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.interview.prep_engine import InterviewPrepEngine, to_prep_response
from app.interview.schemas import (
    VALID_PREP_STAGES,
    ContextualPrepData,
    ContextualPrepRequest,
    ContextualPrepResponse,
)
from app.jobs.models import Job
from app.pipeline.models import Application
from app.pipeline.schemas import StatusTransition
from app.pipeline.service import PipelineService
from app.shared.errors import NotFoundError, ValidationError


@pytest.fixture
async def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
async def sample_job(db_session: AsyncSession, user_id: uuid.UUID) -> Job:
    job = Job(
        id="interview-prep-test-job",
        user_id=user_id,
        source="test",
        title="Senior Backend Engineer",
        company_name="Acme Corp",
        description_raw="We need a senior backend engineer with Python, FastAPI, and PostgreSQL.",
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest.fixture
async def sample_app(
    db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job
) -> Application:
    from app.pipeline.schemas import ApplicationCreate

    svc = PipelineService(db_session)
    return await svc.create_application(
        ApplicationCreate(
            job_id=sample_job.id,
            company_name="Acme Corp",
            position_title="Senior Backend Engineer",
            source="manual",
        ),
        user_id,
    )


MOCK_PREP_RESPONSE = {
    "company_research": {
        "overview": "Acme Corp is a tech company",
        "recent_news": ["Launched new product"],
        "culture_values": ["Innovation", "Collaboration"],
        "interview_style": "Technical deep-dive",
    },
    "role_analysis": {
        "key_requirements": ["Python expertise", "System design"],
        "skill_gaps": ["Kubernetes experience"],
        "talking_points": ["5 years Python experience"],
        "seniority_expectations": "IC with mentoring responsibilities",
    },
    "likely_questions": [
        {
            "question": "Tell me about a complex system you designed",
            "category": "technical",
            "why_likely": "Senior role requires system design",
            "suggested_approach": "Use STAR format",
        },
        {
            "question": "How do you handle disagreements with teammates?",
            "category": "behavioral",
            "why_likely": "Senior roles require collaboration",
            "suggested_approach": "Show empathy and resolution skills",
        },
    ],
    "suggested_answers": [
        {
            "question": "Tell me about a complex system you designed",
            "star_response": {
                "situation": "At previous company",
                "task": "Design a scalable API",
                "action": "Chose FastAPI with async patterns",
                "result": "Handled 10x traffic increase",
            },
            "key_points": ["Scalability", "Technical depth"],
        }
    ],
    "questions_to_ask": [
        {
            "question": "What does success look like in 90 days?",
            "why_effective": "Shows forward thinking",
            "what_to_listen_for": "Clear expectations vs vague answers",
        }
    ],
    "red_flags": [
        {
            "trap": "Badmouthing previous employer",
            "why_dangerous": "Shows lack of professionalism",
            "better_approach": "Focus on what you learned",
        }
    ],
}


# -- Schema tests ----------------------------------------------------------


class TestContextualPrepSchemas:
    def test_valid_stages(self) -> None:
        assert "general" in VALID_PREP_STAGES
        assert "phone_screen" in VALID_PREP_STAGES
        assert "technical" in VALID_PREP_STAGES
        assert "behavioral" in VALID_PREP_STAGES
        assert "final" in VALID_PREP_STAGES

    def test_prep_request_default_stage(self) -> None:
        req = ContextualPrepRequest()
        assert req.stage == "general"

    def test_contextual_prep_data_from_dict(self) -> None:
        data = ContextualPrepData(**MOCK_PREP_RESPONSE)
        assert data.company_research.overview == "Acme Corp is a tech company"
        assert len(data.likely_questions) == 2
        assert len(data.suggested_answers) == 1
        assert len(data.questions_to_ask) == 1
        assert len(data.red_flags) == 1
        assert data.role_analysis.seniority_expectations == "IC with mentoring responsibilities"

    def test_contextual_prep_data_empty(self) -> None:
        data = ContextualPrepData()
        assert data.likely_questions == []
        assert data.company_research.overview == ""


# -- Engine tests ----------------------------------------------------------


class TestInterviewPrepEngine:
    @pytest.mark.asyncio
    async def test_generate_prep_invalid_stage(
        self, db_session: AsyncSession, user_id: uuid.UUID, sample_app: Application
    ) -> None:
        engine = InterviewPrepEngine(db_session)
        with pytest.raises(ValidationError, match="Invalid stage"):
            await engine.generate_prep(sample_app.id, user_id, stage="invalid")

    @pytest.mark.asyncio
    async def test_generate_prep_not_found(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        engine = InterviewPrepEngine(db_session)
        with pytest.raises(NotFoundError):
            await engine.generate_prep(uuid.uuid4(), user_id)

    @pytest.mark.asyncio
    async def test_get_prep_not_found(
        self, db_session: AsyncSession, user_id: uuid.UUID, sample_app: Application
    ) -> None:
        engine = InterviewPrepEngine(db_session)
        with pytest.raises(NotFoundError):
            await engine.get_prep(sample_app.id, user_id)

    @pytest.mark.asyncio
    @patch("app.interview.prep_engine._build_router")
    async def test_generate_prep_success(
        self,
        mock_build_router: AsyncMock,
        db_session: AsyncSession,
        user_id: uuid.UUID,
        sample_app: Application,
    ) -> None:
        mock_router = AsyncMock()
        mock_router.complete_json = AsyncMock(return_value=MOCK_PREP_RESPONSE)
        mock_build_router.return_value = mock_router

        engine = InterviewPrepEngine(db_session)
        package = await engine.generate_prep(sample_app.id, user_id, stage="technical")

        assert package.application_id == sample_app.id
        assert package.user_id == user_id
        assert package.stage == "technical"
        assert isinstance(package.prep_data, dict)
        assert "company_research" in package.prep_data

    @pytest.mark.asyncio
    @patch("app.interview.prep_engine._build_router")
    async def test_generate_then_get(
        self,
        mock_build_router: AsyncMock,
        db_session: AsyncSession,
        user_id: uuid.UUID,
        sample_app: Application,
    ) -> None:
        mock_router = AsyncMock()
        mock_router.complete_json = AsyncMock(return_value=MOCK_PREP_RESPONSE)
        mock_build_router.return_value = mock_router

        engine = InterviewPrepEngine(db_session)
        created = await engine.generate_prep(sample_app.id, user_id)
        retrieved = await engine.get_prep(sample_app.id, user_id)

        assert retrieved.id == created.id
        assert retrieved.prep_data == created.prep_data

    @pytest.mark.asyncio
    @patch("app.interview.prep_engine._build_router")
    async def test_to_prep_response(
        self,
        mock_build_router: AsyncMock,
        db_session: AsyncSession,
        user_id: uuid.UUID,
        sample_app: Application,
    ) -> None:
        mock_router = AsyncMock()
        mock_router.complete_json = AsyncMock(return_value=MOCK_PREP_RESPONSE)
        mock_build_router.return_value = mock_router

        engine = InterviewPrepEngine(db_session)
        package = await engine.generate_prep(sample_app.id, user_id)
        response = to_prep_response(package)

        assert isinstance(response, ContextualPrepResponse)
        assert isinstance(response.prep_data, ContextualPrepData)
        assert len(response.prep_data.likely_questions) == 2
        assert response.stage == "general"

    @pytest.mark.asyncio
    @patch("app.interview.prep_engine._build_router")
    async def test_generate_prep_llm_failure(
        self,
        mock_build_router: AsyncMock,
        db_session: AsyncSession,
        user_id: uuid.UUID,
        sample_app: Application,
    ) -> None:
        mock_router = AsyncMock()
        mock_router.complete_json = AsyncMock(side_effect=RuntimeError("LLM down"))
        mock_build_router.return_value = mock_router

        engine = InterviewPrepEngine(db_session)
        from app.shared.errors import AppError

        with pytest.raises(AppError):
            await engine.generate_prep(sample_app.id, user_id)


# -- Auto-trigger tests ----------------------------------------------------


class TestAutoTrigger:
    @pytest.mark.asyncio
    @patch("app.pipeline.service.PipelineService._schedule_interview_prep")
    async def test_transition_to_interviewing_triggers_prep(
        self,
        mock_schedule: AsyncMock,
        db_session: AsyncSession,
        user_id: uuid.UUID,
        sample_app: Application,
    ) -> None:
        svc = PipelineService(db_session)
        # saved -> applied
        await svc.transition_status(
            sample_app.id,
            StatusTransition(new_status="applied", change_source="user"),
            user_id,
        )
        # applied -> interviewing
        await svc.transition_status(
            sample_app.id,
            StatusTransition(new_status="interviewing", change_source="user"),
            user_id,
        )

        mock_schedule.assert_called_once_with(sample_app.id, user_id)

    @pytest.mark.asyncio
    @patch("app.pipeline.service.PipelineService._schedule_interview_prep")
    async def test_transition_to_applied_does_not_trigger(
        self,
        mock_schedule: AsyncMock,
        db_session: AsyncSession,
        user_id: uuid.UUID,
        sample_app: Application,
    ) -> None:
        svc = PipelineService(db_session)
        await svc.transition_status(
            sample_app.id,
            StatusTransition(new_status="applied", change_source="user"),
            user_id,
        )
        mock_schedule.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.pipeline.service.PipelineService._schedule_interview_prep")
    async def test_auto_trigger_failure_does_not_block_transition(
        self,
        mock_schedule: AsyncMock,
        db_session: AsyncSession,
        user_id: uuid.UUID,
        sample_app: Application,
    ) -> None:
        mock_schedule.side_effect = RuntimeError("scheduler unavailable")

        svc = PipelineService(db_session)
        # saved -> applied -> interviewing
        await svc.transition_status(
            sample_app.id,
            StatusTransition(new_status="applied", change_source="user"),
            user_id,
        )
        app = await svc.transition_status(
            sample_app.id,
            StatusTransition(new_status="interviewing", change_source="user"),
            user_id,
        )
        # Transition succeeded despite prep failure
        assert app.status == "interviewing"
