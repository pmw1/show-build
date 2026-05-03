"""Replace settings.key global unique with (user_id, key) per-user uniqueness.

Allows multiple users to override the same setting key. Global rows
(user_id IS NULL) are still uniquely keyed via a partial unique index.

Revision ID: g010_settings_per_user
Revises: g009_llm_notifications
"""
from alembic import op


revision = 'g010_settings_per_user'
down_revision = 'g009_llm_notifications'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DROP INDEX IF EXISTS ix_settings_key;

        CREATE INDEX IF NOT EXISTS ix_settings_key ON settings (key);

        CREATE UNIQUE INDEX IF NOT EXISTS uq_settings_user_key
            ON settings (user_id, key)
            WHERE user_id IS NOT NULL;

        CREATE UNIQUE INDEX IF NOT EXISTS uq_settings_global_key
            ON settings (key)
            WHERE user_id IS NULL;
    """)


def downgrade():
    op.execute("""
        DROP INDEX IF EXISTS uq_settings_global_key;
        DROP INDEX IF EXISTS uq_settings_user_key;
        DROP INDEX IF EXISTS ix_settings_key;
        CREATE UNIQUE INDEX ix_settings_key ON settings (key);
    """)
