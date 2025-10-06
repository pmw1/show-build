#!/bin/bash
#
# Claude Command Center - Interactive Control Interface
# Single-keypress controls for heartbeat, remote Claude, and system management
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="/tmp/claude_control"
mkdir -p "$STATE_DIR"

HEARTBEAT_STATE="$STATE_DIR/heartbeat_mode"
REMOTE_STATUS="$STATE_DIR/remote_status"
SYSTEM_LOG="$STATE_DIR/command_log"

# Initialize state files
[[ ! -f "$HEARTBEAT_STATE" ]] && echo "AUTO" > "$HEARTBEAT_STATE"
[[ ! -f "$REMOTE_STATUS" ]] && echo "UNKNOWN" > "$REMOTE_STATUS"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Functions
get_heartbeat_status() {
    local mode=$(cat "$HEARTBEAT_STATE" 2>/dev/null || echo "AUTO")
    case "$mode" in
        "AUTO") echo -e "${GREEN}●${NC} Auto";;
        "MANUAL") echo -e "${YELLOW}●${NC} Manual";;
        "OFF") echo -e "${RED}●${NC} Off";;
    esac
}

get_satellite_status() {
    # Check if ClaudeSpawn is running
    if pgrep -f "claudespawn.py" > /dev/null; then
        echo -e "${GREEN}●${NC} Running"
    else
        echo -e "${RED}●${NC} Stopped"
    fi
}

toggle_satellite() {
    echo -e "\n${BLUE}🛰️  Satellite Control Menu${NC}"
    echo -e "${YELLOW}════════════════════════════${NC}"
    echo -e "${GREEN}[1]${NC} Local Satellite (this machine)"
    echo -e "${GREEN}[2]${NC} Remote Satellites (pmw-rm4, etc.)"
    echo -e "${GREEN}[3]${NC} All Satellites"
    echo -e "${GREEN}[q]${NC} Back to main menu"
    echo
    read -p "Choose satellite control [1-3/q]: " -n 1 -r SAT_CHOICE
    echo
    
    case "$SAT_CHOICE" in
        1)
            toggle_local_satellite
            ;;
        2)
            manage_remote_satellites
            ;;
        3)
            toggle_all_satellites
            ;;
        q|Q)
            return
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            sleep 1
            ;;
    esac
}

toggle_local_satellite() {
    if pgrep -f "claudespawn.py" > /dev/null; then
        # ClaudeSpawn is running, stop it
        echo -e "\n${YELLOW}🛑 Stopping local ClaudeSpawn satellite...${NC}"
        pkill -f "claudespawn.py"
        sleep 2
        if ! pgrep -f "claudespawn.py" > /dev/null; then
            echo -e "${GREEN}✅ Local ClaudeSpawn stopped${NC}"
        else
            echo -e "${RED}❌ Failed to stop local ClaudeSpawn${NC}"
        fi
        log_action "Local ClaudeSpawn stopped"
    else
        # ClaudeSpawn is not running, start it
        echo -e "\n${BLUE}🚀 Starting local ClaudeSpawn satellite...${NC}"
        cd /mnt/process/claudespawn
        nohup python3 claudespawn.py --mode local --port 8890 > /tmp/claudespawn.log 2>&1 &
        sleep 3
        if pgrep -f "claudespawn.py" > /dev/null; then
            echo -e "${GREEN}✅ Local ClaudeSpawn started on port 8890${NC}"
            echo -e "${CYAN}📊 Status: http://localhost:8890/status${NC}"
        else
            echo -e "${RED}❌ Failed to start local ClaudeSpawn${NC}"
            echo -e "${YELLOW}Check log: tail /tmp/claudespawn.log${NC}"
        fi
        log_action "Local ClaudeSpawn started"
    fi
    echo
    read -p "Press any key to continue..." -n1
}

