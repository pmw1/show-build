"""Add timezone column to shows table

Revision ID: 1020
Revises: 1019
Create Date: 2026-01-20
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1020_add_show_timezone'
down_revision = '1019_fix_cascade'
branch_labels = None
depends_on = None


def upgrade():
    # Add timezone column to shows table
    op.add_column('shows', sa.Column('timezone', sa.String(50), nullable=True, server_default='America/New_York'))


def downgrade():
    # Remove timezone column from shows table
    op.drop_column('shows', 'timezone')
