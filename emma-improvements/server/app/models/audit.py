"""Audit log model for tracking all system events."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditAction(str, Enum):
    """Audit action types."""
    # Auth events
    LOGIN = "auth.login"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    REGISTER = "auth.register"
    PASSWORD_CHANGE = "auth.password_change"
    PASSWORD_RESET = "auth.password_reset"
    TOKEN_REFRESH = "auth.token_refresh"
    
    # User management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_DEACTIVATE = "user.deactivate"
    USER_ACTIVATE = "user.activate"
    SESSION_REVOKE = "user.session_revoke"
    
    # Service management
    SERVICE_CREATE = "service.create"
    SERVICE_UPDATE = "service.update"
    SERVICE_DELETE = "service.delete"
    SERVICE_TOGGLE = "service.toggle"
    SERVICE_CHECK = "service.check"
    
    # Container management
    CONTAINER_START = "container.start"
    CONTAINER_STOP = "container.stop"
    CONTAINER_RESTART = "container.restart"
    CONTAINER_REMOVE = "container.remove"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    CONFIG_CHANGE = "system.config_change"


class AuditLog(Base):
    """Audit log entry for tracking system events."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Event details
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), index=True)
    
    # Actor
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    user_email: Mapped[str | None] = mapped_column(String(255))
    
    # Context
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    request_id: Mapped[str | None] = mapped_column(String(36))
    
    # Details
    description: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    
    # Status
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    
    __table_args__ = (
        Index("ix_audit_logs_created_at_desc", created_at.desc()),
        Index("ix_audit_logs_user_action", "user_id", "action"),
    )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": str(self.user_id) if self.user_id else None,
            "user_email": self.user_email,
            "ip_address": self.ip_address,
            "description": self.description,
            "details": self.details,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }
