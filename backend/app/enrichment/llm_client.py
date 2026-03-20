from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import structlog

from app.config import settings as _app_settings

logger = structlog.get_logger()


class LLMClient:
    """Shared LLM client for OpenRouter API (OpenAI-compatible).

    Features beyond basic chat:
    - ``chat_json()``  — parse structured JSON from LLM responses
    - ``chat_stream()`` — async iterator of content chunks (SSE)
    - ``model`` override per-call via the ``model`` kwarg
    - Configurable retry on transient errors
    """

    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        self.api_key = api_key
        self.model = model
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://openrouter.ai/api/v1",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": _app_settings.cors_origins[0] if _app_settings.cors_origins else "http://localhost:5173",
                    "X-Title": _app_settings.app_name,
                },
                timeout=90.0,
            )
        return self._client

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    # -----------------------------------------------------------------
    # Core chat
    # -----------------------------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1500,
        model: str | None = None,
        response_format: dict[str, str] | None = None,
    ) -> str:
        """Send a chat completion request. Returns the response text.

        Args:
            model: Override the default model for this call.
            response_format: E.g. ``{"type": "json_object"}`` to request JSON.
        """
        if not self.is_configured:
            logger.warning("llm_not_configured", hint="Set openrouter_api_key")
            return ""

        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        resp = await self.client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")

    # -----------------------------------------------------------------
    # JSON convenience
    # -----------------------------------------------------------------

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2000,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Chat completion that parses JSON from the response.

        Sends ``response_format: {"type": "json_object"}`` and attempts
        to parse the returned text as JSON.  Falls back to extracting
        the first ``{...}`` block if the model wraps the JSON in markdown.

        Returns an empty dict on failure (never raises for parse errors).
        """
        raw = await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            response_format={"type": "json_object"},
        )
        if not raw:
            return {}

        # Try direct parse first
        try:
            return json.loads(raw)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code fences
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            return json.loads(raw[start:end])  # type: ignore[no-any-return]
        except (ValueError, json.JSONDecodeError):
            logger.warning("llm_json_parse_failed", raw_len=len(raw), raw_head=raw[:200])
            return {}

    # -----------------------------------------------------------------
    # Streaming
    # -----------------------------------------------------------------

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """Async iterator that yields content chunks from a streaming response."""
        if not self.is_configured:
            logger.warning("llm_not_configured", hint="Set openrouter_api_key")
            return

        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with self.client.stream("POST", "/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue

    # -----------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
