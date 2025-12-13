"""Database session and engine management with connection pooling."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


def create_engine(settings: Settings) -> AsyncEngine:
    """
    Create async SQLAlchemy engine with appropriate pool settings.
    
    Pool settings only apply to PostgreSQL; SQLite uses NullPool automatically.
    """
    connect_args = {}
    pool_kwargs = {}

    # SQLite-specific settings
    if settings.database_url_str.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        # PostgreSQL pool settings
        pool_kwargs = {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_pool_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "pool_pre_ping": True,  # Verify connections before use
            "pool_recycle": 3600,   # Recycle connections after 1 hour
        }

    return create_async_engine(
        settings.database_url_str,
        echo=settings.debug,
        future=True,
        connect_args=connect_args,
        **pool_kwargs,
    )


# Global engine instance (initialized lazily)
_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the global engine instance."""
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings())
    return _engine


# Expose engine for backward compatibility
engine = property(lambda self: get_engine())


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create session factory bound to the engine."""
    return async_sessionmaker(
        get_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )


# Session factory for dependency injection
AsyncSessionLocal = get_session_factory()


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    Yield an async database session per request.
    
    Used as a FastAPI dependency for request-scoped sessions.
    Automatically handles commit/rollback on exit.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Context manager for manual session management.
    
    Use this when you need a session outside of a request context,
    e.g., in background tasks or CLI commands.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_connectivity() -> bool:
    """
    Verify database connectivity.
    
    Returns True if database is reachable, False otherwise.
    Used for health checks.
    """
    try:
        async with get_engine().begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def dispose_engine() -> None:
    """
    Dispose of the engine and close all connections.
    
    Call this during application shutdown for graceful cleanup.
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
