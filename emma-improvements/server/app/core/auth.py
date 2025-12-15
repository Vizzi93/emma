"""Authentication utilities for JWT and password handling."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings

# Bcrypt configuration
BCRYPT_ROUNDS = 12


class PasswordHasher:
    """Password hashing utilities using bcrypt directly."""

    @staticmethod
    def hash(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except (ValueError, TypeError):
            return False

    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """Check if password hash needs to be updated (different rounds)."""
        try:
            # Extract rounds from hash (format: $2b$XX$...)
            current_rounds = int(hashed_password.split('$')[2])
            return current_rounds != BCRYPT_ROUNDS
        except (IndexError, ValueError):
            return True


class JWTHandler:
    """JWT token creation and validation."""

    ALGORITHM = "HS256"
    ACCESS_TOKEN_TYPE = "access"
    REFRESH_TOKEN_TYPE = "refresh"

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def _secret_key(self) -> str:
        """Get JWT secret key."""
        return self._settings.jwt_secret_key.get_secret_value()

    def create_access_token(
        self,
        user_id: UUID,
        role: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> tuple[str, datetime]:
        """
        Create a new access token.
        
        Returns tuple of (token, expires_at).
        """
        expires_delta = timedelta(minutes=self._settings.jwt_access_token_expire_minutes)
        expires_at = datetime.now(timezone.utc) + expires_delta

        payload = {
            "sub": str(user_id),
            "role": role,
            "type": self.ACCESS_TOKEN_TYPE,
            "exp": expires_at,
            "iat": datetime.now(timezone.utc),
            **(extra_claims or {}),
        }

        token = jwt.encode(payload, self._secret_key, algorithm=self.ALGORITHM)
        return token, expires_at

    def create_refresh_token(self) -> str:
        """Create a new refresh token (random string, stored in DB)."""
        return secrets.token_urlsafe(48)

    def decode_access_token(self, token: str) -> dict[str, Any] | None:
        """
        Decode and validate an access token.
        
        Returns payload dict or None if invalid.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self.ALGORITHM],
            )
            
            # Verify token type
            if payload.get("type") != self.ACCESS_TOKEN_TYPE:
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_token_expiry_seconds(self) -> int:
        """Get access token expiry in seconds."""
        return self._settings.jwt_access_token_expire_minutes * 60

    def get_refresh_token_expiry(self) -> datetime:
        """Get refresh token expiry datetime."""
        return datetime.now(timezone.utc) + timedelta(
            days=self._settings.jwt_refresh_token_expire_days
        )


# Singleton instances
password_hasher = PasswordHasher()
jwt_handler = JWTHandler()
