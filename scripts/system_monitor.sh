#!/bin/bash
#
# System Status Monitor for tmux pane
#

while true; do
    clear
    echo -e "\033[0;36m┌─ System Status ─┐\033[0m"
    echo
    echo "Load: $(cat /proc/loadavg | cut -d' ' -f1-3)"
    echo "Memory: $(free -h | grep Mem | awk '{print $3"/"$2" ("$3/$2*100"%)"}')"
    echo "Disk: $(df -h /mnt/process | tail -1 | awk '{print $3"/"$2" ("$5")"}')"
    echo
    echo "Processes:"
    echo "Claude: $(pgrep -f claude | wc -l)"
    echo "Tmux: $(tmux list-sessions 2>/dev/null | wc -l) sessions"
    echo
    echo "Remote pmw-rm4:"
    if ssh -o ConnectTimeout=2 pmw@pmw-rm4 'echo OK' 2>/dev/null >/dev/null; then
        echo "✅ Connected"
    else
        echo "❌ Offline"
    fi
    echo
    echo "$(date '+%H:%M:%S')"
    
    sleep 5
done