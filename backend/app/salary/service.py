"""LLM-powered salary research and offer evaluation.

Ports v1's salary_analyzer logic into v2's service layer, using the
shared ``ModelRouter`` (with automatic fallback) and a 24-hour
``SalaryCache`` to avoid redundant LLM calls.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enrichment.llm_client import LLMClient
from app.nlp.model_router import ModelRouter
from app.salary.models import SalaryCache
from app.salary.schemas import OfferEvalRequest, SalaryResearchRequest

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Prompts (ported from v1 salary_analyzer.py)
# ---------------------------------------------------------------------------

_RESEARCH_PROMPT = """You are a compensation analyst. Research salary data for this role.

JOB TITLE: {job_title}
LOCATION: {location}

Return ONLY valid JSON:
{{
  "p25": <number - 25th percentile annual salary in USD>,
  "p50": <number - median annual salary in USD>,
  "p75": <number - 75th percentile annual salary in USD>,
  "p90": <number - 90th percentile annual salary in USD>,
  "yoe_brackets": [
    {{"years": "0-2", "range": "$X-$Y"}},
    {{"years": "3-5", "range": "$X-$Y"}},
    {{"years": "6-10", "range": "$X-$Y"}},
    {{"years": "10+", "range": "$X-$Y"}}
  ],
  "competing_companies": ["company1", "company2", "company3"]
}}

Base estimates on current market data for the US tech industry. Be realistic.
"""

_OFFER_EVAL_PROMPT = """You are a salary negotiation coach. Evaluate this job offer.

JOB TITLE: {job_title}
LOCATION: {location}
OFFER AMOUNT: ${offer_amount:,.0f}/year

MARKET DATA (if available):
- 25th percentile: {p25}
- Median: {p50}
- 75th percentile: {p75}
- 90th percentile: {p90}

Return ONLY valid JSON:
{{
  "assessment": "Brief assessment of where the offer falls relative to market (2-3 sentences)",
  "counter_offer": <number - suggested counter-offer amount>,
  "walkaway_point": <number - minimum acceptable salary>,
  "talking_points": ["point1", "point2", "point3"],
  "negotiation_script": "A polished 3-4 sentence script the candidate can use to negotiate"
}}
"""

# Cache validity window
_CACHE_TTL = timedelta(hours=24)


def _build_router() -> ModelRouter:
    """Create a ``ModelRouter`` backed by a fresh ``LLMClient``."""
    llm = LLMClient(settings.openrouter_api_key, settings.default_llm_model)
    return ModelRouter(llm)


class SalaryService:
    """Salary research and offer evaluation backed by LLM + DB cache."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Salary research
    # ------------------------------------------------------------------

    async def research_salary(self, request: SalaryResearchRequest, user_id: uuid.UUID) -> dict:
        """Return percentile salary data, YoE brackets, and competing companies.

        Checks ``SalaryCache`` for a hit within the last 24 hours before
        invoking the LLM.
        """
        location = request.location or "United States"

        logger.info(
            "salary.research_salary",
            job_title=request.job_title,
            location=location,
            user_id=str(user_id),
        )

        # ----- 24-hour cache check -----
        cached = await self._get_valid_cache(request.job_title, location)
        if cached is not None:
            logger.info("salary.cache_hit", cache_id=str(cached.id))
            data: dict = cached.market_data  # type: ignore[assignment]
            data["job_title"] = request.job_title
            data["location"] = location
            data["cached"] = True
            return data

        # ----- LLM call via ModelRouter -----
        router = _build_router()
        prompt = _RESEARCH_PROMPT.format(
            job_title=request.job_title,
            location=location,
        )
        messages = [
            {
                "role": "system",
                "content": "Return ONLY valid JSON with realistic salary estimates.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            result = await router.complete_json(
                task="salary",
                messages=messages,
                temperature=0.2,
                max_tokens=1000,
            )
        except RuntimeError:
            logger.exception("salary.research_llm_failed")
            raise
        finally:
            # Clean up the underlying httpx client
            await router._llm.close()

        # ----- Persist to cache -----
        entry = SalaryCache(
            user_id=user_id,
            job_title=request.job_title,
            company_name=request.company_name,
            location=location,
            market_data=result,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        logger.info("salary.cache_stored", cache_id=str(entry.id))

        # Attach display metadata
        result["job_title"] = request.job_title
        result["location"] = location
        result["cached"] = False
        return result

    # ------------------------------------------------------------------
    # Offer evaluation
    # ------------------------------------------------------------------

    async def evaluate_offer(self, request: OfferEvalRequest, user_id: uuid.UUID) -> dict:
        """Evaluate an offer against market data and return negotiation guidance.

        If cached market data exists it is fed into the evaluation prompt
        so the LLM can give a percentile-aware assessment.
        """
        location = request.location or "United States"

        logger.info(
            "salary.evaluate_offer",
            job_title=request.job_title,
            offer=str(request.offered_salary),
            user_id=str(user_id),
        )

        # Try to pull market data from cache for a richer evaluation
        market: dict = {}
        cached = await self._get_valid_cache(request.job_title, location)
        if cached and cached.market_data:
            market = cached.market_data  # type: ignore[assignment]

        def _fmt(val: object) -> str:
            try:
                return f"${float(val):,.0f}" if val else "N/A"
            except (TypeError, ValueError):
                return "N/A"

        prompt = _OFFER_EVAL_PROMPT.format(
            job_title=request.job_title,
            location=location,
            offer_amount=float(request.offered_salary),
            p25=_fmt(market.get("p25")),
            p50=_fmt(market.get("p50")),
            p75=_fmt(market.get("p75")),
            p90=_fmt(market.get("p90")),
        )
        messages = [
            {"role": "system", "content": "Return ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ]

        router = _build_router()
        try:
            result = await router.complete_json(
                task="salary",
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
            )
        except RuntimeError:
            logger.exception("salary.evaluate_offer_llm_failed")
            raise
        finally:
            await router._llm.close()

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_valid_cache(self, job_title: str, location: str) -> SalaryCache | None:
        """Return a cache entry younger than ``_CACHE_TTL``, or ``None``."""
        cutoff = datetime.now(timezone.utc) - _CACHE_TTL

        query = (
            select(SalaryCache)
            .where(
                SalaryCache.job_title == job_title,
                SalaryCache.location == location,
                SalaryCache.created_at >= cutoff,
            )
            .order_by(SalaryCache.created_at.desc())
            .limit(1)
        )
        return await self.db.scalar(query)
