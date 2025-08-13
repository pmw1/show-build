"""create_blueprint_templates

Revision ID: 005_create_blueprint_templates
Revises: 926ecaa2d8a7
Create Date: 2025-08-12 03:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_create_blueprint_templates'
down_revision = '926ecaa2d8a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create blueprint_templates table
    op.create_table(
        'blueprint_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=False),  # 'episode', 'show', etc.
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('metadata', sa.JSON(), nullable=True),  # Default metadata for episodes created with this template
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blueprint_templates_name'), 'blueprint_templates', ['name'], unique=True)
    op.create_index(op.f('ix_blueprint_templates_template_type'), 'blueprint_templates', ['template_type'])

    # Create blueprint_nodes table for storing directory/file structure
    op.create_table(
        'blueprint_nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('node_type', sa.String(length=20), nullable=False),  # 'directory', 'file'
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),  # File content for file nodes, null for directories
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0),
        sa.Column('is_required', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['template_id'], ['blueprint_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['blueprint_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blueprint_nodes_template_id'), 'blueprint_nodes', ['template_id'])
    op.create_index(op.f('ix_blueprint_nodes_parent_id'), 'blueprint_nodes', ['parent_id'])

    # Create scaffold_episodes table to track created episodes
    op.create_table(
        'scaffold_episodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('episode_number', sa.String(length=10), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),  # Episode-specific metadata
        sa.Column('template_id', sa.Integer(), nullable=True),  # Which blueprint was used
        sa.Column('status', sa.String(length=20), nullable=False, default='draft'),  # 'draft', 'active', 'archived'
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),  # Physical path on filesystem
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['blueprint_templates.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scaffold_episodes_episode_number'), 'scaffold_episodes', ['episode_number'], unique=True)
    op.create_index(op.f('ix_scaffold_episodes_status'), 'scaffold_episodes', ['status'])
    op.create_index(op.f('ix_scaffold_episodes_organization_id'), 'scaffold_episodes', ['organization_id'])

    # Insert default blueprint templates
    # Sunday Show template
    op.execute("""
        INSERT INTO blueprint_templates (name, description, template_type, is_active, is_default, metadata)
        VALUES (
            'Sunday Show',
            'Standard weekly Sunday show format with full rundown structure',
            'episode',
            true,
            true,
            '{"type": "sunday_show", "duration": "01:00:00", "omnystudio_program_id": "6960f124-9e8a-4716-a88c-acfe00399fd7"}'::json
        );
    """)

    op.execute("""
        INSERT INTO blueprint_templates (name, description, template_type, is_active, is_default, metadata)
        VALUES (
            'Sunday Live',
            'Live Sunday show format with streaming optimizations',
            'episode',
            true,
            false,
            '{"type": "sunday_live", "duration": "01:30:00", "streaming": true}'::json
        );
    """)

    op.execute("""
        INSERT INTO blueprint_templates (name, description, template_type, is_active, is_default, metadata)
        VALUES (
            'Generic Live',
            'General purpose live show format',
            'episode',
            true,
            false,
            '{"type": "generic_live", "duration": "01:00:00", "streaming": true}'::json
        );
    """)


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('scaffold_episodes')
    op.drop_table('blueprint_nodes')
    op.drop_table('blueprint_templates')