"""add_parent_child_asset_architecture

Revision ID: c28bb4c36419
Revises: 2d649d0b5e01
Create Date: 2025-10-26 04:53:12.300753

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c28bb4c36419'
down_revision = '2d649d0b5e01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add parent/child relationship columns to asset_id_registry
    op.add_column('asset_id_registry', sa.Column('parent_asset_id', sa.String(50), nullable=True))
    op.add_column('asset_id_registry', sa.Column('asset_role', sa.String(20), nullable=True))
    op.add_column('asset_id_registry', sa.Column('purge_policy', sa.String(20), nullable=True, server_default='keep'))
    op.add_column('asset_id_registry', sa.Column('derivative_type', sa.String(30), nullable=True))

    # Create foreign key for parent_asset_id
    op.create_foreign_key(
        'fk_asset_parent',
        'asset_id_registry', 'asset_id_registry',
        ['parent_asset_id'], ['asset_id'],
        ondelete='SET NULL'
    )

    # Create asset_relationships table for detailed processing metadata
    op.create_table(
        'asset_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_asset_id', sa.String(50), nullable=False),
        sa.Column('child_asset_id', sa.String(50), nullable=False),
        sa.Column('relationship_type', sa.String(30), nullable=False),
        sa.Column('processing_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_asset_id'], ['asset_id_registry.asset_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['child_asset_id'], ['asset_id_registry.asset_id'], ondelete='CASCADE')
    )

    # Create indexes for performance
    op.create_index('ix_asset_relationships_parent', 'asset_relationships', ['parent_asset_id'])
    op.create_index('ix_asset_relationships_child', 'asset_relationships', ['child_asset_id'])
    op.create_index('ix_asset_registry_parent', 'asset_id_registry', ['parent_asset_id'])
    op.create_index('ix_asset_registry_role', 'asset_id_registry', ['asset_role'])

    # Add source/final asset tracking to sot_processing_jobs
    op.add_column('sot_processing_jobs', sa.Column('source_asset_id', sa.String(50), nullable=True))
    op.add_column('sot_processing_jobs', sa.Column('final_asset_id', sa.String(50), nullable=True))

    # Create foreign keys for sot_processing_jobs
    op.create_foreign_key(
        'fk_sot_source_asset',
        'sot_processing_jobs', 'asset_id_registry',
        ['source_asset_id'], ['asset_id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_sot_final_asset',
        'sot_processing_jobs', 'asset_id_registry',
        ['final_asset_id'], ['asset_id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign keys from sot_processing_jobs
    op.drop_constraint('fk_sot_final_asset', 'sot_processing_jobs', type_='foreignkey')
    op.drop_constraint('fk_sot_source_asset', 'sot_processing_jobs', type_='foreignkey')

    # Drop columns from sot_processing_jobs
    op.drop_column('sot_processing_jobs', 'final_asset_id')
    op.drop_column('sot_processing_jobs', 'source_asset_id')

    # Drop indexes
    op.drop_index('ix_asset_registry_role', 'asset_id_registry')
    op.drop_index('ix_asset_registry_parent', 'asset_id_registry')
    op.drop_index('ix_asset_relationships_child', 'asset_relationships')
    op.drop_index('ix_asset_relationships_parent', 'asset_relationships')

    # Drop asset_relationships table
    op.drop_table('asset_relationships')

    # Drop foreign key and columns from asset_id_registry
    op.drop_constraint('fk_asset_parent', 'asset_id_registry', type_='foreignkey')
    op.drop_column('asset_id_registry', 'derivative_type')
    op.drop_column('asset_id_registry', 'purge_policy')
    op.drop_column('asset_id_registry', 'asset_role')
    op.drop_column('asset_id_registry', 'parent_asset_id')