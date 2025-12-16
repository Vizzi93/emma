---
name: api-testing
description: Generate API tests for FastAPI endpoints. Use when creating or testing API routes.
globs:
  - "server/app/api/**/*.py"
  - "server/tests/**/*.py"
---

# API Testing for eMMA

Generate comprehensive API tests for FastAPI endpoints.

## Test Framework
- **pytest** with pytest-asyncio
- **httpx** AsyncClient for async testing
- **pytest-cov** for coverage

## Test Structure
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_headers(client):
    """Get authenticated headers for protected endpoints."""
    response = await client.post("/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

## Test Categories

### 1. Authentication Tests
```python
async def test_login_success(client):
    response = await client.post("/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "correct_password"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

async def test_login_invalid_credentials(client):
    response = await client.post("/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "wrong_password"
    })
    assert response.status_code == 401
```

### 2. CRUD Tests
```python
async def test_create_service(client, auth_headers):
    response = await client.post("/v1/services",
        headers=auth_headers,
        json={"name": "Test Service", "url": "http://test.com", "type": "http"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Service"

async def test_get_services(client, auth_headers):
    response = await client.get("/v1/services", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### 3. Authorization Tests
```python
async def test_admin_only_endpoint_as_viewer(client, viewer_headers):
    response = await client.get("/v1/users", headers=viewer_headers)
    assert response.status_code == 403

async def test_admin_only_endpoint_as_admin(client, admin_headers):
    response = await client.get("/v1/users", headers=admin_headers)
    assert response.status_code == 200
```

### 4. Validation Tests
```python
async def test_create_service_invalid_url(client, auth_headers):
    response = await client.post("/v1/services",
        headers=auth_headers,
        json={"name": "Test", "url": "not-a-url", "type": "http"}
    )
    assert response.status_code == 422
```

## Running Tests
```bash
cd server
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
pytest tests/test_auth.py -v  # Single file
pytest tests/ -k "test_login"  # Pattern match
```

## Coverage Target
- Minimum 70% coverage
- 100% for authentication endpoints
- 100% for authorization checks
