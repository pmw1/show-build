"""Capture inbox table for external contributions (Chrome extension / PWA)

External clients (the capture-extension/ Chrome extension, later a phone PWA
share-target) cannot safely append whiteboard cards — the board save is a full
delete-and-reinsert. Captures land in this inbox instead; the whiteboard UI
drains pending rows into real cards and acks them only after a successful
board save (docs/CAPTURE_INBOX_HANDOFF.md). Media referenced by a capture is
already in the pool (asset_pool_files), so nothing is stranded if never acked.

Revision ID: g026_whiteboard_captures
Revises: g025_xpost_capture_render
Create Date: 2026-07-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'g026_whiteboard_captures'
down_revision = 'g025_xpost_capture_render'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'whiteboard_captures',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('episode_number', sa.String(length=4), nullable=False),
        sa.Column('client_capture_id', sa.String(length=64), nullable=True),
        sa.Column('capture_kind', sa.String(length=20), nullable=False),
        sa.Column('item_type', sa.String(length=20), nullable=False),
        sa.Column('intended_cue_type', sa.String(length=10), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('preview_title', sa.Text(), nullable=True),
        sa.Column('preview_description', sa.Text(), nullable=True),
        sa.Column('preview_image', sa.Text(), nullable=True),
        sa.Column('preview_domain', sa.String(length=255), nullable=True),
        sa.Column('preview_favicon', sa.Text(), nullable=True),
        sa.Column('social_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('media_asset_id', sa.String(length=50), nullable=True),
        sa.Column('media_path', sa.Text(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('media_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extra_assets', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='processing'),
        sa.Column('error', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processing_job_id', sa.String(length=50), nullable=True),
        sa.Column('source', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('placed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('client_capture_id', name='uq_wb_captures_client_id'),
    )
    op.create_index('ix_whiteboard_captures_id', 'whiteboard_captures', ['id'])
    op.create_index('ix_whiteboard_captures_episode_number', 'whiteboard_captures', ['episode_number'])
    op.create_index('ix_whiteboard_captures_media_asset_id', 'whiteboard_captures', ['media_asset_id'])
    op.create_index('ix_whiteboard_captures_status', 'whiteboard_captures', ['status'])
    op.create_index('ix_wb_captures_ep_status', 'whiteboard_captures', ['episode_number', 'status'])


def downgrade():
    op.drop_index('ix_wb_captures_ep_status', table_name='whiteboard_captures')
    op.drop_index('ix_whiteboard_captures_status', table_name='whiteboard_captures')
    op.drop_index('ix_whiteboard_captures_media_asset_id', table_name='whiteboard_captures')
    op.drop_index('ix_whiteboard_captures_episode_number', table_name='whiteboard_captures')
    op.drop_index('ix_whiteboard_captures_id', table_name='whiteboard_captures')
    op.drop_table('whiteboard_captures')
