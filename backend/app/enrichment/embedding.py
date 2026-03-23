from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.config import Settings

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# Embedding dimension for nomic-embed-text v1.5
EMBEDDING_DIM = 768


class EmbeddingService:
    """Generate and manage embeddings for semantic search.

    Supports two backends:
    - Ollama (preferred when enabled): calls local nomic-embed-text model
    - ONNX fallback: sentence-transformers with ONNX backend

    All embeddings are 768-dimensional (nomic-embed-text v1.5).
    Nomic requires task prefixes: ``search_document:`` for indexing,
    ``search_query:`` for queries.
    """

    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self._settings = settings or Settings()
        self._onnx_model: object | None = None

    async def embed(self, text: str, task_prefix: str = "search_document") -> list[float] | None:
        """Embed text with nomic-embed-text. Returns 768-dim vector or None."""
        prefixed = f"{task_prefix}: {text}"

        if self._settings.ollama_enabled:
            try:
                return await self._embed_ollama(prefixed)
            except Exception:
                logger.debug("ollama_embed_fallback", hint="falling back to ONNX")

        return self._embed_onnx(prefixed)

    async def embed_query(self, text: str) -> list[float] | None:
        """Embed a search query (uses search_query prefix)."""
        return await self.embed(text, task_prefix="search_query")

    async def batch_embed(
        self, texts: list[str], task_prefix: str = "search_document"
    ) -> list[list[float]]:
        """Batch embed texts. Uses ONNX true-batch when possible."""
        if self._settings.ollama_enabled:
            results: list[list[float]] = []
            for text in texts:
                vec = await self.embed(text, task_prefix)
                if vec is not None:
                    results.append(vec)
            return results

        prefixed = [f"{task_prefix}: {t}" for t in texts]
        return self._batch_embed_onnx(prefixed)

    async def _embed_ollama(self, text: str) -> list[float]:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._settings.ollama_base_url}/api/embed",
                json={"model": self._settings.ollama_embed_model, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings = data.get("embeddings", [])
            if embeddings:
                return embeddings[0]  # type: ignore[no-any-return]
            return []

    def _load_onnx_model(self) -> object:
        if self._onnx_model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._onnx_model = SentenceTransformer(
                    "nomic-ai/nomic-embed-text-v1.5",
                    backend="onnx",
                    trust_remote_code=True,
                )
            except ImportError:
                logger.warning(
                    "sentence_transformers_not_installed",
                    hint="pip install sentence-transformers onnxruntime",
                )
                raise
        return self._onnx_model

    def _embed_onnx(self, text: str) -> list[float] | None:
        try:
            model = self._load_onnx_model()
            result = model.encode(text)  # type: ignore[union-attr]
            return result.tolist() if hasattr(result, "tolist") else list(result)
        except ImportError:
            return None

    def _batch_embed_onnx(self, texts: list[str]) -> list[list[float]]:
        try:
            model = self._load_onnx_model()
            result = model.encode(texts)  # type: ignore[union-attr]
            return result.tolist() if hasattr(result, "tolist") else list(result)
        except ImportError:
            return []

    # -- Legacy compatibility: embed_text / embed_jobs_batch ----------------

    def embed_text(self, text: str) -> list[float] | None:
        """Legacy sync embedding. New code should use ``await embed()``."""
        return self._embed_onnx(f"search_document: {text}")

    async def embed_jobs_batch(self, user_id: uuid.UUID | None = None, limit: int = 100) -> int:
        """Generate v2 embeddings (768d) for jobs missing them."""
        try:
            from sqlalchemy import select, text

            from app.jobs.models import Job
        except ImportError:
            logger.warning("job_model_not_available")
            return 0

        query = (
            select(Job)
            .where(Job.is_enriched.is_(True))
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
            embedding = await self.embed(job_text, task_prefix="search_document")
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
