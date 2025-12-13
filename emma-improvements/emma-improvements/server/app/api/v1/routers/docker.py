"""Docker container monitoring API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, require_admin, require_operator
from app.models.user import User
from app.schemas.docker import (
    ContainerListResponse,
    ContainerLogsResponse,
    ContainerResponse,
    ContainerStatsResponse,
    DockerInfoResponse,
)
from app.services.docker_service import (
    ContainerNotFoundError,
    DockerError,
    DockerNotAvailableError,
    get_docker_service,
)

router = APIRouter(prefix="/docker", tags=["docker"])
logger = structlog.get_logger(__name__)


def get_docker():
    """Dependency to get Docker service."""
    try:
        return get_docker_service()
    except DockerNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker monitoring is not available",
        ) from e


@router.get("/info", response_model=DockerInfoResponse)
async def get_docker_info(
    current_user: Annotated[User, Depends(get_current_user)],
    docker=Depends(get_docker),
) -> DockerInfoResponse:
    """Get Docker daemon information."""
    try:
        info = await docker.get_docker_info()
        return DockerInfoResponse(**info)
    except DockerError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/containers", response_model=ContainerListResponse)
async def list_containers(
    current_user: Annotated[User, Depends(get_current_user)],
    docker=Depends(get_docker),
    all: bool = Query(True),
    status_filter: str | None = Query(None, alias="status"),
) -> ContainerListResponse:
    """List all Docker containers."""
    try:
        filters = {"status": [status_filter]} if status_filter else None
        containers = await docker.list_containers(all=all, filters=filters)
        return ContainerListResponse(
            items=[ContainerResponse(**c.to_dict()) for c in containers],
            total=len(containers),
        )
    except DockerError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/containers/{container_id}", response_model=ContainerResponse)
async def get_container(
    container_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    docker=Depends(get_docker),
) -> ContainerResponse:
    """Get container details."""
    try:
        container = await docker.get_container(container_id)
        return ContainerResponse(**container.to_dict())
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DockerError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/containers/{container_id}/stats", response_model=ContainerStatsResponse)
async def get_container_stats(
    container_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    docker=Depends(get_docker),
) -> ContainerStatsResponse:
    """Get container resource statistics."""
    try:
        stats = await docker.get_container_stats(container_id)
        return ContainerStatsResponse(**stats.to_dict())
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DockerError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/containers/{container_id}/logs", response_model=ContainerLogsResponse)
async def get_container_logs(
    container_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    docker=Depends(get_docker),
    tail: int = Query(100, ge=1, le=10000),
    timestamps: bool = Query(True),
) -> ContainerLogsResponse:
    """Get container logs."""
    try:
        logs = await docker.get_container_logs(container_id, tail=tail, timestamps=timestamps)
        return ContainerLogsResponse(container_id=container_id, logs=logs, total_lines=len(logs))
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DockerError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/containers/{container_id}/start", status_code=204)
async def start_container(
    container_id: str,
    current_user: Annotated[User, Depends(require_operator)],
    docker=Depends(get_docker),
) -> None:
    """Start a container."""
    try:
        await docker.start_container(container_id)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DockerError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/containers/{container_id}/stop", status_code=204)
async def stop_container(
    container_id: str,
    current_user: Annotated[User, Depends(require_operator)],
    docker=Depends(get_docker),
    timeout: int = Query(10, ge=1, le=300),
) -> None:
    """Stop a container."""
    try:
        await docker.stop_container(container_id, timeout=timeout)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DockerError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/containers/{container_id}/restart", status_code=204)
async def restart_container(
    container_id: str,
    current_user: Annotated[User, Depends(require_operator)],
    docker=Depends(get_docker),
    timeout: int = Query(10, ge=1, le=300),
) -> None:
    """Restart a container."""
    try:
        await docker.restart_container(container_id, timeout=timeout)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DockerError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/containers/{container_id}", status_code=204)
async def remove_container(
    container_id: str,
    current_user: Annotated[User, Depends(require_admin)],
    docker=Depends(get_docker),
    force: bool = Query(False),
) -> None:
    """Remove a container (admin only)."""
    try:
        await docker.remove_container(container_id, force=force)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except DockerError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
