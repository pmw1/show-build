"""Add current_location JSONB to users so other users can see where someone is.

Revision ID: g012_user_location
Revises: g011_user_messaging
"""
from alembic import op


revision = 'g012_user_location'
down_revision = 'g011_user_messaging'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS current_location JSONB,
            ADD COLUMN IF NOT EXISTS location_updated_at TIMESTAMPTZ;
    """)


def downgrade():
    op.execute("""
        ALTER TABLE users
            DROP COLUMN IF EXISTS location_updated_at,
            DROP COLUMN IF EXISTS current_location;
    """)
