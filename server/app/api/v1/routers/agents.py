"""Agent provisioning routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from jinja2 import Environment, PackageLoader, select_autoescape
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_dependency, get_settings_dependency, require_actor
from app.core.config import Settings
from app.core.security import ConfigSigner
from app.models.agent import Agent
from app.schemas.agents import (
    BootstrapResponse,
    ProvisionAgentRequest,
    ProvisionAgentResponse,
)
from app.services import provisioning

router = APIRouter(prefix="/agents", tags=["agents"])

_templates_env = Environment(
    loader=PackageLoader("app", "templates"),
    autoescape=select_autoescape(enabled_extensions=("j2",)),
)


async def _render_template(template_name: str, context: dict[str, str]) -> str:
    template = _templates_env.get_template(template_name)
    return template.render(**context)


@router.post(
    "/provision",
    response_model=ProvisionAgentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def provision_agent(
    request: ProvisionAgentRequest,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
    actor_id: Annotated[str | None, Depends(require_actor)],
) -> ProvisionAgentResponse:
    """Provision a new agent and return a single-use enrollment token."""

    agent, token = await provisioning.create_agent_and_token(
        session=session,
        settings=settings,
        payload=request.model_dump(),
        actor_id=actor_id,
    )
    return ProvisionAgentResponse(agent_id=agent.id, token=token.jti, expires_at=token.expires_at)


@router.get(
    "/bootstrap/{token}",
    response_model=BootstrapResponse,
)
async def bootstrap_agent(
    token: str,
    platform: Annotated[str, Query(pattern="^(linux|windows)$")],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> BootstrapResponse:
    """Return bootstrap materials for an agent enrollment token."""

    async with session.begin():
        try:
            enrollment_token = await provisioning.use_enrollment_token(
                session=session, token_value=token
            )
        except provisioning.ProvisioningError as exc:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc

        agent = await session.get(Agent, enrollment_token.agent_id)
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent missing")

        download_token = await provisioning.create_download_token(
            session=session, settings=settings, agent=agent
        )
        await provisioning.audit_bootstrap(
            session=session,
            actor=None,
            agent_id=str(agent.id),
            host_id=enrollment_token.host_id,
        )

    signer = ConfigSigner(settings)
    config_claims = {
        "agent_id": str(agent.id),
        "version": "1.0",
        "modules": agent.modules,
        "intervals": {
            "sampling": agent.sampling_interval,
            "modules": {
                name: module.get("interval_seconds")
                for name, module in agent.modules.items()
                if isinstance(module, dict)
            },
        },
        "checks": agent.checks or {},
    }
    config_jwt = signer.sign(config_claims)

    download_url = f"{settings.agent_binary_base_url}/download/{download_token.token}"
    template_name = {
        "linux": "bootstrap/linux.sh.j2",
        "windows": "bootstrap/windows.ps1.j2",
    }[platform]
    script = await _render_template(
        template_name,
        {
            "download_url": download_url,
            "enrollment_token": token,
            "config_jwt": config_jwt,
        },
    )

    return BootstrapResponse(
        script=script,
        download_url=download_url,
        config_jwt=config_jwt,
        expires_at=download_token.expires_at,
    )
