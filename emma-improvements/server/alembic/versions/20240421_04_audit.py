"""Create audit_logs table.

Revision ID: 20240421_04
Revises: 20240420_03
Create Date: 2024-04-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "20240421_04"
down_revision: Union[str, None] = "20240420_03_services"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use String(36) for UUID compatibility with SQLite
    # Use JSON instead of JSONB for SQLite compatibility
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("resource_type", sa.String(50), index=True),
        sa.Column("resource_id", sa.String(100), index=True),
        sa.Column("user_id", sa.String(36), index=True),
        sa.Column("user_email", sa.String(255)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("request_id", sa.String(36)),
        sa.Column("description", sa.Text),
        sa.Column("details", sa.JSON),
        sa.Column("old_values", sa.JSON),
        sa.Column("new_values", sa.JSON),
        sa.Column("success", sa.Boolean, default=True),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )
    
    # Composite indexes for common queries
    op.create_index("ix_audit_logs_created_at_desc", "audit_logs", [sa.text("created_at DESC")])
    op.create_index("ix_audit_logs_user_action", "audit_logs", ["user_id", "action"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_user_action")
    op.drop_index("ix_audit_logs_created_at_desc")
    op.drop_table("audit_logs")
