"""add_link_preview_cache

Revision ID: 2f98a11019e6
Revises: 5765d66b2c1f
Create Date: 2025-10-18 02:07:12.695138

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f98a11019e6'
down_revision = '5765d66b2c1f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create link_preview_cache table
    op.create_table(
        'link_preview_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('url_hash', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('preview_data', sa.JSON(), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on url_hash for fast lookups
    op.create_index('idx_link_preview_url_hash', 'link_preview_cache', ['url_hash'])


def downgrade() -> None:
    op.drop_table('link_preview_cache')