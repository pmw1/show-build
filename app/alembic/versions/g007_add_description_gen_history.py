"""Add description_gen_history JSONB column to rundown_items

Stores the full LLM generation + user feedback conversation so each
regeneration iteration has full context.

Revision ID: g007_desc_history
Revises: g006_tone_autogen
"""
from alembic import op

revision = 'g007_desc_history'
down_revision = 'g006_tone_autogen'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'rundown_items' AND column_name = 'description_gen_history'
            ) THEN
                ALTER TABLE rundown_items ADD COLUMN description_gen_history JSONB DEFAULT '[]'::jsonb;
            END IF;
        END $$;
    """)


def downgrade():
    op.drop_column('rundown_items', 'description_gen_history')
