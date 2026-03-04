"""add description to blueprint_nodes

Revision ID: b1a2c3d4e5f6
Revises: a3c8f4e91b2d
Create Date: 2026-02-24 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1a2c3d4e5f6'
down_revision = 'a3c8f4e91b2d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('blueprint_nodes', sa.Column('description', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('blueprint_nodes', 'description')
