"""create auth tables with complete schema

Revision ID: 007_create_auth_tables
Revises: 006_rename_metadata_columns
Create Date: 2025-08-12 00:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007_create_auth_tables'
down_revision: Union[str, None] = '006_rename_metadata_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to users table if they don't exist
    try:
        op.add_column('users', sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    except Exception:
        pass  # Column already exists
    
    try:
        op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True, default=False))
    except Exception:
        pass  # Column already exists
    
    try:
        op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    except Exception:
        pass  # Column already exists
    
    # Create api_keys table if it doesn't exist
    try:
        op.create_table('api_keys',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('key_hash', sa.String(length=255), nullable=False),
            sa.Column('key_prefix', sa.String(length=8), nullable=False),
            sa.Column('client_name', sa.String(length=100), nullable=False),
            sa.Column('access_level', sa.String(length=20), nullable=False),
            sa.Column('created_by_username', sa.String(length=50), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('usage_count', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
        op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
        op.create_index(op.f('ix_api_keys_key_prefix'), 'api_keys', ['key_prefix'], unique=False)
    except Exception:
        pass  # Table already exists


def downgrade() -> None:
    # Remove added columns
    try:
        op.drop_column('users', 'settings')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'is_verified')
    except Exception:
        pass
    
    try:
        op.drop_column('users', 'updated_at')
    except Exception:
        pass
    
    # Drop api_keys table
    try:
        op.drop_table('api_keys')
    except Exception:
        pass