"""Agent management API endpoints."""

from __future__ import annotations

import random
import string
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentListResponse,
    AgentModuleConfig,
)

router = APIRouter(prefix="/agents", tags=["agents"])

# In-memory storage for agents (in production, use database)
_agents_db: dict[str, dict] = {}


def _generate_mock_agents() -> None:
    """Generate initial mock agents if empty."""
    if _agents_db:
        return

    mock_data = [
        {
            "hostname": "prod-web-01",
            "host_id": "host-prod-web-01",
            "os": "linux",
            "architecture": "x86_64",
            "status": "healthy",
            "sampling_interval": 30,
            "tags": ["production", "web"],
            "modules": {"cpu": {"enabled": True}, "memory": {"enabled": True}},
        },
        {
            "hostname": "prod-db-01",
            "host_id": "host-prod-db-01",
            "os": "linux",
            "architecture": "x86_64",
            "status": "warning",
            "sampling_interval": 15,
            "tags": ["production", "database"],
            "modules": {"cpu": {"enabled": True}, "disk": {"enabled": True}},
        },
        {
            "hostname": "staging-api-01",
            "host_id": "host-staging-api-01",
            "os": "linux",
            "architecture": "arm64",
            "status": "healthy",
            "sampling_interval": 60,
            "tags": ["staging", "api"],
            "modules": {"cpu": {"enabled": True}},
        },
    ]

    for data in mock_data:
        agent_id = str(uuid4())
        now = datetime.now(timezone.utc)
        _agents_db[agent_id] = {
            "id": agent_id,
            **data,
            "ip_address": f"10.0.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "version": "1.0.0",
            "is_active": True,
            "last_seen_at": now,
            "created_at": now,
            "updated_at": now,
        }


# Initialize mock data
_generate_mock_agents()


@router.get("", response_model=AgentListResponse)
async def list_agents(
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: str | None = Query(None, alias="status"),
    tag: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AgentListResponse:
    """List all registered agents with optional filters."""
    agents = list(_agents_db.values())

    # Apply filters
    if status_filter:
        agents = [a for a in agents if a["status"] == status_filter]
    if tag:
        agents = [a for a in agents if tag in a.get("tags", [])]
    if search:
        search_lower = search.lower()
        agents = [
            a for a in agents
            if search_lower in a["hostname"].lower()
            or search_lower in a["host_id"].lower()
            or any(search_lower in t.lower() for t in a.get("tags", []))
        ]

    # Sort by hostname
    agents.sort(key=lambda x: x["hostname"])

    # Pagination
    total = len(agents)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    paginated = agents[start:end]

    return AgentListResponse(
        items=[AgentResponse(**a) for a in paginated],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
) -> AgentResponse:
    """Create a new agent."""
    # Check for duplicate host_id
    for existing in _agents_db.values():
        if existing["host_id"] == agent_data.host_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent with host_id '{agent_data.host_id}' already exists",
            )

    agent_id = str(uuid4())
    now = datetime.now(timezone.utc)

    agent = {
        "id": agent_id,
        "host_id": agent_data.host_id,
        "hostname": agent_data.hostname,
        "os": agent_data.os,
        "architecture": agent_data.architecture,
        "status": "unknown",
        "sampling_interval": agent_data.sampling_interval,
        "tags": agent_data.tags,
        "modules": {k: v.model_dump() for k, v in agent_data.modules.items()},
        "ip_address": None,
        "version": None,
        "is_active": True,
        "last_seen_at": None,
        "created_at": now,
        "updated_at": now,
    }

    _agents_db[agent_id] = agent
    return AgentResponse(**agent)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> AgentResponse:
    """Get agent details by ID."""
    agent = _agents_db.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    return AgentResponse(**agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    update_data: AgentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
) -> AgentResponse:
    """Update an existing agent."""
    agent = _agents_db.get(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    # Apply updates
    update_dict = update_data.model_dump(exclude_unset=True)
    if "modules" in update_dict and update_dict["modules"]:
        update_dict["modules"] = {
            k: v.model_dump() if hasattr(v, "model_dump") else v
            for k, v in update_dict["modules"].items()
        }

    agent.update(update_dict)
    agent["updated_at"] = datetime.now(timezone.utc)

    _agents_db[agent_id] = agent
    return AgentResponse(**agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete an agent."""
    if agent_id not in _agents_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    del _agents_db[agent_id]
