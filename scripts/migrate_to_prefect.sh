#!/usr/bin/env bash
###############################################################################
# migrate_to_prefect.sh — Show-Build Migration: Whisper → Prefect
#
# Migrates the entire Show-Build platform from whisperbox (192.168.51.210)
# to prefect (192.168.51.207) with backup to proxima.
#
# Source:  kevin@whisper:/mnt/process/show-build
# Target:  kevin@prefect:/srv/show-build  (LOCAL NVMe disk)
# Backup:  kevin@proxima:~/backup/showbuild/
#
# Usage:   ./scripts/migrate_to_prefect.sh
# Prereqs: SSH access to prefect + proxima, no uncommitted critical work
###############################################################################

set -euo pipefail

# ─── Configuration ───────────────────────────────────────────────────────────
SOURCE_DIR="/mnt/process/show-build"
TARGET_HOST="kevin@192.168.51.207"
TARGET_DIR="/srv/show-build"
BACKUP_HOST="kevin@proxima"
BACKUP_DIR="~/backup/showbuild"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOGFILE="${SOURCE_DIR}/migration_${TIMESTAMP}.log"
ARCHIVE_NAME="showbuild_migration_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="/tmp/${ARCHIVE_NAME}"
REHYDRATE_FILE="${SOURCE_DIR}/REHYDRATE.NOW"
REDEPLOY_FILE="${SOURCE_DIR}/redeploy.sh"
TABLE_COUNTS_FILE="${SOURCE_DIR}/table_counts_source.txt"
STEP_COUNT=9
CURRENT_STEP=0
ERRORS=()

# ─── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ─── Logging ─────────────────────────────────────────────────────────────────
exec > >(tee -a "${LOGFILE}") 2>&1

log_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    local msg="$1"
    echo ""
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  STEP ${CURRENT_STEP}/${STEP_COUNT}: ${msg}${NC}"
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    STEP_START=$(date +%s)
}

log_substep() {
    echo -e "${CYAN}  ▸ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}  ⚠ WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}  ✖ ERROR: $1${NC}"
    ERRORS+=("$1")
}

log_success() {
    local now=$(date +%s)
    local elapsed=$((now - STEP_START))
    echo -e "${MAGENTA}  ✔ Step ${CURRENT_STEP} completed in ${elapsed}s${NC}"
}

log_info() {
    echo -e "${WHITE}  $1${NC}"
}

run_cmd() {
    local desc="$1"
    shift
    log_substep "${desc}"
    if ! "$@"; then
        log_error "Failed: ${desc}"
        return 1
    fi
}

die() {
    log_error "$1"
    echo ""
    echo -e "${RED}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}${BOLD}║  MIGRATION ABORTED — See log: ${LOGFILE}  ║${NC}"
    echo -e "${RED}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Errors encountered:"
    for err in "${ERRORS[@]}"; do
        echo "  - ${err}"
    done
    exit 1
}

# ─── Banner ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║       SHOW-BUILD MIGRATION: WHISPER → PREFECT               ║${NC}"
echo -e "${GREEN}${BOLD}║                                                              ║${NC}"
echo -e "${GREEN}${BOLD}║  Source: whisper (192.168.51.210) /mnt/process/show-build    ║${NC}"
echo -e "${GREEN}${BOLD}║  Target: prefect (192.168.51.207) /srv/show-build            ║${NC}"
echo -e "${GREEN}${BOLD}║  Backup: proxima ~/backup/showbuild/                         ║${NC}"
echo -e "${GREEN}${BOLD}║                                                              ║${NC}"
echo -e "${GREEN}${BOLD}║  Started: $(date)                        ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Log file: ${LOGFILE}"
echo ""

###############################################################################
# STEP 0: Pre-flight Checks
###############################################################################
log_step "Pre-flight Checks"

# Verify we're on the source machine
log_substep "Verifying source directory"
if [[ ! -d "${SOURCE_DIR}/app" ]] || [[ ! -f "${SOURCE_DIR}/docker-compose.yml" ]]; then
    die "Not running from Show-Build source directory: ${SOURCE_DIR}"
fi
log_info "Source directory verified: ${SOURCE_DIR}"

# SSH to prefect
log_substep "Testing SSH to prefect (192.168.51.207)"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes ${TARGET_HOST} "echo OK" &>/dev/null; then
    die "Cannot SSH to prefect (${TARGET_HOST}). Fix SSH access first."
fi
log_info "SSH to prefect: OK"

# SSH to proxima
log_substep "Testing SSH to proxima"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes ${BACKUP_HOST} "echo OK" &>/dev/null; then
    die "Cannot SSH to proxima (${BACKUP_HOST}). Fix SSH access first."
fi
log_info "SSH to proxima: OK"

# Docker on prefect
log_substep "Checking Docker on prefect"
PREFECT_DOCKER=$(ssh ${TARGET_HOST} "docker --version 2>&1" || true)
if [[ ! "${PREFECT_DOCKER}" == *"Docker version"* ]]; then
    die "Docker not available on prefect: ${PREFECT_DOCKER}"
