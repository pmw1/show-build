# SOT Distributed Processing System - UFDP

> **📖 About This Document**
>
> This is **comprehensive technical documentation** for the SOT (Sound on Tape) distributed processing system in Show-Build. This document explains how the system works, how to deploy workers to remote servers, and how to troubleshoot common issues.
>
> **If you're looking to:**
> - **Understand the architecture** → See [Section 2: Architecture](#2-architecture)
> - **Deploy a new worker** → See [Section 4: Deployment](#4-deployment)
> - **Use the UI to deploy** → Navigate to **Settings > System > Deployments** in Show-Build
> - **Troubleshoot problems** → See [Section 9: Troubleshooting](#9-troubleshooting)
> - **Integrate with LLM** → See the "LLM Instructions" section in the Deployments UI
>
> This document follows the **Unified Feature Documentation Protocol (UFDP)** - a standardized format for documenting Show-Build features with multilevel indexing, practical examples, and complete reference information.

---

**Unified Feature Documentation Protocol**

## Document Information

- **Feature**: SOT (Sound on Tape) Distributed Processing with Celery
- **Status**: ✅ Deployed and Operational
- **Created**: 2025-10-06
- **Last Updated**: 2025-10-06
- **UI Location**: Settings > System > Deployments
- **Related Documents**:
  - `docs/ASSETID_SYSTEM_GUIDE.md`
  - `IMG_CUE_INSERTION_WORKFLOW_UFDP.md`
  - `FSQ_NESTED_QUOTE_PROCESSING_UFDP.md`
- **Related Files**:
  - `scripts/deploy_celery_worker.sh` - Automated deployment script
  - `disaffected-ui/src/components/settings/DeploymentSettings.vue` - UI component
  - `app/sot_router.py` - SOT API endpoints
  - `app/services/ffmpeg_tasks.py` - FFmpeg processing tasks

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Components](#3-components)
4. [Deployment](#4-deployment)
5. [API Reference](#5-api-reference)
6. [File Reference](#6-file-reference)
7. [Network Configuration](#7-network-configuration)
8. [Maintenance](#8-maintenance)
9. [Troubleshooting](#9-troubleshooting)
10. [Future Enhancements](#10-future-enhancements)

---

## 1. Overview

### 1.1 Purpose

The SOT Distributed Processing System offloads FFmpeg video processing tasks from the main Show-Build server to dedicated worker machines. This prevents resource-intensive video encoding/decoding operations from blocking the main API server.

### 1.2 Key Features

- ✅ Asynchronous video processing via Celery task queue
- ✅ Distributed architecture: server (whisper) → broker (farmhouse) → worker (kairo)
- ✅ Hot-swappable workers (easily migrate from kairo to proxima)
- ✅ Automatic thumbnail generation
- ✅ Audio extraction (MP3)
- ✅ Video trimming support
- ✅ Task status polling API

### 1.3 Design Principles

1. **Frontend-First**: Frontend controls all cue insertion logic; backend handles storage + async processing
2. **Modular Routers**: Keep `main.py` clean by using dedicated router files
3. **Machine Flexibility**: Workers are machine-agnostic and can be deployed anywhere
4. **Queue Isolation**: FFmpeg tasks use dedicated `media` queue to prevent blocking other tasks

---

## 2. Architecture

### 2.1 System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                              │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  WHISPER (192.168.51.210)                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ FastAPI Server (show-build-server)                        │ │
│  │                                                             │ │
│  │  POST /api/sot/upload                                      │ │
│  │    1. Receive video file                                   │ │
│  │    2. Save to /tmp/sot_uploads/                           │ │
│  │    3. Submit task to Celery                               │ │
│  │    4. Return task_id                                       │ │
│  │                                                             │ │
│  │  GET /api/sot/tasks/{task_id}/status                      │ │
│  │    - Poll task status                                      │ │
│  │    - Return results when complete                          │ │
│  └───────────────────────┬───────────────────────────────────┘ │
└──────────────────────────┼─────────────────────────────────────┘
                           │
                           │ Submit Task
                           │ (via celery_app)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  FARMHOUSE (192.168.51.223)                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Redis 7 Message Broker                                    │ │
│  │                                                             │ │
│  │  Port: 6379 (password: showbuild2025)                     │ │
│  │  Database: 0                                               │ │
│  │                                                             │ │
│  │  Queues:                                                   │ │
│  │    - media (FFmpeg tasks) → kairo                         │ │
│  │    - compilation (script tasks)                           │ │
│  │    - quotes (extraction tasks)                            │ │
│  │    - assets (asset processing)                            │ │
│  └───────────────────────┬───────────────────────────────────┘ │
└──────────────────────────┼─────────────────────────────────────┘
                           │
                           │ Worker polls queue
                           │ (BLPOP media queue)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  KAIRO (192.168.51.197)                                         │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Celery Worker (kairo-celery)                              │ │
│  │                                                             │ │
│  │  Queue: media                                              │ │
│  │  Concurrency: 4 prefork workers                           │ │
│  │  Hostname: media@kairo                                     │ │
│  │                                                             │ │
│  │  Tasks:                                                    │ │
│  │    - services.ffmpeg_tasks.process_sot_video              │ │
│  │    - services.ffmpeg_tasks.extract_audio_from_video       │ │
│  │    - services.ffmpeg_tasks.generate_thumbnail             │ │
│  │                                                             │ │
│  │  FFmpeg Operations:                                        │ │
│  │    1. Extract duration (ffprobe)                          │ │
│  │    2. Generate thumbnail @ 1s (JPG)                       │ │
│  │    3. Extract audio (MP3, 192kbps)                        │ │
│  │    4. Trim/copy video (MP4)                               │ │
│  │    5. Return paths to assets                              │ │
│  └───────────────────────┬───────────────────────────────────┘ │
└──────────────────────────┼─────────────────────────────────────┘
                           │
                           │ Store results in Redis
                           │ (task_id → result dict)
                           ▼
                     ┌──────────────┐
                     │   COMPLETE   │
                     └──────────────┘
```

### 2.2 Data Flow

1. **Upload Phase**:
   ```
   User → FastAPI → /tmp/sot_uploads/{episode}_{slug}_{filename}
   FastAPI → Celery → Submit task(video_path, episode, slug, trim_start, trim_end)
   FastAPI → User → {"task_id": "abc-123", "status": "queued"}
   ```

2. **Processing Phase**:
   ```
   Redis → Kairo Worker → Receive task from media queue
   Kairo → FFmpeg → Extract duration (ffprobe)
   Kairo → FFmpeg → Generate thumbnail (1s mark)
   Kairo → FFmpeg → Extract audio (MP3)
   Kairo → FFmpeg → Process video (trim if needed)
   Kairo → Filesystem → Save to /home/episodes/{episode}/assets/sots/
   Kairo → Redis → Store result {"thumbnail_path": "...", "audio_path": "...", ...}
   Kairo → /tmp → Delete temp upload file
   ```

3. **Polling Phase**:
   ```
   User → FastAPI → GET /api/sot/tasks/{task_id}/status
   FastAPI → Redis → Check task status (PENDING/STARTED/SUCCESS/FAILURE)
   Redis → FastAPI → Return result if SUCCESS
   FastAPI → User → {"status": "SUCCESS", "result": {...}}
   ```

### 2.3 Task Routing

Celery routes tasks based on function module:

| Task Pattern | Queue | Worker | Purpose |
|--------------|-------|--------|---------|
| `services.ffmpeg_tasks.*` | `media` | kairo | Video/audio processing |
| `services.script_compilation.*` | `compilation` | (future) | Script rendering |
| `services.quote_extraction.*` | `quotes` | (future) | Quote extraction |
| `services.asset_processing.*` | `assets` | (future) | Asset optimization |

**Configured in**: `/mnt/process/show-build/app/celery_app.py:32-38`

---

## 3. Components

### 3.1 Machine Roles

#### 3.1.1 Whisper (192.168.51.210)

**Role**: FastAPI Server + Task Dispatcher

**Services**:
- `show-build-server` (Docker container)
- FastAPI application (port 8888)
- Celery client (task submission only, no worker)

**Responsibilities**:
- Accept SOT video uploads
- Save files to temporary storage
- Submit tasks to Redis queue
- Provide task status API
- Return processing results

**Docker Compose**: `/mnt/process/show-build/docker-compose.yml`

#### 3.1.2 Farmhouse (192.168.51.223)

**Role**: Message Broker

**Services**:
- `farmhouse-redis` (Docker container)
- Redis 7 Alpine

**Configuration**:
- Port: `6379`
- Password: `showbuild2025`
- Persistence: AOF (append-only file) enabled
- Save policy: Every 60s if 1000+ keys changed

**Docker Compose**: `/home/kevin/show-build-redis/docker-compose.yml`

**Data Persistence**: `/var/lib/docker/volumes/show-build-redis_redis_data/_data`

#### 3.1.3 Kairo (192.168.51.197)

**Role**: FFmpeg Worker

**Services**:
- `kairo-celery` (Docker container)
- Celery 5.5.3 worker
- FFmpeg (installed in container)

**Configuration**:
- Worker name: `media@kairo`
- Queue: `media`
- Concurrency: 4 (prefork)
- Hostname: `media@kairo`

**Docker Compose**: `/home/kairo/show-build-worker/docker-compose.yml`

**Mounted Volumes**:
- `/mnt/sync/disaffected/episodes:/home/episodes` (episode storage)
- `/mnt/sync/shared_media:/shared_media` (media library)

### 3.2 Software Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11 | Runtime environment |
| FastAPI | 0.100.0+ | Web framework |
| Celery | 5.5.3 | Distributed task queue |
| Redis | 7-alpine | Message broker + result backend |
| FFmpeg | Latest | Video/audio processing |
| Uvicorn | 0.22.0+ | ASGI server |

---

## 4. Deployment

### 4.1 Initial Deployment Checklist

- [x] Deploy Redis on farmhouse
- [x] Deploy Celery worker on kairo
- [x] Create `ffmpeg_tasks.py` service file
- [x] Create `sot_router.py` API module
- [x] Update `celery_app.py` with ffmpeg_tasks
- [x] Update `main.py` to include sot_router
- [x] Add REDIS_URL to docker-compose.yml
- [x] Rebuild server container
- [x] Verify worker registration
- [ ] Configure firewall rules (manual, requires sudo)

### 4.2 Farmhouse Deployment

**Location**: `farmhouse:~/show-build-redis/`

**Files**:

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    container_name: farmhouse-redis
    ports:
      - "0.0.0.0:6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --requirepass "showbuild2025" --appendonly yes --save 60 1000
    restart: unless-stopped
volumes:
  redis_data:
```

**Deployment Commands**:

```bash
# SSH to farmhouse
ssh farmhouse

# Create directory
mkdir -p ~/show-build-redis
cd ~/show-build-redis

# Create docker-compose.yml (use content above)

# Start Redis
docker compose up -d

# Verify
redis-cli -h 127.0.0.1 -a showbuild2025 ping
# Expected: PONG
```

**Health Check**:

```bash
docker logs farmhouse-redis --tail 20
docker ps | grep farmhouse-redis
```

### 4.3 Kairo Deployment

**Location**: `kairo:~/show-build-worker/`

**Files**:

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app /app

# Run Celery worker
CMD ["celery", "-A", "celery_app.celery_app", "worker", "--loglevel=info"]
```

```txt
# requirements.txt
# Celery and Redis
celery[redis]>=5.3.0
redis>=5.0.0

# Database (needed for tasks that access DB)
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9

# Media processing
ffmpeg-python>=0.2.0

# Content processing
python-frontmatter>=1.0.0
markdown>=3.4.3
pydantic>=2.0.3
pydantic-settings>=2.0.3
```

```yaml
# docker-compose.yml
services:
  celery-media:
    build: .
    container_name: kairo-celery
    command: celery -A celery_app worker -Q media --hostname=media@kairo --concurrency=4
    volumes:
      - /mnt/sync/disaffected/episodes:/home/episodes
      - /mnt/sync/shared_media:/shared_media
    environment:
      - REDIS_URL=redis://:showbuild2025@192.168.51.223:6379/0
    restart: unless-stopped
```

**Deployment Commands**:

```bash
# SSH to kairo
ssh kairo

# Create directory
mkdir -p ~/show-build-worker
cd ~/show-build-worker

# Create Dockerfile, requirements.txt, docker-compose.yml (use content above)

# Copy app code from whisper
# (From whisper machine)
scp -r /mnt/process/show-build/app kairo:~/show-build-worker/

# Back on kairo - build and start
docker compose up -d --build

# Verify
docker logs kairo-celery --tail 50
```

**Health Check**:

```bash
# Check container status
docker ps | grep kairo-celery

# Check worker logs
docker logs kairo-celery --tail 30 | grep "media@kairo ready"

# Expected output:
# [2025-10-06 07:02:10,502: INFO/MainProcess] media@kairo ready.
```

### 4.4 Whisper Updates

**Files Modified**:

1. `/mnt/process/show-build/app/services/ffmpeg_tasks.py` - **NEW**
2. `/mnt/process/show-build/app/sot_router.py` - **NEW**
3. `/mnt/process/show-build/app/celery_app.py` - **UPDATED**
4. `/mnt/process/show-build/app/main.py` - **UPDATED**
5. `/mnt/process/show-build/docker-compose.yml` - **UPDATED**

**Deployment Commands**:

```bash
# Already deployed - for reference only
cd /mnt/process/show-build
docker compose up -d --build server
```

**Verification**:

```bash
# Check server logs
docker logs show-build-server --tail 30 | grep "Application startup complete"

# Test Redis connectivity
docker exec show-build-server python -c "
import redis, os
r = redis.from_url(os.getenv('REDIS_URL'))
print('Redis PING:', r.ping())
"

# Check registered workers
docker exec show-build-server python -c "
from celery_app import celery_app
inspect = celery_app.control.inspect()
print('Workers:', list(inspect.stats().keys()) if inspect.stats() else 'None')
"
```

### 4.5 Firewall Configuration (Manual)

**⚠️ PENDING - Requires sudo access on farmhouse**

```bash
# SSH to farmhouse
ssh farmhouse

# Allow whisper to access Redis
sudo ufw allow from 192.168.51.210 to any port 6379 comment "whisper"

# Allow kairo to access Redis
sudo ufw allow from 192.168.51.197 to any port 6379 comment "kairo"

# Check rules
sudo ufw status numbered
```

**Alternative**: If UFW is not enabled, configure iptables:

```bash
sudo iptables -A INPUT -p tcp -s 192.168.51.210 --dport 6379 -j ACCEPT -m comment --comment "whisper"
sudo iptables -A INPUT -p tcp -s 192.168.51.197 --dport 6379 -j ACCEPT -m comment --comment "kairo"
```

---

## 5. API Reference

### 5.1 Upload SOT Video

**Endpoint**: `POST /api/sot/upload`

**Authentication**: Required (JWT token or API key)

**Request**:

```http
POST /api/sot/upload HTTP/1.1
Host: 192.168.51.210:8888
Content-Type: multipart/form-data
Authorization: Bearer <token>

--boundary
Content-Disposition: form-data; name="file"; filename="interview.mp4"
Content-Type: video/mp4

<binary video data>
--boundary
Content-Disposition: form-data; name="episode"

0245
--boundary
Content-Disposition: form-data; name="slug"

mayor-interview
--boundary
Content-Disposition: form-data; name="trim_start"

00:00:05
--boundary
Content-Disposition: form-data; name="trim_end"

00:02:30
--boundary--
```

**Parameters**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | File | ✅ Yes | - | Video file (must be video/* MIME type) |
| `episode` | String | ✅ Yes | - | Episode number (e.g., "0245") |
| `slug` | String | ✅ Yes | - | Item slug for output filenames |
| `trim_start` | String | ❌ No | "00:00:00" | Start time for trimming (HH:MM:SS) |
| `trim_end` | String | ❌ No | "00:00:00" | End time for trimming (HH:MM:SS) |

**Response** (200 OK):

```json
{
  "task_id": "abc123-def456-ghi789",
  "message": "SOT video queued for processing on media worker",
  "status": "queued"
}
```

**Error Responses**:

- **400 Bad Request**: File is not a video
- **500 Internal Server Error**: Upload failed

**Example (curl)**:

```bash
curl -X POST http://192.168.51.210:8888/api/sot/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/video.mp4" \
  -F "episode=0245" \
  -F "slug=mayor-interview" \
  -F "trim_start=00:00:05" \
  -F "trim_end=00:02:30"
```

**Example (JavaScript)**:

```javascript
const formData = new FormData();
formData.append('file', videoFile);
formData.append('episode', '0245');
formData.append('slug', 'mayor-interview');
formData.append('trim_start', '00:00:05');
formData.append('trim_end', '00:02:30');

const response = await fetch('http://192.168.51.210:8888/api/sot/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const result = await response.json();
console.log('Task ID:', result.task_id);
```

### 5.2 Check Task Status

**Endpoint**: `GET /api/sot/tasks/{task_id}/status`

**Authentication**: Required (JWT token or API key)

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | String | ✅ Yes | Task ID returned from upload endpoint |

**Response** (200 OK):

```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "SUCCESS",
  "result": {
    "thumbnail_path": "0245/assets/sots/mayor-interview-thumb.jpg",
    "audio_path": "0245/assets/sots/mayor-interview.mp3",
    "video_path": "0245/assets/sots/mayor-interview.mp4",
    "duration": 145.5,
    "status": "completed"
  },
  "error": null
}
```

**Status Values**:

| Status | Description |
|--------|-------------|
| `PENDING` | Task queued, not yet started |
| `STARTED` | Worker is processing the task |
| `SUCCESS` | Task completed successfully |
| `FAILURE` | Task failed with error |
| `RETRY` | Task failed and is being retried |
| `REVOKED` | Task was cancelled |

**Example (curl)**:

```bash
curl -X GET http://192.168.51.210:8888/api/sot/tasks/abc123-def456-ghi789/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example (JavaScript with polling)**:

```javascript
async function pollTaskStatus(taskId, intervalMs = 2000, maxAttempts = 60) {
  for (let i = 0; i < maxAttempts; i++) {
    const response = await fetch(
      `http://192.168.51.210:8888/api/sot/tasks/${taskId}/status`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );

    const result = await response.json();

    if (result.status === 'SUCCESS') {
      return result.result;
    } else if (result.status === 'FAILURE') {
      throw new Error(result.error);
    }

    // Wait before next poll
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }

  throw new Error('Task timeout');
}

// Usage
const taskResult = await pollTaskStatus('abc123-def456-ghi789');
console.log('Thumbnail:', taskResult.thumbnail_path);
console.log('Audio:', taskResult.audio_path);
console.log('Video:', taskResult.video_path);
```

### 5.3 Cancel Task

**Endpoint**: `DELETE /api/sot/tasks/{task_id}`

**Authentication**: Required (JWT token or API key)

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | String | ✅ Yes | Task ID to cancel |

**Response** (200 OK):

```json
{
  "message": "Task abc123-def456-ghi789 cancelled",
  "status": "cancelled"
}
```

**Example (curl)**:

```bash
curl -X DELETE http://192.168.51.210:8888/api/sot/tasks/abc123-def456-ghi789 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 6. File Reference

### 6.1 Backend Files

#### 6.1.1 `/mnt/process/show-build/app/services/ffmpeg_tasks.py`

**Purpose**: Celery tasks for FFmpeg video/audio processing

**Key Functions**:

```python
@shared_task(bind=True, queue='media')
def process_sot_video(
    self,
    video_path: str,
    episode: str,
    slug: str,
    trim_start: str = "00:00:00",
    trim_end: str = "00:00:00"
) -> dict
```

**Returns**:
```python
{
    "thumbnail_path": "0245/assets/sots/slug-thumb.jpg",
    "audio_path": "0245/assets/sots/slug.mp3",
    "video_path": "0245/assets/sots/slug.mp4",
    "duration": 145.5,
    "status": "completed"
}
```

**Processing Steps**:
1. Extract duration using `ffprobe`
2. Generate thumbnail at 1 second mark (JPG, quality=2)
3. Extract audio as MP3 (192kbps)
4. Trim/copy video (codec copy for speed)
5. Clean up temp files
6. Return asset paths

**Line Count**: ~200 lines

**Dependencies**: `subprocess`, `pathlib`, `celery`, `os`

#### 6.1.2 `/mnt/process/show-build/app/sot_router.py`

**Purpose**: FastAPI router for SOT upload/status endpoints

**Key Routes**:

```python
router = APIRouter(prefix="/api/sot", tags=["SOT Processing"])

@router.post("/upload", response_model=SOTUploadResponse)
async def upload_sot_video(...)

@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(...)

@router.delete("/tasks/{task_id}")
async def cancel_task(...)
```

**Line Count**: ~140 lines

**Dependencies**: `fastapi`, `pydantic`, `celery.result`, `pathlib`, `shutil`

**Temp Storage**: `/tmp/sot_uploads/`

#### 6.1.3 `/mnt/process/show-build/app/celery_app.py`

**Purpose**: Celery application configuration

**Key Configuration**:

```python
REDIS_URL = os.getenv("REDIS_URL", "redis://:showbuild2025@192.168.51.223:6379/0")

celery_app = Celery(
    "showbuild",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "services.script_compilation",
        "services.quote_extraction",
        "services.asset_processing",
        "services.ffmpeg_tasks"  # ← Added for SOT processing
    ]
)

task_routes={
    "services.script_compilation.*": {"queue": "compilation"},
    "services.quote_extraction.*": {"queue": "quotes"},
    "services.asset_processing.*": {"queue": "assets"},
    "services.ffmpeg_tasks.*": {"queue": "media"},  # ← Routes to kairo
}
```

**Changes Made**:
- Line 9: Updated `REDIS_URL` default to farmhouse
- Line 20: Added `"services.ffmpeg_tasks"` to includes
- Line 37: Added media queue routing

#### 6.1.4 `/mnt/process/show-build/app/main.py`

**Purpose**: FastAPI application entry point

**Changes Made**:

```python
# Line 76: Import sot_router
from sot_router import router as sot_router

# Line 179: Include sot_router
app.include_router(sot_router)
```

**Total Lines**: ~800 lines (2 lines added)

#### 6.1.5 `/mnt/process/show-build/docker-compose.yml`

**Purpose**: Docker Compose configuration for server

**Changes Made**:

```yaml
# Line 26: Added REDIS_URL environment variable
environment:
  - REDIS_URL=redis://:showbuild2025@192.168.51.223:6379/0
```

**Total Lines**: ~105 lines (1 line added)

### 6.2 Remote Machine Files

#### 6.2.1 Farmhouse: `~/show-build-redis/docker-compose.yml`

**Purpose**: Redis broker deployment

**Full Content**: See [Section 4.2](#42-farmhouse-deployment)

**Location**: `farmhouse:/home/kevin/show-build-redis/docker-compose.yml`

#### 6.2.2 Kairo: `~/show-build-worker/`

**Directory Structure**:

```
/home/kairo/show-build-worker/
├── docker-compose.yml       # Worker service definition
├── Dockerfile               # Worker image build
├── requirements.txt         # Python dependencies
└── app/                     # Copied from whisper
    ├── celery_app.py
    ├── database.py
    ├── core/
    ├── services/
    │   ├── ffmpeg_tasks.py  # Main processing logic
    │   ├── asset_processing.py
    │   ├── quote_extraction.py
    │   └── script_compilation.py
    └── ...
```

**Files**: See [Section 4.3](#43-kairo-deployment)

**Location**: `kairo:/home/kairo/show-build-worker/`

**Sync Command** (when updating code):

```bash
# From whisper
scp -r /mnt/process/show-build/app kairo:~/show-build-worker/

# Restart worker
ssh kairo "cd ~/show-build-worker && docker compose restart"
```

---

## 7. Network Configuration

### 7.1 IP Addresses

| Machine | IP Address | Hostname | Purpose |
|---------|------------|----------|---------|
| Whisper | 192.168.51.210 | whisper | FastAPI server |
| Farmhouse | 192.168.51.223 | farmhouse | Redis broker |
| Kairo | 192.168.51.197 | kairo | FFmpeg worker |

### 7.2 Port Mappings

| Machine | Service | Internal Port | External Port | Protocol |
|---------|---------|---------------|---------------|----------|
| Whisper | FastAPI | 80 | 8888 | HTTP |
| Whisper | PostgreSQL | 5432 | 5433 | TCP |
| Farmhouse | Redis | 6379 | 6379 | TCP |
| Kairo | Celery Worker | N/A | N/A | N/A |

### 7.3 SSH Configuration

**Location**: `/home/kevin/.ssh/config`

```ssh-config
Host whisper
    Hostname 192.168.51.210
    User kevin
    IdentityFile ~/.ssh/id_ed25519
    ForwardAgent yes

Host farmhouse
    Hostname 192.168.51.223
    User kevin
    IdentityFile ~/.ssh/id_ed25519
    ForwardAgent yes

Host kairo
    Hostname 192.168.51.197
    User kairo
    IdentityFile ~/.ssh/id_ed25519
    ForwardAgent yes
```

**Usage**:

```bash
ssh whisper
ssh farmhouse
ssh kairo
```

### 7.4 Firewall Rules (Pending)

**Source**: whisper (192.168.51.210)
**Destination**: farmhouse (192.168.51.223)
**Port**: 6379 (Redis)
**Protocol**: TCP

**Source**: kairo (192.168.51.197)
**Destination**: farmhouse (192.168.51.223)
**Port**: 6379 (Redis)
**Protocol**: TCP

**Implementation**: See [Section 4.5](#45-firewall-configuration-manual)

---

## 8. Maintenance

### 8.1 Updating Worker Code

When you modify task files on whisper, sync to kairo:

```bash
# From whisper
cd /mnt/process/show-build

# Copy updated app code
scp -r app kairo:~/show-build-worker/

# Restart kairo worker
ssh kairo "cd ~/show-build-worker && docker compose restart"

# Verify new tasks are registered (from whisper)
docker exec show-build-server python -c "
from celery_app import celery_app
inspect = celery_app.control.inspect()
tasks = inspect.registered()
if tasks:
    for worker, task_list in tasks.items():
        print(f'{worker}:')
        for task in sorted(task_list):
            print(f'  - {task}')
"
```

### 8.2 Migrating to New Worker (Kairo → Proxima)

**Step 1**: Deploy worker on proxima

```bash
# SSH to proxima
ssh proxima

# Create directory
mkdir -p ~/show-build-worker
cd ~/show-build-worker

# Copy files from kairo
scp -r kairo:~/show-build-worker/* .

# Update docker-compose.yml hostname
sed -i 's/media@kairo/media@proxima/g' docker-compose.yml

# Start worker
docker compose up -d --build
```

**Step 2**: Verify registration

```bash
# From whisper
docker exec show-build-server python -c "
from celery_app import celery_app
inspect = celery_app.control.inspect()
print('Active workers:', list(inspect.stats().keys()))
"
```

**Step 3**: Shut down kairo worker

```bash
ssh kairo "cd ~/show-build-worker && docker compose down"
```

**Result**: Tasks now route to `media@proxima` instead of `media@kairo`

### 8.3 Monitoring

#### 8.3.1 Check Redis Status

```bash
ssh farmhouse

# Connect to Redis
redis-cli -h 127.0.0.1 -a showbuild2025

# Check queue lengths
LLEN media
LLEN compilation
LLEN quotes
LLEN assets

# Check connected clients
CLIENT LIST

# Exit
exit
```

#### 8.3.2 Check Worker Status

```bash
ssh kairo

# Check worker logs
docker logs kairo-celery --tail 50 -f

# Check container status
docker ps | grep kairo-celery

# Check resource usage
docker stats kairo-celery --no-stream
```

#### 8.3.3 Check Active Tasks

```bash
# From whisper
docker exec show-build-server python -c "
from celery_app import celery_app

inspect = celery_app.control.inspect()

# Active tasks (currently executing)
active = inspect.active()
if active:
    for worker, tasks in active.items():
        print(f'{worker}: {len(tasks)} active tasks')

# Scheduled tasks (waiting)
scheduled = inspect.scheduled()
if scheduled:
    for worker, tasks in scheduled.items():
        print(f'{worker}: {len(tasks)} scheduled tasks')

# Reserved tasks (claimed but not started)
reserved = inspect.reserved()
if reserved:
    for worker, tasks in reserved.items():
        print(f'{worker}: {len(tasks)} reserved tasks')
"
```

### 8.4 Clearing Failed Tasks

```bash
# From whisper
docker exec show-build-server python -c "
from celery_app import celery_app

# Purge all tasks from media queue
celery_app.control.purge()

# Or purge specific queue
from kombu import Queue
queue = Queue('media')
queue(celery_app.connection()).purge()
"
```

### 8.5 Backup and Restore

#### Redis Data Backup

```bash
ssh farmhouse

# Create backup
docker exec farmhouse-redis redis-cli -a showbuild2025 SAVE

# Backup location (in Docker volume)
docker exec farmhouse-redis ls -lh /data/dump.rdb

# Copy backup to host
docker cp farmhouse-redis:/data/dump.rdb ~/redis-backup-$(date +%Y%m%d).rdb
```

#### Redis Data Restore

```bash
ssh farmhouse

# Stop Redis
docker compose -f ~/show-build-redis/docker-compose.yml down

# Restore backup file
docker run --rm -v show-build-redis_redis_data:/data -v ~/:/backup \
  redis:7-alpine cp /backup/redis-backup-20251006.rdb /data/dump.rdb

# Start Redis
docker compose -f ~/show-build-redis/docker-compose.yml up -d
```

---

## 9. Troubleshooting

### 9.1 Worker Not Registering

**Symptom**: `celery_app.control.inspect().stats()` returns `None` or doesn't show `media@kairo`

**Diagnosis**:

```bash
# Check Redis connectivity from kairo
ssh kairo
docker exec kairo-celery python -c "
import redis
r = redis.from_url('redis://:showbuild2025@192.168.51.223:6379/0')
print('PING:', r.ping())
"

# Expected: PING: True
```

**Common Causes**:

1. **Redis not accessible**:
   - Check firewall rules (see [Section 4.5](#45-firewall-configuration-manual))
   - Verify REDIS_URL in docker-compose.yml

2. **Worker crashed on startup**:
   ```bash
   ssh kairo
   docker logs kairo-celery --tail 100 | grep -i error
   ```

3. **Wrong queue name**:
   - Verify `command:` in docker-compose.yml uses `-Q media`
   - Check `task_routes` in celery_app.py

**Solution**:

```bash
# Restart worker with debug logging
ssh kairo
docker compose -f ~/show-build-worker/docker-compose.yml down
docker compose -f ~/show-build-worker/docker-compose.yml up -d

# Watch logs
docker logs kairo-celery -f
```

### 9.2 Tasks Stay in PENDING

**Symptom**: Task status never changes from PENDING

**Diagnosis**:

```bash
# Check if worker is consuming tasks
docker exec show-build-server python -c "
from celery_app import celery_app
inspect = celery_app.control.inspect()
active = inspect.active()
print('Active tasks:', active)
"
```

**Common Causes**:

1. **Worker not running**:
   ```bash
   ssh kairo
   docker ps | grep kairo-celery
   ```

2. **Task routing issue**:
   - Verify task is routed to `media` queue
   - Check `task_routes` in celery_app.py:37

3. **Worker crashed during processing**:
   ```bash
   docker logs kairo-celery --tail 100
   ```

**Solution**:

```bash
# Restart worker
ssh kairo
docker compose restart

# Resubmit task from whisper
```

### 9.3 FFmpeg Errors

**Symptom**: Task fails with FFmpeg-related errors

**Diagnosis**:

```bash
# Check worker logs for FFmpeg stderr
ssh kairo
docker logs kairo-celery | grep -A 10 "ffmpeg"
```

**Common Errors**:

1. **"ffmpeg: command not found"**:
   - FFmpeg not installed in container
   - Check Dockerfile line 5: `RUN apt-get install -y ffmpeg`

2. **"Invalid codec name"**:
   - Unsupported codec in source video
   - Try re-encoding input video

3. **"Permission denied"**:
   - Check mounted volume permissions
   - Ensure `/mnt/sync/disaffected/episodes` is writable

**Solution**:

```bash
# Rebuild worker with FFmpeg
ssh kairo
cd ~/show-build-worker
docker compose down
docker compose up -d --build
```

### 9.4 Redis Connection Timeouts

**Symptom**: `redis.exceptions.TimeoutError` or `ConnectionError`

**Diagnosis**:

```bash
# Test Redis from whisper
docker exec show-build-server python -c "
import redis, time
r = redis.from_url('redis://:showbuild2025@192.168.51.223:6379/0')
start = time.time()
r.ping()
print(f'Latency: {(time.time() - start) * 1000:.2f}ms')
"
```

**Common Causes**:

1. **Network latency**:
   - Check network connectivity: `ping 192.168.51.223`
   - Verify Redis is listening on correct interface

2. **Redis overloaded**:
   ```bash
   ssh farmhouse
   redis-cli -a showbuild2025 INFO stats | grep instantaneous_ops
   ```

3. **Firewall blocking connection**:
   - Verify firewall rules (see [Section 4.5](#45-firewall-configuration-manual))

**Solution**:

```bash
# Increase timeout in celery_app.py
celery_app.conf.update(
    broker_connection_timeout=30,  # seconds
    broker_connection_retry_on_startup=True
)
```

### 9.5 Task Results Not Persisting

**Symptom**: Task completes but result is `None` when polling

**Diagnosis**:

```bash
# Check Redis for result
ssh farmhouse
redis-cli -a showbuild2025
> KEYS celery-task-meta-*
> GET celery-task-meta-<task-id>
```

**Common Causes**:

1. **Result backend not configured**:
   - Verify `backend=REDIS_URL` in celery_app.py:15

2. **Result expired**:
   - Check `result_expires` in celery_app.py:40 (default: 3600s)

3. **Redis persistence disabled**:
   - Verify AOF enabled in farmhouse docker-compose.yml

**Solution**:

```bash
# Increase result expiration time
celery_app.conf.update(
    result_expires=7200  # 2 hours
)
```

---

## 10. Future Enhancements

### 10.1 Planned Features

- [ ] **Web-based Monitoring Dashboard**
  - Flower UI for Celery (port 5555)
  - Real-time task progress tracking
  - Worker health metrics

- [ ] **Multiple Worker Types**
  - Dedicated workers for compilation, quotes, assets queues
  - Auto-scaling based on queue depth

- [ ] **Enhanced Error Handling**
  - Automatic retry with exponential backoff
  - Dead-letter queue for failed tasks
  - Email/Slack notifications on failure

- [ ] **Performance Optimizations**
  - Redis Sentinel for high availability
  - Worker prefetch tuning based on task duration
  - GPU-accelerated FFmpeg encoding

- [ ] **Security Enhancements**
  - TLS/SSL for Redis connections
  - Task result encryption
  - Network isolation with Docker networks

### 10.2 Migration Roadmap

**Phase 1**: Current State ✅
- Single worker (kairo) on media queue
- Basic task routing
- Manual deployment

**Phase 2**: Multi-Worker (Q1 2026)
- Deploy proxima for compilation queue
- Deploy additional worker for quotes queue
- Load balancing across workers

**Phase 3**: High Availability (Q2 2026)
- Redis Sentinel cluster (3 nodes)
- Worker auto-scaling
- Health checks and auto-restart

**Phase 4**: Production Hardening (Q3 2026)
- Monitoring and alerting
- Automated backups
- Disaster recovery procedures

### 10.3 Code Improvements

**Priority 1**: Add comprehensive tests
```python
# tests/test_ffmpeg_tasks.py
def test_process_sot_video():
    result = process_sot_video.apply(
        args=["test.mp4", "9999", "test-slug"]
    ).get()
    assert "thumbnail_path" in result
    assert "audio_path" in result
```

**Priority 2**: Add task progress reporting
```python
@shared_task(bind=True)
def process_sot_video(self, ...):
    self.update_state(state='PROGRESS', meta={'percent': 25})
    # ... generate thumbnail
    self.update_state(state='PROGRESS', meta={'percent': 50})
    # ... extract audio
```

**Priority 3**: Add input validation
```python
# Validate video codec before processing
def validate_video_file(path: str) -> bool:
    probe = ffmpeg.probe(path)
    codec = probe['streams'][0]['codec_name']
    return codec in ['h264', 'hevc', 'vp9']
```

---

## Appendix A: Quick Reference Commands

### Start/Stop Services

```bash
# Farmhouse (Redis)
ssh farmhouse
cd ~/show-build-redis
docker compose up -d        # Start
docker compose down         # Stop
docker compose restart      # Restart

# Kairo (Worker)
ssh kairo
cd ~/show-build-worker
docker compose up -d        # Start
docker compose down         # Stop
docker compose restart      # Restart

# Whisper (Server)
cd /mnt/process/show-build
docker compose up -d server         # Start
docker compose down server          # Stop
docker compose restart server       # Restart
```

### View Logs

```bash
# Farmhouse
ssh farmhouse && docker logs farmhouse-redis -f

# Kairo
ssh kairo && docker logs kairo-celery -f

# Whisper
docker logs show-build-server -f
```

### Check System Health

```bash
# All-in-one health check (run from whisper)
docker exec show-build-server python -c "
import redis, os
from celery_app import celery_app

# Redis
r = redis.from_url(os.getenv('REDIS_URL'))
print('✅ Redis:', 'OK' if r.ping() else 'FAIL')

# Workers
inspect = celery_app.control.inspect()
stats = inspect.stats()
print('✅ Workers:', list(stats.keys()) if stats else 'None')

# Tasks
registered = inspect.registered()
if registered:
    for worker, tasks in registered.items():
        ffmpeg_tasks = [t for t in tasks if 'ffmpeg' in t]
        print(f'✅ FFmpeg tasks on {worker}:', len(ffmpeg_tasks))
"
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **SOT** | Sound on Tape - Video interview or footage cue |
| **Celery** | Distributed task queue for Python |
| **Redis** | In-memory data store used as message broker |
| **Worker** | Celery process that executes tasks |
| **Broker** | Message queue that distributes tasks to workers |
| **Task** | Unit of work submitted to Celery |
| **Queue** | Named channel for routing tasks to specific workers |
| **Prefork** | Worker concurrency model using multiple processes |
| **AOF** | Append-Only File - Redis persistence mechanism |
| **BLPOP** | Blocking List Pop - Redis command for queue consumption |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-06 | Claude (Sonnet 4.5) | Initial deployment documentation |

---

**END OF DOCUMENT**
