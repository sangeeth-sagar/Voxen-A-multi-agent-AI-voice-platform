"""remove duplicate knowledge_base_text column

Revision ID: 005
Revises: v2_schema
Create Date: 2024-01-05
"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = 'v2_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('agent_configs', 'knowledge_base_text')


def downgrade() -> None:
    op.add_column('agent_configs',
        sa.Column('knowledge_base_text', sa.Text(), nullable=True))
