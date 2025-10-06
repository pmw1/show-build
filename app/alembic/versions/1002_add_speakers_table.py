"""add speakers table

Revision ID: 1002_add_speakers
Revises: 1001_add_regions_to_rundown
Create Date: 2025-10-03 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1002_add_speakers'
down_revision = '999_add_script_content_field'
branch_labels = None
depends_on = None


def upgrade():
    # Create speakers table
    op.create_table('speakers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),

        # Speech metrics
        sa.Column('wpm', sa.Float(), nullable=False, server_default='150.0'),
        sa.Column('wpm_min', sa.Float(), server_default='130.0'),
        sa.Column('wpm_max', sa.Float(), server_default='180.0'),

        # Speaker metadata
        sa.Column('role', sa.String(), server_default='host'),
        sa.Column('voice_type', sa.String()),
        sa.Column('language', sa.String(), server_default='en'),
        sa.Column('accent', sa.String()),

        # AI/TTS integration
        sa.Column('xtts_speaker_name', sa.String()),
        sa.Column('voice_sample_path', sa.String()),

        # Status and metadata
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_test_data', sa.Boolean(), server_default='false'),

        # Relationships
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id')),
        sa.Column('show_id', sa.Integer(), sa.ForeignKey('shows.id')),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_speakers_id'), 'speakers', ['id'], unique=False)
    op.create_index(op.f('ix_speakers_name'), 'speakers', ['name'], unique=False)
    op.create_index(op.f('ix_speakers_slug'), 'speakers', ['slug'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_speakers_slug'), table_name='speakers')
    op.drop_index(op.f('ix_speakers_name'), table_name='speakers')
    op.drop_index(op.f('ix_speakers_id'), table_name='speakers')
    op.drop_table('speakers')
