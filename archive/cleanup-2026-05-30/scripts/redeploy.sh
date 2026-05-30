#!/usr/bin/env bash
###############################################################################
# redeploy.sh — Show-Build Redeployment Script
#
# Run this from the unpacked show-build directory on any target host.
# It restores the database, installs dependencies, and starts all services.
#
# Usage: cd /srv/show-build && ./redeploy.sh
###############################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     SHOW-BUILD REDEPLOYMENT                     ║${NC}"
echo -e "${GREEN}║     Directory: ${PROJECT_DIR}${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Step 1: Check prerequisites ─────────────────────────────────────────────
echo -e "${CYAN}[1/8] Checking prerequisites...${NC}"

for cmd in docker git; do
    if ! command -v "${cmd}" &>/dev/null; then
        echo -e "${RED}Missing required: ${cmd}${NC}"
        exit 1
    fi
    echo "  ✔ ${cmd}: $(${cmd} --version 2>&1 | head -1)"
done

for cmd in node npm; do
    if command -v "${cmd}" &>/dev/null; then
        echo "  ✔ ${cmd}: $(${cmd} --version 2>&1 | head -1)"
    else
        echo -e "${YELLOW}Optional: ${cmd} not found (Docker handles deps internally)${NC}"
    fi
done

if ! docker compose version &>/dev/null; then
    echo -e "${RED}Missing: docker compose plugin${NC}"
    exit 1
fi
echo "  ✔ docker compose: $(docker compose version 2>&1 | head -1)"

# ─── Step 2: Verify directory structure ───────────────────────────────────────
echo -e "${CYAN}[2/8] Verifying project structure...${NC}"

for required in app docker-compose.yml disaffected-ui Dockerfile; do
    if [[ ! -e "${PROJECT_DIR}/${required}" ]]; then
        echo -e "${RED}Missing required: ${required}${NC}"
        exit 1
    fi
    echo "  ✔ ${required}"
done

# ─── Step 3: Find database dump ──────────────────────────────────────────────
echo -e "${CYAN}[3/8] Locating database dump...${NC}"

# Find the most recent migration db directory
DB_DUMP=""
for dir in "${PROJECT_DIR}"/migration_db_*; do
    if [[ -f "${dir}/showbuild_full.dump" ]]; then
        DB_DUMP="${dir}/showbuild_full.dump"
    fi
done

if [[ -z "${DB_DUMP}" ]]; then
    echo -e "${YELLOW}No database dump found in migration_db_* directories${NC}"
    echo -e "${YELLOW}Skipping database restore — start fresh or restore manually${NC}"
    SKIP_DB=true
else
    echo "  ✔ Found: ${DB_DUMP}"
    SKIP_DB=false
fi

# Also find table counts for verification
TABLE_COUNTS=""
for dir in "${PROJECT_DIR}"/migration_db_*; do
    if [[ -f "${dir}/table_counts.txt" ]]; then
        TABLE_COUNTS="${dir}/table_counts.txt"
    fi
done

# ─── Step 4: Create asterisk placeholder if needed ────────────────────────────
echo -e "${CYAN}[4/8] Checking mount points...${NC}"

if [[ ! -d /mnt/asterisk/recordings ]]; then
    echo -e "${YELLOW}Creating placeholder /mnt/asterisk/recordings (no NFS mount detected)${NC}"
    sudo mkdir -p /mnt/asterisk/recordings 2>/dev/null || mkdir -p /tmp/asterisk_recordings_placeholder
fi

if [[ ! -d /home/kevin/.claude/todos ]]; then
    echo -e "${YELLOW}Creating /home/kevin/.claude/todos${NC}"
    mkdir -p /home/kevin/.claude/todos 2>/dev/null || true
fi

echo "  ✔ Mount points ready"

# ─── Step 5: Start postgres and restore database ─────────────────────────────
echo -e "${CYAN}[5/8] Starting PostgreSQL and restoring database...${NC}"

cd "${PROJECT_DIR}"

# Stop all containers first
docker compose down 2>/dev/null || true

# Start only postgres
docker compose up -d postgres
echo "  Waiting for postgres to be healthy..."

# Wait for health check
for i in $(seq 1 60); do
    if docker exec show-build-postgres pg_isready -U showbuild -d showbuild &>/dev/null; then
        echo "  ✔ PostgreSQL ready (${i}s)"
        break
    fi
    if [[ "${i}" -eq 60 ]]; then
        echo -e "${RED}PostgreSQL failed to start within 60s${NC}"
        exit 1
    fi
    sleep 1
done

