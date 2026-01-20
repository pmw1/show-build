"""add_is_core_to_content_type_settings

Revision ID: 1015_is_core_types
Revises: 1014_content_library
Create Date: 2026-01-14

Adds is_core and description columns to content_type_settings table
to support hybrid Core/Custom rundown item type system.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1015_is_core_types'
down_revision = '1014_content_library'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_core column with default False (custom types)
    op.add_column('content_type_settings',
        sa.Column('is_core', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add description column for custom type descriptions
    op.add_column('content_type_settings',
        sa.Column('description', sa.Text(), nullable=True)
    )

    # Update existing seeded types to mark them as core type settings (behavior flags only)
    # These rows store settings for core types, not the type definitions themselves
    op.execute("""
        UPDATE content_type_settings
        SET is_core = true
        WHERE type_name IN ('segment', 'interview', 'advertisement', 'promo', 'cta', 'transition', 'cold_open', 'outro')
    """)


def downgrade() -> None:
    op.drop_column('content_type_settings', 'description')
    op.drop_column('content_type_settings', 'is_core')
