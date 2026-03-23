"""Tests for the SQL Pattern Detector (Feature D1)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import column
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.pattern_detector import PatternDetector
from app.jobs.models import Job
from app.pipeline.models import Application
from app.profile.models import UserProfile


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def detector(db_session: AsyncSession) -> PatternDetector:
    return PatternDetector(db_session)


# ---- helpers ----


def _make_job(user_id: uuid.UUID, idx: int, company: str = "Acme") -> Job:
    return Job(
        id=f"pattern-test-{idx}-{uuid.uuid4().hex[:8]}",
        user_id=user_id,
        source="test",
        title=f"Engineer {idx}",
        company_name=company,
        skills_required=["python", "sql", "docker"],
    )


def _make_app(
    user_id: uuid.UUID,
    job: Job,
    status: str = "applied",
    applied_at: datetime | None = None,
) -> Application:
    return Application(
        user_id=user_id,
        job_id=job.id,
        company_name=job.company_name,
        position_title=job.title,
        status=status,
        applied_at=applied_at or datetime.now(timezone.utc) - timedelta(days=30),
    )


# ====================================================================
# Empty DB tests – every method should return empty lists, not errors
# ====================================================================


@pytest.mark.asyncio
async def test_empty_callback_rate(
    detector: PatternDetector, user_id: uuid.UUID
) -> None:
    result = await detector.callback_rate_by_company_size(user_id)
    assert result == []


@pytest.mark.asyncio
async def test_empty_conversion_funnel(
    detector: PatternDetector, user_id: uuid.UUID
) -> None:
    result = await detector.conversion_funnel(user_id)
    assert isinstance(result, list)
    # Funnel always returns all 8 stages even when empty
    assert len(result) == 8
    assert all(r["count"] == 0 for r in result)


@pytest.mark.asyncio
async def test_empty_response_time(
    detector: PatternDetector, user_id: uuid.UUID
) -> None:
    result = await detector.response_time_patterns(user_id)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0]["avg_days_to_response"] == 0.0


def test_elapsed_days_expr_uses_extract_on_postgresql(
    detector: PatternDetector, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(detector, "_dialect_name", lambda: "postgresql")
    expr = detector._elapsed_days_expr(column("first_response_at"), column("applied_at"))
    compiled = str(expr.compile(dialect=postgresql.dialect()))
    assert "EXTRACT" in compiled
    assert "julianday" not in compiled


def test_elapsed_days_expr_uses_julianday_on_sqlite(
    detector: PatternDetector, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(detector, "_dialect_name", lambda: "sqlite")
    expr = detector._elapsed_days_expr(column("first_response_at"), column("applied_at"))
    compiled = str(expr.compile(dialect=sqlite.dialect()))
    assert "julianday" in compiled


@pytest.mark.asyncio
async def test_empty_timing(
    detector: PatternDetector, user_id: uuid.UUID
) -> None:
    result = await detector.best_application_timing(user_id)
    assert result == []


@pytest.mark.asyncio
async def test_empty_ghosting(
    detector: PatternDetector, user_id: uuid.UUID
) -> None:
    result = await detector.company_ghosting_rate(user_id)
    assert result == []


@pytest.mark.asyncio
async def test_empty_skill_gap(
    detector: PatternDetector, user_id: uuid.UUID
) -> None:
    result = await detector.skill_gap_detection(user_id)
    assert result == []


@pytest.mark.asyncio
async def test_empty_get_all_patterns(
    detector: PatternDetector, user_id: uuid.UUID
) -> None:
    result = await detector.get_all_patterns(user_id)
    assert isinstance(result, dict)
    assert "callback_rate_by_company_size" in result
    assert "conversion_funnel" in result
    assert "response_time_patterns" in result
    assert "best_application_timing" in result
    assert "company_ghosting_rate" in result
    assert "skill_gap_detection" in result


# ====================================================================
# Conversion funnel with data
# ====================================================================


@pytest.mark.asyncio
async def test_conversion_funnel_with_data(
    db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    jobs = [_make_job(user_id, i) for i in range(5)]
    db_session.add_all(jobs)
    await db_session.flush()

    apps = [
        _make_app(user_id, jobs[0], status="applied"),
        _make_app(user_id, jobs[1], status="applied"),
        _make_app(user_id, jobs[2], status="screening"),
        _make_app(user_id, jobs[3], status="interviewing"),
        _make_app(user_id, jobs[4], status="offer"),
    ]
    db_session.add_all(apps)
    await db_session.commit()

    detector = PatternDetector(db_session)
    result = await detector.conversion_funnel(user_id)

    counts = {r["stage"]: r["count"] for r in result}
    assert counts["applied"] == 2
    assert counts["screening"] == 1
    assert counts["interviewing"] == 1
    assert counts["offer"] == 1
    assert counts["saved"] == 0


# ====================================================================
# Skill gap detection with data
# ====================================================================


@pytest.mark.asyncio
async def test_skill_gap_detection_with_data(
    db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    # Create a user profile with resume mentioning "python" but not "docker"
    profile = UserProfile(
        user_id=user_id,
        resume_text="Experienced python developer with sql expertise",
    )
    db_session.add(profile)

    # Create 3+ jobs requiring docker (to meet _MIN_SAMPLE)
    jobs = []
    for i in range(4):
        job = _make_job(user_id, i + 100)
        job.skills_required = ["python", "docker", "kubernetes"]
        jobs.append(job)
    db_session.add_all(jobs)
    await db_session.flush()

    apps = [
        _make_app(user_id, j, status="applied") for j in jobs
    ]
    db_session.add_all(apps)
    await db_session.commit()

    detector = PatternDetector(db_session)
    result = await detector.skill_gap_detection(user_id)

    skill_names = [r["skill"] for r in result]
    # docker and kubernetes should be gaps (not in resume)
    assert "docker" in skill_names
    assert "kubernetes" in skill_names
    # python IS in resume, so should NOT be a gap
    assert "python" not in skill_names


# ====================================================================
# Ghosting rate with data
# ====================================================================


@pytest.mark.asyncio
async def test_ghosting_rate_with_data(
    db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    company = "GhostCorp"
    # Create 4 jobs and applications from same company, all still "applied"
    # with applied_at > 14 days ago
    jobs = [_make_job(user_id, i + 200, company=company) for i in range(4)]
    db_session.add_all(jobs)
    await db_session.flush()

    old_date = datetime.now(timezone.utc) - timedelta(days=20)
    apps = [
        _make_app(user_id, j, status="applied", applied_at=old_date)
        for j in jobs
    ]
    db_session.add_all(apps)
    await db_session.commit()

    detector = PatternDetector(db_session)
    result = await detector.company_ghosting_rate(user_id)

    assert len(result) >= 1
    ghost_corp = next((r for r in result if r["company"] == company), None)
    assert ghost_corp is not None
    assert ghost_corp["ghosted"] == 4
    assert ghost_corp["ghosting_rate"] == 100.0


# ====================================================================
# get_all_patterns returns all keys with data
# ====================================================================


@pytest.mark.asyncio
async def test_get_all_patterns_structure(
    db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    detector = PatternDetector(db_session)
    result = await detector.get_all_patterns(user_id)
    expected_keys = {
        "callback_rate_by_company_size",
        "conversion_funnel",
        "response_time_patterns",
        "best_application_timing",
        "company_ghosting_rate",
        "skill_gap_detection",
    }
    assert set(result.keys()) == expected_keys
    # All values are lists
    for v in result.values():
        assert isinstance(v, list)
