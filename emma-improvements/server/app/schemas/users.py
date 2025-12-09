"""Pydantic schemas for user management."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class CreateUserRequest(BaseModel):
    """Create a new user (admin operation)."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = Field(None, max_length=255)
    role: str = Field(default="viewer", pattern="^(admin|operator|viewer)$")
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v


class UpdateUserRequest(BaseModel):
    """Update user details."""
    full_name: str | None = None
    role: str | None = Field(None, pattern="^(admin|operator|viewer)$")
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    """Reset user password."""
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v


class UserResponse(BaseModel):
    """User details response."""
    id: UUID
    email: str
    full_name: str | None
    role: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated list of users."""
    items: list[UserResponse]
    total: int
    limit: int
    offset: int


class SessionResponse(BaseModel):
    """User session details."""
    id: UUID
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class UserSessionsResponse(BaseModel):
    """User's active sessions."""
    user_id: UUID
    sessions: list[SessionResponse]
    total: int


class UserStatsResponse(BaseModel):
    """User statistics."""
    total_users: int
    active_users: int
    inactive_users: int
    by_role: dict[str, int]
    active_sessions: int
