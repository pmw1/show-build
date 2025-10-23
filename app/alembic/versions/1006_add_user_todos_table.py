"""add user_todos table

Revision ID: 1006_add_user_todos
Revises: b3e162fbdbed
Create Date: 2025-10-15 03:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1006_add_user_todos'
down_revision = '1005'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user_todos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('priority', sa.String(length=20), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_by', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_todos_id'), 'user_todos', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_user_todos_id'), table_name='user_todos')
    op.drop_table('user_todos')
