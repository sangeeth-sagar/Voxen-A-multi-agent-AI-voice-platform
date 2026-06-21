"""add refresh token and activity tracking fields

Revision ID: 006
Revises: 005
Create Date: 2024-01-06
"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('refresh_token_hash', sa.String(), nullable=True))
    op.add_column('users', sa.Column('refresh_token_expires_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('last_activity_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_activity_at')
    op.drop_column('users', 'refresh_token_expires_at')
    op.drop_column('users', 'refresh_token_hash')
