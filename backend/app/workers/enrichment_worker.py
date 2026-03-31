from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any, cast

import structlog

from app.config import Settings
from app.database import async_session_factory
from app.enrichment.embedding import EmbeddingService
from app.enrichment.llm_client import LLMClient
from app.enrichment.service import EnrichmentService
from app.enrichment.tfidf import TFIDFScorer
from app.runtime.job_context import (
    build_job_metadata_key as _shared_build_job_metadata_key,
)
from app.runtime.job_context import (
    clear_job_metadata,
    load_job_metadata,
)

logger = structlog.get_logger()


def _build_job_metadata_key(job_id: str) -> str:
    return _shared_build_job_metadata_key(job_id)


async def run_enrichment_batch(
    ctx: Mapping[str, Any] | None = None,
    user_id: str | None = None,
) -> None:
    """Background job: enrich unenriched jobs via LLM."""
    settings = Settings()
    llm_client = LLMClient(settings.openrouter_api_key, settings.default_llm_model)
    metadata = await load_job_metadata(
        ctx,
        logger=logger,
        invalid_event="enrichment_batch_metadata_invalid",
    )
    raw_user_id = user_id or metadata.get("user_id")
    if not isinstance(raw_user_id, str):
        logger.warning("enrichment_batch_skipped", reason="missing_user_scope")
        await clear_job_metadata(ctx)
        await llm_client.close()
        raise RuntimeError("Enrichment batch requires a scoped user_id.")
    try:
        scoped_user_id = uuid.UUID(raw_user_id)
    except ValueError:
        logger.warning("enrichment_batch_skipped", reason="invalid_user_scope")
        await clear_job_metadata(ctx)
        await llm_client.close()
        raise RuntimeError("Enrichment batch received an invalid scoped user_id.")

    async with async_session_factory() as db:
        try:
            service = EnrichmentService(db, llm_client, settings)
            count = await service.enrich_batch(user_id=scoped_user_id, limit=50)
            logger.info(
                "enrichment_completed",
                jobs_enriched=count,
                scoped_user_id=str(scoped_user_id) if scoped_user_id else None,
            )
            await clear_job_metadata(ctx)
        except Exception:
            logger.exception(
                "enrichment_worker_failed",
                scoped_user_id=str(scoped_user_id) if scoped_user_id else None,
            )
            raise
        finally:
            await llm_client.close()


async def run_embedding_batch(ctx: Mapping[str, Any] | None = None) -> None:
    """Background job: generate embeddings for enriched jobs."""
    async with async_session_factory() as db:
        try:
            service = EmbeddingService(db)
            count = await service.embed_jobs_batch(user_id=None, limit=100)
            logger.info("embeddings_generated", count=count)
        except Exception:
            logger.exception("embedding_worker_failed")
            raise


async def run_tfidf_scoring(ctx: Mapping[str, Any] | None = None) -> None:
    """Background job: update TF-IDF scores against user resume."""
    async with async_session_factory() as db:
        try:
            from sqlalchemy import select, update

            from app.jobs.models import Job
            from app.profile.models import UserProfile

            profile = await db.scalar(select(UserProfile).limit(1))
            if not profile or not profile.resume_text:
                logger.debug("tfidf_skipped", reason="no_resume_text")
                return

            jobs = (
                await db.scalars(select(Job).where(Job.tfidf_score.is_(None)).limit(200))
            ).all()
            if not jobs:
                return

            scorer = TFIDFScorer()
            scores = scorer.score_jobs(profile.resume_text, cast(list[object], list(jobs)))
            for job_id, score in scores:
                await db.execute(update(Job).where(Job.id == job_id).values(tfidf_score=score))
            await db.commit()
            logger.info("tfidf_scoring_completed", jobs_scored=len(scores))
        except Exception:
            logger.exception("tfidf_worker_failed")
            raise
