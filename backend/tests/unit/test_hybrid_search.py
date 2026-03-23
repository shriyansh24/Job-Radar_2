"""Tests for hybrid BM25 + semantic search with RRF."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from app.enrichment.embedding import EMBEDDING_DIM
from app.search.hybrid import (
    BM25_WEIGHT,
    RRF_K,
    SEMANTIC_WEIGHT,
    HybridSearchResult,
    HybridSearchService,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_embedder(dim: int = EMBEDDING_DIM) -> AsyncMock:
    embedder = AsyncMock()
    embedder.embed_query = AsyncMock(return_value=[0.1] * dim)
    return embedder


def _make_db(*, is_pg: bool = False) -> AsyncMock:
    db = AsyncMock()
    bind_mock = MagicMock()
    dialect_mock = MagicMock()
    dialect_mock.name = "postgresql" if is_pg else "sqlite"
    bind_mock.dialect = dialect_mock
    type(db).bind = PropertyMock(return_value=bind_mock)
    return db


USER_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# RRF math tests (pure Python, no DB)
# ---------------------------------------------------------------------------


class TestRRFScoring:
    def test_rrf_score_single_source(self):
        """A result appearing only in BM25 at rank 1 gets score = w / (k+1)."""
        score = BM25_WEIGHT * (1.0 / (RRF_K + 1))
        assert score == pytest.approx(BM25_WEIGHT / 61)

    def test_rrf_score_both_sources(self):
        """A result at rank 1 in both gets sum of both scores."""
        bm25_score = BM25_WEIGHT * (1.0 / (RRF_K + 1))
        sem_score = SEMANTIC_WEIGHT * (1.0 / (RRF_K + 1))
        combined = bm25_score + sem_score
        expected = (BM25_WEIGHT + SEMANTIC_WEIGHT) / (RRF_K + 1)
        assert combined == pytest.approx(expected)

    def test_rrf_higher_rank_gets_lower_score(self):
        """Rank 10 should get lower score than rank 1."""
        score_rank1 = BM25_WEIGHT * (1.0 / (RRF_K + 1))
        score_rank10 = BM25_WEIGHT * (1.0 / (RRF_K + 10))
        assert score_rank1 > score_rank10

    def test_weights_sum_to_one(self):
        assert BM25_WEIGHT + SEMANTIC_WEIGHT == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# HybridSearchResult dataclass
# ---------------------------------------------------------------------------


class TestHybridSearchResult:
    def test_creation(self):
        r = HybridSearchResult(job_id="abc123", rrf_score=0.5, bm25_rank=1, semantic_rank=3)
        assert r.job_id == "abc123"
        assert r.rrf_score == 0.5
        assert r.bm25_rank == 1
        assert r.semantic_rank == 3

    def test_optional_ranks(self):
        r = HybridSearchResult(job_id="abc123", rrf_score=0.5)
        assert r.bm25_rank is None
        assert r.semantic_rank is None


# ---------------------------------------------------------------------------
# SQLite fallback tests
# ---------------------------------------------------------------------------


class TestFallbackKeywordSearch:
    @pytest.mark.asyncio
    async def test_fallback_on_sqlite(self):
        """On SQLite, falls back to ILIKE keyword search."""
        db = _make_db(is_pg=False)
        embedder = _make_embedder()

        # Simulate SQLite returning rows
        row1 = SimpleNamespace(id="job-1")
        row2 = SimpleNamespace(id="job-2")
        db.execute = AsyncMock(return_value=MagicMock(__iter__=lambda s: iter([row1, row2])))

        svc = HybridSearchService(db, embedder)
        results = await svc.search("python engineer", USER_ID, limit=10)

        assert len(results) == 2
        assert results[0].job_id == "job-1"
        assert results[1].job_id == "job-2"
        # First result should have higher RRF score
        assert results[0].rrf_score > results[1].rrf_score

    @pytest.mark.asyncio
    async def test_fallback_returns_empty_on_no_matches(self):
        db = _make_db(is_pg=False)
        embedder = _make_embedder()
        db.execute = AsyncMock(return_value=MagicMock(__iter__=lambda s: iter([])))

        svc = HybridSearchService(db, embedder)
        results = await svc.search("nonexistent query", USER_ID, limit=10)

        assert results == []


# ---------------------------------------------------------------------------
# Service initialization
# ---------------------------------------------------------------------------


class TestHybridSearchServiceInit:
    def test_default_weights(self):
        db = _make_db()
        embedder = _make_embedder()
        svc = HybridSearchService(db, embedder)
        assert svc.bm25_weight == BM25_WEIGHT
        assert svc.semantic_weight == SEMANTIC_WEIGHT
        assert svc.rrf_k == RRF_K

    def test_custom_weights(self):
        db = _make_db()
        embedder = _make_embedder()
        svc = HybridSearchService(db, embedder, bm25_weight=0.7, semantic_weight=0.3, rrf_k=30)
        assert svc.bm25_weight == 0.7
        assert svc.semantic_weight == 0.3
        assert svc.rrf_k == 30


# ---------------------------------------------------------------------------
# Embedding failure fallback
# ---------------------------------------------------------------------------


class TestEmbeddingFailureFallback:
    @pytest.mark.asyncio
    async def test_bm25_only_when_embedding_fails(self):
        """When embed_query returns None, should fall back to BM25-only on PG."""
        db = _make_db(is_pg=True)
        embedder = AsyncMock()
        embedder.embed_query = AsyncMock(return_value=None)

        row1 = SimpleNamespace(id="job-1", rank=1)
        db.execute = AsyncMock(return_value=MagicMock(__iter__=lambda s: iter([row1])))

        svc = HybridSearchService(db, embedder)
        results = await svc.search("python", USER_ID, limit=10)

        assert len(results) == 1
        assert results[0].job_id == "job-1"
        assert results[0].bm25_rank == 1
        assert results[0].semantic_rank is None


# ---------------------------------------------------------------------------
# Postgres hybrid search path
# ---------------------------------------------------------------------------


class TestPostgresHybridSearch:
    @pytest.mark.asyncio
    async def test_hybrid_search_calls_execute(self):
        """On Postgres with valid embedding, should execute the hybrid SQL."""
        db = _make_db(is_pg=True)
        embedder = _make_embedder()

        row1 = SimpleNamespace(id="job-1", rrf_score=0.02, bm25_rank=1, semantic_rank=2)
        row2 = SimpleNamespace(id="job-2", rrf_score=0.01, bm25_rank=None, semantic_rank=1)
        db.execute = AsyncMock(return_value=MagicMock(__iter__=lambda s: iter([row1, row2])))

        svc = HybridSearchService(db, embedder)
        results = await svc.search("ML engineer", USER_ID, limit=20)

        assert len(results) == 2
        assert results[0].rrf_score > results[1].rrf_score
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_hybrid_search_passes_correct_params(self):
        """Verify the SQL params include query, embedding, user_id, weights."""
        db = _make_db(is_pg=True)
        embedder = _make_embedder()
        db.execute = AsyncMock(return_value=MagicMock(__iter__=lambda s: iter([])))

        svc = HybridSearchService(db, embedder)
        await svc.search("data scientist", USER_ID, limit=15, offset=5)

        call_args = db.execute.call_args
        params = call_args[0][1]  # positional arg 1 is the params dict
        assert params["query"] == "data scientist"
        assert params["user_id"] == str(USER_ID)
        assert params["limit"] == 15
        assert params["offset"] == 5
        assert params["bm25_w"] == BM25_WEIGHT
        assert params["sem_w"] == SEMANTIC_WEIGHT
        assert params["k"] == RRF_K
        assert params["fetch_limit"] == 15 * 3
        assert "embedding_v2 <=>" in str(call_args[0][0])
