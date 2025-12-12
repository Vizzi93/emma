"""Pydantic schemas for Docker container monitoring."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContainerPortMapping(BaseModel):
    """Port mapping details."""
    
    host_ip: str
    host_port: str


class ContainerResponse(BaseModel):
    """Container information response."""
    
    id: str
    short_id: str
    name: str
    image: str
    status: str
    state: str
    created: datetime
    started_at: datetime | None
    ports: dict[str, list[ContainerPortMapping]]
    labels: dict[str, str]
    health_status: str | None

    class Config:
        from_attributes = True


class ContainerStatsResponse(BaseModel):
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

    class Config:
        from_attributes = True


class ContainerListResponse(BaseModel):
    """List of containers."""
    
    items: list[ContainerResponse]
    total: int


class DockerInfoResponse(BaseModel):
    """Docker daemon information."""
    
    containers: int
    containers_running: int
    containers_paused: int
    containers_stopped: int
    images: int
    docker_version: str
    os: str
    architecture: str
    cpus: int
    memory: int
    storage_driver: str


class ContainerActionRequest(BaseModel):
    """Request for container actions."""
    
    timeout: int = Field(default=10, ge=1, le=300)


class ContainerLogsRequest(BaseModel):
    """Request for container logs."""
    
    tail: int = Field(default=100, ge=1, le=10000)
    since: datetime | None = None
    timestamps: bool = True


class ContainerLogsResponse(BaseModel):
    """Container logs response."""
    
    container_id: str
    logs: list[str]
    total_lines: int


class ContainerFilterParams(BaseModel):
    """Query parameters for filtering containers."""
    
    all: bool = Field(default=True, description="Include stopped containers")
    status: str | None = Field(
        default=None,
        pattern="^(created|restarting|running|removing|paused|exited|dead)$",
    )
    name: str | None = Field(default=None, max_length=255)
    label: str | None = Field(default=None, max_length=255)
