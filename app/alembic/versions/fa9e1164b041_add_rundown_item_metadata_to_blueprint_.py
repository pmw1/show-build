"""add_rundown_item_metadata_to_blueprint_nodes

Revision ID: fa9e1164b041
Revises: d6bc47d3a7a8
Create Date: 2025-10-19 17:35:35.273633

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa9e1164b041'
down_revision = 'd6bc47d3a7a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add rundown_item_metadata column to blueprint_nodes
    op.add_column('blueprint_nodes', sa.Column('rundown_item_metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Drop rundown_item_metadata column
    op.drop_column('blueprint_nodes', 'rundown_item_metadata')