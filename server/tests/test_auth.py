"""
Tests for authentication functionality.

Tests cover:
- User registration
- Login/logout
- Token refresh
- Password validation
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User


class TestRegistration:
    """Test user registration."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"
        assert "id" in data["user"]
        assert "hashed_password" not in data["user"]
        assert "tokens" in data
        assert "access_token" in data["tokens"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with existing email fails."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "test@example.com",  # Same as test_user
                "password": "SecurePass123!",
                "full_name": "Duplicate User",
            },
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_weak_password_too_short(self, client: AsyncClient):
        """Test registration with too short password fails."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "Short1!",  # Too short
                "full_name": "Weak User",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password_no_uppercase(self, client: AsyncClient):
        """Test registration without uppercase fails."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "lowercase123!",  # No uppercase
                "full_name": "Weak User",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password_no_digit(self, client: AsyncClient):
        """Test registration without digit fails."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "NoDigitPass!",  # No digit
                "full_name": "Weak User",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "full_name": "Invalid Email User",
            },
        )

        assert response.status_code == 422


class TestLogin:
    """Test user login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "test@example.com"
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password fails."""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePass123!",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, client: AsyncClient, db_session, test_user: User
    ):
        """Test login with inactive user fails."""
        # Deactivate user
        test_user.is_active = False
        await db_session.commit()

        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!",
            },
        )

        assert response.status_code in [401, 403]


class TestTokenRefresh:
    """Test token refresh functionality."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user: User):
        """Test successful token refresh."""
        # Login first
        login_response = await client.post(
            "/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!",
            },
        )
        refresh_token = login_response.json()["tokens"]["refresh_token"]

        # Refresh token
        response = await client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await client.post(
            "/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test that endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_access_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token fails."""
        response = await client.get("/v1/services")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_access_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token fails."""
        response = await client.get(
            "/v1/services",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_access_with_valid_token(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test accessing protected endpoint with valid token succeeds."""
        response = await client.get("/v1/services", headers=auth_headers)

        # Should succeed (200) or return empty list
        assert response.status_code == 200


class TestCurrentUser:
    """Test current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user(
        self, client: AsyncClient, auth_headers: dict[str, str], test_user: User
    ):
        """Test getting current user info."""
        response = await client.get("/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without auth fails."""
        response = await client.get("/v1/auth/me")

        assert response.status_code == 401
