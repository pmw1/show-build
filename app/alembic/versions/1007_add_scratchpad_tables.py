"""add_scratchpad_tables

Revision ID: 1007_add_scratchpad
Revises: 1006_add_user_todos
Create Date: 2025-10-16 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1007_add_scratchpad'
down_revision = '1006_add_user_todos'
branch_labels = None
depends_on = None


def upgrade():
    # Create scratchpads table
    op.create_table(
        'scratchpads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('episode_number', sa.String(length=10), nullable=True),
        sa.Column('workspace_id', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scratchpads_episode_number', 'scratchpads', ['episode_number'])
    op.create_index('ix_scratchpads_workspace_id', 'scratchpads', ['workspace_id'])

    # Create scratchpad_items table
    op.create_table(
        'scratchpad_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scratchpad_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(length=20), nullable=False),
        sa.Column('x_position', sa.Float(), nullable=False),
        sa.Column('y_position', sa.Float(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('image_data', sa.Text(), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('z_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['scratchpad_id'], ['scratchpads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('scratchpad_items')
    op.drop_index('ix_scratchpads_workspace_id', 'scratchpads')
    op.drop_index('ix_scratchpads_episode_number', 'scratchpads')
    op.drop_table('scratchpads')
