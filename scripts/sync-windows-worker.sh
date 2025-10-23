#!/bin/bash
#
# Automated Windows Worker Code Sync Script
# Syncs Show-Build Python code to Windows Celery worker
#
# Usage:
#   ./scripts/sync-windows-worker.sh [--restart]
#
# Requirements:
#   - Network share access to Windows machine OR
#   - SSH access to Windows machine OR
#   - Git remote configured for Windows repo

set -euo pipefail

# Configuration
WINDOWS_HOST="${WINDOWS_WORKER_HOST:-HOME-MAIN}"
WINDOWS_USER="${WINDOWS_WORKER_USER:-kevin}"
WINDOWS_CODE_PATH="${WINDOWS_WORKER_PATH:-J:/show-build}"
LOCAL_CODE_PATH="/mnt/process/show-build/app"

RESTART_WORKER=false
if [[ "${1:-}" == "--restart" ]]; then
    RESTART_WORKER=true
fi

echo "=========================================="
echo "Show-Build Windows Worker Sync"
echo "=========================================="
echo ""

# Detect sync method
SYNC_METHOD="unknown"

# Check for network share (UNC path or mounted drive)
if [[ -d "/mnt/windows-share/show-build" ]] || [[ -d "/media/J_drive/show-build" ]]; then
    SYNC_METHOD="share"
    SHARE_PATH=$(find /mnt /media -name "show-build" -type d 2>/dev/null | grep -i "windows\|J_drive" | head -1)
    echo "✓ Detected network share: $SHARE_PATH"
fi

# Check for SSH access
if command -v ssh >/dev/null && ssh -o ConnectTimeout=2 -o BatchMode=yes "${WINDOWS_USER}@${WINDOWS_HOST}" exit 2>/dev/null; then
    SYNC_METHOD="ssh"
    echo "✓ Detected SSH access to ${WINDOWS_USER}@${WINDOWS_HOST}"
fi

# Check for Git remote
if git remote -v | grep -q "windows\|HOME-MAIN"; then
    SYNC_METHOD="git"
    echo "✓ Detected Git remote for Windows worker"
fi

if [[ "$SYNC_METHOD" == "unknown" ]]; then
    echo "❌ ERROR: No sync method available"
    echo ""
    echo "Available options:"
    echo "  1. Mount Windows share: sudo mount -t cifs //HOME-MAIN/J /mnt/windows-share -o username=kevin"
    echo "  2. Configure SSH: ssh-copy-id ${WINDOWS_USER}@${WINDOWS_HOST}"
    echo "  3. Add Git remote: git remote add windows ssh://${WINDOWS_USER}@${WINDOWS_HOST}/J/show-build"
    exit 1
fi

echo ""
echo "Sync method: $SYNC_METHOD"
echo "Source: $LOCAL_CODE_PATH"
echo "Destination: $WINDOWS_CODE_PATH"
echo ""

# Perform sync based on method
case "$SYNC_METHOD" in
    share)
        echo "Syncing via network share..."
        rsync -av --delete \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.git' \
            "$LOCAL_CODE_PATH/" "$SHARE_PATH/app/"
        echo "✓ Files synced via network share"
        ;;

    ssh)
        echo "Syncing via SSH..."
        rsync -av --delete \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.git' \
            -e ssh \
            "$LOCAL_CODE_PATH/" "${WINDOWS_USER}@${WINDOWS_HOST}:${WINDOWS_CODE_PATH}/app/"
        echo "✓ Files synced via SSH"

        if [[ "$RESTART_WORKER" == true ]]; then
            echo ""
            echo "Restarting Windows worker..."
            ssh "${WINDOWS_USER}@${WINDOWS_HOST}" "cd ${WINDOWS_CODE_PATH} && taskkill /F /IM celery.exe 2>nul; timeout 2; start cmd /c start_worker.bat"
            echo "✓ Worker restart initiated"
        fi
        ;;

    git)
        echo "Syncing via Git..."
        # Commit changes
        if [[ -n "$(git status --porcelain)" ]]; then
            git add -A
            git commit -m "Auto-sync: Windows worker update $(date '+%Y-%m-%d %H:%M:%S')"
        fi

        # Push to Windows remote
        git push windows dev-fork 2>&1 || {
            echo "⚠️  Git push failed - Windows worker may need to pull manually"
            echo "Run on Windows: cd J:\\show-build && git pull origin dev-fork"
        }
        echo "✓ Changes pushed to Windows Git remote"
        ;;
esac

echo ""
echo "=========================================="
echo "Sync Complete!"
echo "=========================================="
echo ""

if [[ "$RESTART_WORKER" == false && "$SYNC_METHOD" == "ssh" ]]; then
    echo "💡 Tip: Add --restart flag to automatically restart worker"
fi

echo ""
echo "Next steps:"
echo "  1. On Windows: Press Ctrl+C to stop worker"
echo "  2. Run: .\\start_worker.bat"
echo "  3. Verify worker connects successfully"
echo ""
