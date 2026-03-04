import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, update, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Job
from backend.schemas import JobBase, JobListResponse, JobUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    q: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    experience_level: Optional[str] = None,
    remote_type: Optional[str] = None,
    posted_within_days: Optional[int] = None,
    min_match_score: Optional[float] = None,
    min_salary: Optional[float] = None,
    tech_stack: Optional[str] = None,
    company: Optional[str] = None,
    is_starred: Optional[bool] = None,
    sort_by: str = Query("scraped_at", pattern="^(match_score|posted_at|scraped_at|salary_max|title|company_name|last_updated)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Job).where(Job.duplicate_of.is_(None))

    # Full-text search
    if q:
        fts_query = select(text("job_id")).select_from(text("jobs_fts")).where(
            text("jobs_fts MATCH :q")
        )
        matching_ids = (await db.execute(fts_query, {"q": q})).scalars().all()
        if matching_ids:
            query = query.where(Job.job_id.in_(matching_ids))
        else:
            # Fallback to LIKE search
            query = query.where(
                or_(
                    Job.title.ilike(f"%{q}%"),
                    Job.company_name.ilike(f"%{q}%"),
                    Job.description_clean.ilike(f"%{q}%"),
                )
            )

    if location:
        query = query.where(
            or_(
                Job.location_city.ilike(f"%{location}%"),
                Job.location_state.ilike(f"%{location}%"),
                Job.location_country.ilike(f"%{location}%"),
            )
        )

    if source:
        sources = [s.strip() for s in source.split(",")]
        query = query.where(Job.source.in_(sources))

    if status:
        statuses = [s.strip() for s in status.split(",")]
        query = query.where(Job.status.in_(statuses))

    if experience_level:
        levels = [l.strip() for l in experience_level.split(",")]
        query = query.where(Job.experience_level.in_(levels))

    if remote_type:
        types = [t.strip() for t in remote_type.split(",")]
        query = query.where(Job.remote_type.in_(types))

    if posted_within_days:
        cutoff = datetime.utcnow() - timedelta(days=posted_within_days)
        query = query.where(Job.posted_at >= cutoff)

    if min_match_score is not None:
        query = query.where(Job.match_score >= min_match_score)

    if min_salary is not None:
        query = query.where(Job.salary_max >= min_salary)

    if tech_stack:
        stacks = [s.strip() for s in tech_stack.split(",")]
        for stack in stacks:
            query = query.where(Job.tech_stack.ilike(f"%{stack}%"))

    if company:
        query = query.where(Job.company_name.ilike(f"%{company}%"))

    if is_starred is not None:
        query = query.where(Job.is_starred == is_starred)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    sort_column = getattr(Job, sort_by, Job.scraped_at)
    if sort_dir == "desc":
        query = query.order_by(sort_column.desc().nullslast())
    else:
        query = query.order_by(sort_column.asc().nullsfirst())

    # Paginate
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return JobListResponse(
        jobs=[JobBase.model_validate(j) for j in jobs],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/{job_id}", response_model=JobBase)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobBase.model_validate(job)


@router.patch("/{job_id}", response_model=JobBase)
async def update_job(
    job_id: str, body: JobUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = body.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"] == "applied":
        update_data["applied_at"] = datetime.utcnow()

    if update_data:
        await db.execute(
            update(Job).where(Job.job_id == job_id).values(**update_data)
        )
        await db.commit()

    # Refetch
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    return JobBase.model_validate(job)
