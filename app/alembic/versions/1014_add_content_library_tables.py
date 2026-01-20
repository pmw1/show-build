"""add_content_library_tables

Revision ID: 1014_content_library
Revises: aff61354534c
Create Date: 2026-01-14

Adds tables for reusable content system:
- content_library: Master repository for reusable content (ads, promos, CTAs)
- content_placements: Junction table linking library items to rundowns
- content_type_settings: Admin-configurable settings per content type
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1014_content_library'
down_revision = 'aff61354534c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create content_library table
    op.create_table(
        'content_library',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.String(length=50), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('script_content', sa.Text(), nullable=True),
        sa.Column('duration', sa.String(length=20), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('customer_contact', sa.String(length=255), nullable=True),
        sa.Column('priority', sa.String(length=50), server_default='normal', nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_content_library_asset_id', 'content_library', ['asset_id'], unique=True)
    op.create_index('ix_content_library_organization_id', 'content_library', ['organization_id'])
    op.create_index('ix_content_library_item_type', 'content_library', ['item_type'])
    op.create_index('ix_content_library_is_active', 'content_library', ['is_active'])

    # Create content_placements junction table
    op.create_table(
        'content_placements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('library_item_id', sa.Integer(), nullable=False),
        sa.Column('rundown_id', sa.Integer(), nullable=False),
        sa.Column('show_id', sa.Integer(), nullable=True),
        sa.Column('episode_number', sa.String(length=20), nullable=True),
        sa.Column('order_in_rundown', sa.Integer(), nullable=False),
        sa.Column('content_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('airdate', sa.DateTime(timezone=True), nullable=True),
        sa.Column('placed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('removed_before_air', sa.Boolean(), nullable=True),
        sa.Column('placement_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['library_item_id'], ['content_library.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rundown_id'], ['rundowns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['show_id'], ['shows.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_content_placements_library_item_id', 'content_placements', ['library_item_id'])
    op.create_index('ix_content_placements_rundown_id', 'content_placements', ['rundown_id'])
    op.create_index('ix_content_placements_show_id', 'content_placements', ['show_id'])
    op.create_index('ix_content_placements_episode_number', 'content_placements', ['episode_number'])
    op.create_index('ix_content_placements_removed_at', 'content_placements', ['removed_at'])

    # Create content_type_settings table
    op.create_table(
        'content_type_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type_name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_reusable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('default_duration', sa.String(length=20), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_content_type_settings_type_name', 'content_type_settings', ['type_name'], unique=True)
    op.create_index('ix_content_type_settings_organization_id', 'content_type_settings', ['organization_id'])


def downgrade() -> None:
    # Drop content_type_settings table
    op.drop_index('ix_content_type_settings_organization_id', table_name='content_type_settings')
    op.drop_index('ix_content_type_settings_type_name', table_name='content_type_settings')
    op.drop_table('content_type_settings')

    # Drop content_placements table
    op.drop_index('ix_content_placements_removed_at', table_name='content_placements')
    op.drop_index('ix_content_placements_episode_number', table_name='content_placements')
    op.drop_index('ix_content_placements_show_id', table_name='content_placements')
    op.drop_index('ix_content_placements_rundown_id', table_name='content_placements')
    op.drop_index('ix_content_placements_library_item_id', table_name='content_placements')
    op.drop_table('content_placements')

    # Drop content_library table
    op.drop_index('ix_content_library_is_active', table_name='content_library')
    op.drop_index('ix_content_library_item_type', table_name='content_library')
    op.drop_index('ix_content_library_organization_id', table_name='content_library')
    op.drop_index('ix_content_library_asset_id', table_name='content_library')
    op.drop_table('content_library')