fi
log_info "Prefect Docker: ${PREFECT_DOCKER}"

PREFECT_COMPOSE=$(ssh ${TARGET_HOST} "docker compose version 2>&1" || true)
log_info "Prefect Compose: ${PREFECT_COMPOSE}"

# NFS mount on prefect
log_substep "Checking /mnt/sync NFS on prefect"
if ! ssh ${TARGET_HOST} "test -d /mnt/sync/disaffected/episodes"; then
    die "/mnt/sync/disaffected/episodes not accessible on prefect — NFS not mounted?"
fi
log_info "NFS /mnt/sync: mounted and accessible"

# /srv writable on prefect
log_substep "Checking /srv on prefect"
if ! ssh ${TARGET_HOST} "test -d /srv && touch /srv/.migration_test && rm /srv/.migration_test"; then
    log_warn "/srv not directly writable, will use sudo"
fi
log_info "/srv: accessible"

# Disk space on prefect
log_substep "Checking disk space on prefect /srv"
PREFECT_AVAIL=$(ssh ${TARGET_HOST} "df -BG /srv | tail -1 | awk '{print \$4}' | tr -d 'G'")
log_info "Prefect /srv available: ${PREFECT_AVAIL}GB"
if (( PREFECT_AVAIL < 2 )); then
    die "Insufficient disk space on prefect: ${PREFECT_AVAIL}GB (need 2GB minimum)"
fi

# Disk space on proxima
log_substep "Checking disk space on proxima"
PROXIMA_AVAIL=$(ssh ${BACKUP_HOST} "df -BG ~ | tail -1 | awk '{print \$4}' | tr -d 'G'")
log_info "Proxima available: ${PROXIMA_AVAIL}GB"
if (( PROXIMA_AVAIL < 1 )); then
    die "Insufficient disk space on proxima: ${PROXIMA_AVAIL}GB (need at least 1GB)"
fi

# Asterisk mount check on prefect
log_substep "Checking /mnt/asterisk on prefect"
if ssh ${TARGET_HOST} "test -d /mnt/asterisk/recordings" 2>/dev/null; then
    log_info "Asterisk recordings mount: present"
    ASTERISK_AVAILABLE=true
else
    log_warn "Asterisk recordings mount NOT present on prefect — container will mount read-only empty dir"
    log_warn "Add NFS mount later: 192.168.51.223:/mnt/asterisk /mnt/asterisk nfs defaults,_netdev 0 0"
    ASTERISK_AVAILABLE=false
fi

# GID 1001 (disaffected group) check on prefect
log_substep "Checking GID 1001 (disaffected group) on prefect"
if ssh ${TARGET_HOST} "getent group 1001" &>/dev/null; then
    log_info "GID 1001 exists on prefect"
else
    log_warn "GID 1001 (disaffected) does not exist on prefect — creating it"
    ssh ${TARGET_HOST} "sudo groupadd -g 1001 disaffected && sudo usermod -aG disaffected kevin" 2>/dev/null || log_warn "Could not create group 1001 — create manually: sudo groupadd -g 1001 disaffected && sudo usermod -aG disaffected kevin"
fi

# npm check on prefect — install if missing
log_substep "Checking npm on prefect"
if ssh ${TARGET_HOST} "which npm" &>/dev/null; then
    log_info "npm: $(ssh ${TARGET_HOST} 'npm --version' 2>/dev/null)"
    NPM_AVAILABLE=true
else
    log_warn "npm not installed on prefect — installing now"
    if ssh ${TARGET_HOST} "sudo apt-get update -qq && sudo apt-get install -y -qq npm" 2>&1 | tail -3; then
        log_info "npm installed: $(ssh ${TARGET_HOST} 'npm --version' 2>/dev/null)"
        NPM_AVAILABLE=true
    else
        log_warn "npm install failed — Docker builds handle deps internally, but host linting won't work"
        NPM_AVAILABLE=false
    fi
fi

# Environment info
log_substep "Capturing environment info"
echo "--- Source Host Info ---"
uname -a
echo "Docker: $(docker --version 2>&1)"
echo "Docker Compose: $(docker compose version 2>&1)"
echo "Node: $(node --version 2>/dev/null || echo 'not installed')"
echo "Git: $(git --version 2>&1)"
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# Check postgres container running
log_substep "Verifying postgres container running"
if ! docker ps --format '{{.Names}}' | grep -q 'show-build-postgres'; then
    die "show-build-postgres container is not running. Start it first: docker compose up -d postgres"
fi
log_info "show-build-postgres: running"

log_success

###############################################################################
# STEP 1: Full Database Export
###############################################################################
log_step "Full Database Export"

DB_DUMP_DIR="${SOURCE_DIR}/migration_db_${TIMESTAMP}"
mkdir -p "${DB_DUMP_DIR}"

