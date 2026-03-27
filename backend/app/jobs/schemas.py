from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.enrichment.freshness import compute_freshness_score


class JobBase(BaseModel):
    title: str
    company_name: str | None = None
    location: str | None = None
    remote_type: str | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None

    @field_validator("salary_min", "salary_max", mode="before")
    @classmethod
    def clean_nan_salary(cls, v: object) -> Decimal | None:
        if v is None:
            return None
        try:
            d = Decimal(str(v))
            if d.is_nan() or d.is_infinite():
                return None
            return d
        except (InvalidOperation, ValueError, TypeError):
            return None

    experience_level: str | None = None
    job_type: str | None = None


class JobResponse(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    source_url: str | None = None
    company_domain: str | None = None
    company_logo_url: str | None = None
    location_city: str | None = None
    location_state: str | None = None
    location_country: str | None = None
    salary_period: str | None = None
    salary_currency: str = "USD"
    description_markdown: str | None = None
    summary_ai: str | None = None
    skills_required: list[str] = []
    skills_nice_to_have: list[str] = []
    tech_stack: list[str] = []
    red_flags: list[str] = []
    green_flags: list[str] = []
    match_score: Decimal | None = None
    tfidf_score: Decimal | None = None
    freshness_score: float | None = None
    status: str
    is_starred: bool
    is_enriched: bool
    is_hidden: bool = False
    posted_at: datetime | None = None
    scraped_at: datetime
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_freshness_score(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("freshness_score") is None:
                data = dict(data)
                data["freshness_score"] = _derive_freshness_score(data)
            return data

        if getattr(data, "freshness_score", None) is None:
            freshness_score = _derive_freshness_score(data)
            if freshness_score is not None:
                setattr(data, "freshness_score", freshness_score)
        return data


class JobListParams(BaseModel):
    q: str | None = None
    source: str | None = None
    remote_type: str | None = None
    experience_level: str | None = None
    job_type: str | None = None
    min_match_score: float | None = None
    status: str | None = None
    is_starred: bool | None = None
    sort_by: str = "scraped_at"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 50


class JobUpdate(BaseModel):
    status: str | None = None
    is_starred: bool | None = None
    is_hidden: bool | None = None


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 20


class JobExportRequest(BaseModel):
    format: str = "json"
    filters: JobListParams | None = None


def _derive_freshness_score(data: Any) -> float | None:
    """Best-effort freshness score for API responses when the model lacks a stored value."""
    if isinstance(data, dict) and data.get("freshness_score") is not None:
        return float(data["freshness_score"])

    first_seen_at = getattr(data, "first_seen_at", None)
    last_seen_at = getattr(data, "last_seen_at", None)
    scraped_at = getattr(data, "scraped_at", None)
    anchor = first_seen_at or last_seen_at or scraped_at
    if anchor is None:
        return None

    try:
        return compute_freshness_score(anchor)
    except Exception:
        return None
