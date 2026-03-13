from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, JSON, ForeignKey, Float, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class Job(Base):
    __tablename__ = "jobs"

    # Identity
    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(32))
    url: Mapped[str] = mapped_column(Text)
    posted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    duplicate_of: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("jobs.job_id"), nullable=True
    )

    # Company
    company_name: Mapped[str] = mapped_column(String(255))
    company_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Role
    title: Mapped[str] = mapped_column(String(500))
    location_city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location_state: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location_country: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remote_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    job_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    experience_level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Compensation
    salary_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(
        String(8), default="USD", nullable=True
    )
    salary_period: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Content
    description_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_clean: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI Enrichment
    skills_required: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    skills_nice_to_have: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    tech_stack: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    seniority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    remote_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    summary_ai: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    red_flags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    green_flags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_enriched: Mapped[bool] = mapped_column(Boolean, default=False)
    enriched_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # User State
    status: Mapped[str] = mapped_column(String(32), default="new")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    applied_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Zip integration columns
    dedup_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tfidf_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    council_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    apply_questions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    query_params: Mapped[dict] = mapped_column(JSON)
    alert_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0)
    jobs_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running")


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    resume_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resume_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resume_uploaded_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    default_queries: Mapped[Optional[list]] = mapped_column(
        JSON, default=lambda: ["AI Engineer", "ML Engineer", "Data Scientist"]
    )
    default_locations: Mapped[Optional[list]] = mapped_column(
        JSON, default=lambda: ["Remote", "New York, NY"]
    )
    company_watchlist: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Zip integration columns
    resume_parsed: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    application_profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)  # ULID
    filename: Mapped[str] = mapped_column(String(255))
    format: Mapped[str] = mapped_column(String(8))  # pdf/docx/md/tex
    file_path: Mapped[str] = mapped_column(String(512))
    parsed_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parsed_structured: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    version_label: Mapped[str] = mapped_column(String(255), default="v1")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True, onupdate=func.now())


class ApplicationAttempt(Base):
    __tablename__ = "application_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), ForeignKey("jobs.job_id"))
    resume_version_id: Mapped[Optional[str]] = mapped_column(
        String(26), ForeignKey("resume_versions.id"), nullable=True
    )
    ats_provider: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    fields_filled: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fields_skipped: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    screenshots: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    custom_answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
