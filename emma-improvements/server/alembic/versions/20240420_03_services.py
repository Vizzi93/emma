"""Add services and check_results tables.

Revision ID: 20240420_03_services
Revises: 20240419_02_auth
Create Date: 2024-04-20
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

uuid_type = postgresql.UUID(as_uuid=True).with_variant(sa.String(length=36), "sqlite")

revision: str = "20240420_03_services"
down_revision: str = "20240419_02_auth"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Services table
    op.create_table(
        "services",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("target", sa.String(length=512), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False, default={}),
        sa.Column("interval_seconds", sa.Integer(), nullable=False, default=60),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, default=30),
        sa.Column("status", sa.String(length=32), nullable=False, default="unknown"),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("last_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_response_time_ms", sa.Float(), nullable=True),
        sa.Column("uptime_percentage", sa.Float(), nullable=False, default=0.0),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, default=0),
        sa.Column("tags", sa.JSON(), nullable=False, default=[]),
        sa.Column("group_name", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_services_status", "services", ["status"])
    op.create_index("ix_services_type", "services", ["type"])
    op.create_index("ix_services_is_active", "services", ["is_active"])

    # Check results table
    op.create_table(
        "check_results",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("service_id", uuid_type, sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_healthy", sa.Boolean(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_time_ms", sa.Float(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, default={}),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_check_results_service_checked", "check_results", ["service_id", "checked_at"])
    op.create_index("ix_check_results_checked_at", "check_results", ["checked_at"])
    op.create_index("ix_check_results_is_healthy", "check_results", ["is_healthy"])

    # SSL certificates cache table
    op.create_table(
        "ssl_certificates",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("service_id", uuid_type, sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("subject", sa.String(length=512), nullable=False),
        sa.Column("issuer", sa.String(length=512), nullable=False),
        sa.Column("serial_number", sa.String(length=128), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("days_until_expiry", sa.Integer(), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ssl_certificates_expires_at", "ssl_certificates", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_ssl_certificates_expires_at", table_name="ssl_certificates")
    op.drop_table("ssl_certificates")
    op.drop_index("ix_check_results_is_healthy", table_name="check_results")
    op.drop_index("ix_check_results_checked_at", table_name="check_results")
    op.drop_index("ix_check_results_service_checked", table_name="check_results")
    op.drop_table("check_results")
    op.drop_index("ix_services_is_active", table_name="services")
    op.drop_index("ix_services_type", table_name="services")
    op.drop_index("ix_services_status", table_name="services")
    op.drop_table("services")
