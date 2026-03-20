from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    resume_text: str | None = None
    resume_filename: str | None = None
    search_queries: list[str] = []
    search_locations: list[str] = []
    watchlist_companies: list[str] = []
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    education: list[dict] = []
    work_experience: list[dict] = []
    work_authorization: str | None = None
    # v1 extended fields
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    requires_sponsorship: bool | None = None
    notice_period: str | None = None
    available_start: datetime | None = None
    current_title: str | None = None
    current_company: str | None = None
    graduation_year: int | None = None
    highest_degree: str | None = None
    preferred_job_types: list[str] = []
    preferred_remote_types: list[str] = []
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    answer_bank: dict = {}
    theme: str = "dark"
    notifications_enabled: bool = True
    auto_apply_enabled: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    education: list[dict] | None = None
    work_experience: list[dict] | None = None
    work_authorization: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    requires_sponsorship: bool | None = None
    notice_period: str | None = None
    available_start: datetime | None = None
    current_title: str | None = None
    current_company: str | None = None
    graduation_year: int | None = None
    highest_degree: str | None = None
    preferred_job_types: list[str] | None = None
    preferred_remote_types: list[str] | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    search_queries: list[str] | None = None
    search_locations: list[str] | None = None
    watchlist_companies: list[str] | None = None
    theme: str | None = None
    notifications_enabled: bool | None = None
    auto_apply_enabled: bool | None = None
