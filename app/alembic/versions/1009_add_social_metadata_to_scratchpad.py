"""add_social_metadata_to_scratchpad_items

Revision ID: 1009_add_social_metadata
Revises: 1008_add_link_preview_fields
Create Date: 2025-10-16 04:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '1009_add_social_metadata'
down_revision = '1008_add_link_preview_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add JSON column for social media-specific metadata (X/Twitter, Facebook, etc.)
    # Stores comprehensive data for graphical recreation of posts
    op.add_column('scratchpad_items', sa.Column('social_metadata', JSON(), nullable=True))


def downgrade():
    op.drop_column('scratchpad_items', 'social_metadata')
