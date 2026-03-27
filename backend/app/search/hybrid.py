from __future__ import annotations

import inspect
import uuid
from dataclasses import dataclass
from typing import Any, cast

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

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
    """BM25 + semantic search with reciprocal-rank fusion."""

    def __init__(
        self,
        db: AsyncSession,
        embedder: Any,
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
        if not await self._is_postgres():
            return await self._fallback_keyword_search(query, user_id, limit, offset)

        query_embedding = await self._embed_query(query)
        if query_embedding is None:
            return await self._bm25_only_search(query, user_id, limit, offset)

        fetch_limit = limit * 3
        sql = text(
            """
            WITH bm25 AS (
                SELECT id, ROW_NUMBER() OVER (
                    ORDER BY ts_rank_cd(search_vector,
                                        plainto_tsquery('english', :query)) DESC
                ) AS rank
                FROM jobs
                WHERE user_id = :user_id
                  AND is_active = true
                  AND search_vector @@ plainto_tsquery('english', :query)
                LIMIT :fetch_limit
            ),
            semantic AS (
                SELECT id, ROW_NUMBER() OVER (
                    ORDER BY embedding <=> CAST(:q_emb AS vector)
                ) AS rank
                FROM jobs
                WHERE user_id = :user_id
                  AND is_active = true
                  AND embedding IS NOT NULL
                LIMIT :fetch_limit
            ),
            rrf AS (
                SELECT id, :bm25_w * (1.0 / (:k + rank)) AS score,
                       rank AS src_rank, 'bm25' AS src
                FROM bm25
                UNION ALL
                SELECT id, :sem_w * (1.0 / (:k + rank)) AS score,
                       rank AS src_rank, 'semantic' AS src
                FROM semantic
            ),
            combined AS (
                SELECT id, SUM(score) AS rrf_score,
                       MIN(CASE WHEN src = 'bm25' THEN src_rank END) AS bm25_rank,
                       MIN(CASE WHEN src = 'semantic' THEN src_rank END) AS semantic_rank
                FROM rrf
                GROUP BY id
                ORDER BY rrf_score DESC
                LIMIT :limit OFFSET :offset
            )
            SELECT id, rrf_score, bm25_rank, semantic_rank
            FROM combined
            ORDER BY rrf_score DESC
            """
        )

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
        sql = text(
            """
            SELECT id, ROW_NUMBER() OVER (
                ORDER BY ts_rank_cd(search_vector,
                                    plainto_tsquery('english', :query)) DESC
            ) AS rank
            FROM jobs
            WHERE user_id = :user_id
              AND is_active = true
              AND search_vector @@ plainto_tsquery('english', :query)
            ORDER BY rank
            LIMIT :limit OFFSET :offset
            """
        )

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
        like_pattern = f"%{query}%"
        sql = text(
            """
            SELECT id FROM jobs
            WHERE user_id = :user_id
              AND is_active = 1
              AND (
                  title LIKE :pattern
                  OR company_name LIKE :pattern
                  OR description_clean LIKE :pattern
                  OR summary_ai LIKE :pattern
              )
            LIMIT :limit OFFSET :offset
            """
        )

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
                rrf_score=1.0 / (index + 1),
                bm25_rank=index + 1,
                semantic_rank=None,
            )
            for index, row in enumerate(result)
        ]

    async def _embed_query(self, query: str) -> list[float] | None:
        embed_query = getattr(self.embedder, "embed_query", None)
        if callable(embed_query):
            result = embed_query(query)
            if inspect.isawaitable(result):
                awaited = await result
                return cast(list[float] | None, awaited)
            return cast(list[float] | None, result)

        embed_text = getattr(self.embedder, "embed_text", None)
        if callable(embed_text):
            return cast(list[float] | None, embed_text(query))
        return None

    async def _is_postgres(self) -> bool:
        try:
            bind = self.db.bind
            if bind is None:
                return False
            dialect = bind.dialect.name
            return dialect == "postgresql"
        except (AttributeError, TypeError):
            return False
