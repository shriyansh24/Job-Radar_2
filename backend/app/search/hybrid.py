from __future__ import annotations

import inspect
import uuid
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files as _resource_files
from typing import Any, cast

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import TextClause

logger = structlog.get_logger()

RRF_K = 60
BM25_WEIGHT = 0.4
SEMANTIC_WEIGHT = 0.6

_BM25_BASE_QUERY = """
SELECT id, ROW_NUMBER() OVER (
    ORDER BY ts_rank_cd(search_vector,
                        plainto_tsquery('english', :query)) DESC
) AS rank
FROM jobs
WHERE user_id = :user_id
  AND is_active = true
  AND search_vector @@ plainto_tsquery('english', :query)
"""


def _load_sql(filename: str) -> str:
    try:
        sql_text = (
            _resource_files("app.search")
            .joinpath("sql")
            .joinpath(filename)
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, TypeError) as exc:
        raise RuntimeError(
            f"Could not load search SQL template '{filename}'. "
            "Ensure app/search/sql/ files are included in the package data."
        ) from exc
    return sql_text.replace("__BM25_BASE_QUERY__", _BM25_BASE_QUERY.strip())


@lru_cache(maxsize=None)
def _get_hybrid_search_sql() -> TextClause:
    return text(_load_sql("hybrid_search.sql"))


@lru_cache(maxsize=None)
def _get_bm25_only_search_sql() -> TextClause:
    return text(_load_sql("bm25_only_search.sql"))


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
        params = {
            "query": query,
            "q_emb": str(query_embedding),
            "user_id": str(user_id),
            "fetch_limit": fetch_limit,
            "limit": limit,
            "offset": offset,
            "bm25_w": self.bm25_weight,
            "sem_w": self.semantic_weight,
            "k": self.rrf_k,
        }

        def _map_func(row: Any, _: int) -> HybridSearchResult:
            return HybridSearchResult(
                job_id=row.id,
                rrf_score=float(row.rrf_score),
                bm25_rank=row.bm25_rank,
                semantic_rank=row.semantic_rank,
            )

        return await self._execute_search_query(_get_hybrid_search_sql(), params, _map_func)

    async def _bm25_only_search(
        self,
        query: str,
        user_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> list[HybridSearchResult]:
        params = {
            "query": query,
            "user_id": str(user_id),
            "limit": limit,
            "offset": offset,
        }

        def _map_func(row: Any, _: int) -> HybridSearchResult:
            return HybridSearchResult(
                job_id=row.id,
                rrf_score=self.bm25_weight * (1.0 / (self.rrf_k + row.rank)),
                bm25_rank=int(row.rank),
                semantic_rank=None,
            )

        return await self._execute_search_query(_get_bm25_only_search_sql(), params, _map_func)

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

        params = {
            "user_id": str(user_id),
            "pattern": like_pattern,
            "limit": limit,
            "offset": offset,
        }

        def _map_func(row: Any, index: int) -> HybridSearchResult:
            return HybridSearchResult(
                job_id=row.id,
                rrf_score=1.0 / (index + 1),
                bm25_rank=index + 1,
                semantic_rank=None,
            )

        return await self._execute_search_query(sql, params, _map_func)

    async def _execute_search_query(
        self, sql: Any, params: dict[str, Any], map_func: Any
    ) -> list[HybridSearchResult]:
        result = await self.db.execute(sql, params)
        return [map_func(row, index) for index, row in enumerate(result)]

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
