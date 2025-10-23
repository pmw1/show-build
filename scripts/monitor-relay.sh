#!/bin/bash
# Standardized Inter-Claude Relay Monitor
# Monitors relay server for new messages and alerts on updates

# Configuration
RELAY_HOST="${RELAY_HOST:-192.168.51.223}"
RELAY_PORT="${RELAY_PORT:-8001}"
PROJECT="${1:-asterisk-deployment}"
CHECK_INTERVAL="${2:-10}"
LAST_MESSAGE_FILE="/tmp/relay_last_message_${PROJECT}.txt"

RELAY_URL="http://${RELAY_HOST}:${RELAY_PORT}/read?project=${PROJECT}&limit=10"

# Get last seen message ID
if [ -f "$LAST_MESSAGE_FILE" ]; then
    LAST_MESSAGE_ID=$(cat "$LAST_MESSAGE_FILE")
else
    LAST_MESSAGE_ID=0
fi

echo "========================================="
echo "Inter-Claude Relay Monitor"
echo "========================================="
echo "Project: $PROJECT"
echo "Relay: $RELAY_URL"
echo "Check interval: ${CHECK_INTERVAL}s"
echo "Last message ID: $LAST_MESSAGE_ID"
echo ""
echo "Monitoring for new messages..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    # Fetch latest messages
    RESPONSE=$(curl -s "$RELAY_URL" 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo "! Relay connection failed"
        sleep "$CHECK_INTERVAL"
        continue
    fi

    # Get the highest message ID
    LATEST_ID=$(echo "$RESPONSE" | jq -r '.[0].id // 0' 2>/dev/null)

    if [ "$LATEST_ID" -gt "$LAST_MESSAGE_ID" ]; then
        # New message(s) detected
        echo ""
        echo "========================================="
        echo "NEW MESSAGE DETECTED"
        echo "========================================="
        echo "Message ID: $LATEST_ID"
        echo "Timestamp: $(date)"
        echo ""

        # Show all new messages
        echo "$RESPONSE" | jq -c '.[]' | while read -r msg; do
            MSG_ID=$(echo "$msg" | jq -r '.id')
            if [ "$MSG_ID" -gt "$LAST_MESSAGE_ID" ]; then
                echo "--- Message $MSG_ID ---"
                echo "From: $(echo "$msg" | jq -r '.sender // "unknown"')"
                echo "Topic: $(echo "$msg" | jq -r '.topic // "none"')"
                echo ""
                echo "$msg" | jq -r '.content'
                echo ""
            fi
        done

        echo "========================================="
        echo ""

        # Update last seen ID
        echo "$LATEST_ID" > "$LAST_MESSAGE_FILE"
        LAST_MESSAGE_ID=$LATEST_ID
    else
        # No new messages
        echo -n "."
    fi

    sleep "$CHECK_INTERVAL"
done
