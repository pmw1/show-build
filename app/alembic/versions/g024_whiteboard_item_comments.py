"""Add comments JSONB to whiteboard_items

Per-node user comments, available on every card type. Stored as an ordered
array of {id, author, text, ts} entries:

    [{"id": "c-1", "author": "kevin", "text": "check this", "ts": "2026-07-21T05:00:00Z"}]

Revision ID: g024_whiteboard_item_comments
Revises: g023_whiteboard_media_metadata
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'g024_whiteboard_item_comments'
down_revision = 'g023_whiteboard_media_metadata'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'whiteboard_items',
        sa.Column(
            'comments',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column('whiteboard_items', 'comments')
