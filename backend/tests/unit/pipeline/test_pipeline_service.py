from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job
from app.pipeline.models import Application
from app.pipeline.schemas import ApplicationCreate, StatusTransition
from app.pipeline.service import PipelineService
from app.shared.errors import NotFoundError, ValidationError


@pytest.fixture
async def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
async def sample_job(db_session: AsyncSession, user_id: uuid.UUID) -> Job:
    job = Job(
        id="pipeline-test-job",
        user_id=user_id,
        source="test",
        title="Backend Engineer",
        company_name="Pipeline Corp",
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest.fixture
async def sample_app(db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job) -> Application:
    svc = PipelineService(db_session)
    return await svc.create_application(
        ApplicationCreate(
            job_id=sample_job.id,
            company_name="Pipeline Corp",
            position_title="Backend Engineer",
            source="manual",
        ),
        user_id,
    )


@pytest.mark.asyncio
async def test_create_application(db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job):
    svc = PipelineService(db_session)
    app = await svc.create_application(
        ApplicationCreate(
            job_id=sample_job.id,
            company_name="Pipeline Corp",
            position_title="Backend Engineer",
            source="manual",
        ),
        user_id,
    )
    assert app.status == "saved"
    assert app.company_name == "Pipeline Corp"


@pytest.mark.asyncio
async def test_list_applications(
    db_session: AsyncSession, user_id: uuid.UUID, sample_app: Application
):
    svc = PipelineService(db_session)
    result = await svc.list_applications(user_id)
    assert result.total == 1


@pytest.mark.asyncio
async def test_transition_saved_to_applied(
    db_session: AsyncSession, user_id: uuid.UUID, sample_app: Application
):
    svc = PipelineService(db_session)
    app = await svc.transition_status(
        sample_app.id,
        StatusTransition(new_status="applied", change_source="user"),
        user_id,
    )
    assert app.status == "applied"
    assert app.applied_at is not None


@pytest.mark.asyncio
async def test_transition_applied_to_screening(
    db_session: AsyncSession, user_id: uuid.UUID, sample_app: Application
):
    svc = PipelineService(db_session)
    # First: saved -> applied
    await svc.transition_status(
        sample_app.id,
        StatusTransition(new_status="applied", change_source="user"),
        user_id,
    )
    # Then: applied -> screening
    app = await svc.transition_status(
        sample_app.id,
        StatusTransition(new_status="screening", change_source="system"),
        user_id,
    )
    assert app.status == "screening"


@pytest.mark.asyncio
async def test_invalid_transition(
    db_session: AsyncSession, user_id: uuid.UUID, sample_app: Application
):
    svc = PipelineService(db_session)
    # saved -> offer is not valid
    with pytest.raises(ValidationError):
        await svc.transition_status(
            sample_app.id,
            StatusTransition(new_status="offer", change_source="user"),
            user_id,
        )


@pytest.mark.asyncio
async def test_invalid_status(
    db_session: AsyncSession, user_id: uuid.UUID, sample_app: Application
):
    svc = PipelineService(db_session)
    with pytest.raises(ValidationError):
        await svc.transition_status(
            sample_app.id,
            StatusTransition(new_status="nonexistent", change_source="user"),
            user_id,
        )


@pytest.mark.asyncio
async def test_full_pipeline_flow(
    db_session: AsyncSession, user_id: uuid.UUID, sample_app: Application
):
    """Test complete flow: saved -> applied -> screening -> interviewing -> offer -> accepted."""
    svc = PipelineService(db_session)
    transitions = ["applied", "screening", "interviewing", "offer", "accepted"]
    for status in transitions:
        app = await svc.transition_status(
            sample_app.id,
            StatusTransition(new_status=status, change_source="user"),
            user_id,
        )
        assert app.status == status


@pytest.mark.asyncio
async def test_get_history(db_session: AsyncSession, user_id: uuid.UUID, sample_app: Application):
    svc = PipelineService(db_session)
    await svc.transition_status(
        sample_app.id,
        StatusTransition(new_status="applied", change_source="user"),
        user_id,
    )
    history = await svc.get_history(sample_app.id, user_id)
    # Initial "saved" entry + "applied" transition = 2 entries
    assert len(history) == 2
    assert history[0].new_status == "saved"
    assert history[1].new_status == "applied"


@pytest.mark.asyncio
async def test_pipeline_view(
    db_session: AsyncSession, user_id: uuid.UUID, sample_app: Application
):
    svc = PipelineService(db_session)
    view = await svc.get_pipeline_view(user_id)
    assert len(view.saved) == 1
    assert len(view.applied) == 0


@pytest.mark.asyncio
async def test_get_application_not_found(db_session: AsyncSession, user_id: uuid.UUID):
    svc = PipelineService(db_session)
    with pytest.raises(NotFoundError):
        await svc.get_application(uuid.uuid4(), user_id)
