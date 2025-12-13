"""Service monitoring API routes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_dependency, require_operator
from app.models.user import User
from app.schemas.services import (
    CheckResultResponse,
    CreateServiceRequest,
    DashboardStatsResponse,
    ServiceListResponse,
    ServiceResponse,
    ServiceUptimeResponse,
    ServiceWithHistoryResponse,
    UpdateServiceRequest,
    UptimeDataPoint,
)
from app.services.scheduler import get_scheduler
from app.services.service_manager import ServiceError, ServiceManager, ServiceNotFoundError

router = APIRouter(prefix="/services", tags=["services"])
logger = structlog.get_logger(__name__)


# === List & Dashboard ===

@router.get(
    "",
    response_model=ServiceListResponse,
    summary="List all services",
)
async def list_services(
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    current_user: Annotated[User, Depends(get_current_user)],
    is_active: bool | None = Query(None),
    status: str | None = Query(None, pattern="^(healthy|degraded|unhealthy|unknown|paused)$"),
    type: str | None = Query(None, pattern="^(http|https|tcp|ssl|dns|ping)$"),
    group_name: str | None = Query(None),
) -> ServiceListResponse:
    """Get all monitored services with optional filters."""
    manager = ServiceManager(session)
    services = await manager.list_services(
        is_active=is_active,
        status=status,
        type=type,
        group_name=group_name,
    )
    return ServiceListResponse(
        items=[ServiceResponse.model_validate(s) for s in services],
        total=len(services),
    )


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get dashboard statistics",
)
async def get_dashboard_stats(
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardStatsResponse:
    """Get aggregated statistics for the dashboard."""
    manager = ServiceManager(session)
    stats = await manager.get_dashboard_stats()
    return DashboardStatsResponse(**stats)


# === CRUD Operations ===

@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service",
)
async def create_service(
    request: CreateServiceRequest,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    current_user: Annotated[User, Depends(require_operator)],
) -> ServiceResponse:
    """Create a new monitored service."""
    manager = ServiceManager(session)
    
    try:
        service = await manager.create_service(**request.model_dump())
        return ServiceResponse.model_validate(service)
    except ServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{service_id}",
    response_model=ServiceWithHistoryResponse,
    summary="Get service details",
)
async def get_service(
    service_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    current_user: Annotated[User, Depends(get_current_user)],
    include_history: bool = Query(True),
    history_limit: int = Query(20, ge=1, le=100),
) -> ServiceWithHistoryResponse:
    """Get service details with optional check history."""
    manager = ServiceManager(session)
    
    try:
        service = await manager.get_service(service_id)
        
        recent_checks = []
        if include_history:
            checks = await manager.get_check_history(service_id, limit=history_limit)
            recent_checks = [CheckResultResponse.model_validate(c) for c in checks]
        
        response = ServiceWithHistoryResponse.model_validate(service)
        response.recent_checks = recent_checks
        return response
        
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Update service",
)
async def update_service(
    service_id: UUID,
    request: UpdateServiceRequest,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    current_user: Annotated[User, Depends(require_operator)],
) -> ServiceResponse:
    """Update service configuration."""
    manager = ServiceManager(session)
    
    try:
        service = await manager.update_service(
            service_id,
            **request.model_dump(exclude_unset=True),
        )
        return ServiceResponse.model_validate(service)
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete service",
)
async def delete_service(
    service_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    current_user: Annotated[User, Depends(require_operator)],
) -> None:
    """Delete a service and its check history."""
    manager = ServiceManager(session)
    
    try:
        await manager.delete_service(service_id)
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# === Service Actions ===

@router.post(
    "/{service_id}/toggle",
    response_model=ServiceResponse,
    summary="Enable/disable service",
)
async def toggle_service(
    service_id: UUID,
    is_active: bool = Query(...),
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    current_user: Annotated[User, Depends(require_operator)],
) -> ServiceResponse:
    """Enable or disable monitoring for a service."""
    manager = ServiceManager(session)
    
    try:
        service = await manager.toggle_service(service_id, is_active)
        return ServiceResponse.model_validate(service)
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{service_id}/check",
    response_model=CheckResultResponse,
    summary="Run check now",
)
async def run_check_now(
    service_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    current_user: Annotated[User, Depends(require_operator)],
) -> CheckResultResponse:
    """Manually trigger a health check for a service."""
    manager = ServiceManager(session)
    
    try:
        service = await manager.get_service(service_id)
        if not service.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot check inactive service",
            )
        
        result = await manager.execute_check(service)
        return CheckResultResponse.model_validate(result)
        
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# === Check History ===

@router.get(
    "/{service_id}/history",
    response_model=list[CheckResultResponse],
    summary="Get check history",
)
async def get_check_history(
    service_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(100, ge=1, le=1000),
    hours: int = Query(24, ge=1, le=168),
) -> list[CheckResultResponse]:
    """Get check history for a service."""
    manager = ServiceManager(session)
    
    try:
        await manager.get_service(service_id)  # Verify exists
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        checks = await manager.get_check_history(service_id, limit=limit, since=since)
        return [CheckResultResponse.model_validate(c) for c in checks]
        
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{service_id}/uptime",
    response_model=ServiceUptimeResponse,
    summary="Get uptime data for charts",
)
async def get_uptime_data(
    service_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    current_user: Annotated[User, Depends(get_current_user)],
    hours: int = Query(24, ge=1, le=168),
) -> ServiceUptimeResponse:
    """Get uptime data points for charting."""
    manager = ServiceManager(session)
    
    try:
        service = await manager.get_service(service_id)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        checks = await manager.get_check_history(service_id, limit=1000, since=since)
        
        data_points = [
            UptimeDataPoint(
                timestamp=c.checked_at,
                is_healthy=c.is_healthy,
                response_time_ms=c.response_time_ms,
            )
            for c in reversed(checks)  # Chronological order
        ]
        
        return ServiceUptimeResponse(
            service_id=service.id,
            service_name=service.name,
            uptime_percentage=service.uptime_percentage,
            data_points=data_points,
        )
        
    except ServiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
