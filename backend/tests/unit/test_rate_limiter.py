from __future__ import annotations

import asyncio
import time

import pytest

from app.scraping.rate_limiter import CircuitBreaker, TokenBucketLimiter


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

    def test_half_open_after_recovery(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        assert not cb.can_execute()

        # Wait for recovery timeout
        time.sleep(0.06)
        assert cb.can_execute()  # Now half-open
        assert cb.state == "half-open"

    def test_half_open_success_closes(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.01)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.02)
        cb.can_execute()  # Transitions to half-open
        cb.record_success()
        assert cb.state == "closed"
        assert cb.failure_count == 0

    def test_half_open_failure_reopens(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.01)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.02)
        cb.can_execute()  # half-open
        cb.record_failure()
        assert cb.state == "open"
