"""Add website field to shows

Revision ID: 2eb1d08987c1
Revises: 1f2eb28593f6
Create Date: 2025-08-10 06:53:19.753304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2eb1d08987c1'
down_revision = '1f2eb28593f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add website and social_links fields to shows table
    op.add_column('shows', sa.Column('website', sa.String(500), nullable=True))
    op.add_column('shows', sa.Column('social_links', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('shows', 'social_links')
    op.drop_column('shows', 'website')