"""Add segment_llm_data table for LLM preprocessing layer

This migration creates the segment_llm_data table which stores pre-extracted
LLM data (entities, summaries, quotes) for segments. This enables efficient
downstream AI operations by reusing extracted data instead of re-analyzing
raw content for each operation.

Revision ID: 1021_segment_llm_data
Revises: 1020_add_timezone_to_shows
Create Date: 2026-01-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1021_segment_llm_data'
down_revision = '1020_add_show_timezone'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'segment_llm_data',
        # Primary identification
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('asset_id', sa.String(50), unique=True, nullable=False, index=True),

        # Parent relationship
        sa.Column('rundown_item_id', sa.Integer(),
                  sa.ForeignKey('rundown_items.id', ondelete='CASCADE'),
                  nullable=False, index=True),

        # Tier 1: Core extracted data
        sa.Column('llm_description', sa.Text(), nullable=True),
        sa.Column('llm_summary', sa.Text(), nullable=True),
        sa.Column('key_quotes', sa.JSON(), default=list),
        sa.Column('extracted_people', sa.JSON(), default=list),
        sa.Column('extracted_organizations', sa.JSON(), default=list),
        sa.Column('extracted_institutions', sa.JSON(), default=list),
        sa.Column('extracted_topics', sa.JSON(), default=list),

        # Processing metadata
        sa.Column('source_content_hash', sa.String(64), nullable=True, index=True),
        sa.Column('extraction_model', sa.String(100), nullable=True),
        sa.Column('extraction_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),

        # Processing status
        sa.Column('processing_status', sa.String(20), default='pending', index=True),
        sa.Column('processing_tier', sa.Integer(), default=0, index=True),

        # Extensible data storage
        sa.Column('derived_data', sa.JSON(), default=dict),
        sa.Column('tier_metadata', sa.JSON(), default=dict),

        # Error tracking
        sa.Column('error_message', sa.Text(), nullable=True),

        # Review workflow
        sa.Column('needs_review', sa.Boolean(), default=False),
        sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),

        # Standard fields
        sa.Column('is_test_data', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Additional indexes for common queries
    op.create_index('ix_segment_llm_data_extraction_timestamp',
                    'segment_llm_data', ['extraction_timestamp'])
    op.create_index('ix_segment_llm_data_needs_review',
                    'segment_llm_data', ['needs_review'])


def downgrade():
    op.drop_index('ix_segment_llm_data_needs_review', table_name='segment_llm_data')
    op.drop_index('ix_segment_llm_data_extraction_timestamp', table_name='segment_llm_data')
    op.drop_table('segment_llm_data')
