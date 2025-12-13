"""Audit logging service."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditLog

logger = structlog.get_logger(__name__)


class AuditService:
    """Service for audit logging operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        action: AuditAction | str,
        user_id: UUID | None = None,
        user_email: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        description: str | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        
        entry = AuditLog(
            action=action.value if isinstance(action, AuditAction) else action,
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        
        self._session.add(entry)
        await self._session.commit()
        
        logger.info(
            "audit_logged",
            action=entry.action,
            user_id=str(user_id) if user_id else None,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        
        return entry

    async def list_logs(
        self,
        user_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """List audit logs with filters."""
        
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))
        
        conditions = []
        
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)
        if search:
            pattern = f"%{search}%"
            conditions.append(
                (AuditLog.description.ilike(pattern)) |
                (AuditLog.user_email.ilike(pattern)) |
                (AuditLog.resource_id.ilike(pattern))
            )
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        total = await self._session.scalar(count_query) or 0
        
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.scalars(query)
        
        return list(result.all()), total

    async def get_log(self, log_id: UUID) -> AuditLog | None:
        """Get a specific audit log entry."""
        return await self._session.get(AuditLog, log_id)

    async def get_user_activity(
        self,
        user_id: UUID,
        days: int = 30,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get recent activity for a user."""
        
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
        days: int = 7,
    ) -> dict[str, Any]:
        """Get audit statistics."""
        
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total count
        total_query = select(func.count(AuditLog.id)).where(AuditLog.created_at >= since)
        total = await self._session.scalar(total_query) or 0
        
        # By action
        action_query = select(
            AuditLog.action,
            func.count(AuditLog.id),
        ).where(AuditLog.created_at >= since).group_by(AuditLog.action)
        action_result = await self._session.execute(action_query)
        by_action = {row[0]: row[1] for row in action_result.all()}
        
        # By user
        user_query = select(
            AuditLog.user_email,
            func.count(AuditLog.id),
        ).where(
            AuditLog.created_at >= since,
            AuditLog.user_email.isnot(None),
        ).group_by(AuditLog.user_email).order_by(func.count(AuditLog.id).desc()).limit(10)
        user_result = await self._session.execute(user_query)
        by_user = {row[0]: row[1] for row in user_result.all()}
        
        # By day
        day_query = select(
            func.date_trunc('day', AuditLog.created_at).label('day'),
            func.count(AuditLog.id),
        ).where(AuditLog.created_at >= since).group_by('day').order_by('day')
        day_result = await self._session.execute(day_query)
        by_day = {row[0].isoformat(): row[1] for row in day_result.all()}
        
        return {
            "total": total,
            "by_action": by_action,
            "by_user": by_user,
            "by_day": by_day,
            "period_days": days,
        }

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """Delete audit logs older than specified days."""
        from sqlalchemy import delete
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        stmt = delete(AuditLog).where(AuditLog.created_at < cutoff)
        result = await self._session.execute(stmt)
        await self._session.commit()
        
        count = result.rowcount
        logger.info("audit_logs_cleaned", deleted=count, older_than_days=days)
        return count


# Helper function to create audit entries easily
async def audit_log(
    session: AsyncSession,
    action: AuditAction | str,
    **kwargs,
) -> AuditLog:
    """Convenience function to create audit log entry."""
    service = AuditService(session)
    return await service.log(action, **kwargs)
