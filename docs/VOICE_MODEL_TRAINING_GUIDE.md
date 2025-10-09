# Voice Model Training System - Developer Guide

## Overview
Progressive voice sample collection and model training system for building speaker-specific voice models over time. Designed for weekly ingestion of dry audio recordings to gradually build production-quality voice models.

## Status: **STUBBED** ⚠️

The API endpoints and file storage infrastructure are in place, but core processing pipelines are not yet implemented.

## Architecture

### Storage Paths
- **Voice Samples**: `/shared_media/voice_samples/{speaker_slug}/`
- **Voice Models**: `/shared_media/voice_models/{speaker_slug}/`

### API Endpoints

#### `POST /api/voice-model/ingest-sample`
Upload raw audio samples for progressive training dataset building.

**Request**:
```bash
curl -X POST http://192.168.51.210:8888/api/voice-model/ingest-sample \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_file=@josh_week12_dry.mp3" \
  -F "speaker_id=1" \
  -F "week_number=12" \
  -F "episode_number=456" \
  -F "description=Dry audio from episode 456"
```

**Response**:
```json
{
  "success": true,
  "speaker": "Josh",
  "sample_path": "/shared_media/voice_samples/josh/20250107_143022_week12_ep456.mp3",
  "file_size_mb": 45.3,
  "week": "12",
  "episode": "456",
  "message": "Voice sample ingested. Transcription and segmentation pending."
}
```

**Status**: ✅ **Implemented** - File upload and storage working
**TODO**:
- Whisper transcription integration
- Voice segment extraction (5-10 sec chunks)
- Database metadata storage

---

#### `GET /api/voice-model/samples/{speaker_id}`
List all collected voice samples for a speaker.

**Request**:
```bash
curl http://192.168.51.210:8888/api/voice-model/samples/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response**:
```json
{
  "success": true,
  "speaker": "Josh",
  "samples": [
    {
      "filename": "20250107_143022_week12_ep456.mp3",
      "path": "/shared_media/voice_samples/josh/20250107_143022_week12_ep456.mp3",
      "size_mb": 45.3,
      "created": 1704641422
    }
  ],
  "total_count": 12,
  "total_size_mb": 523.7,
  "estimated_duration_minutes": 85.2,
  "training_ready": true,
  "minimum_required_minutes": 5,
  "recommended_minutes": 30
}
```

**Status**: ✅ **Implemented** - File listing working
**Note**: Duration estimation is rough (1 MB ≈ 1 minute). Actual duration extraction pending.

---

#### `POST /api/voice-model/train/{speaker_id}`
Train a voice model from collected samples.

**Request**:
```bash
curl -X POST http://192.168.51.210:8888/api/voice-model/train/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "model_name=josh_model_v1"
```

**Response**:
```json
{
  "success": true,
  "status": "training_queued",
  "speaker": "Josh",
  "model_id": "josh_model_v1",
  "sample_count": 12,
  "estimated_training_time_minutes": 24,
  "message": "Voice model training queued. This feature is under development.",
  "next_steps": [
    "Training pipeline integration with XTTS",
    "Model quality evaluation",
    "A/B testing vs original voice"
  ]
}
```

**Status**: ⚠️ **STUBBED** - Returns success but doesn't train
**TODO**:
- XTTS fine-tuning API integration
- Training manifest generation
- Model checkpoint storage
- Quality metrics evaluation

---

#### `GET /api/voice-model/models/{speaker_id}`
List trained voice models for a speaker.

**Request**:
```bash
curl http://192.168.51.210:8888/api/voice-model/models/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response**:
```json
{
  "success": true,
  "speaker": "Josh",
  "models": [
    {
      "model_id": "josh_20250107_143500",
      "path": "/shared_media/voice_models/josh/josh_20250107_143500",
      "created": 1704641700,
      "size_mb": 245.8
    }
  ],
  "total_count": 1
}
```

**Status**: ✅ **Implemented** - Directory listing working
**Note**: No models exist yet since training is stubbed.

---

#### `DELETE /api/voice-model/sample/{speaker_id}/{filename}`
Delete a voice sample (quality control).

