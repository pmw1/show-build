#!/bin/bash
# Standardized Inter-Claude Relay Post Script
# Posts messages to relay server with proper formatting

# Configuration
RELAY_HOST="${RELAY_HOST:-192.168.51.223}"
RELAY_PORT="${RELAY_PORT:-8001}"
RELAY_URL="http://${RELAY_HOST}:${RELAY_PORT}/write"

# Usage check
if [ $# -lt 3 ]; then
    echo "Usage: $0 <project> <topic> <content_file_or_text> [sender]"
    echo ""
    echo "Examples:"
    echo "  $0 asterisk-deployment urgent-request message.txt"
    echo "  $0 asterisk-deployment status-check 'Quick status request' ShowBuild-Claude"
    echo ""
    echo "Environment variables:"
    echo "  RELAY_HOST (default: 192.168.51.223)"
    echo "  RELAY_PORT (default: 8001)"
    exit 1
fi

PROJECT="$1"
TOPIC="$2"
CONTENT_INPUT="$3"
SENDER="${4:-ShowBuild-Claude}"

# Determine if content is file or text
if [ -f "$CONTENT_INPUT" ]; then
    CONTENT=$(cat "$CONTENT_INPUT")
else
    CONTENT="$CONTENT_INPUT"
fi

# Create JSON payload
TEMP_JSON=$(mktemp)
jq -n \
    --arg sender "$SENDER" \
    --arg project "$PROJECT" \
    --arg topic "$TOPIC" \
    --arg content "$CONTENT" \
    '{
        sender: $sender,
        project: $project,
        topic: $topic,
        content: $content
    }' > "$TEMP_JSON"

# Post to relay
echo "Posting to relay..."
echo "Project: $PROJECT"
echo "Topic: $TOPIC"
echo "Sender: $SENDER"
echo ""

RESPONSE=$(curl -s -X POST "$RELAY_URL" \
    -H 'Content-Type: application/json' \
    -d @"$TEMP_JSON")

# Clean up
rm -f "$TEMP_JSON"

# Show response
echo "Response: $RESPONSE"

# Extract message ID if successful
MESSAGE_ID=$(echo "$RESPONSE" | jq -r '.message_id // empty')
if [ -n "$MESSAGE_ID" ]; then
    echo "✓ Message posted successfully (ID: $MESSAGE_ID)"
    exit 0
else
    echo "✗ Failed to post message"
    exit 1
fi
