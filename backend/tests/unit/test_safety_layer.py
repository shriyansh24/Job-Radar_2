"""Tests for the SafetyLayer auto-apply checks."""

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
    return "a" * 64  # SHA-256 like


class TestSafetyCheck:
    def test_as_dict(self) -> None:
        c = SafetyCheck(name="test", passed=True, detail="ok")
        d = c.as_dict()
        assert d == {"name": "test", "passed": True, "detail": "ok"}


class TestSafetyResult:
    def test_failed_checks(self) -> None:
        r = SafetyResult(
            passed=False,
            checks=[
                SafetyCheck(name="a", passed=True, detail="ok"),
                SafetyCheck(name="b", passed=False, detail="nope"),
                SafetyCheck(name="c", passed=False, detail="also nope"),
            ],
        )
        assert r.failed_checks == ["b", "c"]

    def test_as_dict(self) -> None:
        r = SafetyResult(passed=True, checks=[])
        d = r.as_dict()
        assert d["passed"] is True
        assert d["checks"] == []
        assert d["failed"] == []


class TestDuplicateCheck:
    @pytest.mark.asyncio
    async def test_no_duplicate_passes(
        self, safety: SafetyLayer, user_id: uuid.UUID, job_id: str, db_session: AsyncSession
    ) -> None:
        check = await safety._check_duplicate(job_id, user_id, db_session)
        assert check.passed is True
        assert check.name == "duplicate"

    @pytest.mark.asyncio
    async def test_existing_application_blocks(
        self, safety: SafetyLayer, user_id: uuid.UUID, job_id: str, db_session: AsyncSession
    ) -> None:
        app = Application(user_id=user_id, job_id=job_id, status="applied")
        db_session.add(app)
        await db_session.flush()

        check = await safety._check_duplicate(job_id, user_id, db_session)
        assert check.passed is False
        assert "Already applied" in check.detail


class TestDailyLimit:
    @pytest.mark.asyncio
    async def test_under_limit_passes(
        self, safety: SafetyLayer, user_id: uuid.UUID, db_session: AsyncSession
    ) -> None:
        check = await safety._check_daily_limit(user_id, db_session)
        assert check.passed is True

    @pytest.mark.asyncio
    async def test_at_limit_blocks(
        self, user_id: uuid.UUID, db_session: AsyncSession
    ) -> None:
        layer = SafetyLayer(daily_limit=3, known_ats_types={"lever"})

        # Add 3 runs today
        for _ in range(3):
            run = AutoApplyRun(
                user_id=user_id,
                status="filled",
                started_at=datetime.now(UTC),
            )
            db_session.add(run)
        await db_session.flush()

        check = await layer._check_daily_limit(user_id, db_session)
        assert check.passed is False
        assert "3/3" in check.detail


class TestATSHourlyLimit:
    @pytest.mark.asyncio
    async def test_under_hourly_limit_passes(
        self, safety: SafetyLayer, user_id: uuid.UUID, db_session: AsyncSession
    ) -> None:
        check = await safety._check_ats_hourly_limit(user_id, "lever", db_session)
        assert check.passed is True

    @pytest.mark.asyncio
    async def test_lever_hourly_limit_blocks(
        self, safety: SafetyLayer, user_id: uuid.UUID, db_session: AsyncSession
    ) -> None:
        # Lever limit is 5/hour — add 5 runs
        for _ in range(5):
            run = AutoApplyRun(
                user_id=user_id,
                ats_provider="lever",
                status="filled",
                started_at=datetime.now(UTC),
            )
            db_session.add(run)
        await db_session.flush()

        check = await safety._check_ats_hourly_limit(user_id, "lever", db_session)
        assert check.passed is False
        assert "lever: 5/5" in check.detail

    @pytest.mark.asyncio
    async def test_old_runs_not_counted(
        self, safety: SafetyLayer, user_id: uuid.UUID, db_session: AsyncSession
    ) -> None:
        # Add runs from 2 hours ago
        for _ in range(5):
            run = AutoApplyRun(
                user_id=user_id,
                ats_provider="lever",
                status="filled",
                started_at=datetime.now(UTC) - timedelta(hours=2),
            )
            db_session.add(run)
        await db_session.flush()

        check = await safety._check_ats_hourly_limit(user_id, "lever", db_session)
        assert check.passed is True


