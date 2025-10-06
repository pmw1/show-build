#!/bin/bash
#
# Tiered Memory System - 3 Levels: Immediate → Working → Long-term
# L1: Everything (minutes/hours), L2: Insights (days/weeks), L3: Principles (months/permanent)
#

set -e

# Configuration
MEMORY_ROOT="/mnt/process/claudespawn/eternal_memory"
L1_DIR="$MEMORY_ROOT/L1_immediate"
L2_DIR="$MEMORY_ROOT/L2_working" 
L3_DIR="$MEMORY_ROOT/L3_longterm"

TODAY=$(date +%Y%m%d)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S.%3N')

# Create structure
mkdir -p "$L1_DIR" "$L2_DIR" "$L3_DIR"

# Current files
L1_FILE="$L1_DIR/L1_${TODAY}.log"
L2_FILE="$L2_DIR/L2_${TODAY}.log"  
L3_FILE="$L3_DIR/L3_principles.log"

# Colors
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

get_next_line_number() {
    local file="$1"
    if [[ -f "$file" ]]; then
        echo $(($(wc -l < "$file") + 1))
    else
        echo 1
    fi
}

format_line_ref() {
    local level="$1"
    local date="$2" 
    local line="$3"
    printf "L%d:%s:%05d" "$level" "$date" "$line"
}

# L1: Immediate Memory - Everything
log_immediate() {
    local type="$1"
    local content="$2"
    local line_num=$(get_next_line_number "$L1_FILE")
    local line_ref=$(format_line_ref 1 "$TODAY" "$line_num")
    
    echo "[$TIMESTAMP] [$line_ref] [$type] $content" >> "$L1_FILE"
    echo -e "${CYAN}L1:${NC} $type → $content"
}

# L2: Working Memory - Insights, Rules, Discoveries  
log_working() {
    local type="$1"  # RULE, GOAL, DISCOVERY, COUNTERPOINT
    local content="$2"
    local l1_refs="$3"  # Optional L1 references
    local line_num=$(get_next_line_number "$L2_FILE")
    local line_ref=$(format_line_ref 2 "$TODAY" "$line_num")
    
    echo "[$TIMESTAMP] [$line_ref] [$type] $content" >> "$L2_FILE"
    if [[ -n "$l1_refs" ]]; then
        echo "  ← REF: $l1_refs" >> "$L2_FILE"
    fi
    echo -e "${YELLOW}L2:${NC} $type → $content"
    
    # Also log to L1
    log_immediate "L2_ENTRY" "$type: $content (ref: $line_ref)"
}

# L3: Long-term Memory - Principles, Strategic Direction
log_longterm() {
    local type="$1"  # PRINCIPLE, MISSION, BOUNDARY, PHILOSOPHY
    local content="$2" 
    local l2_refs="$3"  # L2 references
    local line_num=$(get_next_line_number "$L3_FILE")
    local line_ref=$(format_line_ref 3 "$TODAY" "$line_num")
    
    echo "[$TIMESTAMP] [$line_ref] [$type] $content" >> "$L3_FILE"
    if [[ -n "$l2_refs" ]]; then
        echo "  ← REF: $l2_refs" >> "$L3_FILE"
    fi
    echo -e "${GREEN}L3:${NC} $type → $content"
    
    # Also log to working memory
    log_working "L3_PROMOTION" "$type: $content" "$line_ref"
}

search_memory() {
    local query="$1"
    local level="${2:-all}"
    
    echo -e "${CYAN}🔍 Searching memory (Level: $level) for: '$query'${NC}"
    echo
    
    case "$level" in
        "1"|"L1")
            grep -i "$query" "$L1_DIR"/*.log 2>/dev/null | head -10
            ;;
        "2"|"L2") 
            grep -i "$query" "$L2_DIR"/*.log 2>/dev/null | head -10
            ;;
        "3"|"L3")
            grep -i "$query" "$L3_DIR"/*.log 2>/dev/null | head -10
            ;;
        "all"|*)
            echo -e "${GREEN}=== L3 (Long-term) ===${NC}"
            grep -i "$query" "$L3_DIR"/*.log 2>/dev/null | head -5
            echo -e "${YELLOW}=== L2 (Working) ===${NC}" 
            grep -i "$query" "$L2_DIR"/*.log 2>/dev/null | head -5
            echo -e "${CYAN}=== L1 (Immediate) ===${NC}"
            grep -i "$query" "$L1_DIR"/*.log 2>/dev/null | head -5
            ;;
    esac
}

show_stats() {
    local l1_lines=$(find "$L1_DIR" -name "*.log" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
    local l2_lines=$(find "$L2_DIR" -name "*.log" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
    local l3_lines=$(find "$L3_DIR" -name "*.log" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
    local total_size=$(du -sh "$MEMORY_ROOT" 2>/dev/null | cut -f1 || echo "0")
    
    echo -e "${CYAN}🧠 Tiered Memory Statistics:${NC}"
    echo -e "${CYAN}L1 (Immediate):${NC} $l1_lines entries"
    echo -e "${YELLOW}L2 (Working):${NC} $l2_lines insights"  
    echo -e "${GREEN}L3 (Long-term):${NC} $l3_lines principles"
    echo -e "${NC}Total storage: $total_size"
}

# Initialize session
log_immediate "SESSION_START" "Tiered memory system initialized"

# Command interface
case "${1:-help}" in
    "l1"|"immediate")
        log_immediate "$2" "$3"
        ;;
    "l2"|"working")
        log_working "$2" "$3" "$4"
        ;;
    "l3"|"longterm")
        log_longterm "$2" "$3" "$4"
        ;;
    "search")
        search_memory "$2" "$3"
        ;;
    "stats")
        show_stats
        ;;
    "help"|*)
        echo -e "${GREEN}Tiered Memory System${NC}"
        echo "  $0 l1 TYPE 'content'              - Log immediate event"
        echo "  $0 l2 TYPE 'content' 'l1_refs'    - Log working insight"
        echo "  $0 l3 TYPE 'content' 'l2_refs'    - Log long-term principle" 
        echo "  $0 search 'query' [level]         - Search memory"
        echo "  $0 stats                          - Show statistics"
        echo
        echo -e "${CYAN}Types:${NC} USER_INPUT, CLAUDE_OUTPUT, SYSTEM_EVENT, FILE_CHANGE"
        echo -e "${YELLOW}Types:${NC} RULE, GOAL, DISCOVERY, COUNTERPOINT, PATTERN"
        echo -e "${GREEN}Types:${NC} PRINCIPLE, MISSION, BOUNDARY, PHILOSOPHY"
        ;;
esac