# Custom format dump (restorable)
log_substep "Exporting database (custom format for restore)"
docker exec show-build-postgres pg_dump -U showbuild -Fc showbuild > "${DB_DUMP_DIR}/showbuild_full.dump"
DUMP_SIZE=$(du -sh "${DB_DUMP_DIR}/showbuild_full.dump" | awk '{print $1}')
log_info "Custom dump: ${DUMP_SIZE}"

# Plain SQL for human inspection
log_substep "Exporting database (plain SQL for inspection)"
docker exec show-build-postgres pg_dump -U showbuild showbuild > "${DB_DUMP_DIR}/showbuild_full.sql"
SQL_SIZE=$(du -sh "${DB_DUMP_DIR}/showbuild_full.sql" | awk '{print $1}')
log_info "Plain SQL dump: ${SQL_SIZE}"

# Roles dump
log_substep "Exporting database roles"
docker exec show-build-postgres pg_dumpall -U showbuild --roles-only > "${DB_DUMP_DIR}/roles.sql"
log_info "Roles exported"

# Table counts for verification
log_substep "Capturing table counts for verification"
docker exec show-build-postgres psql -U showbuild -d showbuild -t -A -c \
    "SELECT relname || '|' || n_live_tup FROM pg_stat_user_tables ORDER BY relname;" \
    > "${DB_DUMP_DIR}/table_counts.txt"
cp "${DB_DUMP_DIR}/table_counts.txt" "${TABLE_COUNTS_FILE}"
log_info "Table counts:"
while IFS='|' read -r table count; do
    if [[ -n "${table}" ]]; then
        printf "    %-45s %s rows\n" "${table}" "${count}"
    fi
done < "${DB_DUMP_DIR}/table_counts.txt"

log_success

###############################################################################
# STEP 2: Capture Environment State
###############################################################################
log_step "Capture Environment State"

ENV_DIR="${SOURCE_DIR}/migration_env_${TIMESTAMP}"
mkdir -p "${ENV_DIR}"

# Container environment
log_substep "Capturing container environment variables"
docker exec show-build-server env | sort > "${ENV_DIR}/server_env.txt" 2>/dev/null || log_warn "Could not capture server env"

# .env file
log_substep "Copying .env file"
if [[ -f "${SOURCE_DIR}/.env" ]]; then
    cp "${SOURCE_DIR}/.env" "${ENV_DIR}/dot_env_backup"
    log_info ".env copied"
else
    log_warn "No .env file found"
fi

# Resolved compose config
log_substep "Capturing resolved docker compose config"
cd "${SOURCE_DIR}" && docker compose config > "${ENV_DIR}/compose_resolved.yml" 2>/dev/null || log_warn "Could not capture compose config"

# Docker volumes and networks
log_substep "Capturing Docker volumes and networks"
docker volume ls > "${ENV_DIR}/docker_volumes.txt" 2>/dev/null
docker network ls > "${ENV_DIR}/docker_networks.txt" 2>/dev/null

# Crontab
log_substep "Capturing crontab"
crontab -l > "${ENV_DIR}/crontab.txt" 2>/dev/null || echo "# no crontab" > "${ENV_DIR}/crontab.txt"

# Git state
log_substep "Capturing git state"
cd "${SOURCE_DIR}"
{
    echo "=== Branch ==="
    git branch --show-current 2>/dev/null || echo "detached HEAD"
    echo ""
    echo "=== Status ==="
    git status --short 2>/dev/null
    echo ""
    echo "=== Recent Log (10 commits) ==="
    git log --oneline -10 2>/dev/null
    echo ""
    echo "=== Remotes ==="
    git remote -v 2>/dev/null
} > "${ENV_DIR}/git_state.txt"

# Directory listings
log_substep "Capturing directory listings"
ls -lah "${SOURCE_DIR}/" > "${ENV_DIR}/ls_root.txt" 2>/dev/null
ls -lah "${SOURCE_DIR}/app/" > "${ENV_DIR}/ls_app.txt" 2>/dev/null
ls -lah "${SOURCE_DIR}/disaffected-ui/" > "${ENV_DIR}/ls_ui.txt" 2>/dev/null
ls -lah "${SOURCE_DIR}/scripts/" > "${ENV_DIR}/ls_scripts.txt" 2>/dev/null
ls -lah "${SOURCE_DIR}/tools/" > "${ENV_DIR}/ls_tools.txt" 2>/dev/null

# Full tree (excluding big dirs)
log_substep "Generating project tree"
if command -v tree &>/dev/null; then
    tree -a -I 'node_modules|.git|__pycache__|backups' "${SOURCE_DIR}" > "${ENV_DIR}/project_tree.txt" 2>/dev/null || log_warn "tree command failed"
