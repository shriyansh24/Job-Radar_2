from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, TypeAdapter, field_validator

HTTP_URL_ADAPTER = TypeAdapter(AnyHttpUrl)


def _normalize_http_url(value: str) -> str:
    return str(HTTP_URL_ADAPTER.validate_python(value.strip()))


class ScraperRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    status: str
    jobs_found: int
    jobs_new: int
    jobs_updated: int
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: Decimal | None = None


class ScraperRunRequest(BaseModel):
    sources: list[str] | None = None
    queries: list[str] | None = None
    locations: list[str] | None = None


class CareerPageCreate(BaseModel):
    """Create a career-page scrape target."""

    url: str
    company_name: str | None = None

    @field_validator("url")
    @classmethod
    def normalize_url(cls, value: str) -> str:
        return _normalize_http_url(value)


class CareerPageUpdate(BaseModel):
    """Partial update for a career-page scrape target."""

    url: str | None = None
    company_name: str | None = None
    enabled: bool | None = None

    @field_validator("url")
    @classmethod
    def normalize_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_http_url(value)


class CareerPageResponse(BaseModel):
    """Response schema for career-page scrape targets.

    Maps from ScrapeTarget with source_kind='career_page'.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    company_name: str | None = None
    enabled: bool
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# ScrapeTarget schemas
# ---------------------------------------------------------------------------


class ScrapeTargetResponse(BaseModel):
    """Full response schema for a ScrapeTarget."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None = None
    url: str
    company_name: str | None = None
    company_domain: str | None = None
    source_kind: str
    ats_vendor: str | None = None
    ats_board_token: str | None = None
    start_tier: int
    max_tier: int
    priority_class: str
    schedule_interval_m: int
    enabled: bool
    quarantined: bool
    quarantine_reason: str | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_success_tier: int | None = None
    last_http_status: int | None = None
    consecutive_failures: int
    failure_count: int
    next_scheduled_at: datetime | None = None
    lca_filings: int | None = None
    industry: str | None = None
    created_at: datetime
    updated_at: datetime


class ScrapeTargetListResponse(BaseModel):
    """Paginated list of ScrapeTargets."""

    items: list[ScrapeTargetResponse]
    total: int


class ScrapeTargetUpdate(BaseModel):
    """Partial update for a ScrapeTarget."""

    priority_class: str | None = None
    enabled: bool | None = None
    start_tier: int | None = None
    max_tier: int | None = None


class ScrapeTargetImportItem(BaseModel):
    """Single entry in a bulk import request."""

    url: str
    company_name: str | None = None
    priority_class: str | None = None
    ats_vendor: str | None = None


class ScrapeTargetImportResponse(BaseModel):
    """Result of a bulk import operation."""

    imported: int
    skipped: int
    errors: list[str]


class ScrapeTargetReleaseRequest(BaseModel):
    """Optional body for releasing a quarantined target."""

    force_tier: int | None = None


# ---------------------------------------------------------------------------
# ScrapeAttempt schemas
# ---------------------------------------------------------------------------


class ScrapeAttemptResponse(BaseModel):
    """Response schema for a ScrapeAttempt."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID | None = None
    target_id: uuid.UUID
    selected_tier: int
    actual_tier_used: int
    scraper_name: str
    parser_name: str | None = None
    status: str
    http_status: int | None = None
    duration_ms: int | None = None
    retries: int
    escalations: int
    jobs_extracted: int
    content_hash_before: str | None = None
    content_hash_after: str | None = None
    content_changed: bool | None = None
    pages_crawled: int | None = None
    pagination_stopped_reason: str | None = None
    error_class: str | None = None
    error_message: str | None = None
    browser_used: bool
    created_at: datetime


class ScrapeTargetWithAttemptsResponse(BaseModel):
    """Target plus its most recent attempts."""

    target: ScrapeTargetResponse
    recent_attempts: list[ScrapeAttemptResponse]


# ---------------------------------------------------------------------------
# Batch trigger schemas
# ---------------------------------------------------------------------------


class TriggerBatchRequest(BaseModel):
    """Optional body for triggering a batch scrape run."""

    priority_class: str | None = None
    batch_size: int = 50


class TriggerBatchResponse(BaseModel):
    """Summary of a triggered batch scrape run."""

    run_id: uuid.UUID | None = None
    targets_attempted: int
    targets_succeeded: int
    targets_failed: int
    jobs_found: int
    errors: list[str]
