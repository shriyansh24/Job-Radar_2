"""HybridLLMRouter: local Ollama-first routing with cloud fallback.

Feature E2 — provides an ``OllamaClient`` for local inference and a
``HybridLLMRouter`` that transparently falls back to the cloud
``LLMClient`` when the local instance is unavailable or unhealthy.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx
import structlog

from app.config import Settings
from app.enrichment.llm_client import LLMClient

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Think-tag stripping (Qwen3 emits <think>…</think> reasoning blocks)
# ---------------------------------------------------------------------------

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_think_tags(text: str) -> str:
    """Remove ``<think>…</think>`` blocks produced by Qwen3 models."""
    return _THINK_RE.sub("", text).strip()


# ---------------------------------------------------------------------------
# OllamaClient
# ---------------------------------------------------------------------------


class OllamaClient:
    """Async REST client for a local Ollama instance."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "qwen3:8b-q5_k_m",
        num_ctx: int = 8192,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.num_ctx = num_ctx
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=120.0,
            )
        return self._client

    # -- health -------------------------------------------------------------

    async def health_check(self) -> bool:
        """Return *True* if Ollama is reachable (GET /api/tags, 3 s timeout)."""
        try:
            resp = await self.client.get("/api/tags", timeout=3.0)
            return resp.status_code == 200  # noqa: PLR2004
        except (httpx.HTTPError, OSError):
            return False

    # -- chat ---------------------------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
        strip_think: bool = True,
    ) -> str:
        """Non-streaming chat completion via ``/api/chat``."""
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": self.num_ctx,
            },
        }
        resp = await self.client.post("/api/chat", json=payload)
        resp.raise_for_status()
        content: str = resp.json().get("message", {}).get("content", "")
        if strip_think:
            content = strip_think_tags(content)
        return content

    # -- chat_json ----------------------------------------------------------

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Chat and parse the response as JSON.

        Handles markdown code fences (```json … ```) gracefully.
        Returns an empty dict on parse failure — never raises for JSON errors.
        """
        raw = await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            strip_think=True,
        )
        if not raw:
            return {}

        # Direct parse
        try:
            return json.loads(raw)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            pass

        # Strip markdown fences and retry
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            return json.loads(raw[start:end])  # type: ignore[no-any-return]
        except (ValueError, json.JSONDecodeError):
            logger.warning(
                "ollama_json_parse_failed",
                raw_len=len(raw),
                raw_head=raw[:200],
            )
            return {}

    # -- chat_stream --------------------------------------------------------

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """Yield content chunks from Ollama's newline-delimited JSON stream."""
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_ctx": self.num_ctx,
            },
        }
        async with self.client.stream("POST", "/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

    # -- embed --------------------------------------------------------------

    async def embed(
        self,
        text: str,
        model: str = "nomic-embed-text",
    ) -> list[float]:
        """Generate an embedding vector via ``/api/embed``."""
        payload: dict[str, Any] = {
            "model": model,
            "input": text,
        }
        resp = await self.client.post("/api/embed", json=payload)
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns {"embeddings": [[…]]}
        embeddings = data.get("embeddings", [])
        if embeddings:
            return embeddings[0]  # type: ignore[no-any-return]
        return []

    # -- lifecycle ----------------------------------------------------------

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------


class _CircuitBreaker:
    """Minimal circuit breaker: opens after *threshold* failures within
    *window* seconds and stays open for *cooldown* seconds.
    """

    def __init__(
        self,
        threshold: int = 3,
        window: float = 60.0,
        cooldown: float = 300.0,
    ) -> None:
        self.threshold = threshold
        self.window = window
        self.cooldown = cooldown
        self._failures: list[float] = []
        self._open_until: float = 0.0

    @property
    def is_open(self) -> bool:
        now = time.monotonic()
        if now < self._open_until:
            return True
        # If cooldown expired, reset
        if self._open_until > 0 and now >= self._open_until:
            self.reset()
        return False

    def record_failure(self) -> None:
        now = time.monotonic()
        self._failures = [t for t in self._failures if now - t < self.window]
        self._failures.append(now)
        if len(self._failures) >= self.threshold:
            self._open_until = now + self.cooldown
            logger.warning(
                "circuit_breaker_opened",
                cooldown=self.cooldown,
                failures=len(self._failures),
            )

    def record_success(self) -> None:
        self._failures.clear()
        self._open_until = 0.0

    def reset(self) -> None:
        self._failures.clear()
        self._open_until = 0.0


# ---------------------------------------------------------------------------
# HybridLLMRouter
# ---------------------------------------------------------------------------


class HybridLLMRouter:
    """Routes LLM calls to local Ollama when healthy, cloud otherwise.

    Exposes the same ``chat`` / ``chat_json`` interface as ``LLMClient``
    so callers can swap transparently.
    """

    TASK_MODEL_MAP: dict[str, str] = {
        "resume_tailor": "qwen3:8b",
        "cover_letter": "qwen3:8b",
        "field_classify": "qwen3:4b",
        "job_parse": "qwen3:4b",
        "embedding": "nomic-embed-text",
    }

    def __init__(
        self,
        ollama: OllamaClient,
        cloud: LLMClient,
        settings: Settings,
    ) -> None:
        self.ollama = ollama
        self.cloud = cloud
        self.settings = settings
        self._breaker = _CircuitBreaker(threshold=3, window=60.0, cooldown=300.0)

    def _resolve_model(self, task: str, model: str | None) -> str | None:
        """Return the Ollama model name for *task*, or *model* override."""
        if model:
            return model
        return self.TASK_MODEL_MAP.get(task)

    async def _try_local(
        self,
        messages: list[dict[str, str]],
        model: str | None,
        **kwargs: Any,
    ) -> str | None:
        """Attempt an Ollama call.  Returns *None* on any failure."""
        if not self.settings.ollama_enabled:
            return None
        if self._breaker.is_open:
            return None
        try:
            result = await self.ollama.chat(messages, model=model, **kwargs)
            self._breaker.record_success()
            return result
        except Exception:
            self._breaker.record_failure()
            logger.info("ollama_call_failed", model=model, exc_info=True)
            return None

    async def _try_local_json(
        self,
        messages: list[dict[str, str]],
        model: str | None,
    ) -> dict[str, Any] | None:
        """Attempt an Ollama JSON call.  Returns *None* on any failure."""
        if not self.settings.ollama_enabled:
            return None
        if self._breaker.is_open:
            return None
        try:
            result = await self.ollama.chat_json(messages, model=model)
            self._breaker.record_success()
            return result
        except Exception:
            self._breaker.record_failure()
            logger.info("ollama_json_call_failed", model=model, exc_info=True)
            return None

    # -- public interface ---------------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        task: str = "default",
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Chat with local-first routing and cloud fallback."""
        resolved = self._resolve_model(task, model)

        local_result = await self._try_local(messages, model=resolved, **kwargs)
        if local_result is not None:
            return local_result

        # Fall back to cloud
        return await self.cloud.chat(messages, model=model, **kwargs)

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        task: str = "default",
        model: str | None = None,
    ) -> dict[str, Any]:
        """JSON chat with local-first routing and cloud fallback."""
        resolved = self._resolve_model(task, model)

        local_result = await self._try_local_json(messages, model=resolved)
        if local_result is not None:
            return local_result

        # Fall back to cloud
        return await self.cloud.chat_json(messages, model=model)

    async def close(self) -> None:
        await self.ollama.close()
        await self.cloud.close()
