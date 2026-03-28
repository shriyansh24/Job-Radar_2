from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.models import Job
from app.outcomes.models import ApplicationOutcome, CompanyInsight
from app.pipeline.models import Application

POSITIVE_STAGES = {
    "screening",
    "interviewing",
    "offer",
    "accepted",
}


async def get_training_data(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
) -> list[dict[str, object]]:
    result = await db.execute(
        select(ApplicationOutcome, Application, Job)
        .join(
            Application,
            Application.id == ApplicationOutcome.application_id,
        )
        .outerjoin(Job, Job.id == Application.job_id)
        .where(ApplicationOutcome.user_id == user_id)
    )
    rows_raw = result.all()

    training_data: list[dict[str, object]] = []
    for outcome, application, job in rows_raw:
        if job is None:
            continue

        label = 1 if outcome.stage_reached in POSITIVE_STAGES else 0
        features = await build_features(
            db,
            user_id=user_id,
            job=job,
            application=application,
            outcome=outcome,
        )
        training_data.append({"features": features, "label": label})

    return training_data


async def build_features(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    job: Job,
    application: Application | None = None,
    outcome: ApplicationOutcome | None = None,
) -> list[float]:
    del application

    title_sim = await title_similarity(db, user_id=user_id, job_title=job.title or "")
    company_score = await company_familiarity(
        db,
        user_id=user_id,
        company_name=job.company_name or "",
    )
    skill_overlap = compute_skill_overlap(job)
    salary_match = compute_salary_match(job)
    location_match = compute_location_match(job)
    experience_match = compute_experience_match(job)
    freshness = compute_freshness(job)
    referral = float(outcome.referral_used) if outcome else 0.0

    return [
        title_sim,
        company_score,
        skill_overlap,
        salary_match,
        location_match,
        experience_match,
        freshness,
        referral,
    ]


async def title_similarity(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    job_title: str,
) -> float:
    result = await db.execute(
        select(Application.position_title)
        .where(
            Application.user_id == user_id,
            Application.position_title.isnot(None),
        )
        .limit(50)
    )
    past_titles = [r[0] for r in result.all() if r[0]]

    if not past_titles or not job_title:
        return 0.5

    job_words = set(job_title.lower().split())
    best_sim = 0.0
    for title in past_titles:
        title_words = set(title.lower().split())
        if not job_words or not title_words:
            continue
        overlap = len(job_words & title_words)
        union = len(job_words | title_words)
        sim = overlap / union if union > 0 else 0.0
        best_sim = max(best_sim, sim)

    return best_sim


async def company_familiarity(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    company_name: str,
) -> float:
    if not company_name:
        return 0.0

    result = await db.execute(
        select(CompanyInsight).where(
            CompanyInsight.user_id == user_id,
            CompanyInsight.company_name == company_name,
        )
    )
    insight = result.scalar_one_or_none()
    if insight is None:
        return 0.0

    if insight.total_applications > 0 and insight.callback_count > 0:
        return min(
            1.0,
            float(insight.callback_count) / float(insight.total_applications),
        )
    return 0.1


def compute_skill_overlap(job: Job) -> float:
    skills = job.skills_required or []
    if not skills:
        return 0.5
    return min(1.0, len(skills) / 10.0)


def compute_salary_match(job: Job) -> float:
    if job.salary_min is not None and job.salary_max is not None:
        salary_range = float(job.salary_max) - float(job.salary_min)
        midpoint = (float(job.salary_min) + float(job.salary_max)) / 2
        if midpoint > 0:
            return min(1.0, 1.0 - (salary_range / midpoint / 2))
    if job.salary_max is not None:
        return 0.7
    return 0.5


def compute_location_match(job: Job) -> float:
    if job.remote_type == "remote":
        return 1.0
    if job.remote_type == "hybrid":
        return 0.7
    if job.remote_type in ("onsite", "on-site"):
        return 0.4
    return 0.5


def compute_experience_match(job: Job) -> float:
    if job.experience_level is None:
        return 0.5

    level_map = {
        "entry": 0.3,
        "junior": 0.4,
        "mid": 0.6,
        "senior": 0.8,
        "lead": 0.9,
        "principal": 0.95,
        "staff": 0.95,
        "director": 0.9,
        "vp": 0.85,
        "executive": 0.8,
    }
    return level_map.get(job.experience_level.lower(), 0.5)


def compute_freshness(job: Job) -> float:
    if job.posted_at is None:
        if job.scraped_at:
            posted = job.scraped_at
        else:
            return 0.5
    else:
        posted = job.posted_at

    now = datetime.now(timezone.utc)
    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=timezone.utc)

    days_old = (now - posted).total_seconds() / 86400
    if days_old <= 1:
        return 1.0
    if days_old <= 7:
        return 0.8
    if days_old <= 14:
        return 0.6
    if days_old <= 30:
        return 0.4
    return 0.2
