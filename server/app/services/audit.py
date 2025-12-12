"""Audit logging service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditLog

logger = structlog.get_logger(__name__)


class AuditService:
    """Service for audit logging and querying."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        action: str | AuditAction,
        *,
        resource_type: str | None = None,
        resource_id: str | None = None,
        user_id: UUID | None = None,
        user_email: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        description: str | None = None,
        details: dict[str, Any] | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        action_str = action.value if isinstance(action, AuditAction) else action
        
        entry = AuditLog(
            action=action_str,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            description=description,
            details=details,
            old_values=old_values,
            new_values=new_values,
            success=success,
            error_message=error_message,
        )
        
        self._session.add(entry)
        await self._session.commit()
        
        logger.info(
            "audit_logged",
            action=action_str,
            resource_type=resource_type,
            resource_id=resource_id,
            user_email=user_email,
            success=success,
        )
        
        return entry

    async def query(
        self,
        *,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        user_id: UUID | None = None,
        success: bool | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """Query audit logs with filters."""
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))
        
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
            count_query = count_query.where(AuditLog.resource_type == resource_type)
        
        if resource_id:
            query = query.where(AuditLog.resource_id == resource_id)
            count_query = count_query.where(AuditLog.resource_id == resource_id)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)
        
        if success is not None:
            query = query.where(AuditLog.success == success)
            count_query = count_query.where(AuditLog.success == success)
        
        if since:
            query = query.where(AuditLog.created_at >= since)
            count_query = count_query.where(AuditLog.created_at >= since)
        
        if until:
            query = query.where(AuditLog.created_at <= until)
            count_query = count_query.where(AuditLog.created_at <= until)
        
        if search:
            pattern = f"%{search}%"
            query = query.where(
                (AuditLog.description.ilike(pattern)) |
                (AuditLog.user_email.ilike(pattern)) |
                (AuditLog.resource_id.ilike(pattern))
            )
            count_query = count_query.where(
                (AuditLog.description.ilike(pattern)) |
                (AuditLog.user_email.ilike(pattern)) |
                (AuditLog.resource_id.ilike(pattern))
            )
        
        total = await self._session.scalar(count_query) or 0
        
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.scalars(query)
        
        return list(result.all()), total

    async def get_user_activity(
        self,
        user_id: UUID,
        days: int = 30,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get recent activity for a specific user."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = select(AuditLog).where(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= since,
        ).order_by(AuditLog.created_at.desc()).limit(limit)
        
        result = await self._session.scalars(query)
        return list(result.all())

    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get audit history for a specific resource."""
        query = select(AuditLog).where(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        ).order_by(AuditLog.created_at.desc()).limit(limit)
        
        result = await self._session.scalars(query)
        return list(result.all())

    async def get_stats(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Get audit statistics."""
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Total count
        total_query = select(func.count(AuditLog.id)).where(AuditLog.created_at >= since)
        total = await self._session.scalar(total_query) or 0
        
        # Success/failure
        success_query = select(func.count(AuditLog.id)).where(
            AuditLog.created_at >= since, AuditLog.success == True
        )
        success = await self._session.scalar(success_query) or 0
        
        # By action
        action_query = select(
            AuditLog.action, func.count(AuditLog.id)
        ).where(AuditLog.created_at >= since).group_by(AuditLog.action)
        action_result = await self._session.execute(action_query)
        by_action = {row[0]: row[1] for row in action_result.all()}
        
        # Unique users
        users_query = select(func.count(func.distinct(AuditLog.user_id))).where(
            AuditLog.created_at >= since, AuditLog.user_id.isnot(None)
        )
        unique_users = await self._session.scalar(users_query) or 0
        
        return {
            "total_events": total,
            "successful": success,
            "failed": total - success,
            "by_action": by_action,
            "unique_users": unique_users,
            "period_days": (datetime.now(timezone.utc) - since).days,
        }

    async def cleanup(self, retention_days: int = 90) -> int:
        """Delete audit logs older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        query = delete(AuditLog).where(AuditLog.created_at < cutoff)
        result = await self._session.execute(query)
        await self._session.commit()
        
        count = result.rowcount
        if count > 0:
            logger.info("audit_cleanup", deleted_count=count, retention_days=retention_days)
        
        return count


# Context-aware audit helper
_current_request_context: dict[str, Any] = {}


def set_audit_context(
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> None:
    """Set context for audit logging (call from middleware)."""
    global _current_request_context
    _current_request_context = {
        "ip_address": ip_address,
        "user_agent": user_agent,
        "request_id": request_id,
    }


def get_audit_context() -> dict[str, Any]:
    """Get current audit context."""
    return _current_request_context.copy()


def clear_audit_context() -> None:
    """Clear audit context."""
    global _current_request_context
    _current_request_context = {}
