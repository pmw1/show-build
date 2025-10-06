"""Add regions to rundown structure

Revision ID: 1001_add_regions_to_rundown
Revises: 999_add_script_content_field
Create Date: 2025-09-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1001_add_regions_to_rundown'
down_revision = '999_add_script_content_field'
branch_labels = None
depends_on = None

def upgrade():
    # Create regions table
    op.create_table('regions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('asset_id', sa.String(length=50), nullable=False, index=True),
        sa.Column('is_test_data', sa.Boolean(), nullable=False, default=False),
        sa.Column('rundown_id', sa.Integer(), nullable=False),
        sa.Column('region_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_in_rundown', sa.Integer(), nullable=False),
        sa.Column('estimated_duration', sa.String(length=20), nullable=True),
        sa.Column('actual_duration', sa.String(length=20), nullable=True),
        sa.Column('is_collapsible', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_collapsed', sa.Boolean(), nullable=True, default=False),
        sa.Column('allow_reorder', sa.Boolean(), nullable=True, default=True),
        sa.Column('color_theme', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['rundown_id'], ['rundowns.id'], ),
        sa.UniqueConstraint('asset_id')
    )

    # Add region_id column to rundown_items table
    op.add_column('rundown_items', sa.Column('region_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_rundown_items_region_id', 'rundown_items', 'regions', ['region_id'], ['id'])


def downgrade():
    # Remove region_id column from rundown_items
    op.drop_constraint('fk_rundown_items_region_id', 'rundown_items', type_='foreignkey')
    op.drop_column('rundown_items', 'region_id')

    # Drop regions table
    op.drop_table('regions')