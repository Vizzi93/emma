"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session


async def get_settings_dependency() -> Settings:
    """Expose settings as a dependency."""

    return get_settings()


async def get_db_dependency() -> AsyncSession:
    """Expose DB session dependency."""

    async for session in get_db_session():
        return session
    raise RuntimeError("Database session dependency failed to yield")


async def require_actor(
    role: str = Header(..., alias="X-Role"),
    actor_id: str | None = Header(default=None, alias="X-Actor-Id"),
) -> str | None:
    """Ensure the caller has sufficient privileges."""

    allowed_roles = {"ADMIN", "OPERATOR"}
    if role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return actor_id
