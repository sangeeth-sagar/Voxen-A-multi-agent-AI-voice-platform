"""recreate agent_tools table, add tool columns to api_calls

Revision ID: 009
Revises: 008
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agent_tools")

    op.create_table(
        "agent_tools",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_id", sa.Integer(),
                  sa.ForeignKey("agent_configs.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("parameters_schema", sa.JSON(), nullable=False, default=dict),
        sa.Column("target_url", sa.String(500), nullable=False),
        sa.Column("http_method", sa.String(10), nullable=False, server_default=sa.text("'POST'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "name", name="uq_agent_tools_agent_name"),
    )

    op.add_column(
        "api_calls",
        sa.Column("tool_name", sa.String(), nullable=True),
    )
    op.add_column(
        "api_calls",
        sa.Column("tool_target_url", sa.String(), nullable=True),
    )
    op.add_column(
        "api_calls",
        sa.Column("tool_status_code", sa.Integer(), nullable=True),
    )
    op.add_column(
        "api_calls",
        sa.Column("tool_latency_ms", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("api_calls", "tool_latency_ms")
    op.drop_column("api_calls", "tool_status_code")
    op.drop_column("api_calls", "tool_target_url")
    op.drop_column("api_calls", "tool_name")

    op.execute("DROP TABLE IF EXISTS agent_tools")
