from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

import app.workers.enrichment_worker as enrichment_worker


@pytest.mark.asyncio
async def test_run_enrichment_batch_scopes_to_requested_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_context = AsyncMock()
    db_context.__aenter__.return_value = object()
    db_context.__aexit__.return_value = False
    llm_client = Mock()
    llm_client.close = AsyncMock()
    service = Mock()
    service.enrich_batch = AsyncMock(return_value=3)
    logger = Mock()
    scoped_user_id = uuid.uuid4()

    monkeypatch.setattr(enrichment_worker, "async_session_factory", lambda: db_context)
    monkeypatch.setattr(enrichment_worker, "LLMClient", Mock(return_value=llm_client))
    monkeypatch.setattr(enrichment_worker, "EnrichmentService", Mock(return_value=service))
    monkeypatch.setattr(enrichment_worker, "logger", logger)

    await enrichment_worker.run_enrichment_batch(user_id=str(scoped_user_id))

    service.enrich_batch.assert_awaited_once_with(user_id=scoped_user_id, limit=50)
    llm_client.close.assert_awaited_once()
    logger.info.assert_called_once_with(
        "enrichment_completed",
        jobs_enriched=3,
        scoped_user_id=str(scoped_user_id),
    )


@pytest.mark.asyncio
async def test_run_enrichment_batch_raises_for_missing_scope_and_clears_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llm_client = Mock()
    llm_client.close = AsyncMock()
    redis = Mock()
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock()
    logger = Mock()

    monkeypatch.setattr(enrichment_worker, "LLMClient", Mock(return_value=llm_client))
    monkeypatch.setattr(enrichment_worker, "logger", logger)

    with pytest.raises(RuntimeError, match="requires a scoped user_id"):
        await enrichment_worker.run_enrichment_batch(
            ctx={"redis": redis, "job_id": "job-123"},
        )

    redis.delete.assert_awaited_once_with(
        enrichment_worker._build_job_metadata_key("job-123")
    )
    llm_client.close.assert_awaited_once()
    logger.warning.assert_called_once_with(
        "enrichment_batch_skipped",
        reason="missing_user_scope",
    )


@pytest.mark.asyncio
async def test_run_enrichment_batch_preserves_metadata_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_context = AsyncMock()
    db_context.__aenter__.return_value = object()
    db_context.__aexit__.return_value = False
    llm_client = Mock()
    llm_client.close = AsyncMock()
    service = Mock()
    service.enrich_batch = AsyncMock(side_effect=RuntimeError("boom"))
    logger = Mock()
    scoped_user_id = uuid.uuid4()
    redis = Mock()
    redis.get = AsyncMock(return_value='{"user_id":"%s"}' % scoped_user_id)
    redis.delete = AsyncMock()

    monkeypatch.setattr(enrichment_worker, "async_session_factory", lambda: db_context)
    monkeypatch.setattr(enrichment_worker, "LLMClient", Mock(return_value=llm_client))
    monkeypatch.setattr(enrichment_worker, "EnrichmentService", Mock(return_value=service))
    monkeypatch.setattr(enrichment_worker, "logger", logger)

    with pytest.raises(RuntimeError, match="boom"):
        await enrichment_worker.run_enrichment_batch(
            ctx={"redis": redis, "job_id": "job-456"},
        )

    service.enrich_batch.assert_awaited_once_with(user_id=scoped_user_id, limit=50)
    redis.delete.assert_not_awaited()
    llm_client.close.assert_awaited_once()
    logger.exception.assert_called_once_with(
        "enrichment_worker_failed",
        scoped_user_id=str(scoped_user_id),
    )
