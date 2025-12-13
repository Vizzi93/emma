"""Initial migration - create base schema.

Revision ID: 20240418_01_initial
Revises:
Create Date: 2024-04-18 10:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20240418_01_initial"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Initial schema setup - base tables will be created by subsequent migrations
    pass


def downgrade() -> None:
    pass
