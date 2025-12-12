"""Audit context for request tracking."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from uuid import UUID

# Context variables for audit tracking
_audit_context: ContextVar[dict[str, Any]] = ContextVar("audit_context", default={})


@dataclass
class AuditContext:
    """Audit context for current request."""
    
    user_id: UUID | None = None
    user_email: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None


def set_audit_context(
    user_id: UUID | None = None,
    user_email: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> None:
    """Set audit context for current request."""
    _audit_context.set({
        "user_id": user_id,
        "user_email": user_email,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "request_id": request_id,
    })


def get_audit_context() -> dict[str, Any]:
    """Get current audit context."""
    return _audit_context.get()


def clear_audit_context() -> None:
    """Clear audit context."""
    _audit_context.set({})
