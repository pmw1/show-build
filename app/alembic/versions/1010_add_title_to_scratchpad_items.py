"""add_title_to_scratchpad_items

Revision ID: 1010_add_title_field
Revises: 1009_add_social_metadata
Create Date: 2025-10-16 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1010_add_title_field'
down_revision = '1009_add_social_metadata'
branch_labels = None
depends_on = None


def upgrade():
    # Add title field for custom card headers
    op.add_column('scratchpad_items', sa.Column('title', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('scratchpad_items', 'title')
