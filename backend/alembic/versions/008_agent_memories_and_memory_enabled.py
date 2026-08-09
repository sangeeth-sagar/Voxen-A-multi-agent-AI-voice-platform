"""create agent_memories table, add memory_enabled to agent_configs

Revision ID: 008
Revises: 007
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_memories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_id", sa.Integer(),
                  sa.ForeignKey("agent_configs.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("session_id", sa.String(), nullable=True, index=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(),
                  server_default=sa.func.now(),
                  onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "user_id", name="uq_agent_memories_agent_user"),
    )

    op.add_column(
        "agent_configs",
        sa.Column("memory_enabled", sa.Boolean(),
                  nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("agent_configs", "memory_enabled")
    op.drop_table("agent_memories")
