#!/bin/bash
# setup_nfs_infrastructure.sh
# Complete NFS infrastructure setup for Show-Build distributed processing
#
# This script sets up:
# 1. NFS server on whisper (this machine)
# 2. NFS client on kairo (remote worker)
# 3. Shared temp directories
# 4. Health monitoring
#
# Usage: sudo ./scripts/setup_nfs_infrastructure.sh
#
# Logs: /var/log/show-build/nfs_setup.log

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file location
LOG_DIR="/var/log/show-build"
LOG_FILE="$LOG_DIR/nfs_setup_$(date +%Y%m%d_%H%M%S).log"

# Create log directory
mkdir -p "$LOG_DIR"

# Function to log with timestamp and also display to console
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Write to log file
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"

    # Also display to console with colors
    case $level in
        INFO)
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        SUCCESS)
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        WARNING)
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
    esac
}

# Function to run command and log output
run_cmd() {
    local description="$1"
    shift
    local cmd="$@"

    log INFO "Running: $description"
    log INFO "Command: $cmd"

    # Run command and capture output
    if output=$($cmd 2>&1); then
        log SUCCESS "$description - Completed"
        echo "$output" >> "$LOG_FILE"
        return 0
    else
        log ERROR "$description - Failed"
        echo "$output" >> "$LOG_FILE"
        return 1
    fi
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log ERROR "This script must be run as root (use sudo)"
        exit 1
    fi
    log SUCCESS "Running as root"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Header
echo "============================================================"
echo "  Show-Build NFS Infrastructure Setup"
echo "  $(date)"
echo "============================================================"
echo ""
log INFO "Starting NFS infrastructure setup"
log INFO "Log file: $LOG_FILE"
echo ""

# Check root
check_root

# Detect original user (who ran sudo)
if [ -n "$SUDO_USER" ]; then
    ORIGINAL_USER="$SUDO_USER"
    log INFO "Original user: $ORIGINAL_USER"
else
    log ERROR "Cannot detect original user - script must be run with sudo"
    exit 1
fi

# Get original user's home directory
ORIGINAL_HOME=$(eval echo ~$ORIGINAL_USER)

# Function to run SSH as original user (not root)
ssh_as_user() {
    sudo -u "$ORIGINAL_USER" -H ssh "$@"
}

# Function to run SCP as original user
scp_as_user() {
    sudo -u "$ORIGINAL_USER" -H scp "$@"
}

# ============================================================
# PHASE 1: NFS SERVER SETUP (WHISPER)
# ============================================================

log INFO "=== PHASE 1: NFS Server Setup (Whisper) ==="
echo ""

# Step 1: Install NFS server
log INFO "Step 1: Installing NFS server packages"
if ! dpkg -l | grep -q nfs-kernel-server; then
    run_cmd "Update package list" apt update
    run_cmd "Install nfs-kernel-server" apt install -y nfs-kernel-server
else
    log INFO "NFS server already installed, skipping"
fi

# Step 2: Backup existing exports
if [ -f /etc/exports ]; then
    backup_file="/etc/exports.backup.$(date +%Y%m%d_%H%M%S)"
    log INFO "Backing up /etc/exports to $backup_file"
    cp /etc/exports "$backup_file"
    log SUCCESS "Backup created: $backup_file"
fi

# Step 3: Configure exports
log INFO "Step 2: Configuring NFS exports"
export_line="/mnt/sync 192.168.51.0/24(rw,sync,no_subtree_check,no_root_squash)"

if grep -q "^/mnt/sync" /etc/exports 2>/dev/null; then
    log WARNING "/mnt/sync already exported, skipping"
else
    echo "$export_line" >> /etc/exports
    log SUCCESS "Added export: $export_line"
fi

# Step 4: Apply exports
log INFO "Step 3: Applying NFS exports"
run_cmd "Reload NFS exports" exportfs -a

# Step 5: Show active exports
log INFO "Active NFS exports:"
exportfs -v >> "$LOG_FILE"
exportfs -v

# Step 6: Enable and start NFS server
log INFO "Step 4: Starting NFS server"
run_cmd "Enable NFS server on boot" systemctl enable nfs-kernel-server
run_cmd "Start NFS server" systemctl start nfs-kernel-server

# Step 7: Check NFS server status
log INFO "Checking NFS server status:"
systemctl status nfs-kernel-server --no-pager >> "$LOG_FILE"
if systemctl is-active --quiet nfs-kernel-server; then
    log SUCCESS "NFS server is running"
else
    log ERROR "NFS server is not running"
    exit 1
fi

# Step 8: Create shared temp directory
log INFO "Step 5: Creating shared temp directories"
mkdir -p /mnt/sync/temp/uploads
chmod 777 /mnt/sync/temp/uploads
log SUCCESS "Created /mnt/sync/temp/uploads (chmod 777)"

mkdir -p /mnt/sync/temp/processing
chmod 777 /mnt/sync/temp/processing
log SUCCESS "Created /mnt/sync/temp/processing (chmod 777)"

# Step 9: Check if firewall is active
log INFO "Step 6: Checking firewall configuration"
if command_exists ufw && ufw status | grep -q "Status: active"; then
    log INFO "UFW firewall is active"

    # Check if NFS rule already exists
    if ufw status | grep -q "2049"; then
        log INFO "NFS firewall rule already exists"
    else
        log INFO "Adding NFS firewall rule"
        ufw allow from 192.168.51.0/24 to any port nfs
        ufw reload
        log SUCCESS "NFS firewall rule added"
    fi
else
    log INFO "UFW firewall not active, skipping firewall configuration"
fi

# Step 10: Verify NFS port is listening
log INFO "Step 7: Verifying NFS port 2049 is listening"
if ss -tulpn | grep -q ":2049"; then
    log SUCCESS "NFS port 2049 is listening"
    ss -tulpn | grep ":2049" >> "$LOG_FILE"
else
    log WARNING "NFS port 2049 is not listening - may indicate a problem"
fi

echo ""
log SUCCESS "=== PHASE 1 COMPLETE: NFS Server Setup ==="
echo ""

# ============================================================
# PHASE 2: NFS CLIENT SETUP (KAIRO)
# ============================================================

log INFO "=== PHASE 2: NFS Client Setup (Kairo) ==="
echo ""

# Step 1: Check SSH connectivity to kairo
log INFO "Step 1: Checking SSH connectivity to kairo"
if ssh_as_user -o ConnectTimeout=5 kairo "echo 'SSH OK'" >/dev/null 2>&1; then
    log SUCCESS "SSH connection to kairo successful"
else
    log ERROR "Cannot connect to kairo via SSH"
    log ERROR "Please ensure:"
    log ERROR "  1. kairo is accessible"
    log ERROR "  2. SSH key is configured (~/.ssh/id_ed25519)"
    log ERROR "  3. Host alias 'kairo' exists in ~/.ssh/config"
    exit 1
fi

# Step 1.5: Get sudo password for kairo
log INFO "Kairo requires sudo access for NFS setup"
echo ""
echo -n "Enter sudo password for kairo@kairo: "
read -s KAIRO_SUDO_PASSWORD
echo ""
echo ""

# Test sudo password
log INFO "Testing sudo password..."
if echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "sudo -S -k whoami" 2>/dev/null | grep -q "root"; then
    log SUCCESS "Sudo password verified"
else
    log ERROR "Sudo password incorrect or sudo not configured"
    exit 1
fi

# Step 2: Install NFS client on kairo
log INFO "Step 2: Installing NFS client on kairo"
echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "sudo -S apt update" >> "$LOG_FILE" 2>&1
log INFO "Updated package list on kairo"

if ssh_as_user kairo "dpkg -l | grep -q nfs-common"; then
    log INFO "nfs-common already installed on kairo, skipping"
else
    echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "sudo -S apt install -y nfs-common" >> "$LOG_FILE" 2>&1
    log SUCCESS "Installed nfs-common on kairo"
fi

# Step 3: Create mount point on kairo
log INFO "Step 3: Creating mount point on kairo"
echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "sudo -S mkdir -p /mnt/sync" >> "$LOG_FILE" 2>&1
log SUCCESS "Created /mnt/sync on kairo"

# Step 4: Test NFS mount manually
log INFO "Step 4: Testing NFS mount on kairo"
if ssh_as_user kairo "mountpoint -q /mnt/sync"; then
    log WARNING "/mnt/sync already mounted on kairo, unmounting first"
    echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "sudo -S umount /mnt/sync" >> "$LOG_FILE" 2>&1
fi

log INFO "Mounting whisper:/mnt/sync to kairo:/mnt/sync"
if echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "sudo -S mount -t nfs whisper:/mnt/sync /mnt/sync" >> "$LOG_FILE" 2>&1; then
    log SUCCESS "Test mount successful"
else
    log ERROR "Test mount failed"
    log ERROR "Check log file for details: $LOG_FILE"
    exit 1
fi

# Step 5: Verify mount and access
log INFO "Step 5: Verifying NFS mount on kairo"
if ssh_as_user kairo "mountpoint -q /mnt/sync"; then
    log SUCCESS "NFS mount verified"
else
    log ERROR "Mount verification failed"
    exit 1
fi

# Test read access
log INFO "Testing read access on kairo"
if ssh_as_user kairo "ls -la /mnt/sync/disaffected/episodes" >> "$LOG_FILE" 2>&1; then
    log SUCCESS "Read access verified"
else
    log WARNING "Cannot read episodes directory - may not exist yet"
fi

# Test write access
log INFO "Testing write access on kairo"
test_file="/mnt/sync/temp/.nfs_test_$(date +%s)"
if ssh_as_user kairo "touch $test_file && rm $test_file" >> "$LOG_FILE" 2>&1; then
    log SUCCESS "Write access verified"
else
    log ERROR "Write access failed - check NFS permissions"
    exit 1
fi

# Step 6: Add to fstab for automatic mounting
log INFO "Step 6: Configuring automatic mount on boot (fstab)"

# Backup fstab first
echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "sudo -S cp /etc/fstab /etc/fstab.backup.\$(date +%Y%m%d_%H%M%S)" >> "$LOG_FILE" 2>&1
log INFO "Backed up /etc/fstab on kairo"

fstab_entry="whisper:/mnt/sync /mnt/sync nfs defaults,_netdev 0 0"

if ssh_as_user kairo "grep -q 'whisper:/mnt/sync' /etc/fstab"; then
    log WARNING "NFS entry already exists in /etc/fstab, skipping"
else
    echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "echo '$fstab_entry' | sudo -S tee -a /etc/fstab" >> "$LOG_FILE" 2>&1
    log SUCCESS "Added NFS mount to /etc/fstab"
fi

# Step 7: Test fstab mount
log INFO "Step 7: Testing fstab mount"
echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "sudo -S umount /mnt/sync" >> "$LOG_FILE" 2>&1
log INFO "Unmounted /mnt/sync"

if echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "sudo -S mount -a" >> "$LOG_FILE" 2>&1; then
    log SUCCESS "fstab mount test successful"
else
    log ERROR "fstab mount test failed"
    exit 1
fi

# Verify mount again
if ssh_as_user kairo "mountpoint -q /mnt/sync"; then
    log SUCCESS "NFS mount verified after fstab test"
else
    log ERROR "Mount verification failed after fstab test"
    exit 1
fi

echo ""
log SUCCESS "=== PHASE 2 COMPLETE: NFS Client Setup ==="
echo ""

# ============================================================
# PHASE 3: DOCKER INTEGRATION
# ============================================================

log INFO "=== PHASE 3: Docker Integration ==="
echo ""

# Step 1: Check if Celery worker container exists on kairo
log INFO "Step 1: Checking for Celery worker on kairo"
if ssh_as_user kairo "docker ps -a --filter 'name=celery' --format '{{.Names}}'" | grep -q celery; then
    log SUCCESS "Found Celery worker container on kairo"
    worker_name=$(ssh_as_user kairo "docker ps -a --filter 'name=celery' --format '{{.Names}}'" | head -1)
    log INFO "Worker container: $worker_name"

    # Show current mounts
    log INFO "Current volume mounts:"
    ssh_as_user kairo "docker inspect $worker_name --format='{{range .Mounts}}{{.Source}} -> {{.Destination}}\n{{end}}'" >> "$LOG_FILE"
    ssh_as_user kairo "docker inspect $worker_name --format='{{range .Mounts}}{{.Source}} -> {{.Destination}}\n{{end}}'"

    # Restart worker to pick up new mounts
    log INFO "Restarting worker to apply NFS mounts"
    ssh_as_user kairo "docker restart $worker_name" >> "$LOG_FILE" 2>&1
    log SUCCESS "Worker restarted"

    # Wait for container to be ready
    sleep 3

    # Verify worker can access NFS
    log INFO "Verifying worker can access NFS mount"
    if ssh_as_user kairo "docker exec $worker_name ls /home/episodes" >> "$LOG_FILE" 2>&1; then
        log SUCCESS "Worker can access /home/episodes"
    else
        log WARNING "Worker cannot access /home/episodes - may need docker-compose update"
    fi
else
    log INFO "No Celery worker found on kairo - will be configured during deployment"
fi

# Step 2: Update whisper server to use shared temp
log INFO "Step 2: Checking whisper server configuration"
if [ -f /mnt/process/show-build/docker-compose.yml ]; then
    log INFO "Found docker-compose.yml"

    # Check if already configured
    if grep -q "/mnt/sync/temp/uploads:/tmp/sot_uploads" /mnt/process/show-build/docker-compose.yml; then
        log INFO "Shared temp already configured in docker-compose.yml"
    else
        log WARNING "Shared temp not configured in docker-compose.yml"
        log INFO "You may need to add this volume mount to the server container:"
        log INFO "  - /mnt/sync/temp/uploads:/tmp/sot_uploads:rw"
    fi
else
    log WARNING "docker-compose.yml not found at /mnt/process/show-build/"
fi

echo ""
log SUCCESS "=== PHASE 3 COMPLETE: Docker Integration ==="
echo ""

# ============================================================
# PHASE 4: HEALTH MONITORING SETUP
# ============================================================

log INFO "=== PHASE 4: Health Monitoring Setup ==="
echo ""

# Step 1: Create NFS health check script
log INFO "Step 1: Creating NFS health check script"
cat > /usr/local/bin/check_nfs_mount.sh << 'HEALTH_SCRIPT'
#!/bin/bash
# NFS mount health check for Show-Build workers

MOUNT_POINT="/mnt/sync"
NFS_SERVER="whisper:/mnt/sync"
LOG_FILE="/var/log/show-build/nfs_health.log"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if mount is active
if ! mountpoint -q "$MOUNT_POINT"; then
    log "ERROR: NFS mount is DOWN"
    log "Attempting to mount..."
    mount -a

    if ! mountpoint -q "$MOUNT_POINT"; then
        log "CRITICAL: Failed to mount NFS share"
        exit 1
    fi
fi

# Test read access
if ! ls "$MOUNT_POINT/disaffected/episodes" > /dev/null 2>&1; then
    log "ERROR: Cannot read NFS mount"
    exit 1
fi

# Test write access
TEST_FILE="$MOUNT_POINT/temp/.health_check_$(date +%s)"
if ! touch "$TEST_FILE" 2>/dev/null; then
    log "ERROR: Cannot write to NFS mount"
    exit 1
fi
rm -f "$TEST_FILE"

log "OK: NFS mount is healthy"
exit 0
HEALTH_SCRIPT

chmod +x /usr/local/bin/check_nfs_mount.sh
log SUCCESS "Created /usr/local/bin/check_nfs_mount.sh"

# Step 2: Copy health check script to kairo
log INFO "Step 2: Installing health check on kairo"
scp_as_user /usr/local/bin/check_nfs_mount.sh kairo:/tmp/ >> "$LOG_FILE" 2>&1
echo "$KAIRO_SUDO_PASSWORD" | ssh_as_user kairo "sudo -S mv /tmp/check_nfs_mount.sh /usr/local/bin/ && sudo -S chmod +x /usr/local/bin/check_nfs_mount.sh" >> "$LOG_FILE" 2>&1
log SUCCESS "Installed health check on kairo"

# Step 3: Add to cron on kairo
log INFO "Step 3: Configuring cron job on kairo (every 5 minutes)"
ssh_as_user kairo "(crontab -l 2>/dev/null | grep -v 'check_nfs_mount.sh'; echo '*/5 * * * * /usr/local/bin/check_nfs_mount.sh') | crontab -" >> "$LOG_FILE" 2>&1
log SUCCESS "Cron job configured on kairo"

# Step 4: Test health check
log INFO "Step 4: Testing health check on kairo"
if ssh_as_user kairo "/usr/local/bin/check_nfs_mount.sh" >> "$LOG_FILE" 2>&1; then
    log SUCCESS "Health check passed on kairo"
else
    log ERROR "Health check failed on kairo"
fi

echo ""
log SUCCESS "=== PHASE 4 COMPLETE: Health Monitoring ==="
echo ""

# ============================================================
# FINAL VERIFICATION
# ============================================================

log INFO "=== FINAL VERIFICATION ==="
echo ""

# Check 1: NFS server status
log INFO "Check 1: NFS server status on whisper"
if systemctl is-active --quiet nfs-kernel-server; then
    log SUCCESS "✓ NFS server is running"
else
    log ERROR "✗ NFS server is not running"
fi

# Check 2: NFS exports
log INFO "Check 2: NFS exports on whisper"
if showmount -e localhost | grep -q "/mnt/sync"; then
    log SUCCESS "✓ /mnt/sync is exported"
else
    log ERROR "✗ /mnt/sync is not exported"
fi

# Check 3: NFS mount on kairo
log INFO "Check 3: NFS mount on kairo"
if ssh_as_user kairo "mountpoint -q /mnt/sync"; then
    log SUCCESS "✓ NFS is mounted on kairo"
else
    log ERROR "✗ NFS is not mounted on kairo"
fi

# Check 4: Read access from kairo
log INFO "Check 4: Read access from kairo"
if ssh_as_user kairo "ls /mnt/sync/disaffected/episodes" >> "$LOG_FILE" 2>&1; then
    log SUCCESS "✓ Kairo can read episodes directory"
else
    log WARNING "⚠ Kairo cannot read episodes directory (may be empty)"
fi

# Check 5: Write access from kairo
log INFO "Check 5: Write access from kairo"
test_file="/mnt/sync/temp/.final_test_$(date +%s)"
if ssh_as_user kairo "touch $test_file && rm $test_file" >> "$LOG_FILE" 2>&1; then
    log SUCCESS "✓ Kairo can write to shared temp"
else
    log ERROR "✗ Kairo cannot write to shared temp"
fi

# Check 6: Docker worker
log INFO "Check 6: Docker worker on kairo"
if ssh_as_user kairo "docker ps --filter 'name=celery' --format '{{.Names}}'" | grep -q celery; then
    worker_name=$(ssh_as_user kairo "docker ps --filter 'name=celery' --format '{{.Names}}'" | head -1)

    # Check if worker is running
    if ssh_as_user kairo "docker ps --filter 'name=$worker_name' --format '{{.Status}}'" | grep -q "Up"; then
        log SUCCESS "✓ Celery worker is running"
    else
        log WARNING "⚠ Celery worker exists but is not running"
    fi

    # Check if worker can access NFS
    if ssh_as_user kairo "docker exec $worker_name ls /home/episodes" >> "$LOG_FILE" 2>&1; then
        log SUCCESS "✓ Worker can access NFS mount"
    else
        log WARNING "⚠ Worker cannot access NFS mount"
    fi
else
    log INFO "ℹ No Celery worker deployed yet"
fi

echo ""
log INFO "=== SETUP COMPLETE ==="
echo ""
echo "============================================================"
log SUCCESS "NFS infrastructure setup completed successfully!"
echo "============================================================"
echo ""
log INFO "Summary:"
log INFO "  - NFS server running on whisper (192.168.51.197)"
log INFO "  - NFS client configured on kairo"
log INFO "  - Shared storage: /mnt/sync"
log INFO "  - Shared temp: /mnt/sync/temp/uploads"
log INFO "  - Health monitoring active (every 5 minutes)"
echo ""
log INFO "Next steps:"
log INFO "  1. Review log file: $LOG_FILE"
log INFO "  2. Update docker-compose.yml to use /mnt/sync/temp/uploads"
log INFO "  3. Restart Show-Build server: docker compose restart server"
log INFO "  4. Test SOT upload workflow"
echo ""
log INFO "Documentation:"
log INFO "  - NFS Infrastructure: /mnt/process/show-build/NFS_INFRASTRUCTURE_UFDP.md"
log INFO "  - Media Processing: /mnt/process/show-build/MEDIA_PROCESSING_WORKFLOW_UFDP.md"
log INFO "  - UFDP Index: /mnt/process/show-build/UFDP_INDEX.md"
echo ""
log INFO "Full log saved to: $LOG_FILE"
echo ""
