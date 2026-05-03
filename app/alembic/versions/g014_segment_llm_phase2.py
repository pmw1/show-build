"""Add Phase 2 enrichment columns to segment_llm_data.

Phase 1 (current) does synchronous, single-pass entity extraction with a
local Ollama model. Phase 2 (this migration) is an async enrichment step
that calls Grok (X.AI) to verify roles, look up social handles, generate
short bios, build per-segment timelines, and surface fact-check flags.

All Phase 2 output lives in a single phase2_data JSONB column so the schema
stays additive and Phase 1 output remains untouched. Status / model /
timing / errors / Celery task id are tracked in dedicated columns to keep
the row queryable without unpacking JSONB.

Revision ID: g014_segment_llm_phase2
Revises: g013_legacy_cue_convert_seed
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'g014_segment_llm_phase2'
down_revision = 'g013_legacy_cue_convert_seed'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'segment_llm_data',
        sa.Column('phase2_data', postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'{}'::jsonb"))
    )
    op.add_column(
        'segment_llm_data',
        sa.Column('phase2_status', sa.String(length=20),
                  nullable=False, server_default='not_started')
    )
    op.add_column(
        'segment_llm_data',
        sa.Column('phase2_started_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'segment_llm_data',
        sa.Column('phase2_completed_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'segment_llm_data',
        sa.Column('phase2_model', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'segment_llm_data',
        sa.Column('phase2_task_id', sa.String(length=100), nullable=True)
    )
    op.add_column(
        'segment_llm_data',
        sa.Column('phase2_error', sa.Text(), nullable=True)
    )
    op.create_index(
        'ix_segment_llm_data_phase2_status',
        'segment_llm_data', ['phase2_status']
    )


def downgrade():
    op.drop_index('ix_segment_llm_data_phase2_status', table_name='segment_llm_data')
    op.drop_column('segment_llm_data', 'phase2_error')
    op.drop_column('segment_llm_data', 'phase2_task_id')
    op.drop_column('segment_llm_data', 'phase2_model')
    op.drop_column('segment_llm_data', 'phase2_completed_at')
    op.drop_column('segment_llm_data', 'phase2_started_at')
    op.drop_column('segment_llm_data', 'phase2_status')
    op.drop_column('segment_llm_data', 'phase2_data')
