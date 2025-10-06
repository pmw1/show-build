#!/bin/bash
#
# Setup Backup Cron Jobs
# Monday 4am, Wednesday 4am, Saturday 6am, Sunday 4am
#

set -e

BACKUP_SCRIPT="/mnt/process/show-build/scripts/backup_database.sh"
CRON_USER="$(whoami)"

echo "🔄 Setting up database backup cron jobs..."

# Create crontab entries
CRON_ENTRIES="
# Show-Build Database Backups
0 4 * * 1 $BACKUP_SCRIPT >> /mnt/process/show-build/backup.log 2>&1  # Monday 4am
0 4 * * 3 $BACKUP_SCRIPT >> /mnt/process/show-build/backup.log 2>&1  # Wednesday 4am  
0 6 * * 6 $BACKUP_SCRIPT >> /mnt/process/show-build/backup.log 2>&1  # Saturday 6am
0 4 * * 0 $BACKUP_SCRIPT >> /mnt/process/show-build/backup.log 2>&1  # Sunday 4am
"

# Add to crontab (preserve existing entries)
(crontab -l 2>/dev/null | grep -v "Show-Build Database Backups" | grep -v "backup_database.sh" || true; echo "$CRON_ENTRIES") | crontab -

echo "✅ Cron jobs installed for user: $CRON_USER"
echo ""
echo "📅 Backup Schedule:"
echo "   Monday    4:00 AM"
echo "   Wednesday 4:00 AM" 
echo "   Saturday  6:00 AM"
echo "   Sunday    4:00 AM"
echo ""
echo "📋 Current crontab:"
crontab -l | grep -A5 -B1 "Show-Build" || echo "No Show-Build entries found"
echo ""
echo "📊 Test backup: $BACKUP_SCRIPT"