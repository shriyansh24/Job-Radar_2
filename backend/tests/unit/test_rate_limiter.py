from __future__ import annotations

import asyncio
import time

import pytest

import app.scraping.rate_limiter as rate_limiter_module
from app.scraping.rate_limiter import (
    DEFAULT_POLICIES,
    CircuitBreaker,
    RateLimiter,
    RatePolicy,
    TokenBucketLimiter,
    get_limiter,
)


class TestTokenBucketLimiter:
    @pytest.mark.asyncio
    async def test_burst_allows_immediate(self):
        limiter = TokenBucketLimiter(rate=1.0, burst=3)
        start = time.monotonic()
        for _ in range(3):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # Should be nearly instant

    @pytest.mark.asyncio
    async def test_rate_limits_after_burst(self):
        limiter = TokenBucketLimiter(rate=10.0, burst=1)
        await limiter.acquire()  # Use the one burst token
        start = time.monotonic()
        await limiter.acquire()  # Should wait ~0.1s
        elapsed = time.monotonic() - start
        assert elapsed >= 0.05  # At least some delay

    @pytest.mark.asyncio
    async def test_tokens_replenish(self):
        limiter = TokenBucketLimiter(rate=100.0, burst=2)
        await limiter.acquire()
        await limiter.acquire()
        # Tokens exhausted, wait for replenishment
        await asyncio.sleep(0.05)  # 0.05s * 100 tokens/s = 5 tokens added
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.05  # Should be nearly instant after replenishment


class TestCircuitBreaker:
    @staticmethod
    def _set_now(monkeypatch: pytest.MonkeyPatch, start: float = 100.0) -> list[float]:
        current = [start]
        monkeypatch.setattr(rate_limiter_module, "_now", lambda: current[0])
        return current

    def test_initial_state_closed(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10)
        assert cb.state == "closed"
        assert cb.can_execute()

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10)
        cb.record_failure()
        cb.record_failure()
        assert cb.can_execute()
        cb.record_failure()  # 3rd failure
        assert cb.state == "open"
        assert not cb.can_execute()

    def test_success_resets_count(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == "closed"
        cb.record_failure()
        cb.record_failure()
        assert cb.can_execute()  # Only 2 failures, not at threshold

    def test_half_open_after_recovery(self, monkeypatch: pytest.MonkeyPatch):
        current = self._set_now(monkeypatch)
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        assert not cb.can_execute()

        current[0] += 0.051
        assert cb.can_execute()  # Now half-open
        assert cb.state == "half-open"

    def test_half_open_after_recovery_uses_high_resolution_clock(self, monkeypatch):
        values = iter([100.0, 100.03, 100.079, 100.081])
        monkeypatch.setattr(rate_limiter_module, "_now", lambda: next(values))
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)

        cb.record_failure()
        cb.record_failure()

        assert not cb.can_execute()
        assert cb.can_execute()
        assert cb.state == "half-open"

    def test_half_open_success_closes(self, monkeypatch: pytest.MonkeyPatch):
        current = self._set_now(monkeypatch)
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.01)
        cb.record_failure()
        cb.record_failure()
        current[0] += 0.011
        cb.can_execute()  # Transitions to half-open
        cb.record_success()
        assert cb.state == "closed"
        assert cb.failure_count == 0

    def test_half_open_failure_reopens(self, monkeypatch: pytest.MonkeyPatch):
        current = self._set_now(monkeypatch)
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.01)
        cb.record_failure()
        cb.record_failure()
        current[0] += 0.011
        cb.can_execute()  # half-open
        cb.record_failure()
        assert cb.state == "open"


def test_workday_has_dedicated_policy():
    limiter = get_limiter("workday")

    assert "workday" in DEFAULT_POLICIES
    assert limiter._policy is DEFAULT_POLICIES["workday"]
    assert limiter._policy.rps == 5.0


@pytest.mark.asyncio
async def test_with_retry_raises_runtime_error_when_no_attempts_run():
    limiter = RateLimiter(RatePolicy(rps=1.0, max_retries=-1))

    async def never_called():
        raise AssertionError("callback should not run")

    with pytest.raises(RuntimeError, match="without capturing an exception"):
        await limiter.with_retry(never_called)
