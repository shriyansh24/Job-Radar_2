from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ApplicationCreate(BaseModel):
    job_id: str | None = None
    company_name: str | None = None
    position_title: str | None = None
    source: str = "manual"
    notes: str | None = None
    resume_version_id: uuid.UUID | None = None


class ApplicationUpdate(BaseModel):
    company_name: str | None = None
    position_title: str | None = None
    notes: str | None = None
    follow_up_at: datetime | None = None
    reminder_at: datetime | None = None
    salary_offered: Decimal | None = None


class StatusTransition(BaseModel):
    new_status: str
    note: str | None = None
    change_source: str = "user"


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: str | None = None
    company_name: str | None = None
    position_title: str | None = None
    status: str
    source: str | None = None
    applied_at: datetime | None = None
    offer_at: datetime | None = None
    rejected_at: datetime | None = None
    follow_up_at: datetime | None = None
    reminder_at: datetime | None = None
    notes: str | None = None
    salary_offered: Decimal | None = None
    created_at: datetime
    updated_at: datetime


class StatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    old_status: str | None = None
    new_status: str
    change_source: str | None = None
    note: str | None = None
    changed_at: datetime


class PipelineView(BaseModel):
    saved: list[ApplicationResponse] = []
    applied: list[ApplicationResponse] = []
    screening: list[ApplicationResponse] = []
    interviewing: list[ApplicationResponse] = []
    offer: list[ApplicationResponse] = []
    rejected: list[ApplicationResponse] = []
    withdrawn: list[ApplicationResponse] = []
    accepted: list[ApplicationResponse] = []