**Request**:
```bash
curl -X DELETE http://192.168.51.210:8888/api/voice-model/sample/1/20250107_143022_week12_ep456.mp3 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response**:
```json
{
  "success": true,
  "message": "Sample 20250107_143022_week12_ep456.mp3 deleted"
}
```

**Status**: ✅ **Implemented** - File deletion working

---

## Workflow Design

### Phase 1: Initial "Bullshit" Model (Current)
**Goal**: Quick proof-of-concept with XTTS fine-tuning

1. Collect 5-10 minutes of clean audio
2. Generate XTTS fine-tuned model (quick, lower quality)
3. Test in production (Discord bot, etc.)

**Status**: Infrastructure ready, XTTS integration pending

---

### Phase 2: Progressive Weekly Collection (In Progress)
**Goal**: Build robust training dataset over time

**Weekly Workflow**:
1. Record episode (include dry audio track)
2. Upload dry audio via `/ingest-sample` endpoint
3. System automatically:
   - Transcribes with Whisper
   - Extracts clean voice segments
   - Stores with metadata
   - Adds to training dataset

**Accumulation Strategy**:
- **Week 1-4**: 5-20 minutes (basic model possible)
- **Week 5-12**: 30-60 minutes (good quality model)
- **Week 13+**: 2+ hours (production-grade model)

**Status**: Sample ingestion working, processing pipeline stubbed

---

### Phase 3: Robust Model Training (Future)
**Goal**: Production-quality voice models with quality metrics

**Training Pipeline**:
1. Combine all samples into training manifest
2. Extract mel spectrograms from audio
3. Train prosody model (speech patterns)
4. Train acoustic model (voice characteristics)
5. Fine-tune with speaker embedding
6. Generate quality metrics (MOS score, etc.)
7. A/B test vs original voice

**Status**: Fully stubbed, design in place

---

## File Organization

### Sample Naming Convention
```
{timestamp}_{week}{week_number}_{ep}{episode_number}.{ext}

Examples:
20250107_143022_week12_ep456.mp3
20250114_092315_week13_ep457.wav
```

### Model Naming Convention
```
{speaker_slug}_{timestamp}

Examples:
josh_20250107_143500
kevin_20250108_091200
```

---

## Database Schema (Pending)

```sql
CREATE TABLE voice_samples (
    id SERIAL PRIMARY KEY,
    speaker_id INTEGER REFERENCES speakers(id),
    file_path TEXT NOT NULL,
    transcript TEXT,
    duration_seconds FLOAT,
    week_number INTEGER,
    episode_number INTEGER,
    quality_score FLOAT,
    is_training_ready BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE voice_models (
    id SERIAL PRIMARY KEY,
    speaker_id INTEGER REFERENCES speakers(id),
    model_id TEXT UNIQUE NOT NULL,
    model_path TEXT NOT NULL,
    sample_count INTEGER,
    training_duration_minutes FLOAT,
    quality_metrics JSONB,
    is_production BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Status**: Schema designed, migration not created

---

## Integration Points

### WPM Audio Analysis
Voice samples can be analyzed for WPM using the `/api/wpm-audio/analyze` endpoint:
```bash
curl -X POST http://192.168.51.210:8888/api/wpm-audio/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_file=@sample.mp3" \
  -F "speaker_id=1"
```

### Whisper Transcription
Shares Whisper configuration with WPM analysis tool:
- Primary: `whisper-medium` (192.168.51.197:8887)
- Fallback: `openwebui-whisper-api` (192.168.51.197:8886)
- Config: Database `api_configs` table

### Future: Discord Bot
Planned integration for automated sample collection via Discord channel uploads.

---

## Development TODO

### High Priority
- [ ] Integrate Whisper transcription into sample ingestion
- [ ] Implement voice segment extraction (5-10 sec chunks)
- [ ] Create `voice_samples` database table
- [ ] Store sample metadata in database

### Medium Priority
- [ ] Connect XTTS fine-tuning API
- [ ] Implement training manifest generation
- [ ] Build model checkpoint storage
- [ ] Add quality metrics evaluation

### Low Priority
- [ ] Create frontend upload modal
- [ ] Build A/B testing framework
- [ ] Discord bot integration
- [ ] Automated quality scoring

---

## Testing

### Test Sample Ingestion
```bash
# Upload test audio
curl -X POST http://192.168.51.210:8888/api/voice-model/ingest-sample \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_file=@test_voice.mp3" \
  -F "speaker_id=1" \
  -F "week_number=1" \
  -F "episode_number=100"

# List samples
curl http://192.168.51.210:8888/api/voice-model/samples/1 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check file storage
ls -lh /shared_media/voice_samples/josh/
```

### Verify Router Registration
```bash
# Check API docs
curl http://192.168.51.210:8888/docs

# Look for /api/voice-model/* endpoints
```

---

## Notes

**User Vision** (from conversation):
> "we can do a bullshit one initially even with xtts and a few seconds. but yes, slowly and over time... week by week i want to add to it and start building a model.."

**Future Use Cases**:
- Discord bot for voice generation
- Automated podcast narration
- Voice replacement/enhancement
- Multi-speaker synthesis

**Design Philosophy**:
- Start simple (XTTS quick model)
- Build progressively (weekly collection)
- Maintain quality (transcription + metadata)
- Plan for production (robust training pipeline)

---

**Status**: Infrastructure complete, processing pipelines pending
**File**: `/mnt/process/show-build/app/voice_model_router.py`
**Registered**: Yes (main.py line 75, 178)
