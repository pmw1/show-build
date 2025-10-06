#!/bin/bash

# Voice Claude Integration
# Integrates XTTS/Whisper with Claude Code interactive session
# Usage: ./voice_claude.sh [kairo_server] [whisper_port] [xtts_port]

KAIRO_SERVER=${1:-"kairo-server"}
WHISPER_PORT=${2:-"9000"}
XTTS_PORT=${3:-"9001"}

echo "🎙️ Voice Claude Integration Starting..."
echo "📡 Server: $KAIRO_SERVER"
echo "🎤 Whisper Port: $WHISPER_PORT"
echo "🔊 XTTS Port: $XTTS_PORT"

# Find Claude's TTY or process
CLAUDE_PID=$(pgrep -f "claude" | head -1)
if [[ -z "$CLAUDE_PID" ]]; then
    echo "❌ Claude Code session not found. Make sure Claude is running."
    exit 1
fi

CLAUDE_TTY=$(ps -o tty= -p "$CLAUDE_PID" | tr -d ' ')
if [[ "$CLAUDE_TTY" == "?" ]]; then
    echo "⚠️  TTY not found, trying alternative methods..."
    # Try to find the controlling terminal
    CLAUDE_TTY=$(lsof -p "$CLAUDE_PID" | grep -E 'pts|tty' | head -1 | awk '{print $9}')
    if [[ -z "$CLAUDE_TTY" ]]; then
        echo "❌ Could not determine Claude's terminal"
        exit 1
    fi
fi

echo "✅ Found Claude PID: $CLAUDE_PID on TTY: $CLAUDE_TTY"

# Create temp directory
mkdir -p /tmp/voice-claude
cd /tmp/voice-claude

# Background process: Monitor Claude output for TTS
echo "👂 Starting output monitor..."
(
    # Monitor the terminal for new output
    while true; do
        # Capture recent terminal output
        if [[ -e "/dev/$CLAUDE_TTY" ]]; then
            # Read from the terminal device (this may need adjustment)
            timeout 1 cat "/dev/$CLAUDE_TTY" 2>/dev/null | while read -r line; do
                # Filter for actual Claude responses (not prompts/commands)
                if [[ ${#line} -gt 20 && ! "$line" =~ ^[[:space:]]*$ && ! "$line" =~ ^\> ]]; then
                    echo "🔊 Speaking: $(echo "$line" | cut -c1-50)..."
                    
                    # Send to XTTS
                    echo "$line" | curl -s -X POST \
                        "http://$KAIRO_SERVER:$XTTS_PORT/speak" \
                        -H "Content-Type: text/plain" \
                        -d @- -o "speech_$(date +%s).wav" 2>/dev/null
                    
                    # Play the audio (background to not block)
                    aplay "speech_$(date +%s).wav" 2>/dev/null &
                fi
            done
        fi
        sleep 0.5
    done
) &
TTS_PID=$!

# Main voice input loop
echo ""
echo "🔴 Voice input active. Speak and it will be sent to Claude."
echo "   Press Ctrl+C to exit"
echo ""

while true; do
    echo -n "🎤 Recording (5 seconds)... "
    
    # Record audio
    arecord -D default -f cd -t wav -d 5 "voice_$(date +%s).wav" 2>/dev/null
    echo "done"
    
    echo -n "🔄 Transcribing... "
    
    # Transcribe with Whisper
    TEXT=$(curl -s -X POST "http://$KAIRO_SERVER:$WHISPER_PORT/transcribe" \
           -F "audio=@voice_$(date +%s).wav" 2>/dev/null | jq -r '.text // empty' 2>/dev/null)
    
    if [[ -z "$TEXT" || "$TEXT" == "null" ]]; then
        echo "❌ Transcription failed or empty"
        continue
    fi
    
    echo "done"
    echo "📝 You said: $TEXT"
    
    # Send to Claude's TTY
    echo -n "⚡ Injecting into Claude... "
    if echo "$TEXT" > "/dev/$CLAUDE_TTY" 2>/dev/null; then
        echo "done"
    else
        echo "❌ Failed to inject text"
    fi
    
    echo "---"
    sleep 1
done

# Cleanup
echo "🧹 Cleaning up..."
kill $TTS_PID 2>/dev/null
rm -f /tmp/voice-claude/*.wav
rmdir /tmp/voice-claude 2>/dev/null