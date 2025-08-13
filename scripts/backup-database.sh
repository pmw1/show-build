#!/bin/bash

# Show-Build Database Backup Script
# Multi-site redundant backup system

set -e

# Configuration
CONFIG_DIR="/app/config"
BACKUP_DIR="/mnt/sync/disaffected/backups"
LOG_FILE="/var/log/show-build-backup.log"
RETENTION_DAYS=30

# Database connection settings
DB_HOST="${DB_HOST:-10.0.1.1}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-showbuild}"
DB_USER="${DB_USER:-showbuild}"
DB_PASSWORD="${DB_PASSWORD:-showbuild_primary_2025}"

# Site configuration
SITE_NAME="${SITE_NAME:-ravena}"
BACKUP_REMOTE_SITES="${BACKUP_REMOTE_SITES:-burlington:10.0.2.1 montpelier:10.0.3.1}"

# Functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

create_backup_dirs() {
    log "Creating backup directories..."
    mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly,config}
    mkdir -p "/tmp/backup-staging"
}

backup_database() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/daily/showbuild_${SITE_NAME}_${timestamp}.sql"
    
    log "Starting database backup..."
    
    # Set password for non-interactive backup
    export PGPASSWORD="$DB_PASSWORD"
    
    # Create database backup
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --clean --create --if-exists \
        --format=custom --compress=9 \
        --file="$backup_file" 2>>"$LOG_FILE"; then
        
        log "Database backup completed: $backup_file"
        
        # Get backup size
        local size=$(du -h "$backup_file" | cut -f1)
        log "Backup size: $size"
        
        # Test backup integrity
        if pg_restore --list "$backup_file" >/dev/null 2>&1; then
            log "Backup integrity verified"
            echo "$backup_file"
        else
            error_exit "Backup integrity check failed"
        fi
    else
        error_exit "Database backup failed"
    fi
}

backup_configuration() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local config_backup="$BACKUP_DIR/config/config_${SITE_NAME}_${timestamp}.tar.gz"
    
    log "Backing up configuration files..."
    
    if [ -d "$CONFIG_DIR" ]; then
        tar -czf "$config_backup" -C "$CONFIG_DIR" . 2>>"$LOG_FILE"
        log "Configuration backup completed: $config_backup"
        echo "$config_backup"
    else
        log "Warning: Config directory $CONFIG_DIR not found"
    fi
}

replicate_to_sites() {
    local db_backup="$1"
    local config_backup="$2"
    
    if [ -z "$BACKUP_REMOTE_SITES" ]; then
        log "No remote sites configured for backup replication"
        return 0
    fi
    
    log "Replicating backups to remote sites..."
    
    for site_config in $BACKUP_REMOTE_SITES; do
        IFS=':' read -r site_name site_ip <<< "$site_config"
        
        log "Replicating to site: $site_name ($site_ip)"
        
        # Test connectivity
        if ping -c 1 -W 2 "$site_ip" >/dev/null 2>&1; then
            # Create remote backup directory
            ssh -o ConnectTimeout=10 "backup@$site_ip" "mkdir -p /backup/remote/$SITE_NAME" 2>>"$LOG_FILE" || continue
            
            # Copy database backup
            if [ -n "$db_backup" ] && [ -f "$db_backup" ]; then
                scp -o ConnectTimeout=10 "$db_backup" "backup@$site_ip:/backup/remote/$SITE_NAME/" 2>>"$LOG_FILE" && \
                log "Database backup replicated to $site_name" || \
                log "Warning: Failed to replicate database backup to $site_name"
            fi
            
            # Copy config backup
            if [ -n "$config_backup" ] && [ -f "$config_backup" ]; then
                scp -o ConnectTimeout=10 "$config_backup" "backup@$site_ip:/backup/remote/$SITE_NAME/" 2>>"$LOG_FILE" && \
                log "Config backup replicated to $site_name" || \
                log "Warning: Failed to replicate config backup to $site_name"
            fi
        else
            log "Warning: Site $site_name ($site_ip) is unreachable"
        fi
    done
}

cleanup_old_backups() {
    log "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
    
    # Clean daily backups
    find "$BACKUP_DIR/daily" -name "showbuild_*.sql" -mtime +$RETENTION_DAYS -delete 2>>"$LOG_FILE" || true
    
    # Clean config backups
    find "$BACKUP_DIR/config" -name "config_*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>>"$LOG_FILE" || true
    
    # Keep weekly backups for 3 months
    find "$BACKUP_DIR/weekly" -name "*.sql" -mtime +90 -delete 2>>"$LOG_FILE" || true
    
    # Keep monthly backups for 1 year
    find "$BACKUP_DIR/monthly" -name "*.sql" -mtime +365 -delete 2>>"$LOG_FILE" || true
    
    log "Cleanup completed"
}

weekly_backup() {
    local db_backup="$1"
    local today=$(date '+%u')  # Day of week (1=Monday, 7=Sunday)
    
    if [ "$today" = "7" ]; then  # Sunday
        local weekly_backup="$BACKUP_DIR/weekly/showbuild_${SITE_NAME}_$(date '+%Y%V').sql"
        cp "$db_backup" "$weekly_backup" 2>>"$LOG_FILE"
        log "Weekly backup created: $weekly_backup"
    fi
}

