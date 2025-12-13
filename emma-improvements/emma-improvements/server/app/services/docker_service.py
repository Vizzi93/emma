"""Docker container monitoring and management service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import structlog

logger = structlog.get_logger(__name__)

# Try to import aiodocker, gracefully handle if not installed
try:
    import aiodocker
    DOCKER_AVAILABLE = True
except ImportError:
    aiodocker = None  # type: ignore
    DOCKER_AVAILABLE = False
    logger.warning("aiodocker not installed, Docker monitoring disabled")


@dataclass
class ContainerInfo:
    """Container information."""
    
    id: str
    short_id: str
    name: str
    image: str
    status: str
    state: str
    created: datetime
    started_at: datetime | None
    ports: dict[str, list[dict[str, str]]]
    labels: dict[str, str]
    health_status: str | None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "short_id": self.short_id,
            "name": self.name,
            "image": self.image,
            "status": self.status,
            "state": self.state,
            "created": self.created.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ports": self.ports,
            "labels": self.labels,
            "health_status": self.health_status,
        }


@dataclass
class ContainerStats:
    """Container resource statistics."""
    
    container_id: str
    container_name: str
    cpu_percent: float
    memory_usage: int
    memory_limit: int
    memory_percent: float
    network_rx: int
    network_tx: int
    block_read: int
    block_write: int
    pids: int
    timestamp: datetime
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "container_id": self.container_id,
            "container_name": self.container_name,
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_usage": self.memory_usage,
            "memory_limit": self.memory_limit,
            "memory_percent": round(self.memory_percent, 2),
            "network_rx": self.network_rx,
            "network_tx": self.network_tx,
            "block_read": self.block_read,
            "block_write": self.block_write,
            "pids": self.pids,
            "timestamp": self.timestamp.isoformat(),
        }


class DockerError(Exception):
    """Docker-related error."""
    pass


class DockerNotAvailableError(DockerError):
    """Docker is not available."""
    pass


class ContainerNotFoundError(DockerError):
    """Container not found."""
    pass


class DockerService:
    """
    Service for Docker container monitoring and management.
    
    Uses aiodocker for async Docker API communication.
    Supports both socket and TCP connections.
    """

    def __init__(self, docker_url: str | None = None) -> None:
        """
        Initialize Docker service.
        
        Args:
            docker_url: Docker daemon URL. Defaults to unix socket.
                       Examples: unix:///var/run/docker.sock, tcp://localhost:2375
        """
        if not DOCKER_AVAILABLE:
            raise DockerNotAvailableError(
                "aiodocker is not installed. Run: pip install aiodocker"
            )
        
        self._docker_url = docker_url
        self._client: aiodocker.Docker | None = None

    async def connect(self) -> None:
        """Connect to Docker daemon."""
        try:
            self._client = aiodocker.Docker(url=self._docker_url)
            # Test connection
            await self._client.version()
            logger.info("docker_connected", url=self._docker_url or "default")
        except Exception as e:
            logger.error("docker_connection_failed", error=str(e))
            raise DockerError(f"Failed to connect to Docker: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from Docker daemon."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("docker_disconnected")

    async def _ensure_connected(self) -> aiodocker.Docker:
        """Ensure we have an active connection."""
        if self._client is None:
            await self.connect()
        return self._client  # type: ignore

    # === Container Information ===

    async def list_containers(
        self,
        all: bool = True,
        filters: dict[str, Any] | None = None,
    ) -> list[ContainerInfo]:
        """
        List all containers.
        
        Args:
            all: Include stopped containers
            filters: Docker API filters (e.g., {"status": ["running"]})
        """
        client = await self._ensure_connected()
        
        try:
            containers = await client.containers.list(all=all, filters=filters)
            result = []
            
            for container in containers:
                info = await self._parse_container_info(container)
                result.append(info)
            
            return result
            
        except Exception as e:
            logger.exception("docker_list_error", error=str(e))
            raise DockerError(f"Failed to list containers: {e}") from e

    async def get_container(self, container_id: str) -> ContainerInfo:
        """Get detailed container information."""
        client = await self._ensure_connected()
        
        try:
            container = await client.containers.get(container_id)
            return await self._parse_container_info(container)
        except aiodocker.exceptions.DockerError as e:
            if "404" in str(e):
                raise ContainerNotFoundError(f"Container {container_id} not found")
            raise DockerError(f"Failed to get container: {e}") from e

    async def _parse_container_info(self, container) -> ContainerInfo:
        """Parse container object into ContainerInfo."""
        data = container._container
        
        # Get container name (remove leading /)
        names = data.get("Names", [])
        name = names[0].lstrip("/") if names else data.get("Id", "")[:12]
        
        # Parse timestamps
        created = datetime.fromisoformat(
            data.get("Created", "").replace("Z", "+00:00")
        )
        
        # Get detailed info for started_at
        started_at = None
        state_data = data.get("State", {})
        if isinstance(state_data, dict) and state_data.get("StartedAt"):
            started_str = state_data["StartedAt"]
            if started_str and not started_str.startswith("0001"):
                try:
                    started_at = datetime.fromisoformat(
                        started_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
        
        # Parse health status
        health_status = None
        if isinstance(state_data, dict) and "Health" in state_data:
            health_status = state_data["Health"].get("Status")
        
        # Parse ports
        ports = {}
        for port_config in data.get("Ports", []):
            private = f"{port_config.get('PrivatePort')}/{port_config.get('Type', 'tcp')}"
            if private not in ports:
                ports[private] = []
            if port_config.get("PublicPort"):
                ports[private].append({
                    "host_ip": port_config.get("IP", "0.0.0.0"),
                    "host_port": str(port_config.get("PublicPort")),
                })
        
        return ContainerInfo(
            id=data.get("Id", ""),
            short_id=data.get("Id", "")[:12],
            name=name,
            image=data.get("Image", ""),
            status=data.get("Status", ""),
            state=data.get("State", "") if isinstance(data.get("State"), str) else state_data.get("Status", ""),
            created=created,
            started_at=started_at,
            ports=ports,
            labels=data.get("Labels", {}),
            health_status=health_status,
        )

    # === Container Stats ===

    async def get_container_stats(self, container_id: str) -> ContainerStats:
        """Get current resource statistics for a container."""
        client = await self._ensure_connected()
        
        try:
            container = await client.containers.get(container_id)
            stats = await container.stats(stream=False)
            
            # Parse the first (and only) stats entry
            if isinstance(stats, list):
                stats = stats[0] if stats else {}
            
            return self._parse_stats(container_id, stats)
            
        except aiodocker.exceptions.DockerError as e:
            if "404" in str(e):
                raise ContainerNotFoundError(f"Container {container_id} not found")
            raise DockerError(f"Failed to get stats: {e}") from e

    async def stream_container_stats(
        self,
        container_id: str,
    ) -> AsyncIterator[ContainerStats]:
        """Stream live statistics for a container."""
        client = await self._ensure_connected()
        
        try:
            container = await client.containers.get(container_id)
            
            async for stats in container.stats(stream=True):
                yield self._parse_stats(container_id, stats)
                
        except aiodocker.exceptions.DockerError as e:
            if "404" in str(e):
                raise ContainerNotFoundError(f"Container {container_id} not found")
            raise DockerError(f"Failed to stream stats: {e}") from e

    def _parse_stats(self, container_id: str, stats: dict) -> ContainerStats:
        """Parse Docker stats into ContainerStats."""
        # CPU calculation
        cpu_delta = (
            stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0) -
            stats.get("precpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
        )
        system_delta = (
            stats.get("cpu_stats", {}).get("system_cpu_usage", 0) -
            stats.get("precpu_stats", {}).get("system_cpu_usage", 0)
        )
        num_cpus = stats.get("cpu_stats", {}).get("online_cpus", 1)
        
        cpu_percent = 0.0
        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
        
        # Memory
        memory_stats = stats.get("memory_stats", {})
        memory_usage = memory_stats.get("usage", 0) - memory_stats.get("stats", {}).get("cache", 0)
        memory_limit = memory_stats.get("limit", 1)
        memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0
        
        # Network I/O
        network_rx = 0
        network_tx = 0
        for iface_stats in stats.get("networks", {}).values():
            network_rx += iface_stats.get("rx_bytes", 0)
            network_tx += iface_stats.get("tx_bytes", 0)
        
        # Block I/O
        block_read = 0
        block_write = 0
        for io_stat in stats.get("blkio_stats", {}).get("io_service_bytes_recursive", []) or []:
            if io_stat.get("op") == "read":
                block_read += io_stat.get("value", 0)
            elif io_stat.get("op") == "write":
                block_write += io_stat.get("value", 0)
        
        # PIDs
        pids = stats.get("pids_stats", {}).get("current", 0)
        
        return ContainerStats(
            container_id=container_id,
            container_name=stats.get("name", "").lstrip("/"),
            cpu_percent=cpu_percent,
            memory_usage=memory_usage,
            memory_limit=memory_limit,
            memory_percent=memory_percent,
            network_rx=network_rx,
            network_tx=network_tx,
            block_read=block_read,
            block_write=block_write,
            pids=pids,
            timestamp=datetime.now(timezone.utc),
        )

    # === Container Actions ===

    async def start_container(self, container_id: str) -> None:
        """Start a container."""
        client = await self._ensure_connected()
        
        try:
            container = await client.containers.get(container_id)
            await container.start()
            logger.info("container_started", container_id=container_id)
        except aiodocker.exceptions.DockerError as e:
            if "404" in str(e):
                raise ContainerNotFoundError(f"Container {container_id} not found")
            raise DockerError(f"Failed to start container: {e}") from e

    async def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Stop a container."""
        client = await self._ensure_connected()
        
        try:
            container = await client.containers.get(container_id)
            await container.stop(t=timeout)
            logger.info("container_stopped", container_id=container_id)
        except aiodocker.exceptions.DockerError as e:
            if "404" in str(e):
                raise ContainerNotFoundError(f"Container {container_id} not found")
            raise DockerError(f"Failed to stop container: {e}") from e

    async def restart_container(self, container_id: str, timeout: int = 10) -> None:
        """Restart a container."""
        client = await self._ensure_connected()
        
        try:
            container = await client.containers.get(container_id)
            await container.restart(t=timeout)
            logger.info("container_restarted", container_id=container_id)
        except aiodocker.exceptions.DockerError as e:
            if "404" in str(e):
                raise ContainerNotFoundError(f"Container {container_id} not found")
            raise DockerError(f"Failed to restart container: {e}") from e

    async def remove_container(
        self,
        container_id: str,
        force: bool = False,
        v: bool = False,
    ) -> None:
        """Remove a container."""
        client = await self._ensure_connected()
        
        try:
            container = await client.containers.get(container_id)
            await container.delete(force=force, v=v)
            logger.info("container_removed", container_id=container_id)
        except aiodocker.exceptions.DockerError as e:
            if "404" in str(e):
                raise ContainerNotFoundError(f"Container {container_id} not found")
            raise DockerError(f"Failed to remove container: {e}") from e

    # === Container Logs ===

    async def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        since: datetime | None = None,
        timestamps: bool = True,
    ) -> list[str]:
        """Get container logs."""
        client = await self._ensure_connected()
        
        try:
            container = await client.containers.get(container_id)
            
            params = {
                "stdout": True,
                "stderr": True,
                "tail": tail,
                "timestamps": timestamps,
            }
            
            if since:
                params["since"] = int(since.timestamp())
            
            logs = await container.log(**params)
            return logs
            
        except aiodocker.exceptions.DockerError as e:
            if "404" in str(e):
                raise ContainerNotFoundError(f"Container {container_id} not found")
            raise DockerError(f"Failed to get logs: {e}") from e

    async def stream_container_logs(
        self,
        container_id: str,
        since: datetime | None = None,
    ) -> AsyncIterator[str]:
        """Stream live container logs."""
        client = await self._ensure_connected()
        
        try:
            container = await client.containers.get(container_id)
            
            params = {
                "stdout": True,
                "stderr": True,
                "follow": True,
                "timestamps": True,
            }
            
            if since:
                params["since"] = int(since.timestamp())
            
            async for line in container.log(**params, stream=True):
                yield line
                
        except aiodocker.exceptions.DockerError as e:
            if "404" in str(e):
                raise ContainerNotFoundError(f"Container {container_id} not found")
            raise DockerError(f"Failed to stream logs: {e}") from e

    # === Docker Info ===

    async def get_docker_info(self) -> dict[str, Any]:
        """Get Docker daemon information."""
        client = await self._ensure_connected()
        
        try:
            info = await client.system.info()
            return {
                "containers": info.get("Containers", 0),
                "containers_running": info.get("ContainersRunning", 0),
                "containers_paused": info.get("ContainersPaused", 0),
                "containers_stopped": info.get("ContainersStopped", 0),
                "images": info.get("Images", 0),
                "docker_version": info.get("ServerVersion", ""),
                "os": info.get("OperatingSystem", ""),
                "architecture": info.get("Architecture", ""),
                "cpus": info.get("NCPU", 0),
                "memory": info.get("MemTotal", 0),
                "storage_driver": info.get("Driver", ""),
            }
        except Exception as e:
            raise DockerError(f"Failed to get Docker info: {e}") from e


# Global Docker service instance
_docker_service: DockerService | None = None


def get_docker_service(docker_url: str | None = None) -> DockerService:
    """Get or create the global Docker service."""
    global _docker_service
    
    if not DOCKER_AVAILABLE:
        raise DockerNotAvailableError(
            "aiodocker is not installed. Run: pip install aiodocker"
        )
    
    if _docker_service is None:
        _docker_service = DockerService(docker_url)
    
    return _docker_service


async def init_docker_service(docker_url: str | None = None) -> DockerService | None:
    """Initialize Docker service on startup."""
    if not DOCKER_AVAILABLE:
        logger.warning("docker_monitoring_disabled", reason="aiodocker not installed")
        return None
    
    try:
        service = get_docker_service(docker_url)
        await service.connect()
        return service
    except Exception as e:
        logger.warning("docker_init_failed", error=str(e))
        return None


async def shutdown_docker_service() -> None:
    """Shutdown Docker service."""
    global _docker_service
    if _docker_service:
        await _docker_service.disconnect()
        _docker_service = None
