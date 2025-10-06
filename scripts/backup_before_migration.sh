#!/bin/bash
"""
Database backup script for critical tables before migrations
Run this before major migrations to ensure data safety
"""

set -e  # Exit on any error

# Configuration
BACKUP_DIR="/mnt/sync/disaffected/backups/$(date +%Y%m%d_%H%M%S)"
DB_USER="showbuild"
DB_NAME="showbuild"
CONTAINER_NAME="show-build-postgres"

# Critical tables to backup
CRITICAL_TABLES=(
    "users"
    "settings" 
    "episodes_legacy"
    "rundown_items_legacy"
    "assets"
    "processing_jobs"
    "extracted_quotes"
    "organizations"
    "shows"
    "episodes"
    "rundown_items"
    "permissions"
    "roles"
    "groups"
    "user_roles"
    "user_groups"
    "role_permissions"
    "group_roles"
    "group_permissions" 
    "user_permissions"
    "audit_logs"
)

echo "🗂️  Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

echo "📋 Creating backup manifest..."
cat > "$BACKUP_DIR/backup_manifest.txt" << EOF
# Database Backup Manifest
# Created: $(date)
# Database: $DB_NAME
# Container: $CONTAINER_NAME
# 
# Tables backed up:
EOF

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: PostgreSQL container '$CONTAINER_NAME' is not running"
    echo "   Start it with: docker compose up -d postgres"
    exit 1
fi

echo "🗄️  Backing up critical tables..."

# Backup each table individually
for table in "${CRITICAL_TABLES[@]}"; do
    echo "   Backing up table: $table"
    
    # Check if table exists
    table_exists=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '$table');" | tr -d ' \n')
    
    if [ "$table_exists" = "t" ]; then
        # Get row count
        row_count=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM $table;" | tr -d ' \n')
        
        # Backup table structure and data
        docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" -t "$table" --inserts > "$BACKUP_DIR/${table}.sql"
        
        # Log to manifest
        echo "- $table ($row_count rows) -> ${table}.sql" >> "$BACKUP_DIR/backup_manifest.txt"
        
        echo "   ✅ $table ($row_count rows)"
    else
        echo "   ⚠️  Table $table does not exist, skipping"
        echo "- $table (NOT FOUND)" >> "$BACKUP_DIR/backup_manifest.txt"
    fi
done

# Create full schema backup
echo "📐 Backing up complete database schema..."
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" --schema-only > "$BACKUP_DIR/schema_full.sql"

# Create restore script
echo "📝 Creating restore script..."
cat > "$BACKUP_DIR/restore_backup.sh" << 'EOF'
#!/bin/bash
# Database Restore Script
# Generated automatically during backup

set -e

CONTAINER_NAME="show-build-postgres"
DB_USER="showbuild" 
DB_NAME="showbuild"
BACKUP_DIR="$(dirname "$0")"

echo "🔄 Database Restore Utility"
echo "   Backup created: $(basename "$BACKUP_DIR")"
echo ""
echo "⚠️  WARNING: This will overwrite existing data!"
echo "   Make sure you have a current backup before proceeding."
echo ""
read -p "Continue with restore? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo "🗄️  Restoring database from backup..."

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: PostgreSQL container '$CONTAINER_NAME' is not running"
    exit 1
fi

# Restore each table
for sql_file in "$BACKUP_DIR"/*.sql; do
    if [[ "$sql_file" != *"schema_full.sql"* ]]; then
        table_name=$(basename "$sql_file" .sql)
        echo "   Restoring table: $table_name"
        
        # Drop and recreate table to avoid conflicts
        docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "DROP TABLE IF EXISTS $table_name CASCADE;" || true
        
        # Restore table
        docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$sql_file"
        
        echo "   ✅ $table_name restored"
    fi
done

echo "✅ Database restore completed!"
EOF

chmod +x "$BACKUP_DIR/restore_backup.sh"

# Create verification script
cat > "$BACKUP_DIR/verify_backup.sh" << 'EOF'
#!/bin/bash
# Backup Verification Script

set -e

CONTAINER_NAME="show-build-postgres"
DB_USER="showbuild"
DB_NAME="showbuild" 
BACKUP_DIR="$(dirname "$0")"

echo "🔍 Verifying backup integrity..."

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: PostgreSQL container '$CONTAINER_NAME' is not running"
    exit 1
fi

# Verify each backup file
for sql_file in "$BACKUP_DIR"/*.sql; do
    if [[ "$sql_file" != *"schema_full.sql"* ]]; then
        table_name=$(basename "$sql_file" .sql)
        
        # Check if backup file is valid SQL
        if ! grep -q "CREATE TABLE\|INSERT INTO" "$sql_file"; then
            echo "   ⚠️  Warning: $table_name backup may be incomplete"
        else
            echo "   ✅ $table_name backup appears valid"
        fi
    fi
done

echo "✅ Backup verification completed!"
EOF

chmod +x "$BACKUP_DIR/verify_backup.sh"

# Final backup summary
echo ""
echo "✅ Backup completed successfully!"
echo "   📁 Location: $BACKUP_DIR"
echo "   📋 Manifest: $BACKUP_DIR/backup_manifest.txt"
echo "   🔄 Restore: $BACKUP_DIR/restore_backup.sh"
echo "   🔍 Verify: $BACKUP_DIR/verify_backup.sh"
echo ""
echo "🛡️  Your data is now safely backed up before migration!"

# Show backup size
backup_size=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "   💾 Backup size: $backup_size"

# Verify the backup
echo ""
echo "🔍 Running backup verification..."
"$BACKUP_DIR/verify_backup.sh"