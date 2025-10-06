"""add_test_data_flags

Adds is_test_data boolean field to content tables to separate test/dummy data from production data.
All existing data will be marked as production (FALSE) by default.

Revision ID: b3e162fbdbed
Revises: 3f52b5bd2d92
Create Date: 2025-08-13 14:54:15.572715

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3e162fbdbed'
down_revision = '3f52b5bd2d92'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Content tables - high priority
    op.add_column('episodes_legacy', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('rundown_items_legacy', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('episodes', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('rundown_items', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('assets', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('organizations', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('shows', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))
    
    # System tables - lower priority
    op.add_column('users', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('processing_jobs', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))
    
    # Additional content tables
    op.add_column('cue_blocks', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('extracted_quotes', sa.Column('is_test_data', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_test_data columns in reverse order
    op.drop_column('extracted_quotes', 'is_test_data')
    op.drop_column('cue_blocks', 'is_test_data')
    op.drop_column('processing_jobs', 'is_test_data')
    op.drop_column('users', 'is_test_data')
    op.drop_column('shows', 'is_test_data')
    op.drop_column('organizations', 'is_test_data')
    op.drop_column('assets', 'is_test_data')
    op.drop_column('rundown_items', 'is_test_data')
    op.drop_column('episodes', 'is_test_data')
    op.drop_column('rundown_items_legacy', 'is_test_data')
    op.drop_column('episodes_legacy', 'is_test_data')