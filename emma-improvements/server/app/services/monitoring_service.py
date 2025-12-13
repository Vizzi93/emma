"""Monitoring hierarchy service with caching and status aggregation."""

from __future__ import annotations

import asyncio
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from cachetools import TTLCache

from app.schemas.monitoring import (
    AggregatedStatus,
    HostMetricsSchema,
    HostSchema,
    HostServiceSchema,
    HostStatus,
    MonitoringHierarchyResponse,
    MonitoringStatsResponse,
    RegionSchema,
    ServiceStatus,
    VerfahrenSchema,
)

logger = structlog.get_logger(__name__)

# ============================================================================
# Cache Configuration
# ============================================================================

# TTL Cache: max 100 items, 30 second TTL
_hierarchy_cache: TTLCache[str, MonitoringHierarchyResponse] = TTLCache(maxsize=100, ttl=30)
_stats_cache: TTLCache[str, MonitoringStatsResponse] = TTLCache(maxsize=10, ttl=30)

CACHE_KEY_HIERARCHY = "monitoring_hierarchy"
CACHE_KEY_STATS = "monitoring_stats"


# ============================================================================
# Exceptions
# ============================================================================

class MonitoringError(Exception):
    """Base monitoring error."""
    pass


class RegionNotFoundError(MonitoringError):
    """Region not found."""
    pass


class VerfahrenNotFoundError(MonitoringError):
    """Verfahren not found."""
    pass


class HostNotFoundError(MonitoringError):
    """Host not found."""
    pass


class ServiceNotFoundError(MonitoringError):
    """Service not found on host."""
    pass


# ============================================================================
# Monitoring Service
# ============================================================================

