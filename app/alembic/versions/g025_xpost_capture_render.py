"""X-post capture + render columns on gfx_xpost_cues

Broadcast pipeline for X-post GFX cues (see docs/plans): immutable capture
stamp (captured_at/captured_by + full_metadata already existed), user-facing
title + attributed notes (same [{id, author, text, ts}] shape as
whiteboard_items.comments from g024), the display_sequence styling/animation
contract, and the transparent key-variant output paths for vMix alpha keying.

Revision ID: g025_xpost_capture_render
Revises: g024_whiteboard_item_comments
Create Date: 2026-07-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'g025_xpost_capture_render'
down_revision = 'g024_whiteboard_item_comments'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('gfx_xpost_cues', sa.Column('captured_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('gfx_xpost_cues', sa.Column('captured_by', sa.String(length=100), nullable=True))
    op.add_column('gfx_xpost_cues', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('gfx_xpost_cues', sa.Column('notes', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('gfx_xpost_cues', sa.Column('display_sequence', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('gfx_xpost_cues', sa.Column('generated_key_path', sa.Text(), nullable=True))
    op.add_column('gfx_xpost_cues', sa.Column('generated_key_url', sa.Text(), nullable=True))
    op.add_column('gfx_xpost_cues', sa.Column('last_render_task_id', sa.String(length=64), nullable=True))


def downgrade():
    op.drop_column('gfx_xpost_cues', 'last_render_task_id')
    op.drop_column('gfx_xpost_cues', 'generated_key_url')
    op.drop_column('gfx_xpost_cues', 'generated_key_path')
    op.drop_column('gfx_xpost_cues', 'display_sequence')
    op.drop_column('gfx_xpost_cues', 'notes')
    op.drop_column('gfx_xpost_cues', 'title')
    op.drop_column('gfx_xpost_cues', 'captured_by')
    op.drop_column('gfx_xpost_cues', 'captured_at')
