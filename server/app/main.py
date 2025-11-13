"""FastAPI application entrypoint."""

from __future__ import annotations

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.agents import router as agents_router
from app.core.config import get_settings

logger = structlog.get_logger(__name__)

settings = get_settings()

app = FastAPI(title="Emma Monitoring API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(agents_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health() -> dict[str, str]:
    """Healthcheck endpoint for readiness probes."""

    return {"status": "ok"}
