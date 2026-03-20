from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_name: str
    domain: str | None = None
    careers_url: str | None = None
    logo_url: str | None = None
    ats_provider: str | None = None
    validation_state: str
    confidence_score: Decimal
    job_count: int
    source_count: int
    created_at: datetime
    updated_at: datetime


class CompanyResolveRequest(BaseModel):
    name: str
