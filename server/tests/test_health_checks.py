"""
Tests for health check functionality.

Tests cover:
- HTTP/HTTPS checks
- TCP connectivity checks
- Response time measurement
- Error handling
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.health_checks import (
    BaseChecker,
    HTTPChecker,
    TCPChecker,
    CheckResult,
    get_checker,
)


class TestCheckResult:
    """Test CheckResult dataclass."""

    def test_result_creation_healthy(self):
        """Test creating a healthy check result."""
        result = CheckResult(
            is_healthy=True,
            response_time_ms=50.0,
            status_code=200,
            message="OK",
        )

        assert result.is_healthy is True
        assert result.response_time_ms == 50.0
        assert result.status_code == 200
        assert result.error is None

    def test_result_creation_unhealthy(self):
        """Test creating an unhealthy check result."""
        result = CheckResult(
            is_healthy=False,
            response_time_ms=0.0,
            message="Connection failed",
            error="Connection refused",
        )

        assert result.is_healthy is False
        assert result.error == "Connection refused"

    def test_result_with_metadata(self):
        """Test check result with metadata."""
        result = CheckResult(
            is_healthy=True,
            response_time_ms=100.0,
            metadata={"ssl_expiry": "2025-12-31"},
        )

        assert result.metadata is not None
        assert result.metadata["ssl_expiry"] == "2025-12-31"


class TestHTTPChecker:
    """Test HTTP health checker."""

    @pytest.mark.asyncio
    async def test_http_success(self):
        """Test successful HTTP check."""
        checker = HTTPChecker(timeout=5.0)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_client.request.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await checker.check("https://example.com", {})

        assert result.is_healthy is True
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_http_server_error(self):
        """Test HTTP check with server error."""
        checker = HTTPChecker(timeout=5.0)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.request.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await checker.check("https://example.com", {"expected_status": 200})

        assert result.is_healthy is False
        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_http_connection_error(self):
        """Test HTTP check with connection error."""
        checker = HTTPChecker(timeout=1.0)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request.side_effect = httpx.ConnectError("Connection refused")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await checker.check("https://nonexistent.invalid", {})

        assert result.is_healthy is False
        assert result.error is not None


class TestTCPChecker:
    """Test TCP connectivity checker."""

    @pytest.mark.asyncio
    async def test_tcp_success(self):
        """Test successful TCP connection."""
        checker = TCPChecker(timeout=5.0)

        with patch("asyncio.open_connection") as mock_open:
            mock_reader = AsyncMock()
            mock_writer = MagicMock()
            mock_writer.close = MagicMock()
            mock_writer.wait_closed = AsyncMock()
            mock_open.return_value = (mock_reader, mock_writer)

            result = await checker.check("localhost:80", {})

        assert result.is_healthy is True

    @pytest.mark.asyncio
    async def test_tcp_connection_refused(self):
        """Test TCP check with refused connection."""
        checker = TCPChecker(timeout=1.0)

        with patch("asyncio.open_connection") as mock_open:
            mock_open.side_effect = ConnectionRefusedError()

            result = await checker.check("localhost:99999", {})

        assert result.is_healthy is False
        assert result.error is not None


class TestGetChecker:
    """Test checker factory function."""

    def test_get_http_checker(self):
        """Test getting HTTP checker."""
        checker = get_checker("http", timeout=10.0)
        assert isinstance(checker, HTTPChecker)

    def test_get_tcp_checker(self):
        """Test getting TCP checker."""
        checker = get_checker("tcp", timeout=10.0)
        assert isinstance(checker, TCPChecker)

    def test_get_unknown_checker(self):
        """Test getting unknown checker type."""
        with pytest.raises(ValueError):
            get_checker("unknown", timeout=10.0)
