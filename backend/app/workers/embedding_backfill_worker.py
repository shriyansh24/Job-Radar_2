from __future__ import annotations

import structlog

from app.config import Settings
from app.database import async_session_factory
from app.enrichment.embedding import EmbeddingService

logger = structlog.get_logger()

# Process in batches of this size
BACKFILL_BATCH_SIZE = 100


async def run_embedding_backfill(ctx: dict | None = None) -> None:
    """Background job: backfill v2 embeddings (768d nomic-embed-text) for jobs.

    Processes jobs that have been enriched but lack an embedding.
    Runs in resumable batches -- each invocation processes up to BACKFILL_BATCH_SIZE jobs.
    """
    settings = Settings()

    async with async_session_factory() as db:
        try:
            from sqlalchemy import func, select, text

            from app.jobs.models import Job

            # Count remaining jobs without embeddings
            remaining = await db.scalar(
                select(func.count())
                .select_from(Job)
                .where(Job.is_enriched.is_(True), text("embedding_v2 IS NULL"))
            )

            if not remaining:
                logger.debug("embedding_backfill_skipped", reason="no_enriched_jobs")
                return

            embedder = EmbeddingService(db, settings)

            # Fetch batch of jobs needing embeddings
            jobs = (
                await db.scalars(
                    select(Job)
                    .where(Job.is_enriched.is_(True), text("embedding_v2 IS NULL"))
                    .order_by(Job.created_at.asc())
                    .limit(BACKFILL_BATCH_SIZE)
                )
            ).all()

            if not jobs:
                logger.debug("embedding_backfill_complete", reason="all_jobs_processed")
                return

            embedded_count = 0
            failed_count = 0

            for job in jobs:
                try:
                    job_text = _build_job_text(job)
                    embedding = await embedder.embed(job_text, task_prefix="search_document")

                    if embedding is None:
                        failed_count += 1
                        continue

                    await db.execute(
                        text("UPDATE jobs SET embedding_v2 = :emb WHERE id = :id"),
                        {"emb": str(embedding), "id": job.id},
                    )
                    embedded_count += 1
                except Exception:
                    failed_count += 1
                    logger.warning(
                        "embedding_backfill_job_failed",
                        job_id=job.id,
                        exc_info=True,
                    )

            if embedded_count > 0:
                await db.commit()

            logger.info(
                "embedding_backfill_batch_complete",
                embedded=embedded_count,
                failed=failed_count,
                remaining=remaining - embedded_count,
            )

        except Exception:
            logger.error("embedding_backfill_worker_failed", exc_info=True)


def _build_job_text(job: object) -> str:
    """Build text representation of a job for embedding."""
    title = getattr(job, "title", "") or ""
    company = getattr(job, "company_name", "") or ""
    summary = getattr(job, "summary_ai", "") or ""
    skills = getattr(job, "skills_required", None) or []
    location = getattr(job, "location", "") or ""
    description = getattr(job, "description_clean", "") or ""

    parts = [title, company, location, summary]
    if skills:
        parts.append(" ".join(skills))
    if description:
        # Truncate description to fit within nomic's 2048 token context
        parts.append(description[:1500])

    return " ".join(p for p in parts if p)
