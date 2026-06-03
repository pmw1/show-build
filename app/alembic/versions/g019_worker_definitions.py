"""worker_definitions table — DB-backed worker fleet config

Backs the Settings → Workers config panel. Each row declares one Celery worker
(name, image/repo URL, host, queues, concurrency, gpu, flavor). This is the
DB source of truth that supersedes the static deploy/workers/workers.yml.
v1: stores definitions + the UI shows live status via `celery inspect`; it does
NOT remotely deploy.

Additive: create_table only, no backfill, safe on live DB.

Revision ID: g019_worker_definitions
Revises: c4e378d8259e
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


revision = 'g019_worker_definitions'
down_revision = 'c4e378d8259e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'worker_definitions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('image', sa.String(500), nullable=False),
        sa.Column('flavor', sa.String(40), nullable=True),
        sa.Column('host', sa.String(100), nullable=True),
        sa.Column('queues', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('concurrency', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('gpu', sa.String(20), nullable=True),
        sa.Column('mounts', sa.JSON(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False,
                  server_default=sa.true(), index=True),
        sa.Column('owner_tool', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=func.now(), onupdate=func.now()),
    )


def downgrade() -> None:
    op.drop_table('worker_definitions')
