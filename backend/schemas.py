from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# --- Job Schemas ---

class JobBase(BaseModel):
    job_id: str
    source: str
    url: str
    posted_at: Optional[datetime] = None
    scraped_at: datetime
    is_active: bool = True
    duplicate_of: Optional[str] = None
    company_name: str
    company_domain: Optional[str] = None
    company_logo_url: Optional[str] = None
    title: str
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    remote_type: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    department: Optional[str] = None
    industry: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "USD"
    salary_period: Optional[str] = None
    description_raw: Optional[str] = None
    description_clean: Optional[str] = None
    description_markdown: Optional[str] = None
    skills_required: Optional[list] = None
    skills_nice_to_have: Optional[list] = None
    tech_stack: Optional[list] = None
    seniority_score: Optional[float] = None
    remote_score: Optional[float] = None
    match_score: Optional[float] = None
    summary_ai: Optional[str] = None
    red_flags: Optional[list] = None
    green_flags: Optional[list] = None
    is_enriched: bool = False
    enriched_at: Optional[datetime] = None
    status: str = "new"
    notes: Optional[str] = None
    applied_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    is_starred: bool = False
    tags: Optional[list] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: list[JobBase]
    total: int
    page: int
    limit: int
    has_more: bool


class JobUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list] = None
    is_starred: Optional[bool] = None


# --- Scraper Schemas ---

class ScraperRunRequest(BaseModel):
    source: str = "all"  # "all"|"serpapi"|"greenhouse"|"lever"|"ashby"|"jobspy"


class ScraperRunResponse(BaseModel):
    id: int
    source: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    jobs_found: int = 0
    jobs_new: int = 0
    jobs_updated: int = 0
    error_message: Optional[str] = None
    status: str = "running"

    class Config:
        from_attributes = True


class ScraperStatusResponse(BaseModel):
    runs: list[ScraperRunResponse]
    is_running: bool


# --- Stats Schemas ---

class StatsResponse(BaseModel):
    total_jobs: int
    new_today: int
    by_source: dict
    by_status: dict
    by_experience_level: dict
    top_companies: list
    top_skills: list
    jobs_over_time: list
    avg_match_score: Optional[float] = None


# --- Search Schemas ---

class SemanticSearchResult(BaseModel):
    job: JobBase
    similarity: float


# --- Copilot Schemas ---

class CopilotRequest(BaseModel):
    tool: str  # "coverLetter"|"interviewPrep"|"gapAnalysis"
    job_id: str


class CopilotResponse(BaseModel):
    content: str
    tool: str
    job_id: str


# --- Settings Schemas ---

class SettingsResponse(BaseModel):
    serpapi_key_set: bool = False
    theirstack_key_set: bool = False
    apify_key_set: bool = False
    openrouter_key_set: bool = False
    openrouter_primary_model: str = "anthropic/claude-3-5-haiku"
    openrouter_fallback_model: str = "openai/gpt-4o-mini"
    default_queries: list = Field(default_factory=lambda: ["AI Engineer", "ML Engineer", "Data Scientist"])
    default_locations: list = Field(default_factory=lambda: ["Remote", "New York, NY"])
    company_watchlist: list = Field(default_factory=list)
    resume_filename: Optional[str] = None
    resume_uploaded_at: Optional[datetime] = None
    scraper_intervals: dict = Field(default_factory=lambda: {
        "serpapi": 6, "greenhouse": 3, "lever": 3,
        "ashby": 3, "jobspy": 12,
    })
    scraper_enabled: dict = Field(default_factory=lambda: {
        "serpapi": True, "greenhouse": True, "lever": True,
        "ashby": True, "jobspy": True, "theirstack": False, "apify": False,
    })


class SettingsUpdate(BaseModel):
    serpapi_key: Optional[str] = None
    theirstack_key: Optional[str] = None
    apify_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_primary_model: Optional[str] = None
    openrouter_fallback_model: Optional[str] = None
    default_queries: Optional[list] = None
    default_locations: Optional[list] = None
    company_watchlist: Optional[list] = None
    scraper_intervals: Optional[dict] = None
    scraper_enabled: Optional[dict] = None


# --- Saved Search Schemas ---

class SavedSearchCreate(BaseModel):
    name: str
    query_params: dict
    alert_enabled: bool = False


class SavedSearchResponse(BaseModel):
    id: int
    name: str
    query_params: dict
    alert_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True
