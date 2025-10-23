"""rename_scratchpad_to_whiteboard

Revision ID: 5765d66b2c1f
Revises: ae4cfb4408a1
Create Date: 2025-10-18 01:17:52.744270

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5765d66b2c1f'
down_revision = 'ae4cfb4408a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename scratchpads table to whiteboards
    op.rename_table('scratchpads', 'whiteboards')

    # Rename scratchpad_items table to whiteboard_items
    op.rename_table('scratchpad_items', 'whiteboard_items')

    # Rename foreign key column in whiteboard_items
    op.alter_column('whiteboard_items', 'scratchpad_id', new_column_name='whiteboard_id')


def downgrade() -> None:
    # Reverse the changes
    op.alter_column('whiteboard_items', 'whiteboard_id', new_column_name='scratchpad_id')
    op.rename_table('whiteboard_items', 'scratchpad_items')
    op.rename_table('whiteboards', 'scratchpads')