"""remove organization slug

Revision ID: 003
Revises: 002
Create Date: 2025-08-10 05:52:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Remove slug column from organizations table (if it exists)
    try:
        op.drop_index('ix_organizations_slug', table_name='organizations')
    except:
        pass  # Index might not exist
    
    try:
        op.drop_column('organizations', 'slug')
    except:
        pass  # Column might not exist


def downgrade():
    # Add slug column back
    op.add_column('organizations', sa.Column('slug', sa.String(100), nullable=False, server_default='temp-slug'))
    op.create_index('ix_organizations_slug', 'organizations', ['slug'], unique=True)
    
    # Remove the temporary default
    op.alter_column('organizations', 'slug', server_default=None)