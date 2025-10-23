"""add_template_inheritance_support

Revision ID: d6bc47d3a7a8
Revises: 1012_add_asset_pool_tables
Create Date: 2025-10-19 17:23:47.883415

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd6bc47d3a7a8'
down_revision = '1012_add_asset_pool_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add parent_template_id for cascading inheritance
    op.add_column('blueprint_templates', sa.Column('parent_template_id', sa.Integer(), nullable=True))
    op.add_column('blueprint_templates', sa.Column('inheritance_mode', sa.String(length=20), nullable=False, server_default='merge'))

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_blueprint_templates_parent',
        'blueprint_templates',
        'blueprint_templates',
        ['parent_template_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Create index for parent_template_id
    op.create_index(
        'ix_blueprint_templates_parent_template_id',
        'blueprint_templates',
        ['parent_template_id']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_blueprint_templates_parent_template_id', table_name='blueprint_templates')

    # Drop foreign key
    op.drop_constraint('fk_blueprint_templates_parent', 'blueprint_templates', type_='foreignkey')

    # Drop columns
    op.drop_column('blueprint_templates', 'inheritance_mode')
    op.drop_column('blueprint_templates', 'parent_template_id')