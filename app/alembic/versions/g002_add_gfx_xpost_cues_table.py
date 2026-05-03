"""Add gfx_xpost_cues table

Stores structured metadata for GFX-XPOST cues (full-screen X/Twitter post graphics).
All fields mirror the data available from the Twitter/X API v2.

Revision ID: g002_xpost_cues
Revises: g001_wb_media
"""
from alembic import op
import sqlalchemy as sa

revision = 'g002_xpost_cues'
down_revision = 'g001_wb_media'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'gfx_xpost_cues',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('asset_id', sa.String(50), unique=True, nullable=False, index=True),

        # Episode + rundown item linkage
        sa.Column('episode_number', sa.String(20), nullable=False, index=True),
        sa.Column('rundown_item_id', sa.Integer(), sa.ForeignKey('rundown_items.id'), nullable=True),

        # Slug
        sa.Column('slug', sa.String(255), nullable=False),

        # Author
        sa.Column('xpost_name', sa.String(255), nullable=True),
        sa.Column('xpost_username', sa.String(255), nullable=True),
        sa.Column('xpost_profile_photo', sa.Text(), nullable=True),
        sa.Column('xpost_verified', sa.Boolean(), server_default='false'),
        sa.Column('xpost_bio', sa.Text(), nullable=True),
        sa.Column('xpost_followers', sa.Integer(), nullable=True),
        sa.Column('xpost_following', sa.Integer(), nullable=True),

        # Post content
        sa.Column('xpost_post_text', sa.Text(), nullable=True),
        sa.Column('xpost_tweet_id', sa.String(50), nullable=True, index=True),
        sa.Column('xpost_conversation_id', sa.String(50), nullable=True),

        # Media
        sa.Column('xpost_media_urls', sa.JSON(), nullable=True),
        sa.Column('xpost_media_objects', sa.JSON(), nullable=True),
        sa.Column('xpost_media_local_paths', sa.JSON(), nullable=True),

        # Timing
        sa.Column('xpost_datetime', sa.DateTime(timezone=True), nullable=True),

        # Engagement
        sa.Column('xpost_view_count', sa.Integer(), nullable=True),
        sa.Column('xpost_likes', sa.Integer(), nullable=True),
        sa.Column('xpost_retweets', sa.Integer(), nullable=True),
        sa.Column('xpost_replies', sa.Integer(), nullable=True),
        sa.Column('xpost_quotes', sa.Integer(), nullable=True),
        sa.Column('xpost_bookmarks', sa.Integer(), nullable=True),

        # Source
        sa.Column('xpost_source_url', sa.Text(), nullable=True),
        sa.Column('xpost_platform', sa.String(20), server_default='x'),

        # Entities / references
        sa.Column('xpost_entities', sa.JSON(), nullable=True),
        sa.Column('xpost_referenced_tweets', sa.JSON(), nullable=True),

        # Rendering
        sa.Column('aspect_ratio', sa.String(20), nullable=True),
        sa.Column('render_mode', sa.String(20), server_default='png'),
        sa.Column('generated_asset_path', sa.Text(), nullable=True),
        sa.Column('generated_asset_url', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('duration', sa.String(20), server_default='00:00:15:00'),
        sa.Column('enumerator', sa.String(10), nullable=True),

        # Archival
        sa.Column('full_metadata', sa.JSON(), nullable=True),

        # Whiteboard origin (no FK — whiteboard_items in separate model file)
        sa.Column('whiteboard_item_id', sa.Integer(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('gfx_xpost_cues')
