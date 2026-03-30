from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.nlp.model_router import TASK_MODELS, ModelRouter


@pytest.mark.asyncio
async def test_complete_json_raises_when_all_models_return_empty():
    llm = MagicMock()
    llm.chat_json = AsyncMock(return_value={})
    router = ModelRouter(llm)

    with pytest.raises(RuntimeError, match="all models exhausted for JSON task 'interview'"):
        await router.complete_json(
            task="interview",
            messages=[{"role": "user", "content": "Generate interview questions"}],
        )

    assert llm.chat_json.await_count == len(TASK_MODELS["interview"])
