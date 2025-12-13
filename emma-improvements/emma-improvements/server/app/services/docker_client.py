"""Docker container monitoring and management."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class ContainerState(str, Enum):
    """Docker container states."""
    
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    EXITED = "exited"
    DEAD = "dead"
    CREATED = "created"
    REMOVING = "removing"


@dataclass
class ContainerStats:
    """Container resource usage statistics."""
    
    cpu_percent: float = 0.0
    memory_usage_mb: float = 0.0
    memory_limit_mb: float = 0.0
    memory_percent: float = 0.0
    network_rx_mb: float = 0.0
    network_tx_mb: float = 0.0
    block_read_mb: float = 0.0
    block_write_mb: float = 0.0
    pids: int = 0


@dataclass
class Container:
    """Docker container information."""
    
    id: str
    short_id: str
    name: str
    image: str
    state: ContainerState
    status: str  # Human readable status like "Up 2 hours"
    created_at: datetime
    started_at: datetime | None = None
    ports: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    networks: list[str] = field(default_factory=list)
    stats: ContainerStats | None = None
    health_status: str | None = None  # healthy, unhealthy, starting, none

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "short_id": self.short_id,
            "name": self.name,
            "image": self.image,
            "state": self.state.value,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ports": self.ports,
            "labels": self.labels,
            "networks": self.networks,
            "health_status": self.health_status,
            "stats": {
                "cpu_percent": self.stats.cpu_percent,
                "memory_usage_mb": round(self.stats.memory_usage_mb, 2),
                "memory_limit_mb": round(self.stats.memory_limit_mb, 2),
                "memory_percent": round(self.stats.memory_percent, 2),
                "network_rx_mb": round(self.stats.network_rx_mb, 2),
                "network_tx_mb": round(self.stats.network_tx_mb, 2),
                "pids": self.stats.pids,
            } if self.stats else None,
        }


@dataclass
class DockerHost:
    """Docker host configuration."""
    
    id: str
    name: str
    url: str  # unix:///var/run/docker.sock or tcp://host:2375
    is_local: bool = True
    tls_verify: bool = False
    tls_cert_path: str | None = None


class DockerClientError(Exception):
    """Docker client error."""
    pass


class DockerClient:
    """
    Async Docker API client.
    
    Supports both Unix socket and TCP connections.
    """

    def __init__(self, host: DockerHost) -> None:
        self.host = host
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            if self.host.url.startswith("unix://"):
                # Unix socket connection
                socket_path = self.host.url.replace("unix://", "")
                transport = httpx.AsyncHTTPTransport(uds=socket_path)
                self._client = httpx.AsyncClient(
                    transport=transport,
                    base_url="http://localhost",
                    timeout=30.0,
                )
            else:
                # TCP connection
                self._client = httpx.AsyncClient(
                    base_url=self.host.url,
                    timeout=30.0,
                    verify=self.host.tls_verify,
                )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def ping(self) -> bool:
        """Check if Docker daemon is accessible."""
        try:
            client = await self._get_client()
            response = await client.get("/_ping")
            return response.status_code == 200
        except Exception as e:
            logger.warning("docker_ping_failed", host=self.host.name, error=str(e))
            return False

    async def get_info(self) -> dict[str, Any]:
        """Get Docker system info."""
        client = await self._get_client()
        response = await client.get("/info")
        response.raise_for_status()
        return response.json()

    async def list_containers(self, all: bool = True) -> list[Container]:
        """List all containers."""
        try:
            client = await self._get_client()
            response = await client.get("/containers/json", params={"all": str(all).lower()})
            response.raise_for_status()
            
            containers = []
            for data in response.json():
                container = self._parse_container(data)
                containers.append(container)
            
            return containers
            
        except Exception as e:
            logger.exception("docker_list_containers_failed", host=self.host.name, error=str(e))
            raise DockerClientError(f"Failed to list containers: {e}") from e

    async def get_container(self, container_id: str) -> Container:
        """Get container details."""
        try:
            client = await self._get_client()
            response = await client.get(f"/containers/{container_id}/json")
            response.raise_for_status()
            
            data = response.json()
            return self._parse_container_detail(data)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise DockerClientError(f"Container {container_id} not found") from e
            raise DockerClientError(f"Failed to get container: {e}") from e

    async def get_container_stats(self, container_id: str) -> ContainerStats:
        """Get container resource stats (single snapshot, non-streaming)."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"/containers/{container_id}/stats",
                params={"stream": "false"},
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_stats(data)
            
        except Exception as e:
            logger.warning("docker_stats_failed", container_id=container_id, error=str(e))
            return ContainerStats()

    async def start_container(self, container_id: str) -> bool:
        """Start a container."""
        try:
            client = await self._get_client()
            response = await client.post(f"/containers/{container_id}/start")
            return response.status_code in (204, 304)  # 304 = already started
        except Exception as e:
            logger.exception("docker_start_failed", container_id=container_id, error=str(e))
            raise DockerClientError(f"Failed to start container: {e}") from e

    async def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a container."""
        try:
            client = await self._get_client()
            response = await client.post(
                f"/containers/{container_id}/stop",
                params={"t": timeout},
            )
            return response.status_code in (204, 304)  # 304 = already stopped
        except Exception as e:
            logger.exception("docker_stop_failed", container_id=container_id, error=str(e))
            raise DockerClientError(f"Failed to stop container: {e}") from e

    async def restart_container(self, container_id: str, timeout: int = 10) -> bool:
        """Restart a container."""
        try:
            client = await self._get_client()
            response = await client.post(
                f"/containers/{container_id}/restart",
                params={"t": timeout},
            )
            return response.status_code == 204
        except Exception as e:
            logger.exception("docker_restart_failed", container_id=container_id, error=str(e))
            raise DockerClientError(f"Failed to restart container: {e}") from e

    async def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        since: int | None = None,
    ) -> str:
        """Get container logs."""
        try:
            client = await self._get_client()
            params = {
                "stdout": "true",
                "stderr": "true",
                "tail": str(tail),
                "timestamps": "true",
            }
            if since:
                params["since"] = str(since)
            
            response = await client.get(
                f"/containers/{container_id}/logs",
                params=params,
            )
            response.raise_for_status()
            
            # Docker logs have a header for each line, strip it
            return self._clean_logs(response.content)
            
        except Exception as e:
            logger.exception("docker_logs_failed", container_id=container_id, error=str(e))
            raise DockerClientError(f"Failed to get logs: {e}") from e

    def _parse_container(self, data: dict[str, Any]) -> Container:
        """Parse container from list response."""
        # Extract name (remove leading /)
        names = data.get("Names", [])
        name = names[0].lstrip("/") if names else data.get("Id", "")[:12]
        
        # Parse state
        state_str = data.get("State", "unknown").lower()
        try:
            state = ContainerState(state_str)
        except ValueError:
            state = ContainerState.EXITED
        
        # Parse created timestamp
        created = datetime.fromtimestamp(data.get("Created", 0), tz=timezone.utc)
        
        # Parse ports
        ports = {}
        for port_info in data.get("Ports", []):
            private_port = f"{port_info.get('PrivatePort')}/{port_info.get('Type', 'tcp')}"
            if private_port not in ports:
                ports[private_port] = []
            if port_info.get("PublicPort"):
                ports[private_port].append({
                    "host_ip": port_info.get("IP", "0.0.0.0"),
                    "host_port": port_info.get("PublicPort"),
                })
        
        # Parse networks
        network_settings = data.get("NetworkSettings", {})
        networks = list(network_settings.get("Networks", {}).keys())
        
        return Container(
            id=data.get("Id", ""),
            short_id=data.get("Id", "")[:12],
            name=name,
            image=data.get("Image", ""),
            state=state,
            status=data.get("Status", ""),
            created_at=created,
            ports=ports,
            labels=data.get("Labels", {}),
            networks=networks,
        )

    def _parse_container_detail(self, data: dict[str, Any]) -> Container:
        """Parse container from inspect response."""
        config = data.get("Config", {})
        state_data = data.get("State", {})
        network_settings = data.get("NetworkSettings", {})
        
        # Parse state
        state_str = state_data.get("Status", "unknown").lower()
        try:
            state = ContainerState(state_str)
        except ValueError:
            state = ContainerState.EXITED
        
        # Parse timestamps
        created = datetime.fromisoformat(
            data.get("Created", "1970-01-01T00:00:00Z").replace("Z", "+00:00")
        )
        started_at = None
        if state_data.get("StartedAt") and not state_data["StartedAt"].startswith("0001"):
            started_at = datetime.fromisoformat(
                state_data["StartedAt"].replace("Z", "+00:00")
            )
        
        # Parse ports
        ports = {}
        for container_port, host_bindings in network_settings.get("Ports", {}).items():
            ports[container_port] = []
            if host_bindings:
                for binding in host_bindings:
                    ports[container_port].append({
                        "host_ip": binding.get("HostIp", "0.0.0.0"),
                        "host_port": int(binding.get("HostPort", 0)),
                    })
        
        # Health status
        health = state_data.get("Health", {})
        health_status = health.get("Status") if health else None
        
        return Container(
            id=data.get("Id", ""),
            short_id=data.get("Id", "")[:12],
            name=data.get("Name", "").lstrip("/"),
            image=config.get("Image", ""),
            state=state,
            status=f"{state.value} ({state_data.get('Status', '')})",
            created_at=created,
            started_at=started_at,
            ports=ports,
            labels=config.get("Labels", {}),
            networks=list(network_settings.get("Networks", {}).keys()),
            health_status=health_status,
        )

    def _parse_stats(self, data: dict[str, Any]) -> ContainerStats:
        """Parse container stats response."""
        # CPU calculation
        cpu_delta = (
            data.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0) -
            data.get("precpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
        )
        system_delta = (
            data.get("cpu_stats", {}).get("system_cpu_usage", 0) -
            data.get("precpu_stats", {}).get("system_cpu_usage", 0)
        )
        num_cpus = data.get("cpu_stats", {}).get("online_cpus", 1) or 1
        
        cpu_percent = 0.0
        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
        
        # Memory
        memory_stats = data.get("memory_stats", {})
        memory_usage = memory_stats.get("usage", 0)
        memory_limit = memory_stats.get("limit", 1)
        memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0
        
        # Network I/O
        networks = data.get("networks", {})
        network_rx = sum(n.get("rx_bytes", 0) for n in networks.values())
        network_tx = sum(n.get("tx_bytes", 0) for n in networks.values())
        
        # Block I/O
        blkio = data.get("blkio_stats", {}).get("io_service_bytes_recursive", []) or []
        block_read = sum(item.get("value", 0) for item in blkio if item.get("op") == "read")
        block_write = sum(item.get("value", 0) for item in blkio if item.get("op") == "write")
        
        return ContainerStats(
            cpu_percent=round(cpu_percent, 2),
            memory_usage_mb=memory_usage / (1024 * 1024),
            memory_limit_mb=memory_limit / (1024 * 1024),
            memory_percent=memory_percent,
            network_rx_mb=network_rx / (1024 * 1024),
            network_tx_mb=network_tx / (1024 * 1024),
            block_read_mb=block_read / (1024 * 1024),
            block_write_mb=block_write / (1024 * 1024),
            pids=data.get("pids_stats", {}).get("current", 0),
        )

    def _clean_logs(self, content: bytes) -> str:
        """Remove Docker log headers and decode content."""
        lines = []
        i = 0
        while i < len(content):
            # Docker multiplexed stream header is 8 bytes
            if i + 8 <= len(content):
                # Skip header, read size from bytes 4-7
                size = int.from_bytes(content[i+4:i+8], byteorder='big')
                i += 8
                if i + size <= len(content):
                    line = content[i:i+size].decode('utf-8', errors='replace').strip()
                    if line:
                        lines.append(line)
                    i += size
                else:
                    break
            else:
                break
        return "\n".join(lines)


class DockerManager:
    """Manages multiple Docker hosts."""

    def __init__(self) -> None:
        self._hosts: dict[str, DockerHost] = {}
        self._clients: dict[str, DockerClient] = {}

    def add_host(self, host: DockerHost) -> None:
        """Register a Docker host."""
        self._hosts[host.id] = host
        self._clients[host.id] = DockerClient(host)
        logger.info("docker_host_added", host_id=host.id, name=host.name)

    def remove_host(self, host_id: str) -> None:
        """Remove a Docker host."""
        if host_id in self._hosts:
            del self._hosts[host_id]
        if host_id in self._clients:
            del self._clients[host_id]

    def get_client(self, host_id: str) -> DockerClient:
        """Get client for a specific host."""
        if host_id not in self._clients:
            raise DockerClientError(f"Unknown Docker host: {host_id}")
        return self._clients[host_id]

    @property
    def hosts(self) -> list[DockerHost]:
        """Get all registered hosts."""
        return list(self._hosts.values())

    async def close_all(self) -> None:
        """Close all clients."""
        for client in self._clients.values():
            await client.close()


# Global Docker manager instance
_docker_manager: DockerManager | None = None


def get_docker_manager() -> DockerManager:
    """Get or create global Docker manager."""
    global _docker_manager
    if _docker_manager is None:
        _docker_manager = DockerManager()
        
        # Add default local Docker socket
        _docker_manager.add_host(DockerHost(
            id="local",
            name="Local Docker",
            url="unix:///var/run/docker.sock",
            is_local=True,
        ))
    
    return _docker_manager
