"""Tests for agent provisioning and bootstrap logic."""

from __future__ import annotations

import asyncio
from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.schemas.agents import ProvisionAgentRequest
from app.services import provisioning
from app.api.v1.routers.agents import bootstrap_agent


def test_provision_creates_agent_and_token(prepare_database: None) -> None:
    """Provisioning should persist agent metadata and issue a token."""

    payload = ProvisionAgentRequest(
        host_id="host-123",
        hostname="agent-host",
        os="linux",
        architecture="x86_64",
        sampling_interval=30,
        tags=["prod", "db"],
        modules={
            "cpu": {"enabled": True, "interval_seconds": 15},
            "mem": {"enabled": True},
        },
        checks={"http": {"url": "https://example.com"}},
    )
    settings = get_settings()

    async def _create() -> tuple[str, str]:
        async with AsyncSessionLocal() as session:
            agent, token = await provisioning.create_agent_and_token(
                session=session,
                settings=settings,
                payload=payload.model_dump(),
                actor_id="admin-user",
            )
            return str(agent.id), token.jti

    agent_id, token_value = asyncio.run(_create())
    assert UUID(agent_id)
    assert UUID(token_value)


def test_bootstrap_returns_script_and_marks_token_used(signing_public_key: str) -> None:
    """Bootstrap should render scripts and invalidate enrollment tokens."""

    provision_payload = ProvisionAgentRequest(
        host_id="bootstrap-1",
        hostname="bootstrap-host",
        os="linux",
        architecture="arm64",
        sampling_interval=20,
        modules={"cpu": {"enabled": True, "interval_seconds": 10}},
    )
    settings = get_settings()

    async def _bootstrap() -> tuple[str, dict[str, str]]:
        async with AsyncSessionLocal() as session:
            agent, token = await provisioning.create_agent_and_token(
                session=session,
                settings=settings,
                payload=provision_payload.model_dump(),
                actor_id="admin",
            )
            response = await bootstrap_agent(
                token=token.jti,
                platform="linux",
                session=session,
                settings=settings,
            )
            return token.jti, response.model_dump()

    token_value, bootstrap_data = asyncio.run(_bootstrap())
    assert bootstrap_data["download_url"].startswith("https://downloads.emma.local")
    assert bootstrap_data["script"].startswith("#!/usr/bin/env bash")

    decoded = jwt.decode(
        bootstrap_data["config_jwt"],
        signing_public_key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )
    assert decoded["modules"]["cpu"]["enabled"] is True

    async def _call_again() -> None:
        async with AsyncSessionLocal() as session:
            with pytest.raises(HTTPException):
                await bootstrap_agent(
                    token=token_value,
                    platform="linux",
                    session=session,
                    settings=settings,
                )

    asyncio.run(_call_again())
