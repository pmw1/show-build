"""Add whiteboard media filesystem columns

Adds media_asset_id, media_path, and media_fallback_url to whiteboard_items
for filesystem-based media storage (replacing base64 image_data).

Revision ID: g001_wb_media
Revises: None (standalone)
"""
from alembic import op
import sqlalchemy as sa

revision = 'g001_wb_media'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns for filesystem-based media storage
    op.add_column('whiteboard_items', sa.Column('media_asset_id', sa.String(50), nullable=True))
    op.add_column('whiteboard_items', sa.Column('media_path', sa.Text(), nullable=True))
    op.add_column('whiteboard_items', sa.Column('media_fallback_url', sa.Text(), nullable=True))

    # Add index on media_asset_id for fast lookups
    op.create_index('ix_whiteboard_items_media_asset_id', 'whiteboard_items', ['media_asset_id'])


def downgrade():
    op.drop_index('ix_whiteboard_items_media_asset_id', table_name='whiteboard_items')
    op.drop_column('whiteboard_items', 'media_fallback_url')
    op.drop_column('whiteboard_items', 'media_path')
    op.drop_column('whiteboard_items', 'media_asset_id')
