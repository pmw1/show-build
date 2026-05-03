"""Add llm_notifications table for LLM task completion/failure notifications

Revision ID: g009_llm_notifications
Revises: g008_auto_desc_enabled
"""
from alembic import op
import sqlalchemy as sa

revision = 'g009_llm_notifications'
down_revision = 'g008_auto_desc_enabled'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS llm_notifications (
            id SERIAL PRIMARY KEY,
            type VARCHAR(50) NOT NULL DEFAULT 'llm_content',
            content_type VARCHAR(50) NOT NULL,
            asset_id VARCHAR(100),
            segment_title VARCHAR(500),
            episode_number VARCHAR(20),
            status VARCHAR(20) NOT NULL,
            message TEXT,
            seen BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_llm_notifications_unseen
            ON llm_notifications(seen, created_at DESC) WHERE seen = FALSE;
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS llm_notifications;")
