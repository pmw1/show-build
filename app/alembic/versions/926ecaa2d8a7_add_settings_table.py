"""add_settings_table

Revision ID: 926ecaa2d8a7
Revises: daf031ec47e1
Create Date: 2025-08-11 05:19:14.241237

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '926ecaa2d8a7'
down_revision = 'daf031ec47e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create settings table
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_settings_key'), 'settings', ['key'], unique=True)
    
    # Also rename the 'settings' column in users table to 'preferences' to avoid conflict
    op.alter_column('users', 'settings', new_column_name='preferences')


def downgrade() -> None:
    # Rename back the preferences column to settings
    op.alter_column('users', 'preferences', new_column_name='settings')
    
    # Drop settings table
    op.drop_index(op.f('ix_settings_key'), table_name='settings')
    op.drop_table('settings')