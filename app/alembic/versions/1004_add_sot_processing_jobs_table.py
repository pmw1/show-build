"""add_sot_processing_jobs_table

Adds sot_processing_jobs table for tracking multi-phase SOT video processing pipeline.

Revision ID: 1004
Revises: 1003
Create Date: 2025-10-11 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1004'
down_revision = '1003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sot_processing_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('temp_job_id', sa.String(length=50), nullable=False),
        sa.Column('episode', sa.String(length=10), nullable=True),
        sa.Column('slug', sa.String(length=255), nullable=True),
        sa.Column('current_phase', sa.String(length=20), nullable=False, server_default='upload'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('celery_task_id', sa.String(length=50), nullable=True),
        sa.Column('working_directory', sa.Text(), nullable=True),
        sa.Column('final_video_path', sa.Text(), nullable=True),
        sa.Column('final_audio_path', sa.Text(), nullable=True),
        sa.Column('final_thumbnail_path', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('temp_job_id')
    )

    # Create index on temp_job_id for fast lookups
    op.create_index('idx_sot_jobs_temp_job_id', 'sot_processing_jobs', ['temp_job_id'])

    # Create index on status for filtering active jobs
    op.create_index('idx_sot_jobs_status', 'sot_processing_jobs', ['status'])


def downgrade() -> None:
    op.drop_index('idx_sot_jobs_status', table_name='sot_processing_jobs')
    op.drop_index('idx_sot_jobs_temp_job_id', table_name='sot_processing_jobs')
    op.drop_table('sot_processing_jobs')
