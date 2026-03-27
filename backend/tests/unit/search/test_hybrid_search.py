from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from app.search.hybrid import (
    BM25_WEIGHT,
    RRF_K,
    SEMANTIC_WEIGHT,
    HybridSearchResult,
    HybridSearchService,
)


def _make_embedder(*, async_query: bool = True):
    if async_query:
        embedder = AsyncMock()
        embedder.embed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
        return embedder

    class _Embedder:
        def embed_text(self, text: str):  # noqa: ARG002
            return [0.1, 0.2, 0.3]

    return _Embedder()


def _make_db(*, is_pg: bool = False) -> AsyncMock:
    db = AsyncMock()
    bind_mock = MagicMock()
    dialect_mock = MagicMock()
    dialect_mock.name = "postgresql" if is_pg else "sqlite"
    bind_mock.dialect = dialect_mock
    type(db).bind = PropertyMock(return_value=bind_mock)
    return db


USER_ID = uuid.uuid4()


class TestHybridSearchResult:
    def test_creation(self):
        result = HybridSearchResult(
            job_id="abc123",
            rrf_score=0.5,
            bm25_rank=1,
            semantic_rank=3,
        )
        assert result.job_id == "abc123"
        assert result.rrf_score == 0.5
        assert result.bm25_rank == 1
        assert result.semantic_rank == 3


class TestHybridSearchService:
    @pytest.mark.asyncio
    async def test_fallback_on_sqlite(self):
        db = _make_db(is_pg=False)
        db.execute = AsyncMock(
            return_value=MagicMock(
                __iter__=lambda _: iter(
                    [SimpleNamespace(id="job-1"), SimpleNamespace(id="job-2")]
                )
            )
        )
        service = HybridSearchService(db, _make_embedder())
        results = await service.search("python engineer", USER_ID, limit=10)
        assert len(results) == 2
        assert results[0].job_id == "job-1"
        assert results[0].rrf_score > results[1].rrf_score

    @pytest.mark.asyncio
    async def test_bm25_only_when_embedding_unavailable(self):
        db = _make_db(is_pg=True)
        embedder = AsyncMock()
        embedder.embed_query = AsyncMock(return_value=None)
        db.execute = AsyncMock(
            return_value=MagicMock(
                __iter__=lambda _: iter([SimpleNamespace(id="job-1", rank=1)])
            )
        )
        service = HybridSearchService(db, embedder)
        results = await service.search("python", USER_ID, limit=10)
        assert len(results) == 1
        assert results[0].job_id == "job-1"
        assert results[0].bm25_rank == 1
        assert results[0].semantic_rank is None

    @pytest.mark.asyncio
    async def test_sync_embed_text_is_supported(self):
        db = _make_db(is_pg=True)
        db.execute = AsyncMock(return_value=MagicMock(__iter__=lambda _: iter([])))
        service = HybridSearchService(db, _make_embedder(async_query=False))
        await service.search("python", USER_ID, limit=10)
        params = db.execute.call_args[0][1]
        assert params["q_emb"] == str([0.1, 0.2, 0.3])

    @pytest.mark.asyncio
    async def test_hybrid_search_passes_rrf_params(self):
        db = _make_db(is_pg=True)
        db.execute = AsyncMock(return_value=MagicMock(__iter__=lambda _: iter([])))
        service = HybridSearchService(db, _make_embedder())
        await service.search("data scientist", USER_ID, limit=15, offset=5)

        sql = str(db.execute.call_args[0][0])
        params = db.execute.call_args[0][1]
        assert "embedding <=>" in sql
        assert "search_vector" in sql
        assert params["query"] == "data scientist"
        assert params["user_id"] == str(USER_ID)
        assert params["limit"] == 15
        assert params["offset"] == 5
        assert params["bm25_w"] == BM25_WEIGHT
        assert params["sem_w"] == SEMANTIC_WEIGHT
        assert params["k"] == RRF_K
