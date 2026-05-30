"""Add recording session storage for showtime writeback.

Showtime (vMix show-control on the Win11 VM) feeds per-take recording
data back to show-build after a session. Today the PUT /save-episode
endpoint silently drops this payload — see docs/SHOWTIME_INTEGRATION_ANALYSIS.md.

This migration lays down a fully relational model (Kevin's choice: C2)
so cross-episode analytics ("find all pickups", "average drift per
operator", "which cues fire late") are SQL-shaped, not JSONB-shaped.

Multiple sessions per episode are supported (rehearsals + retakes +
real take). Each session is independent and append-only.

Tables added:
- recording_sessions   one row per session, FK -> episodes
- recording_takes      one row per take, FK -> recording_sessions
                       (+ optional FK -> rundown_items for the segment
                        being recorded; null when freeform/uncategorized)
- take_markers         operator markers during a take
                       (FK -> recording_takes)
- take_cue_fires       cue-fire wallclock events
                       (FK -> recording_takes, optional FK -> rundown_items)

Revision history note: this revision chains from g014 (not g015) by
user direction 2026-05-20. g015_public_api_publish_lifecycle is
blocked by pre-existing duplicate (rundown_id, slug) pairs in
production and is being resolved separately. Decoupling showtime work
unblocks the integration; the two branches will be reconciled when
g015 is ready to apply.

Revision ID: g016_recording_sessions
Revises: g014_segment_llm_phase2
"""
from alembic import op
import sqlalchemy as sa


revision = 'g016_recording_sessions'
down_revision = 'g014_segment_llm_phase2'
branch_labels = None
depends_on = None


