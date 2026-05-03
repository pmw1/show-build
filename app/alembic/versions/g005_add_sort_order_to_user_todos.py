"""Add sort_order column to user_todos for drag-drop priority ordering

Revision ID: g005_todo_sort
Revises: g004_assignee
"""
from alembic import op
import sqlalchemy as sa

revision = 'g005_todo_sort'
down_revision = 'g004_assignee'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_todos' AND column_name = 'sort_order'
            ) THEN
                ALTER TABLE user_todos ADD COLUMN sort_order INTEGER;
            END IF;
        END $$;
    """)
    # Seed sort_order for existing rows based on current sort
    # (active first, priority desc, newest first)
    op.execute("""
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       ORDER BY
                           (status = 'completed') ASC,
                           CASE priority
                               WHEN 'critical' THEN 4
                               WHEN 'high' THEN 3
                               WHEN 'normal' THEN 2
                               WHEN 'low' THEN 1
                               ELSE 0
                           END DESC,
                           created_at DESC
                   ) AS rn
            FROM user_todos
        )
        UPDATE user_todos u SET sort_order = r.rn
        FROM ranked r WHERE u.id = r.id AND u.sort_order IS NULL;
    """)


def downgrade():
    op.drop_column('user_todos', 'sort_order')
