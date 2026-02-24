"""add_mp3_encoding_profiles_table

Revision ID: a3c8f4e91b2d
Revises: f2b765213d1a
Create Date: 2026-02-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3c8f4e91b2d'
down_revision = 'f2b765213d1a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'mp3_encoding_profiles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bitrate', sa.String(20), nullable=False, server_default='192k'),
        sa.Column('sample_rate', sa.Integer(), nullable=False, server_default='44100'),
        sa.Column('channels', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('quality', sa.Integer(), nullable=True),
        sa.Column('normalize_audio', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Seed default profiles
    op.execute("""
        INSERT INTO mp3_encoding_profiles (name, description, bitrate, sample_rate, channels, is_default, sort_order)
        VALUES
            ('Standard (192k)', 'Good quality for podcast distribution', '192k', 44100, 2, true, 0),
            ('High Quality (320k)', 'Maximum quality MP3 encoding', '320k', 48000, 2, false, 1),
            ('Compact (128k)', 'Smaller file size for web distribution', '128k', 44100, 2, false, 2)
    """)


def downgrade() -> None:
    op.drop_table('mp3_encoding_profiles')
