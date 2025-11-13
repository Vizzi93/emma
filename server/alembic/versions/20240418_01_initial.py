"""Initial schema for agents and tokens."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

uuid_type = postgresql.UUID(as_uuid=True).with_variant(sa.String(length=36), "sqlite")

revision: str = "20240418_01_initial"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("host_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("os", sa.String(length=64), nullable=False),
        sa.Column("architecture", sa.String(length=64), nullable=False),
        sa.Column("sampling_interval", sa.Integer(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("modules", sa.JSON(), nullable=False),
        sa.Column("checks", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "enrollment_tokens",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("jti", sa.String(length=36), nullable=False, unique=True),
        sa.Column("agent_id", uuid_type, sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("host_id", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint("uq_enrollment_token_jti", "enrollment_tokens", ["jti"])

    op.create_table(
        "agent_download_tokens",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("token", sa.String(length=36), nullable=False, unique=True),
        sa.Column("agent_id", uuid_type, sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint("uq_agent_download_token_token", "agent_download_tokens", ["token"])
    op.create_index("ix_agent_download_token_expires_at", "agent_download_tokens", ["expires_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_agent_download_token_expires_at", table_name="agent_download_tokens")
    op.drop_constraint("uq_agent_download_token_token", "agent_download_tokens", type_="unique")
    op.drop_table("agent_download_tokens")
    op.drop_constraint("uq_enrollment_token_jti", "enrollment_tokens", type_="unique")
    op.drop_table("enrollment_tokens")
    op.drop_table("agents")
