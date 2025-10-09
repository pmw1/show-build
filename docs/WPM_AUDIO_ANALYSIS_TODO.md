# WPM Audio Analysis Tool - Implementation TODO

## Overview
Upload MP3 audio to automatically calculate Words Per Minute (WPM) for speaker profiles.

## Endpoint Created
`POST /api/wpm-audio/analyze`

## What's Stubbed Out

### ✅ Complete
- API endpoint structure
- File upload handling (MP3, WAV, M4A)
- Audio duration extraction (using ffprobe)
- Word counting logic
- WPM calculation (words / minutes)
- Speaker profile update

### ⚠️ Needs Implementation

#### 1. Audio Transcription
**Current Status**: Stubbed to use `faster-whisper` library

**Options for Tonight:**

**Option A: Use Your Whisper Server** (RECOMMENDED if you have access info)
```python
# In transcribe_audio() function
import httpx

async def transcribe_audio(audio_path: str) -> str:
    # Load Whisper server config from database (api_configs table)
    # TODO: Add to api_configs:
    #   service: whisper
    #   host: http://YOUR_WHISPER_SERVER:PORT
    #   api_key: YOUR_KEY (if needed)

    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(audio_path, 'rb') as f:
            response = await client.post(
                f"{whisper_host}/transcribe",
                files={"file": f}
            )

    return response.json()["text"]
```

**Option B: Local faster-whisper** (if no server available)
```bash
# Install in container
pip install faster-whisper

# Already coded - just uncomment in wpm_audio_router.py
```

**Option C: OpenAI Whisper API** (costs money but simple)
```python
import openai

def transcribe_audio(audio_path: str) -> str:
    with open(audio_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript["text"]
```

#### 2. Frontend Upload Component
Create a modal or section in MetadataPanel:
- File upload input (accept MP3/WAV/M4A)
- Speaker selection dropdown
- Progress indicator during transcription
- Display results: WPM, word count, duration, transcript preview
- Button to save WPM to speaker profile

#### 3. Dependencies to Add
```txt
# Add to requirements.txt
faster-whisper==0.10.0  # If using local transcription
```

## Usage Flow

1. User opens WPM measurement tool
2. Uploads MP3 of speaker (Josh, Kevin, etc.)
3. Backend:
   - Extracts audio duration
   - Transcribes to text
   - Counts words
   - Calculates WPM
4. Frontend displays results
5. User confirms and saves to speaker profile
6. Speaker's WPM is now accurate for all timing calculations

## API Response Example

```json
{
  "success": true,
  "wpm": 165,
  "wpm_min": 140,
  "wpm_max": 190,
  "word_count": 450,
  "duration_seconds": 163.5,
  "transcript": "This is the beginning of the transcript...",
  "full_transcript_length": 2847,
  "speaker_updated": true
}
```

## Where to Add Whisper Server Config

**If using your Whisper server**, add to `api_configs` table:

```sql
INSERT INTO api_configs (workflow, category, service, config_key, config_value, is_enabled, created_at, updated_at)
VALUES
  ('preproduction', 'ai_services', 'whisper', 'host', 'http://YOUR_SERVER:PORT', true, NOW(), NOW()),
  ('preproduction', 'ai_services', 'whisper', 'enabled', 'true', true, NOW(), NOW());
```

Then in `wpm_audio_router.py`, load config like Ollama does:
```python
from api_config import api_config_manager

whisper_config = api_config_manager.get_service_config(
    workflow="preproduction",
    category="ai_services",
    service="whisper"
)
```

## Testing

```bash
# Test endpoint
curl -X POST http://192.168.51.210:8888/api/wpm-audio/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_file=@test_audio.mp3" \
  -F "speaker_id=1"
```

## Next Steps for Tonight

1. Add Whisper server info to api_configs table
2. Implement `transcribe_audio()` function to call your Whisper server
3. Test with a sample MP3
4. Create simple frontend upload form
5. Measure Josh and Kevin's actual WPM rates!

---

**File**: `/mnt/process/show-build/app/wpm_audio_router.py`
**Status**: Backend API ready, transcription needs connection to your Whisper server