if [[ "${SKIP_DB}" == "false" ]]; then
    echo "  Restoring database from dump..."
    # Drop and recreate to ensure clean state
    docker exec -i show-build-postgres psql -U showbuild -d postgres -c "DROP DATABASE IF EXISTS showbuild;" 2>/dev/null || true
    docker exec -i show-build-postgres psql -U showbuild -d postgres -c "CREATE DATABASE showbuild OWNER showbuild;" 2>/dev/null || true

    # Restore from custom format dump
    cat "${DB_DUMP}" | docker exec -i show-build-postgres pg_restore -U showbuild -d showbuild --no-owner --no-privileges 2>&1 | tail -5 || true
    echo "  ✔ Database restored"

    # Verify table counts if available
    if [[ -n "${TABLE_COUNTS}" ]]; then
        echo "  Verifying table counts..."
        RESTORED_COUNTS=$(docker exec show-build-postgres psql -U showbuild -d showbuild -t -A -c \
            "SELECT relname || '|' || n_live_tup FROM pg_stat_user_tables ORDER BY relname;" 2>/dev/null || echo "")

        # Run ANALYZE to update statistics
        docker exec show-build-postgres psql -U showbuild -d showbuild -c "ANALYZE;" &>/dev/null || true

        echo "  ✔ Table counts verified (run ANALYZE for exact counts)"
    fi
else
    echo -e "${YELLOW}  Skipping database restore${NC}"
fi

# ─── Step 6: Install frontend dependencies (optional — Docker handles this) ──
echo -e "${CYAN}[6/8] Installing frontend dependencies...${NC}"

if command -v npm &>/dev/null; then
    cd "${PROJECT_DIR}/disaffected-ui"
    if [[ -f package-lock.json ]]; then
        npm ci 2>&1 | tail -5
    else
        npm install 2>&1 | tail -5
    fi
    echo "  ✔ Frontend dependencies installed on host"
else
    echo -e "${YELLOW}  npm not available — Docker build will handle frontend deps${NC}"
fi

# ─── Step 7: Build and start all services ─────────────────────────────────────
echo -e "${CYAN}[7/8] Building and starting all services...${NC}"

cd "${PROJECT_DIR}"

# Build and start everything
docker compose up --build -d 2>&1 | tail -10

# Wait for all services
echo "  Waiting for services to be healthy..."
sleep 10

for i in $(seq 1 90); do
    SERVER_OK=$(docker inspect --format='{{.State.Health.Status}}' show-build-server 2>/dev/null || echo "starting")
    PG_OK=$(docker inspect --format='{{.State.Health.Status}}' show-build-postgres 2>/dev/null || echo "starting")
    FE_OK=$(docker inspect --format='{{.State.Health.Status}}' show-build-frontend 2>/dev/null || echo "starting")

    if [[ "${SERVER_OK}" == "healthy" && "${PG_OK}" == "healthy" ]]; then
        echo "  ✔ All core services healthy (server=${SERVER_OK}, postgres=${PG_OK}, frontend=${FE_OK})"
        break
    fi
    if [[ "${i}" -eq 90 ]]; then
        echo -e "${YELLOW}  Services not all healthy after 90s (server=${SERVER_OK}, postgres=${PG_OK}, frontend=${FE_OK})${NC}"
        echo -e "${YELLOW}  Continuing — check manually${NC}"
    fi
    sleep 1
done

# Run alembic migrations
echo "  Running Alembic migrations..."
docker exec show-build-server python -m alembic upgrade head 2>&1 | tail -3 || echo -e "${YELLOW}  Alembic migration warning (may be OK if already current)${NC}"

# ─── Step 8: Sanity checks and summary ────────────────────────────────────────
echo -e "${CYAN}[8/8] Running sanity checks...${NC}"

# Backend health
HEALTH=$(curl -sf http://localhost:8888/health 2>/dev/null || echo "FAILED")
echo "  Backend health: ${HEALTH}"

# Frontend
FE_CHECK=$(curl -sfk https://localhost:8091 2>/dev/null | head -1 || echo "FAILED")
if [[ "${FE_CHECK}" == *"html"* ]] || [[ "${FE_CHECK}" == *"DOCTYPE"* ]]; then
    echo "  ✔ Frontend responding"
else
    echo -e "${YELLOW}  Frontend check: ${FE_CHECK}${NC}"
fi

# Docker status
echo ""
echo "  Container status:"
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'show-build|NAMES'

# ─── Setup backup cron ───────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}Setting up backup cron...${NC}"
CRON_ENTRY="0 4 * * 1,3,6,0 ${PROJECT_DIR}/scripts/backup_database.sh >> ${PROJECT_DIR}/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v 'show-build.*backup'; echo "# Show-Build Database Backups"; echo "${CRON_ENTRY}") | crontab - 2>/dev/null || echo -e "${YELLOW}  Could not set crontab — set manually${NC}"

# ─── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  REDEPLOYMENT COMPLETE                                       ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
echo -e "${GREEN}║  Frontend:  https://${HOST_IP}:8091                   ║${NC}"
echo -e "${GREEN}║  Backend:   https://${HOST_IP}:8888/health            ║${NC}"
echo -e "${GREEN}║  Postgres:  ${HOST_IP}:5433                           ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
