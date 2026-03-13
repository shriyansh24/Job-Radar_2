"""Test token bucket rate limiter with circuit breaker."""
import asyncio
import pytest
import time
from backend.scrapers.rate_limiter import (
    RatePolicy, RateLimiter, CircuitOpenError, get_limiter,
    DEFAULT_POLICIES,
)


class TestRatePolicy:
    def test_default_values(self):
        p = RatePolicy(rps=10.0, backoff_base=1.0, max_retries=3, circuit_threshold=5)
        assert p.rps == 10.0
        assert p.circuit_cooldown == 300.0

    def test_custom_cooldown(self):
        p = RatePolicy(rps=1.0, backoff_base=2.0, max_retries=2, circuit_threshold=3, circuit_cooldown=60.0)
        assert p.circuit_cooldown == 60.0


class TestRateLimiter:
    async def test_acquire_respects_rate(self):
        policy = RatePolicy(rps=100.0, backoff_base=1.0, max_retries=3, circuit_threshold=5)
        limiter = RateLimiter(policy)
        start = time.monotonic()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.5

    async def test_circuit_breaker_opens_after_threshold(self):
        policy = RatePolicy(rps=100.0, backoff_base=0.01, max_retries=1, circuit_threshold=3, circuit_cooldown=60.0)
        limiter = RateLimiter(policy)
        for _ in range(3):
            limiter.record_failure()
        with pytest.raises(CircuitOpenError):
            await limiter.acquire()

    async def test_circuit_resets_on_success(self):
        policy = RatePolicy(rps=100.0, backoff_base=0.01, max_retries=1, circuit_threshold=3, circuit_cooldown=60.0)
        limiter = RateLimiter(policy)
        limiter.record_failure()
        limiter.record_failure()
        limiter.record_success()
        await limiter.acquire()

    async def test_with_retry_succeeds(self):
        policy = RatePolicy(rps=100.0, backoff_base=0.01, max_retries=3, circuit_threshold=5)
        limiter = RateLimiter(policy)
        call_count = 0
        async def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient")
            return "success"
        result = await limiter.with_retry(flaky_fn)
        assert result == "success"
        assert call_count == 3

    async def test_with_retry_exhausts_retries(self):
        policy = RatePolicy(rps=100.0, backoff_base=0.01, max_retries=2, circuit_threshold=10)
        limiter = RateLimiter(policy)
        async def always_fail():
            raise ConnectionError("permanent")
        with pytest.raises(ConnectionError):
            await limiter.with_retry(always_fail)


class TestDefaultPolicies:
    def test_greenhouse_policy_exists(self):
        assert "greenhouse" in DEFAULT_POLICIES
        assert DEFAULT_POLICIES["greenhouse"].rps == 10.0

    def test_serpapi_policy_exists(self):
        assert "serpapi" in DEFAULT_POLICIES

    def test_generic_fallback(self):
        assert "generic" in DEFAULT_POLICIES
        assert DEFAULT_POLICIES["generic"].rps == 0.1


class TestGetLimiter:
    def test_returns_limiter_for_known_source(self):
        limiter = get_limiter("greenhouse")
        assert isinstance(limiter, RateLimiter)

    def test_returns_generic_for_unknown_source(self):
        limiter = get_limiter("unknown_ats")
        assert isinstance(limiter, RateLimiter)

    def test_caches_instances(self):
        a = get_limiter("lever")
        b = get_limiter("lever")
        assert a is b
