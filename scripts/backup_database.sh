#!/bin/bash
#
# Show-Build Database Backup System
# Creates compressed database dumps and syncs with remote system
#

set -e

# Configuration
BACKUP_DIR="/mnt/process/show-build/backups"
REMOTE_HOST="pmw@pmw-rm4"
REMOTE_BACKUP_DIR="/home/pmw/show-build-backups"
DB_NAME="showbuild"
DB_USER="showbuild"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="showbuild_backup_${TIMESTAMP}.sql.gz"
LOG_FILE="/mnt/process/show-build/backup.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup directories
mkdir -p "$BACKUP_DIR"
ssh "$REMOTE_HOST" "mkdir -p $REMOTE_BACKUP_DIR" 2>/dev/null || true

log "🔄 Starting database backup: $BACKUP_FILE"

# Create database dump
if docker exec show-build-postgres pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists | gzip > "$BACKUP_DIR/$BACKUP_FILE"; then
    log "✅ Database dump created: $(du -sh "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)"
else
    log "❌ Database dump failed"
    exit 1
fi

# Verify backup integrity
if gunzip -t "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null; then
    log "✅ Backup integrity verified"
else
    log "❌ Backup integrity check failed"
    exit 1
fi

# Sync to remote system
log "🔄 Syncing backup to remote system..."
if scp "$BACKUP_DIR/$BACKUP_FILE" "$REMOTE_HOST:$REMOTE_BACKUP_DIR/"; then
    log "✅ Backup synced to remote: $REMOTE_HOST:$REMOTE_BACKUP_DIR/$BACKUP_FILE"
else
    log "⚠️ Remote sync failed, backup exists locally only"
fi

# Cleanup old backups (keep last 10)
log "🧹 Cleaning up old backups..."
cd "$BACKUP_DIR"
ls -t showbuild_backup_*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
KEPT=$(ls -t showbuild_backup_*.sql.gz 2>/dev/null | wc -l)
log "📊 Kept $KEPT recent backups locally"

# Remote cleanup
ssh "$REMOTE_HOST" "cd $REMOTE_BACKUP_DIR && ls -t showbuild_backup_*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm -f" 2>/dev/null || true

# Final status
BACKUP_SIZE=$(du -sh "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
log "✅ Backup complete: $BACKUP_FILE ($BACKUP_SIZE)"

# Send notification to pmw-rm4 Claude
echo "Backup completed: $BACKUP_FILE ($BACKUP_SIZE) - $(date)" > /tmp/backup_notification.txt
scp /tmp/backup_notification.txt "$REMOTE_HOST:~/BACKUP_STATUS.txt" 2>/dev/null || true
rm -f /tmp/backup_notification.txt

log "🎯 Mission accomplished!"