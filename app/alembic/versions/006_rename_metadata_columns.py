"""rename metadata columns to avoid reserved names

Revision ID: 006_rename_metadata_columns
Revises: 005_create_blueprint_templates
Create Date: 2025-08-12 00:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_rename_metadata_columns'
down_revision: Union[str, None] = '005_create_blueprint_templates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename metadata column in blueprint_templates to template_metadata
    op.alter_column('blueprint_templates', 'metadata', new_column_name='template_metadata')
    
    # Rename metadata column in scaffold_episodes to episode_metadata
    op.alter_column('scaffold_episodes', 'metadata', new_column_name='episode_metadata')


def downgrade() -> None:
    # Rename back to original names
    op.alter_column('blueprint_templates', 'template_metadata', new_column_name='metadata')
    op.alter_column('scaffold_episodes', 'episode_metadata', new_column_name='metadata')