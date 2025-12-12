"""Agent ORM models for agent management."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class AgentStatus(str, Enum):
    """Agent connection status."""
    ONLINE = "online"
    OFFLINE = "offline"
    PENDING = "pending"
    ERROR = "error"


class Agent(Base):
    """Remote monitoring agent."""

    __tablename__ = "agents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Agent metadata
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    os_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(32), default=AgentStatus.PENDING.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Configuration
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Timestamps
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Agent {self.name}>"


class EnrollmentToken(Base):
    """Token for agent enrollment."""

    __tablename__ = "enrollment_tokens"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # Metadata
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Status
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_by_agent_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Timestamps
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired and not self.is_used


class AgentDownloadToken(Base):
    """Token for agent binary download."""

    __tablename__ = "agent_download_tokens"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # Target
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # linux, windows, darwin
    architecture: Mapped[str] = mapped_column(String(50), nullable=False)  # amd64, arm64

    # Timestamps
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) >= self.expires_at
