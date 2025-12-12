"""Service monitoring ORM models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class ServiceType(str, Enum):
    """Supported service check types."""
    
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    SSL = "ssl"
    DNS = "dns"
    DOCKER = "docker"
    PING = "ping"


class ServiceStatus(str, Enum):
    """Service health status."""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    PAUSED = "paused"


class Service(Base):
    """Monitored service definition."""

    __tablename__ = "services"
    __table_args__ = (
        Index("ix_services_status", "status"),
        Index("ix_services_type", "type"),
        Index("ix_services_is_active", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    
    # Check configuration
    target: Mapped[str] = mapped_column(String(512), nullable=False)  # URL, host:port, domain
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Scheduling
    interval_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(32), default=ServiceStatus.UNKNOWN.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metrics (cached for quick access)
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    uptime_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Categorization
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    group_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships
    check_results: Mapped[list["CheckResult"]] = relationship(
        "CheckResult",
        back_populates="service",
        cascade="all, delete-orphan",
        order_by="desc(CheckResult.checked_at)",
    )

    def __repr__(self) -> str:
        return f"<Service {self.name} ({self.type})>"


class CheckResult(Base):
    """Individual check result record."""

    __tablename__ = "check_results"
    __table_args__ = (
        Index("ix_check_results_service_checked", "service_id", "checked_at"),
        Index("ix_check_results_checked_at", "checked_at"),
        Index("ix_check_results_is_healthy", "is_healthy"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    service_id: Mapped[UUID] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    
    # Result
    is_healthy: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)  # HTTP status
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Details
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    check_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamp
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    # Relationships
    service: Mapped["Service"] = relationship("Service", back_populates="check_results")

    def __repr__(self) -> str:
        status = "✓" if self.is_healthy else "✗"
        return f"<CheckResult {status} {self.service_id} @ {self.checked_at}>"


class SSLCertificateInfo(Base):
    """Cached SSL certificate information."""

    __tablename__ = "ssl_certificates"
    __table_args__ = (
        Index("ix_ssl_certificates_expires_at", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    service_id: Mapped[UUID] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    
    # Certificate info
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    issuer: Mapped[str] = mapped_column(String(512), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(128), nullable=False)
    
    # Validity
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    days_until_expiry: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Timestamps
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    @property
    def is_expiring_soon(self) -> bool:
        """Check if certificate expires within 30 days."""
        return self.days_until_expiry <= 30

    @property
    def is_expired(self) -> bool:
        """Check if certificate is expired."""
        return self.days_until_expiry <= 0
