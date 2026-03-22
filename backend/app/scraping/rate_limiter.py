"""Token bucket rate limiter with circuit breaker for scrapers.

Enhanced with per-source policies and retry support from v1.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is open and requests are blocked."""


@dataclass
class RatePolicy:
    """Configuration for a rate limiter + circuit breaker."""

    rps: float
    backoff_base: float = 1.0
    max_retries: int = 3
    circuit_threshold: int = 5
    circuit_cooldown: float = 300.0


class TokenBucketLimiter:
    """Token bucket rate limiter per source."""

    def __init__(self, rate: float, burst: int = 1):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_time = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_time
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_time = now

            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1


class CircuitBreaker:
    """Circuit breaker for scraper sources.

    States: closed (normal), open (tripped), half-open (recovery).
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "closed"

    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if (
                self.last_failure_time
                and (time.monotonic() - self.last_failure_time) > self.recovery_timeout
            ):
                self.state = "half-open"
                return True
            return False
        return True  # half-open

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning("circuit_breaker.opened", failures=self.failure_count)


class RateLimiter:
    """Combined token bucket + circuit breaker with retry support."""

    def __init__(self, policy: RatePolicy) -> None:
        self._policy = policy
        self._bucket = TokenBucketLimiter(rate=policy.rps)
        self._breaker = CircuitBreaker(
            failure_threshold=policy.circuit_threshold,
            recovery_timeout=policy.circuit_cooldown,
        )

    async def acquire(self) -> None:
        if not self._breaker.can_execute():
            raise CircuitOpenError(
                f"Circuit breaker is OPEN. Retry after {self._policy.circuit_cooldown}s."
            )
        await self._bucket.acquire()

    def record_success(self) -> None:
        self._breaker.record_success()

    def record_failure(self) -> None:
        self._breaker.record_failure()

    async def with_retry(self, fn: Callable[[], Awaitable[T]]) -> T:
        """Call fn with exponential back-off retries."""
        last_exc: Exception | None = None
        for attempt in range(self._policy.max_retries + 1):
            await self.acquire()
            try:
                result = await fn()
                self.record_success()
                return result
            except CircuitOpenError:
                raise
            except Exception as exc:
                last_exc = exc
                self.record_failure()
                if attempt < self._policy.max_retries:
                    wait = self._policy.backoff_base * (2**attempt)
                    logger.debug(
                        "rate_limiter.retry",
                        attempt=attempt + 1,
                        max=self._policy.max_retries + 1,
                        wait=wait,
                    )
                    await asyncio.sleep(wait)

        if last_exc is None:
            raise RuntimeError("RateLimiter.with_retry exhausted without capturing an exception")
        raise last_exc


# ---------------------------------------------------------------------------
# Default policies per source
# ---------------------------------------------------------------------------

DEFAULT_POLICIES: dict[str, RatePolicy] = {
    "greenhouse": RatePolicy(rps=10.0, backoff_base=1.0, max_retries=3, circuit_threshold=5),
    "lever": RatePolicy(rps=5.0, backoff_base=1.0, max_retries=3, circuit_threshold=5),
    "ashby": RatePolicy(rps=5.0, backoff_base=1.0, max_retries=3, circuit_threshold=5),
    "workday": RatePolicy(rps=5.0, backoff_base=1.0, max_retries=3, circuit_threshold=5),
    "serpapi": RatePolicy(rps=1.0, backoff_base=2.0, max_retries=3, circuit_threshold=5),
    "jobspy": RatePolicy(rps=0.5, backoff_base=2.0, max_retries=2, circuit_threshold=5),
    "theirstack": RatePolicy(rps=2.0, backoff_base=1.0, max_retries=3, circuit_threshold=5),
    "apify": RatePolicy(rps=2.0, backoff_base=1.0, max_retries=3, circuit_threshold=5),
    "scrapingbee": RatePolicy(rps=1.0, backoff_base=2.0, max_retries=3, circuit_threshold=5),
    "scrapling": RatePolicy(rps=2.0, backoff_base=2.0, max_retries=3, circuit_threshold=5),
    "ai_scraper": RatePolicy(rps=0.5, backoff_base=2.0, max_retries=2, circuit_threshold=3),
    "generic": RatePolicy(rps=0.1, backoff_base=2.0, max_retries=2, circuit_threshold=3),
}

_limiter_cache: dict[str, RateLimiter] = {}


def get_limiter(source_id: str) -> RateLimiter:
    """Return a cached RateLimiter for *source_id*."""
    if source_id not in _limiter_cache:
        policy = DEFAULT_POLICIES.get(source_id, DEFAULT_POLICIES["generic"])
        _limiter_cache[source_id] = RateLimiter(policy)
    return _limiter_cache[source_id]