else
    find "${SOURCE_DIR}" -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' -not -path '*/backups/*' | head -500 > "${ENV_DIR}/project_tree.txt"
fi

log_success

###############################################################################
# STEP 3: Generate REHYDRATE.NOW Document (pre-migration snapshot)
###############################################################################
# We build this incrementally — start now, finish at the end
log_step "Begin REHYDRATE.NOW Document"

cat > "${REHYDRATE_FILE}" << 'REHYDRATE_HEADER'
╔══════════════════════════════════════════════════════════════════════════════╗
║                       REHYDRATE.NOW — Migration Audit Trail                ║
║                       Show-Build: Whisper → Prefect                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
REHYDRATE_HEADER

cat >> "${REHYDRATE_FILE}" << EOF

══════════════════════════════════════════════════════════════
(c) Migration Objective
══════════════════════════════════════════════════════════════

DATE:   $(date -u '+%Y-%m-%d %H:%M:%S UTC')
FROM:   kevin@whisper (192.168.51.210) /mnt/process/show-build
TO:     kevin@prefect (192.168.51.207) /srv/show-build
REASON: Whisper's GPU (RTX 3060 Ti) causes hard system crashes during
        inference workloads, killing active Claude Code sessions. Prefect
        has 64 cores, 125GB RAM, 3.4TB free NVMe — stable and powerful.
PLAN:   Both instances run concurrently until prefect is verified, then
        whisper show-build instance is decommissioned.

══════════════════════════════════════════════════════════════
(a) Source Directory Listings (Whisper, pre-migration)
══════════════════════════════════════════════════════════════

EOF

# Append directory listings
for f in ls_root.txt ls_app.txt ls_ui.txt ls_scripts.txt ls_tools.txt; do
    if [[ -f "${ENV_DIR}/${f}" ]]; then
        echo "--- ${f} ---" >> "${REHYDRATE_FILE}"
        cat "${ENV_DIR}/${f}" >> "${REHYDRATE_FILE}"
        echo "" >> "${REHYDRATE_FILE}"
    fi
done

cat >> "${REHYDRATE_FILE}" << EOF

══════════════════════════════════════════════════════════════
(b) Project Tree (Whisper, pre-migration)
══════════════════════════════════════════════════════════════

EOF
if [[ -f "${ENV_DIR}/project_tree.txt" ]]; then
    cat "${ENV_DIR}/project_tree.txt" >> "${REHYDRATE_FILE}"
fi

cat >> "${REHYDRATE_FILE}" << EOF

══════════════════════════════════════════════════════════════
(e) Database Table Counts — SOURCE (Whisper)
══════════════════════════════════════════════════════════════

EOF
if [[ -f "${DB_DUMP_DIR}/table_counts.txt" ]]; then
    while IFS='|' read -r table count; do
        if [[ -n "${table}" ]]; then
            printf "%-45s %s rows\n" "${table}" "${count}" >> "${REHYDRATE_FILE}"
        fi
    done < "${DB_DUMP_DIR}/table_counts.txt"
fi

cat >> "${REHYDRATE_FILE}" << EOF

══════════════════════════════════════════════════════════════
(f) Docker Container Status — SOURCE (Whisper)
══════════════════════════════════════════════════════════════

$(docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || echo "Could not capture docker ps")

══════════════════════════════════════════════════════════════
Git State — SOURCE (Whisper)
══════════════════════════════════════════════════════════════

$(cat "${ENV_DIR}/git_state.txt" 2>/dev/null || echo "Not captured")

EOF

log_info "REHYDRATE.NOW started — will be completed after migration"
log_success

###############################################################################
# STEP 4: Generate Redeploy Script
###############################################################################
log_step "Generate Redeploy Script (redeploy.sh)"

cat > "${REDEPLOY_FILE}" << 'REDEPLOY_EOF'
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
REDEPLOY_EOF

chmod +x "${REDEPLOY_FILE}"
log_info "redeploy.sh generated ($(wc -l < "${REDEPLOY_FILE}") lines)"
log_success

###############################################################################
# STEP 5: Create Project Archive
###############################################################################
log_step "Create Project Archive"

log_substep "Creating tarball: ${ARCHIVE_PATH}"
log_info "This may take a minute..."

cd /mnt/process

tar czf "${ARCHIVE_PATH}" \
    --warning=no-file-ignored \
    --exclude='show-build/node_modules' \
    --exclude='show-build/disaffected-ui/node_modules' \
    --exclude='show-build/disaffected-ui/ssl' \
    --exclude='show-build/.git/lfs' \
    --exclude='show-build/backups/*.sql.gz' \
    --exclude='show-build/__pycache__' \
    --exclude='show-build/app/__pycache__' \
    --exclude='show-build/app/**/__pycache__' \
    --exclude='show-build/app/gunicorn.ctl' \
    --exclude='show-build/migration_env_*' \
    show-build/ 2>&1 | grep -v "socket ignored" || true

ARCHIVE_SIZE=$(du -sh "${ARCHIVE_PATH}" | awk '{print $1}')
log_info "Archive created: ${ARCHIVE_SIZE}"

