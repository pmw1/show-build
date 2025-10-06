# Voice Claude Integration

Voice interface for Claude Code using XTTS (Text-to-Speech) and Whisper (Speech-to-Text).

## Requirements

1. **XTTS Server** running on kairo server
2. **Whisper Server** running on kairo server  
3. **Audio tools**: `arecord`, `aplay`, `jq`, `curl`
4. **Claude Code** running in interactive session

## Setup

```bash
# Install audio tools (if not already installed)
sudo apt install alsa-utils jq curl

# Make script executable
chmod +x voice_claude.sh
```

## Usage

```bash
# Basic usage (assumes kairo-server hostname)
./voice_claude.sh

# With custom server and ports
./voice_claude.sh 192.168.1.100 9000 9001
```

## How It Works

1. **Voice Input**: Records 5-second audio clips
2. **Transcription**: Sends audio to Whisper server for speech-to-text
3. **Injection**: Injects transcribed text directly into Claude's terminal
4. **Voice Output**: Monitors Claude's responses and speaks them via XTTS

## API Endpoints Expected

**Whisper Server:**
```bash
POST /transcribe
Content-Type: multipart/form-data
Form field: audio (wav file)
Response: {"text": "transcribed text"}
```

**XTTS Server:**
```bash
POST /speak  
Content-Type: text/plain
Body: text to speak
Response: audio/wav stream
```

## Troubleshooting

- **"Claude not found"**: Make sure Claude Code is running
- **"TTY access denied"**: Run with proper permissions 
- **"Audio device not found"**: Check `arecord -l` for available devices
- **"Server unreachable"**: Verify kairo server IP and ports

## Files

- `voice_claude.sh` - Main integration script
- `README.md` - This documentation