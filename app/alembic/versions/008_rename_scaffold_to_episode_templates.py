"""rename scaffold_episodes table to episode_templates

Revision ID: 008_rename_scaffold_to_episode_templates
Revises: 007_create_auth_tables
Create Date: 2025-08-12 02:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008_rename_to_episode_templates'
down_revision: Union[str, None] = '007_create_auth_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename the table
    op.rename_table('scaffold_episodes', 'episode_templates')


def downgrade() -> None:
    # Rename back to original name
    op.rename_table('episode_templates', 'scaffold_episodes')