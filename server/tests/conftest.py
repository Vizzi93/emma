"""
Shared pytest fixtures for eMMA backend tests.

This module provides common fixtures for:
- Async test configuration
- Test database setup/teardown
- HTTP client for API testing
- Authentication helpers
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

# Load test environment BEFORE importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only-32chars")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-unit-tests-32")
os.environ.setdefault("AGENT_BINARY_BASE_URL", "http://localhost:8000/agents")
os.environ.setdefault("CONFIG_SIGNING_KEY_ID", "test-key-id")
os.environ.setdefault("CONFIG_SIGNING_PRIVATE_KEY", "test-private-key-for-signing-configs")
os.environ.setdefault("ENVIRONMENT", "development")

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models.user import User, UserRole
from app.core.auth import password_hasher

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def engine() -> AsyncIterator[AsyncEngine]:
    """Create a test database engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Required for in-memory SQLite
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Create a database session for each test."""
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Create a test HTTP client with overridden database dependency."""

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=password_hasher.hash("TestPass123!"),
        full_name="Test User",
        role=UserRole.VIEWER.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        email="admin@example.com",
        password_hash=password_hasher.hash("AdminPass123!"),
        full_name="Admin User",
        role=UserRole.ADMIN.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def operator_user(db_session: AsyncSession) -> User:
    """Create an operator user."""
    user = User(
        email="operator@example.com",
        password_hash=password_hasher.hash("OperatorPass123!"),
        full_name="Operator User",
        role=UserRole.OPERATOR.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict[str, str]:
    """Get authentication headers for a test user."""
    response = await client.post(
        "/v1/auth/login",
        json={"email": "test@example.com", "password": "TestPass123!"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, admin_user: User) -> dict[str, str]:
    """Get authentication headers for an admin user."""
    response = await client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    token = response.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def operator_headers(client: AsyncClient, operator_user: User) -> dict[str, str]:
    """Get authentication headers for an operator user."""
    response = await client.post(
        "/v1/auth/login",
        json={"email": "operator@example.com", "password": "OperatorPass123!"},
    )
    assert response.status_code == 200, f"Operator login failed: {response.text}"
    token = response.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
