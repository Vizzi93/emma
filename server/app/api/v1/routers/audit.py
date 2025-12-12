"""Audit log API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_dependency, require_admin
from app.models.user import User
from app.schemas.audit import AuditLogListResponse, AuditLogResponse, AuditStatsResponse
from app.services.audit import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    days: int = Query(7, ge=1, le=90),
) -> AuditStatsResponse:
    """Get audit statistics (admin only)."""
    service = AuditService(session)
    from datetime import timedelta, timezone
    since = datetime.now(timezone.utc) - timedelta(days=days)
    stats = await service.get_stats(since=since)
    return AuditStatsResponse(**stats)


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    user_id: UUID | None = Query(None),
    success: bool | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    search: str | None = Query(None, max_length=100),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> AuditLogListResponse:
    """List audit logs with filters (admin only)."""
    service = AuditService(session)
    logs, total = await service.query(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        success=success,
        since=since,
        until=until,
        search=search,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/user/{user_id}", response_model=list[AuditLogResponse])
async def get_user_activity(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(50, ge=1, le=200),
) -> list[AuditLogResponse]:
    """Get activity for a specific user (admin only)."""
    service = AuditService(session)
    logs = await service.get_user_activity(user_id, days=days, limit=limit)
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/resource/{resource_type}/{resource_id}", response_model=list[AuditLogResponse])
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    limit: int = Query(50, ge=1, le=200),
) -> list[AuditLogResponse]:
    """Get audit history for a specific resource (admin only)."""
    service = AuditService(session)
    logs = await service.get_resource_history(resource_type, resource_id, limit=limit)
    return [AuditLogResponse.model_validate(log) for log in logs]
