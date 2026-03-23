from __future__ import annotations

import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.salary.schemas import (
    MarketRange,
    NegotiationPoint,
    SalaryBrief,
    SalaryBriefRequest,
)
from app.salary.service import SalaryService


def _mock_job(
    job_id: str = "abc123",
    title: str = "Software Engineer",
    company_name: str = "Acme Corp",
    location: str = "San Francisco, CA",
    company_domain: str = "acme.com",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=job_id,
        title=title,
        company_name=company_name,
        location=location,
        company_domain=company_domain,
        summary_ai="Build scalable systems",
        description_clean="We are looking for a Software Engineer",
    )


def _build_service(
    *,
    scalar_side_effect: list | None = None,
    scalar_return: object = None,
) -> tuple[SalaryService, MagicMock]:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    if scalar_side_effect is not None:
        db.scalar = AsyncMock(side_effect=scalar_side_effect)
    else:
        db.scalar = AsyncMock(return_value=scalar_return)

    service = SalaryService(db)
    return service, db


@pytest.mark.asyncio
async def test_generate_brief_returns_brief():
    user_id = uuid.uuid4()
    job = _mock_job()
    # First scalar call: Job lookup
    # Second scalar call: Company lookup (returns None)
    # Third scalar call: cache check (returns None)
    # Fourth scalar call: cache check inside research_salary (returns None)
    service, db = _build_service(
        scalar_side_effect=[job, None, None, None]
    )

    mock_router = MagicMock()
    # First call: research_salary LLM call
    # Second call: brief generation LLM call
    mock_router.complete_json = AsyncMock(
        side_effect=[
            {
                "p25": 120000,
                "p50": 145000,
                "p75": 170000,
                "p90": 195000,
                "yoe_brackets": [],
                "competing_companies": [],
            },
            {
                "leverage_points": [
                    {"category": "skills", "point": "Strong Python", "strength": "high"}
                ],
                "talking_points": ["You have strong skills", "Market is hot"],
                "counter_offer_template": "I appreciate the offer...",
                "risk_assessment": "Low risk to negotiate.",
            },
        ]
    )
    mock_router._llm = MagicMock()
    mock_router._llm.close = AsyncMock()

    with patch("app.salary.service._build_router", return_value=mock_router):
        brief = await service.generate_brief(
            "abc123",
            user_id,
            SalaryBriefRequest(key_skills=["Python", "FastAPI"]),
        )

    assert isinstance(brief, SalaryBrief)
    assert brief.job_id == "abc123"
    assert brief.job_title == "Software Engineer"
    assert brief.company_name == "Acme Corp"
    assert len(brief.leverage_points) == 1
    assert brief.leverage_points[0].category == "skills"
    assert len(brief.talking_points) == 2
    assert brief.counter_offer_template == "I appreciate the offer..."
    assert "jobs.user_id" in str(db.scalar.await_args_list[0].args[0])


@pytest.mark.asyncio
async def test_generate_brief_job_not_found():
    user_id = uuid.uuid4()
    service, db = _build_service(scalar_return=None)

    with pytest.raises(Exception) as exc_info:
        await service.generate_brief("nonexistent", user_id)

    assert "not found" in str(exc_info.value.detail).lower()
    assert "jobs.user_id" in str(db.scalar.await_args_list[0].args[0])


@pytest.mark.asyncio
async def test_generate_brief_llm_failure():
    job = _mock_job()
    service, db = _build_service(
        scalar_side_effect=[job, None, None, None]
    )

    mock_router = MagicMock()
    # research_salary succeeds, brief generation fails
    mock_router.complete_json = AsyncMock(
        side_effect=[
            {"p25": 120000, "p50": 145000, "p75": 170000, "p90": 195000},
            RuntimeError("LLM down"),
        ]
    )
    mock_router._llm = MagicMock()
    mock_router._llm.close = AsyncMock()

    with patch("app.salary.service._build_router", return_value=mock_router):
        with pytest.raises(Exception) as exc_info:
            await service.generate_brief("abc123", uuid.uuid4())

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_generate_brief_empty_llm_response():
    job = _mock_job()
    service, db = _build_service(
        scalar_side_effect=[job, None, None, None]
    )

    mock_router = MagicMock()
    mock_router.complete_json = AsyncMock(
        side_effect=[
            {"p25": 120000, "p50": 145000, "p75": 170000, "p90": 195000},
            {},
        ]
    )
    mock_router._llm = MagicMock()
    mock_router._llm.close = AsyncMock()

    with patch("app.salary.service._build_router", return_value=mock_router):
        with pytest.raises(Exception) as exc_info:
            await service.generate_brief("abc123", uuid.uuid4())

    assert exc_info.value.status_code == 502


def test_salary_brief_schema():
    brief = SalaryBrief(
        job_id="test123",
        job_title="Engineer",
        market_range=MarketRange(p50=Decimal("150000")),
        leverage_points=[
            NegotiationPoint(category="skills", point="test", strength="high")
        ],
        talking_points=["point1"],
    )
    assert brief.job_id == "test123"
    assert brief.market_range.p50 == Decimal("150000")
    assert brief.leverage_points[0].strength == "high"


def test_market_range_defaults():
    mr = MarketRange()
    assert mr.currency == "USD"
    assert mr.p25 is None
    assert mr.source_description == ""


def test_negotiation_point_defaults():
    np = NegotiationPoint(category="market", point="High demand")
    assert np.strength == "medium"
