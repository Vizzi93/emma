"""WebSocket connection manager for real-time updates."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

import structlog
from fastapi import WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)


class EventType(str, Enum):
    """WebSocket event types."""
    
    # Connection events
    CONNECTED = "connected"
    PING = "ping"
    PONG = "pong"
    
    # Service events
    SERVICE_CREATED = "service.created"
    SERVICE_UPDATED = "service.updated"
    SERVICE_DELETED = "service.deleted"
    SERVICE_STATUS_CHANGED = "service.status_changed"
    SERVICE_CHECK_COMPLETED = "service.check_completed"
    
    # Alert events
    ALERT_TRIGGERED = "alert.triggered"
    ALERT_RESOLVED = "alert.resolved"
    
    # Agent events
    AGENT_CONNECTED = "agent.connected"
    AGENT_DISCONNECTED = "agent.disconnected"
    AGENT_METRICS = "agent.metrics"


@dataclass
class WebSocketEvent:
    """WebSocket event structure."""
    
    type: EventType
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_json(self) -> str:
        """Serialize event to JSON string."""
        return json.dumps({
            "type": self.type.value,
            "data": self._serialize_data(self.data),
            "timestamp": self.timestamp.isoformat(),
        })
    
    def _serialize_data(self, data: Any) -> Any:
        """Recursively serialize data, handling UUIDs and datetimes."""
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, UUID):
            return str(data)
        elif isinstance(data, datetime):
            return data.isoformat()
        return data


@dataclass
class Connection:
    """Represents an active WebSocket connection."""
    
    websocket: WebSocket
    user_id: str | None = None
    subscriptions: set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    Features:
    - Track active connections per user
    - Subscription-based filtering
    - Broadcast to all or specific users
    - Automatic cleanup on disconnect
    """

    def __init__(self) -> None:
        self._connections: dict[str, Connection] = {}
        self._lock = asyncio.Lock()

    @property
    def connection_count(self) -> int:
        """Number of active connections."""
        return len(self._connections)

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: str | None = None,
    ) -> Connection:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket instance
            connection_id: Unique identifier for this connection
            user_id: Optional user ID for user-specific broadcasts
        """
        await websocket.accept()
        
        connection = Connection(
            websocket=websocket,
            user_id=user_id,
        )
        
        async with self._lock:
            self._connections[connection_id] = connection
        
        logger.info(
            "websocket_connected",
            connection_id=connection_id,
            user_id=user_id,
            total_connections=self.connection_count,
        )
        
        # Send welcome message
        await self._send_to_connection(
            connection,
            WebSocketEvent(
                type=EventType.CONNECTED,
                data={"connection_id": connection_id, "message": "Connected to eMMA"},
            ),
        )
        
        return connection

    async def disconnect(self, connection_id: str) -> None:
        """Remove a connection."""
        async with self._lock:
            if connection_id in self._connections:
                del self._connections[connection_id]
        
        logger.info(
            "websocket_disconnected",
            connection_id=connection_id,
            total_connections=self.connection_count,
        )

    async def subscribe(self, connection_id: str, channel: str) -> None:
        """Subscribe a connection to a channel."""
        async with self._lock:
            if connection_id in self._connections:
                self._connections[connection_id].subscriptions.add(channel)
                logger.debug("websocket_subscribed", connection_id=connection_id, channel=channel)

    async def unsubscribe(self, connection_id: str, channel: str) -> None:
        """Unsubscribe a connection from a channel."""
        async with self._lock:
            if connection_id in self._connections:
                self._connections[connection_id].subscriptions.discard(channel)

    async def broadcast(self, event: WebSocketEvent, channel: str | None = None) -> int:
        """
        Broadcast an event to all connections (or filtered by channel).
        
        Args:
            event: The event to broadcast
            channel: Optional channel filter
            
        Returns:
            Number of connections that received the message
        """
        sent_count = 0
        disconnected = []
        
        async with self._lock:
            connections = list(self._connections.items())
        
        for connection_id, connection in connections:
            # Check channel subscription if specified
            if channel and channel not in connection.subscriptions:
                continue
            
            try:
                await self._send_to_connection(connection, event)
                sent_count += 1
            except Exception as e:
                logger.warning(
                    "websocket_send_failed",
                    connection_id=connection_id,
                    error=str(e),
                )
                disconnected.append(connection_id)
        
        # Cleanup failed connections
        for connection_id in disconnected:
            await self.disconnect(connection_id)
        
        if sent_count > 0:
            logger.debug(
                "websocket_broadcast",
                event_type=event.type.value,
                sent_count=sent_count,
                channel=channel,
            )
        
        return sent_count

    async def send_to_user(self, user_id: str, event: WebSocketEvent) -> int:
        """Send an event to all connections for a specific user."""
        sent_count = 0
        
        async with self._lock:
            connections = [
                (cid, conn) for cid, conn in self._connections.items()
                if conn.user_id == user_id
            ]
        
        for connection_id, connection in connections:
            try:
                await self._send_to_connection(connection, event)
                sent_count += 1
            except Exception:
                await self.disconnect(connection_id)
        
        return sent_count

    async def _send_to_connection(
        self,
        connection: Connection,
        event: WebSocketEvent,
    ) -> None:
        """Send an event to a specific connection."""
        await connection.websocket.send_text(event.to_json())

    async def handle_message(
        self,
        connection_id: str,
        message: str,
    ) -> WebSocketEvent | None:
        """
        Handle an incoming message from a client.
        
        Supports:
        - ping/pong for keepalive
        - subscribe/unsubscribe for channels
        """
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")
            
            if msg_type == "ping":
                return WebSocketEvent(type=EventType.PONG, data={})
            
            elif msg_type == "subscribe":
                channel = data.get("channel")
                if channel:
                    await self.subscribe(connection_id, channel)
                    return WebSocketEvent(
                        type=EventType.CONNECTED,
                        data={"subscribed": channel},
                    )
            
            elif msg_type == "unsubscribe":
                channel = data.get("channel")
                if channel:
                    await self.unsubscribe(connection_id, channel)
            
            return None
            
        except json.JSONDecodeError:
            logger.warning("websocket_invalid_message", connection_id=connection_id)
            return None


# Global connection manager instance
_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the global connection manager."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


# Convenience functions for broadcasting events
async def broadcast_service_event(
    event_type: EventType,
    service_data: dict[str, Any],
) -> None:
    """Broadcast a service-related event."""
    manager = get_connection_manager()
    event = WebSocketEvent(type=event_type, data=service_data)
    await manager.broadcast(event, channel="services")


async def broadcast_check_result(
    service_id: str,
    check_data: dict[str, Any],
) -> None:
    """Broadcast a check result event."""
    manager = get_connection_manager()
    event = WebSocketEvent(
        type=EventType.SERVICE_CHECK_COMPLETED,
        data={"service_id": service_id, **check_data},
    )
    await manager.broadcast(event, channel="services")


async def broadcast_alert(alert_data: dict[str, Any]) -> None:
    """Broadcast an alert event."""
    manager = get_connection_manager()
    event = WebSocketEvent(type=EventType.ALERT_TRIGGERED, data=alert_data)
    await manager.broadcast(event)  # Alerts go to everyone
