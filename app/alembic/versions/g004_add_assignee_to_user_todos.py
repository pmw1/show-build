"""Add assignee column to user_todos table

Supports the unified work queue where todos can be assigned to
specific users or to Claude.

Revision ID: g004_assignee
Revises: g003_ep_publish
"""
from alembic import op
import sqlalchemy as sa

revision = 'g004_assignee'
down_revision = 'g003_ep_publish'
branch_labels = None
depends_on = None


def upgrade():
    # Column may already exist (added via direct SQL earlier)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_todos' AND column_name = 'assignee'
            ) THEN
                ALTER TABLE user_todos ADD COLUMN assignee VARCHAR(100);
            END IF;
        END $$;
    """)


def downgrade():
    op.drop_column('user_todos', 'assignee')
