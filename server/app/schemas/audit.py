"""Pydantic schemas for audit logs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    id: UUID
    action: str
    resource_type: str | None
    resource_id: str | None
    user_id: UUID | None
    user_email: str | None
    ip_address: str | None
    description: str | None
    details: dict[str, Any] | None
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None
    success: bool
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs."""
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class AuditStatsResponse(BaseModel):
    """Audit statistics."""
    total_events: int
    successful: int
    failed: int
    by_action: dict[str, int]
    unique_users: int
    period_days: int


class AuditFilterParams(BaseModel):
    """Query parameters for filtering audit logs."""
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    user_id: UUID | None = None
    success: bool | None = None
    since: datetime | None = None
    until: datetime | None = None
    search: str | None = Field(None, max_length=100)
    limit: int = Field(100, ge=1, le=500)
    offset: int = Field(0, ge=0)