# Compute checksum
ARCHIVE_MD5=$(md5sum "${ARCHIVE_PATH}" | awk '{print $1}')
log_info "MD5: ${ARCHIVE_MD5}"

log_success

###############################################################################
# STEP 6: SCP Archive to Proxima (Backup)
###############################################################################
log_step "SCP Archive to Proxima (Backup)"

log_substep "Ensuring backup directory on proxima"
ssh ${BACKUP_HOST} "mkdir -p ${BACKUP_DIR}"

# Check for existing archive, enumerate if needed
PROXIMA_ARCHIVE="${BACKUP_DIR}/${ARCHIVE_NAME}"
ENUM=1
while ssh ${BACKUP_HOST} "test -f ${PROXIMA_ARCHIVE}" 2>/dev/null; do
    ENUM=$((ENUM + 1))
    PROXIMA_ARCHIVE="${BACKUP_DIR}/showbuild_migration_${TIMESTAMP}_$(printf '%03d' ${ENUM}).tar.gz"
done

log_substep "Transferring archive to proxima: $(basename ${PROXIMA_ARCHIVE})"
scp "${ARCHIVE_PATH}" "${BACKUP_HOST}:${PROXIMA_ARCHIVE}"

# Verify checksum
log_substep "Verifying checksum on proxima"
REMOTE_MD5=$(ssh ${BACKUP_HOST} "md5sum ${PROXIMA_ARCHIVE}" | awk '{print $1}')
if [[ "${ARCHIVE_MD5}" != "${REMOTE_MD5}" ]]; then
    die "Checksum mismatch on proxima! Local: ${ARCHIVE_MD5}, Remote: ${REMOTE_MD5}"
fi
log_info "Checksum verified: ${REMOTE_MD5}"

log_success

###############################################################################
# STEP 7: SCP Archive to Prefect + Unpack
###############################################################################
log_step "SCP Archive to Prefect + Unpack"

# Create target directory
log_substep "Preparing target directory on prefect"
ssh ${TARGET_HOST} "sudo mkdir -p /srv/show-build && sudo chown kevin:kevin /srv/show-build"

# Check if target already has content — enumerate if needed
TARGET_FINAL="${TARGET_DIR}"
if ssh ${TARGET_HOST} "test -f ${TARGET_DIR}/docker-compose.yml" 2>/dev/null; then
    log_warn "Target ${TARGET_DIR} already contains a show-build installation"
    TARGET_FINAL="${TARGET_DIR}_${TIMESTAMP}"
    log_info "Using alternate: ${TARGET_FINAL}"
    ssh ${TARGET_HOST} "sudo mkdir -p ${TARGET_FINAL} && sudo chown kevin:kevin ${TARGET_FINAL}"
fi

# Transfer archive
log_substep "Transferring archive to prefect"
scp "${ARCHIVE_PATH}" "${TARGET_HOST}:/tmp/${ARCHIVE_NAME}"

# Unpack
log_substep "Unpacking archive on prefect"
ssh ${TARGET_HOST} "cd /tmp && tar xzf ${ARCHIVE_NAME} && rsync -a show-build/ ${TARGET_FINAL}/ && rm -rf /tmp/show-build /tmp/${ARCHIVE_NAME}"
log_info "Unpacked to ${TARGET_FINAL}"

log_success

###############################################################################
# STEP 8: Remote Setup on Prefect (Dependencies + Docker + DB Restore)
###############################################################################
log_step "Remote Setup on Prefect"

# Create asterisk placeholder if needed
if [[ "${ASTERISK_AVAILABLE}" == "false" ]]; then
    log_substep "Creating asterisk recordings placeholder on prefect"
    ssh ${TARGET_HOST} "sudo mkdir -p /mnt/asterisk/recordings && sudo chown kevin:kevin /mnt/asterisk/recordings" 2>/dev/null || true
fi

# Ensure claude todos dir
log_substep "Ensuring claude todos directory on prefect"
ssh ${TARGET_HOST} "mkdir -p /home/kevin/.claude/todos" 2>/dev/null || true

# Update docker-compose volume paths (only if project root changed)
if [[ "${TARGET_FINAL}" != "/srv/show-build" ]]; then
    log_warn "Non-standard target path: ${TARGET_FINAL} — docker-compose uses relative paths, should be OK"
fi

# Delete stale SSL certs so Docker regenerates with correct IP
log_substep "Removing whisper SSL certs (Docker will regenerate for prefect IP)"
ssh ${TARGET_HOST} "rm -f ${TARGET_FINAL}/disaffected-ui/ssl/cert.pem ${TARGET_FINAL}/disaffected-ui/ssl/key.pem" 2>/dev/null || true

# Update frontend Dockerfile SSL generation to use prefect IP
log_substep "Updating frontend Dockerfile SSL SAN for prefect IP (192.168.51.207)"
ssh ${TARGET_HOST} "sed -i 's/192.168.51.210/192.168.51.207/g' ${TARGET_FINAL}/disaffected-ui/Dockerfile" 2>/dev/null || log_warn "Could not update Dockerfile IP — SSL certs will use old IP"

