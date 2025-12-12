"""Security and observability middleware."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import TypeVar

import structlog
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = structlog.get_logger(__name__)

# Type alias for ASGI call chain
CallNext = Callable[[Request], Awaitable[Response]]
T = TypeVar("T")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Inject request ID and timing into every request."""

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()

        # Bind request context to structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=self._get_client_ip(request),
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "request_failed",
                duration_ms=round(duration_ms, 2),
                error=str(exc),
            )
            raise

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract real client IP, respecting reverse proxy headers."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
    }

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        response = await call_next(request)
        for header, value in self.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter.
    
    Production: Replace with Redis-backed solution (e.g., slowapi with Redis).
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_limit: int = 10,
    ) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in {"/health", "/ready"}:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - 60

        # Clean old entries and count recent requests
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > window_start
        ]
        request_count = len(self._requests[client_ip])

        # Check rate limit
        if request_count >= self.requests_per_minute:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                request_count=request_count,
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Try again later.",
                    "retry_after_seconds": 60,
                },
                headers={"Retry-After": "60"},
            )

        # Track this request
        self._requests[client_ip].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - request_count - 1
        )
        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
