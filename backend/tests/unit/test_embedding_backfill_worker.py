from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enrichment.embedding import EMBEDDING_DIM
from app.workers.embedding_backfill_worker import run_embedding_backfill


@pytest.mark.asyncio
async def test_embedding_backfill_targets_embedding_v2_only():
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=1)

    scalars_result = MagicMock()
    scalars_result.all.return_value = [
        SimpleNamespace(
            id="job-1",
            title="Software Engineer",
            company_name="Acme",
            summary_ai="Build APIs",
            skills_required=["Python"],
            location="Remote",
            description_clean="A long description",
        )
    ]
    db.scalars = AsyncMock(return_value=scalars_result)

    embedder = AsyncMock()
    embedder.embed = AsyncMock(return_value=[0.1] * EMBEDDING_DIM)

    @asynccontextmanager
    async def fake_session_factory():
        yield db

    with (
        patch(
            "app.workers.embedding_backfill_worker.async_session_factory",
            fake_session_factory,
        ),
        patch(
            "app.workers.embedding_backfill_worker.EmbeddingService",
            return_value=embedder,
        ),
    ):
        await run_embedding_backfill()

    assert "embedding_v2 IS NULL" in str(db.scalar.await_args.args[0])
    assert "embedding_v2 IS NULL" in str(db.scalars.await_args.args[0])
    assert "embedding_v2" in str(db.execute.await_args.args[0])
    db.commit.assert_awaited_once()
