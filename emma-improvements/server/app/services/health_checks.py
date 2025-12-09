"""Health check executors for different service types."""

from __future__ import annotations

import asyncio
import socket
import ssl
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CheckResult:
    """Result of a health check execution."""
    
    is_healthy: bool
    response_time_ms: float
    status_code: int | None = None
    message: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BaseChecker(ABC):
    """Abstract base class for health checkers."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    @abstractmethod
    async def check(self, target: str, config: dict[str, Any]) -> CheckResult:
        """Execute health check and return result."""
        pass

    def _measure_time(self, start: float) -> float:
        """Calculate elapsed time in milliseconds."""
        return (time.perf_counter() - start) * 1000


class HTTPChecker(BaseChecker):
    """HTTP/HTTPS endpoint health checker."""

    async def check(self, target: str, config: dict[str, Any]) -> CheckResult:
        """
        Check HTTP endpoint health.
        
        Config options:
            method: HTTP method (default: GET)
            expected_status: Expected status code (default: 200)
            expected_body: String that should be in response body
            headers: Additional headers to send
            verify_ssl: Whether to verify SSL (default: True)
            follow_redirects: Whether to follow redirects (default: True)
        """
        start = time.perf_counter()
        
        method = config.get("method", "GET").upper()
        expected_status = config.get("expected_status", 200)
        expected_body = config.get("expected_body")
        headers = config.get("headers", {})
        verify_ssl = config.get("verify_ssl", True)
        follow_redirects = config.get("follow_redirects", True)

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=verify_ssl,
                follow_redirects=follow_redirects,
            ) as client:
                response = await client.request(method, target, headers=headers)
                response_time = self._measure_time(start)

                # Check status code
                status_ok = response.status_code == expected_status
                
                # Check body content if specified
                body_ok = True
                if expected_body and expected_body not in response.text:
                    body_ok = False

                is_healthy = status_ok and body_ok
                
                message = None
                if not status_ok:
                    message = f"Expected status {expected_status}, got {response.status_code}"
                elif not body_ok:
                    message = f"Response body does not contain expected content"

                return CheckResult(
                    is_healthy=is_healthy,
                    response_time_ms=response_time,
                    status_code=response.status_code,
                    message=message,
                    metadata={
                        "content_length": len(response.content),
                        "headers": dict(response.headers),
                    },
                )

        except httpx.TimeoutException:
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"Request timeout after {self.timeout}s",
            )
        except httpx.ConnectError as e:
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"Connection failed: {str(e)}",
            )
        except Exception as e:
            logger.exception("http_check_error", target=target, error=str(e))
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"Check failed: {str(e)}",
            )


class TCPChecker(BaseChecker):
    """TCP port connectivity checker."""

    async def check(self, target: str, config: dict[str, Any]) -> CheckResult:
        """
        Check TCP port connectivity.
        
        Target format: host:port
        """
        start = time.perf_counter()

        try:
            # Parse host:port
            if ":" not in target:
                return CheckResult(
                    is_healthy=False,
                    response_time_ms=0,
                    error="Invalid target format. Expected host:port",
                )
            
            host, port_str = target.rsplit(":", 1)
            port = int(port_str)

            # Try to connect
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout,
            )
            writer.close()
            await writer.wait_closed()

            return CheckResult(
                is_healthy=True,
                response_time_ms=self._measure_time(start),
                message=f"Successfully connected to {host}:{port}",
                metadata={"host": host, "port": port},
            )

        except asyncio.TimeoutError:
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"Connection timeout after {self.timeout}s",
            )
        except ConnectionRefusedError:
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error="Connection refused",
            )
        except Exception as e:
            logger.exception("tcp_check_error", target=target, error=str(e))
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"Check failed: {str(e)}",
            )


class SSLChecker(BaseChecker):
    """SSL certificate checker."""

    async def check(self, target: str, config: dict[str, Any]) -> CheckResult:
        """
        Check SSL certificate validity and expiration.
        
        Target: hostname or hostname:port
        Config options:
            warn_days: Days before expiry to warn (default: 30)
        """
        start = time.perf_counter()
        warn_days = config.get("warn_days", 30)

        try:
            # Parse target
            if ":" in target:
                host, port_str = target.rsplit(":", 1)
                port = int(port_str)
            else:
                host = target
                port = 443

            # Get certificate info
            cert_info = await asyncio.to_thread(
                self._get_cert_info, host, port
            )

            if cert_info is None:
                return CheckResult(
                    is_healthy=False,
                    response_time_ms=self._measure_time(start),
                    error="Could not retrieve SSL certificate",
                )

            # Check expiration
            expires_at = cert_info["expires_at"]
            days_until_expiry = (expires_at - datetime.now(timezone.utc)).days

            is_healthy = days_until_expiry > warn_days
            is_valid = days_until_expiry > 0

            message = None
            if days_until_expiry <= 0:
                message = "Certificate has expired!"
            elif days_until_expiry <= warn_days:
                message = f"Certificate expires in {days_until_expiry} days"

            return CheckResult(
                is_healthy=is_healthy,
                response_time_ms=self._measure_time(start),
                message=message,
                metadata={
                    "subject": cert_info["subject"],
                    "issuer": cert_info["issuer"],
                    "expires_at": expires_at.isoformat(),
                    "days_until_expiry": days_until_expiry,
                    "is_valid": is_valid,
                    "serial_number": cert_info["serial_number"],
                },
            )

        except ssl.SSLError as e:
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"SSL error: {str(e)}",
            )
        except Exception as e:
            logger.exception("ssl_check_error", target=target, error=str(e))
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"Check failed: {str(e)}",
            )

    def _get_cert_info(self, host: str, port: int) -> dict[str, Any] | None:
        """Retrieve SSL certificate information."""
        context = ssl.create_default_context()
        
        with socket.create_connection((host, port), timeout=self.timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                
                if not cert:
                    return None

                # Parse subject
                subject_parts = []
                for rdn in cert.get("subject", []):
                    for key, value in rdn:
                        subject_parts.append(f"{key}={value}")
                subject = ", ".join(subject_parts)

                # Parse issuer
                issuer_parts = []
                for rdn in cert.get("issuer", []):
                    for key, value in rdn:
                        issuer_parts.append(f"{key}={value}")
                issuer = ", ".join(issuer_parts)

                # Parse dates
                not_after = cert.get("notAfter", "")
                expires_at = datetime.strptime(
                    not_after, "%b %d %H:%M:%S %Y %Z"
                ).replace(tzinfo=timezone.utc)

                return {
                    "subject": subject,
                    "issuer": issuer,
                    "expires_at": expires_at,
                    "serial_number": cert.get("serialNumber", ""),
                }


class DNSChecker(BaseChecker):
    """DNS resolution checker."""

    async def check(self, target: str, config: dict[str, Any]) -> CheckResult:
        """
        Check DNS resolution.
        
        Target: domain name
        Config options:
            expected_ip: Expected IP address (optional)
            record_type: DNS record type (default: A)
        """
        start = time.perf_counter()
        expected_ip = config.get("expected_ip")

        try:
            # Resolve DNS
            result = await asyncio.to_thread(socket.gethostbyname, target)
            response_time = self._measure_time(start)

            is_healthy = True
            message = f"Resolved to {result}"

            if expected_ip and result != expected_ip:
                is_healthy = False
                message = f"Expected {expected_ip}, got {result}"

            return CheckResult(
                is_healthy=is_healthy,
                response_time_ms=response_time,
                message=message,
                metadata={"resolved_ip": result},
            )

        except socket.gaierror as e:
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"DNS resolution failed: {str(e)}",
            )
        except Exception as e:
            logger.exception("dns_check_error", target=target, error=str(e))
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"Check failed: {str(e)}",
            )


class PingChecker(BaseChecker):
    """ICMP ping checker (requires appropriate permissions)."""

    async def check(self, target: str, config: dict[str, Any]) -> CheckResult:
        """
        Check host reachability via ping.
        
        Note: May require root/admin privileges.
        """
        start = time.perf_counter()
        count = config.get("count", 3)

        try:
            # Use system ping command
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", str(count), "-W", str(int(self.timeout)), target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout + 5,
            )

            response_time = self._measure_time(start)
            is_healthy = proc.returncode == 0

            # Parse average response time from output
            avg_time = None
            output = stdout.decode()
            if "avg" in output.lower():
                # Try to extract average time
                import re
                match = re.search(r"avg[^=]*=\s*[\d.]+/([\d.]+)/", output)
                if match:
                    avg_time = float(match.group(1))

            return CheckResult(
                is_healthy=is_healthy,
                response_time_ms=avg_time or response_time,
                message="Host is reachable" if is_healthy else "Host unreachable",
                metadata={"output": output[:500]},  # Truncate output
            )

        except asyncio.TimeoutError:
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"Ping timeout after {self.timeout}s",
            )
        except Exception as e:
            logger.exception("ping_check_error", target=target, error=str(e))
            return CheckResult(
                is_healthy=False,
                response_time_ms=self._measure_time(start),
                error=f"Check failed: {str(e)}",
            )


# Checker registry
CHECKERS: dict[str, type[BaseChecker]] = {
    "http": HTTPChecker,
    "https": HTTPChecker,
    "tcp": TCPChecker,
    "ssl": SSLChecker,
    "dns": DNSChecker,
    "ping": PingChecker,
}


def get_checker(check_type: str, timeout: float = 30.0) -> BaseChecker:
    """Get appropriate checker for service type."""
    checker_class = CHECKERS.get(check_type.lower())
    if not checker_class:
        raise ValueError(f"Unknown check type: {check_type}")
    return checker_class(timeout=timeout)
