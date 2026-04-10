"""Unit tests for CanonicalJobService using in-memory SQLite."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Register canonical_jobs tables with Base.metadata
from app.canonical_jobs import models as canonical_job_models
from app.canonical_jobs.service import STALE_THRESHOLD_DAYS, CanonicalJobService
from app.shared.errors import NotFoundError

CanonicalJob = canonical_job_models.CanonicalJob

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_canonical_job(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    title: str = "Software Engineer",
    company_name: str = "Acme",
    status: str = "open",
    is_stale: bool = False,
    last_refreshed_at: datetime | None = None,
) -> CanonicalJob:
    if last_refreshed_at is None:
        last_refreshed_at = datetime.now(timezone.utc)
    job = CanonicalJob(
        user_id=user_id,
        title=title,
        company_name=company_name,
        status=status,
        is_stale=is_stale,
        last_refreshed_at=last_refreshed_at,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


# ---------------------------------------------------------------------------
# list_canonical_jobs
# ---------------------------------------------------------------------------


class TestListCanonicalJobs:
    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self, db_session: AsyncSession):
        svc = CanonicalJobService(db_session)
        result = await svc.list_canonical_jobs(uuid.uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_scoped_to_user(self, db_session: AsyncSession):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        await _make_canonical_job(db_session, user_a)
        await _make_canonical_job(db_session, user_b)

        svc = CanonicalJobService(db_session)
        result = await svc.list_canonical_jobs(user_a)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_filter_by_status(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        await _make_canonical_job(db_session, user_id, status="open")
        await _make_canonical_job(db_session, user_id, status="closed")

        svc = CanonicalJobService(db_session)
        result = await svc.list_canonical_jobs(user_id, status="closed")
        assert len(result) == 1
        assert result[0].status == "closed"

    @pytest.mark.asyncio
    async def test_filter_stale_only(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        await _make_canonical_job(db_session, user_id, is_stale=False)
        await _make_canonical_job(db_session, user_id, is_stale=True)

        svc = CanonicalJobService(db_session)
        result = await svc.list_canonical_jobs(user_id, stale_only=True)
        assert len(result) == 1
        assert result[0].is_stale is True


# ---------------------------------------------------------------------------
# get_canonical_job
# ---------------------------------------------------------------------------


class TestGetCanonicalJob:
    @pytest.mark.asyncio
    async def test_returns_own_job(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        job = await _make_canonical_job(db_session, user_id, title="ML Engineer")
        svc = CanonicalJobService(db_session)

        result = await svc.get_canonical_job(job.id, user_id)
        assert result.title == "ML Engineer"

    @pytest.mark.asyncio
    async def test_wrong_user_raises_not_found(self, db_session: AsyncSession):
        owner = uuid.uuid4()
        other = uuid.uuid4()
        job = await _make_canonical_job(db_session, owner)
        svc = CanonicalJobService(db_session)

        with pytest.raises(NotFoundError):
            await svc.get_canonical_job(job.id, other)

    @pytest.mark.asyncio
    async def test_missing_id_raises_not_found(self, db_session: AsyncSession):
        svc = CanonicalJobService(db_session)
        with pytest.raises(NotFoundError):
            await svc.get_canonical_job(uuid.uuid4(), uuid.uuid4())


# ---------------------------------------------------------------------------
# close_job / reactivate_job
# ---------------------------------------------------------------------------


class TestCloseAndReactivate:
    @pytest.mark.asyncio
    async def test_close_sets_status_closed(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        job = await _make_canonical_job(db_session, user_id, status="open")
        svc = CanonicalJobService(db_session)

        closed = await svc.close_job(job.id, user_id)
        assert closed.status == "closed"

    @pytest.mark.asyncio
    async def test_reactivate_sets_status_open_and_clears_stale(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        job = await _make_canonical_job(db_session, user_id, status="closed", is_stale=True)
        svc = CanonicalJobService(db_session)

        active = await svc.reactivate_job(job.id, user_id)
        assert active.status == "open"
        assert active.is_stale is False


# ---------------------------------------------------------------------------
# run_staleness_sweep
# ---------------------------------------------------------------------------


class TestStalenessSweep:
    @pytest.mark.asyncio
    async def test_marks_old_open_jobs_as_stale(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        old_date = datetime.now(timezone.utc) - timedelta(days=STALE_THRESHOLD_DAYS + 1)
        await _make_canonical_job(
            db_session, user_id, status="open", is_stale=False, last_refreshed_at=old_date
        )

        svc = CanonicalJobService(db_session)
        count = await svc.run_staleness_sweep(user_id)
        assert count == 1

    @pytest.mark.asyncio
    async def test_does_not_mark_recent_jobs_stale(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        recent_date = datetime.now(timezone.utc) - timedelta(days=1)
        await _make_canonical_job(
            db_session, user_id, status="open", is_stale=False, last_refreshed_at=recent_date
        )

        svc = CanonicalJobService(db_session)
        count = await svc.run_staleness_sweep(user_id)
        assert count == 0

    @pytest.mark.asyncio
    async def test_already_stale_jobs_not_counted_twice(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        old_date = datetime.now(timezone.utc) - timedelta(days=STALE_THRESHOLD_DAYS + 1)
        await _make_canonical_job(
            db_session, user_id, status="open", is_stale=True, last_refreshed_at=old_date
        )

        svc = CanonicalJobService(db_session)
        count = await svc.run_staleness_sweep(user_id)
        assert count == 0

    @pytest.mark.asyncio
    async def test_closed_jobs_not_swept(self, db_session: AsyncSession):
        user_id = uuid.uuid4()
        old_date = datetime.now(timezone.utc) - timedelta(days=STALE_THRESHOLD_DAYS + 1)
        await _make_canonical_job(
            db_session, user_id, status="closed", is_stale=False, last_refreshed_at=old_date
        )

        svc = CanonicalJobService(db_session)
        count = await svc.run_staleness_sweep(user_id)
        assert count == 0
