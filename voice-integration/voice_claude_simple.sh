#!/bin/bash

# Simple Voice Claude - Uses named pipes for communication
# Usage: ./voice_claude_simple.sh [kairo_server] [whisper_port] [xtts_port]

KAIRO_SERVER=${1:-"kairo-server"}
WHISPER_PORT=${2:-"9000"}
XTTS_PORT=${3:-"9001"}
VOICE_PIPE="/tmp/claude_voice_input"

echo "🎙️ Simple Voice Claude Integration"
echo "📡 Server: $KAIRO_SERVER"
echo ""

# Create named pipe for voice input
if [[ ! -p "$VOICE_PIPE" ]]; then
    mkfifo "$VOICE_PIPE"
    echo "✅ Created voice input pipe: $VOICE_PIPE"
fi

echo "📋 SETUP INSTRUCTIONS:"
echo "   1. In your Claude session, run: cat $VOICE_PIPE"
echo "   2. This will make Claude wait for voice input"
echo "   3. Speak into this terminal to send commands to Claude"
echo ""
echo "🔴 Voice input ready. Speak your commands..."
echo ""

# Create temp directory for audio files
mkdir -p /tmp/voice-claude
cd /tmp/voice-claude

# Main voice input loop
while true; do
    echo -n "🎤 Recording (press Enter when ready to speak, Ctrl+C to exit): "
    read -r
    
    echo -n "🔴 Recording 5 seconds... "
    arecord -D default -f cd -t wav -d 5 "voice_$(date +%s).wav" 2>/dev/null
    echo "done"
    
    echo -n "🔄 Transcribing... "
    
    # Get the most recent audio file
    AUDIO_FILE=$(ls -t voice_*.wav 2>/dev/null | head -1)
    
    if [[ -z "$AUDIO_FILE" ]]; then
        echo "❌ No audio file found"
        continue
    fi
    
    # Transcribe with Whisper
    TEXT=$(curl -s -X POST "http://$KAIRO_SERVER:$WHISPER_PORT/transcribe" \
           -F "audio=@$AUDIO_FILE" 2>/dev/null | jq -r '.text // empty' 2>/dev/null)
    
    if [[ -z "$TEXT" || "$TEXT" == "null" || "$TEXT" == "empty" ]]; then
        echo "❌ Transcription failed or empty"
        continue
    fi
    
    echo "done"
    echo "📝 You said: $TEXT"
    
    # Send to named pipe (Claude should be reading from this)
    echo -n "⚡ Sending to Claude via pipe... "
    if echo "$TEXT" > "$VOICE_PIPE" 2>/dev/null; then
        echo "done"
    else
        echo "❌ Failed - make sure Claude is reading from: cat $VOICE_PIPE"
    fi
    
    # Optional: Get Claude's response and speak it
    echo -n "🔊 Speak Claude's response? (y/N): "
    read -r -t 3 speak_choice
    
    if [[ "$speak_choice" =~ ^[Yy]$ ]]; then
        echo "📝 Paste Claude's response here (press Enter twice when done):"
        CLAUDE_RESPONSE=""
        while IFS= read -r line; do
            if [[ -z "$line" ]]; then
                break
            fi
            CLAUDE_RESPONSE="$CLAUDE_RESPONSE$line "
        done
        
        if [[ -n "$CLAUDE_RESPONSE" ]]; then
            echo "🔊 Speaking Claude's response..."
            echo "$CLAUDE_RESPONSE" | curl -s -X POST \
                "http://$KAIRO_SERVER:$XTTS_PORT/speak" \
                -H "Content-Type: text/plain" \
                -d @- -o "speech_$(date +%s).wav" 2>/dev/null
            
            # Play the audio
            SPEECH_FILE=$(ls -t speech_*.wav 2>/dev/null | head -1)
            if [[ -n "$SPEECH_FILE" ]]; then
                aplay "$SPEECH_FILE" 2>/dev/null
            fi
        fi
    fi
    
    echo "---"
done

# Cleanup
echo "🧹 Cleaning up..."
rm -f /tmp/voice-claude/*.wav
rm -f "$VOICE_PIPE"
rmdir /tmp/voice-claude 2>/dev/null