manage_remote_satellites() {
    echo -e "\n${BLUE}🌐 Remote Satellite Management${NC}"
    echo -e "${YELLOW}═══════════════════════════════${NC}"
    echo -e "${GREEN}[1]${NC} Start pmw-rm4 satellite"
    echo -e "${GREEN}[2]${NC} Stop pmw-rm4 satellite"
    echo -e "${GREEN}[3]${NC} Restart pmw-rm4 satellite"
    echo -e "${GREEN}[4]${NC} Check pmw-rm4 satellite status"
    echo -e "${GREEN}[5]${NC} Deploy new satellite to pmw-rm4"
    echo -e "${GREEN}[q]${NC} Back"
    echo
    read -p "Choose action [1-5/q]: " -n 1 -r REMOTE_CHOICE
    echo
    
    case "$REMOTE_CHOICE" in
        1)
            start_remote_satellite "pmw@pmw-rm4"
            ;;
        2)
            stop_remote_satellite "pmw@pmw-rm4"
            ;;
        3)
            restart_remote_satellite "pmw@pmw-rm4"
            ;;
        4)
            check_remote_satellite_status "pmw@pmw-rm4"
            ;;
        5)
            deploy_remote_satellite "pmw@pmw-rm4"
            ;;
        q|Q)
            return
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            sleep 1
            ;;
    esac
    echo
    read -p "Press any key to continue..." -n1
}

start_remote_satellite() {
    local remote_host="$1"
    echo -e "\n${BLUE}🚀 Starting remote satellite on $remote_host...${NC}"
    
    ssh "$remote_host" "sudo systemctl start claudespawn" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Remote satellite started${NC}"
        log_action "Remote satellite started on $remote_host"
    else
        echo -e "${RED}❌ Failed to start remote satellite${NC}"
        echo -e "${YELLOW}Trying manual start...${NC}"
        ssh "$remote_host" "cd /home/pmw/claudespawn && nohup python claudespawn.py --mode remote --home-base http://intstruct.pmwconnect.com:47291 > satellite.log 2>&1 &"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Remote satellite started manually${NC}"
        else
            echo -e "${RED}❌ Manual start also failed${NC}"
        fi
    fi
}

stop_remote_satellite() {
    local remote_host="$1"
    echo -e "\n${YELLOW}🛑 Stopping remote satellite on $remote_host...${NC}"
    
    ssh "$remote_host" "sudo systemctl stop claudespawn" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Remote satellite stopped${NC}"
        log_action "Remote satellite stopped on $remote_host"
    else
        echo -e "${YELLOW}Trying manual stop...${NC}"
        ssh "$remote_host" "pkill -f claudespawn.py"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Remote satellite stopped manually${NC}"
        else
            echo -e "${RED}❌ Failed to stop remote satellite${NC}"
        fi
    fi
}

restart_remote_satellite() {
    local remote_host="$1"
    echo -e "\n${BLUE}🔄 Restarting remote satellite on $remote_host...${NC}"
    stop_remote_satellite "$remote_host"
    sleep 3
    start_remote_satellite "$remote_host"
}

check_remote_satellite_status() {
    local remote_host="$1"
    echo -e "\n${BLUE}📊 Remote Satellite Status: $remote_host${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    
    # Check systemd service
    echo -e "${CYAN}Systemd Service:${NC}"
    ssh "$remote_host" "sudo systemctl status claudespawn --no-pager -l" 2>/dev/null || echo "Service not found"
    
    # Check process
    echo -e "\n${CYAN}Process Status:${NC}"
    ssh "$remote_host" "pgrep -f claudespawn.py && echo 'ClaudeSpawn running' || echo 'ClaudeSpawn not running'"
    
    # Check logs
    echo -e "\n${CYAN}Recent Logs:${NC}"
    ssh "$remote_host" "tail -5 /home/pmw/claudespawn/satellite.log 2>/dev/null || echo 'No log file found'"
    
    # Check port
    echo -e "\n${CYAN}Port Status:${NC}"
    ssh "$remote_host" "ss -tlnp | grep :8890 && echo 'Port 8890 listening' || echo 'Port 8890 not listening'"
}

