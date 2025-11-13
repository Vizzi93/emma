"""Test configuration and fixtures."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Iterator

import pytest
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure environment before importing application modules
_tmp_dir = Path(".pytest_cache")
_tmp_dir.mkdir(exist_ok=True)
db_path = _tmp_dir / "emma_test.db"
private_key_path = _tmp_dir / "config_signing_key.pem"
public_key_path = _tmp_dir / "config_signing_key.pub.pem"

if not private_key_path.exists():
    import subprocess

    subprocess.run(["openssl", "genrsa", "-out", str(private_key_path), "2048"], check=True)
    subprocess.run(
        ["openssl", "rsa", "-in", str(private_key_path), "-pubout", "-out", str(public_key_path)],
        check=True,
    )

private_pem = private_key_path.read_text()
public_pem = public_key_path.read_text()

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
os.environ.setdefault("AGENT_BINARY_BASE_URL", "https://downloads.emma.local")
os.environ.setdefault("CONFIG_SIGNING_KEY_ID", "test-key")
os.environ.setdefault("CONFIG_SIGNING_PRIVATE_KEY", private_pem)

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

get_settings.cache_clear()
get_settings()


@pytest.fixture(scope="session")
def signing_public_key() -> str:
    """Return the PEM encoded public key for verifying JWTs."""

    return public_pem


@pytest.fixture(scope="session", autouse=True)
def prepare_database() -> Iterator[None]:
    """Create database schema for tests."""

    async def _setup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _teardown() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_setup())
    yield
    asyncio.run(_teardown())