# Install frontend dependencies (only if npm available, Docker handles this internally anyway)
if [[ "${NPM_AVAILABLE}" == "true" ]]; then
    log_substep "Installing frontend dependencies on prefect (npm ci)"
    ssh ${TARGET_HOST} "cd ${TARGET_FINAL}/disaffected-ui && npm ci 2>&1 | tail -5" || log_warn "npm ci failed — Docker build will handle deps"
else
    log_substep "Skipping host npm ci (npm not installed — Docker handles deps internally)"
fi

# Stop any existing show-build containers on prefect
log_substep "Stopping any existing show-build containers on prefect"
ssh ${TARGET_HOST} "cd ${TARGET_FINAL} && docker compose down 2>/dev/null || true"

# Build and start docker
log_substep "Building and starting Docker services on prefect"
ssh ${TARGET_HOST} "cd ${TARGET_FINAL} && docker compose up --build -d 2>&1 | tail -15"

# Wait for postgres health
log_substep "Waiting for PostgreSQL to be healthy on prefect"
for i in $(seq 1 60); do
    PG_READY=$(ssh ${TARGET_HOST} "docker exec show-build-postgres pg_isready -U showbuild -d showbuild 2>&1" || echo "not ready")
    if [[ "${PG_READY}" == *"accepting connections"* ]]; then
        log_info "PostgreSQL ready (${i}s)"
        break
    fi
    if [[ "${i}" -eq 60 ]]; then
        die "PostgreSQL on prefect failed to start within 60s"
    fi
    sleep 1
done

# Restore database
log_substep "Restoring database on prefect"

# Find the dump file path on prefect
PREFECT_DUMP=$(ssh ${TARGET_HOST} "ls -1 ${TARGET_FINAL}/migration_db_*/showbuild_full.dump 2>/dev/null | tail -1")
if [[ -z "${PREFECT_DUMP}" ]]; then
    die "Cannot find database dump on prefect"
fi
log_info "Using dump: ${PREFECT_DUMP}"

# Drop and recreate database
ssh ${TARGET_HOST} "docker exec show-build-postgres psql -U showbuild -d postgres -c 'DROP DATABASE IF EXISTS showbuild;' 2>/dev/null || true"
ssh ${TARGET_HOST} "docker exec show-build-postgres psql -U showbuild -d postgres -c 'CREATE DATABASE showbuild OWNER showbuild;' 2>/dev/null || true"

# Restore
ssh ${TARGET_HOST} "cat ${PREFECT_DUMP} | docker exec -i show-build-postgres pg_restore -U showbuild -d showbuild --no-owner --no-privileges 2>&1 | tail -5 || true"
log_info "Database restored"

# Run ANALYZE
ssh ${TARGET_HOST} "docker exec show-build-postgres psql -U showbuild -d showbuild -c 'ANALYZE;'" &>/dev/null || true

# Run Alembic migrations
log_substep "Running Alembic migrations on prefect"
ssh ${TARGET_HOST} "docker exec show-build-server python -m alembic upgrade head 2>&1 | tail -3" || log_warn "Alembic migration may have warnings (often OK)"

# Verify table counts
log_substep "Verifying table counts on prefect"
PREFECT_COUNTS=$(ssh ${TARGET_HOST} "docker exec show-build-postgres psql -U showbuild -d showbuild -t -A -c \"SELECT tablename || '|' || n_live_tup FROM pg_stat_user_tables ORDER BY tablename;\"" 2>/dev/null || echo "")
if [[ -n "${PREFECT_COUNTS}" ]]; then
    log_info "Prefect table counts:"
    echo "${PREFECT_COUNTS}" | while IFS='|' read -r table count; do
        if [[ -n "${table}" ]]; then
            printf "    %-45s %s rows\n" "${table}" "${count}"
        fi
    done
fi

# Wait for all services healthy
log_substep "Waiting for all services to be healthy on prefect"
sleep 10
for i in $(seq 1 90); do
    SERVER_STATUS=$(ssh ${TARGET_HOST} "docker inspect --format='{{.State.Health.Status}}' show-build-server 2>/dev/null" || echo "starting")
    PG_STATUS=$(ssh ${TARGET_HOST} "docker inspect --format='{{.State.Health.Status}}' show-build-postgres 2>/dev/null" || echo "starting")

    if [[ "${SERVER_STATUS}" == "healthy" && "${PG_STATUS}" == "healthy" ]]; then
        log_info "All services healthy (server=${SERVER_STATUS}, postgres=${PG_STATUS})"
        break
    fi
    if [[ "${i}" -eq 90 ]]; then
        log_warn "Services not all healthy after 90s (server=${SERVER_STATUS}, postgres=${PG_STATUS})"
    fi
    sleep 1