monthly_backup() {
    local db_backup="$1"
    local today=$(date '+%d')
    
    if [ "$today" = "01" ]; then  # First day of month
        local monthly_backup="$BACKUP_DIR/monthly/showbuild_${SITE_NAME}_$(date '+%Y%m').sql"
        cp "$db_backup" "$monthly_backup" 2>>"$LOG_FILE"
        log "Monthly backup created: $monthly_backup"
    fi
}

verify_replication() {
    log "Verifying replication status..."
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # Check if this is the primary server
    local is_primary=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -t -c "SELECT NOT pg_is_in_recovery();" 2>/dev/null | tr -d ' ')
    
    if [ "$is_primary" = "t" ]; then
        log "Primary server - checking replication slots"
        
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            -c "SELECT slot_name, active, restart_lsn FROM pg_replication_slots;" \
            2>>"$LOG_FILE" || true
    else
        log "Replica server - checking replication lag"
        
        local lag=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            -t -c "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()));" \
            2>/dev/null | tr -d ' ')
        
        if [ -n "$lag" ] && [ "$lag" != "" ]; then
            log "Replication lag: ${lag} seconds"
            
            # Alert if lag is too high
            if (( $(echo "$lag > 300" | bc -l) )); then
                log "WARNING: High replication lag detected (${lag}s)"
            fi
        fi
    fi
}

generate_backup_report() {
    local db_backup="$1"
    local config_backup="$2"
    local report_file="$BACKUP_DIR/backup_report_$(date '+%Y%m%d').txt"
    
    {
        echo "Show-Build Backup Report"
        echo "======================="
        echo "Site: $SITE_NAME"
        echo "Date: $(date)"
        echo "Database Host: $DB_HOST:$DB_PORT"
        echo
        
        if [ -n "$db_backup" ] && [ -f "$db_backup" ]; then
            echo "Database Backup: $(basename "$db_backup")"
            echo "Size: $(du -h "$db_backup" | cut -f1)"
            echo "MD5: $(md5sum "$db_backup" | cut -d' ' -f1)"
        else
            echo "Database Backup: FAILED"
        fi
        
        if [ -n "$config_backup" ] && [ -f "$config_backup" ]; then
            echo "Config Backup: $(basename "$config_backup")"
            echo "Size: $(du -h "$config_backup" | cut -f1)"
        else
            echo "Config Backup: FAILED or SKIPPED"
        fi
        
        echo
        echo "Disk Usage:"
        df -h "$BACKUP_DIR"
        
        echo
        echo "Recent Backups:"
        ls -lht "$BACKUP_DIR/daily" | head -5
        
    } > "$report_file"
    
    log "Backup report generated: $report_file"
}

# Main execution
main() {
    log "Starting backup process for site: $SITE_NAME"
    
    # Check if backup is already running
    local pidfile="/var/run/show-build-backup.pid"
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            error_exit "Backup already running (PID: $pid)"
        fi
    fi
    echo $$ > "$pidfile"
    
    # Trap to cleanup on exit
    trap 'rm -f "$pidfile"' EXIT
    
    # Create directories
    create_backup_dirs
    
    # Verify replication status
    verify_replication
    
    # Create backups
    local db_backup=$(backup_database)
    local config_backup=$(backup_configuration)
    
    # Handle weekly/monthly backups
    weekly_backup "$db_backup"
    monthly_backup "$db_backup"
    
    # Replicate to remote sites
    replicate_to_sites "$db_backup" "$config_backup"
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Generate report
    generate_backup_report "$db_backup" "$config_backup"
    
    log "Backup process completed successfully"
}

# Handle command line arguments
case "${1:-}" in
    --daily)
        main
        ;;
    --weekly)
        RETENTION_DAYS=90
        main
        ;;
    --monthly)
        RETENTION_DAYS=365
        main
        ;;
    --restore)
        if [ -z "$2" ]; then
            echo "Usage: $0 --restore <backup_file>"
            exit 1
        fi
        # Restore functionality would go here
        echo "Restore functionality not implemented yet"
        echo "To restore manually:"
        echo "pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --clean --create '$2'"
        ;;
    --test)
        echo "Testing backup system..."
        DB_HOST="localhost"
        BACKUP_REMOTE_SITES=""
        main
        ;;
    *)
        echo "Show-Build Database Backup Script"
        echo "Usage: $0 [--daily|--weekly|--monthly|--restore <file>|--test]"
        echo
        echo "Options:"
        echo "  --daily   Run daily backup (default)"
        echo "  --weekly  Run weekly backup with extended retention"
        echo "  --monthly Run monthly backup with long retention"
        echo "  --restore Restore from backup file"
        echo "  --test    Test backup with local settings"
        echo
        echo "Environment Variables:"
        echo "  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD"
        echo "  SITE_NAME, BACKUP_REMOTE_SITES"
        exit 0
        ;;
esac