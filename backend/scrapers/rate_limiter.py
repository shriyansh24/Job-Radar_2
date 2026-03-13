"""Token bucket rate limiter with circuit breaker for scrapers."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is open and requests are blocked."""


@dataclass
class RatePolicy:
    """Configuration for a rate limiter + circuit breaker."""

    rps: float
    backoff_base: float
    max_retries: int
    circuit_threshold: int
    circuit_cooldown: float = 300.0


class RateLimiter:
    """Token-bucket rate limiter with an integrated circuit breaker.

    The circuit breaker has three states:
    - CLOSED  (normal)  – requests pass through.
    - OPEN    (tripped) – requests raise CircuitOpenError immediately.
    - HALF_OPEN         – one probe request is allowed; success → CLOSED.

    Token bucket: tokens are added at ``policy.rps`` per second up to a
    capacity of 1 token (strict per-request pacing).
    """

    _STATE_CLOSED = "CLOSED"
    _STATE_OPEN = "OPEN"

    def __init__(self, policy: RatePolicy) -> None:
        self._policy = policy
        # Token bucket
        self._tokens: float = 1.0
        self._last_refill: float = time.monotonic()
        self._bucket_lock = asyncio.Lock()
        # Circuit breaker
        self._failure_count: int = 0
        self._state: str = self._STATE_CLOSED
        self._opened_at: float | None = None

    # ------------------------------------------------------------------
    # Circuit breaker helpers
    # ------------------------------------------------------------------

    def _check_half_open(self) -> bool:
        """Return True if the cooldown has elapsed (circuit is half-open)."""
        if self._opened_at is None:
            return False
        return time.monotonic() - self._opened_at >= self._policy.circuit_cooldown

    def record_failure(self) -> None:
        """Increment failure counter; open circuit if threshold is reached."""
        self._failure_count += 1
        if self._failure_count >= self._policy.circuit_threshold:
            self._state = self._STATE_OPEN
            self._opened_at = time.monotonic()
            logger.warning(
                "Circuit breaker OPENED after %d failures", self._failure_count
            )

    def record_success(self) -> None:
        """Reset failure counter and close the circuit."""
        self._failure_count = 0
        self._state = self._STATE_CLOSED
        self._opened_at = None

    # ------------------------------------------------------------------
    # Token bucket
    # ------------------------------------------------------------------

    async def _wait_for_token(self) -> None:
        """Block until a token is available, then consume it."""
        async with self._bucket_lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(1.0, self._tokens + elapsed * self._policy.rps)
                self._last_refill = now

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return

                # Sleep until one token is available
                deficit = 1.0 - self._tokens
                wait_sec = deficit / self._policy.rps
                await asyncio.sleep(wait_sec)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def acquire(self) -> None:
        """Acquire one token, respecting the circuit breaker state.

        Raises:
            CircuitOpenError: when the circuit is open and cooldown has not
                              elapsed.
        """
        if self._state == self._STATE_OPEN:
            if self._check_half_open():
                # Allow one probe; do not change state here — record_success
                # or record_failure will transition.
                logger.debug("Circuit half-open: allowing probe request")
            else:
                raise CircuitOpenError(
                    "Circuit breaker is OPEN. "
                    f"Retry after {self._policy.circuit_cooldown}s cooldown."
                )

        await self._wait_for_token()

    async def with_retry(
        self,
        fn: Callable[[], Awaitable[T]],
    ) -> T:
        """Call ``fn`` with exponential back-off retries.

        Each failure calls ``record_failure()``. On success calls
        ``record_success()``. Raises the last exception after
        ``policy.max_retries`` attempts.
        """
        last_exc: Exception | None = None
        for attempt in range(self._policy.max_retries + 1):
            await self.acquire()
            try:
                result = await fn()
                self.record_success()
                return result
            except CircuitOpenError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                self.record_failure()
                if attempt < self._policy.max_retries:
                    wait = self._policy.backoff_base * (2**attempt)
                    logger.debug(
                        "Attempt %d/%d failed (%s); retrying in %.2fs",
                        attempt + 1,
                        self._policy.max_retries + 1,
                        exc,
                        wait,
                    )
                    await asyncio.sleep(wait)

        assert last_exc is not None
        raise last_exc


# ---------------------------------------------------------------------------
# Default policies per source
# ---------------------------------------------------------------------------

DEFAULT_POLICIES: dict[str, RatePolicy] = {
    "greenhouse": RatePolicy(
        rps=10.0, backoff_base=1.0, max_retries=3, circuit_threshold=5
    ),
    "lever": RatePolicy(
        rps=5.0, backoff_base=1.0, max_retries=3, circuit_threshold=5
    ),
    "ashby": RatePolicy(
        rps=5.0, backoff_base=1.0, max_retries=3, circuit_threshold=5
    ),
    "serpapi": RatePolicy(
        rps=1.0, backoff_base=2.0, max_retries=3, circuit_threshold=5
    ),
    "jobspy": RatePolicy(
        rps=0.5, backoff_base=2.0, max_retries=2, circuit_threshold=5
    ),
    "theirstack": RatePolicy(
        rps=2.0, backoff_base=1.0, max_retries=3, circuit_threshold=5
    ),
    "apify": RatePolicy(
        rps=2.0, backoff_base=1.0, max_retries=3, circuit_threshold=5
    ),
    "generic": RatePolicy(
        rps=0.1, backoff_base=2.0, max_retries=2, circuit_threshold=3
    ),
}

# Module-level cache: source_id → RateLimiter
_limiter_cache: dict[str, RateLimiter] = {}


def get_limiter(source_id: str) -> RateLimiter:
    """Return a cached :class:`RateLimiter` for *source_id*.

    Falls back to the ``"generic"`` policy for unknown sources.
    """
    if source_id not in _limiter_cache:
        policy = DEFAULT_POLICIES.get(source_id, DEFAULT_POLICIES["generic"])
        _limiter_cache[source_id] = RateLimiter(policy)
    return _limiter_cache[source_id]
