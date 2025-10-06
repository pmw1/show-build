"""Add script_content field to rundown_items

Revision ID: 999_add_script_content_field
Revises: 999_consolidate_episode_tables
Create Date: 2025-09-20 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '999_add_script_content_field'
down_revision = '999_consolidate_episode_tables'
branch_labels = None
depends_on = None

def upgrade():
    """Add script_content field to separate script content from description metadata"""

    # Add the new script_content column
    op.add_column('rundown_items', sa.Column('script_content', sa.Text(), nullable=True))

    # Migrate existing data: Move script content from description to script_content
    # This assumes that description currently contains script content
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE rundown_items
        SET script_content = description
        WHERE description IS NOT NULL
        AND description != ''
    """))

    # Clear description field since it now should only contain metadata descriptions
    # Note: We're not clearing it automatically since some may be actual descriptions
    # The application code will need to handle this separation

def downgrade():
    """Remove script_content field and restore data to description"""

    # Migrate data back to description field (if needed)
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE rundown_items
        SET description = COALESCE(script_content, description)
        WHERE script_content IS NOT NULL
    """))

    # Drop the script_content column
    op.drop_column('rundown_items', 'script_content')