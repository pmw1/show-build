# Media Processing Workflow for Show-Build

> **📖 About This Document**
>
> This is **comprehensive workflow documentation** for video/audio processing in Show-Build's distributed architecture. This document explains the entire lifecycle of a media file from upload through processing to final delivery, including preprocessing, distributed task execution, and postprocessing steps.
>
> **If you're looking to:**
> - **Understand the complete workflow** → See [Section 2: Complete Workflow](#2-complete-workflow)
> - **Add new media processing tasks** → See [Section 5: Development Guide](#5-development-guide)
> - **Troubleshoot processing failures** → See [Section 7: Troubleshooting](#7-troubleshooting)
> - **Understand preprocessing steps** → See [Section 3: Preprocessing](#3-preprocessing)
> - **Understand postprocessing steps** → See [Section 4: Postprocessing](#4-postprocessing)
>
> **UFDP Format**: This document follows the Unified Feature Documentation Protocol with hierarchical section indexing.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Complete Workflow](#2-complete-workflow)
3. [Preprocessing](#3-preprocessing)
4. [Postprocessing](#4-postprocessing)
5. [Development Guide](#5-development-guide)
6. [Task Types](#6-task-types)
7. [Troubleshooting](#7-troubleshooting)
8. [Performance Optimization](#8-performance-optimization)

---

## 1. Overview

### 1.1 What is Media Processing?

**Media processing** in Show-Build refers to the automated conversion, extraction, and manipulation of video/audio files uploaded by users. This includes:

- **Video trimming** - Cut segments from longer files
- **Audio extraction** - Pull audio tracks from video
- **Thumbnail generation** - Create preview images
- **Format conversion** - Convert between codecs/containers
- **Quality adjustment** - Change resolution, bitrate, etc.

### 1.2 Why Distributed Processing?

**Problem:** FFmpeg operations are CPU-intensive and can take minutes per file

**Solution:** Offload processing to dedicated worker machines with:
- High CPU cores (FFmpeg parallelization)
- GPU acceleration (NVIDIA/AMD for encoding)
- Fast storage (NVMe for temp files)
- Isolated from web server (doesn't impact user requests)

**Architecture:**
```
USER → WHISPER (Web Server) → REDIS (Task Queue) → KAIRO/PROXIMA (Workers) → WHISPER (Results)
```

### 1.3 Media Types Processed

| Type | Extension | Use Case | Processing Steps |
|------|-----------|----------|------------------|
| **SOT** | .mp4, .mov | Sound on Tape (interview clips) | Extract audio, generate thumbnail, trim |
| **FSQ** | .png | Full Screen Quote | Image optimization, text rendering |
| **VO** | .mp3, .wav | Voice Over | Audio normalization, format conversion |
| **PKG** | .mp4 | Package (complete segments) | Trimming, quality adjustment |
| **NAT** | .mp3, .wav | Natural sound | Audio extraction, level adjustment |

---

## 2. Complete Workflow

### 2.1 End-to-End SOT Processing Example

**Scenario:** User uploads 10-minute interview video, wants 30-second clip

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: UPLOAD & PREPROCESSING (Whisper)                           │
└─────────────────────────────────────────────────────────────────────┘

1. USER ACTION
   ├─ Opens Content Editor, selects episode 0245
   ├─ Clicks "Add SOT" button
   └─ Fills form:
      - File: interview_mayor.mp4 (125 MB, 10:23 duration)
      - Slug: mayor-interview
      - Trim: 02:15 to 02:45 (30 seconds)

2. FRONTEND (Vue Component)
   ├─ Validates file type (must be video/*)
   ├─ Validates file size (< 500 MB)
   └─ Submits multipart/form-data to API:
      POST /api/sot/upload
      {
        file: [binary data],
        episode: "0245",
        slug: "mayor-interview",
        trim_start: "00:02:15",
        trim_end: "00:02:45"
      }

3. WHISPER: sot_router.py (FastAPI Endpoint)
   ├─ Receives upload (line 37-89)
   ├─ Validates content type (must start with 'video/')
   ├─ Saves to shared temp directory:
   │  /mnt/sync/temp/uploads/0245_mayor-interview_interview_mayor.mp4
   │  (This is on NFS - visible to all workers!)
   └─ Returns immediately:
      {
        "task_id": "e4f7a9d2-1234-5678-90ab-cdef12345678",
        "message": "SOT video queued for processing on media worker",
        "status": "queued"
      }

4. WHISPER: sot_router.py (Task Submission)
   ├─ Submits Celery task (line 77-80):
   │  process_sot_video.apply_async(
   │    args=[
   │      "/mnt/sync/temp/uploads/0245_mayor-interview_interview_mayor.mp4",
   │      "0245",
   │      "mayor-interview",
   │      "00:02:15",
   │      "00:02:45"
   │    ],
   │    queue='media'
   │  )
   └─ Task serialized to JSON and sent to Redis

┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: TASK QUEUING (Farmhouse - Redis)                           │
└─────────────────────────────────────────────────────────────────────┘

5. REDIS (farmhouse:6379)
   ├─ Receives task via RPUSH to 'media' queue
   ├─ Stores task data:
   │  {
   │    "task": "services.ffmpeg_tasks.process_sot_video",
   │    "id": "e4f7a9d2-1234-5678-90ab-cdef12345678",
   │    "args": [...],
   │    "kwargs": {},
   │    "eta": null,
   │    "expires": null
   │  }
   └─ Waits for worker to BLPOP (blocking pop)

┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: TASK EXECUTION (Kairo - Celery Worker)                     │
└─────────────────────────────────────────────────────────────────────┘

6. KAIRO: Celery Worker
   ├─ Polls Redis every 1 second: BLPOP media
   ├─ Receives task e4f7a9d2-...
   ├─ Loads task module: services.ffmpeg_tasks
   ├─ Sets task status in Redis:
   │  "celery-task-meta-e4f7a9d2-..." = {"status": "STARTED", ...}
   └─ Executes process_sot_video()

7. KAIRO: ffmpeg_tasks.py (Processing Logic)

   Step 1: Get video duration
   ├─ Command: ffprobe -v error -show_entries format=duration
   │           /mnt/sync/temp/uploads/0245_mayor-interview_interview_mayor.mp4
   ├─ Output: 623.45 (seconds)
   └─ Log: "Video duration: 623.45s"

   Step 2: Create output directory
   ├─ Path: /home/episodes/0245/assets/sots/
   │  (This is /mnt/sync/disaffected/episodes/0245/assets/sots/ via NFS)
   ├─ Command: mkdir -p (creates parent dirs if needed)
   └─ Log: "Created output directory"

   Step 3: Generate thumbnail
   ├─ Command: ffmpeg -y -ss 1
   │           -i /mnt/sync/temp/uploads/0245_mayor-interview_interview_mayor.mp4
   │           -vframes 1 -q:v 2
   │           /home/episodes/0245/assets/sots/mayor-interview-thumb.jpg
   ├─ Output: 150 KB JPEG (1920x1080)
   ├─ Time: ~2 seconds
   └─ Log: "Thumbnail created: mayor-interview-thumb.jpg"

   Step 4: Extract audio
   ├─ Command: ffmpeg -y
   │           -i /mnt/sync/temp/uploads/0245_mayor-interview_interview_mayor.mp4
   │           -vn -acodec libmp3lame -ab 192k
   │           /home/episodes/0245/assets/sots/mayor-interview.mp3
   ├─ Output: 23 MB MP3 (full 10:23 audio)
   ├─ Time: ~15 seconds
   └─ Log: "Audio extracted: mayor-interview.mp3"

   Step 5: Trim video
   ├─ Calculate trim duration:
   │  start = 02:15 = 135 seconds
   │  end = 02:45 = 165 seconds
   │  duration = 30 seconds
   ├─ Command: ffmpeg -y -ss 00:02:15
   │           -i /mnt/sync/temp/uploads/0245_mayor-interview_interview_mayor.mp4
   │           -t 30 -c copy
   │           /home/episodes/0245/assets/sots/mayor-interview.mp4
   ├─ Output: 12 MB MP4 (30 seconds, codec copy = fast)
   ├─ Time: ~3 seconds (codec copy is fast!)
   └─ Log: "Video processed: mayor-interview.mp4"

   Step 6: Cleanup temp file
   ├─ Command: rm /mnt/sync/temp/uploads/0245_mayor-interview_interview_mayor.mp4
   └─ Log: "Removed temp file"

   Step 7: Return result
   └─ Returns dict:
      {
        "thumbnail_path": "0245/assets/sots/mayor-interview-thumb.jpg",
        "audio_path": "0245/assets/sots/mayor-interview.mp3",
        "video_path": "0245/assets/sots/mayor-interview.mp4",
        "duration": 30.0,
        "status": "completed"
      }

8. KAIRO: Celery Worker (Result Storage)
   ├─ Serializes result to JSON
   ├─ Stores in Redis:
   │  SET "celery-task-meta-e4f7a9d2-..." '{"status": "SUCCESS", "result": {...}}'
   └─ Task complete (total time: ~20 seconds)

┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 4: POSTPROCESSING & DELIVERY (Whisper)                        │
└─────────────────────────────────────────────────────────────────────┘

9. FRONTEND: Status Polling
   ├─ Every 2 seconds, polls:
   │  GET /api/sot/tasks/e4f7a9d2-1234-5678-90ab-cdef12345678/status
   ├─ Receives:
   │  {"task_id": "e4f7a9d2-...", "status": "STARTED"}  (first few polls)
   │  {"task_id": "e4f7a9d2-...", "status": "SUCCESS", "result": {...}}  (final)
   └─ Updates UI: "Processing complete!"

10. WHISPER: sot_router.py (Status Endpoint)
    ├─ Receives GET request (line 92-124)
    ├─ Queries Redis for task result:
    │  AsyncResult(task_id, app=celery_app)
    ├─ Returns result to frontend:
    │  {
    │    "task_id": "e4f7a9d2-...",
    │    "status": "SUCCESS",
    │    "result": {
    │      "thumbnail_path": "0245/assets/sots/mayor-interview-thumb.jpg",
    │      "audio_path": "0245/assets/sots/mayor-interview.mp3",
    │      "video_path": "0245/assets/sots/mayor-interview.mp4",
    │      "duration": 30.0
    │    }
    │  }
    └─ Frontend displays success, shows thumbnail preview

11. FRONTEND: Update Episode Data
    ├─ Creates/updates rundown item in database:
    │  INSERT INTO rundown_items (episode_id, slug, type, duration, ...)
    │  VALUES (0245, 'mayor-interview', 'SOT', 30.0, ...)
    ├─ Saves asset paths to cue metadata
    └─ User sees new SOT item in rundown panel

12. FILE LOCATIONS (Final State)
    /mnt/sync/disaffected/episodes/0245/assets/sots/
    ├── mayor-interview-thumb.jpg  (150 KB)
    ├── mayor-interview.mp3        (23 MB, full audio)
    └── mayor-interview.mp4        (12 MB, 30 sec trimmed video)
```

### 2.2 Data Flow Diagram

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│  BROWSER │      │  WHISPER │      │  REDIS   │      │  KAIRO   │
│  (User)  │      │ (FastAPI)│      │(farmhouse)│      │ (Worker) │
└────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                  │                  │
     │ 1. Upload file  │                  │                  │
     ├────────────────>│                  │                  │
     │                 │                  │                  │
     │                 │ 2. Save to NFS   │                  │
     │                 │    /mnt/sync/    │                  │
     │                 │    temp/uploads  │                  │
     │                 │                  │                  │
     │                 │ 3. Queue task    │                  │
     │                 ├─────────────────>│                  │
     │                 │                  │                  │
     │ 4. Return       │                  │ 5. Worker polls  │
     │    task_id      │                  │    (BLPOP)       │
     │<────────────────┤                  │<─────────────────┤
     │                 │                  │                  │
     │                 │                  │ 6. Dequeue task  │
     │                 │                  ├─────────────────>│
     │                 │                  │                  │
     │                 │                  │                  │ 7. Read input
     │                 │                  │                  │    from NFS
     │                 │                  │                  │
     │                 │                  │                  │ 8. Process
     │                 │                  │                  │    (FFmpeg)
     │                 │                  │                  │
     │                 │                  │                  │ 9. Write output
     │                 │                  │                  │    to NFS
     │                 │                  │                  │
     │                 │                  │ 10. Store result │
     │                 │                  │<─────────────────┤
     │                 │                  │                  │
     │ 11. Poll status │                  │                  │
     ├────────────────>│                  │                  │
     │                 │                  │                  │
     │                 │ 12. Check Redis  │                  │
     │                 ├─────────────────>│                  │
     │                 │                  │                  │
     │                 │ 13. Return result│                  │
     │                 │<─────────────────┤                  │
     │                 │                  │                  │
     │ 14. Deliver     │                  │                  │
     │     result      │                  │                  │
     │<────────────────┤                  │                  │
     │                 │                  │                  │
```

---

## 3. Preprocessing

### 3.1 What is Preprocessing?

**Preprocessing** = Steps taken BEFORE submitting task to Celery

**Goals:**
1. Validate user input (file type, size, format)
2. Save uploaded file to shared location
3. Generate unique identifiers
4. Prepare task parameters

### 3.2 Preprocessing Steps (Detailed)

#### Step 1: Frontend Validation

**Location:** `disaffected-ui/src/components/modals/SotModal.vue`

```javascript
// File type validation
const allowedTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo']
if (!allowedTypes.includes(file.type)) {
  showError("Invalid file type. Please upload MP4, MOV, or AVI.")
  return
}

// File size validation (500 MB limit)
const maxSize = 500 * 1024 * 1024
if (file.size > maxSize) {
  showError("File too large. Maximum size is 500 MB.")
  return
}

// Duration validation (if provided)
if (trimStart && trimEnd) {
  const start = parseTime(trimStart)  // Convert HH:MM:SS to seconds
  const end = parseTime(trimEnd)

  if (end <= start) {
    showError("End time must be after start time.")
    return
  }

  if (end - start > 300) {  // 5 minutes max
    showError("Trimmed clip cannot exceed 5 minutes.")
    return
  }
}
```

#### Step 2: File Upload to Server

**Transport:** Multipart form data (handles large files efficiently)

```javascript
// Create FormData object
const formData = new FormData()
formData.append('file', file)  // File object from <input type="file">
formData.append('episode', episode)
formData.append('slug', slug)
formData.append('trim_start', trimStart || '00:00:00')
formData.append('trim_end', trimEnd || '00:00:00')

// Upload with progress tracking
const response = await axios.post('/api/sot/upload', formData, {
  headers: {
    'Content-Type': 'multipart/form-data'
  },
  onUploadProgress: (progressEvent) => {
    const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
    updateProgress(percentCompleted)
  }
})
```

**Network considerations:**
- 100 MB file over gigabit LAN = ~1 second
- 100 MB file over 100 Mbps WAN = ~10 seconds
- Show progress bar to user during upload

#### Step 3: Server-Side File Handling

**Location:** `app/sot_router.py` (line 62-74)

```python
# Validate content type (server-side check, don't trust client)
if not file.content_type.startswith('video/'):
    raise HTTPException(status_code=400, detail="File must be a video")

# Create shared temp directory (on NFS mount)
temp_dir = Path("/mnt/sync/temp/uploads")
temp_dir.mkdir(exist_ok=True)  # Create if doesn't exist

# Generate unique filename to prevent collisions
# Format: {episode}_{slug}_{original_filename}
temp_file_path = temp_dir / f"{episode}_{slug}_{file.filename}"

# Save uploaded file (streaming to avoid loading entire file in memory)
with open(temp_file_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)
```

**Why `/mnt/sync/temp/uploads`?**
- It's on NFS (kairo can read it directly)
- Temporary location (cleaned up after processing)
- Avoids copying file twice (upload → local → worker)

#### Step 4: Task Submission

```python
# Submit to Celery
task = process_sot_video.apply_async(
    args=[
        str(temp_file_path),  # Where worker will find the file
        episode,              # Episode number
        slug,                 # Output filename base
        trim_start,           # Trim start time
        trim_end              # Trim end time
    ],
    queue='media'  # Route to media queue (high CPU workers)
)

# Return task ID to client for polling
return SOTUploadResponse(
    task_id=task.id,
    message=f"SOT video queued for processing on media worker",
    status="queued"
)
```

### 3.3 Preprocessing Checklist

Before submitting any media processing task:

- [x] Validate file type (frontend + backend)
- [x] Validate file size (< 500 MB)
- [x] Validate parameters (trim times, codec options, etc.)
- [x] Save to shared NFS location (not local disk)
- [x] Generate unique filename (prevent collisions)
- [x] Set appropriate task queue (media, compilation, etc.)
- [x] Return task ID immediately (don't wait for completion)

---

## 4. Postprocessing

### 4.1 What is Postprocessing?

**Postprocessing** = Steps taken AFTER Celery task completes

**Goals:**
1. Retrieve task results from Redis
2. Update database with file paths
3. Notify user of completion
4. Clean up temporary files
5. Trigger dependent tasks (if needed)

### 4.2 Postprocessing Steps (Detailed)

#### Step 1: Status Polling

**Location:** `disaffected-ui/src/components/modals/SotModal.vue`

```javascript
// Poll task status every 2 seconds
const pollInterval = setInterval(async () => {
  const response = await axios.get(`/api/sot/tasks/${taskId}/status`)

  if (response.data.status === 'SUCCESS') {
    clearInterval(pollInterval)
    handleSuccess(response.data.result)
  } else if (response.data.status === 'FAILURE') {
    clearInterval(pollInterval)
    handleError(response.data.error)
  } else {
    // Still processing (PENDING or STARTED)
    updateProgress('Processing video...')
  }
}, 2000)
```

**Why polling instead of WebSocket?**
- Simpler implementation
- Works through proxies/load balancers
- Less server resources (2-second interval is fine)
- Can be paused/resumed easily

#### Step 2: Result Retrieval

**Location:** `app/sot_router.py` (line 92-124)

```python
@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, current_user=Depends(...)):
    # Query Celery result backend (Redis)
    task_result = AsyncResult(task_id, app=celery_app)

    response = TaskStatusResponse(
        task_id=task_id,
        status=task_result.status  # PENDING, STARTED, SUCCESS, FAILURE
    )

    if task_result.successful():
        # Task completed successfully
        response.result = task_result.result
        # Example result:
        # {
        #   "thumbnail_path": "0245/assets/sots/mayor-interview-thumb.jpg",
        #   "audio_path": "0245/assets/sots/mayor-interview.mp3",
        #   "video_path": "0245/assets/sots/mayor-interview.mp4",
        #   "duration": 30.0,
        #   "status": "completed"
        # }

    elif task_result.failed():
        # Task failed with error
        response.error = str(task_result.info)
        # Example error: "FFmpeg failed: Invalid codec parameters"

    return response
```

#### Step 3: Database Update

**Location:** Frontend after receiving SUCCESS status

```javascript
async function handleSuccess(result) {
  // Update rundown item with asset paths
  await axios.put(`/api/episodes/${episode}/rundown/${slug}`, {
    type: 'SOT',
    duration: result.duration,
    assets: {
      thumbnail: result.thumbnail_path,
      audio: result.audio_path,
      video: result.video_path
    },
    status: 'production'  // Mark as ready for use
  })

  // Update local state
  rundownStore.updateItem(slug, {
    duration: result.duration,
    thumbnail: result.thumbnail_path
  })

  // Show success notification
  showNotification('SOT processed successfully!', 'success')

  // Close modal
  closeModal()
}
```

#### Step 4: Error Handling

```javascript
async function handleError(error) {
  console.error('Processing failed:', error)

  // Determine error type
  let userMessage = 'Processing failed. Please try again.'

  if (error.includes('FFmpeg')) {
    userMessage = 'Video file may be corrupted or unsupported format.'
  } else if (error.includes('timeout')) {
    userMessage = 'Processing timed out. File may be too large.'
  } else if (error.includes('disk full')) {
    userMessage = 'Server storage is full. Contact administrator.'
  }

  // Show error notification
  showNotification(userMessage, 'error')

  // Allow user to retry
  enableRetryButton()
}
```

#### Step 5: Cleanup (Automatic)

**Location:** `app/services/ffmpeg_tasks.py` (line 136-138)

```python
# After successful processing, remove temp file
if os.path.exists(video_path) and "/tmp/" in video_path:
    os.remove(video_path)
    logger.info(f"Removed temp file: {video_path}")
```

**Additional cleanup (cron job on whisper):**

```bash
# /etc/cron.daily/cleanup-temp-uploads
#!/bin/bash
# Remove temp uploads older than 24 hours

find /mnt/sync/temp/uploads -type f -mtime +1 -delete

# Log cleanup
echo "[$(date)] Cleaned temp uploads older than 24 hours" >> /var/log/media-cleanup.log
```

### 4.3 Postprocessing Checklist

After task completion:

- [x] Retrieve result from Redis
- [x] Validate result structure (has required fields)
- [x] Update database with file paths
- [x] Update frontend state (rundown, UI)
- [x] Notify user (success/failure)
- [x] Clean up temp files (automatic in task)
- [x] Handle errors gracefully (show user-friendly message)
- [x] Log completion (for debugging/auditing)

---

## 5. Development Guide

### 5.1 Adding New Media Processing Tasks

**Example: Add "generate subtitles" task**

#### Step 1: Create Task Function

**File:** `app/services/ffmpeg_tasks.py`

```python
@shared_task(bind=True, queue='media', name='services.ffmpeg_tasks.generate_subtitles')
def generate_subtitles(self, video_path: str, episode: str, slug: str, language: str = "en"):
    """
    Generate subtitles using Whisper AI.

    Args:
        video_path: Path to video file
        episode: Episode number
        slug: Output filename base
        language: Language code (en, es, fr, etc.)

    Returns:
        dict: {"subtitles_path": str, "status": str}
    """
    try:
        logger.info(f"Generating subtitles for {video_path}")

        # Create output directory
        episode_dir = Path("/home/episodes") / episode / "assets" / "subtitles"
        episode_dir.mkdir(parents=True, exist_ok=True)

        output_file = episode_dir / f"{slug}.srt"

        # Run Whisper (assuming installed in worker environment)
        cmd = [
            "whisper",
            video_path,
            "--language", language,
            "--output_format", "srt",
            "--output_dir", str(episode_dir)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        logger.info(f"Subtitles created: {output_file}")

        return {
            "subtitles_path": str(output_file.relative_to("/home/episodes")),
            "language": language,
            "status": "completed"
        }

    except Exception as e:
        logger.error(f"Subtitle generation failed: {str(e)}")
        raise
```

#### Step 2: Create API Endpoint

**File:** `app/subtitles_router.py` (new file)

```python
from fastapi import APIRouter, Form, Depends
from celery.result import AsyncResult
from celery_app import celery_app
from services.ffmpeg_tasks import generate_subtitles
from auth.router import get_current_user_or_key

router = APIRouter(prefix="/api/subtitles", tags=["Subtitles"])

@router.post("/generate")
async def generate_subtitles_endpoint(
    video_path: str = Form(...),
    episode: str = Form(...),
    slug: str = Form(...),
    language: str = Form("en"),
    current_user=Depends(get_current_user_or_key)
):
    """Generate subtitles for video."""
    task = generate_subtitles.apply_async(
        args=[video_path, episode, slug, language],
        queue='media'
    )

    return {
        "task_id": task.id,
        "message": "Subtitle generation queued",
        "status": "queued"
    }

@router.get("/tasks/{task_id}/status")
async def get_subtitle_task_status(
    task_id: str,
    current_user=Depends(get_current_user_or_key)
):
    """Check subtitle generation status."""
    task_result = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.successful() else None,
        "error": str(task_result.info) if task_result.failed() else None
    }
```

#### Step 3: Register Router

**File:** `app/main.py`

```python
from subtitles_router import router as subtitles_router

# ... other imports ...

app.include_router(subtitles_router)
```

#### Step 4: Create Frontend Component

**File:** `disaffected-ui/src/components/modals/SubtitlesModal.vue`

```vue
<template>
  <v-dialog v-model="dialog" max-width="500">
    <v-card>
      <v-card-title>Generate Subtitles</v-card-title>

      <v-card-text>
        <v-select
          v-model="language"
          :items="languages"
          label="Language"
        />

        <v-btn @click="generateSubtitles" :loading="processing">
          Generate
        </v-btn>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const dialog = ref(false)
const language = ref('en')
const processing = ref(false)

const languages = [
  { value: 'en', title: 'English' },
  { value: 'es', title: 'Spanish' },
  { value: 'fr', title: 'French' }
]

async function generateSubtitles() {
  processing.value = true

  const { data } = await axios.post('/api/subtitles/generate', {
    video_path: props.videoPath,
    episode: props.episode,
    slug: props.slug,
    language: language.value
  })

  // Poll for completion
  const pollInterval = setInterval(async () => {
    const status = await axios.get(`/api/subtitles/tasks/${data.task_id}/status`)

    if (status.data.status === 'SUCCESS') {
      clearInterval(pollInterval)
      processing.value = false
      emit('success', status.data.result)
      dialog.value = false
    }
  }, 2000)
}
</script>
```

### 5.2 Task Development Best Practices

1. **Always use `@shared_task(bind=True)`** - Enables task methods like `self.retry()`
2. **Set explicit queue** - `queue='media'` routes to correct workers
3. **Use descriptive task names** - `services.ffmpeg_tasks.generate_subtitles`
4. **Log everything** - Use `logger.info()` for debugging
5. **Return structured data** - Always return dict with `status` field
6. **Handle errors gracefully** - Catch exceptions, log details, raise for Celery retry
7. **Clean up temp files** - Delete temp files after processing
8. **Use NFS paths** - Read from `/home/episodes` or `/mnt/sync/temp`

### 5.3 Testing Tasks Locally

```bash
# On kairo (worker machine)

# Enter worker container
docker exec -it kairo-celery bash

# Test task directly (bypasses Celery)
python3 -c "
from services.ffmpeg_tasks import process_sot_video
result = process_sot_video(
    '/mnt/sync/temp/uploads/test.mp4',
    '0245',
    'test-sot',
    '00:00:00',
    '00:00:10'
)
print(result)
"

# Test task via Celery
python3 -c "
from celery_app import celery_app
from services.ffmpeg_tasks import process_sot_video

task = process_sot_video.apply_async(
    args=['/mnt/sync/temp/uploads/test.mp4', '0245', 'test-sot', '00:00:00', '00:00:10'],
    queue='media'
)

print(f'Task ID: {task.id}')
print(f'Status: {task.status}')
print(f'Result: {task.result}')
"
```

---

## 6. Task Types

### 6.1 Current Task Implementations

| Task Name | Queue | Purpose | Processing Time | Dependencies |
|-----------|-------|---------|----------------|--------------|
| `process_sot_video` | media | Extract audio, generate thumbnail, trim video | 15-30s per file | ffmpeg, ffprobe |
| `extract_audio_from_video` | media | Pull audio track from video | 10-20s per file | ffmpeg |
| `generate_thumbnail` | media | Create preview image at timestamp | 2-5s per file | ffmpeg |

### 6.2 Planned Task Implementations

| Task Name | Queue | Purpose | Complexity |
|-----------|-------|---------|------------|
| `generate_subtitles` | media | AI subtitle generation | High (Whisper AI) |
| `normalize_audio` | media | Level audio to -16 LUFS | Medium |
| `convert_video_codec` | media | Transcode to different codec | High (GPU) |
| `generate_waveform` | media | Create audio waveform image | Low |
| `detect_scenes` | media | AI scene detection | High (ML) |
| `stabilize_video` | media | Video stabilization | Very High (GPU) |

### 6.3 Queue Routing Strategy

| Queue | Workers | Use Case | Resource Profile |
|-------|---------|----------|------------------|
| `media` | kairo, proxima | Video/audio processing | High CPU, optional GPU |
| `compilation` | whisper | Script compilation, PDF generation | Low CPU, high memory |
| `quotes` | whisper | Text rendering, image generation | Medium CPU |
| `assets` | whisper | File organization, metadata | Low CPU |

---

## 7. Troubleshooting

### 7.1 Common Issues

#### Issue: "Task stays in PENDING status forever"

**Causes:**
1. Worker not running
2. Worker not subscribed to correct queue
3. Redis connection failed

**Diagnosis:**
```bash
# Check if workers are active
docker exec show-build-server celery -A celery_app inspect active

# Should show workers like: media@kairo

# Check Redis connectivity
redis-cli -h 192.168.51.223 -a showbuild2025 ping
# Should return: PONG

# Check task is in queue
redis-cli -h 192.168.51.223 -a showbuild2025 LLEN media
# Should return number > 0 if task is queued
```

**Solution:**
```bash
# Restart worker
ssh kairo "docker restart kairo-celery"

# Verify worker registered
docker exec show-build-server celery -A celery_app inspect active
```

#### Issue: "FFmpeg command failed"

**Causes:**
1. Input file corrupted
2. Unsupported codec
3. Insufficient disk space

**Diagnosis:**
```bash
# Check file integrity
ffprobe /mnt/sync/temp/uploads/problem-file.mp4

# Check disk space on worker
ssh kairo "df -h /mnt/sync"

# Check worker logs
ssh kairo "docker logs kairo-celery --tail 100"
```

**Solution:**
```bash
# If disk full, clean up
ssh kairo "docker exec kairo-celery rm -rf /tmp/*"

# If codec unsupported, transcode first
ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4
```

#### Issue: "Cannot read input file on worker"

**Causes:**
1. NFS mount not active
2. File saved to local disk instead of NFS
3. Permission issues

**Diagnosis:**
```bash
# Check NFS mount on worker
ssh kairo "mountpoint /mnt/sync"
# Should return: /mnt/sync is a mountpoint

# Check file exists from worker
ssh kairo "ls -la /mnt/sync/temp/uploads/file.mp4"

# Check file permissions
ssh kairo "stat /mnt/sync/temp/uploads/file.mp4"
```

**Solution:**
```bash
# Remount NFS
ssh kairo "sudo umount /mnt/sync && sudo mount -a"

# Fix permissions
ssh whisper "chmod 644 /mnt/sync/temp/uploads/*.mp4"
```

### 7.2 Debugging Workflow

1. **Check task status in Redis**
   ```bash
   redis-cli -h farmhouse -a showbuild2025
   > GET "celery-task-meta-<task-id>"
   ```

2. **Check worker logs**
   ```bash
   ssh kairo "docker logs kairo-celery --tail 200 --follow"
   ```

3. **Check NFS connectivity**
   ```bash
   ssh kairo "ls -la /mnt/sync/disaffected/episodes/"
   ```

4. **Test FFmpeg directly**
   ```bash
   ssh kairo "docker exec kairo-celery ffmpeg -version"
   ```

5. **Manually run task**
   ```bash
   ssh kairo "docker exec kairo-celery python3 -c 'from services.ffmpeg_tasks import process_sot_video; print(process_sot_video(...))'"
   ```

---

## 8. Performance Optimization

### 8.1 FFmpeg Optimization

**Use codec copy when possible:**
```python
# Slow (re-encodes video)
ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4

# Fast (copies streams without re-encoding)
ffmpeg -i input.mp4 -c copy output.mp4
```

**Enable hardware acceleration:**
```python
# NVIDIA GPU encoding (if available)
ffmpeg -hwaccel cuda -i input.mp4 -c:v h264_nvenc output.mp4

# Intel QuickSync
ffmpeg -hwaccel qsv -i input.mp4 -c:v h264_qsv output.mp4
```

**Parallel processing:**
```python
# Use multiple threads (default is 1)
ffmpeg -threads 4 -i input.mp4 output.mp4
```

### 8.2 Celery Optimization

**Increase worker concurrency:**
```yaml
# docker-compose.yml
command: celery -A celery_app worker --concurrency=8
```

**Use task routing:**
```python
# Route CPU-heavy tasks to GPU workers
task.apply_async(args=[...], queue='gpu-workers')
```

**Enable result compression:**
```python
# celery_app.py
app.conf.result_compression = 'gzip'
```

### 8.3 NFS Optimization

**Increase buffer sizes:**
```
# /etc/fstab
whisper:/mnt/sync /mnt/sync nfs rsize=1048576,wsize=1048576 0 0
```

**Use async writes (faster, less safe):**
```
# /etc/exports on whisper
/mnt/sync 192.168.51.0/24(rw,async,no_subtree_check,no_root_squash)
```

---

## Summary

This media processing workflow provides:

✅ **Distributed processing** - Offload CPU-intensive tasks to dedicated workers
✅ **NFS integration** - Shared storage, no file duplication
✅ **Robust error handling** - Retry logic, status polling, user notifications
✅ **Scalable architecture** - Add workers without code changes
✅ **Developer-friendly** - Easy to add new processing tasks
✅ **Production-ready** - Logging, monitoring, cleanup automation

**Next Steps:**
1. Set up NFS (see NFS_INFRASTRUCTURE_UFDP.md)
2. Deploy worker to kairo
3. Test SOT upload workflow
4. Add new task types as needed
