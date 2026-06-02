"""merge public_api g015 into mainline g017

Revision ID: c4e378d8259e
Revises: g015_public_api_publish_lifecycle, g017_rundown_item_block_letter
Create Date: 2026-06-02 12:43:55.372882

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4e378d8259e'
down_revision = ('g015_public_api_publish_lifecycle', 'g017_rundown_item_block_letter')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass