"""Add tariff_days to subscriptions

Revision ID: 002
Revises: 001
Create Date: 2026-01-22

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.add_column('subscriptions', sa.Column('tariff_days', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_column('subscriptions', 'tariff_days')
