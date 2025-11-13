"""Provisioning services for agents."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.agent import Agent, AgentDownloadToken, AuditLog, EnrollmentToken


class ProvisioningError(Exception):
    """Raised when provisioning fails."""


async def create_agent_and_token(
    *,
    session: AsyncSession,
    settings: Settings,
    payload: dict[str, Any],
    actor_id: str | None,
) -> tuple[Agent, EnrollmentToken]:
    """Create an agent and corresponding enrollment token."""

    agent = Agent(
        host_id=payload["host_id"],
        hostname=payload["hostname"],
        os=payload["os"],
        architecture=payload["architecture"],
        sampling_interval=payload["sampling_interval"],
        tags=payload.get("tags", []),
        modules=payload.get("modules", {}),
        checks=payload.get("checks"),
    )
    session.add(agent)
    try:
        await session.flush()
    except IntegrityError as exc:  # pragma: no cover - defensive, tested via logic
        await session.rollback()
        raise ProvisioningError("Agent with the same host_id already exists") from exc

    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.enrollment_token_ttl_hours)
    enrollment_token = EnrollmentToken(
        jti=str(uuid4()),
        agent_id=agent.id,
        host_id=agent.host_id,
        expires_at=expires_at,
    )
    session.add(enrollment_token)

    session.add(
        AuditLog(
            event_type="agent.provision",
            actor_id=actor_id,
            metadata={"agent_id": str(agent.id), "host_id": agent.host_id},
        )
    )

    await session.commit()
    await session.refresh(agent)
    await session.refresh(enrollment_token)
    return agent, enrollment_token


async def use_enrollment_token(
    *,
    session: AsyncSession,
    token_value: str,
) -> EnrollmentToken:
    """Validate and mark an enrollment token as used."""

    query = select(EnrollmentToken).where(EnrollmentToken.jti == token_value)
    token = await session.scalar(query)
    if token is None:
        raise ProvisioningError("Enrollment token not found")

    now = datetime.now(timezone.utc)
    if token.expires_at <= now:
        raise ProvisioningError("Enrollment token expired")
    if token.used_at is not None:
        raise ProvisioningError("Enrollment token already used")

    token.used_at = now
    await session.flush()
    return token


async def create_download_token(
    *,
    session: AsyncSession,
    settings: Settings,
    agent: Agent,
) -> AgentDownloadToken:
    """Create a short-lived agent download token."""

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.download_token_ttl_minutes)
    download_token = AgentDownloadToken(
        token=str(uuid4()),
        agent_id=agent.id,
        expires_at=expires_at,
    )
    session.add(download_token)
    await session.flush()
    return download_token


async def audit_bootstrap(
    *,
    session: AsyncSession,
    actor: str | None,
    agent_id: str,
    host_id: str,
) -> None:
    """Persist an audit event for bootstrap usage."""

    session.add(
        AuditLog(
            event_type="agent.bootstrap",
            actor_id=actor,
            metadata={"agent_id": agent_id, "host_id": host_id},
        )
    )
    await session.flush()