deploy_remote_satellite() {
    local remote_host="$1"
    echo -e "\n${BLUE}📦 Deploying ClaudeSpawn to $remote_host...${NC}"
    
    # Run deployment script
    if [ -f "./claudespawn_deploy.sh" ]; then
        echo -e "${CYAN}Running deployment script...${NC}"
        ./claudespawn_deploy.sh
        echo -e "${GREEN}✅ Deployment script completed${NC}"
    else
        echo -e "${RED}❌ Deployment script not found${NC}"
        echo -e "${YELLOW}Manual deployment required${NC}"
    fi
}

toggle_all_satellites() {
    echo -e "\n${BLUE}🌍 Managing All Satellites${NC}"
    echo -e "${YELLOW}════════════════════════════${NC}"
    echo -e "${GREEN}[1]${NC} Start all satellites"
    echo -e "${GREEN}[2]${NC} Stop all satellites"
    echo -e "${GREEN}[3]${NC} Restart all satellites"
    echo -e "${GREEN}[4]${NC} Status of all satellites"
    echo -e "${GREEN}[q]${NC} Back"
    echo
    read -p "Choose action [1-4/q]: " -n 1 -r ALL_CHOICE
    echo
    
    case "$ALL_CHOICE" in
        1)
            echo -e "${BLUE}Starting all satellites...${NC}"
            toggle_local_satellite
            start_remote_satellite "pmw@pmw-rm4"
            ;;
        2)
            echo -e "${YELLOW}Stopping all satellites...${NC}"
            pkill -f "claudespawn.py" 2>/dev/null
            stop_remote_satellite "pmw@pmw-rm4"
            ;;
        3)
            echo -e "${BLUE}Restarting all satellites...${NC}"
            toggle_all_satellites # Stop
            sleep 3
            toggle_all_satellites # Start
            ;;
        4)
            echo -e "${BLUE}All Satellite Status:${NC}"
            echo -e "\n${CYAN}Local:${NC} $(get_satellite_status)"
            check_remote_satellite_status "pmw@pmw-rm4"
            ;;
        q|Q)
            return
            ;;
    esac
    echo
    read -p "Press any key to continue..." -n1
}

get_remote_status() {
    # Check pmw-rm4 status
    if ssh -o ConnectTimeout=2 pmw@pmw-rm4 'echo "OK"' 2>/dev/null >/dev/null; then
        echo -e "${GREEN}●${NC} Online"
    else
        echo -e "${RED}●${NC} Offline"
    fi
}

toggle_heartbeat() {
    local current=$(cat "$HEARTBEAT_STATE")
    case "$current" in
        "AUTO") echo "MANUAL" > "$HEARTBEAT_STATE";;
        "MANUAL") echo "OFF" > "$HEARTBEAT_STATE";;
        "OFF") echo "AUTO" > "$HEARTBEAT_STATE";;
    esac
    log_action "Heartbeat: $(cat "$HEARTBEAT_STATE")"
}

send_manual_ping() {
    local ping_num=$(date +%s | tail -c 2)
    echo "<ping> Manual #$ping_num. Status check requested."
    log_action "Manual ping sent"
}

check_remote_claude() {
    log_action "Checking pmw-rm4..."
    echo -e "\n${BLUE}Remote Claude Status:${NC}"
    
    # Check SSH connectivity
    if ssh -o ConnectTimeout=3 pmw@pmw-rm4 'echo "Connection OK"' 2>/dev/null; then
        echo -e "${GREEN}✅ SSH Connection: OK${NC}"
        
        # Check if Claude is running
        if ssh pmw@pmw-rm4 'tmux list-sessions 2>/dev/null | grep -q claude' 2>/dev/null; then
            echo -e "${GREEN}✅ Claude Session: Active${NC}"
        else
            echo -e "${YELLOW}⚠️  Claude Session: Not found${NC}"
        fi
        
        # Check for responses
        if scp pmw@pmw-rm4:~/CLAUDECOM.txt ./remote_response.txt 2>/dev/null; then
            echo -e "${GREEN}✅ Communication: Response available${NC}"
            echo -e "\n${CYAN}Latest Response:${NC}"
            tail -5 ./remote_response.txt | sed 's/^/  /'
            rm -f ./remote_response.txt
        else
            echo -e "${YELLOW}⏳ Communication: No new responses${NC}"
        fi
        
        # System load
        local load=$(ssh pmw@pmw-rm4 'uptime | cut -d":" -f4-' 2>/dev/null || echo "unknown")
        echo -e "${BLUE}📊 Load:${NC} $load"
        
    else
        echo -e "${RED}❌ SSH Connection: Failed${NC}"
        echo -e "${YELLOW}   Check network or remote system${NC}"
    fi
    
    echo
    read -p "Press any key to continue..." -n1
}

