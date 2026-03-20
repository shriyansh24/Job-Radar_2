from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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


class CareerPageUpdate(BaseModel):
    """Partial update for a career-page scrape target."""

    url: str | None = None
    company_name: str | None = None
    enabled: bool | None = None


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
