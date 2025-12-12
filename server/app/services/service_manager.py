"""Service management and health check scheduling."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket import (
    EventType,
    broadcast_service_event,
    broadcast_check_result,
)
from app.models.service import CheckResult as CheckResultModel
from app.models.service import Service, ServiceStatus, ServiceType
from app.services.health_checks import CheckResult, get_checker

logger = structlog.get_logger(__name__)


class ServiceError(Exception):
    """Base service error."""
    pass


class ServiceNotFoundError(ServiceError):
    """Service not found."""
    pass


class ServiceManager:
    """Manage services and execute health checks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # === CRUD Operations ===

    async def create_service(
        self,
        name: str,
        type: str,
        target: str,
        description: str | None = None,
        config: dict[str, Any] | None = None,
        interval_seconds: int = 60,
        timeout_seconds: int = 30,
        tags: list[str] | None = None,
        group_name: str | None = None,
    ) -> Service:
        """Create a new monitored service."""
        
        # Validate type
        if type not in [t.value for t in ServiceType]:
            raise ServiceError(f"Invalid service type: {type}")

        service = Service(
            name=name,
            description=description,
            type=type,
            target=target,
            config=config or {},
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds,
            tags=tags or [],
            group_name=group_name,
            status=ServiceStatus.UNKNOWN.value,
        )

        self._session.add(service)
        await self._session.commit()
        await self._session.refresh(service)

        logger.info("service_created", service_id=str(service.id), name=name, type=type)
        
        # Broadcast WebSocket event
        await broadcast_service_event(
            EventType.SERVICE_CREATED,
            self._service_to_dict(service),
        )
        
        return service

    async def get_service(self, service_id: UUID) -> Service:
        """Get service by ID."""
        service = await self._session.get(Service, service_id)
        if service is None:
            raise ServiceNotFoundError(f"Service {service_id} not found")
        return service

    async def list_services(
        self,
        is_active: bool | None = None,
        status: str | None = None,
        type: str | None = None,
        group_name: str | None = None,
        tags: list[str] | None = None,
    ) -> list[Service]:
        """List services with optional filters."""
        query = select(Service)

        if is_active is not None:
            query = query.where(Service.is_active == is_active)
        if status:
            query = query.where(Service.status == status)
        if type:
            query = query.where(Service.type == type)
        if group_name:
            query = query.where(Service.group_name == group_name)
        if tags:
            # Filter services that have any of the specified tags
            for tag in tags:
                query = query.where(Service.tags.contains([tag]))

        query = query.order_by(Service.name)
        result = await self._session.scalars(query)
        return list(result.all())

    async def update_service(
        self,
        service_id: UUID,
        **updates: Any,
    ) -> Service:
        """Update service configuration."""
        service = await self.get_service(service_id)

        allowed_fields = {
            "name", "description", "target", "config", "interval_seconds",
            "timeout_seconds", "tags", "group_name", "is_active",
        }

        for key, value in updates.items():
            if key in allowed_fields and value is not None:
                setattr(service, key, value)

        await self._session.commit()
        await self._session.refresh(service)

        logger.info("service_updated", service_id=str(service_id))
        return service

    async def delete_service(self, service_id: UUID) -> None:
        """Delete a service and its check history."""
        service = await self.get_service(service_id)
        await self._session.delete(service)
        await self._session.commit()

        logger.info("service_deleted", service_id=str(service_id))

    async def toggle_service(self, service_id: UUID, is_active: bool) -> Service:
        """Enable or disable service monitoring."""
        service = await self.get_service(service_id)
        service.is_active = is_active
        service.status = ServiceStatus.PAUSED.value if not is_active else ServiceStatus.UNKNOWN.value
        
        await self._session.commit()
        await self._session.refresh(service)

        logger.info("service_toggled", service_id=str(service_id), is_active=is_active)
        return service

    # === Health Check Execution ===

    async def execute_check(self, service: Service) -> CheckResultModel:
        """Execute health check for a service and store result."""
        
        checker = get_checker(service.type, timeout=service.timeout_seconds)
        result = await checker.check(service.target, service.config)

        # Create check result record
        check_result = CheckResultModel(
            service_id=service.id,
            is_healthy=result.is_healthy,
            status_code=result.status_code,
            response_time_ms=result.response_time_ms,
            message=result.message,
            error=result.error,
            metadata=result.metadata or {},
        )
        self._session.add(check_result)

        # Update service status
        old_status = service.status
        await self._update_service_status(service, result)
        new_status = service.status

        await self._session.commit()

        logger.debug(
            "check_executed",
            service_id=str(service.id),
            is_healthy=result.is_healthy,
            response_time_ms=result.response_time_ms,
        )

        # Broadcast check result via WebSocket
        await broadcast_check_result(
            str(service.id),
            {
                "is_healthy": result.is_healthy,
                "status_code": result.status_code,
                "response_time_ms": result.response_time_ms,
                "message": result.message,
                "error": result.error,
                "checked_at": check_result.checked_at.isoformat(),
            },
        )

        # Broadcast status change if changed
        if old_status != new_status:
            await broadcast_service_event(
                EventType.SERVICE_STATUS_CHANGED,
                {
                    **self._service_to_dict(service),
                    "old_status": old_status,
                    "new_status": new_status,
                },
            )

        return check_result

    async def _update_service_status(
        self,
        service: Service,
        result: CheckResult,
    ) -> None:
        """Update service status based on check result."""
        
        service.last_check_at = datetime.now(timezone.utc)
        service.last_response_time_ms = result.response_time_ms

        if result.is_healthy:
            service.consecutive_failures = 0
            service.status = ServiceStatus.HEALTHY.value
        else:
            service.consecutive_failures += 1
            
            # Degraded after 1 failure, unhealthy after 3
            if service.consecutive_failures >= 3:
                service.status = ServiceStatus.UNHEALTHY.value
            else:
                service.status = ServiceStatus.DEGRADED.value

        # Recalculate uptime (last 24 hours)
        service.uptime_percentage = await self._calculate_uptime(service.id)

    async def _calculate_uptime(
        self,
        service_id: UUID,
        hours: int = 24,
    ) -> float:
        """Calculate uptime percentage for the given period."""
        
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = select(
            func.count(CheckResultModel.id).label("total"),
            func.sum(
                func.cast(CheckResultModel.is_healthy, Integer)
            ).label("healthy"),
        ).where(
            and_(
                CheckResultModel.service_id == service_id,
                CheckResultModel.checked_at >= since,
            )
        )

        result = await self._session.execute(query)
        row = result.one()

        total = row.total or 0
        healthy = row.healthy or 0

        if total == 0:
            return 0.0

        return round((healthy / total) * 100, 2)

    # === Check Results ===

    async def get_check_history(
        self,
        service_id: UUID,
        limit: int = 100,
        since: datetime | None = None,
    ) -> list[CheckResultModel]:
        """Get check history for a service."""
        
        query = select(CheckResultModel).where(
            CheckResultModel.service_id == service_id
        )

        if since:
            query = query.where(CheckResultModel.checked_at >= since)

        query = query.order_by(CheckResultModel.checked_at.desc()).limit(limit)
        
        result = await self._session.scalars(query)
        return list(result.all())

    async def cleanup_old_results(self, days: int = 30) -> int:
        """Delete check results older than specified days."""
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = delete(CheckResultModel).where(
            CheckResultModel.checked_at < cutoff
        )
        
        result = await self._session.execute(query)
        await self._session.commit()

        deleted = result.rowcount
        logger.info("check_results_cleaned", deleted_count=deleted, older_than_days=days)
        return deleted

    # === Dashboard Stats ===

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Get aggregated stats for dashboard."""
        
        # Count by status
        status_query = select(
            Service.status,
            func.count(Service.id),
        ).where(
            Service.is_active == True
        ).group_by(Service.status)

        status_result = await self._session.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result.all()}

        # Get services due for check
        now = datetime.now(timezone.utc)
        due_query = select(func.count(Service.id)).where(
            and_(
                Service.is_active == True,
                Service.last_check_at < now - timedelta(seconds=60),
            )
        )
        due_result = await self._session.scalar(due_query)

        # Average response time (last hour)
        hour_ago = now - timedelta(hours=1)
        avg_query = select(
            func.avg(CheckResultModel.response_time_ms)
        ).where(
            CheckResultModel.checked_at >= hour_ago
        )
        avg_response = await self._session.scalar(avg_query)

        return {
            "total_services": sum(status_counts.values()),
            "status_counts": status_counts,
            "services_due": due_result or 0,
            "avg_response_time_ms": round(avg_response, 2) if avg_response else None,
        }

    def _service_to_dict(self, service: Service) -> dict[str, Any]:
        """Convert service to dictionary for WebSocket broadcast."""
        return {
            "id": str(service.id),
            "name": service.name,
            "type": service.type,
            "target": service.target,
            "status": service.status,
            "is_active": service.is_active,
            "last_check_at": service.last_check_at.isoformat() if service.last_check_at else None,
            "last_response_time_ms": service.last_response_time_ms,
            "uptime_percentage": service.uptime_percentage,
            "consecutive_failures": service.consecutive_failures,
        }


# Need this import for the Integer cast
from sqlalchemy import Integer
