from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enrichment.embedding import EmbeddingService
from app.jobs.models import Job
from app.jobs.schemas import JobExportRequest, JobListParams, JobResponse, JobUpdate
from app.search.hybrid import HybridSearchService
from app.shared.errors import NotFoundError
from app.shared.pagination import PaginatedResponse

logger = structlog.get_logger()


SORTABLE_COLUMNS = frozenset(
    {
        "scraped_at",
        "match_score",
        "title",
        "company_name",
        "posted_at",
        "created_at",
        "salary_min",
        "tfidf_score",
    }
)


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_jobs(self, params: JobListParams, user_id: uuid.UUID) -> PaginatedResponse[Job]:
        query = select(Job).where(Job.user_id == user_id, Job.is_active.is_(True))

        if params.source:
            query = query.where(Job.source == params.source)
        if params.remote_type:
            query = query.where(Job.remote_type == params.remote_type)
        if params.experience_level:
            query = query.where(Job.experience_level == params.experience_level)
        if params.job_type:
            query = query.where(Job.job_type == params.job_type)
        if params.status:
            query = query.where(Job.status == params.status)
        if params.is_starred is not None:
            query = query.where(Job.is_starred.is_(params.is_starred))
        if params.min_match_score is not None:
            query = query.where(Job.match_score >= params.min_match_score)
        if params.q:
            # Degrade to LIKE on SQLite; on PostgreSQL use tsvector match
            query = query.where(
                Job.title.ilike(f"%{params.q}%")
                | Job.company_name.ilike(f"%{params.q}%")
                | Job.description_clean.ilike(f"%{params.q}%")
            )

        # Sorting (allowlist prevents arbitrary column access)
        sort_field = params.sort_by if params.sort_by in SORTABLE_COLUMNS else "scraped_at"
        sort_col = getattr(Job, sort_field, Job.scraped_at)
        query = query.order_by(sort_col.desc() if params.sort_order == "desc" else sort_col.asc())

        # Count
        count_q = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_q) or 0

        # Paginate
        offset = (params.page - 1) * params.page_size
        result = await self.db.scalars(query.offset(offset).limit(params.page_size))
        items = list(result.all())

        return PaginatedResponse(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_job(self, job_id: str, user_id: uuid.UUID) -> Job:
        result = await self.db.execute(select(Job).where(Job.id == job_id, Job.user_id == user_id))
        job = result.scalar_one_or_none()
        if job is None:
            raise NotFoundError(f"Job {job_id} not found")
        return job

    async def update_job(self, job_id: str, data: JobUpdate, user_id: uuid.UUID) -> Job:
        job = await self.get_job(job_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(job, key, value)
        job.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def delete_job(self, job_id: str, user_id: uuid.UUID) -> None:
        job = await self.get_job(job_id, user_id)
        job.is_active = False
        job.updated_at = datetime.now(UTC)
        await self.db.commit()

    async def semantic_search(self, query: str, limit: int, user_id: uuid.UUID) -> list[Job]:
        """Semantic search over jobs with hybrid ranking and graceful fallback."""
        search_service = HybridSearchService(self.db, EmbeddingService(self.db))
        ranked_results = await search_service.search(query, user_id, limit=limit)
        if not ranked_results:
            return []

        job_ids = [result.job_id for result in ranked_results]
        jobs = list(
            (
                await self.db.scalars(
                    select(Job).where(
                        Job.user_id == user_id,
                        Job.is_active.is_(True),
                        Job.id.in_(job_ids),
                    )
                )
            ).all()
        )
        jobs_by_id = {job.id: job for job in jobs}
        return [jobs_by_id[job_id] for job_id in job_ids if job_id in jobs_by_id]

    async def export_jobs(self, params: JobExportRequest, user_id: uuid.UUID) -> bytes:
        list_params = params.filters or JobListParams()
        list_params.page_size = 10000
        result = await self.list_jobs(list_params, user_id)

        if params.format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "id",
                    "title",
                    "company_name",
                    "location",
                    "source",
                    "remote_type",
                    "status",
                    "match_score",
                    "scraped_at",
                ],
            )
            writer.writeheader()
            for job in result.items:
                writer.writerow(
                    {
                        "id": job.id,
                        "title": job.title,
                        "company_name": job.company_name,
                        "location": job.location,
                        "source": job.source,
                        "remote_type": job.remote_type,
                        "status": job.status,
                        "match_score": str(job.match_score) if job.match_score else "",
                        "scraped_at": str(job.scraped_at),
                    }
                )
            return output.getvalue().encode()

        # Default JSON
        items = [JobResponse.model_validate(j).model_dump(mode="json") for j in result.items]
        return json.dumps(items, indent=2).encode()
