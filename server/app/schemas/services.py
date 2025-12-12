"""Pydantic schemas for service monitoring."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# === Request Schemas ===

class CreateServiceRequest(BaseModel):
    """Create a new monitored service."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    type: str = Field(..., pattern="^(http|https|tcp|ssl|dns|ping)$")
    target: str = Field(..., min_length=1, max_length=512)
    config: dict[str, Any] = Field(default_factory=dict)
    interval_seconds: int = Field(default=60, ge=10, le=3600)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    tags: list[str] = Field(default_factory=list)
    group_name: str | None = Field(None, max_length=128)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Ensure tags are valid."""
        return [tag.strip().lower() for tag in v if tag.strip()]


class UpdateServiceRequest(BaseModel):
    """Update service configuration."""
    
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    target: str | None = Field(None, min_length=1, max_length=512)
    config: dict[str, Any] | None = None
    interval_seconds: int | None = Field(None, ge=10, le=3600)
    timeout_seconds: int | None = Field(None, ge=5, le=120)
    tags: list[str] | None = None
    group_name: str | None = None
    is_active: bool | None = None


class ServiceFilterParams(BaseModel):
    """Query parameters for filtering services."""
    
    is_active: bool | None = None
    status: str | None = Field(None, pattern="^(healthy|degraded|unhealthy|unknown|paused)$")
    type: str | None = Field(None, pattern="^(http|https|tcp|ssl|dns|ping)$")
    group_name: str | None = None
    tags: list[str] | None = None


# === Response Schemas ===

class CheckResultResponse(BaseModel):
    """Individual check result."""
    
    id: UUID
    service_id: UUID
    is_healthy: bool
    status_code: int | None
    response_time_ms: float | None
    message: str | None
    error: str | None
    metadata: dict[str, Any]
    checked_at: datetime

    class Config:
        from_attributes = True


class ServiceResponse(BaseModel):
    """Service details response."""
    
    id: UUID
    name: str
    description: str | None
    type: str
    target: str
    config: dict[str, Any]
    interval_seconds: int
    timeout_seconds: int
    status: str
    is_active: bool
    last_check_at: datetime | None
    last_response_time_ms: float | None
    uptime_percentage: float
    consecutive_failures: int
    tags: list[str]
    group_name: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServiceWithHistoryResponse(ServiceResponse):
    """Service with recent check history."""
    
    recent_checks: list[CheckResultResponse] = Field(default_factory=list)


class ServiceListResponse(BaseModel):
    """Paginated list of services."""
    
    items: list[ServiceResponse]
    total: int


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics."""
    
    total_services: int
    status_counts: dict[str, int]
    services_due: int
    avg_response_time_ms: float | None


class ServiceStatusSummary(BaseModel):
    """Quick status summary for a service."""
    
    id: UUID
    name: str
    status: str
    last_check_at: datetime | None
    last_response_time_ms: float | None
    uptime_percentage: float


class UptimeDataPoint(BaseModel):
    """Single uptime data point for charts."""
    
    timestamp: datetime
    is_healthy: bool
    response_time_ms: float | None


class ServiceUptimeResponse(BaseModel):
    """Uptime history for charts."""
    
    service_id: UUID
    service_name: str
    uptime_percentage: float
    data_points: list[UptimeDataPoint]
