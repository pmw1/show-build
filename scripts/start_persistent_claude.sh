#!/bin/bash
#
# Start Persistent Claude - Show-Build Wrapper
# Calls the main script from ClaudeSpawn project
#

CLAUDESPAWN_DIR="/mnt/process/claudespawn"

if [[ -x "$CLAUDESPAWN_DIR/scripts/show-build-integration/start_persistent_claude.sh" ]]; then
    exec "$CLAUDESPAWN_DIR/scripts/show-build-integration/start_persistent_claude.sh" "$@"
else
    echo "❌ ClaudeSpawn integration script not found"
    echo "Expected: $CLAUDESPAWN_DIR/scripts/show-build-integration/start_persistent_claude.sh"
    exit 1
fi