class MonitoringService:
    """
    Service for managing monitoring hierarchy.

    In production, this would connect to a real monitoring backend
    (e.g., Prometheus, Zabbix, Nagios). For now, it generates mock data.
    """

    def __init__(self) -> None:
        self._last_generated: datetime | None = None
        self._cached_data: MonitoringHierarchyResponse | None = None

    # === Hierarchy Operations ===

    async def get_hierarchy(
        self,
        region_filter: str | None = None,
        status_filter: AggregatedStatus | None = None,
        include_offline: bool = True,
    ) -> MonitoringHierarchyResponse:
        """
        Get the full monitoring hierarchy with optional filters.

        Results are cached for 30 seconds.
        """
        # Check cache first
        cache_key = f"{CACHE_KEY_HIERARCHY}:{region_filter}:{status_filter}:{include_offline}"

        if cache_key in _hierarchy_cache:
            logger.debug("hierarchy_cache_hit", cache_key=cache_key)
            return _hierarchy_cache[cache_key]

        logger.debug("hierarchy_cache_miss", cache_key=cache_key)

        # Generate/fetch hierarchy data
        hierarchy = await self._fetch_hierarchy()

        # Apply filters
        filtered_regions = hierarchy.regions

        if region_filter:
            region_lower = region_filter.lower()
            filtered_regions = [
                r for r in filtered_regions
                if region_lower in r.name.lower()
            ]

        if status_filter:
            filtered_regions = [
                r for r in filtered_regions
                if r.aggregated_status == status_filter
            ]

        if not include_offline:
            # Remove offline hosts from the hierarchy
            filtered_regions = self._filter_offline_hosts(filtered_regions)

        result = MonitoringHierarchyResponse(
            regions=filtered_regions,
            last_updated=hierarchy.last_updated,
        )

        # Cache result
        _hierarchy_cache[cache_key] = result

        return result

    async def get_region(self, region_id: str) -> RegionSchema:
        """Get a single region by ID."""
        hierarchy = await self.get_hierarchy()

        for region in hierarchy.regions:
            if region.id == region_id:
                return region

        raise RegionNotFoundError(f"Region {region_id} not found")

    async def get_verfahren(self, verfahren_id: str) -> VerfahrenSchema:
        """Get a single verfahren by ID."""
        hierarchy = await self.get_hierarchy()

        for region in hierarchy.regions:
            for verfahren in region.verfahren:
                if verfahren.id == verfahren_id:
                    return verfahren

        raise VerfahrenNotFoundError(f"Verfahren {verfahren_id} not found")

    async def get_host(self, host_id: str) -> HostSchema:
        """Get a single host by ID."""
        hierarchy = await self.get_hierarchy()

        for region in hierarchy.regions:
            for verfahren in region.verfahren:
                for host in verfahren.hosts:
                    if host.id == host_id:
                        return host

        raise HostNotFoundError(f"Host {host_id} not found")

    async def list_hosts(
        self,
        status: HostStatus | None = None,
        region_id: str | None = None,
        verfahren_id: str | None = None,
    ) -> tuple[list[HostSchema], int]:
        """List all hosts with optional filters."""
        hierarchy = await self.get_hierarchy()
        hosts: list[HostSchema] = []

        for region in hierarchy.regions:
            if region_id and region.id != region_id:
                continue

            for verfahren in region.verfahren:
                if verfahren_id and verfahren.id != verfahren_id:
                    continue

                for host in verfahren.hosts:
                    if status and host.status != status:
                        continue
                    hosts.append(host)

        return hosts, len(hosts)

    # === Actions ===

    async def refresh_host(self, host_id: str) -> HostSchema:
        """
        Trigger a refresh/ping for a specific host.

        In production, this would trigger an actual health check.
        """
        host = await self.get_host(host_id)

        # Simulate refresh delay
        await asyncio.sleep(0.5)

        # Simulate status improvement chance
        new_status = host.status
        if host.status == HostStatus.WARNING and random.random() > 0.7:
            new_status = HostStatus.ONLINE

        # Create updated host with fresh timestamp
        refreshed_host = HostSchema(
            id=host.id,
            name=host.name,
            ip=host.ip,
            status=new_status,
            lastCheck=datetime.now(timezone.utc),
            services=host.services,
            metrics=host.metrics,
        )

        logger.info(
            "host_refreshed",
            host_id=host_id,
            old_status=host.status.value,
            new_status=new_status.value,
        )

        # Invalidate cache
        self._invalidate_cache()

        return refreshed_host

    async def check_service(self, host_id: str, service_name: str) -> HostServiceSchema:
        """
        Check a specific service on a host.

        In production, this would perform an actual service check.
        """
        host = await self.get_host(host_id)

        service = next(
            (s for s in host.services if s.name == service_name),
            None
        )

        if not service:
            raise ServiceNotFoundError(
                f"Service {service_name} not found on host {host_id}"
            )

        # Simulate check delay
        await asyncio.sleep(0.3)

        # Simulate status improvement chance for error services
        new_status = service.status
        if service.status == ServiceStatus.ERROR and random.random() > 0.5:
            new_status = ServiceStatus.RUNNING

        checked_service = HostServiceSchema(
            name=service.name,
            port=service.port,
            status=new_status,
        )

        logger.info(
            "service_checked",
            host_id=host_id,
            service_name=service_name,
            old_status=service.status.value,
            new_status=new_status.value,
        )

        # Invalidate cache
        self._invalidate_cache()

        return checked_service

    # === Statistics ===

    async def get_stats(self) -> MonitoringStatsResponse:
        """Get aggregated monitoring statistics."""
        if CACHE_KEY_STATS in _stats_cache:
            return _stats_cache[CACHE_KEY_STATS]

        hierarchy = await self.get_hierarchy()

        total_hosts = 0
        healthy_hosts = 0
        warning_hosts = 0
        offline_hosts = 0
        total_verfahren = 0

        for region in hierarchy.regions:
            total_verfahren += len(region.verfahren)

            for verfahren in region.verfahren:
                for host in verfahren.hosts:
                    total_hosts += 1
                    if host.status == HostStatus.ONLINE:
                        healthy_hosts += 1
                    elif host.status == HostStatus.WARNING:
                        warning_hosts += 1
                    elif host.status == HostStatus.OFFLINE:
                        offline_hosts += 1

        stats = MonitoringStatsResponse(
            totalRegions=len(hierarchy.regions),
            totalVerfahren=total_verfahren,
            totalHosts=total_hosts,
            healthyHosts=healthy_hosts,
            warningHosts=warning_hosts,
            offlineHosts=offline_hosts,
        )

        _stats_cache[CACHE_KEY_STATS] = stats
        return stats

    # === Private Methods ===

    async def _fetch_hierarchy(self) -> MonitoringHierarchyResponse:
        """
        Fetch hierarchy from data source.

        In production, this would query a database or external monitoring API.
        For now, it generates realistic mock data.
        """
        # Use cached data if recent enough
        base_cache_key = CACHE_KEY_HIERARCHY
        if base_cache_key in _hierarchy_cache:
            return _hierarchy_cache[base_cache_key]

        # Generate mock data
        hierarchy = self._generate_mock_hierarchy()
        _hierarchy_cache[base_cache_key] = hierarchy

        return hierarchy

    def _generate_mock_hierarchy(self) -> MonitoringHierarchyResponse:
        """Generate realistic mock monitoring data."""
        regions_data = [
            {
                "name": "Bremerhaven",
                "verfahren": [
                    ("Mastu_BHV001", "Masterumgebung BHV", "Primäre Produktionsumgebung"),
                    ("Mastu_BHV002", "Masterumgebung BHV Backup", "Disaster Recovery"),
                    ("Fila_BHV001", "Fileablage BHV", "Zentrale Dokumentenverwaltung"),
                    ("Web_BHV001", "Webservices BHV", "Öffentliche Webportale"),
                ],
            },
            {
                "name": "Hamburg",
                "verfahren": [
                    ("Mastu_HH001", "Masterumgebung Hamburg", "Hauptrechenzentrum"),
                    ("Fila_HH001", "Fileablage Hamburg", "Archivierung"),
                    ("API_HH001", "API Gateway Hamburg", "Zentrale API-Verwaltung"),
                ],
            },
            {
                "name": "Niedersachsen",
                "verfahren": [
                    ("Mastu_NL001", "Masterumgebung NDS", "Produktionsumgebung"),
                    ("Mastu_NL002", "Test-Umgebung NDS", "Staging und QA"),
                    ("Fila_NL001", "Fileablage NDS", "Zentrale Dateiablage"),
                    ("DB_NL001", "Datenbank Cluster NDS", "PostgreSQL HA Cluster"),
                ],
            },
        ]

        regions: list[RegionSchema] = []

        for region_data in regions_data:
            verfahren_list: list[VerfahrenSchema] = []

            for code, name, description in region_data["verfahren"]:
                hosts = self._generate_hosts(random.randint(5, 12))
                aggregated = self._calculate_aggregated_status(hosts)

                verfahren_list.append(VerfahrenSchema(
                    id=self._generate_id("verfahren"),
                    code=code,
                    name=name,
                    description=description,
                    hosts=hosts,
                    aggregatedStatus=aggregated,
                ))

            region_aggregated = self._calculate_region_status(verfahren_list)

            regions.append(RegionSchema(
                id=self._generate_id("region"),
                name=region_data["name"],
                verfahren=verfahren_list,
                aggregatedStatus=region_aggregated,
            ))

        return MonitoringHierarchyResponse(
            regions=regions,
            lastUpdated=datetime.now(timezone.utc),
        )

    def _generate_hosts(self, count: int) -> list[HostSchema]:
        """Generate a list of mock hosts."""
        prefixes = ["srv", "app", "web", "db", "api", "cache", "worker"]
        roles = ["master", "slave", "primary", "node", "backend"]
        services_pool = [
            ("nginx", 80), ("nginx-ssl", 443), ("postgresql", 5432),
            ("redis", 6379), ("node-app", 3000), ("docker", 2375),
            ("ssh", 22), ("prometheus", 9090), ("elasticsearch", 9200),
        ]

        hosts: list[HostSchema] = []

        for i in range(count):
            # 80% online, 15% warning, 5% offline
            rand = random.random()
            if rand < 0.80:
                status = HostStatus.ONLINE
            elif rand < 0.95:
                status = HostStatus.WARNING
            else:
                status = HostStatus.OFFLINE

            prefix = random.choice(prefixes)
            role = random.choice(roles)
            hostname = f"{prefix}-{role}-{str(i+1).zfill(2)}"

            services = self._generate_services(status, services_pool)
            metrics = self._generate_metrics(status)

            hosts.append(HostSchema(
                id=self._generate_id("host"),
                name=hostname,
                ip=f"10.{random.randint(100, 200)}.{random.randint(1, 50)}.{random.randint(1, 254)}",
                status=status,
                lastCheck=datetime.now(timezone.utc) - timedelta(seconds=random.randint(0, 300)),
                services=services,
                metrics=metrics,
            ))

        return hosts

    def _generate_services(
        self,
        host_status: HostStatus,
        pool: list[tuple[str, int]],
    ) -> list[HostServiceSchema]:
        """Generate services for a host based on its status."""
        num_services = random.randint(2, 5)
        selected = random.sample(pool, min(num_services, len(pool)))
        services: list[HostServiceSchema] = []

        for name, port in selected:
            if host_status == HostStatus.OFFLINE:
                status = ServiceStatus.STOPPED
            elif host_status == HostStatus.WARNING:
                rand = random.random()
                status = (
                    ServiceStatus.RUNNING if rand < 0.6
                    else ServiceStatus.ERROR if rand < 0.9
                    else ServiceStatus.STOPPED
                )
            else:
                status = (
                    ServiceStatus.RUNNING if random.random() < 0.95
                    else ServiceStatus.ERROR
                )

            services.append(HostServiceSchema(
                name=name,
                port=port,
                status=status,
            ))

        return services

    def _generate_metrics(self, status: HostStatus) -> HostMetricsSchema | None:
        """Generate resource metrics for a host."""
        if status == HostStatus.OFFLINE:
            return HostMetricsSchema(cpu=0, memory=0, disk=0, uptime=0)

        is_warning = status == HostStatus.WARNING

        return HostMetricsSchema(
            cpu=random.uniform(70, 95) if is_warning else random.uniform(5, 65),
            memory=random.uniform(75, 95) if is_warning else random.uniform(20, 70),
            disk=random.uniform(30, 85),
            uptime=random.randint(3600, 86400 * 90),  # 1 hour to 90 days
        )

    def _calculate_aggregated_status(
        self,
        hosts: list[HostSchema],
    ) -> AggregatedStatus:
        """Calculate aggregated status from hosts."""
        if not hosts:
            return AggregatedStatus.HEALTHY

        offline_count = sum(1 for h in hosts if h.status == HostStatus.OFFLINE)
        warning_count = sum(1 for h in hosts if h.status == HostStatus.WARNING)

        if offline_count > 0:
            return AggregatedStatus.CRITICAL
        if warning_count > 0:
            return AggregatedStatus.DEGRADED
        return AggregatedStatus.HEALTHY

    def _calculate_region_status(
        self,
        verfahren_list: list[VerfahrenSchema],
    ) -> AggregatedStatus:
        """Calculate aggregated status for a region."""
        if not verfahren_list:
            return AggregatedStatus.HEALTHY

        has_critical = any(
            v.aggregated_status == AggregatedStatus.CRITICAL
            for v in verfahren_list
        )
        has_degraded = any(
            v.aggregated_status == AggregatedStatus.DEGRADED
            for v in verfahren_list
        )

        if has_critical:
            return AggregatedStatus.CRITICAL
        if has_degraded:
            return AggregatedStatus.DEGRADED
        return AggregatedStatus.HEALTHY

    def _filter_offline_hosts(
        self,
        regions: list[RegionSchema],
    ) -> list[RegionSchema]:
        """Remove offline hosts from hierarchy."""
        filtered_regions: list[RegionSchema] = []

        for region in regions:
            filtered_verfahren: list[VerfahrenSchema] = []

            for verfahren in region.verfahren:
                online_hosts = [
                    h for h in verfahren.hosts
                    if h.status != HostStatus.OFFLINE
                ]

                if online_hosts:
                    filtered_verfahren.append(VerfahrenSchema(
                        id=verfahren.id,
                        code=verfahren.code,
                        name=verfahren.name,
                        description=verfahren.description,
                        hosts=online_hosts,
                        aggregatedStatus=self._calculate_aggregated_status(online_hosts),
                    ))

            if filtered_verfahren:
                filtered_regions.append(RegionSchema(
                    id=region.id,
                    name=region.name,
                    verfahren=filtered_verfahren,
                    aggregatedStatus=self._calculate_region_status(filtered_verfahren),
                ))

        return filtered_regions

    def _generate_id(self, prefix: str) -> str:
        """Generate a random ID with prefix."""
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{prefix}-{suffix}"

    def _invalidate_cache(self) -> None:
        """Invalidate all caches."""
        _hierarchy_cache.clear()
        _stats_cache.clear()
        logger.debug("monitoring_cache_invalidated")


# ============================================================================
# Singleton Instance
# ============================================================================

_monitoring_service: MonitoringService | None = None


def get_monitoring_service() -> MonitoringService:
    """Get or create the monitoring service singleton."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
