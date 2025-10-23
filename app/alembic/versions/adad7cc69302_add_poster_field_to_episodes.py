"""add_poster_field_to_episodes

Revision ID: adad7cc69302
Revises: fa9e1164b041
Create Date: 2025-10-22 00:28:17.123673

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adad7cc69302'
down_revision = 'fa9e1164b041'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add poster columns to episodes table for different aspect ratios
    op.add_column('episodes', sa.Column('poster_16x9', sa.String(500), nullable=True, comment='Widescreen poster (16:9) - YouTube, web'))
    op.add_column('episodes', sa.Column('poster_1x1', sa.String(500), nullable=True, comment='Square poster (1:1) - Instagram, social'))
    op.add_column('episodes', sa.Column('poster_9x16', sa.String(500), nullable=True, comment='Vertical poster (9:16) - Stories, TikTok'))
    op.add_column('episodes', sa.Column('poster_4x5', sa.String(500), nullable=True, comment='Portrait poster (4:5) - Facebook, Twitter'))


def downgrade() -> None:
    # Remove poster columns from episodes table
    op.drop_column('episodes', 'poster_16x9')
    op.drop_column('episodes', 'poster_1x1')
    op.drop_column('episodes', 'poster_9x16')
    op.drop_column('episodes', 'poster_4x5')