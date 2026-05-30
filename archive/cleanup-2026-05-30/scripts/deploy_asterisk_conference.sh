#!/bin/bash
# ============================================================================
# Deploy Show-Build Conference System to Asterisk Server
# Target: 192.168.51.223
# ============================================================================

set -e

ASTERISK_HOST="192.168.51.223"
ASTERISK_USER="root"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Show-Build Conference Deployment"
echo "Target: ${ASTERISK_HOST}"
echo "=========================================="

# Check if we can reach the server
echo ""
echo "[1/7] Testing connectivity to Asterisk server..."
if ! ping -c 1 -W 2 ${ASTERISK_HOST} > /dev/null 2>&1; then
    echo "ERROR: Cannot reach ${ASTERISK_HOST}"
    exit 1
fi
echo "✓ Server reachable"

# Copy PIN validator script
echo ""
echo "[2/7] Deploying PIN validator script..."
scp ${SCRIPT_DIR}/asterisk_pin_validator.py ${ASTERISK_USER}@${ASTERISK_HOST}:/usr/local/bin/
ssh ${ASTERISK_USER}@${ASTERISK_HOST} "chmod +x /usr/local/bin/asterisk_pin_validator.py"
echo "✓ PIN validator deployed"

# Copy dialplan configuration
echo ""
echo "[3/7] Deploying dialplan configuration..."
scp ${SCRIPT_DIR}/asterisk_conference_dialplan.conf ${ASTERISK_USER}@${ASTERISK_HOST}:/etc/asterisk/extensions_showbuild.conf
echo "✓ Dialplan deployed"

# Backup existing extensions.conf
echo ""
echo "[4/7] Backing up existing extensions.conf..."
ssh ${ASTERISK_USER}@${ASTERISK_HOST} "cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup-\$(date +%Y%m%d-%H%M%S)"
echo "✓ Backup created"

# Add include directive if not already present
echo ""
echo "[5/7] Adding include directive to extensions.conf..."
ssh ${ASTERISK_USER}@${ASTERISK_HOST} "grep -q 'extensions_showbuild.conf' /etc/asterisk/extensions.conf || echo -e '\n; Show-Build Conference Integration\n#include extensions_showbuild.conf' >> /etc/asterisk/extensions.conf"
echo "✓ Include directive added"

# Configure ConfBridge (backup first)
echo ""
echo "[6/7] Configuring ConfBridge..."
ssh ${ASTERISK_USER}@${ASTERISK_HOST} << 'EOF'
    # Backup confbridge.conf
    if [ -f /etc/asterisk/confbridge.conf ]; then
        cp /etc/asterisk/confbridge.conf /etc/asterisk/confbridge.conf.backup-$(date +%Y%m%d-%H%M%S)
    fi

    # Add Show-Build profiles if not present
    if ! grep -q "\[default_bridge\]" /etc/asterisk/confbridge.conf 2>/dev/null; then
        cat >> /etc/asterisk/confbridge.conf << 'CONFEOF'

; ============================================================================
; Show-Build Conference Profiles
; ============================================================================

[default_bridge]
type=bridge
max_members=50
record_conference=yes
record_file=/var/spool/asterisk/monitor/conf-${CONFBRIDGE(bridge,name)}-%Y%m%d-%H%M%S.wav
mixing_interval=20
video_mode=follow_talker

[default_user]
type=user
marked=no
startmuted=no
music_on_hold_when_empty=yes
quiet=no
announce_user_count=yes
announce_user_count_all=yes
announce_only_user=yes
dtmf_passthrough=yes
CONFEOF
    fi
EOF
echo "✓ ConfBridge configured"

# Reload Asterisk
echo ""
echo "[7/7] Reloading Asterisk..."
ssh ${ASTERISK_USER}@${ASTERISK_HOST} << 'EOF'
    asterisk -rx "dialplan reload"
    asterisk -rx "module reload app_confbridge"
    asterisk -rx "core show version"
EOF
echo "✓ Asterisk reloaded"

# Configure NFS server for recordings
echo ""
echo "[8/9] Configuring NFS server for recordings..."
ssh ${ASTERISK_USER}@${ASTERISK_HOST} << 'EOF'
    # Install NFS server if not present
    if ! command -v exportfs &> /dev/null; then
        apt-get update
        apt-get install -y nfs-kernel-server
    fi

    # Create recordings directory if it doesn't exist
    mkdir -p /var/spool/asterisk/monitor
    chown asterisk:asterisk /var/spool/asterisk/monitor
    chmod 755 /var/spool/asterisk/monitor

    # Export to Show-Build server
    EXPORT_LINE="/var/spool/asterisk/monitor 192.168.51.210(ro,sync,no_subtree_check)"
    if ! grep -q "/var/spool/asterisk/monitor" /etc/exports 2>/dev/null; then
        echo "${EXPORT_LINE}" >> /etc/exports
        exportfs -ra
        echo "✓ NFS export configured"
    else
        echo "✓ NFS export already configured"
    fi
EOF

echo ""
echo "[9/9] Verifying NFS export..."
if showmount -e ${ASTERISK_HOST} 2>/dev/null | grep -q "/var/spool/asterisk/monitor"; then
    echo "✓ NFS export verified"
else
    echo "WARNING: NFS export not visible yet (may need firewall configuration)"
fi

echo ""
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo ""
echo "Conference system is now active on:"
echo "  DID: +1-802-221-4885"
echo "  Server: ${ASTERISK_HOST}"
echo ""
echo "To test:"
echo "  1. Create conference in Show-Build UI"
echo "  2. Note the 6-digit PIN"
echo "  3. Dial +1-802-221-4885"
echo "  4. Enter PIN when prompted"
echo ""
echo "Next: Mount NFS share on Show-Build server:"
echo "  sudo ${SCRIPT_DIR}/setup_nfs_mount.sh"
echo "  docker compose restart server"
echo ""
echo "Logs:"
echo "  ssh ${ASTERISK_USER}@${ASTERISK_HOST} 'asterisk -rvvv'"
echo "  ssh ${ASTERISK_USER}@${ASTERISK_HOST} 'tail -f /var/log/asterisk/full'"
echo ""
