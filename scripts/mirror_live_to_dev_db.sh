#!/usr/bin/env bash
#
# mirror_live_to_dev_db.sh — refresh the DEV database from a live snapshot.
#
# Drops and recreates `showbuild_dev` as a fresh copy of the live `showbuild`
# database, so the migration sandbox (the TipTap ScriptEditor dev harness) always
# starts from current real show data. Safe to run anytime: pg_dump reads live
# WITHOUT locking it; the live `showbuild` DB is never written to.
#
# Direction is HARD-CODED live -> dev and guarded so it can never run backwards.
#
# Usage:
#   scripts/mirror_live_to_dev_db.sh                 # uses defaults below
#   PG_CONTAINER=show-build-postgres scripts/mirror_live_to_dev_db.sh
#
# Intended to run on DEV container startup (see the dev compose service), not on
# the live stack.

set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-show-build-postgres}"
PG_USER="${PG_USER:-showbuild}"
LIVE_DB="${LIVE_DB:-showbuild}"
DEV_DB="${DEV_DB:-showbuild_dev}"

# --- Safety guards -----------------------------------------------------------
if [ "$DEV_DB" = "$LIVE_DB" ]; then
  echo "FATAL: DEV_DB ($DEV_DB) must differ from LIVE_DB ($LIVE_DB). Refusing." >&2
  exit 1
fi
case "$DEV_DB" in
  *dev*|*test*) : ;;  # dev/test targets only
  *)
    echo "FATAL: refusing to write to '$DEV_DB' — target must contain 'dev' or 'test'." >&2
    exit 1
    ;;
esac

echo "[mirror] $(date -Is) refreshing $DEV_DB from $LIVE_DB (container=$PG_CONTAINER)"

# Wait for postgres to accept connections (startup-hook friendly).
for i in $(seq 1 30); do
  if docker exec "$PG_CONTAINER" pg_isready -U "$PG_USER" -d "$LIVE_DB" >/dev/null 2>&1; then
    break
  fi
  echo "[mirror] waiting for postgres ($i/30)..."
  sleep 2
done

# Terminate any stale connections to the dev DB, then drop + recreate it.
docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d postgres -v ON_ERROR_STOP=1 \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DEV_DB' AND pid<>pg_backend_pid();" \
  >/dev/null 2>&1 || true
docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d postgres -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS $DEV_DB;"
docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d postgres -v ON_ERROR_STOP=1 \
  -c "CREATE DATABASE $DEV_DB OWNER $PG_USER;"

# Dump live (read-only, no lock) and pipe straight into the dev DB.
docker exec "$PG_CONTAINER" sh -c \
  "pg_dump -U '$PG_USER' -d '$LIVE_DB' --no-owner --no-acl | psql -U '$PG_USER' -d '$DEV_DB' -q -v ON_ERROR_STOP=1"

# Quick integrity echo.
docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$DEV_DB" -t -c \
  "SELECT 'rundown_items='||count(*) FROM rundown_items;" 2>/dev/null | tr -d ' '

echo "[mirror] $(date -Is) done — $DEV_DB is a fresh copy of $LIVE_DB"
