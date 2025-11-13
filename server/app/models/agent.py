"""Agent ORM models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


class Agent(Base):
    """Represents a monitored agent installation."""

    __tablename__ = "agents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    host_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    os: Mapped[str] = mapped_column(String(64), nullable=False)
    architecture: Mapped[str] = mapped_column(String(64), nullable=False)
    sampling_interval: Mapped[int] = mapped_column(nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    modules: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    checks: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    enrollment_tokens: Mapped[list["EnrollmentToken"]] = relationship(
        "EnrollmentToken", back_populates="agent", cascade="all, delete-orphan"
    )
    download_tokens: Mapped[list["AgentDownloadToken"]] = relationship(
        "AgentDownloadToken", back_populates="agent", cascade="all, delete-orphan"
    )


class EnrollmentToken(Base):
    """Enrollment token for agent bootstrap."""

    __tablename__ = "enrollment_tokens"
    __table_args__ = (UniqueConstraint("jti", name="uq_enrollment_token_jti"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    jti: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id"), nullable=False)
    host_id: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="enrollment_tokens")


class AgentDownloadToken(Base):
    """Short lived download tokens for agent binaries."""

    __tablename__ = "agent_download_tokens"
    __table_args__ = (
        UniqueConstraint("token", name="uq_agent_download_token_token"),
        Index("ix_agent_download_token_expires_at", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="download_tokens")


class AuditLog(Base):
    """Audit log entries for provisioning events."""

    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_created_at", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