log_action() {
    echo "$(date '+%H:%M:%S') - $1" >> "$SYSTEM_LOG"
}

show_status() {
    clear
    echo -e "${CYAN}┌─ ${PURPLE}Command Center${NC} ${CYAN}─┐${NC}"
    echo
    echo -e "Heartbeat: $(get_heartbeat_status)"
    echo -e "Satellite: $(get_satellite_status)"
    echo -e "Remote: $(get_remote_status)" 
    echo -e "Time: $(date '+%H:%M:%S')"
    echo
    echo -e "${GREEN}[h]${NC} Heartbeat  ${GREEN}[p]${NC} Ping"
    echo -e "${GREEN}[r]${NC} Remote     ${GREEN}[d]${NC} Database" 
    echo -e "${GREEN}[t]${NC} Satellite  ${GREEN}[s]${NC} Status"
    echo -e "${GREEN}[l]${NC} Logs       ${GREEN}[c]${NC} Clear"
    echo -e "${GREEN}[k]${NC} ${RED}KILL${NC}       ${GREEN}[q]${NC} Quit"
    echo
    echo -e "${PURPLE}Ctrl+b + arrows = switch panes${NC}"
    echo
    echo -e "${YELLOW}Press key for action...${NC}"
}

show_logs() {
    echo -e "\n${BLUE}Recent Activity:${NC}"
    if [[ -f "$SYSTEM_LOG" ]]; then
        tail -10 "$SYSTEM_LOG"
    else
        echo "No activity logged yet."
    fi
    echo
    read -p "Press any key to continue..." -n1
}

# Main loop
log_action "Command Center started"

while true; do
    show_status
    read -n1 key
    
    case "$key" in
        h|H)
            toggle_heartbeat
            ;;
        p|P)
            send_manual_ping
            ;;
        r|R)
            check_remote_claude
            ;;
        t|T)
            toggle_satellite
            ;;
        d|D)
            echo -e "\n${BLUE}Database Coordination:${NC}"
            echo "Sending database status check to pmw-rm4..."
            echo "Database status request from command center - $(date)" > /tmp/db_request.txt
            scp /tmp/db_request.txt pmw@pmw-rm4:~/CLAUDECOM.txt 2>/dev/null && echo "✅ Request sent" || echo "❌ Send failed"
            rm -f /tmp/db_request.txt
            sleep 2
            ;;
        s|S)
            echo -e "\n${BLUE}System Status:${NC}"
            uptime
            echo "Load: $(cat /proc/loadavg)"
            echo "Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"
            sleep 3
            ;;
        l|L)
            show_logs
            ;;
        c|C)
            clear
            ;;
        k|K)
            echo -e "\n${RED}🚨 EMERGENCY KILL SWITCH${NC}"
            echo "This will terminate ALL Claude processes!"
            read -p "Type 'YES' to confirm emergency stop: " confirm
            if [[ "$confirm" == "YES" ]]; then
                exec "$SCRIPT_DIR/kill_all_claude.sh"
            else
                echo "Cancelled - no processes killed"
                sleep 2
            fi
            ;;
        q|Q)
            log_action "Command Center closed"
            echo -e "\n${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            # Ignore unknown keys
            ;;
    esac
done