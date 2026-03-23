from __future__ import annotations

import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.enrichment.embedding import EmbeddingService

logger = structlog.get_logger()

# Reciprocal Rank Fusion constant (standard value from literature)
RRF_K = 60
BM25_WEIGHT = 0.4
SEMANTIC_WEIGHT = 0.6


@dataclass
class HybridSearchResult:
    job_id: str
    rrf_score: float
    bm25_rank: int | None = None
    semantic_rank: int | None = None


class HybridSearchService:
    """BM25 (tsvector) + pgvector semantic search with Reciprocal Rank Fusion.

    Combines PostgreSQL full-text search for keyword matching with pgvector
    cosine similarity for semantic matching. Results are fused using RRF.

    Falls back to ILIKE keyword search when running on SQLite (tests).
    """

    def __init__(
        self,
        db: AsyncSession,
        embedder: EmbeddingService,
        bm25_weight: float = BM25_WEIGHT,
        semantic_weight: float = SEMANTIC_WEIGHT,
        rrf_k: int = RRF_K,
    ) -> None:
        self.db = db
        self.embedder = embedder
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        self.rrf_k = rrf_k

    async def search(
        self,
        query: str,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[HybridSearchResult]:
        """Run hybrid BM25+semantic search with RRF fusion.

        Returns a list of HybridSearchResult sorted by RRF score descending.
        Falls back to keyword-only search on non-PostgreSQL databases.
        """
        is_pg = await self._is_postgres()
        if not is_pg:
            return await self._fallback_keyword_search(query, user_id, limit, offset)

        query_embedding = await self.embedder.embed_query(query)
        if query_embedding is None:
            return await self._bm25_only_search(query, user_id, limit, offset)

        fetch_limit = limit * 3  # Over-fetch for better fusion

        sql = text("""
            WITH bm25 AS (
                SELECT id, ROW_NUMBER() OVER (
                    ORDER BY ts_rank_cd(search_vector,
                                        plainto_tsquery('english', :query)) DESC
                ) as rank
                FROM jobs
                WHERE user_id = :user_id
                  AND is_active = true
                  AND search_vector @@ plainto_tsquery('english', :query)
                LIMIT :fetch_limit
            ),
            semantic AS (
                SELECT id, ROW_NUMBER() OVER (
                    ORDER BY embedding_v2 <=> :q_emb::vector
                ) as rank
                FROM jobs
                WHERE user_id = :user_id
                  AND is_active = true
                  AND embedding_v2 IS NOT NULL
                LIMIT :fetch_limit
            ),
            rrf AS (
                SELECT id, :bm25_w * (1.0 / (:k + rank)) as score,
                       rank as src_rank, 'bm25' as src
                FROM bm25
                UNION ALL
                SELECT id, :sem_w * (1.0 / (:k + rank)) as score,
                       rank as src_rank, 'semantic' as src
                FROM semantic
            ),
            combined AS (
                SELECT id, SUM(score) as rrf_score,
                       MIN(CASE WHEN src = 'bm25' THEN src_rank END) as bm25_rank,
                       MIN(CASE WHEN src = 'semantic' THEN src_rank END) as semantic_rank
                FROM rrf
                GROUP BY id
                ORDER BY rrf_score DESC
                LIMIT :limit OFFSET :offset
            )
            SELECT id, rrf_score, bm25_rank, semantic_rank
            FROM combined
            ORDER BY rrf_score DESC
        """)

        result = await self.db.execute(
            sql,
            {
                "query": query,
                "q_emb": str(query_embedding),
                "user_id": str(user_id),
                "fetch_limit": fetch_limit,
                "limit": limit,
                "offset": offset,
                "bm25_w": self.bm25_weight,
                "sem_w": self.semantic_weight,
                "k": self.rrf_k,
            },
        )

        return [
            HybridSearchResult(
                job_id=row.id,
                rrf_score=float(row.rrf_score),
                bm25_rank=row.bm25_rank,
                semantic_rank=row.semantic_rank,
            )
            for row in result
        ]

    async def _bm25_only_search(
        self,
        query: str,
        user_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> list[HybridSearchResult]:
        """BM25-only search when semantic embedding is unavailable."""
        sql = text("""
            SELECT id, ROW_NUMBER() OVER (
                ORDER BY ts_rank_cd(search_vector,
                                    plainto_tsquery('english', :query)) DESC
            ) as rank
            FROM jobs
            WHERE user_id = :user_id
              AND is_active = true
              AND search_vector @@ plainto_tsquery('english', :query)
            ORDER BY rank
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(
            sql,
            {
                "query": query,
                "user_id": str(user_id),
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            HybridSearchResult(
                job_id=row.id,
                rrf_score=self.bm25_weight * (1.0 / (self.rrf_k + row.rank)),
                bm25_rank=int(row.rank),
                semantic_rank=None,
            )
            for row in result
        ]

    async def _fallback_keyword_search(
        self,
        query: str,
        user_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> list[HybridSearchResult]:
        """ILIKE fallback for SQLite (test environments)."""
        like_pattern = f"%{query}%"
        sql = text("""
            SELECT id FROM jobs
            WHERE user_id = :user_id
              AND is_active = 1
              AND (
                  title LIKE :pattern
                  OR company_name LIKE :pattern
                  OR description_clean LIKE :pattern
              )
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(
            sql,
            {
                "user_id": str(user_id),
                "pattern": like_pattern,
                "limit": limit,
                "offset": offset,
            },
        )

        return [
            HybridSearchResult(
                job_id=row.id,
                rrf_score=1.0 / (idx + 1),
                bm25_rank=idx + 1,
                semantic_rank=None,
            )
            for idx, row in enumerate(result)
        ]

    async def _is_postgres(self) -> bool:
        """Detect if the current database is PostgreSQL."""
        try:
            dialect = self.db.bind.dialect.name  # type: ignore[union-attr]
            return dialect == "postgresql"
        except (AttributeError, TypeError):
            return False
