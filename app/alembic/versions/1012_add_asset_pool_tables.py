"""Add asset pool tables

Revision ID: 1012_add_asset_pool_tables
Revises: 2f98a11019e6
Create Date: 2025-01-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1012_add_asset_pool_tables'
down_revision = '2f98a11019e6'
branch_labels = None
depends_on = None


def upgrade():
    # Create asset_pool_files table
    op.create_table(
        'asset_pool_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.String(50), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('original_filename', sa.Text(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('thumbnail_path', sa.Text(), nullable=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['asset_id'], ['asset_id_registry.asset_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('asset_id')
    )
    op.create_index('idx_asset_pool_asset_id', 'asset_pool_files', ['asset_id'])
    op.create_index('idx_asset_pool_source', 'asset_pool_files', ['source'])

    # Create asset_tags table
    op.create_table(
        'asset_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.String(50), nullable=False),
        sa.Column('tag', sa.String(100), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['asset_id'], ['asset_id_registry.asset_id'], ondelete='CASCADE')
    )
    op.create_index('idx_asset_tags_asset_id', 'asset_tags', ['asset_id'])
    op.create_index('idx_asset_tags_tag', 'asset_tags', ['tag'])

    # Create whiteboard_node_links table
    op.create_table(
        'whiteboard_node_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('whiteboard_id', sa.Integer(), nullable=False),
        sa.Column('source_item_id', sa.Integer(), nullable=False),
        sa.Column('target_item_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=True),
        sa.Column('label', sa.Text(), nullable=True),
        sa.Column('color', sa.String(20), server_default='#1976d2', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['whiteboard_id'], ['whiteboards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_item_id'], ['whiteboard_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_item_id'], ['whiteboard_items.id'], ondelete='CASCADE')
    )
    op.create_index('idx_node_links_source', 'whiteboard_node_links', ['source_item_id'])
    op.create_index('idx_node_links_target', 'whiteboard_node_links', ['target_item_id'])

    # Add new columns to whiteboard_items
    op.add_column('whiteboard_items', sa.Column('asset_id', sa.String(50), nullable=True))
    op.add_column('whiteboard_items', sa.Column('parent_item_id', sa.Integer(), nullable=True))
    op.add_column('whiteboard_items', sa.Column('is_child', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('whiteboard_items', sa.Column('video_url', sa.Text(), nullable=True))
    op.add_column('whiteboard_items', sa.Column('audio_url', sa.Text(), nullable=True))
    op.add_column('whiteboard_items', sa.Column('thumbnail_url', sa.Text(), nullable=True))
    op.add_column('whiteboard_items', sa.Column('html_content', sa.Text(), nullable=True))
    op.add_column('whiteboard_items', sa.Column('code_content', sa.Text(), nullable=True))
    op.add_column('whiteboard_items', sa.Column('code_language', sa.String(50), nullable=True))
    op.add_column('whiteboard_items', sa.Column('markdown_content', sa.Text(), nullable=True))
    op.add_column('whiteboard_items', sa.Column('file_url', sa.Text(), nullable=True))
    op.add_column('whiteboard_items', sa.Column('mime_type', sa.String(100), nullable=True))
    op.add_column('whiteboard_items', sa.Column('file_size', sa.BigInteger(), nullable=True))
    op.add_column('whiteboard_items', sa.Column('collapsed', sa.Boolean(), server_default='false', nullable=True))

    # Add foreign keys
    op.create_foreign_key(
        'fk_whiteboard_items_asset_id',
        'whiteboard_items', 'asset_id_registry',
        ['asset_id'], ['asset_id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_whiteboard_items_parent_item_id',
        'whiteboard_items', 'whiteboard_items',
        ['parent_item_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop foreign keys from whiteboard_items
    op.drop_constraint('fk_whiteboard_items_parent_item_id', 'whiteboard_items', type_='foreignkey')
    op.drop_constraint('fk_whiteboard_items_asset_id', 'whiteboard_items', type_='foreignkey')

    # Drop new columns from whiteboard_items
    op.drop_column('whiteboard_items', 'collapsed')
    op.drop_column('whiteboard_items', 'file_size')
    op.drop_column('whiteboard_items', 'mime_type')
    op.drop_column('whiteboard_items', 'file_url')
    op.drop_column('whiteboard_items', 'markdown_content')
    op.drop_column('whiteboard_items', 'code_language')
    op.drop_column('whiteboard_items', 'code_content')
    op.drop_column('whiteboard_items', 'html_content')
    op.drop_column('whiteboard_items', 'thumbnail_url')
    op.drop_column('whiteboard_items', 'audio_url')
    op.drop_column('whiteboard_items', 'video_url')
    op.drop_column('whiteboard_items', 'is_child')
    op.drop_column('whiteboard_items', 'parent_item_id')
    op.drop_column('whiteboard_items', 'asset_id')

    # Drop tables
    op.drop_index('idx_node_links_target', table_name='whiteboard_node_links')
    op.drop_index('idx_node_links_source', table_name='whiteboard_node_links')
    op.drop_table('whiteboard_node_links')

    op.drop_index('idx_asset_tags_tag', table_name='asset_tags')
    op.drop_index('idx_asset_tags_asset_id', table_name='asset_tags')
    op.drop_table('asset_tags')

    op.drop_index('idx_asset_pool_source', table_name='asset_pool_files')
    op.drop_index('idx_asset_pool_asset_id', table_name='asset_pool_files')
    op.drop_table('asset_pool_files')
