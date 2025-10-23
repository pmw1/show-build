"""add_job_type_to_sot_processing_jobs

Adds job_type and clips_data fields to sot_processing_jobs table for routing different processing workflows.

Revision ID: 1005
Revises: 1004
Create Date: 2025-10-11 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1005'
down_revision = '1004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add asset_id column for linking to cue block
    op.add_column('sot_processing_jobs',
        sa.Column('asset_id', sa.String(length=50), nullable=True)
    )

    # Add job_type column with default 'full_process'
    op.add_column('sot_processing_jobs',
        sa.Column('job_type', sa.String(length=30), nullable=False, server_default='full_process')
    )

    # Add clips_data column for storing JSON clips array
    op.add_column('sot_processing_jobs',
        sa.Column('clips_data', sa.Text(), nullable=True)
    )

    # Create index on job_type for filtering by processing type
    op.create_index('idx_sot_jobs_job_type', 'sot_processing_jobs', ['job_type'])

    # Create index on asset_id for quick cue block lookups
    op.create_index('idx_sot_jobs_asset_id', 'sot_processing_jobs', ['asset_id'])


def downgrade() -> None:
    op.drop_index('idx_sot_jobs_asset_id', table_name='sot_processing_jobs')
    op.drop_index('idx_sot_jobs_job_type', table_name='sot_processing_jobs')
    op.drop_column('sot_processing_jobs', 'clips_data')
    op.drop_column('sot_processing_jobs', 'job_type')
    op.drop_column('sot_processing_jobs', 'asset_id')
