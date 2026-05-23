"""add_post_idempotency_key

Revision ID: 2c9d8f4a1b77
Revises: f41c2d3e9a10
Create Date: 2026-05-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '2c9d8f4a1b77'
down_revision = 'f41c2d3e9a10'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('posts', sa.Column('idempotency_key', sa.String(length=128), nullable=True))
    op.create_unique_constraint(
        'uq_posts_user_idempotency_key',
        'posts',
        ['user_id', 'idempotency_key'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_posts_user_idempotency_key', 'posts', type_='unique')
    op.drop_column('posts', 'idempotency_key')
