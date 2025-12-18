"""FastAPI dependencies for authentication and database access."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import jwt_handler
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models.user import User, UserRole

# Bearer token security scheme
bearer_scheme = HTTPBearer(auto_error=False)


async def get_settings_dependency() -> Settings:
    """Expose settings as a dependency."""
    return get_settings()


async def get_db_dependency():
    """
    Expose DB session dependency.

    Yields an AsyncSession that is properly committed/rolled back on exit.
    Uses the same lifecycle as get_db_session to ensure proper cleanup.
    """
    async for session in get_db_session():
        try:
            yield session
        except Exception:
            # Let the outer get_db_session handle rollback
            raise


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> User:
    """
    Validate JWT token and return current user.
    
    Raises HTTPException if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    # Decode token
    payload = jwt_handler.decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    # Get user ID from payload
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # Get user from database
    user = await session.get(User, user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user and verify they are active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to require specific user roles.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: Annotated[User, Depends(require_role(UserRole.ADMIN))]
        ):
            ...
    """
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


# Pre-configured role dependencies
require_admin = require_role(UserRole.ADMIN)
require_operator = require_role(UserRole.ADMIN, UserRole.OPERATOR)
require_viewer = require_role(UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER)


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> User | None:
    """
    Get current user if authenticated, None otherwise.
    
    Use for endpoints that work for both authenticated and anonymous users.
    """
    if credentials is None:
        return None

    payload = jwt_handler.decode_access_token(credentials.credentials)
    if payload is None:
        return None

    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return None

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        return None

    return user
