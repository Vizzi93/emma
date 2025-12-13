"""Monitoring hierarchy API routes."""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.monitoring import (
    AggregatedStatus,
    HostListResponse,
    HostRefreshResponse,
    HostSchema,
    HostStatus,
    MonitoringHierarchyResponse,
    MonitoringStatsResponse,
    RegionSchema,
    ServiceCheckResponse,
    VerfahrenSchema,
)
from app.services.monitoring_service import (
    HostNotFoundError,
    MonitoringService,
    RegionNotFoundError,
    ServiceNotFoundError,
    VerfahrenNotFoundError,
    get_monitoring_service,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
logger = structlog.get_logger(__name__)


# === Dependency ===

def get_service() -> MonitoringService:
    """Get monitoring service instance."""
    return get_monitoring_service()


# === Hierarchy Endpoints ===

@router.get(
    "/hierarchy",
    response_model=MonitoringHierarchyResponse,
    summary="Get monitoring hierarchy",
    description="Returns the full monitoring hierarchy with regions, verfahren, and hosts. "
                "Results are cached for 30 seconds.",
)
async def get_hierarchy(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MonitoringService, Depends(get_service)],
    region: str | None = Query(
        None,
        description="Filter by region name (case-insensitive partial match)",
        examples=["bremerhaven", "hamburg"],
    ),
    status: AggregatedStatus | None = Query(
        None,
        description="Filter by aggregated status",
        examples=["healthy", "degraded", "critical"],
    ),
    include_offline: bool = Query(
        True,
        alias="includeOffline",
        description="Include offline hosts in response",
    ),
) -> MonitoringHierarchyResponse:
    """
    Get the full monitoring hierarchy.

    Returns all regions with their verfahren and hosts.
    Supports filtering by region name and aggregated status.
    """
    logger.debug(
        "hierarchy_requested",
        user_id=str(current_user.id),
        region_filter=region,
        status_filter=status.value if status else None,
    )

    hierarchy = await service.get_hierarchy(
        region_filter=region,
        status_filter=status,
        include_offline=include_offline,
    )

    return hierarchy


@router.get(
    "/stats",
    response_model=MonitoringStatsResponse,
    summary="Get monitoring statistics",
    description="Returns aggregated statistics across all regions and hosts.",
)
async def get_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MonitoringService, Depends(get_service)],
) -> MonitoringStatsResponse:
    """Get aggregated monitoring statistics."""
    return await service.get_stats()


# === Region Endpoints ===

@router.get(
    "/regions/{region_id}",
    response_model=RegionSchema,
    summary="Get region details",
)
async def get_region(
    region_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MonitoringService, Depends(get_service)],
) -> RegionSchema:
    """Get details of a specific region by ID."""
    try:
        return await service.get_region(region_id)
    except RegionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# === Verfahren Endpoints ===

@router.get(
    "/verfahren/{verfahren_id}",
    response_model=VerfahrenSchema,
    summary="Get verfahren details",
)
async def get_verfahren(
    verfahren_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MonitoringService, Depends(get_service)],
) -> VerfahrenSchema:
    """Get details of a specific verfahren by ID."""
    try:
        return await service.get_verfahren(verfahren_id)
    except VerfahrenNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# === Host Endpoints ===

@router.get(
    "/hosts",
    response_model=HostListResponse,
    summary="List all hosts",
)
async def list_hosts(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MonitoringService, Depends(get_service)],
    status: HostStatus | None = Query(None, description="Filter by host status"),
    region_id: str | None = Query(None, description="Filter by region ID"),
    verfahren_id: str | None = Query(None, description="Filter by verfahren ID"),
) -> HostListResponse:
    """List all hosts with optional filters."""
    items, total = await service.list_hosts(
        status=status,
        region_id=region_id,
        verfahren_id=verfahren_id,
    )

    return HostListResponse(items=items, total=total)


@router.get(
    "/hosts/{host_id}",
    response_model=HostSchema,
    summary="Get host details",
)
async def get_host(
    host_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MonitoringService, Depends(get_service)],
) -> HostSchema:
    """Get details of a specific host by ID."""
    try:
        return await service.get_host(host_id)
    except HostNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/hosts/{host_id}/refresh",
    response_model=HostRefreshResponse,
    summary="Refresh host status",
    description="Trigger a health check refresh for a specific host.",
)
async def refresh_host(
    host_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MonitoringService, Depends(get_service)],
) -> HostRefreshResponse:
    """Trigger a refresh/ping for a specific host."""
    try:
        host = await service.refresh_host(host_id)

        logger.info(
            "host_refresh_triggered",
            host_id=host_id,
            user_id=str(current_user.id),
            new_status=host.status.value,
        )

        return HostRefreshResponse(
            host=host,
            message=f"Host {host.name} refreshed successfully",
        )

    except HostNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/hosts/{host_id}/services/{service_name}/check",
    response_model=ServiceCheckResponse,
    summary="Check service on host",
    description="Trigger a health check for a specific service on a host.",
)
async def check_service(
    host_id: str,
    service_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    monitoring_service: Annotated[MonitoringService, Depends(get_service)],
) -> ServiceCheckResponse:
    """Trigger a check for a specific service on a host."""
    try:
        checked_service = await monitoring_service.check_service(host_id, service_name)

        logger.info(
            "service_check_triggered",
            host_id=host_id,
            service_name=service_name,
            user_id=str(current_user.id),
            new_status=checked_service.status.value,
        )

        return ServiceCheckResponse(
            service=checked_service,
            hostId=host_id,
            message=f"Service {service_name} check completed",
        )

    except HostNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# === Admin Endpoints ===

@router.post(
    "/refresh",
    response_model=MonitoringHierarchyResponse,
    summary="Refresh entire hierarchy",
    description="Force a refresh of the entire monitoring hierarchy. Admin only.",
)
async def refresh_hierarchy(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MonitoringService, Depends(get_service)],
) -> MonitoringHierarchyResponse:
    """Force refresh the entire monitoring hierarchy."""
    # In production, add admin role check
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")

    logger.info(
        "hierarchy_refresh_triggered",
        user_id=str(current_user.id),
    )

    # Invalidate cache and fetch fresh data
    service._invalidate_cache()
    return await service.get_hierarchy()
