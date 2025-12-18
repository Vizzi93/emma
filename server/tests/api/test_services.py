"""
Tests for service management API endpoints.

Tests cover:
- CRUD operations for services
- Service health checks
- Filtering and pagination
- Role-based access control
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User


class TestServiceCRUD:
    """Test service CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_service(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test creating a new service."""
        response = await client.post(
            "/v1/services",
            headers=admin_headers,
            json={
                "name": "Test Service",
                "url": "https://example.com",
                "check_type": "http",
                "check_interval": 60,
                "timeout": 10,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Service"
        assert data["url"] == "https://example.com"
        assert data["status"] == "unknown"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_service_unauthorized(self, client: AsyncClient):
        """Test creating service without auth fails."""
        response = await client.post(
            "/v1/services",
            json={
                "name": "Test Service",
                "url": "https://example.com",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_service_viewer_forbidden(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test that viewers cannot create services."""
        response = await client.post(
            "/v1/services",
            headers=auth_headers,  # Viewer role
            json={
                "name": "Test Service",
                "url": "https://example.com",
            },
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_services(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test listing services."""
        # Create some services first
        for i in range(3):
            await client.post(
                "/v1/services",
                headers=admin_headers,
                json={
                    "name": f"Service {i}",
                    "url": f"https://example{i}.com",
                },
            )

        response = await client.get("/v1/services", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3

    @pytest.mark.asyncio
    async def test_list_services_pagination(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test service listing with pagination."""
        # Create services
        for i in range(5):
            await client.post(
                "/v1/services",
                headers=admin_headers,
                json={
                    "name": f"Paginated Service {i}",
                    "url": f"https://paginated{i}.com",
                },
            )

        # Get first page
        response = await client.get(
            "/v1/services",
            headers=admin_headers,
            params={"limit": 2, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 5

    @pytest.mark.asyncio
    async def test_get_service_by_id(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting a specific service."""
        # Create service
        create_response = await client.post(
            "/v1/services",
            headers=admin_headers,
            json={
                "name": "Specific Service",
                "url": "https://specific.com",
            },
        )
        service_id = create_response.json()["id"]

        # Get service
        response = await client.get(
            f"/v1/services/{service_id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == service_id
        assert data["name"] == "Specific Service"

    @pytest.mark.asyncio
    async def test_get_nonexistent_service(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test getting non-existent service returns 404."""
        response = await client.get(
            "/v1/services/99999999-9999-9999-9999-999999999999",
            headers=admin_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_service(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test updating a service."""
        # Create service
        create_response = await client.post(
            "/v1/services",
            headers=admin_headers,
            json={
                "name": "Update Me",
                "url": "https://update.com",
            },
        )
        service_id = create_response.json()["id"]

        # Update service
        response = await client.put(
            f"/v1/services/{service_id}",
            headers=admin_headers,
            json={
                "name": "Updated Name",
                "url": "https://updated.com",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["url"] == "https://updated.com"

    @pytest.mark.asyncio
    async def test_delete_service(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test deleting a service."""
        # Create service
        create_response = await client.post(
            "/v1/services",
            headers=admin_headers,
            json={
                "name": "Delete Me",
                "url": "https://delete.com",
            },
        )
        service_id = create_response.json()["id"]

        # Delete service
        response = await client.delete(
            f"/v1/services/{service_id}",
            headers=admin_headers,
        )

        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            f"/v1/services/{service_id}",
            headers=admin_headers,
        )
        assert get_response.status_code == 404


class TestServiceFiltering:
    """Test service filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test filtering services by status."""
        response = await client.get(
            "/v1/services",
            headers=admin_headers,
            params={"status": "healthy"},
        )

        assert response.status_code == 200
        data = response.json()
        # All returned services should be healthy
        for service in data["items"]:
            assert service["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_search_by_name(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test searching services by name."""
        # Create services
        await client.post(
            "/v1/services",
            headers=admin_headers,
            json={"name": "Alpha Service", "url": "https://alpha.com"},
        )
        await client.post(
            "/v1/services",
            headers=admin_headers,
            json={"name": "Beta Service", "url": "https://beta.com"},
        )

        response = await client.get(
            "/v1/services",
            headers=admin_headers,
            params={"search": "Alpha"},
        )

        assert response.status_code == 200
        data = response.json()
        assert all("Alpha" in s["name"] for s in data["items"])


class TestServiceHealthCheck:
    """Test service health check trigger."""

    @pytest.mark.asyncio
    async def test_trigger_check(
        self, client: AsyncClient, admin_headers: dict[str, str]
    ):
        """Test triggering a manual health check."""
        # Create service
        create_response = await client.post(
            "/v1/services",
            headers=admin_headers,
            json={
                "name": "Check Me",
                "url": "https://httpbin.org/status/200",
            },
        )
        service_id = create_response.json()["id"]

        # Trigger check
        response = await client.post(
            f"/v1/services/{service_id}/check",
            headers=admin_headers,
        )

        # Should return check result or accepted
        assert response.status_code in [200, 202]
