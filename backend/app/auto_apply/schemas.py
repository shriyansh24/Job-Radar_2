from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AutoApplyProfileCreate(BaseModel):
    name: str
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    cover_letter_template: str | None = None


class AutoApplyProfileUpdate(BaseModel):
    name: str | None = None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    cover_letter_template: str | None = None
    is_active: bool | None = None


class AutoApplyProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    cover_letter_template: str | None = None
    is_active: bool
    created_at: datetime


class RuleCreate(BaseModel):
    profile_id: uuid.UUID | None = None
    name: str | None = None
    priority: int = 0
    min_match_score: float | None = None
    required_keywords: list[str] = []
    excluded_keywords: list[str] = []
    required_companies: list[str] = []
    excluded_companies: list[str] = []
    experience_levels: list[str] = []
    remote_types: list[str] = []


class RuleUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    priority: int | None = None
    min_match_score: float | None = None
    required_keywords: list[str] | None = None
    excluded_keywords: list[str] | None = None


class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    profile_id: uuid.UUID | None = None
    name: str | None = None
    is_active: bool
    priority: int
    min_match_score: float | None = None
    required_keywords: list[str] = []
    excluded_keywords: list[str] = []
    required_companies: list[str] = []
    excluded_companies: list[str] = []
    experience_levels: list[str] = []
    remote_types: list[str] = []
    created_at: datetime


class RunResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: str | None = None
    rule_id: uuid.UUID | None = None
    status: str
    ats_provider: str | None = None
    fields_filled: dict = {}
    fields_missed: list[str] = []
    screenshots: list[str] = []
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AutoApplyStatsResponse(BaseModel):
    total_runs: int = 0
    successful: int = 0
    failed: int = 0
    pending: int = 0


class ApplySingleRequest(BaseModel):
    job_id: str
