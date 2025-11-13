"""Application configuration using Pydantic settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = Field(..., alias="DATABASE_URL")
    api_v1_prefix: str = Field("/v1", alias="API_V1_PREFIX")
    enrollment_token_ttl_hours: int = Field(24, alias="ENROLLMENT_TOKEN_TTL_HOURS")
    download_token_ttl_minutes: int = Field(10, alias="DOWNLOAD_TOKEN_TTL_MINUTES")
    agent_binary_base_url: AnyHttpUrl = Field(..., alias="AGENT_BINARY_BASE_URL")
    config_signing_key_id: str = Field(..., alias="CONFIG_SIGNING_KEY_ID")
    config_signing_key_path: Optional[Path] = Field(None, alias="CONFIG_SIGNING_KEY_PATH")
    config_signing_private_key: Optional[str] = Field(
        None, alias="CONFIG_SIGNING_PRIVATE_KEY"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
