#!/bin/bash
#
# ClaudeSpawn Management - Show-Build Wrapper
# Provides easy access to ClaudeSpawn tools from show-build
#

CLAUDESPAWN_DIR="/mnt/process/claudespawn"

show_help() {
    echo "🚀 ClaudeSpawn Management (Show-Build Integration)"
    echo "=================================================="
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start        Start persistent Claude session"
    echo "  interface    Launch 7-pane Star Trek monitoring interface"
    echo "  docker       Manage ClaudeSpawn Docker container"
    echo "  monitor      Monitor Claude processes"
    echo "  kill         Kill all Claude processes"
    echo "  log          Start conversation logger"
    echo "  status       Show ClaudeSpawn status"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start persistent Claude"
    echo "  $0 interface          # Launch monitoring interface"
    echo "  $0 docker start       # Start ClaudeSpawn container"
    echo "  $0 status             # Check if running"
}

case "${1:-help}" in
    start)
        exec "$CLAUDESPAWN_DIR/scripts/show-build-integration/start_persistent_claude.sh" "${@:2}"
        ;;
    interface)
        exec "$CLAUDESPAWN_DIR/scripts/show-build-integration/launch_claudespawn_interface.sh" "${@:2}"
        ;;
    docker)
        exec "$CLAUDESPAWN_DIR/scripts/show-build-integration/claudespawn_docker.sh" "${@:2}"
        ;;
    monitor)
        exec "$CLAUDESPAWN_DIR/scripts/show-build-integration/claude_monitor.sh" "${@:2}"
        ;;
    kill)
        exec "$CLAUDESPAWN_DIR/scripts/show-build-integration/kill_all_claude.sh" "${@:2}"
        ;;
    log)
        exec "$CLAUDESPAWN_DIR/scripts/show-build-integration/claude_conversation_logger.sh" "${@:2}"
        ;;
    status)
        echo "🔍 ClaudeSpawn Status Check"
        echo "=========================="
        if curl -s http://localhost:47291/status >/dev/null 2>&1; then
            echo "✅ ClaudeSpawn: Running (http://localhost:47291)"
            curl -s http://localhost:47291/status | head -n 3
        else
            echo "❌ ClaudeSpawn: Not running"
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_help
        exit 1
        ;;
esac