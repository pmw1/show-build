"""Consolidate episode tables: remove episodes_legacy, rename episode_templates to blueprints

Revision ID: 999_consolidate_episode_tables
Revises:
Create Date: 2025-09-16 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '999_consolidate_episode_tables'
down_revision: Union[str, None] = 'b3e162fbdbed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Consolidate episode tables:
    1. Drop episodes_legacy table (obsolete)
    2. Rename episode_templates to blueprints (clearer naming)

    This migration cleans up the architectural mess of having 3 episode tables.
    After this migration:
    - episodes: Main episode records with AssetIDs
    - blueprints: Episodes created from templates (formerly episode_templates)
    - blueprint_templates: Actual reusable templates
    """

    # Step 1: Drop episodes_legacy table (already removed from code) - skip if doesn't exist
    print("Dropping episodes_legacy table if exists...")
    op.execute("DROP TABLE IF EXISTS episodes_legacy")

    # Step 2: Rename episode_templates to blueprints
    print("Renaming episode_templates to blueprints...")
    op.rename_table('episode_templates', 'blueprints')


def downgrade() -> None:
    """
    Revert the consolidation changes.
    Note: episodes_legacy data will be lost as it was already deleted.
    """

    # Recreate episodes_legacy table structure (empty)
    print("Recreating episodes_legacy table (empty)...")
    op.create_table('episodes_legacy',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('episode_number', sa.String(4), unique=True, index=True, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('subtitle', sa.String(255), nullable=True),
        sa.Column('airdate', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(20), default='draft', nullable=False),
        sa.Column('duration', sa.String(10), nullable=True),
        sa.Column('guest', sa.String(255), nullable=True),
        sa.Column('tags', sa.JSON, default=list, nullable=True),
        sa.Column('slug', sa.String(100), nullable=True),
        sa.Column('is_test_data', sa.Boolean, default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Rename blueprints back to episode_templates
    print("Renaming blueprints back to episode_templates...")
    op.rename_table('blueprints', 'episode_templates')