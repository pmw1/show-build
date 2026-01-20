"""Fix segment_locks foreign key to cascade delete

Revision ID: 1019_fix_cascade
Revises: 1018_segment_locks
Create Date: 2026-01-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1019_fix_cascade'
down_revision = '1018_segment_locks'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing foreign key constraint
    op.drop_constraint(
        'segment_locks_rundown_item_asset_id_fkey',
        'segment_locks',
        type_='foreignkey'
    )

    # Recreate with ON DELETE CASCADE
    op.create_foreign_key(
        'segment_locks_rundown_item_asset_id_fkey',
        'segment_locks',
        'rundown_items',
        ['rundown_item_asset_id'],
        ['asset_id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop the CASCADE foreign key
    op.drop_constraint(
        'segment_locks_rundown_item_asset_id_fkey',
        'segment_locks',
        type_='foreignkey'
    )

    # Recreate without CASCADE
    op.create_foreign_key(
        'segment_locks_rundown_item_asset_id_fkey',
        'segment_locks',
        'rundown_items',
        ['rundown_item_asset_id'],
        ['asset_id']
    )
