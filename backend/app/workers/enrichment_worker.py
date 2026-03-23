from __future__ import annotations

import structlog

from app.config import Settings
from app.database import async_session_factory
from app.enrichment.embedding import EmbeddingService
from app.enrichment.llm_client import LLMClient
from app.enrichment.service import EnrichmentService
from app.enrichment.tfidf import TFIDFScorer

logger = structlog.get_logger()


async def run_enrichment_batch(ctx: dict | None = None) -> None:
    """Background job: enrich unenriched jobs via LLM."""
    settings = Settings()
    llm_client = LLMClient(settings.openrouter_api_key, settings.default_llm_model)

    async with async_session_factory() as db:
        try:
            service = EnrichmentService(db, llm_client, settings)
            count = await service.enrich_batch(user_id=None, limit=50)
            logger.info("enrichment_completed", jobs_enriched=count)
        except Exception as e:
            logger.error("enrichment_worker_failed", error=str(e))
        finally:
            await llm_client.close()


async def run_embedding_batch(ctx: dict | None = None) -> None:
    """Background job: generate embeddings for enriched jobs."""
    settings = Settings()
    async with async_session_factory() as db:
        try:
            service = EmbeddingService(db, settings)
            count = await service.embed_jobs_batch(user_id=None, limit=100)
            logger.info("embeddings_generated", count=count)
        except Exception as e:
            logger.error("embedding_worker_failed", error=str(e))


async def run_tfidf_scoring(ctx: dict | None = None) -> None:
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
            scores = scorer.score_jobs(profile.resume_text, jobs)
            for job_id, score in scores:
                await db.execute(update(Job).where(Job.id == job_id).values(tfidf_score=score))
            await db.commit()
            logger.info("tfidf_scoring_completed", jobs_scored=len(scores))
        except Exception as e:
            logger.error("tfidf_worker_failed", error=str(e))