class TestCompanyCooldown:
    @pytest.mark.asyncio
    async def test_no_recent_apps_passes(
        self, safety: SafetyLayer, user_id: uuid.UUID, db_session: AsyncSession
    ) -> None:
        check = await safety._check_company_cooldown(user_id, "Acme Corp", db_session)
        assert check.passed is True

    @pytest.mark.asyncio
    async def test_recent_app_blocks(
        self, safety: SafetyLayer, user_id: uuid.UUID, db_session: AsyncSession
    ) -> None:
        app = Application(
            user_id=user_id,
            company_name="acme corp",
            status="applied",
        )
        db_session.add(app)
        await db_session.flush()

        check = await safety._check_company_cooldown(user_id, "Acme Corp", db_session)
        assert check.passed is False
        assert "1 roles" in check.detail


class TestBlacklist:
    def test_no_blacklist_passes(self, safety: SafetyLayer) -> None:
        check = safety._check_blacklist("Acme", "Engineer", [], [])
        assert check.passed is True

    def test_blacklisted_company_blocks(self, safety: SafetyLayer) -> None:
        check = safety._check_blacklist("Evil Corp", "Engineer", ["evil corp"], [])
        assert check.passed is False
        assert "blacklisted" in check.detail.lower()

    def test_blacklisted_keyword_blocks(self, safety: SafetyLayer) -> None:
        check = safety._check_blacklist("Acme", "Senior Intern", [], ["intern"])
        assert check.passed is False
        assert "intern" in check.detail.lower()

    def test_case_insensitive(self, safety: SafetyLayer) -> None:
        check = safety._check_blacklist("EVIL CORP", "Engineer", ["evil corp"], [])
        assert check.passed is False


class TestBudget:
    def test_under_budget_passes(self, safety: SafetyLayer) -> None:
        check = safety._check_budget(5.0)
        assert check.passed is True

    def test_over_budget_blocks(self, safety: SafetyLayer) -> None:
        check = safety._check_budget(15.0)
        assert check.passed is False
        assert "$15.00" in check.detail


class TestFreshness:
    def test_fresh_posting_passes(self, safety: SafetyLayer) -> None:
        check = safety._check_freshness(datetime.now(UTC) - timedelta(days=5))
        assert check.passed is True

    def test_stale_posting_blocks(self, safety: SafetyLayer) -> None:
        check = safety._check_freshness(datetime.now(UTC) - timedelta(days=45))
        assert check.passed is False
        assert "45 days" in check.detail

    def test_no_first_seen_passes(self, safety: SafetyLayer) -> None:
        check = safety._check_freshness(None)
        assert check.passed is True

    def test_naive_datetime_handled(self, safety: SafetyLayer) -> None:
        naive = datetime.now() - timedelta(days=5)  # noqa: DTZ005
        check = safety._check_freshness(naive)
        assert check.passed is True


class TestFirstTimeATS:
    def test_known_ats_passes(self, safety: SafetyLayer) -> None:
        check = safety._check_first_time_ats("lever")
        assert check.passed is True

    def test_unknown_ats_blocks(self, safety: SafetyLayer) -> None:
        check = safety._check_first_time_ats("taleo")
        assert check.passed is False
        assert "requires confirmation" in check.detail.lower()

    def test_no_ats_passes(self, safety: SafetyLayer) -> None:
        check = safety._check_first_time_ats(None)
        assert check.passed is True

    def test_mark_ats_known(self, safety: SafetyLayer) -> None:
        assert safety._check_first_time_ats("taleo").passed is False
        safety.mark_ats_known("taleo")
        assert safety._check_first_time_ats("taleo").passed is True


class TestFullSafetyCheck:
    @pytest.mark.asyncio
    async def test_all_pass(
        self, safety: SafetyLayer, user_id: uuid.UUID, job_id: str, db_session: AsyncSession
    ) -> None:
        result = await safety.check_safety(
            job_id=job_id,
            user_id=user_id,
            db=db_session,
            ats_provider="lever",
            company_name="Acme Corp",
            first_seen_at=datetime.now(UTC) - timedelta(days=2),
        )
        assert result.passed is True
        assert len(result.failed_checks) == 0

    @pytest.mark.asyncio
    async def test_multiple_failures(
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
        failed = result.failed_checks
        assert "daily_limit" in failed
        assert "blacklist" in failed
        assert "freshness" in failed
        assert "first_time_ats" in failed

    @pytest.mark.asyncio
    async def test_duplicate_blocks(
        self, safety: SafetyLayer, user_id: uuid.UUID, job_id: str, db_session: AsyncSession
    ) -> None:
        app = Application(user_id=user_id, job_id=job_id, status="applied")
        db_session.add(app)
        await db_session.flush()

        result = await safety.check_safety(
            job_id=job_id,
            user_id=user_id,
            db=db_session,
            ats_provider="lever",
        )
        assert result.passed is False
        assert "duplicate" in result.failed_checks
