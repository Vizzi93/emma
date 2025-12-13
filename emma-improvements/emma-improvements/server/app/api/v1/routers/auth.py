"""Authentication API routes."""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_dependency
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    UserResponse,
)
from app.services.auth import (
    AuthService,
    InvalidCredentialsError,
    InvalidTokenError,
    UserExistsError,
    UserInactiveError,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = structlog.get_logger(__name__)


def get_client_info(request: Request) -> tuple[str | None, str | None]:
    """Extract client IP and user agent from request."""
    # Get real IP (respecting proxy headers)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None

    user_agent = request.headers.get("User-Agent")
    return ip_address, user_agent


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account and return authentication tokens.",
)
async def register(
    request_body: RegisterRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> AuthResponse:
    """Register a new user."""
    ip_address, user_agent = get_client_info(request)
    auth_service = AuthService(session)

    try:
        return await auth_service.register(
            request=request_body,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except UserExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login user",
    description="Authenticate with email and password to receive tokens.",
)
async def login(
    request_body: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> AuthResponse:
    """Login with email and password."""
    ip_address, user_agent = get_client_info(request)
    auth_service = AuthService(session)

    try:
        return await auth_service.login(
            email=request_body.email,
            password=request_body.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except UserInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token.",
)
async def refresh_token(
    request_body: RefreshTokenRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> AccessTokenResponse:
    """Refresh access token."""
    ip_address, user_agent = get_client_info(request)
    auth_service = AuthService(session)

    try:
        return await auth_service.refresh_access_token(
            refresh_token=request_body.refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Revoke the refresh token to logout.",
)
async def logout(
    request_body: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> MessageResponse:
    """Logout by revoking refresh token."""
    auth_service = AuthService(session)
    await auth_service.logout(request_body.refresh_token)
    return MessageResponse(message="Successfully logged out")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Logout all sessions",
    description="Revoke all refresh tokens for the current user.",
)
async def logout_all_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> MessageResponse:
    """Logout all sessions by revoking all refresh tokens."""
    auth_service = AuthService(session)
    count = await auth_service.logout_all_sessions(current_user.id)
    return MessageResponse(message=f"Logged out from {count} session(s)")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's profile.",
)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change the current user's password. This will logout all sessions.",
)
async def change_password(
    request_body: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_dependency)],
) -> MessageResponse:
    """Change password for current user."""
    auth_service = AuthService(session)

    try:
        await auth_service.change_password(
            user_id=current_user.id,
            current_password=request_body.current_password,
            new_password=request_body.new_password,
        )
        return MessageResponse(
            message="Password changed successfully. Please login again."
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
