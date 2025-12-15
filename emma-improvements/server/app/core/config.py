"""Application configuration with validation and environment detection."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import (
    AnyHttpUrl,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application settings with full validation.
    
    All sensitive values use SecretStr to prevent accidental logging.
    Environment-specific defaults ensure secure production deployments.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === Environment ===
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode (NEVER in production)",
    )

    # === Server ===
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=3001, ge=1, le=65535, description="Server port")

    # === API ===
    api_v1_prefix: str = Field(default="/v1")
    api_title: str = Field(default="eMMA Monitoring API")
    api_version: str = Field(default="1.0.0")

    # === Database ===
    database_url: SecretStr = Field(
        ...,
        description="Async database URL (postgresql+asyncpg:// or sqlite+aiosqlite://)",
    )
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_pool_max_overflow: int = Field(default=10, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=5, le=120)

    # === Security ===
    secret_key: SecretStr = Field(
        ...,
        min_length=32,
        description="Application secret key (min 32 chars)",
    )
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="CORS allowed origins",
    )
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed Host headers",
    )

    # === Rate Limiting ===
    rate_limit_requests_per_minute: int = Field(default=60, ge=1, le=1000)
    rate_limit_burst: int = Field(default=10, ge=1, le=100)

    # === Agent Provisioning ===
    enrollment_token_ttl_hours: int = Field(default=24, ge=1, le=168)
    download_token_ttl_minutes: int = Field(default=10, ge=1, le=60)
    agent_binary_base_url: AnyHttpUrl = Field(
        ...,
        description="Base URL for agent binary downloads",
    )

    # === JWT Authentication ===
    jwt_secret_key: SecretStr = Field(
        ...,
        min_length=32,
        description="Secret key for JWT signing (min 32 chars)",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Access token expiry in minutes",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiry in days",
    )

    # === Agent Config Signing (RSA) ===
    config_signing_key_id: str = Field(
        ...,
        min_length=1,
        description="Key ID for JWT header",
    )
    config_signing_key_path: Path | None = Field(
        default=None,
        description="Path to PEM private key file",
    )
    config_signing_private_key: SecretStr | None = Field(
        default=None,
        description="PEM private key content (alternative to path)",
    )

    # === Logging ===
    log_level: str = Field(default="INFO")
    log_format: str = Field(
        default="json",
        pattern="^(json|console)$",
        description="Log output format",
    )

    # === Observability ===
    sentry_dsn: SecretStr | None = Field(
        default=None,
        description="Sentry DSN for error tracking",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated origins string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_signing_key(self) -> "Settings":
        """Ensure exactly one signing key source is provided."""
        has_path = self.config_signing_key_path is not None
        has_content = self.config_signing_private_key is not None

        if not has_path and not has_content:
            raise ValueError(
                "Either CONFIG_SIGNING_KEY_PATH or CONFIG_SIGNING_PRIVATE_KEY must be set"
            )
        if has_path and has_content:
            raise ValueError(
                "Set only one of CONFIG_SIGNING_KEY_PATH or CONFIG_SIGNING_PRIVATE_KEY"
            )
        return self

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Enforce secure defaults in production."""
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("DEBUG must be False in production")
            if "*" in self.allowed_origins:
                raise ValueError("Wildcard CORS origins not allowed in production")
            if not str(self.database_url.get_secret_value()).startswith("postgresql"):
                raise ValueError("Production requires PostgreSQL database")
        return self

    @property
    def database_url_str(self) -> str:
        """Return database URL as string for SQLAlchemy."""
        return self.database_url.get_secret_value()

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == Environment.PRODUCTION

    def get_signing_key(self) -> str:
        """Load and return the private signing key."""
        if self.config_signing_private_key:
            return self.config_signing_private_key.get_secret_value()
        if self.config_signing_key_path:
            return self.config_signing_key_path.read_text(encoding="utf-8")
        raise RuntimeError("No signing key configured")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear settings cache (useful for testing)."""
    get_settings.cache_clear()
