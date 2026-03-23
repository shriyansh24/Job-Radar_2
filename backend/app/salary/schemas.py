from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------


class YoEBracket(BaseModel):
    years: str
    range: str


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class SalaryResearchRequest(BaseModel):
    job_title: str
    company_name: str | None = None
    location: str | None = None


class OfferEvalRequest(BaseModel):
    job_title: str
    company_name: str | None = None
    location: str | None = None
    offered_salary: Decimal
    offered_benefits: list[str] = []


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class SalaryResearchResponse(BaseModel):
    job_title: str
    location: str | None = None
    p25: Decimal | None = None
    p50: Decimal | None = None
    p75: Decimal | None = None
    p90: Decimal | None = None
    yoe_brackets: list[YoEBracket] = []
    competing_companies: list[str] = []
    currency: str = "USD"
    cached: bool = False


class OfferEvalResponse(BaseModel):
    assessment: str
    counter_offer: Decimal | None = None
    walkaway_point: Decimal | None = None
    talking_points: list[str] = []
    negotiation_script: str = ""


# ---------------------------------------------------------------------------
# Salary Brief (F2 - Negotiation Intelligence)
# ---------------------------------------------------------------------------


class MarketRange(BaseModel):
    p25: Decimal | None = None
    p50: Decimal | None = None
    p75: Decimal | None = None
    p90: Decimal | None = None
    currency: str = "USD"
    source_description: str = ""


class NegotiationPoint(BaseModel):
    category: str
    point: str
    strength: str = "medium"


class SalaryBriefRequest(BaseModel):
    competing_offers: list[str] = []
    years_experience: int | None = None
    key_skills: list[str] = []


class SalaryBrief(BaseModel):
    job_id: str
    job_title: str
    company_name: str | None = None
    location: str | None = None
    market_range: MarketRange
    company_avg_offer: Decimal | None = None
    leverage_points: list[NegotiationPoint] = []
    talking_points: list[str] = []
    counter_offer_template: str = ""
    risk_assessment: str = ""
    cached: bool = False
