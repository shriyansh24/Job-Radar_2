from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auto_apply.models import AutoApplyRun
from app.auto_apply.safety import SafetyCheck, SafetyLayer, SafetyResult
from app.pipeline.models import Application


@pytest.fixture
def safety() -> SafetyLayer:
    return SafetyLayer(known_ats_types={"lever", "greenhouse"})


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def job_id() -> str:
    return "a" * 64


class TestSafetyCheck:
    def test_as_dict(self) -> None:
        check = SafetyCheck(name="test", passed=True, detail="ok")
        assert check.as_dict() == {"name": "test", "passed": True, "detail": "ok"}


class TestSafetyResult:
    def test_failed_checks(self) -> None:
        result = SafetyResult(
            passed=False,
            checks=[
                SafetyCheck(name="a", passed=True, detail="ok"),
                SafetyCheck(name="b", passed=False, detail="nope"),
                SafetyCheck(name="c", passed=False, detail="also nope"),
            ],
        )
        assert result.failed_checks == ["b", "c"]


class TestSafetyLayer:
    @pytest.mark.asyncio
    async def test_duplicate_check_blocks_existing_application(
        self, safety: SafetyLayer, user_id: uuid.UUID, job_id: str, db_session: AsyncSession
    ) -> None:
        db_session.add(Application(user_id=user_id, job_id=job_id, status="applied"))
        await db_session.flush()

        check = await safety._check_duplicate(job_id, user_id, db_session)
        assert check.passed is False
        assert "Already applied" in check.detail

    @pytest.mark.asyncio
    async def test_daily_limit_blocks_at_limit(
        self, user_id: uuid.UUID, db_session: AsyncSession
    ) -> None:
        layer = SafetyLayer(daily_limit=3, known_ats_types={"lever"})
        for _ in range(3):
            db_session.add(
                AutoApplyRun(user_id=user_id, status="filled", started_at=datetime.now(UTC))
            )
        await db_session.flush()

        check = await layer._check_daily_limit(user_id, db_session)
        assert check.passed is False
        assert "3/3" in check.detail

    @pytest.mark.asyncio
    async def test_hourly_limit_ignores_old_runs(
        self, safety: SafetyLayer, user_id: uuid.UUID, db_session: AsyncSession
    ) -> None:
        for _ in range(5):
            db_session.add(
                AutoApplyRun(
                    user_id=user_id,
                    ats_provider="lever",
                    status="filled",
                    started_at=datetime.now(UTC) - timedelta(hours=2),
                )
            )
        await db_session.flush()

        check = await safety._check_ats_hourly_limit(user_id, "lever", db_session)
        assert check.passed is True

    def test_blacklist_blocks_company_and_keyword(self, safety: SafetyLayer) -> None:
        company_check = safety._check_blacklist("Evil Corp", "Engineer", ["evil corp"], [])
        keyword_check = safety._check_blacklist("Acme", "Senior Intern", [], ["intern"])
        assert company_check.passed is False
        assert keyword_check.passed is False

    def test_freshness_and_first_time_ats(self, safety: SafetyLayer) -> None:
        stale = safety._check_freshness(datetime.now(UTC) - timedelta(days=45))
        first_time = safety._check_first_time_ats("taleo")
        assert stale.passed is False
        assert first_time.passed is False

    @pytest.mark.asyncio
    async def test_full_safety_check_accumulates_failures(
        self, user_id: uuid.UUID, job_id: str, db_session: AsyncSession
    ) -> None:
        layer = SafetyLayer(daily_limit=0, known_ats_types=set())
        result = await layer.check_safety(
            job_id=job_id,
            user_id=user_id,
            db=db_session,
            ats_provider="taleo",
            company_name="Evil Corp",
            blacklisted_companies=["evil corp"],
            first_seen_at=datetime.now(UTC) - timedelta(days=60),
        )
        assert result.passed is False
        assert "daily_limit" in result.failed_checks
        assert "blacklist" in result.failed_checks
        assert "freshness" in result.failed_checks
        assert "first_time_ats" in result.failed_checks
