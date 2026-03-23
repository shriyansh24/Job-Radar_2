"""Tests for the upgraded EmbeddingService (nomic-embed-text, 768d)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enrichment.embedding import EMBEDDING_DIM, EmbeddingService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeOnnxModel:
    """Fake sentence-transformers model returning 768-dim vectors."""

    def encode(self, text_or_texts):
        import random

        random.seed(42)
        if isinstance(text_or_texts, list):
            return [[random.random() for _ in range(EMBEDDING_DIM)] for _ in text_or_texts]
        return [random.random() for _ in range(EMBEDDING_DIM)]


def _make_settings(**overrides):
    defaults = {
        "ollama_enabled": False,
        "ollama_base_url": "http://localhost:11434",
        "ollama_embed_model": "nomic-embed-text",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _job(job_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=job_id,
        title="Software Engineer",
        company_name="Acme",
        summary_ai="Build APIs",
        skills_required=["Python"],
        is_enriched=True,
    )


# ---------------------------------------------------------------------------
# ONNX embedding tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_returns_768_dim_vector():
    db = AsyncMock()
    settings = _make_settings()
    svc = EmbeddingService(db, settings)
    svc._onnx_model = _FakeOnnxModel()

    result = await svc.embed("test text")

    assert result is not None
    assert len(result) == EMBEDDING_DIM


@pytest.mark.asyncio
async def test_embed_query_uses_search_query_prefix():
    db = AsyncMock()
    settings = _make_settings()
    svc = EmbeddingService(db, settings)

    calls = []

    class _CapturingModel:
        def encode(self, text):
            calls.append(text)
            return [0.1] * EMBEDDING_DIM

    svc._onnx_model = _CapturingModel()

    await svc.embed_query("machine learning engineer")

    assert len(calls) == 1
    assert calls[0].startswith("search_query: ")


@pytest.mark.asyncio
async def test_embed_document_uses_search_document_prefix():
    db = AsyncMock()
    settings = _make_settings()
    svc = EmbeddingService(db, settings)

    calls = []

    class _CapturingModel:
        def encode(self, text):
            calls.append(text)
            return [0.1] * EMBEDDING_DIM

    svc._onnx_model = _CapturingModel()

    await svc.embed("job description text")

    assert len(calls) == 1
    assert calls[0].startswith("search_document: ")


@pytest.mark.asyncio
async def test_batch_embed_returns_list_of_768_vectors():
    db = AsyncMock()
    settings = _make_settings()
    svc = EmbeddingService(db, settings)
    svc._onnx_model = _FakeOnnxModel()

    texts = ["text one", "text two", "text three"]
    results = await svc.batch_embed(texts)

    assert len(results) == 3
    for vec in results:
        assert len(vec) == EMBEDDING_DIM


@pytest.mark.asyncio
async def test_embed_returns_none_when_onnx_not_available():
    db = AsyncMock()
    settings = _make_settings()
    svc = EmbeddingService(db, settings)

    with patch.object(svc, "_load_onnx_model", side_effect=ImportError("no onnx")):
        result = await svc.embed("test")

    assert result is None


@pytest.mark.asyncio
async def test_ollama_fallback_to_onnx():
    """When Ollama is enabled but fails, should fall back to ONNX."""
    db = AsyncMock()
    settings = _make_settings(ollama_enabled=True)
    svc = EmbeddingService(db, settings)
    svc._onnx_model = _FakeOnnxModel()

    with patch.object(svc, "_embed_ollama", side_effect=Exception("connection refused")):
        result = await svc.embed("test text")

    assert result is not None
    assert len(result) == EMBEDDING_DIM


@pytest.mark.asyncio
async def test_embed_returns_none_when_vector_dimension_is_invalid():
    db = AsyncMock()
    settings = _make_settings()
    svc = EmbeddingService(db, settings)

    class _WrongDimModel:
        def encode(self, text):  # noqa: ARG002
            return [0.1] * 3

    svc._onnx_model = _WrongDimModel()

    result = await svc.embed("test text")

    assert result is None


@pytest.mark.asyncio
async def test_embed_ollama_returns_none_when_no_embedding_is_produced():
    db = AsyncMock()
    settings = _make_settings(ollama_enabled=True)
    svc = EmbeddingService(db, settings)

    response = MagicMock()
    response.json.return_value = {"embeddings": []}
    response.raise_for_status.return_value = None

    client = AsyncMock()
    client.post.return_value = response
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=client):
        result = await svc._embed_ollama("search_document: test")

    assert result is None


@pytest.mark.asyncio
async def test_embed_text_legacy_compat():
    """Legacy embed_text method still works."""
    db = AsyncMock()
    settings = _make_settings()
    svc = EmbeddingService(db, settings)
    svc._onnx_model = _FakeOnnxModel()

    result = svc.embed_text("test text")

    assert result is not None
    assert len(result) == EMBEDDING_DIM


@pytest.mark.asyncio
async def test_embed_jobs_batch_commits_on_success():
    db = AsyncMock()
    scalars_result = MagicMock()
    scalars_result.all.return_value = [_job("job-1"), _job("job-2")]
    db.scalars = AsyncMock(return_value=scalars_result)

    settings = _make_settings()
    svc = EmbeddingService(db, settings)
    svc._onnx_model = _FakeOnnxModel()

    count = await svc.embed_jobs_batch(limit=2)

    assert count == 2
    assert db.execute.await_count == 2
    assert "embedding_v2" in str(db.execute.await_args_list[0].args[0])
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_embed_jobs_batch_rolls_back_on_failure():
    db = AsyncMock()
    scalars_result = MagicMock()
    scalars_result.all.return_value = [_job("job-1"), _job("job-2")]
    db.scalars = AsyncMock(return_value=scalars_result)
    db.execute.side_effect = [None, RuntimeError("boom")]

    settings = _make_settings()
    svc = EmbeddingService(db, settings)
    svc._onnx_model = _FakeOnnxModel()

    count = await svc.embed_jobs_batch(limit=2)

    assert count == 0
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


def test_embedding_dim_constant_is_768():
    assert EMBEDDING_DIM == 768
