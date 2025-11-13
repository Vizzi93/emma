"""Pydantic schemas for agent provisioning."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentModuleConfig(BaseModel):
    """Configuration for an individual agent module."""

    enabled: bool = True
    interval_seconds: int | None = Field(default=None, ge=5, le=3600)
    settings: dict[str, Any] = Field(default_factory=dict)


class ProvisionAgentRequest(BaseModel):
    """Request payload for provisioning an agent."""

    host_id: str = Field(..., min_length=1, max_length=128)
    hostname: str = Field(..., min_length=1, max_length=255)
    os: str = Field(..., min_length=1, max_length=64)
    architecture: str = Field(..., min_length=1, max_length=64)
    sampling_interval: int = Field(..., ge=5, le=3600)
    tags: list[str] = Field(default_factory=list)
    modules: dict[str, AgentModuleConfig] = Field(default_factory=dict)
    checks: dict[str, Any] | None = None


class ProvisionAgentResponse(BaseModel):
    """Response returned after provisioning an agent."""

    agent_id: UUID
    token: str
    expires_at: datetime


class BootstrapResponse(BaseModel):
    """Response payload for agent bootstrap."""

    script: str
    download_url: str
    config_jwt: str
    expires_at: datetime
