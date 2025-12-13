"""Authentication service with business logic."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import jwt_handler, password_hasher
from app.models.user import RefreshToken, User, UserRole
from app.schemas.auth import (
    AccessTokenResponse,
    AuthResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

logger = structlog.get_logger(__name__)


class AuthError(Exception):
    """Base authentication error."""
    pass


class InvalidCredentialsError(AuthError):
    """Invalid email or password."""
    pass


class UserExistsError(AuthError):
    """User with email already exists."""
    pass


class UserNotFoundError(AuthError):
    """User not found."""
    pass


class UserInactiveError(AuthError):
    """User account is inactive."""
    pass


class InvalidTokenError(AuthError):
    """Invalid or expired token."""
    pass


class AuthService:
    """Authentication service."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register(
        self,
        request: RegisterRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResponse:
        """
        Register a new user.
        
        Creates user account and returns auth tokens.
        """
        # Hash password
        password_hash = password_hasher.hash(request.password)

        # Create user
        user = User(
            email=request.email.lower(),
            password_hash=password_hash,
            full_name=request.full_name,
            role=UserRole.VIEWER.value,  # Default role
            is_active=True,
            is_verified=False,  # Email verification can be added later
        )

        self._session.add(user)

        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            logger.warning("registration_failed_duplicate", email=request.email)
            raise UserExistsError("User with this email already exists") from exc

        # Create tokens
        tokens = await self._create_tokens(user, ip_address, user_agent)

        logger.info("user_registered", user_id=str(user.id), email=user.email)

        await self._session.commit()

        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def login(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResponse:
        """
        Authenticate user with email and password.
        
        Returns auth tokens on success.
        """
        # Find user
        query = select(User).where(User.email == email.lower())
        user = await self._session.scalar(query)

        if user is None:
            logger.warning("login_failed_user_not_found", email=email)
            raise InvalidCredentialsError("Invalid email or password")

        # Verify password
        if not password_hasher.verify(password, user.password_hash):
            logger.warning("login_failed_invalid_password", user_id=str(user.id))
            raise InvalidCredentialsError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            logger.warning("login_failed_user_inactive", user_id=str(user.id))
            raise UserInactiveError("User account is inactive")

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)

        # Check if password needs rehash (e.g., after bcrypt rounds update)
        if password_hasher.needs_rehash(user.password_hash):
            user.password_hash = password_hasher.hash(password)

        # Create tokens
        tokens = await self._create_tokens(user, ip_address, user_agent)

        logger.info("user_logged_in", user_id=str(user.id))

        await self._session.commit()

        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AccessTokenResponse:
        """
        Refresh an access token using a valid refresh token.
        """
        # Find refresh token
        query = select(RefreshToken).where(RefreshToken.token == refresh_token)
        token_record = await self._session.scalar(query)

        if token_record is None:
            logger.warning("refresh_failed_token_not_found")
            raise InvalidTokenError("Invalid refresh token")

        if not token_record.is_valid:
            logger.warning(
                "refresh_failed_token_invalid",
                revoked=token_record.revoked,
                expired=token_record.is_expired,
            )
            raise InvalidTokenError("Refresh token is invalid or expired")

        # Get user
        user = await self._session.get(User, token_record.user_id)
        if user is None or not user.is_active:
            raise InvalidTokenError("User not found or inactive")

        # Create new access token
        access_token, _ = jwt_handler.create_access_token(user.id, user.role)

        logger.info("access_token_refreshed", user_id=str(user.id))

        return AccessTokenResponse(
            access_token=access_token,
            expires_in=jwt_handler.get_token_expiry_seconds(),
        )

    async def logout(self, refresh_token: str) -> None:
        """
        Logout user by revoking refresh token.
        """
        query = select(RefreshToken).where(RefreshToken.token == refresh_token)
        token_record = await self._session.scalar(query)

        if token_record and not token_record.revoked:
            token_record.revoked = True
            token_record.revoked_at = datetime.now(timezone.utc)
            await self._session.commit()
            logger.info("user_logged_out", user_id=str(token_record.user_id))

    async def logout_all_sessions(self, user_id: UUID) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Returns count of revoked tokens.
        """
        query = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
        )
        result = await self._session.scalars(query)
        tokens = result.all()

        now = datetime.now(timezone.utc)
        for token in tokens:
            token.revoked = True
            token.revoked_at = now

        await self._session.commit()

        logger.info("all_sessions_revoked", user_id=str(user_id), count=len(tokens))
        return len(tokens)

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change user password.
        """
        user = await self._session.get(User, user_id)
        if user is None:
            raise UserNotFoundError("User not found")

        # Verify current password
        if not password_hasher.verify(current_password, user.password_hash):
            logger.warning("password_change_failed", user_id=str(user_id))
            raise InvalidCredentialsError("Current password is incorrect")

        # Update password
        user.password_hash = password_hasher.hash(new_password)

        # Revoke all refresh tokens (force re-login)
        await self.logout_all_sessions(user_id)

        await self._session.commit()
        logger.info("password_changed", user_id=str(user_id))

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        return await self._session.get(User, user_id)

    async def _create_tokens(
        self,
        user: User,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        """Create access and refresh tokens for user."""
        # Create access token
        access_token, _ = jwt_handler.create_access_token(user.id, user.role)

        # Create refresh token
        refresh_token_value = jwt_handler.create_refresh_token()
        refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token_value,
            expires_at=jwt_handler.get_refresh_token_expiry(),
            ip_address=ip_address,
            user_agent=user_agent[:512] if user_agent else None,
        )
        self._session.add(refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_value,
            expires_in=jwt_handler.get_token_expiry_seconds(),
        )
