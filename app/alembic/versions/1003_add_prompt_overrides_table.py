"""add_prompt_overrides_table

Revision ID: 1003_add_prompt_overrides_table
Revises: 1002_add_speakers_table
Create Date: 2025-10-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

# revision identifiers, used by Alembic.
revision = '1003'
down_revision = 'b3e162fbdbed'
branch_labels = None
depends_on = None


def upgrade():
    # Create prompt_overrides table
    op.create_table(
        'prompt_overrides',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('category', sa.String(50), nullable=False, comment='Category: generate, analyze, extract, refactor, compose'),
        sa.Column('operation_key', sa.String(100), nullable=False, comment='Operation key from useLLMPrompts (e.g., generate-segment-script)'),
        sa.Column('system_prompt', sa.Text, nullable=True, comment='Override system prompt'),
        sa.Column('user_prompt_template', sa.Text, nullable=True, comment='Override user prompt template with {{variable}} placeholders'),
        sa.Column('is_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('notes', sa.Text, nullable=True, comment='Developer notes about this override'),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('metadata', JSONB, nullable=True, comment='Additional metadata'),
    )

    # Create unique constraint on category + operation_key
    op.create_index('idx_prompt_overrides_category_operation', 'prompt_overrides', ['category', 'operation_key'], unique=True)
    op.create_index('idx_prompt_overrides_enabled', 'prompt_overrides', ['is_enabled'])


def downgrade():
    op.drop_index('idx_prompt_overrides_enabled', table_name='prompt_overrides')
    op.drop_index('idx_prompt_overrides_category_operation', table_name='prompt_overrides')
    op.drop_table('prompt_overrides')
