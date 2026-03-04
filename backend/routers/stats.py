import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Job
from backend.schemas import StatsResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Total jobs (excluding duplicates)
    total = (
        await db.execute(
            select(func.count(Job.job_id)).where(Job.duplicate_of.is_(None))
        )
    ).scalar() or 0

    # New today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    new_today = (
        await db.execute(
            select(func.count(Job.job_id)).where(
                Job.scraped_at >= today_start,
                Job.duplicate_of.is_(None),
            )
        )
    ).scalar() or 0

    # By source
    source_rows = (
        await db.execute(
            select(Job.source, func.count(Job.job_id))
            .where(Job.duplicate_of.is_(None))
            .group_by(Job.source)
        )
    ).all()
    by_source = {row[0]: row[1] for row in source_rows}

    # By status
    status_rows = (
        await db.execute(
            select(Job.status, func.count(Job.job_id))
            .where(Job.duplicate_of.is_(None))
            .group_by(Job.status)
        )
    ).all()
    by_status = {row[0]: row[1] for row in status_rows}

    # By experience level
    exp_rows = (
        await db.execute(
            select(Job.experience_level, func.count(Job.job_id))
            .where(Job.duplicate_of.is_(None))
            .where(Job.experience_level.isnot(None))
            .group_by(Job.experience_level)
        )
    ).all()
    by_experience_level = {row[0]: row[1] for row in exp_rows}

    # Top companies
    company_rows = (
        await db.execute(
            select(Job.company_name, func.count(Job.job_id).label("count"))
            .where(Job.duplicate_of.is_(None))
            .group_by(Job.company_name)
            .order_by(func.count(Job.job_id).desc())
            .limit(20)
        )
    ).all()
    top_companies = [{"name": row[0], "count": row[1]} for row in company_rows]

    # Top skills (from JSON arrays)
    skills_result = (
        await db.execute(
            select(Job.skills_required)
            .where(Job.skills_required.isnot(None))
            .where(Job.duplicate_of.is_(None))
        )
    ).scalars().all()

    skill_counts: dict[str, int] = {}
    for skills_list in skills_result:
        if isinstance(skills_list, list):
            for skill in skills_list:
                skill = str(skill).strip()
                if skill:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

    top_skills = sorted(
        [{"skill": k, "count": v} for k, v in skill_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:30]

    # Jobs over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_rows = (
        await db.execute(
            select(
                func.date(Job.scraped_at).label("date"),
                Job.source,
                func.count(Job.job_id).label("count"),
            )
            .where(Job.scraped_at >= thirty_days_ago)
            .where(Job.duplicate_of.is_(None))
            .group_by(func.date(Job.scraped_at), Job.source)
            .order_by(func.date(Job.scraped_at))
        )
    ).all()

    jobs_over_time = []
    date_map: dict[str, dict] = {}
    for row in daily_rows:
        date_str = str(row[0])
        if date_str not in date_map:
            date_map[date_str] = {"date": date_str}
        date_map[date_str][row[1]] = row[2]
    jobs_over_time = list(date_map.values())

    # Average match score
    avg_score = (
        await db.execute(
            select(func.avg(Job.match_score)).where(
                Job.match_score.isnot(None),
                Job.duplicate_of.is_(None),
            )
        )
    ).scalar()

    return StatsResponse(
        total_jobs=total,
        new_today=new_today,
        by_source=by_source,
        by_status=by_status,
        by_experience_level=by_experience_level,
        top_companies=top_companies,
        top_skills=top_skills,
        jobs_over_time=jobs_over_time,
        avg_match_score=round(avg_score, 1) if avg_score else None,
    )
