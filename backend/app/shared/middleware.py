from __future__ import annotations

import asyncio
import time
import uuid
from collections import defaultdict, deque

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings

logger = structlog.get_logger()
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        structlog.contextvars.clear_contextvars()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
        route = request.scope.get("route")
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            route_name=getattr(route, "name", None),
            route_path=getattr(route, "path", None),
            auth_user_id=getattr(request.state, "auth_user_id", None),
            status=response.status_code,
            duration_ms=round(duration_ms, 1),
        )
        return response


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        async with self._lock:
            bucket = self._requests[key]
            while bucket and now - bucket[0] >= window_seconds:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                return False, retry_after
            bucket.append(now)
            return True, max(0, limit - len(bucket))

    async def clear(self) -> None:
        async with self._lock:
            self._requests.clear()


api_rate_limiter = InMemoryRateLimiter()


class ApiRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not request.url.path.startswith(settings.api_prefix):
            return await call_next(request)

        client_host = request.client.host if request.client else "unknown"
        is_login = request.url.path == f"{settings.api_prefix}/auth/login"
        limit = (
            settings.login_rate_limit_per_minute
            if is_login
            else settings.api_rate_limit_per_minute
        )
        bucket = f"api:{request.url.path}"
        if is_login:
            email = "unknown"
            try:
                payload = await request.json()
                email = str(payload.get("email", "unknown")).lower()
            except Exception as exc:
                logger.debug("login_rate_limit_payload_unavailable", error=str(exc))
            bucket = f"login:{email}"
        allowed, meta = await api_rate_limiter.check(
            key=f"{bucket}:{client_host}",
            limit=limit,
            window_seconds=60,
        )
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry later."},
                headers={"Retry-After": str(meta)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(meta)
        return response


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not request.url.path.startswith(settings.api_prefix) or request.method in SAFE_METHODS:
            return await call_next(request)

        bearer_authorization = bool(request.headers.get("Authorization"))
        cookie_auth_present = bool(
            request.cookies.get(settings.access_cookie_name)
            or request.cookies.get(settings.refresh_cookie_name)
        )
        if not cookie_auth_present or bearer_authorization:
            return await call_next(request)

        csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
        csrf_header = request.headers.get(settings.csrf_header_name)
        if not csrf_cookie or csrf_cookie != csrf_header:
            logger.warning(
                "csrf_validation_failed",
                reason="missing_or_invalid_token",
                method=request.method,
                path=request.url.path,
                has_cookie=bool(csrf_cookie),
                has_header=bool(csrf_header),
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing or invalid"},
            )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        if request.url.scheme == "https" or settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
