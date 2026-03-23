from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_jobs: int = 0
    total_applications: int = 0
    total_interviews: int = 0
    total_offers: int = 0
    applications_by_status: dict[str, int] = {}
    response_rate: float = 0.0
    avg_days_to_response: float = 0.0
    jobs_scraped_today: int = 0
    enriched_jobs: int = 0


class DailyStats(BaseModel):
    date: date
    jobs_scraped: int = 0
    applications: int = 0


class SourceStats(BaseModel):
    source: str
    total_jobs: int = 0
    quality_score: float = 0.0
    avg_match_score: float | None = None


class SkillStats(BaseModel):
    skill: str
    count: int = 0
    percentage: float = 0.0


class FunnelData(BaseModel):
    saved: int = 0
    applied: int = 0
    screening: int = 0
    interviewing: int = 0
    offer: int = 0
    accepted: int = 0


class FunnelStageData(BaseModel):
    stage: str
    count: int = 0


# --------------- Pattern Detector schemas (Feature D1) ---------------


class PatternInsight(BaseModel):
    """A single insight row returned by a pattern query."""

    label: str
    value: float = 0.0
    detail: str = ""
    sample_size: int = 0
    warning: str | None = None


class AllPatternsResponse(BaseModel):
    """Aggregate response from ``GET /analytics/patterns``."""

    callback_rate_by_company_size: list[dict] = []
    conversion_funnel: list[FunnelStageData] = []
    response_time_patterns: list[dict] = []
    best_application_timing: list[dict] = []
    company_ghosting_rate: list[dict] = []
    skill_gap_detection: list[dict] = []
