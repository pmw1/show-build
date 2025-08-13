"""Add show poster field

Revision ID: 1f2eb28593f6
Revises: 3f192a2fc30b
Create Date: 2025-08-10 06:52:33.270725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1f2eb28593f6'
down_revision = '3f192a2fc30b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add poster field to shows table - URL for 1000x1000 show poster image
    op.add_column('shows', sa.Column('poster', sa.String(500), nullable=True))


def downgrade() -> None:
    # Remove the poster column
    op.drop_column('shows', 'poster')