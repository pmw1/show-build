"""Add show category field

Revision ID: 64f7a59415be
Revises: f05ce8ada5b1
Create Date: 2025-08-10 06:48:59.436428

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '64f7a59415be'
down_revision = 'f05ce8ada5b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add category and trailer fields to shows table
    op.add_column('shows', sa.Column('category', sa.String(100), nullable=True))
    op.add_column('shows', sa.Column('trailer', sa.String(500), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('shows', 'trailer')
    op.drop_column('shows', 'category')