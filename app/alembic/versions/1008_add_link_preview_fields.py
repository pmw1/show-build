"""add_link_preview_fields_to_scratchpad_items

Revision ID: 1008_add_link_preview_fields
Revises: 1007_add_scratchpad
Create Date: 2025-10-16 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1008_add_link_preview_fields'
down_revision = '1007_add_scratchpad'
branch_labels = None
depends_on = None


def upgrade():
    # Add link preview metadata fields to scratchpad_items
    op.add_column('scratchpad_items', sa.Column('preview_title', sa.Text(), nullable=True))
    op.add_column('scratchpad_items', sa.Column('preview_description', sa.Text(), nullable=True))
    op.add_column('scratchpad_items', sa.Column('preview_image', sa.Text(), nullable=True))
    op.add_column('scratchpad_items', sa.Column('preview_domain', sa.String(length=255), nullable=True))
    op.add_column('scratchpad_items', sa.Column('preview_favicon', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('scratchpad_items', 'preview_favicon')
    op.drop_column('scratchpad_items', 'preview_domain')
    op.drop_column('scratchpad_items', 'preview_image')
    op.drop_column('scratchpad_items', 'preview_description')
    op.drop_column('scratchpad_items', 'preview_title')
