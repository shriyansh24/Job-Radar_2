from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class EmbeddingService:
    """Generate and manage embeddings for semantic search.

    Uses sentence-transformers (lazy-imported to avoid heavy startup cost).
    Embeddings are stored in pgvector — PostgreSQL only.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._model = None

    @property
    def model(self):
        """Lazy-load sentence-transformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                logger.warning(
                    "sentence_transformers_not_installed",
                    hint="pip install sentence-transformers",
                )
                return None
        return self._model

    def embed_text(self, text: str) -> list[float] | None:
        """Generate 384-dim embedding for text."""
        if self.model is None:
            return None
        return self.model.encode(text).tolist()

    async def embed_jobs_batch(self, user_id: uuid.UUID | None = None, limit: int = 100) -> int:
        """Generate embeddings for jobs without them."""
        try:
            from sqlalchemy import select, text

            from app.jobs.models import Job
        except ImportError:
            logger.warning("job_model_not_available")
            return 0

        if self.model is None:
            return 0

        query = (
            select(Job)
            .where(Job.is_enriched == True)  # noqa: E712
            .limit(limit)
        )
        if user_id:
            query = query.where(Job.user_id == user_id)

        jobs = (await self.db.scalars(query)).all()

        updates: list[dict[str, str]] = []
        for job in jobs:
            job_text = (
                f"{job.title} {job.company_name or ''} "
                f"{job.summary_ai or ''} "
                f"{' '.join(job.skills_required or [])}"
            )
            embedding = self.embed_text(job_text)
            if embedding is None:
                continue

            updates.append({"emb": str(embedding), "id": job.id})

        if not updates:
            return 0

        try:
            for update in updates:
                await self.db.execute(
                    text("UPDATE jobs SET embedding = :emb WHERE id = :id"),
                    update,
                )
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.warning("embedding_batch_failed", error=str(e), attempted=len(updates))
            return 0

        logger.info("embeddings_generated", count=len(updates), total=len(jobs))
        return len(updates)
