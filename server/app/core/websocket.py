"""WebSocket connection manager for real-time updates."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import UUID

import structlog
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger(__name__)


# Pydantic models for WebSocket message validation
class WebSocketMessage(BaseModel):
    """Base WebSocket message from client."""

    type: Literal["ping", "subscribe", "unsubscribe"]


class SubscribeMessage(WebSocketMessage):
    """Subscribe to a channel."""

    type: Literal["subscribe"]
    channel: str


class UnsubscribeMessage(WebSocketMessage):
    """Unsubscribe from a channel."""

    type: Literal["unsubscribe"]
    channel: str


class PingMessage(WebSocketMessage):
    """Ping message for keepalive."""

    type: Literal["ping"]


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
        except json.JSONDecodeError as e:
            logger.warning(
                "websocket_invalid_json",
                connection_id=connection_id,
                error=str(e),
            )
            return WebSocketEvent(
                type=EventType.PONG,
                data={"error": "Invalid JSON format"},
            )

        msg_type = data.get("type", "")

        try:
            if msg_type == "ping":
                PingMessage.model_validate(data)
                return WebSocketEvent(type=EventType.PONG, data={})

            elif msg_type == "subscribe":
                validated = SubscribeMessage.model_validate(data)
                await self.subscribe(connection_id, validated.channel)
                return WebSocketEvent(
                    type=EventType.CONNECTED,
                    data={"subscribed": validated.channel},
                )

            elif msg_type == "unsubscribe":
                validated = UnsubscribeMessage.model_validate(data)
                await self.unsubscribe(connection_id, validated.channel)
                return WebSocketEvent(
                    type=EventType.PONG,
                    data={"unsubscribed": validated.channel},
                )

            else:
                logger.warning(
                    "websocket_unknown_message_type",
                    connection_id=connection_id,
                    msg_type=msg_type,
                )
                return WebSocketEvent(
                    type=EventType.PONG,
                    data={"error": f"Unknown message type: {msg_type}"},
                )

        except ValidationError as e:
            logger.warning(
                "websocket_validation_error",
                connection_id=connection_id,
                msg_type=msg_type,
                errors=e.errors(),
            )
            return WebSocketEvent(
                type=EventType.PONG,
                data={"error": "Invalid message format", "details": e.errors()},
            )


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
