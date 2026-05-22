"""add_user_contact_fields

Revision ID: f41c2d3e9a10
Revises: e8388e567879
Create Date: 2026-05-22 19:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f41c2d3e9a10'
down_revision = 'e8388e567879'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE users SET avatar_url = '' WHERE avatar_url IS NULL")
    op.execute("UPDATE users SET bio = '' WHERE bio IS NULL")
    op.alter_column('users', 'avatar_url', nullable=False)
    op.alter_column('users', 'bio', nullable=False)
    op.add_column('users', sa.Column('phone', sa.String(length=32), server_default='', nullable=False))
    op.add_column('users', sa.Column('instagram', sa.String(length=50), server_default='', nullable=False))
    op.alter_column('users', 'phone', server_default=None)
    op.alter_column('users', 'instagram', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'instagram')
    op.drop_column('users', 'phone')
    op.alter_column('users', 'bio', nullable=True)
    op.alter_column('users', 'avatar_url', nullable=True)
