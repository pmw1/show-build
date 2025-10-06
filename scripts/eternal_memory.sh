#!/bin/bash
#
# Eternal Memory System - Timestamped Log of Everything
# Captures all Claude interactions, commands, system events
#

set -e

# Configuration
MEMORY_DIR="/mnt/process/show-build/eternal_memory"
CONVERSATIONS_DIR="$MEMORY_DIR/conversations"
SYSTEM_EVENTS_DIR="$MEMORY_DIR/system_events" 
SEARCH_INDEX="$MEMORY_DIR/search_index.txt"
CURRENT_SESSION="$MEMORY_DIR/current_session.log"

# Create directory structure
mkdir -p "$CONVERSATIONS_DIR" "$SYSTEM_EVENTS_DIR"

# Session ID based on timestamp
SESSION_ID=$(date +%Y%m%d_%H%M%S)
SESSION_FILE="$CONVERSATIONS_DIR/session_${SESSION_ID}.log"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

log_memory() {
    local type="$1"
    local content="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S.%3N')
    local entry="[$timestamp] [$type] $content"
    
    # Log to current session
    echo "$entry" >> "$SESSION_FILE"
    echo "$entry" >> "$CURRENT_SESSION"
    
    # Update search index
    echo "$timestamp|$type|$content|$SESSION_FILE" >> "$SEARCH_INDEX"
}

log_system_event() {
    local event="$1"
    local details="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S.%3N')
    local event_file="$SYSTEM_EVENTS_DIR/$(date +%Y%m%d)_events.log"
    
    echo "[$timestamp] EVENT: $event | DETAILS: $details" >> "$event_file"
    log_memory "SYSTEM" "$event: $details"
}

search_memory() {
    local query="$1"
    local results_file="/tmp/memory_search_results.txt"
    
    echo -e "${BLUE}🔍 Searching eternal memory for: '$query'${NC}"
    echo
    
    # Search in conversations and system events
    grep -i "$query" "$MEMORY_DIR"/**/*.log 2>/dev/null | head -20 > "$results_file" || true
    
    if [[ -s "$results_file" ]]; then
        echo -e "${GREEN}📚 Found matches:${NC}"
        cat "$results_file" | while IFS=':' read -r file content; do
            local basename=$(basename "$file")
            echo -e "${YELLOW}$basename:${NC} $content"
        done
    else
        echo -e "${YELLOW}No matches found${NC}"
    fi
    
    rm -f "$results_file"
}

get_memory_stats() {
    local total_conversations=$(find "$CONVERSATIONS_DIR" -name "*.log" | wc -l)
    local total_events=$(find "$SYSTEM_EVENTS_DIR" -name "*.log" | wc -l)
    local total_entries=$(wc -l < "$SEARCH_INDEX" 2>/dev/null || echo 0)
    local memory_size=$(du -sh "$MEMORY_DIR" 2>/dev/null | cut -f1 || echo "0")
    
    echo -e "${BLUE}🧠 Eternal Memory Statistics:${NC}"
    echo "Sessions: $total_conversations"
    echo "Event days: $total_events" 
    echo "Total entries: $total_entries"
    echo "Storage used: $memory_size"
    echo "Current session: session_${SESSION_ID}.log"
}

# Initialize session
log_system_event "SESSION_START" "Eternal memory initialized for session $SESSION_ID"

case "${1:-help}" in
    "log")
        log_memory "$2" "$3"
        ;;
    "event") 
        log_system_event "$2" "$3"
        ;;
    "search")
        search_memory "$2"
        ;;
    "stats")
        get_memory_stats
        ;;
    "help"|*)
        echo -e "${GREEN}Eternal Memory System Commands:${NC}"
        echo "  $0 log TYPE 'content'     - Log interaction"  
        echo "  $0 event NAME 'details'   - Log system event"
        echo "  $0 search 'query'         - Search memory"
        echo "  $0 stats                  - Show statistics"
        ;;
esac