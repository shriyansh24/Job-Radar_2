from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.enrichment.embedding import EMBEDDING_DIM, EmbeddingService


class _FakeModel:
    def encode(self, text: str):  # noqa: ARG002
        return [0.1] * EMBEDDING_DIM


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


@pytest.mark.asyncio
async def test_embed_jobs_batch_rolls_back_on_store_failure():
    db = AsyncMock()
    scalars_result = MagicMock()
    scalars_result.all.return_value = [_job("job-1"), _job("job-2")]
    db.scalars = AsyncMock(return_value=scalars_result)
    db.execute.side_effect = [None, RuntimeError("boom")]

    service = EmbeddingService(db, _make_settings())
    service._onnx_model = _FakeModel()

    count = await service.embed_jobs_batch(limit=2)

    assert count == 0
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_embed_jobs_batch_commits_full_batch_when_all_updates_succeed():
    db = AsyncMock()
    scalars_result = MagicMock()
    scalars_result.all.return_value = [_job("job-1"), _job("job-2")]
    db.scalars = AsyncMock(return_value=scalars_result)

    service = EmbeddingService(db, _make_settings())
    service._onnx_model = _FakeModel()

    count = await service.embed_jobs_batch(limit=2)

    assert count == 2
    assert db.execute.await_count == 2
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()
