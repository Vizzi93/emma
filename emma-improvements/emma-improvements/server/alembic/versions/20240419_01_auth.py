"""Add user authentication tables.

Revision ID: 20240419_01_auth
Revises: 20240418_01_initial
Create Date: 2024-04-19 10:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

uuid_type = postgresql.UUID(as_uuid=True).with_variant(sa.String(length=36), "sqlite")

revision: str = "20240419_01_auth"
down_revision: str = "20240418_01_initial"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="VIEWER"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint("uq_user_email", "users", ["email"])
    op.create_index("ix_user_email", "users", ["email"])

    # Refresh tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("device_info", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint("uq_refresh_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("ix_refresh_token_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_token_expires_at", "refresh_tokens", ["expires_at"])

    # Password reset tokens table
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint(
        "uq_password_reset_token_hash", "password_reset_tokens", ["token_hash"]
    )
    op.create_index("ix_password_reset_user_id", "password_reset_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_password_reset_user_id", table_name="password_reset_tokens")
    op.drop_constraint("uq_password_reset_token_hash", "password_reset_tokens", type_="unique")
    op.drop_table("password_reset_tokens")

    op.drop_index("ix_refresh_token_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_token_user_id", table_name="refresh_tokens")
    op.drop_constraint("uq_refresh_token_hash", "refresh_tokens", type_="unique")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_user_email", table_name="users")
    op.drop_constraint("uq_user_email", "users", type_="unique")
    op.drop_table("users")
