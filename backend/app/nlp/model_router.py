"""Task-based model router with automatic fallback.

Routes LLM requests to the optimal model for a given task type,
with automatic fallback through a chain of models on failure.

Uses the shared ``LLMClient`` (httpx-based) — no litellm dependency.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.enrichment.llm_client import LLMClient

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Task → model preference mappings
# ---------------------------------------------------------------------------
# Each task maps to an ordered list of model strings.  The router tries
# them left-to-right until one succeeds.

TASK_MODELS: dict[str, list[str]] = {
    "enrichment": [
        "anthropic/claude-3-5-haiku-20241022",
        "openai/gpt-4o-mini",
        "openai/gpt-3.5-turbo",
    ],
    "cover_letter": [
        "anthropic/claude-3-5-sonnet-20241022",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
    ],
    "resume_tailor": [
        "anthropic/claude-3-5-sonnet-20241022",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
    ],
    "interview": [
        "anthropic/claude-3-5-haiku-20241022",
        "openai/gpt-4o-mini",
        "openai/gpt-3.5-turbo",
    ],
    "salary": [
        "anthropic/claude-3-5-haiku-20241022",
        "openai/gpt-4o-mini",
    ],
    "copilot": [
        "anthropic/claude-3-5-sonnet-20241022",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
    ],
    # Catch-all default
    "default": [
        "anthropic/claude-3-5-haiku-20241022",
        "openai/gpt-4o-mini",
    ],
}


class ModelRouter:
    """Routes LLM completion requests to the best available model for a task.

    Wraps the shared ``LLMClient`` and iterates through the fallback chain
    defined in ``TASK_MODELS`` when a model fails.

    Usage::

        router = ModelRouter(llm_client)
        text = await router.complete("cover_letter", messages)
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client

    def _models_for_task(self, task: str) -> list[str]:
        """Return the ordered model list for *task*, falling back to default."""
        return TASK_MODELS.get(task, TASK_MODELS["default"])

    async def complete(
        self,
        task: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 1500,
        response_format: dict[str, str] | None = None,
    ) -> str:
        """Route a chat completion request to the best model for *task*.

        Tries models in order; on failure (HTTP error, timeout), falls
        through to the next candidate.

        Returns the response text or raises ``RuntimeError`` if all
        models are exhausted.
        """
        models = self._models_for_task(task)
        last_exc: Exception | None = None

        for model in models:
            try:
                logger.debug("model_router_trying", task=task, model=model)
                text = await self._llm.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model,
                    response_format=response_format,
                )
                logger.debug("model_router_succeeded", task=task, model=model)
                return text
            except (httpx.HTTPStatusError, httpx.TimeoutException) as exc:
                logger.warning(
                    "model_router_failed",
                    task=task,
                    model=model,
                    error=str(exc),
                )
                last_exc = exc
            except Exception as exc:
                logger.warning(
                    "model_router_unexpected",
                    task=task,
                    model=model,
                    error=str(exc),
                )
                last_exc = exc

        raise RuntimeError(
            f"ModelRouter: all models exhausted for task '{task}'. "
            f"Last error: {last_exc}"
        ) from last_exc

    async def complete_json(
        self,
        task: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """Route a JSON chat completion using the fallback chain.

        Uses ``response_format: json_object`` and parses the result.
        Falls back across models on failure.
        """
        import json

        models = self._models_for_task(task)
        last_exc: Exception | None = None

        for model in models:
            try:
                logger.debug("model_router_json_trying", task=task, model=model)
                result = await self._llm.chat_json(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model,
                )
                if result:
                    logger.debug("model_router_json_succeeded", task=task, model=model)
                    return result
                # Empty result — try next model
                logger.warning("model_router_json_empty", task=task, model=model)
            except (httpx.HTTPStatusError, httpx.TimeoutException, json.JSONDecodeError) as exc:
                logger.warning(
                    "model_router_json_failed",
                    task=task,
                    model=model,
                    error=str(exc),
                )
                last_exc = exc
            except Exception as exc:
                logger.warning(
                    "model_router_json_unexpected",
                    task=task,
                    model=model,
                    error=str(exc),
                )
                last_exc = exc

        if last_exc:
            raise RuntimeError(
                f"ModelRouter: all models exhausted for JSON task '{task}'. "
                f"Last error: {last_exc}"
            ) from last_exc
        return {}
