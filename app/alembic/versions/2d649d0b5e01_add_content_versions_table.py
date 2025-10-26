"""add_content_versions_table

Revision ID: 2d649d0b5e01
Revises: 1013
Create Date: 2025-10-25 12:42:39.104211

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2d649d0b5e01'
down_revision = '1013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create content_versions table
    op.create_table('content_versions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('rundown_item_id', sa.Integer(), nullable=False),
    sa.Column('asset_id', sa.String(length=50), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('script_content', sa.Text(), nullable=False),
    sa.Column('content_hash', sa.String(length=64), nullable=False),
    sa.Column('content_length', sa.Integer(), nullable=False),
    sa.Column('change_type', sa.String(length=20), nullable=False),
    sa.Column('change_summary', sa.Text(), nullable=True),
    sa.Column('created_by', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['rundown_item_id'], ['rundown_items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_versions_asset_id'), 'content_versions', ['asset_id'], unique=False)
    op.create_index(op.f('ix_content_versions_content_hash'), 'content_versions', ['content_hash'], unique=False)
    op.create_index(op.f('ix_content_versions_id'), 'content_versions', ['id'], unique=False)
    op.create_index(op.f('ix_content_versions_rundown_item_id'), 'content_versions', ['rundown_item_id'], unique=False)


def downgrade() -> None:
    # Drop content_versions table
    op.drop_index(op.f('ix_content_versions_rundown_item_id'), table_name='content_versions')
    op.drop_index(op.f('ix_content_versions_id'), table_name='content_versions')
    op.drop_index(op.f('ix_content_versions_content_hash'), table_name='content_versions')
    op.drop_index(op.f('ix_content_versions_asset_id'), table_name='content_versions')
    op.drop_table('content_versions')
