"""User messaging + presence: add display_name/chip_color/last_seen_at to users
and create user_messages table.

Revision ID: g011_user_messaging
Revises: g010_settings_per_user
"""
from alembic import op


revision = 'g011_user_messaging'
down_revision = 'g010_settings_per_user'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS display_name VARCHAR(100),
            ADD COLUMN IF NOT EXISTS chip_color VARCHAR(40),
            ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ;

        CREATE TABLE IF NOT EXISTS user_messages (
            id BIGSERIAL PRIMARY KEY,
            from_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            to_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,  -- NULL = broadcast
            content TEXT NOT NULL,
            sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            read_at TIMESTAMPTZ,
            reply_to BIGINT REFERENCES user_messages(id) ON DELETE SET NULL
        );

        -- Inbox lookup: "what unread messages do I have?"
        CREATE INDEX IF NOT EXISTS ix_user_messages_inbox
            ON user_messages (to_user_id, read_at, sent_at DESC);

        -- Thread lookup between two users.
        CREATE INDEX IF NOT EXISTS ix_user_messages_thread
            ON user_messages (from_user_id, to_user_id, sent_at);

        -- Presence query: "who's been active recently?"
        CREATE INDEX IF NOT EXISTS ix_users_last_seen
            ON users (last_seen_at DESC NULLS LAST);
    """)


def downgrade():
    op.execute("""
        DROP INDEX IF EXISTS ix_users_last_seen;
        DROP INDEX IF EXISTS ix_user_messages_thread;
        DROP INDEX IF EXISTS ix_user_messages_inbox;
        DROP TABLE IF EXISTS user_messages;
        ALTER TABLE users
            DROP COLUMN IF EXISTS last_seen_at,
            DROP COLUMN IF EXISTS chip_color,
            DROP COLUMN IF EXISTS display_name;
    """)
