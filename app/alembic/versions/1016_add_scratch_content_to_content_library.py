"""add_scratch_content_to_content_library

Revision ID: 1016_scratch_content
Revises: 1015_is_core_types
Create Date: 2026-01-15

Adds scratch_content column to content_library table to support
per-item scratch/notes space in the Reusables Studio editor.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1016_scratch_content'
down_revision = '1015_is_core_types'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add scratch_content column for per-item scratch/notes
    op.add_column('content_library',
        sa.Column('scratch_content', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('content_library', 'scratch_content')
