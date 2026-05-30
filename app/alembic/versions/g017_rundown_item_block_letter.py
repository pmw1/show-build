"""Add block_letter column to rundown_items.

Showtime needs explicit block grouping (A/B/C/D) to drive its filename
grammar and the cue-runner timing model. Show-build's editor today
infers blocks from ordering + advert separators, which doesn't survive
the HTTP boundary. This adds the column nullable so existing data is
untouched; editor + backfill come in a follow-up.

See docs/SHOWTIME_INTEGRATION_ANALYSIS.md Gap B.

Revision ID: g017_rundown_item_block_letter
Revises: g016_recording_sessions
"""
from alembic import op
import sqlalchemy as sa


revision = 'g017_rundown_item_block_letter'
down_revision = 'g016_recording_sessions'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'rundown_items',
        sa.Column('block_letter', sa.String(2), nullable=True),
    )


def downgrade():
    op.drop_column('rundown_items', 'block_letter')
