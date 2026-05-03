"""Add auto_description_enabled per-segment toggle

Revision ID: g008_auto_desc_enabled
Revises: g007_desc_history
"""
from alembic import op

revision = 'g008_auto_desc_enabled'
down_revision = 'g007_desc_history'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'rundown_items' AND column_name = 'auto_description_enabled'
            ) THEN
                ALTER TABLE rundown_items ADD COLUMN auto_description_enabled BOOLEAN NOT NULL DEFAULT TRUE;
            END IF;
        END $$;
    """)


def downgrade():
    op.drop_column('rundown_items', 'auto_description_enabled')
