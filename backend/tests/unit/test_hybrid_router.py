"""Tests for HybridLLMRouter and OllamaClient (Feature E2)."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.config import Settings
from app.enrichment.hybrid_router import (
    HybridLLMRouter,
    OllamaClient,
    _CircuitBreaker,
    strip_think_tags,
)
from app.enrichment.llm_client import LLMClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def ollama() -> OllamaClient:
    return OllamaClient(base_url="http://localhost:11434")


@pytest.fixture()
def cloud() -> LLMClient:
    client = LLMClient(api_key="test-key", model="anthropic/claude-3.5-sonnet")
    return client


@pytest.fixture()
def settings_enabled() -> Settings:
    return Settings(
        ollama_enabled=True,
        secret_key="test-secret",
        debug=True,
    )


@pytest.fixture()
def settings_disabled() -> Settings:
    return Settings(
        ollama_enabled=False,
        secret_key="test-secret",
        debug=True,
    )


@pytest.fixture()
def router(ollama: OllamaClient, cloud: LLMClient, settings_enabled: Settings) -> HybridLLMRouter:
    return HybridLLMRouter(ollama=ollama, cloud=cloud, settings=settings_enabled)


# ---------------------------------------------------------------------------
# Think-tag stripping
# ---------------------------------------------------------------------------


class TestStripThinkTags:
    def test_removes_think_block(self) -> None:
        text = "<think>internal reasoning here</think>The actual answer."
        assert strip_think_tags(text) == "The actual answer."

    def test_removes_multiline_think_block(self) -> None:
        text = "<think>\nstep 1\nstep 2\n</think>\nFinal answer."
        assert strip_think_tags(text) == "Final answer."

    def test_no_think_tags_unchanged(self) -> None:
        text = "Just a normal response."
        assert strip_think_tags(text) == "Just a normal response."

    def test_multiple_think_blocks(self) -> None:
        text = "<think>a</think>Hello <think>b</think>World"
        assert strip_think_tags(text) == "Hello World"

    def test_empty_think_block(self) -> None:
        text = "<think></think>Result"
        assert strip_think_tags(text) == "Result"


# ---------------------------------------------------------------------------
# OllamaClient
# ---------------------------------------------------------------------------


class TestOllamaClient:
    @staticmethod
    def _inject_mock_client(ollama: OllamaClient) -> MagicMock:
        """Inject a mock httpx.AsyncClient into the OllamaClient."""
        mock_client = MagicMock()
        ollama._client = mock_client  # noqa: SLF001
        return mock_client

    @pytest.mark.anyio()
    async def test_health_check_success(self, ollama: OllamaClient) -> None:
        mock_resp = MagicMock(status_code=200)
        mock_client = self._inject_mock_client(ollama)
        mock_client.get = AsyncMock(return_value=mock_resp)
        result = await ollama.health_check()
        assert result is True

    @pytest.mark.anyio()
    async def test_health_check_failure(self, ollama: OllamaClient) -> None:
        mock_client = self._inject_mock_client(ollama)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        result = await ollama.health_check()
        assert result is False

    @pytest.mark.anyio()
    async def test_chat_strips_think_tags(self, ollama: OllamaClient) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": "<think>reasoning</think>The answer is 42."}
        }
        mock_client = self._inject_mock_client(ollama)
        mock_client.post = AsyncMock(return_value=mock_resp)
        result = await ollama.chat([{"role": "user", "content": "test"}])
        assert result == "The answer is 42."

    @pytest.mark.anyio()
    async def test_chat_no_strip(self, ollama: OllamaClient) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": "<think>reasoning</think>Answer."}
        }
        mock_client = self._inject_mock_client(ollama)
        mock_client.post = AsyncMock(return_value=mock_resp)
        result = await ollama.chat(
            [{"role": "user", "content": "test"}], strip_think=False
        )
        assert "<think>" in result

    @pytest.mark.anyio()
    async def test_chat_json_parses(self, ollama: OllamaClient) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": '{"key": "value"}'}
        }
        mock_client = self._inject_mock_client(ollama)
        mock_client.post = AsyncMock(return_value=mock_resp)
        result = await ollama.chat_json([{"role": "user", "content": "test"}])
        assert result == {"key": "value"}

    @pytest.mark.anyio()
    async def test_chat_json_handles_code_fence(self, ollama: OllamaClient) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": '```json\n{"key": "value"}\n```'}
        }
        mock_client = self._inject_mock_client(ollama)
        mock_client.post = AsyncMock(return_value=mock_resp)
        result = await ollama.chat_json([{"role": "user", "content": "test"}])
        assert result == {"key": "value"}

    @pytest.mark.anyio()
    async def test_chat_json_returns_empty_on_bad_json(self, ollama: OllamaClient) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": "not json at all"}
        }
        mock_client = self._inject_mock_client(ollama)
        mock_client.post = AsyncMock(return_value=mock_resp)
        result = await ollama.chat_json([{"role": "user", "content": "test"}])
        assert result == {}


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    def test_starts_closed(self) -> None:
        cb = _CircuitBreaker(threshold=3)
        assert cb.is_open is False

    def test_opens_after_threshold(self) -> None:
        cb = _CircuitBreaker(threshold=3, window=60.0, cooldown=300.0)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is False
        cb.record_failure()
        assert cb.is_open is True

    def test_success_resets(self) -> None:
        cb = _CircuitBreaker(threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        assert cb.is_open is False

    def test_cooldown_resets(self) -> None:
        cb = _CircuitBreaker(threshold=3, window=60.0, cooldown=0.1)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is True
        # Simulate time passing beyond cooldown
        cb._open_until = time.monotonic() - 1
        assert cb.is_open is False


# ---------------------------------------------------------------------------
# HybridLLMRouter
# ---------------------------------------------------------------------------


class TestHybridLLMRouter:
    @pytest.mark.anyio()
    async def test_local_healthy_uses_ollama(self, router: HybridLLMRouter) -> None:
        router.ollama.chat = AsyncMock(return_value="local answer")
        router.cloud.chat = AsyncMock(return_value="cloud answer")

        result = await router.chat([{"role": "user", "content": "hi"}])
        assert result == "local answer"
        router.ollama.chat.assert_awaited_once()
        router.cloud.chat.assert_not_awaited()

    @pytest.mark.anyio()
    async def test_local_down_falls_back_to_cloud(self, router: HybridLLMRouter) -> None:
        router.ollama.chat = AsyncMock(side_effect=httpx.ConnectError("refused"))
        router.cloud.chat = AsyncMock(return_value="cloud answer")

        result = await router.chat([{"role": "user", "content": "hi"}])
        assert result == "cloud answer"

    @pytest.mark.anyio()
    async def test_circuit_opens_after_3_failures(self, router: HybridLLMRouter) -> None:
        router.ollama.chat = AsyncMock(side_effect=httpx.ConnectError("refused"))
        router.cloud.chat = AsyncMock(return_value="cloud answer")

        # Trigger 3 failures
        for _ in range(3):
            await router.chat([{"role": "user", "content": "hi"}])

        # 4th call should skip local entirely
        router.ollama.chat.reset_mock()
        await router.chat([{"role": "user", "content": "hi"}])
        router.ollama.chat.assert_not_awaited()

    @pytest.mark.anyio()
    async def test_circuit_resets_after_cooldown(self, router: HybridLLMRouter) -> None:
        router.ollama.chat = AsyncMock(side_effect=httpx.ConnectError("refused"))
        router.cloud.chat = AsyncMock(return_value="cloud answer")

        # Open the circuit
        for _ in range(3):
            await router.chat([{"role": "user", "content": "hi"}])
        assert router._breaker.is_open is True

        # Simulate cooldown expiry
        router._breaker._open_until = time.monotonic() - 1

        # Now ollama should be tried again
        router.ollama.chat = AsyncMock(return_value="recovered")
        result = await router.chat([{"role": "user", "content": "hi"}])
        assert result == "recovered"

    @pytest.mark.anyio()
    async def test_disabled_always_uses_cloud(
        self,
        ollama: OllamaClient,
        cloud: LLMClient,
        settings_disabled: Settings,
    ) -> None:
        router = HybridLLMRouter(ollama=ollama, cloud=cloud, settings=settings_disabled)
        ollama.chat = AsyncMock(return_value="local")  # type: ignore[method-assign]
        cloud.chat = AsyncMock(return_value="cloud")  # type: ignore[method-assign]

        result = await router.chat([{"role": "user", "content": "hi"}])
        assert result == "cloud"
        ollama.chat.assert_not_awaited()  # type: ignore[union-attr]

    @pytest.mark.anyio()
    async def test_task_model_mapping(self, router: HybridLLMRouter) -> None:
        router.ollama.chat = AsyncMock(return_value="answer")

        await router.chat(
            [{"role": "user", "content": "hi"}],
            task="resume_tailor",
        )
        call_kwargs = router.ollama.chat.call_args
        assert call_kwargs.kwargs.get("model") == "qwen3:8b"

    @pytest.mark.anyio()
    async def test_explicit_model_overrides_task(self, router: HybridLLMRouter) -> None:
        router.ollama.chat = AsyncMock(return_value="answer")

        await router.chat(
            [{"role": "user", "content": "hi"}],
            task="resume_tailor",
            model="custom:model",
        )
        call_kwargs = router.ollama.chat.call_args
        assert call_kwargs.kwargs.get("model") == "custom:model"

    @pytest.mark.anyio()
    async def test_chat_json_local_healthy(self, router: HybridLLMRouter) -> None:
        router.ollama.chat_json = AsyncMock(return_value={"key": "local"})
        router.cloud.chat_json = AsyncMock(return_value={"key": "cloud"})

        result = await router.chat_json([{"role": "user", "content": "hi"}])
        assert result == {"key": "local"}

    @pytest.mark.anyio()
    async def test_chat_json_fallback(self, router: HybridLLMRouter) -> None:
        router.ollama.chat_json = AsyncMock(side_effect=httpx.ConnectError("refused"))
        router.cloud.chat_json = AsyncMock(return_value={"key": "cloud"})

        result = await router.chat_json([{"role": "user", "content": "hi"}])
        assert result == {"key": "cloud"}
