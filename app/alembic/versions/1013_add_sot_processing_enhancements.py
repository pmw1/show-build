"""add_sot_processing_enhancements

Revision ID: 1013
Revises: adad7cc69302
Create Date: 2025-10-22

Adds enhanced fields to sot_processing_jobs table for:
- Multiple thumbnail candidates with user selection
- Pre-analysis and post-analysis metadata
- Processing failure/warning reports
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1013'
down_revision = 'adad7cc69302'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to sot_processing_jobs table
    op.add_column('sot_processing_jobs',
        sa.Column('thumbnail_candidates', postgresql.JSON(astext_type=sa.Text()), nullable=True,
                  comment='Array of generated thumbnail filenames for user selection'))

    op.add_column('sot_processing_jobs',
        sa.Column('selected_thumbnail', sa.String(255), nullable=True,
                  comment='User-selected thumbnail filename'))

    op.add_column('sot_processing_jobs',
        sa.Column('pre_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True,
                  comment='Technical analysis of uploaded raw file (duration, resolution, codec, etc)'))

    op.add_column('sot_processing_jobs',
        sa.Column('post_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True,
                  comment='Technical analysis of final processed file (verification)'))

    op.add_column('sot_processing_jobs',
        sa.Column('processing_report', postgresql.JSON(astext_type=sa.Text()), nullable=True,
                  comment='Comprehensive report of all phases: successes, failures, warnings'))


def downgrade():
    # Remove columns in reverse order
    op.drop_column('sot_processing_jobs', 'processing_report')
    op.drop_column('sot_processing_jobs', 'post_analysis')
    op.drop_column('sot_processing_jobs', 'pre_analysis')
    op.drop_column('sot_processing_jobs', 'selected_thumbnail')
    op.drop_column('sot_processing_jobs', 'thumbnail_candidates')
