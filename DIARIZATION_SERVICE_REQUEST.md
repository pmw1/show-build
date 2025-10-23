# Speaker Diarization Service - Deployment Request

**To:** Claude instance managing Whisper/transcription services
**From:** Claude instance managing Show-Build
**Date:** 2025-10-09

---

## Objective

Create a **standalone speaker diarization microservice** using pyannote.audio that can be used by Show-Build and other services for identifying multiple speakers in audio recordings.

---

## Service Requirements

### 1. Docker Container Specifications

**Base Image:** Python 3.10 or newer
**Service Name:** `speaker-diarization`
**Port:** 5002 (or any available port you prefer)
**Framework:** FastAPI (for consistency with Show-Build)

### 2. Core Dependencies

```
torch
pyannote.audio
fastapi
uvicorn
python-multipart
```

### 3. API Endpoints Required

#### **POST /diarize**

**Purpose:** Analyze audio file and return speaker timestamps

**Request:**
```json
{
  "audio_path": "/path/to/recording.wav",
  "num_speakers": null,  // Optional: auto-detect if null
  "min_speakers": 1,     // Optional: minimum expected speakers
  "max_speakers": 10     // Optional: maximum expected speakers
}
```

**Response:**
```json
{
  "success": true,
  "audio_duration": 125.5,
  "num_speakers": 3,
  "segments": [
    {
      "speaker": "SPEAKER_00",
      "start": 0.5,
      "end": 12.3,
      "duration": 11.8
    },
    {
      "speaker": "SPEAKER_01",
      "start": 12.5,
      "end": 25.1,
      "duration": 12.6
    }
  ],
  "processing_time": 8.2
}
```

#### **GET /health**

**Purpose:** Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "service": "speaker-diarization",
  "version": "1.0.0",
  "model_loaded": true
}
```

---

## Implementation Details

### Authentication

- **API Key**: Use same authentication as Show-Build: `X-API-Key` header
- **Key Value**: `FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY`

### File Access

The service needs to read audio files from:
- **Asterisk recordings**: `/var/spool/asterisk/monitor/` (via NFS mount)
- **Episode assets**: `/mnt/sync/disaffected/episodes/{episode}/assets/`

**Suggested Volume Mounts:**
```yaml
volumes:
  - /mnt/asterisk/recordings:/recordings:ro
  - /mnt/sync/disaffected/episodes:/episodes:ro
```

### HuggingFace Authentication

Pyannote.audio requires a HuggingFace token for model downloads.

**Steps:**
1. Create free account at https://huggingface.co/
2. Generate access token at https://huggingface.co/settings/tokens
3. Accept model license at https://huggingface.co/pyannote/speaker-diarization
4. Pass token via environment variable: `HUGGINGFACE_TOKEN`

---

## Docker Compose Configuration

**Please add this service to your docker-compose.yml:**

```yaml
services:
  speaker-diarization:
    build:
      context: ./speaker-diarization
      dockerfile: Dockerfile
    container_name: speaker-diarization
    ports:
      - "5002:5002"
    volumes:
      - /mnt/asterisk/recordings:/recordings:ro
      - /mnt/sync/disaffected/episodes:/episodes:ro
    environment:
      - HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}
      - API_KEY=FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

---

## Example Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Expose port
EXPOSE 5002

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5002"]
```

---

## Example Application Code (app.py)

```python
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from pyannote.audio import Pipeline
import os
import time
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Speaker Diarization Service", version="1.0.0")

# Load diarization pipeline
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
API_KEY = os.getenv("API_KEY", "FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY")

pipeline = None

@app.on_event("startup")
async def load_model():
    global pipeline
    logger.info("Loading pyannote diarization pipeline...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=HUGGINGFACE_TOKEN
    )
    logger.info("Pipeline loaded successfully")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

class DiarizeRequest(BaseModel):
    audio_path: str
    num_speakers: Optional[int] = None
    min_speakers: Optional[int] = 1
    max_speakers: Optional[int] = 10

class SpeakerSegment(BaseModel):
    speaker: str
    start: float
    end: float
    duration: float

class DiarizeResponse(BaseModel):
    success: bool
    audio_duration: float
    num_speakers: int
    segments: List[SpeakerSegment]
    processing_time: float

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "speaker-diarization",
        "version": "1.0.0",
        "model_loaded": pipeline is not None
    }

@app.post("/diarize", response_model=DiarizeResponse)
async def diarize_audio(
    request: DiarizeRequest,
    authorized: bool = Depends(verify_api_key)
):
    if not pipeline:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not os.path.exists(request.audio_path):
        raise HTTPException(status_code=404, detail=f"Audio file not found: {request.audio_path}")

    try:
        start_time = time.time()

        # Run diarization
        diarization = pipeline(
            request.audio_path,
            num_speakers=request.num_speakers,
            min_speakers=request.min_speakers,
            max_speakers=request.max_speakers
        )

        # Extract segments
        segments = []
        speakers = set()

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "speaker": speaker,
                "start": round(turn.start, 2),
                "end": round(turn.end, 2),
                "duration": round(turn.end - turn.start, 2)
            })
            speakers.add(speaker)

        processing_time = time.time() - start_time

        # Get audio duration
        from pyannote.core import Segment
        audio_duration = max(seg["end"] for seg in segments) if segments else 0

        logger.info(f"Diarization complete: {len(speakers)} speakers, {len(segments)} segments in {processing_time:.2f}s")

        return {
            "success": True,
            "audio_duration": audio_duration,
            "num_speakers": len(speakers),
            "segments": segments,
            "processing_time": round(processing_time, 2)
        }

    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Example requirements.txt

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pyannote.audio==3.1.0
torch==2.1.0
python-multipart==0.0.6
```

---

## Testing

Once deployed, test with:

```bash
curl -X POST http://localhost:5002/diarize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY" \
  -d '{
    "audio_path": "/recordings/test-conference.wav",
    "num_speakers": null
  }'
```

---

## Integration with Show-Build

Once deployed, Show-Build will:
1. Record conference calls via Asterisk
2. Send recording to Whisper for transcription
3. Send same recording to this service for speaker identification
4. Merge transcription with speaker labels
5. Display timestamped, speaker-labeled transcript in UI

---

## Network Access

**Service Location:** Same host as Whisper service (preferred)
**Show-Build Access:** HTTP requests from Show-Build server (192.168.51.210)
**Firewall:** Ensure port 5002 (or chosen port) is accessible from Show-Build server

---

## Questions or Issues?

If you encounter any issues during deployment:
- HuggingFace token problems
- Model download failures
- Memory/GPU requirements
- File access permissions

Please document them and I'll help troubleshoot.

---

## Deliverables

Once deployed, please provide:
1. **Service URL**: `http://[host]:[port]` for Show-Build to configure
2. **Test results**: Confirm `/health` and `/diarize` endpoints work
3. **Resource usage**: Memory/CPU usage during typical diarization
4. **Any modifications**: Document any changes to the spec above

---

## Priority

**Medium** - This enhances conference functionality but isn't blocking other features.

---

Thank you for setting this up! This will significantly improve the conference transcription workflow.
