"""Unit tests for SourceHealthService using in-memory SQLite."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.errors import NotFoundError
from app.source_health.service import SourceHealthService

# ---------------------------------------------------------------------------
# list_sources
# ---------------------------------------------------------------------------


class TestListSources:
    @pytest.mark.asyncio
    async def test_empty_db_returns_empty_list(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        result = await svc.list_sources()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_sources_after_recording_checks(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        await svc.record_check("greenhouse", "success", 42)
        await svc.record_check("lever", "success", 10)

        result = await svc.list_sources()
        names = [s.source_name for s in result]
        assert "greenhouse" in names
        assert "lever" in names


# ---------------------------------------------------------------------------
# record_check — success path
# ---------------------------------------------------------------------------


class TestRecordCheck:
    @pytest.mark.asyncio
    async def test_creates_registry_entry_on_first_check(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        await svc.record_check("ashby", "success", 5)

        sources = await svc.list_sources()
        assert len(sources) == 1
        assert sources[0].source_name == "ashby"

    @pytest.mark.asyncio
    async def test_success_sets_healthy_state(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        await svc.record_check("myats", "success", 20)

        sources = await svc.list_sources()
        assert sources[0].health_state == "healthy"
        assert sources[0].failure_count == 0

    @pytest.mark.asyncio
    async def test_failure_sets_degraded_state(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        await svc.record_check("badats", "failure", 0, error="timeout")

        sources = await svc.list_sources()
        assert sources[0].health_state == "degraded"
        assert sources[0].failure_count == 1

    @pytest.mark.asyncio
    async def test_success_after_failure_resets_failure_count(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        await svc.record_check("flaky", "failure", 0, error="timeout")
        await svc.record_check("flaky", "success", 10)

        sources = await svc.list_sources()
        assert sources[0].health_state == "healthy"
        assert sources[0].failure_count == 0

    @pytest.mark.asyncio
    async def test_accumulates_total_jobs_found(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        await svc.record_check("workday", "success", 30)
        await svc.record_check("workday", "success", 20)

        sources = await svc.list_sources()
        assert sources[0].total_jobs_found == 50

    @pytest.mark.asyncio
    async def test_multiple_failures_increments_count(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        await svc.record_check("unstable", "failure", 0)
        await svc.record_check("unstable", "failure", 0)
        await svc.record_check("unstable", "failure", 0)

        sources = await svc.list_sources()
        assert sources[0].failure_count == 3

    @pytest.mark.asyncio
    async def test_reuses_existing_registry_entry(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        await svc.record_check("lever", "success", 5)
        await svc.record_check("lever", "success", 7)

        sources = await svc.list_sources()
        # Should be one entry, not two
        lever_sources = [s for s in sources if s.source_name == "lever"]
        assert len(lever_sources) == 1


# ---------------------------------------------------------------------------
# get_source_health
# ---------------------------------------------------------------------------


class TestGetSourceHealth:
    @pytest.mark.asyncio
    async def test_returns_source_and_logs(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        await svc.record_check("lever", "success", 10)
        await svc.record_check("lever", "failure", 0, error="503")

        sources = await svc.list_sources()
        source_id = sources[0].id

        source, logs = await svc.get_source_health(source_id)
        assert source.source_name == "lever"
        assert len(logs) == 2
        statuses = {log.check_status for log in logs}
        assert "success" in statuses
        assert "failure" in statuses

    @pytest.mark.asyncio
    async def test_missing_source_id_raises_not_found(self, db_session: AsyncSession):
        svc = SourceHealthService(db_session)
        with pytest.raises(NotFoundError):
            await svc.get_source_health(uuid.uuid4())
