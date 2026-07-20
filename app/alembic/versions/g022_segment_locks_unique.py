"""Unique index on segment_locks.rundown_item_asset_id

A segment may only ever have ONE lock row. The column previously carried a
plain (non-unique) index, so nothing at the DB level stopped two rows for the
same segment. Every lookup in segment_locks_router.py filters on this column
and calls .first(), so duplicates make lock identity nondeterministic: one
request could check one row, renew a second, and release a third — letting two
users each believe they hold the lock on the same segment.

The acquire path is check-then-insert with no constraint between the two
steps, so two near-simultaneous requests can both pass the check and both
insert. This index closes that race: the loser now gets an IntegrityError,
which the router translates into the normal 423 Locked response.

Deduplicates before creating the index (keeping the newest lock per segment,
which is the one a live editor is heartbeating) so the migration cannot fail
on pre-existing duplicates.

Revision ID: g022_segment_locks_unique
Revises: g021_slug_history
"""
from alembic import op

revision = 'g022_segment_locks_unique'
down_revision = 'g021_slug_history'
branch_labels = None
depends_on = None


def upgrade():
    # Drop any duplicates first — keep the most recently acquired row per
    # segment. Locks are ephemeral (30s TTL), so discarding stale duplicates
    # is safe: the losing client simply re-acquires on its next heartbeat.
    op.execute("""
        DELETE FROM segment_locks a
        USING segment_locks b
        WHERE a.rundown_item_asset_id = b.rundown_item_asset_id
          AND (a.locked_at, a.id) < (b.locked_at, b.id);
    """)

    # Replace the plain index with a unique one. Guarded so a re-run (or a
    # database where this was applied by hand) is a no-op rather than an error.
    op.execute("DROP INDEX IF EXISTS ix_segment_locks_rundown_item_asset_id;")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'segment_locks'
                  AND indexname = 'ix_segment_locks_rundown_item_asset_id'
            ) THEN
                CREATE UNIQUE INDEX ix_segment_locks_rundown_item_asset_id
                    ON segment_locks (rundown_item_asset_id);
            END IF;
        END $$;
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_segment_locks_rundown_item_asset_id;")
    op.execute("""
        CREATE INDEX ix_segment_locks_rundown_item_asset_id
            ON segment_locks (rundown_item_asset_id);
    """)
