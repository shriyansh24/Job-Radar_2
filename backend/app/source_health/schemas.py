from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SourceHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_name: str
    health_state: str
    quality_score: Decimal
    total_jobs_found: int
    last_check_at: datetime | None = None
    failure_count: int
    backoff_until: datetime | None = None
    created_at: datetime


class SourceHealthDetail(SourceHealthResponse):
    recent_checks: list[SourceCheckLogResponse] = []


class SourceCheckLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    check_type: str | None = None
    check_status: str | None = None
    jobs_found: int
    error_message: str | None = None
    checked_at: datetime


# Fix forward reference
SourceHealthDetail.model_rebuild()
