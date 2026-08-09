"""add auth_provider to users

Revision ID: 007
Revises: 006
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("auth_provider", sa.String(20),
                  nullable=False, server_default=sa.text("'local'")),
    )


def downgrade() -> None:
    op.drop_column("users", "auth_provider")
