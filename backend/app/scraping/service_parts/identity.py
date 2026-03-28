from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from app.scraping.deduplication import derive_ats_identity
from app.scraping.port import ScrapedJob


def compute_job_id(job: ScrapedJob) -> str:
    """SHA-256 of (source + title + company + location) for stable ID."""
    content = f"{job.source}|{job.title}|{job.company_name}|{job.location}"
    return hashlib.sha256(content.encode()).hexdigest()[:64]


def scraped_job_to_dict(job: ScrapedJob) -> dict[str, Any]:
    """Convert ScrapedJob to dict for Job ORM model."""
    ats_identity = derive_ats_identity(job)
    return {
        "source": job.source,
        "source_url": job.source_url,
        "title": job.title,
        "company_name": job.company_name,
        "company_domain": job.company_domain,
        "company_logo_url": job.company_logo_url,
        "location": job.location,
        "remote_type": job.remote_type,
        "description_raw": job.description_raw,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_period": job.salary_period,
        "salary_currency": job.salary_currency,
        "experience_level": job.experience_level,
        "job_type": job.job_type,
        "posted_at": job.posted_at,
        "ats_job_id": ats_identity["ats_job_id"],
        "ats_provider": ats_identity["ats_provider"],
        "ats_composite_key": ats_identity["ats_composite_key"],
        "scraped_at": datetime.now(UTC),
    }
