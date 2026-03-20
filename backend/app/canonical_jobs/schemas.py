from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CanonicalJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company_name: str
    company_domain: str | None = None
    location: str | None = None
    remote_type: str | None = None
    status: str
    source_count: int
    first_seen_at: datetime
    last_refreshed_at: datetime
    is_stale: bool
    merged_data: dict | None = None
    created_at: datetime


class RawJobSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    source_url: str | None = None
    job_id: str | None = None
    scraped_at: datetime | None = None


class CanonicalJobDetailResponse(CanonicalJobResponse):
    sources: list[RawJobSourceResponse] = []
