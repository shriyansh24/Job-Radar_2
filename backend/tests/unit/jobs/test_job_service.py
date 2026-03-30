from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job
from app.jobs.schemas import JobListParams, JobUpdate
from app.jobs.service import JobService
from app.shared.errors import NotFoundError


@pytest.fixture
async def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
async def sample_job(db_session: AsyncSession, user_id: uuid.UUID) -> Job:
    job = Job(
        id="test-job-001",
        user_id=user_id,
        source="linkedin",
        title="Software Engineer",
        company_name="Test Corp",
        location="Remote",
        remote_type="remote",
        status="new",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.mark.asyncio
async def test_list_jobs_empty(db_session: AsyncSession, user_id: uuid.UUID):
    svc = JobService(db_session)
    result = await svc.list_jobs(JobListParams(), user_id)
    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_list_jobs_with_data(db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job):
    svc = JobService(db_session)
    result = await svc.list_jobs(JobListParams(), user_id)
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == "test-job-001"


@pytest.mark.asyncio
async def test_list_jobs_filter_source(
    db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job
):
    svc = JobService(db_session)
    result = await svc.list_jobs(JobListParams(source="linkedin"), user_id)
    assert result.total == 1

    result = await svc.list_jobs(JobListParams(source="indeed"), user_id)
    assert result.total == 0


@pytest.mark.asyncio
async def test_list_jobs_text_search(
    db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job
):
    svc = JobService(db_session)
    result = await svc.list_jobs(JobListParams(q="Software"), user_id)
    assert result.total == 1

    result = await svc.list_jobs(JobListParams(q="Nonexistent"), user_id)
    assert result.total == 0


@pytest.mark.asyncio
async def test_get_job(db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job):
    svc = JobService(db_session)
    job = await svc.get_job("test-job-001", user_id)
    assert job.title == "Software Engineer"


@pytest.mark.asyncio
async def test_get_job_not_found(db_session: AsyncSession, user_id: uuid.UUID):
    svc = JobService(db_session)
    with pytest.raises(NotFoundError):
        await svc.get_job("nonexistent", user_id)


@pytest.mark.asyncio
async def test_update_job(db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job):
    svc = JobService(db_session)
    updated = await svc.update_job("test-job-001", JobUpdate(is_starred=True), user_id)
    assert updated.is_starred is True


@pytest.mark.asyncio
async def test_delete_job_soft(db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job):
    svc = JobService(db_session)
    await svc.delete_job("test-job-001", user_id)
    # After soft delete, job should not appear in listings
    result = await svc.list_jobs(JobListParams(), user_id)
    assert result.total == 0


@pytest.mark.asyncio
async def test_list_jobs_user_isolation(
    db_session: AsyncSession, user_id: uuid.UUID, sample_job: Job
):
    """Jobs from one user should not be visible to another."""
    other_user = uuid.uuid4()
    svc = JobService(db_session)
    result = await svc.list_jobs(JobListParams(), other_user)
    assert result.total == 0
