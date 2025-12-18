"""WebSocket endpoint for real-time updates."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.core.auth import jwt_handler
from app.core.websocket import (
    EventType,
    WebSocketEvent,
    get_connection_manager,
)

router = APIRouter(tags=["websocket"])
logger = structlog.get_logger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    """
    WebSocket endpoint for real-time updates.
    
    Connect with optional JWT token for authentication:
    ws://host/ws?token=YOUR_JWT_TOKEN
    
    Messages from client:
    - {"type": "ping"} - Keepalive, server responds with pong
    - {"type": "subscribe", "channel": "services"} - Subscribe to channel
    - {"type": "unsubscribe", "channel": "services"} - Unsubscribe
    
    Events from server:
    - service.created, service.updated, service.deleted
    - service.status_changed, service.check_completed
    - alert.triggered, alert.resolved
    """
    manager = get_connection_manager()
    connection_id = str(uuid4())
    user_id = None
    
    # Validate token if provided
    if token:
        payload = jwt_handler.decode_access_token(token)
        if payload:
            user_id = payload.get("sub")
    
    # Accept connection
    connection = await manager.connect(
        websocket=websocket,
        connection_id=connection_id,
        user_id=user_id,
    )
    
    # Auto-subscribe to common channels
    await manager.subscribe(connection_id, "services")
    await manager.subscribe(connection_id, "alerts")
    
    try:
        # Keepalive task
        async def send_keepalive():
            while True:
                await asyncio.sleep(30)
                if websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        await websocket.send_text(
                            WebSocketEvent(
                                type=EventType.PING,
                                data={"keepalive": True},
                            ).to_json()
                        )
                    except Exception as e:
                        logger.debug(
                            "websocket_keepalive_failed",
                            connection_id=connection_id,
                            error=str(e),
                        )
                        break
                else:
                    break
        
        keepalive_task = asyncio.create_task(send_keepalive())
        
        try:
            # Message loop with timeout to detect hung connections
            RECEIVE_TIMEOUT = 120  # 2 minutes, keepalive is 30s
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=RECEIVE_TIMEOUT,
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        "websocket_receive_timeout",
                        connection_id=connection_id,
                        timeout=RECEIVE_TIMEOUT,
                    )
                    break

                response = await manager.handle_message(connection_id, message)

                if response:
                    await websocket.send_text(response.to_json())
                    
        finally:
            keepalive_task.cancel()
            try:
                await keepalive_task
            except asyncio.CancelledError:
                pass
                
    except WebSocketDisconnect:
        logger.debug("websocket_client_disconnected", connection_id=connection_id)
    except Exception as e:
        logger.exception("websocket_error", connection_id=connection_id, error=str(e))
    finally:
        await manager.disconnect(connection_id)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    manager = get_connection_manager()
    return {
        "active_connections": manager.connection_count,
    }
