"""merge_heads

Revision ID: ae4cfb4408a1
Revises: 1001_add_is_dummy_to_episodes, 1001_add_regions_to_rundown, 1002_add_speakers, 1011_add_oauth_tokens
Create Date: 2025-10-18 01:17:49.321443

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae4cfb4408a1'
down_revision = ('1001_add_is_dummy_to_episodes', '1001_add_regions_to_rundown', '1002_add_speakers', '1011_add_oauth_tokens')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass