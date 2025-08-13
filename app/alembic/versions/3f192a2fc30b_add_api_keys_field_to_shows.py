"""Add api_keys field to shows

Revision ID: 3f192a2fc30b
Revises: 64f7a59415be
Create Date: 2025-08-10 06:49:48.656476

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f192a2fc30b'
down_revision = '64f7a59415be'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add api_keys field to shows table - JSON field to store API credentials/tokens
    op.add_column('shows', sa.Column('api_keys', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove the api_keys column
    op.drop_column('shows', 'api_keys')