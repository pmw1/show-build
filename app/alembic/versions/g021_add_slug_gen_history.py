"""Add slug_gen_history JSONB column to rundown_items

Stores the LLM slug generation + user feedback conversation (same gen-history
pattern as description_gen_history) so slug regeneration has full context.

Revision ID: g021_slug_history
Revises: g020_normalize_color_keys
"""
from alembic import op

revision = 'g021_slug_history'
down_revision = 'g020_normalize_color_keys'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'rundown_items' AND column_name = 'slug_gen_history'
            ) THEN
                ALTER TABLE rundown_items ADD COLUMN slug_gen_history JSONB DEFAULT '[]'::jsonb;
            END IF;
        END $$;
    """)


def downgrade():
    op.drop_column('rundown_items', 'slug_gen_history')
