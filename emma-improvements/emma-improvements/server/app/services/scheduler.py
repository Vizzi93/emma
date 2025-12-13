"""Background scheduler for periodic health checks."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.service import Service, ServiceStatus
from app.services.service_manager import ServiceManager

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


class HealthCheckScheduler:
    """
    Background scheduler that runs health checks for all active services.
    
    Uses asyncio to run checks concurrently while respecting individual
    service intervals.
    """

    def __init__(
        self,
        max_concurrent_checks: int = 50,
        check_interval: float = 10.0,
    ) -> None:
        """
        Initialize scheduler.
        
        Args:
            max_concurrent_checks: Maximum number of concurrent health checks
            check_interval: How often to scan for services needing checks (seconds)
        """
        self._max_concurrent = max_concurrent_checks
        self._check_interval = check_interval
        self._semaphore = asyncio.Semaphore(max_concurrent_checks)
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            logger.warning("scheduler_already_running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "scheduler_started",
            max_concurrent=self._max_concurrent,
            check_interval=self._check_interval,
        )

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if not self._running:
            return

        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("scheduler_stopped")

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_services()
            except Exception as e:
                logger.exception("scheduler_error", error=str(e))

            await asyncio.sleep(self._check_interval)

    async def _check_services(self) -> None:
        """Find and check all services due for a health check."""
        async with AsyncSessionLocal() as session:
            services = await self._get_services_due(session)

            if not services:
                return

            logger.debug("services_due_for_check", count=len(services))

            # Run checks concurrently
            tasks = [
                self._run_check(service.id)
                for service in services
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _get_services_due(self, session: AsyncSession) -> list[Service]:
        """Get all services that are due for a health check."""
        now = datetime.now(timezone.utc)

        # Service is due if:
        # 1. Never checked (last_check_at is NULL), OR
        # 2. Last check was more than interval_seconds ago
        query = select(Service).where(
            and_(
                Service.is_active == True,
                Service.status != ServiceStatus.PAUSED.value,
                or_(
                    Service.last_check_at.is_(None),
                    Service.last_check_at < now - timedelta(seconds=1),  # Will be filtered in Python
                ),
            )
        )

        result = await session.scalars(query)
        services = list(result.all())

        # Filter by individual intervals
        due_services = []
        for service in services:
            if service.last_check_at is None:
                due_services.append(service)
            else:
                next_check = service.last_check_at + timedelta(seconds=service.interval_seconds)
                if now >= next_check:
                    due_services.append(service)

        return due_services

    async def _run_check(self, service_id) -> None:
        """Run a single health check with concurrency limiting."""
        async with self._semaphore:
            async with AsyncSessionLocal() as session:
                try:
                    manager = ServiceManager(session)
                    service = await session.get(Service, service_id)
                    
                    if service and service.is_active:
                        await manager.execute_check(service)
                        
                except Exception as e:
                    logger.exception(
                        "check_execution_error",
                        service_id=str(service_id),
                        error=str(e),
                    )

    async def run_check_now(self, service_id) -> None:
        """Manually trigger a health check for a specific service."""
        await self._run_check(service_id)
        logger.info("manual_check_triggered", service_id=str(service_id))


# Global scheduler instance
_scheduler: HealthCheckScheduler | None = None


def get_scheduler() -> HealthCheckScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = HealthCheckScheduler()
    return _scheduler


async def start_scheduler() -> None:
    """Start the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler() -> None:
    """Stop the global scheduler."""
    global _scheduler
    if _scheduler:
        await _scheduler.stop()
        _scheduler = None
