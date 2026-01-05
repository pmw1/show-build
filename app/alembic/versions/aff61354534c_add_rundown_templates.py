"""add_rundown_templates

Revision ID: aff61354534c
Revises: c28bb4c36419
Create Date: 2025-11-24 20:21:27.174587

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'aff61354534c'
down_revision = 'c28bb4c36419'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create rundown_templates table
    op.create_table(
        'rundown_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('episode_template_id', sa.Integer(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['episode_template_id'], ['blueprint_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'episode_template_id', 'name', name='uq_rundown_template_org_episode_name')
    )
    op.create_index('ix_rundown_templates_organization_id', 'rundown_templates', ['organization_id'])
    op.create_index('ix_rundown_templates_episode_template_id', 'rundown_templates', ['episode_template_id'])

    # Create rundown_template_items table
    op.create_table(
        'rundown_template_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rundown_template_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('slug', sa.String(length=100), nullable=True),
        sa.Column('script_content', sa.Text(), nullable=True),
        sa.Column('duration', sa.String(length=20), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('item_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rundown_template_id'], ['rundown_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rundown_template_items_template_id', 'rundown_template_items', ['rundown_template_id'])
    op.create_index('ix_rundown_template_items_sort_order', 'rundown_template_items', ['rundown_template_id', 'sort_order'])

    # Add rundown_template_id column to episodes table
    op.add_column('episodes', sa.Column('rundown_template_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_episodes_rundown_template', 'episodes', 'rundown_templates', ['rundown_template_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_episodes_rundown_template_id', 'episodes', ['rundown_template_id'])


def downgrade() -> None:
    # Remove rundown_template_id from episodes
    op.drop_index('ix_episodes_rundown_template_id', table_name='episodes')
    op.drop_constraint('fk_episodes_rundown_template', 'episodes', type_='foreignkey')
    op.drop_column('episodes', 'rundown_template_id')

    # Drop rundown_template_items table
    op.drop_index('ix_rundown_template_items_sort_order', table_name='rundown_template_items')
    op.drop_index('ix_rundown_template_items_template_id', table_name='rundown_template_items')
    op.drop_table('rundown_template_items')

    # Drop rundown_templates table
    op.drop_index('ix_rundown_templates_episode_template_id', table_name='rundown_templates')
    op.drop_index('ix_rundown_templates_organization_id', table_name='rundown_templates')
    op.drop_table('rundown_templates')
