"""Security helpers for signing agent configuration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt

from app.core.config import Settings


class ConfigSigner:
    """Sign agent configuration payloads using JWT."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._private_key = self._load_private_key(settings)

    @staticmethod
    def _load_private_key(settings: Settings) -> str:
        if settings.config_signing_private_key:
            return settings.config_signing_private_key
        if settings.config_signing_key_path:
            path = Path(settings.config_signing_key_path)
            return path.read_text(encoding="utf-8")
        raise RuntimeError("No signing key configured")

    def sign(self, payload: dict[str, Any]) -> str:
        """Return a signed JWT for the provided payload."""

        now = datetime.now(timezone.utc)
        token = jwt.encode(
            payload={**payload, "iat": int(now.timestamp())},
            key=self._private_key,
            algorithm="RS256",
            headers={"kid": self._settings.config_signing_key_id},
        )
        return token
