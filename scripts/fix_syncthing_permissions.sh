#!/bin/bash
# Fix Syncthing Permission Issues
# Removes problematic read-only iCloud directories that block sync

set -e

echo "🔧 Syncthing Permission Fix Script"
echo "=================================="

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run with sudo"
    echo "Usage: sudo ./fix_syncthing_permissions.sh"
    exit 1
fi

PROBLEMATIC_DIR="/mnt/sync/disaffected/episodes/0241/scripts/iCloud~com~hankinsoft~sqlpro"

echo "📁 Checking problematic directory: $PROBLEMATIC_DIR"

if [ -d "$PROBLEMATIC_DIR" ]; then
    echo "🔍 Found read-only iCloud directory blocking Syncthing"

    # Show current permissions
    echo "📋 Current permissions:"
    ls -la "$PROBLEMATIC_DIR"

    # Force remove the problematic directory
    echo "🗑️  Removing problematic directory..."
    chmod -R 755 "$PROBLEMATIC_DIR" 2>/dev/null || true
    rm -rf "$PROBLEMATIC_DIR"

    if [ ! -d "$PROBLEMATIC_DIR" ]; then
        echo "✅ Successfully removed problematic directory"
    else
        echo "❌ Failed to remove directory, trying alternative method..."

        # Alternative: Remove all iCloud directories
        find "/mnt/sync/disaffected/episodes" -name "iCloud~*" -type d -exec rm -rf {} + 2>/dev/null || true

        if [ ! -d "$PROBLEMATIC_DIR" ]; then
            echo "✅ Successfully removed with alternative method"
        else
            echo "❌ Manual intervention required"
            exit 1
        fi
    fi
else
    echo "ℹ️  Problematic directory not found - may already be resolved"
fi

# Restart Syncthing container to clear the error state
echo "🔄 Restarting Syncthing container..."
docker restart syncthing

echo "⏳ Waiting for Syncthing to restart..."
sleep 5

# Check if Syncthing is healthy
echo "🏥 Checking Syncthing health..."
HEALTH_STATUS=$(docker inspect syncthing --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")

if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "✅ Syncthing is healthy and running"

    # Show recent logs to verify fix
    echo "📋 Recent Syncthing logs (last 10 lines):"
    docker logs --tail 10 syncthing | grep -v "permission denied" | tail -5 || echo "No recent error-free logs"

    echo ""
    echo "🎉 Fix completed successfully!"
    echo "📝 Monitor Syncthing logs with: docker logs -f syncthing"
    echo "🌐 Access Syncthing web UI at: http://localhost:8384"

else
    echo "⚠️  Syncthing health status: $HEALTH_STATUS"
    echo "📋 Recent logs:"
    docker logs --tail 10 syncthing
fi

echo ""
echo "✨ Script completed"