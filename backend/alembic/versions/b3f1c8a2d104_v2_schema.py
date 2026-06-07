"""v2 schema - superadmin, api keys, webhooks

Revision ID: v2_schema
Revises: aa66ff0464cb
Create Date: 2026-06-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "v2_schema"
down_revision: Union[str, None] = "aa66ff0464cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: superadmin flag, encrypted user API keys, key
    assignments per agent, and token-based webhook endpoints."""

    # Add superadmin column to users. `is_active` already exists in the
    # initial schema, so we only add the new flag here.
    op.add_column(
        "users",
        sa.Column(
            "is_superadmin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # user_api_keys — one encrypted key per (user, provider)
    op.create_table(
        "user_api_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_user_api_keys_user_id"), "user_api_keys", ["user_id"], unique=False
    )

    # agent_api_key_assignments — which keys power which agent
    op.create_table(
        "agent_api_key_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "agent_id",
            sa.Integer(),
            sa.ForeignKey("agent_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("llm_provider", sa.String(length=50), nullable=True),
        sa.Column(
            "llm_api_key_id",
            sa.Integer(),
            sa.ForeignKey("user_api_keys.id"),
            nullable=True,
        ),
        sa.Column("tts_provider", sa.String(length=50), nullable=True),
        sa.Column(
            "tts_api_key_id",
            sa.Integer(),
            sa.ForeignKey("user_api_keys.id"),
            nullable=True,
        ),
        sa.Column("stt_provider", sa.String(length=50), nullable=True),
        sa.Column(
            "stt_api_key_id",
            sa.Integer(),
            sa.ForeignKey("user_api_keys.id"),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_agent_api_key_assignments_agent_id"),
        "agent_api_key_assignments",
        ["agent_id"],
        unique=False,
    )

    # webhook_endpoints — token-based external integration
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "agent_id",
            sa.Integer(),
            sa.ForeignKey("agent_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("webhook_secret", sa.String(length=100), nullable=False),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.UniqueConstraint("webhook_secret"),
    )
    op.create_index(
        op.f("ix_webhook_endpoints_agent_id"),
        "webhook_endpoints",
        ["agent_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_webhook_endpoints_user_id"),
        "webhook_endpoints",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_webhook_endpoints_user_id"), table_name="webhook_endpoints"
    )
    op.drop_index(
        op.f("ix_webhook_endpoints_agent_id"), table_name="webhook_endpoints"
    )
    op.drop_table("webhook_endpoints")

    op.drop_index(
        op.f("ix_agent_api_key_assignments_agent_id"),
        table_name="agent_api_key_assignments",
    )
    op.drop_table("agent_api_key_assignments")

    op.drop_index(op.f("ix_user_api_keys_user_id"), table_name="user_api_keys")
    op.drop_table("user_api_keys")

    op.drop_column("users", "is_superadmin")
