"""triggers table — configurable interval/cron/datetime/watch_folder/state_change/manual

The triggers system (cross-tool standardization, see showtime
docs/trigger-system-design.md, approved relay #708). A trigger is a ROW, not
hardcoded beat_schedule. A tick_triggers Celery task reads this table every ~30s
and enqueues the bound task_name via the enqueue-and-log path; Beat stays a pure
dispatcher. Additive: does NOT touch existing tables; the 4 hardcoded
beat_schedule entries keep working unchanged.

down_revision = g019_worker_definitions. This migration was originally drafted
against c4e378d8259e (the g015-orphan + g017 merge, relay #723), but g019 landed
on that same parent in the meantime — leaving g018 and g019 as sibling heads off
c4e378d8259e. Re-pointed onto g019 on 2026-06-04 to keep a single linear head
(verified: both showbuild + showbuild_dev DBs sit at g019_worker_definitions).
NOTE: `005_create_blueprint_templates` is a separate pre-existing FILE-LEVEL orphan
head (never applied to either DB); it is unrelated to this migration and left as-is.

Revision ID: g018_triggers_table
Revises: g019_worker_definitions
Create Date: 2026-06-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = 'g018_triggers_table'
down_revision = 'g019_worker_definitions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'triggers',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        # human label, unique (e.g. 'showtime-continuous-upload')
        sa.Column('name', sa.String(255), nullable=False, unique=True, index=True),
        # interval | cron | datetime | watch_folder | state_change | manual
        sa.Column('type', sa.String(20), nullable=False, index=True),
        # type-specific config (interval{seconds}, cron{minute,hour,...},
        # datetime{run_at}, watch_folder{path,glob,stability_seconds,...}, etc.)
        sa.Column('config', sa.JSON(), nullable=False),
        # fully-qualified Celery task name fired on trigger (send_task by name)
        sa.Column('task_name', sa.String(255), nullable=False),
        # {"args": [...], "kwargs": {...}} template passed to the task
        sa.Column('task_args', sa.JSON(), nullable=True),
        # target queue; null -> task's default route
        sa.Column('queue', sa.String(50), nullable=True),
        # the on/off switch (per-feature toggles flip this)
        sa.Column('enabled', sa.Boolean(), nullable=False,
                  server_default=sa.true(), index=True),
        # mirrors celery_job_log.category (sot/tools/ingest/backup/...)
        sa.Column('category', sa.String(50), nullable=False,
                  server_default='general'),
        # which tool owns this trigger (showtime/media-prep/show-build) — provenance
        sa.Column('owner_tool', sa.String(50), nullable=True),
        # bookkeeping
        sa.Column('last_fired_at', sa.DateTime(timezone=True), nullable=True),
        # most recent Celery task_id (joins celery_job_log.task_id)
        sa.Column('last_task_id', sa.String(255), nullable=True),
        sa.Column('fire_count', sa.Integer(), nullable=False, server_default='0'),
        # one-shot types (datetime) set this true after firing
        sa.Column('consumed', sa.Boolean(), nullable=False,
                  server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=func.now(), onupdate=func.now()),
    )


def downgrade() -> None:
    op.drop_table('triggers')
