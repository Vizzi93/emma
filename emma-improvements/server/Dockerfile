# ============================================================
# eMMA Backend Dockerfile
# ============================================================
# Multi-stage build for minimal, secure production image
# ============================================================

# === Stage 1: Builder ===
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip wheel --no-cache-dir --wheel-dir=/build/wheels -e .

# === Stage 2: Production ===
FROM python:3.12-slim as production

# Security: Run as non-root user
RUN groupadd --gid 1000 emma \
    && useradd --uid 1000 --gid emma --shell /bin/bash --create-home emma

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY --chown=emma:emma app/ ./app/
COPY --chown=emma:emma alembic/ ./alembic/
COPY --chown=emma:emma alembic.ini ./

# Security: Switch to non-root user
USER emma

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# === Stage 3: Development ===
FROM production as development

USER root

# Install dev dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

USER emma

# Development server with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