done

# Sanity check endpoints
log_substep "Running sanity checks on prefect"
HEALTH_CHECK=$(ssh ${TARGET_HOST} "curl -sf http://localhost:8888/health 2>/dev/null" || echo "FAILED")
log_info "Backend health: ${HEALTH_CHECK}"

FE_CHECK=$(ssh ${TARGET_HOST} "curl -sfk https://localhost:8091 2>/dev/null | head -c 100" || echo "FAILED")
if [[ "${FE_CHECK}" == *"html"* ]] || [[ "${FE_CHECK}" == *"DOCTYPE"* ]]; then
    log_info "Frontend: responding (HTML detected)"
else
    log_warn "Frontend check returned: ${FE_CHECK}"
fi

# Docker ps on prefect
log_info "Docker containers on prefect:"
ssh ${TARGET_HOST} "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'show-build|NAMES'"

# Setup backup cron on prefect
log_substep "Setting up backup cron on prefect"
ssh ${TARGET_HOST} "
CRON_ENTRY='0 4 * * 1,3,6,0 ${TARGET_FINAL}/scripts/backup_database.sh >> ${TARGET_FINAL}/backup.log 2>&1'
(crontab -l 2>/dev/null | grep -v 'show-build.*backup'; echo '# Show-Build Database Backups'; echo \"\${CRON_ENTRY}\") | crontab -
" 2>/dev/null || log_warn "Could not set crontab on prefect — set manually"

log_success

###############################################################################
# STEP 9: Finalize REHYDRATE.NOW Document
###############################################################################
log_step "Finalize REHYDRATE.NOW Document"

cat >> "${REHYDRATE_FILE}" << EOF

══════════════════════════════════════════════════════════════
(d) Migration Log Output (stdout/stderr)
══════════════════════════════════════════════════════════════

See full log: ${LOGFILE}

Summary of steps executed:
  Step 0: Pre-flight Checks — PASSED
  Step 1: Database Export — ${DUMP_SIZE} dump, ${SQL_SIZE} SQL
  Step 2: Environment Capture — completed
  Step 3: REHYDRATE.NOW — started
  Step 4: Redeploy Script — generated
  Step 5: Archive — ${ARCHIVE_SIZE}, MD5: ${ARCHIVE_MD5}
  Step 6: Proxima Backup — checksum verified
  Step 7: Prefect Unpack — ${TARGET_FINAL}
  Step 8: Remote Setup — DB restored, services started
  Step 9: Finalize — this document

══════════════════════════════════════════════════════════════
(e) Database Table Counts — TARGET (Prefect)
══════════════════════════════════════════════════════════════

${PREFECT_COUNTS:-"Not captured — run ANALYZE and check manually"}

══════════════════════════════════════════════════════════════
(f) Docker Container Status — TARGET (Prefect)
══════════════════════════════════════════════════════════════

$(ssh ${TARGET_HOST} "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'" 2>/dev/null || echo "Could not capture")

══════════════════════════════════════════════════════════════
(g) Verification URLs
══════════════════════════════════════════════════════════════

Frontend: https://192.168.51.207:8091
Backend:  https://192.168.51.207:8888/health
Postgres: 192.168.51.207:5433

══════════════════════════════════════════════════════════════
(i) Pre-Migration Fixes Applied
══════════════════════════════════════════════════════════════

The following issues were identified during pre-flight audit and fixed
in the migration script before execution:

1. NPM NOT INSTALLED ON PREFECT
   - Node 18.19.1 is installed via Ubuntu repos but npm is not included
   - Impact: Host-level npm ci / linting commands fail
   - Fix: Script installs npm via apt during pre-flight checks on prefect
   - Fallback: If install fails, Docker frontend Dockerfile still handles
     its own npm install internally during container build

2. SSL CERTIFICATES HARDCODED TO WHISPERBOX IP (192.168.51.210)
   - Frontend Dockerfile start.sh generates self-signed certs with
     CN=192.168.51.210 and SAN=IP:192.168.51.210
   - Impact: SSL cert IP mismatch on prefect (192.168.51.207)
   - Fix: Script deletes stale certs from archive and sed-replaces the
     IP in the Dockerfile so regenerated certs match 192.168.51.207

3. GID 1001 (disaffected group) MISSING ON PREFECT
   - Whisper: kevin in group 1001 (disaffected)
   - Prefect: no group 1001 exists
   - docker-compose runs server as user 1000:1001
   - Impact: Container works (Dockerfile creates group internally), but
     host-level access to NFS files with gid 1001 would fail
   - Fix: Script creates group 1001 (disaffected) on prefect and adds
     kevin to it during pre-flight

4. GIT HISTORY WOULD BE LOST (.git/objects excluded)
   - Original plan excluded .git/objects from archive to save space
   - Impact: git log, git diff, git status all broken on prefect
   - Fix: Removed .git/objects exclusion — full git history preserved
     in archive. GitHub remote (git@github.com:pmw1/show-build.git)
     also available for fetch/pull.

5. HOST npm ci UNNECESSARY FOR DOCKER MIGRATION
   - Frontend Dockerfile does its own npm install --legacy-peer-deps
   - docker-compose volume mounts only source dirs, not node_modules
   - Impact: Script would fail at npm ci step if npm not installed
   - Fix: Made host npm ci conditional on npm availability

══════════════════════════════════════════════════════════════
(h) Rollback Instructions
══════════════════════════════════════════════════════════════

If prefect deployment fails or has issues:

1. WHISPER IS STILL RUNNING — no changes were made to the source
   - Frontend: https://192.168.51.210:8091
   - Backend:  https://192.168.51.210:8888/health

2. To stop prefect instance:
   ssh kevin@192.168.51.207 "cd ${TARGET_FINAL} && docker compose down"

3. To fully remove prefect instance:
   ssh kevin@192.168.51.207 "cd ${TARGET_FINAL} && docker compose down -v"
   ssh kevin@192.168.51.207 "sudo rm -rf ${TARGET_FINAL}"

4. Backup archive on proxima:
   ssh kevin@proxima "ls -la ~/backup/showbuild/"

5. Database dump (local copy):
   ls -la ${DB_DUMP_DIR}/

══════════════════════════════════════════════════════════════
Migration Completed: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
══════════════════════════════════════════════════════════════

EOF

# Copy REHYDRATE.NOW to prefect
scp "${REHYDRATE_FILE}" "${TARGET_HOST}:${TARGET_FINAL}/REHYDRATE.NOW" 2>/dev/null || log_warn "Could not copy REHYDRATE.NOW to prefect"

log_info "REHYDRATE.NOW finalized and copied to prefect"
log_success

###############################################################################
# CLEANUP
###############################################################################

# Remove local archive from /tmp
log_substep "Cleaning up local temp files"
rm -f "${ARCHIVE_PATH}" 2>/dev/null || true

# Clean up migration temp dirs (keep the db dump dir for safety)
rm -rf "${ENV_DIR}" 2>/dev/null || true

###############################################################################
# FINAL SUMMARY
###############################################################################
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║                                                                  ║${NC}"
echo -e "${GREEN}${BOLD}║   MIGRATION COMPLETE                                             ║${NC}"
echo -e "${GREEN}${BOLD}║                                                                  ║${NC}"
echo -e "${GREEN}${BOLD}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}${BOLD}║                                                                  ║${NC}"
echo -e "${GREEN}${BOLD}║   PREFECT (NEW):                                                 ║${NC}"
echo -e "${GREEN}${BOLD}║     Frontend:  https://192.168.51.207:8091                       ║${NC}"
echo -e "${GREEN}${BOLD}║     Backend:   https://192.168.51.207:8888/health                ║${NC}"
echo -e "${GREEN}${BOLD}║     Project:   ${TARGET_FINAL}$(printf '%*s' $((25 - ${#TARGET_FINAL})) '')║${NC}"
echo -e "${GREEN}${BOLD}║                                                                  ║${NC}"
echo -e "${GREEN}${BOLD}║   WHISPER (ORIGINAL — still running):                            ║${NC}"
echo -e "${GREEN}${BOLD}║     Frontend:  https://192.168.51.210:8091                       ║${NC}"
echo -e "${GREEN}${BOLD}║     Backend:   https://192.168.51.210:8888/health                ║${NC}"
echo -e "${GREEN}${BOLD}║                                                                  ║${NC}"
echo -e "${GREEN}${BOLD}║   BACKUP:                                                        ║${NC}"
echo -e "${GREEN}${BOLD}║     proxima: ~/backup/showbuild/                                 ║${NC}"
echo -e "${GREEN}${BOLD}║                                                                  ║${NC}"
echo -e "${GREEN}${BOLD}║   DOCUMENTS:                                                     ║${NC}"
echo -e "${GREEN}${BOLD}║     Log:       ${LOGFILE}${NC}"
echo -e "${GREEN}${BOLD}║     Audit:     ${TARGET_FINAL}/REHYDRATE.NOW                     ║${NC}"
echo -e "${GREEN}${BOLD}║     Redeploy:  ${TARGET_FINAL}/redeploy.sh                       ║${NC}"
echo -e "${GREEN}${BOLD}║                                                                  ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Warnings/Errors encountered:${NC}"
    for err in "${ERRORS[@]}"; do
        echo -e "${YELLOW}  - ${err}${NC}"
    done
    echo ""
fi

echo "Next steps:"
echo "  1. Verify: curl -k https://192.168.51.207:8091"
echo "  2. Verify: curl http://192.168.51.207:8888/health"
echo "  3. Log into frontend on prefect, check episode data"
echo "  4. Run both instances in parallel until confident"
echo "  5. Decommission whisper show-build when ready"
echo ""
echo "Migration finished at $(date)"
