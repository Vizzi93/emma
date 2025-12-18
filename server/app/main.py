"""FastAPI application entrypoint with production-ready configuration."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.routers.agents import router as agents_router
from app.api.v1.routers.audit import router as audit_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.docker import router as docker_router
from app.api.v1.routers.monitoring import router as monitoring_router
from app.api.v1.routers.services import router as services_router
from app.api.v1.routers.users import router as users_router
from app.api.v1.routers.websocket import router as websocket_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import (
    RateLimitMiddleware,
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from sqlalchemy import text

from app.db.session import engine
from app.services.docker_client import get_docker_manager
from app.services.scheduler import start_scheduler, stop_scheduler

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan handler.
    
    Startup: Validate DB connection, run checks
    Shutdown: Close DB pool gracefully
    """
    settings = get_settings()
    setup_logging(settings)
    
    logger.info(
        "application_starting",
        environment=settings.environment.value,
        api_version=settings.api_version,
    )

    # Verify database connectivity
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("database_connected")
    except Exception as exc:
        logger.critical("database_connection_failed", error=str(exc))
        raise RuntimeError("Cannot connect to database") from exc

    # Start health check scheduler
    await start_scheduler()
    logger.info("health_check_scheduler_started")

    yield  # Application runs here

    # Graceful shutdown
    logger.info("application_shutting_down")
    await stop_scheduler()
    logger.info("health_check_scheduler_stopped")

    # Close Docker clients
    docker_manager = get_docker_manager()
    await docker_manager.close_all()
    logger.info("docker_clients_closed")

    await engine.dispose()
    logger.info("database_pool_closed")


def create_application() -> FastAPI:
    """Factory function to create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        openapi_url="/openapi.json" if settings.is_development else None,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # === Middleware Stack (order matters - first added = outermost) ===

    # 1. Request context & tracing (outermost - catches everything)
    app.add_middleware(RequestContextMiddleware)

    # 2. Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_requests_per_minute,
        burst_limit=settings.rate_limit_burst,
    )

    # 4. Trusted hosts (prevent host header attacks)
    if settings.allowed_hosts != ["*"]:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts,
        )

    # 5. CORS (innermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Role", "X-Actor-Id"],
        expose_headers=["X-Request-ID", "X-Response-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # === Exception Handlers ===

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return clean validation errors without leaking internal details."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"][1:]),  # Skip 'body'
                "message": error["msg"],
                "type": error["type"],
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation failed", "errors": errors},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all handler to prevent stack traces in responses."""
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # === Routes ===

    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(agents_router, prefix=settings.api_v1_prefix)
    app.include_router(audit_router, prefix=settings.api_v1_prefix)
    app.include_router(monitoring_router, prefix=settings.api_v1_prefix)
    # Legacy route for compatibility (without v1 prefix)
    app.include_router(monitoring_router, prefix="/api", tags=["monitoring-legacy"])
    app.include_router(services_router, prefix=settings.api_v1_prefix)
    app.include_router(docker_router, prefix=settings.api_v1_prefix)
    app.include_router(users_router, prefix=settings.api_v1_prefix)
    app.include_router(websocket_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        """
        Liveness probe - returns OK if application is running.
        Use for Kubernetes/Docker health checks.
        """
        return {"status": "ok"}

    @app.get("/ready", tags=["system"])
    async def ready() -> dict[str, str]:
        """
        Readiness probe - verifies database connectivity.
        Returns 503 if database is unreachable.
        """
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "ready", "database": "connected"}
        except Exception as exc:
            logger.error("readiness_check_failed", error=str(exc))
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "database": "disconnected"},
            )

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )
