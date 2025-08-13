"""Add show fields: format, logo, host, schedule

Revision ID: f05ce8ada5b1
Revises: 1dadb9179087
Create Date: 2025-08-10 06:48:37.004391

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f05ce8ada5b1'
down_revision = '1dadb9179087'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new fields to shows table
    op.add_column('shows', sa.Column('format', sa.String(100), nullable=True))
    op.add_column('shows', sa.Column('logo', sa.String(500), nullable=True))
    op.add_column('shows', sa.Column('host', sa.String(255), nullable=True))
    op.add_column('shows', sa.Column('schedule', sa.String(255), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('shows', 'schedule')
    op.drop_column('shows', 'host')
    op.drop_column('shows', 'logo')
    op.drop_column('shows', 'format')