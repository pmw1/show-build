# FSQ PNG Generation Integration

**Status**: ✅ Fully Integrated (Ready for Testing)
**Date**: 2025-10-25
**Architecture**: Async Celery-based background processing

---

## Overview

The FSQ (Full Screen Quote) PNG generation system has been fully integrated into Show-Build with both **manual** and **programmatic** generation capabilities using Celery background workers.

### Key Benefits

1. **Non-blocking UI**: PNG generation doesn't freeze the interface
2. **Scalable**: Can offload to dedicated worker machines (including Windows workers)
3. **Automatic Retries**: Celery handles failures with exponential backoff
4. **Progress Tracking**: Real-time status monitoring via task polling
5. **Manual Control**: Users can generate PNGs on-demand from any FSQ cue card

---

## Architecture

```
┌─────────────────────┐
│  Frontend (Vue 3)   │
│  PlaceholderCueCard │
│  "Generate PNG"     │
│      Button         │
└──────────┬──────────┘
           │ POST /api/fsq/generate-async
           ▼
┌─────────────────────┐
│   Backend (FastAPI) │
│  fsq_asset_router   │
│  /generate-async    │
└──────────┬──────────┘
           │ Queue Task
           ▼
┌─────────────────────┐
│  Celery (Redis)     │
│  Task Queue         │
│  "assets" queue     │
└──────────┬──────────┘
           │ Execute
           ▼
┌─────────────────────┐
│  Celery Worker      │
│  generate_fsq_png() │
│  asset_processing.py│
└──────────┬──────────┘
           │ subprocess
           ▼
┌─────────────────────┐
│  Python Tool        │
│  render_fsq_png.py  │
│  (Pillow/PIL)       │
└──────────┬──────────┘
           │ Output
           ▼
┌─────────────────────┐
│  Episode Assets     │
│  /episodes/XXXX/    │
│  assets/images/     │
│  fsq_*.png          │
└─────────────────────┘
```

---

## Components

### 1. Celery Task (`app/services/asset_processing.py`)

**Task Name**: `services.asset_processing.generate_fsq_png`
**Queue**: `assets`
**Timeout**: 30 seconds
**Max Retries**: 2

```python
@shared_task(bind=True, name='services.asset_processing.generate_fsq_png')
def generate_fsq_png(
    self,
    episode_id: str,
    quote: str,
    attribution: str,
    slug: str,
    asset_id: str,
    alignment: str = 'center',
    font_family: str = 'serif',
    font_size: int = 70,
    duration: str = '00:00:05:00'
):
    # Creates temp JSON, calls render_fsq_png.py, returns asset path
```

**Features**:
- Progress updates (`self.update_state()`)
- Automatic retry on timeout or failure
- Task ID tracking for monitoring
- Worker hostname logging

---

### 2. API Endpoints (`app/fsq_asset_router.py`)

#### Async Generation Endpoint

**POST** `/api/fsq/generate-async`

**Request Body**:
```json
{
  "episode_id": "0246",
  "quote": "Quote text here",
  "attribution": "Source attribution",
  "slug": "quote-slug",
  "asset_id": "ASSET_12345",
  "alignment": "center",
  "font_family": "serif",
  "font_size": 70,
  "duration": "00:00:05:00"
}
```

**Response**:
```json
{
  "success": true,
  "task_id": "abc123-task-id",
  "status": "QUEUED",
  "message": "FSQ PNG generation task queued: abc123-task-id"
}
```

#### Task Status Endpoint

**GET** `/api/fsq/task/{task_id}`

**Response (In Progress)**:
```json
{
  "task_id": "abc123",
  "state": "PROGRESS",
  "ready": false,
  "progress": {
    "status": "Rendering PNG...",
    "progress": 50
  }
}
```

**Response (Completed)**:
```json
{
  "task_id": "abc123",
  "state": "SUCCESS",
  "ready": true,
  "successful": true,
  "result": {
    "success": true,
    "asset_path": "/mnt/sync/.../fsq_quote-slug.png",
    "asset_url": "/episodes/0246/assets/images/fsq_quote-slug.png",
    "asset_id": "ASSET_12345",
    "file_size": 125000,
    "filename": "fsq_quote-slug.png",
    "worker": "celery@kairo"
  }
}
```

---

### 3. Frontend Button (`disaffected-ui/src/components/content-editor/cards/PlaceholderCueCard.vue`)

**Location**: Card footer, visible only for FSQ cues

```vue
<v-btn
  v-if="cueData.type === 'FSQ'"
  size="x-small"
  variant="text"
  color="white"
  @click.stop="handleGeneratePNG"
  :loading="generatingPNG"
>
  <v-icon size="small">mdi-image-auto-adjust</v-icon>
  <span>Generate PNG</span>
</v-btn>
```

**Behavior**:
1. Validates quote data (AssetID, quote text)
2. Sends POST request to `/api/fsq/generate-async`
3. Shows task ID in alert
4. Polls task status every 2 seconds (max 30 attempts)
5. Shows completion notification with filename

---

## Usage

### Manual Generation (UI)

1. **Open Content Editor** for an episode
2. **Find an FSQ cue** in the rundown
3. **Click "Generate PNG"** button in the cue card footer
4. **Wait for notification** (usually 2-10 seconds)
5. **PNG appears** in `/episodes/{episode}/assets/images/`

### Programmatic Generation

