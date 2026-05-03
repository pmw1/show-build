"""Add episode-level publishing metadata columns

Adds 28 new columns to the episodes table for comprehensive publishing
metadata across platforms: core description, content rating, production crew,
master publishing control, OmnyStudio, YouTube, and social media.

Revision ID: g003_ep_publish
Revises: g002_xpost_cues
"""
from alembic import op
import sqlalchemy as sa

revision = 'g003_ep_publish'
down_revision = ('b1a2c3d4e5f6', 'g002_xpost_cues')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Core Episode Description ---
    op.add_column('episodes', sa.Column('subtitle', sa.String(500), nullable=True))
    op.add_column('episodes', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('episodes', sa.Column('tags', sa.String(1000), nullable=True))
    op.add_column('episodes', sa.Column('notes', sa.Text(), nullable=True))

    # --- Content Rating ---
    op.add_column('episodes', sa.Column('explicit', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('episodes', sa.Column('content_warnings', sa.String(500), nullable=True))

    # --- Production Crew ---
    op.add_column('episodes', sa.Column('recording_date', sa.DateTime(), nullable=True))
    op.add_column('episodes', sa.Column('producer', sa.String(255), nullable=True))
    op.add_column('episodes', sa.Column('editor', sa.String(255), nullable=True))

    # --- Master Publishing Control ---
    op.add_column('episodes', sa.Column('publish_status', sa.String(20), nullable=True, server_default='draft'))
    op.add_column('episodes', sa.Column('schedule_datetime', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episodes', sa.Column('visibility', sa.String(20), nullable=True, server_default='public'))

    # --- OmnyStudio (Podcast Distribution) ---
    op.add_column('episodes', sa.Column('omny_description', sa.Text(), nullable=True))
    op.add_column('episodes', sa.Column('omny_visibility', sa.String(20), nullable=True, server_default='public'))
    op.add_column('episodes', sa.Column('omny_publish_status', sa.String(20), nullable=True, server_default='draft'))
    op.add_column('episodes', sa.Column('omny_schedule_datetime', sa.DateTime(timezone=True), nullable=True))

    # --- YouTube ---
    op.add_column('episodes', sa.Column('yt_title', sa.String(100), nullable=True))
    op.add_column('episodes', sa.Column('yt_description', sa.Text(), nullable=True))
    op.add_column('episodes', sa.Column('yt_tags', sa.String(500), nullable=True))
    op.add_column('episodes', sa.Column('yt_privacy_status', sa.String(20), nullable=True, server_default='private'))
    op.add_column('episodes', sa.Column('yt_schedule_datetime', sa.DateTime(timezone=True), nullable=True))

    # --- Social Media Promotion ---
    op.add_column('episodes', sa.Column('social_hashtags', sa.String(500), nullable=True))
    op.add_column('episodes', sa.Column('twitter_post_text', sa.Text(), nullable=True))
    op.add_column('episodes', sa.Column('twitter_schedule_datetime', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episodes', sa.Column('instagram_caption', sa.Text(), nullable=True))
    op.add_column('episodes', sa.Column('instagram_schedule_datetime', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episodes', sa.Column('facebook_post_text', sa.Text(), nullable=True))
    op.add_column('episodes', sa.Column('facebook_schedule_datetime', sa.DateTime(timezone=True), nullable=True))
    op.add_column('episodes', sa.Column('tiktok_caption', sa.Text(), nullable=True))
    op.add_column('episodes', sa.Column('tiktok_schedule_datetime', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Social Media
    op.drop_column('episodes', 'tiktok_schedule_datetime')
    op.drop_column('episodes', 'tiktok_caption')
    op.drop_column('episodes', 'facebook_schedule_datetime')
    op.drop_column('episodes', 'facebook_post_text')
    op.drop_column('episodes', 'instagram_schedule_datetime')
    op.drop_column('episodes', 'instagram_caption')
    op.drop_column('episodes', 'twitter_schedule_datetime')
    op.drop_column('episodes', 'twitter_post_text')
    op.drop_column('episodes', 'social_hashtags')

    # YouTube
    op.drop_column('episodes', 'yt_schedule_datetime')
    op.drop_column('episodes', 'yt_privacy_status')
    op.drop_column('episodes', 'yt_tags')
    op.drop_column('episodes', 'yt_description')
    op.drop_column('episodes', 'yt_title')

    # OmnyStudio
    op.drop_column('episodes', 'omny_schedule_datetime')
    op.drop_column('episodes', 'omny_publish_status')
    op.drop_column('episodes', 'omny_visibility')
    op.drop_column('episodes', 'omny_description')

    # Master Publishing Control
    op.drop_column('episodes', 'visibility')
    op.drop_column('episodes', 'schedule_datetime')
    op.drop_column('episodes', 'publish_status')

    # Production Crew
    op.drop_column('episodes', 'editor')
    op.drop_column('episodes', 'producer')
    op.drop_column('episodes', 'recording_date')

    # Content Rating
    op.drop_column('episodes', 'content_warnings')
    op.drop_column('episodes', 'explicit')

    # Core Episode Description
    op.drop_column('episodes', 'notes')
    op.drop_column('episodes', 'tags')
    op.drop_column('episodes', 'description')
    op.drop_column('episodes', 'subtitle')
