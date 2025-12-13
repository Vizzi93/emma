"""User management service for admin operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import password_hasher
from app.models.user import RefreshToken, User, UserRole

logger = structlog.get_logger(__name__)


class UserManagementError(Exception):
    """Base user management error."""
    pass


class UserNotFoundError(UserManagementError):
    """User not found."""
    pass


class UserExistsError(UserManagementError):
    """User already exists."""
    pass


class CannotModifySelfError(UserManagementError):
    """Cannot modify own account for certain operations."""
    pass


class UserManagementService:
    """Service for user management operations (admin only)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_users(
        self,
        include_inactive: bool = False,
        role: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[User], int]:
        """List users with optional filters."""
        query = select(User)
        count_query = select(func.count(User.id))

        if not include_inactive:
            query = query.where(User.is_active == True)
            count_query = count_query.where(User.is_active == True)

        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)

        if search:
            pattern = f"%{search}%"
            query = query.where((User.email.ilike(pattern)) | (User.full_name.ilike(pattern)))
            count_query = count_query.where((User.email.ilike(pattern)) | (User.full_name.ilike(pattern)))

        total = await self._session.scalar(count_query) or 0
        query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.scalars(query)
        return list(result.all()), total

    async def get_user(self, user_id: UUID) -> User:
        """Get user by ID."""
        user = await self._session.get(User, user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        query = select(User).where(User.email == email.lower())
        return await self._session.scalar(query)

    async def create_user(
        self, email: str, password: str, full_name: str | None = None,
        role: str = UserRole.VIEWER.value, is_active: bool = True,
    ) -> User:
        """Create a new user (admin operation)."""
        existing = await self.get_user_by_email(email)
        if existing:
            raise UserExistsError(f"User with email {email} already exists")

        if role not in [r.value for r in UserRole]:
            raise UserManagementError(f"Invalid role: {role}")

        user = User(
            email=email.lower(),
            password_hash=password_hasher.hash(password),
            full_name=full_name,
            role=role,
            is_active=is_active,
            is_verified=True,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        logger.info("user_created_by_admin", user_id=str(user.id), email=email, role=role)
        return user

    async def update_user(self, user_id: UUID, current_user_id: UUID, **updates: Any) -> User:
        """Update user details."""
        user = await self.get_user(user_id)
        allowed_fields = {"full_name", "role", "is_active", "is_verified"}

        if user_id == current_user_id and "role" in updates:
            raise CannotModifySelfError("Cannot change your own role")
        if user_id == current_user_id and updates.get("is_active") == False:
            raise CannotModifySelfError("Cannot deactivate your own account")

        for key, value in updates.items():
            if key in allowed_fields and value is not None:
                if key == "role" and value not in [r.value for r in UserRole]:
                    raise UserManagementError(f"Invalid role: {value}")
                setattr(user, key, value)

        await self._session.commit()
        await self._session.refresh(user)
        logger.info("user_updated_by_admin", user_id=str(user_id), updates=list(updates.keys()))
        return user

    async def reset_password(self, user_id: UUID, new_password: str, current_user_id: UUID) -> None:
        """Reset user password (admin operation)."""
        user = await self.get_user(user_id)
        user.password_hash = password_hasher.hash(new_password)
        if user_id != current_user_id:
            await self._revoke_all_sessions(user_id)
        await self._session.commit()
        logger.info("password_reset_by_admin", user_id=str(user_id), by_user_id=str(current_user_id))

    async def delete_user(self, user_id: UUID, current_user_id: UUID) -> None:
        """Delete a user permanently."""
        if user_id == current_user_id:
            raise CannotModifySelfError("Cannot delete your own account")
        user = await self.get_user(user_id)
        await self._revoke_all_sessions(user_id)
        await self._session.delete(user)
        await self._session.commit()
        logger.info("user_deleted_by_admin", user_id=str(user_id), by_user_id=str(current_user_id))

    async def get_user_sessions(self, user_id: UUID) -> list[RefreshToken]:
        """Get all active sessions for a user."""
        query = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        ).order_by(RefreshToken.created_at.desc())
        result = await self._session.scalars(query)
        return list(result.all())

    async def revoke_session(self, session_id: UUID, user_id: UUID) -> None:
        """Revoke a specific session."""
        query = update(RefreshToken).where(
            RefreshToken.id == session_id, RefreshToken.user_id == user_id,
        ).values(revoked=True)
        await self._session.execute(query)
        await self._session.commit()
        logger.info("session_revoked", session_id=str(session_id), user_id=str(user_id))

    async def revoke_all_user_sessions(self, user_id: UUID, current_user_id: UUID) -> int:
        """Revoke all sessions for a user."""
        query = update(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked == False,
        ).values(revoked=True)
        result = await self._session.execute(query)
        await self._session.commit()
        count = result.rowcount
        logger.info("all_sessions_revoked", user_id=str(user_id), by_user_id=str(current_user_id), count=count)
        return count

    async def _revoke_all_sessions(self, user_id: UUID) -> None:
        """Internal: Revoke all sessions for a user."""
        query = update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
        await self._session.execute(query)

    async def get_user_stats(self) -> dict[str, Any]:
        """Get user statistics for dashboard."""
        total = await self._session.scalar(select(func.count(User.id))) or 0
        active = await self._session.scalar(select(func.count(User.id)).where(User.is_active == True)) or 0
        
        role_result = await self._session.execute(select(User.role, func.count(User.id)).group_by(User.role))
        by_role = {row[0]: row[1] for row in role_result.all()}
        
        active_sessions = await self._session.scalar(select(func.count(RefreshToken.id)).where(
            RefreshToken.revoked == False, RefreshToken.expires_at > datetime.now(timezone.utc)
        )) or 0

        return {
            "total_users": total,
            "active_users": active,
            "inactive_users": total - active,
            "by_role": by_role,
            "active_sessions": active_sessions,
        }
