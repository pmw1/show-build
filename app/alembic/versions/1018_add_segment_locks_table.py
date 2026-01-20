"""Add segment_locks table for concurrent editing protection

Revision ID: 1018_segment_locks
Revises: 1017_add_customers_table
Create Date: 2026-01-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1018_segment_locks'
down_revision = '1017_customers'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'segment_locks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('asset_id', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('rundown_item_asset_id', sa.String(50), sa.ForeignKey('rundown_items.asset_id'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('locked_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Index for efficient cleanup of expired locks
    op.create_index('ix_segment_locks_expires_at', 'segment_locks', ['expires_at'])


def downgrade():
    op.drop_index('ix_segment_locks_expires_at', table_name='segment_locks')
    op.drop_table('segment_locks')
