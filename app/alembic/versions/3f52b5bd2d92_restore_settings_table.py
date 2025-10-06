"""restore_settings_table

Revision ID: 3f52b5bd2d92
Revises: 0e73074190a2
Create Date: 2025-08-13 14:12:41.234132

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f52b5bd2d92'
down_revision = '0e73074190a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Restore the settings table that was accidentally removed
    op.create_table('settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_settings_key'), 'settings', ['key'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_settings_key'), table_name='settings')
    op.drop_table('settings')