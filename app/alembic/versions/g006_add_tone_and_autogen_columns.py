"""Add tone classification + auto-generation columns

RundownItem gets: tone, tone_rationale, tone_confidence,
llm_generated_fields, auto_generate_attempts.
Episode gets: auto_generate_enabled.

Revision ID: g006_tone_autogen
Revises: g005_todo_sort
"""
from alembic import op
import sqlalchemy as sa

revision = 'g006_tone_autogen'
down_revision = 'g005_todo_sort'
branch_labels = None
depends_on = None


def _add_column_if_missing(table, column_name, column_sql):
    """Idempotent column add — skips if column already exists."""
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = '{column_name}'
            ) THEN
                ALTER TABLE {table} ADD COLUMN {column_sql};
            END IF;
        END $$;
    """)


def upgrade():
    # --- rundown_items ---
    _add_column_if_missing('rundown_items', 'tone',
                           "tone VARCHAR(32)")
    _add_column_if_missing('rundown_items', 'tone_rationale',
                           "tone_rationale TEXT")
    _add_column_if_missing('rundown_items', 'tone_confidence',
                           "tone_confidence FLOAT")
    _add_column_if_missing('rundown_items', 'llm_generated_fields',
                           "llm_generated_fields JSONB DEFAULT '[]'::jsonb")
    _add_column_if_missing('rundown_items', 'auto_generate_attempts',
                           "auto_generate_attempts INTEGER NOT NULL DEFAULT 0")

    # --- episodes ---
    _add_column_if_missing('episodes', 'auto_generate_enabled',
                           "auto_generate_enabled BOOLEAN NOT NULL DEFAULT TRUE")


def downgrade():
    op.drop_column('rundown_items', 'auto_generate_attempts')
    op.drop_column('rundown_items', 'llm_generated_fields')
    op.drop_column('rundown_items', 'tone_confidence')
    op.drop_column('rundown_items', 'tone_rationale')
    op.drop_column('rundown_items', 'tone')
    op.drop_column('episodes', 'auto_generate_enabled')
