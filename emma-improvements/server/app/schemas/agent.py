"""Pydantic schemas for Agent API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentModuleConfig(BaseModel):
    """Configuration for an agent module."""
    enabled: bool = True
    interval_seconds: int | None = None
    settings: dict[str, Any] | None = None


class AgentBase(BaseModel):
    """Base schema for Agent."""
    hostname: str = Field(..., min_length=1, max_length=255)
    os: str = Field(default="linux", max_length=50)
    architecture: str = Field(default="x86_64", max_length=50)
    sampling_interval: int = Field(default=30, ge=5, le=3600)
    tags: list[str] = Field(default_factory=list)
    modules: dict[str, AgentModuleConfig] = Field(default_factory=dict)


class AgentCreate(AgentBase):
    """Schema for creating an Agent."""
    host_id: str = Field(..., min_length=1, max_length=255)


class AgentUpdate(BaseModel):
    """Schema for updating an Agent."""
    hostname: str | None = Field(None, min_length=1, max_length=255)
    sampling_interval: int | None = Field(None, ge=5, le=3600)
    tags: list[str] | None = None
    modules: dict[str, AgentModuleConfig] | None = None
    is_active: bool | None = None


class AgentResponse(AgentBase):
    """Schema for Agent response."""
    id: UUID
    host_id: str
    status: str = "unknown"
    ip_address: str | None = None
    version: str | None = None
    is_active: bool = True
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    """Schema for paginated agent list."""
    items: list[AgentResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


class EnrollmentTokenCreate(BaseModel):
    """Schema for creating an enrollment token."""
    description: str | None = Field(None, max_length=255)
    ttl_hours: int = Field(default=24, ge=1, le=168)


class EnrollmentTokenResponse(BaseModel):
    """Schema for enrollment token response."""
    id: UUID
    token: str
    description: str | None
    expires_at: datetime
    is_used: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProvisionAgentRequest(BaseModel):
    """Schema for agent provisioning request."""
    enrollment_token: str
    host_id: str
    hostname: str
    os: str = "linux"
    architecture: str = "x86_64"


class ProvisionAgentResponse(BaseModel):
    """Schema for agent provisioning response."""
    agent_id: UUID
    access_token: str
    expires_at: datetime
