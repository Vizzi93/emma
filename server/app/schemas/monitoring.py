"""Pydantic schemas for monitoring hierarchy API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# === Enums ===

class HostStatus(str, Enum):
    """Host connection status."""
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"
    UNKNOWN = "unknown"


class ServiceStatus(str, Enum):
    """Service running status."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class AggregatedStatus(str, Enum):
    """Aggregated health status for regions/verfahren."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


# === Host-Level Schemas ===

class HostServiceSchema(BaseModel):
    """Service running on a host."""
    name: str = Field(..., description="Service name (e.g., nginx, postgresql)")
    port: int = Field(..., ge=1, le=65535, description="Service port")
    status: ServiceStatus = Field(..., description="Service status")

    model_config = {"from_attributes": True}


class HostMetricsSchema(BaseModel):
    """Host resource metrics."""
    cpu: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    memory: float = Field(..., ge=0, le=100, description="Memory usage percentage")
    disk: float = Field(..., ge=0, le=100, description="Disk usage percentage")
    uptime: int = Field(..., ge=0, description="Uptime in seconds")

    model_config = {"from_attributes": True}


class HostSchema(BaseModel):
    """Host/server in the monitoring hierarchy."""
    id: str = Field(..., description="Unique host identifier")
    name: str = Field(..., description="Host display name")
    ip: str = Field(..., description="IP address")
    status: HostStatus = Field(..., description="Connection status")
    last_check: datetime = Field(..., alias="lastCheck", description="Last health check timestamp")
    services: list[HostServiceSchema] = Field(default_factory=list, description="Services on this host")
    metrics: HostMetricsSchema | None = Field(None, description="Resource metrics")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# === Verfahren-Level Schemas ===

class VerfahrenSchema(BaseModel):
    """Verfahren (procedure/application group) containing hosts."""
    id: str = Field(..., description="Unique verfahren identifier")
    code: str = Field(..., description="Verfahren code (e.g., Mastu_NL001)")
    name: str = Field(..., description="Display name")
    description: str | None = Field(None, description="Optional description")
    hosts: list[HostSchema] = Field(default_factory=list, description="Hosts in this verfahren")
    aggregated_status: AggregatedStatus = Field(
        ...,
        alias="aggregatedStatus",
        description="Aggregated health status"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# === Region-Level Schemas ===

class RegionSchema(BaseModel):
    """Geographic region containing verfahren."""
    id: str = Field(..., description="Unique region identifier")
    name: str = Field(..., description="Region name (e.g., Bremerhaven)")
    verfahren: list[VerfahrenSchema] = Field(default_factory=list, description="Verfahren in this region")
    aggregated_status: AggregatedStatus = Field(
        ...,
        alias="aggregatedStatus",
        description="Aggregated health status"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# === API Response Schemas ===

class MonitoringHierarchyResponse(BaseModel):
    """Full monitoring hierarchy response."""
    regions: list[RegionSchema] = Field(..., description="All regions")
    last_updated: datetime = Field(..., alias="lastUpdated", description="Last data refresh timestamp")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class MonitoringStatsResponse(BaseModel):
    """Aggregated monitoring statistics."""
    total_regions: int = Field(..., alias="totalRegions")
    total_verfahren: int = Field(..., alias="totalVerfahren")
    total_hosts: int = Field(..., alias="totalHosts")
    healthy_hosts: int = Field(..., alias="healthyHosts")
    warning_hosts: int = Field(..., alias="warningHosts")
    offline_hosts: int = Field(..., alias="offlineHosts")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class HostRefreshResponse(BaseModel):
    """Response after refreshing a host."""
    host: HostSchema
    message: str = Field(default="Host refreshed successfully")


class ServiceCheckResponse(BaseModel):
    """Response after checking a service."""
    service: HostServiceSchema
    host_id: str = Field(..., alias="hostId")
    message: str = Field(default="Service check completed")

    model_config = {"populate_by_name": True}


# === Query Parameters ===

class HierarchyFilters(BaseModel):
    """Filter parameters for hierarchy endpoint."""
    region: str | None = Field(None, description="Filter by region name (case-insensitive)")
    status: AggregatedStatus | None = Field(None, description="Filter by aggregated status")
    include_offline: bool = Field(True, description="Include offline hosts in response")


class HostFilters(BaseModel):
    """Filter parameters for hosts endpoint."""
    status: HostStatus | None = Field(None, description="Filter by host status")
    region_id: str | None = Field(None, alias="region_id", description="Filter by region ID")
    verfahren_id: str | None = Field(None, alias="verfahren_id", description="Filter by verfahren ID")


class HostListResponse(BaseModel):
    """Paginated host list response."""
    items: list[HostSchema]
    total: int
