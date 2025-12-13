"""Agent management API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("")
async def list_agents() -> dict:
    """List all registered agents."""
    return {"agents": [], "total": 0}


@router.get("/{agent_id}")
async def get_agent(agent_id: str) -> dict:
    """Get agent details by ID."""
    return {"id": agent_id, "status": "unknown", "message": "Agent not found"}
