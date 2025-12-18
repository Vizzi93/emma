---
name: api-testing
description: Use this skill to generate comprehensive API tests for FastAPI applications. Creates pytest tests with async support, authentication testing, validation testing, and error handling verification.
---

# API Testing Skill

## Overview

This skill helps generate comprehensive API tests for FastAPI applications using pytest and pytest-asyncio.

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── test_auth.py          # Authentication tests
├── test_users.py         # User management tests
├── test_services.py      # Service CRUD tests
└── test_api/
    ├── __init__.py
    ├── test_auth_routes.py
    └── test_service_routes.py
```

## Core Fixtures (conftest.py)

```python
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db_session
from app.models import Base

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    """Create database session for each test."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    """Create test client with overridden dependencies."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
async def auth_headers(client):
    """Get authentication headers for protected routes."""
    # Create test user
    await client.post("/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    })

    # Login
    response = await client.post("/v1/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def admin_headers(client, db_session):
    """Get admin authentication headers."""
    from app.models.user import User
    from app.core.auth import get_password_hash

    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin User",
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()

    response = await client.post("/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "AdminPass123!"
    })
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
```

## Test Patterns

### Authentication Tests

```python
import pytest
from httpx import AsyncClient

class TestAuthentication:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post("/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with existing email."""
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123!",
            "full_name": "User One"
        }

        await client.post("/v1/auth/register", json=user_data)
        response = await client.post("/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post("/v1/auth/register", json={
            "email": "weak@example.com",
            "password": "weak",
            "full_name": "Weak User"
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Register first
        await client.post("/v1/auth/register", json={
            "email": "login@example.com",
            "password": "SecurePass123!",
            "full_name": "Login User"
        })

        response = await client.post("/v1/auth/login", json={
            "email": "login@example.com",
            "password": "SecurePass123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with wrong password."""
        response = await client.post("/v1/auth/login", json={
            "email": "login@example.com",
            "password": "WrongPassword123!"
        })

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_refresh(self, client: AsyncClient, auth_headers: dict):
        """Test token refresh."""
        # Get refresh token from login
        response = await client.post("/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        refresh_token = response.json()["refresh_token"]

        # Refresh
        response = await client.post("/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        assert "access_token" in response.json()
```

### CRUD Tests

```python
class TestServices:
    """Test service CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_service(self, client: AsyncClient, auth_headers: dict):
        """Test service creation."""
        response = await client.post(
            "/v1/services",
            headers=auth_headers,
            json={
                "name": "Test Service",
                "url": "https://example.com",
                "check_interval": 60,
                "timeout": 10
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Service"
        assert data["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_list_services(self, client: AsyncClient, auth_headers: dict):
        """Test listing services with pagination."""
        # Create multiple services
        for i in range(5):
            await client.post(
                "/v1/services",
                headers=auth_headers,
                json={"name": f"Service {i}", "url": f"https://example{i}.com"}
            )

        response = await client.get(
            "/v1/services",
            headers=auth_headers,
            params={"limit": 3, "offset": 0}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 5

    @pytest.mark.asyncio
    async def test_get_service_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent service."""
        response = await client.get(
            "/v1/services/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test accessing protected route without auth."""
        response = await client.get("/v1/services")

        assert response.status_code == 401
```

### Validation Tests

```python
class TestValidation:
    """Test input validation."""

    @pytest.mark.asyncio
    async def test_invalid_email_format(self, client: AsyncClient):
        """Test registration with invalid email."""
        response = await client.post("/v1/auth/register", json={
            "email": "not-an-email",
            "password": "SecurePass123!",
            "full_name": "Test User"
        })

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("email" in str(e).lower() for e in errors)

    @pytest.mark.asyncio
    async def test_missing_required_field(self, client: AsyncClient, auth_headers: dict):
        """Test creating service without required field."""
        response = await client.post(
            "/v1/services",
            headers=auth_headers,
            json={"url": "https://example.com"}  # Missing 'name'
        )

        assert response.status_code == 422
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::TestAuthentication::test_login_success -v

# Run async tests only
pytest tests/ -v -m asyncio
```

## Best Practices

1. **Isolation:** Each test should be independent
2. **Cleanup:** Use fixtures with proper teardown
3. **Naming:** Test names should describe the scenario
4. **Assertions:** One logical assertion per test
5. **Edge Cases:** Test error conditions and boundaries
6. **Mocking:** Mock external services (email, external APIs)
