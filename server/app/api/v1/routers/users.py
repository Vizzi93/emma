"""User management API routes (admin only)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_dependency, require_admin
from app.models.user import User
from app.schemas.users import (
    CreateUserRequest, UpdateUserRequest, ResetPasswordRequest,
    UserResponse, UserListResponse, UserSessionsResponse, SessionResponse, UserStatsResponse,
)
from app.services.user_management import (
    UserManagementService, UserNotFoundError, UserExistsError, CannotModifySelfError, UserManagementError,
)

router = APIRouter(prefix="/users", tags=["users"])
logger = structlog.get_logger(__name__)


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> UserStatsResponse:
    """Get user statistics (admin only)."""
    service = UserManagementService(session)
    stats = await service.get_user_stats()
    return UserStatsResponse(**stats)


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
    include_inactive: bool = Query(False),
    role: str | None = Query(None, pattern="^(admin|operator|viewer)$"),
    search: str | None = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> UserListResponse:
    """List all users (admin only)."""
    service = UserManagementService(session)
    users, total = await service.list_users(
        include_inactive=include_inactive, role=role, search=search, limit=limit, offset=offset,
    )
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total, limit=limit, offset=offset,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> UserResponse:
    """Create a new user (admin only)."""
    service = UserManagementService(session)
    try:
        user = await service.create_user(
            email=request.email, password=request.password, full_name=request.full_name,
            role=request.role, is_active=request.is_active,
        )
        return UserResponse.model_validate(user)
    except UserExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except UserManagementError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> UserResponse:
    """Get user details (admin only)."""
    service = UserManagementService(session)
    try:
        user = await service.get_user(user_id)
        return UserResponse.model_validate(user)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    request: UpdateUserRequest,
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> UserResponse:
    """Update user details (admin only)."""
    service = UserManagementService(session)
    try:
        user = await service.update_user(user_id, current_user.id, **request.model_dump(exclude_unset=True))
        return UserResponse.model_validate(user)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except CannotModifySelfError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except UserManagementError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    user_id: UUID,
    request: ResetPasswordRequest,
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> None:
    """Reset user password (admin only)."""
    service = UserManagementService(session)
    try:
        await service.reset_password(user_id, request.new_password, current_user.id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> None:
    """Delete a user (admin only)."""
    service = UserManagementService(session)
    try:
        await service.delete_user(user_id, current_user.id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except CannotModifySelfError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get("/{user_id}/sessions", response_model=UserSessionsResponse)
async def get_user_sessions(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> UserSessionsResponse:
    """Get user's active sessions (admin only)."""
    service = UserManagementService(session)
    try:
        await service.get_user(user_id)  # Verify user exists
        sessions = await service.get_user_sessions(user_id)
        return UserSessionsResponse(
            user_id=user_id,
            sessions=[SessionResponse.model_validate(s) for s in sessions],
            total=len(sessions),
        )
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{user_id}/sessions", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_sessions(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> None:
    """Revoke all sessions for a user (admin only)."""
    service = UserManagementService(session)
    try:
        await service.get_user(user_id)
        await service.revoke_all_user_sessions(user_id, current_user.id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{user_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    user_id: UUID,
    session_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> None:
    """Revoke a specific session (admin only)."""
    service = UserManagementService(session)
    await service.revoke_session(session_id, user_id)
