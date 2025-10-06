"""Add is_dummy field to episodes table

Revision ID: 1001_add_is_dummy_to_episodes
Revises: 999_add_script_content_field
Create Date: 2025-10-02 04:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1001_add_is_dummy_to_episodes'
down_revision: Union[str, None] = '999_add_script_content_field'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_dummy boolean field to episodes table."""
    # Add is_dummy column to episodes table
    op.add_column('episodes', sa.Column('is_dummy', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Remove is_dummy field from episodes table."""
    # Remove is_dummy column from episodes table
    op.drop_column('episodes', 'is_dummy')