```javascript
// From any Vue component or script
const response = await fetch('/api/fsq/generate-async', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    episode_id: '0246',
    quote: 'Your quote text',
    attribution: '1 Corinthians 14:34-35',
    slug: 'quote-slug',
    asset_id: 'ASSET_12345',
    alignment: 'center',
    font_family: 'serif',
    font_size: 70
  })
});

const { task_id } = await response.json();

// Poll for status
const statusResponse = await fetch(`/api/fsq/task/${task_id}`);
const status = await statusResponse.json();
```

---

## Celery Worker Setup

### Local Worker (Linux)

```bash
# From /mnt/process/show-build/app
celery -A celery_app worker -Q assets -l info --hostname=local_assets@%h
```

### Windows Worker

```bash
# From show-build/app directory
celery -A celery_app worker -Q assets -l info --hostname=windows_assets@%h --pool=solo
```

**Note**: Windows workers must use `--pool=solo` due to threading limitations.

---

## Configuration

### Celery Queue Routing (`app/celery_app.py`)

```python
task_routes={
    "services.asset_processing.*": {"queue": "assets"},
}
```

### Redis Connection

**URL**: `redis://:showbuild2025@192.168.51.223:6379/0`
**Queue**: `assets`

---

## Output Specifications

### PNG Format

- **Resolution**: 1920x1080 (HD)
- **Format**: PNG with transparency
- **Background**: Transparent with 80% height black overlay (75% opacity)
- **Text**: White Helvetica/Georgia/Courier (user-selectable)
- **Attribution**: Light gray, bottom-aligned
- **Font Size**: Auto-calculated or user-specified

### File Naming

**Pattern**: `fsq_{slug}.png`
**Example**: `fsq_let-your-women.png`

### File Location

**Path**: `/mnt/sync/disaffected/episodes/{episode}/assets/images/`
**URL**: `/episodes/{episode}/assets/images/fsq_{slug}.png`

---

## Testing

### Test Scenario 1: Manual Generation

1. Create FSQ cue with quote text
2. Click "Generate PNG" button
3. Verify alert shows task ID
4. Wait for completion notification
5. Check `/episodes/{episode}/assets/images/` for PNG

### Test Scenario 2: Celery Worker Failover

1. Start 2 workers (local + Windows)
2. Generate PNG
3. Kill one worker mid-processing
4. Verify other worker picks up task
5. Verify PNG generates successfully

### Test Scenario 3: API Direct Call

```bash
curl -X POST https://192.168.51.207:8888/api/fsq/generate-async \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "episode_id": "0246",
    "quote": "Test quote text",
    "attribution": "Test Attribution",
    "slug": "test-quote",
    "asset_id": "TEST_123",
    "alignment": "center"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "task_id": "...",
  "status": "QUEUED"
}
```

---

## Troubleshooting

### Issue: Task Queued But Never Processes

**Cause**: No Celery worker running on `assets` queue

**Solution**:
```bash
celery -A celery_app worker -Q assets -l info
```

### Issue: PNG Not Found After Completion

**Cause**: Path mismatch or permissions issue

**Check**:
1. Worker logs: `celery -A celery_app worker -l debug`
2. File permissions: `ls -la /mnt/sync/disaffected/episodes/{episode}/assets/images/`
3. Asset path in task result

### Issue: Timeout After 30 Seconds

**Cause**: render_fsq_png.py script not found or hanging

**Check**:
1. Script exists: `ls -la /mnt/process/show-build/tools/render_fsq_png.py`
2. Python dependencies: `pip install Pillow`
3. Font availability: `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`

### Issue: Button Not Visible

**Cause**: FSQ cue card not rendering correctly

**Check**:
1. Cue type is exactly `FSQ` (case-sensitive)
2. Vue component mounted: Check browser console
3. PlaceholderCueCard.vue loaded correctly

---

## Future Enhancements

### Planned Features

1. **Batch Generation**: Generate PNGs for all FSQ cues in an episode
2. **Template Library**: Pre-designed quote templates with different styles
3. **Video Compositing**: Generate 30-second video clips with quote over background
4. **Font Upload**: Custom font support
5. **Background Images**: User-uploaded background images for quotes
6. **Export Formats**: PDF, SVG, multiple resolutions

### Integration Points

- **Script Compilation**: Auto-generate PNGs when compiling script
- **Episode Scaffolding**: Pre-generate placeholder PNGs for template quotes
- **Media List**: Include FSQ PNGs in vMix media list exports

---

## Related Files

### Backend
- `app/services/asset_processing.py` - Celery task implementation
- `app/fsq_asset_router.py` - API endpoints
- `app/celery_app.py` - Celery configuration
- `tools/render_fsq_png.py` - PNG rendering script

### Frontend
- `disaffected-ui/src/components/content-editor/cards/PlaceholderCueCard.vue` - UI button
- `disaffected-ui/src/components/modals/FsqModal.vue` - FSQ creation modal

### Documentation
- `docs/FSQ_PNG_GENERATION_INTEGRATION.md` - This file
- `FSQ_NESTED_QUOTE_PROCESSING_UFDP.md` - Quote processing logic

---

## Summary

The FSQ PNG generation system is now fully integrated and ready for testing. The system provides:

✅ **Manual UI button** for on-demand generation
✅ **Async Celery processing** for scalability
✅ **Progress tracking** via task polling
✅ **Automatic retries** on failure
✅ **Multi-worker support** (local + Windows)
✅ **REST API** for programmatic access

**Next Steps**: Start a Celery worker and test the "Generate PNG" button on an FSQ cue card!