def upgrade():
    # -----------------------------------------------------------------
    # 1. recording_sessions — one row per recording session
    # -----------------------------------------------------------------
    op.create_table(
        'recording_sessions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'episode_id', sa.Integer,
            sa.ForeignKey('episodes.id', ondelete='CASCADE',
                          name='fk_recording_sessions_episode'),
            nullable=False, index=True,
        ),
        # Showtime-assigned session identifier (UUID string). Lets
        # showtime correlate its on-disk state with the DB row without
        # round-tripping our integer id.
        sa.Column('session_uuid', sa.String(64),
                  nullable=False, unique=True),
        # 'rehearsal' | 'live' | 'retake' | 'pickup-session' | other
        sa.Column('session_kind', sa.String(32),
                  nullable=False, server_default='live'),
        # 'in_progress' | 'wrapped' | 'aborted'
        sa.Column('status', sa.String(20),
                  nullable=False, server_default='in_progress'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True)),
        sa.Column('operator', sa.String(120)),
        sa.Column('host_machine', sa.String(120)),
        sa.Column('vmix_version', sa.String(60)),
        sa.Column('showtime_version', sa.String(40)),
        # Aggregate counters maintained on wrap; cheap to recompute but
        # convenient for list views.
        sa.Column('take_count', sa.Integer,
                  nullable=False, server_default='0'),
        sa.Column('total_duration_seconds', sa.Float),
        # Final on-disk locations the operator was writing to. Useful
        # for post-prod handoff. Free-form because layout may evolve.
        sa.Column('recording_root_path', sa.String(500)),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  onupdate=sa.func.now()),
    )
    op.create_index(
        'idx_recording_sessions_episode_started',
        'recording_sessions', ['episode_id', 'started_at'],
    )

    # -----------------------------------------------------------------
    # 2. recording_takes — one row per take written
    # -----------------------------------------------------------------
    op.create_table(
        'recording_takes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'session_id', sa.Integer,
            sa.ForeignKey('recording_sessions.id', ondelete='CASCADE',
                          name='fk_recording_takes_session'),
            nullable=False, index=True,
        ),
        # The rundown item this take was associated with (segment being
        # recorded). Null when the take was free-form / uncategorized.
        sa.Column(
            'rundown_item_id', sa.Integer,
            sa.ForeignKey('rundown_items.id', ondelete='SET NULL',
                          name='fk_recording_takes_rundown_item'),
            nullable=True, index=True,
        ),
        # On-disk filename without path (e.g. "0273-block-a-seg01-take03.mxf").
        # Unique per session.
        sa.Column('filename', sa.String(255), nullable=False),
        # Filename grammar parts — parsed from filename by showtime.
        # Stored explicitly so post-prod and analytics don't reparse.
        sa.Column('category', sa.String(40)),
        sa.Column('block_letter', sa.String(2)),
        sa.Column('segment_number', sa.Integer),
        sa.Column('take_number', sa.Integer),
        sa.Column('pickup_number', sa.Integer),
        # 'pending_review' | 'good' | 'discard' | 'reshoot' | 'pickup-target'
        sa.Column('status', sa.String(30),
                  nullable=False, server_default='pending_review'),
        sa.Column('started_at_wallclock', sa.DateTime(timezone=True),
                  nullable=False),
        sa.Column('ended_at_wallclock', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Float),
        sa.Column('disk_band', sa.String(20)),
        # Pickup splice metadata (mirrors .pickup.json sidecar). Null
        # for ordinary takes; populated when this take is a pickup.
        sa.Column('pickup_replaces_from_seconds', sa.Float),
        sa.Column('pickup_back_seconds', sa.Integer),
        sa.Column('pickup_splices_into_filename', sa.String(255)),
        sa.Column('operator_note', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            'session_id', 'filename',
            name='uq_recording_takes_session_filename',
        ),
    )
    op.create_index(
        'idx_recording_takes_rundown_item',
        'recording_takes', ['rundown_item_id'],
    )

    # -----------------------------------------------------------------
    # 3. take_markers — operator markers within a take
    # -----------------------------------------------------------------
    op.create_table(
        'take_markers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'take_id', sa.Integer,
            sa.ForeignKey('recording_takes.id', ondelete='CASCADE',
                          name='fk_take_markers_take'),
            nullable=False, index=True,
        ),
        # 'good' | 'bad' | 'pickup' | 'flag' | 'cut' | 'note'
        sa.Column('kind', sa.String(20), nullable=False),
        # Seconds from take start (Float keeps fractional precision).
        sa.Column('offset_seconds', sa.Float, nullable=False),
        sa.Column('wallclock', sa.DateTime(timezone=True), nullable=False),
        sa.Column('note', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    # -----------------------------------------------------------------
    # 4. take_cue_fires — cue-fire wallclock events
    # -----------------------------------------------------------------
    op.create_table(
        'take_cue_fires',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'take_id', sa.Integer,
            sa.ForeignKey('recording_takes.id', ondelete='CASCADE',
                          name='fk_take_cue_fires_take'),
            nullable=False, index=True,
        ),
        # The rundown_item the cue belongs to. Null if showtime fired
        # a cue not yet matched back to a DB rundown item (e.g. ad-hoc).
        sa.Column(
            'rundown_item_id', sa.Integer,
            sa.ForeignKey('rundown_items.id', ondelete='SET NULL',
                          name='fk_take_cue_fires_rundown_item'),
            nullable=True, index=True,
        ),
        # Showtime's cue UUID — lets us match the fire to the originating
        # cue in the show-build cue list once cues are surfaced (Gap A,
        # later migration).
        sa.Column('cue_uuid', sa.String(64)),
        # 'graphic' | 'sot' | 'fsq' | 'gfx' | 'script-cue' | other
        sa.Column('cue_type', sa.String(40)),
        sa.Column('cue_title', sa.String(255)),
        # 'manual' | 'on-cue' | 'auto' | 'scheduled'
        sa.Column('trigger', sa.String(20)),
        sa.Column('offset_seconds', sa.Float),
        sa.Column('fired_at_wallclock', sa.DateTime(timezone=True),
                  nullable=False),
        sa.Column('status', sa.String(20),
                  nullable=False, server_default='fired'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('take_cue_fires')
    op.drop_table('take_markers')
    op.drop_index(
        'idx_recording_takes_rundown_item',
        table_name='recording_takes',
    )
    op.drop_table('recording_takes')
    op.drop_index(
        'idx_recording_sessions_episode_started',
        table_name='recording_sessions',
    )
    op.drop_table('recording_sessions')
