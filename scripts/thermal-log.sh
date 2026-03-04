#!/bin/bash
# Thermal + GPU + CPU logger - logs every 5 seconds
LOGFILE="/mnt/process/show-build/logs/thermal.log"
mkdir -p "$(dirname "$LOGFILE")"

echo "=== Thermal logging started $(date) ===" >> "$LOGFILE"
echo "FORMAT: timestamp | CPU zones | CPU freq/governor | load | memory | GPU temp/util/mem/power/fan" >> "$LOGFILE"

while true; do
    # CPU thermal zones
    TEMPS=""
    i=0
    for zone in /sys/class/thermal/thermal_zone*/temp; do
        t=$(cat "$zone" 2>/dev/null)
        if [ -n "$t" ]; then
            TEMPS="$TEMPS z${i}=$((t/1000))°C"
        fi
        i=$((i+1))
    done

    # CPU frequency and governor
    CPU_FREQ=""
    for cpu in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq; do
        f=$(cat "$cpu" 2>/dev/null)
        if [ -n "$f" ]; then
            CPU_FREQ="$CPU_FREQ $((f/1000))MHz"
        fi
    done
    GOV=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "n/a")

    # CPU load
    LOAD=$(cut -d' ' -f1-3 /proc/loadavg)

    # Memory
    MEM=$(free -m | awk '/Mem:/{printf "used=%dMB/%dMB(%.0f%%)", $3, $2, $3/$2*100}')

    # NVIDIA GPU
    GPU=$(nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,utilization.memory,power.draw,fan.speed --format=csv,noheader,nounits 2>/dev/null)
    if [ -n "$GPU" ]; then
        GPU_TEMP=$(echo "$GPU" | cut -d',' -f1 | xargs)
        GPU_UTIL=$(echo "$GPU" | cut -d',' -f2 | xargs)
        GPU_MEM=$(echo "$GPU" | cut -d',' -f3 | xargs)
        GPU_PWR=$(echo "$GPU" | cut -d',' -f4 | xargs)
        GPU_FAN=$(echo "$GPU" | cut -d',' -f5 | xargs)
        GPU_STR="gpu=${GPU_TEMP}°C util=${GPU_UTIL}% mem=${GPU_MEM}% pwr=${GPU_PWR}W fan=${GPU_FAN}%"
    else
        GPU_STR="gpu=n/a"
    fi

    echo "$(date '+%Y-%m-%d %H:%M:%S') |${TEMPS} | cpu=[${CPU_FREQ} ] ${GOV} | load=${LOAD} | ${MEM} | ${GPU_STR}" >> "$LOGFILE"
    sleep 5
done
