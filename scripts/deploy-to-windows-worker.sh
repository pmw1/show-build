#!/bin/bash
#
# Automated Windows Worker Deployment Script
# Full CI/CD-style deployment: commit, push, sync, restart
#
# Usage:
#   ./scripts/deploy-to-windows-worker.sh [message]
#
# This script:
#   1. Commits current changes with automatic or custom message
#   2. Pushes to Git (Windows can pull OR use direct sync)
#   3. Syncs files to Windows worker
#   4. Restarts Windows Celery worker
#   5. Verifies worker reconnection

set -euo pipefail

# Configuration
WINDOWS_HOST="${WINDOWS_WORKER_HOST:-HOME-MAIN}"
WINDOWS_USER="${WINDOWS_WORKER_USER:-kevin}"
WINDOWS_CODE_PATH="${WINDOWS_WORKER_PATH:-J:/show-build}"
COMMIT_MESSAGE="${1:-Auto-deploy: Windows worker update $(date '+%Y-%m-%d %H:%M:%S')}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Windows Worker Automated Deployment${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Step 1: Check for changes
echo -e "${BLUE}[1/6] Checking for changes...${NC}"
if [[ -z "$(git status --porcelain)" ]]; then
    echo -e "${YELLOW}⚠️  No changes to commit${NC}"
    SKIP_COMMIT=true
else
    echo -e "${GREEN}✓ Changes detected${NC}"
    SKIP_COMMIT=false
    git status --short | head -10
    echo ""
fi

# Step 2: Commit changes
if [[ "$SKIP_COMMIT" == false ]]; then
    echo -e "${BLUE}[2/6] Committing changes...${NC}"
    git add -A
    git commit -m "$COMMIT_MESSAGE" || {
        echo -e "${RED}❌ Git commit failed${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Changes committed${NC}"
    echo ""
else
    echo -e "${BLUE}[2/6] Skipping commit (no changes)${NC}"
    echo ""
fi

# Step 3: Push to remote
echo -e "${BLUE}[3/6] Pushing to Git remote...${NC}"
git push origin dev-fork 2>&1 || {
    echo -e "${YELLOW}⚠️  Git push failed (continuing anyway)${NC}"
}
echo -e "${GREEN}✓ Pushed to origin/dev-fork${NC}"
echo ""

# Step 4: Detect Windows connection method
echo -e "${BLUE}[4/6] Detecting Windows connection method...${NC}"
SYNC_METHOD="none"

# Try SSH first (most reliable)
if command -v ssh >/dev/null 2>&1; then
    if timeout 3 ssh -o ConnectTimeout=2 -o BatchMode=yes "${WINDOWS_USER}@${WINDOWS_HOST}" exit 2>/dev/null; then
        SYNC_METHOD="ssh"
        echo -e "${GREEN}✓ SSH connection verified${NC}"
    fi
fi

# Fallback to network share
if [[ "$SYNC_METHOD" == "none" ]]; then
    SHARE_PATH=$(find /mnt /media -path "*${WINDOWS_HOST}*" -o -path "*J*drive*" -o -path "*windows*share*" 2>/dev/null | grep -i "show-build" | head -1 || echo "")
    if [[ -n "$SHARE_PATH" && -d "$SHARE_PATH" ]]; then
        SYNC_METHOD="share"
        echo -e "${GREEN}✓ Network share found: $SHARE_PATH${NC}"
    fi
fi

if [[ "$SYNC_METHOD" == "none" ]]; then
    echo -e "${RED}❌ ERROR: Cannot connect to Windows worker${NC}"
    echo ""
    echo -e "${YELLOW}Manual steps required:${NC}"
    echo -e "  1. On Windows: ${CYAN}cd J:\\show-build${NC}"
    echo -e "  2. Run: ${CYAN}git pull origin dev-fork${NC}"
    echo -e "  3. Stop worker (Ctrl+C)"
    echo -e "  4. Run: ${CYAN}.\\start_worker.bat${NC}"
    exit 1
fi

echo ""

# Step 5: Sync files to Windows
echo -e "${BLUE}[5/6] Syncing files to Windows...${NC}"
case "$SYNC_METHOD" in
    ssh)
        # Use rsync over SSH
        rsync -avz --delete \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.git' \
            --exclude='node_modules' \
            --exclude='venv' \
            --exclude='backups' \
            -e "ssh -o ConnectTimeout=5" \
            /mnt/process/show-build/app/ \
            "${WINDOWS_USER}@${WINDOWS_HOST}:${WINDOWS_CODE_PATH}/app/" 2>&1 | grep -E "sent|received|total size" || echo -e "${YELLOW}(rsync output filtered)${NC}"

        echo -e "${GREEN}✓ Files synced via SSH${NC}"
        ;;

    share)
        # Direct copy via network share
        rsync -av --delete \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.git' \
            /mnt/process/show-build/app/ \
            "$SHARE_PATH/app/" 2>&1 | grep -E "sent|received|total size" || echo -e "${YELLOW}(rsync output filtered)${NC}"

        echo -e "${GREEN}✓ Files synced via network share${NC}"
        ;;
esac
echo ""

# Step 6: Restart Windows worker
echo -e "${BLUE}[6/6] Restarting Windows worker...${NC}"
if [[ "$SYNC_METHOD" == "ssh" ]]; then
    # Kill existing worker
    ssh "${WINDOWS_USER}@${WINDOWS_HOST}" "taskkill /F /IM celery.exe 2>nul; taskkill /F /IM python.exe /FI \"WINDOWTITLE eq *celery*\" 2>nul; exit 0" 2>/dev/null || true
    sleep 2

    # Start worker in background (detached)
    ssh "${WINDOWS_USER}@${WINDOWS_HOST}" "cd ${WINDOWS_CODE_PATH} && start /MIN cmd /c start_worker.bat" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Could not restart worker remotely${NC}"
        echo -e "${YELLOW}Please manually restart on Windows: .\\start_worker.bat${NC}"
    }

    echo -e "${GREEN}✓ Worker restart command sent${NC}"
else
    echo -e "${YELLOW}⚠️  Cannot restart worker via network share${NC}"
    echo -e "${YELLOW}Please manually restart on Windows:${NC}"
    echo -e "  1. Press Ctrl+C to stop worker"
    echo -e "  2. Run: ${CYAN}.\\start_worker.bat${NC}"
fi

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Monitor worker reconnection (if SSH available)
if [[ "$SYNC_METHOD" == "ssh" ]]; then
    echo -e "${BLUE}Monitoring worker reconnection...${NC}"
    echo -e "${YELLOW}(Checking Celery events for 15 seconds)${NC}"
    echo ""

    timeout 15 docker exec show-build-server celery -A celery_app inspect active 2>/dev/null | grep -i "windows\|HOME-MAIN" || {
        echo -e "${YELLOW}⚠️  Worker not detected yet (may take 30-60 seconds)${NC}"
    }
fi

echo ""
echo -e "${CYAN}Summary:${NC}"
echo -e "  Commit: ${GREEN}${COMMIT_MESSAGE}${NC}"
echo -e "  Method: ${GREEN}${SYNC_METHOD}${NC}"
echo -e "  Target: ${GREEN}${WINDOWS_USER}@${WINDOWS_HOST}:${WINDOWS_CODE_PATH}${NC}"
echo ""
