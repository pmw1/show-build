#!/bin/bash
# ============================================================================
# Setup NFS Mount for Asterisk Conference Recordings
# Host: 192.168.51.210 (Show-Build server)
# NFS Server: 192.168.51.223 (Asterisk server)
# ============================================================================

set -e

ASTERISK_HOST="192.168.51.223"
NFS_MOUNT_POINT="/mnt/asterisk/recordings"
NFS_EXPORT="/var/spool/asterisk/monitor"

echo "=========================================="
echo "NFS Mount Setup for Asterisk Recordings"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Install NFS client if not already installed
echo ""
echo "[1/5] Installing NFS client..."
if ! command -v mount.nfs &> /dev/null; then
    apt-get update
    apt-get install -y nfs-common
    echo "✓ NFS client installed"
else
    echo "✓ NFS client already installed"
fi

# Create mount point
echo ""
echo "[2/5] Creating mount point..."
mkdir -p ${NFS_MOUNT_POINT}
echo "✓ Mount point created: ${NFS_MOUNT_POINT}"

# Test NFS server availability
echo ""
echo "[3/5] Testing NFS server availability..."
if ! showmount -e ${ASTERISK_HOST} 2>/dev/null | grep -q "${NFS_EXPORT}"; then
    echo "WARNING: NFS export not yet available from ${ASTERISK_HOST}"
    echo "You need to configure NFS server on Asterisk first:"
    echo ""
    echo "  ssh root@${ASTERISK_HOST}"
    echo "  apt-get install nfs-kernel-server"
    echo "  echo '${NFS_EXPORT} 192.168.51.210(ro,sync,no_subtree_check)' >> /etc/exports"
    echo "  exportfs -ra"
    echo ""
    echo "After configuring the server, run this script again."
    exit 1
fi
echo "✓ NFS export verified"

# Mount the NFS share
echo ""
echo "[4/5] Mounting NFS share..."
if mountpoint -q ${NFS_MOUNT_POINT}; then
    echo "✓ Already mounted"
else
    mount -t nfs ${ASTERISK_HOST}:${NFS_EXPORT} ${NFS_MOUNT_POINT}
    echo "✓ NFS share mounted"
fi

# Add to /etc/fstab for persistence
echo ""
echo "[5/5] Adding to /etc/fstab for automatic mounting..."
FSTAB_ENTRY="${ASTERISK_HOST}:${NFS_EXPORT} ${NFS_MOUNT_POINT} nfs ro,defaults 0 0"
if grep -q "${NFS_MOUNT_POINT}" /etc/fstab; then
    echo "✓ Entry already exists in /etc/fstab"
else
    echo "${FSTAB_ENTRY}" >> /etc/fstab
    echo "✓ Added to /etc/fstab"
fi

# Test access
echo ""
echo "Testing NFS mount access..."
if [ -r ${NFS_MOUNT_POINT} ]; then
    echo "✓ NFS mount is readable"
    ls -la ${NFS_MOUNT_POINT} | head -5
else
    echo "WARNING: Cannot read NFS mount"
fi

echo ""
echo "=========================================="
echo "✓ NFS Mount Setup Complete!"
echo "=========================================="
echo ""
echo "Asterisk recordings will be available at:"
echo "  Host: ${NFS_MOUNT_POINT}"
echo "  Docker: /asterisk/recordings (read-only)"
echo ""
echo "Next steps:"
echo "  1. Restart Docker containers: docker compose restart server"
echo "  2. Recordings will be automatically accessible"
echo ""
