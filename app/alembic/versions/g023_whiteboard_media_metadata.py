"""Add media_metadata JSONB to whiteboard_items

Stores extracted image metadata for whiteboard image cards:
intrinsic properties (format, dimensions, file size), EXIF when present
(camera, lens, exposure, date taken, GPS), and page-level metadata for
images dragged in from the web (source page title/description/site).

Revision ID: g023_whiteboard_media_metadata
Revises: g022_segment_locks_unique
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'g023_whiteboard_media_metadata'
down_revision = 'g022_segment_locks_unique'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'whiteboard_items',
        sa.Column(
            'media_metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column('whiteboard_items', 'media_metadata')
