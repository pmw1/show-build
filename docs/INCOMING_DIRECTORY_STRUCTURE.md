# Incoming Directory Structure

**Version:** 1.0
**Last Updated:** January 2025
**Status:** Production Ready

---

## Overview

The `/incoming/` directory serves as a **staging area** for all uploaded media files before processing. Files are organized by type and automatically cleaned up after processing.

**Path:**
- **Linux:** `/mnt/sync/disaffected/incoming/`
- **Windows:** `Z:\incoming\`

---

## Current Structure

```
/mnt/sync/disaffected/incoming/
└── nat/                    ← Natural sound / SOT video clips
    └── [timestamped files, auto-deleted after processing]
```

---

## Design Philosophy

### ✅ **Organic Growth**

New subdirectories are added **as needed** when new media types are introduced:

```
incoming/
├── nat/              ← Video clips (SOT/NATSOT) [IMPLEMENTED]
├── images/           ← When image upload is needed
├── audio/            ← When audio-only uploads are needed
├── graphics/         ← When graphics are uploaded
├── documents/        ← When documents/PDFs are uploaded
└── raw/              ← Catch-all for uncategorized uploads
```

### ✅ **Self-Documenting**

Each subdirectory name indicates what it contains:
- `nat/` → Natural sound video clips (broadcast term)
- `images/` → Image files
- `audio/` → Audio-only files
- etc.

### ✅ **Temporary Storage**

Files in `incoming/` are **ephemeral**:
- Uploaded by backend
- Processed by workers
- **Deleted after processing completes**
- Retention: ~24 hours (automatic cleanup)

---

## Processing Flow

### Example: SOT/NATSOT Video Upload

**1. Upload:**
```
User uploads video
    ↓
Backend saves to: /incoming/nat/0245_interview-clip_20250122_abc123_video.mp4
    ↓
Celery task submitted with this path
```

**2. Processing:**
```
Worker claims task
    ↓
Reads from: /incoming/nat/0245_interview-clip_...
    ↓
Processes (normalize, trim, thumbnails, etc.)
    ↓
Writes outputs to: /episodes/0245/assets/sots/interview-clip.mp4
```

**3. Cleanup:**
```
Processing complete
    ↓
Delete: /incoming/nat/0245_interview-clip_...
    ↓
Incoming file removed (no longer needed)
```

---

## Future Subdirectories (Planned)

### `incoming/images/`
**Purpose:** Guest photos, screenshots, social media images
**Processing:** Image optimization, multiple sizes, watermarking
**Output:** `episodes/{episode}/assets/images/`

**Workflow:**
```python
@shared_task
def process_guest_photo(input_path, episode, guest_name):
    # Read from incoming/images/
    # Resize (1920x1080, 800x800, 400x400)
    # Optimize compression
    # Output to episodes/{episode}/assets/images/guest/{guest_name}.jpg
```

---

### `incoming/audio/`
**Purpose:** Voice samples, music, sound effects
**Processing:** Audio normalization, format conversion
**Output:** `episodes/{episode}/assets/audio/`

**Workflow:**
```python
@shared_task
def process_audio_file(input_path, episode, slug):
    # Read from incoming/audio/
    # Normalize to -23 LUFS
    # Convert to MP3/WAV
    # Output to episodes/{episode}/assets/audio/{slug}.mp3
```

---

### `incoming/graphics/`
**Purpose:** Lower thirds, bumpers, stingers (rendered)
**Processing:** Format validation, optimization
**Output:** `episodes/{episode}/assets/graphics/`

**Workflow:**
```python
@shared_task
def process_graphic(input_path, episode, graphic_type, slug):
    # Read from incoming/graphics/
    # Validate format (PNG with alpha, MOV, MP4)
    # Optimize
    # Output to episodes/{episode}/assets/graphics/{slug}.png
```

---

### `incoming/documents/`
**Purpose:** Scripts, notes, research documents
**Processing:** Format conversion, OCR, text extraction
**Output:** `episodes/{episode}/documents/`

**Workflow:**
```python
@shared_task
def process_document(input_path, episode, doc_type):
    # Read from incoming/documents/
    # Convert PDF → markdown
    # Extract text
    # Output to episodes/{episode}/documents/{doc_type}.md
```

---

### `incoming/raw/`
**Purpose:** Catch-all for unprocessed/uncategorized uploads
**Processing:** Manual review, categorization
**Output:** User manually moves to appropriate subdirectory

---

## Adding New Media Types

### Step-by-Step Process

**1. Create Subdirectory:**
```bash
mkdir -p /mnt/sync/disaffected/incoming/{new_type}
chmod 775 /mnt/sync/disaffected/incoming/{new_type}
```

**2. Create Upload Endpoint:**
```python
# app/{new_type}_router.py
@router.post("/upload")
async def upload_new_type(file: UploadFile, ...):
    media_root = get_media_root()
    upload_dir = media_root / "incoming" / "{new_type}"
    # Save file
    # Submit to Celery
```

**3. Create Processing Task:**
```python
# app/services/{new_type}_tasks.py
@shared_task
def process_new_type(input_path, ...):
    # Read from incoming/{new_type}/
    # Process
    # Output to episodes/{episode}/assets/{new_type}/
    # Delete input file
```

**4. Update Documentation:**
- Add to this file
- Add to CROSS_PLATFORM_WORKERS.md
- Update API documentation

---

## Directory Retention & Cleanup

### Automatic Cleanup (Recommended)

**Celery Beat Task:**
```python
from celery import shared_task
from datetime import datetime, timedelta
from platform_utils import get_media_root

@shared_task
def cleanup_incoming_files():
    """
    Remove files older than 24 hours from incoming/ directories.

    Runs daily at 3 AM via Celery Beat.
    """
    media_root = get_media_root()
    incoming_dir = media_root / "incoming"

    cutoff_time = datetime.now() - timedelta(hours=24)

    for subdir in incoming_dir.iterdir():
        if not subdir.is_dir():
            continue

        for file in subdir.glob("*"):
            if file.is_file():
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                if file_time < cutoff_time:
                    file.unlink()
                    logger.info(f"Cleaned up old upload: {file.name}")
```

**Schedule in celeryconfig.py:**
```python
from celery.schedules import crontab

beat_schedule = {
    'cleanup-incoming-files': {
        'task': 'services.cleanup_tasks.cleanup_incoming_files',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
    }
}
```

---

## Monitoring & Debugging

### Check Current Files

**Linux:**
```bash
# List all incoming files
find /mnt/sync/disaffected/incoming/ -type f -ls

# Check specific type
ls -lah /mnt/sync/disaffected/incoming/nat/

# Count files by age
find /mnt/sync/disaffected/incoming/ -type f -mtime +1 | wc -l  # Older than 24h
```

**Windows:**
```powershell
# List all incoming files
Get-ChildItem Z:\incoming\ -Recurse -File

# Check specific type
dir Z:\incoming\nat\

# Files older than 24 hours
Get-ChildItem Z:\incoming\ -Recurse -File | Where-Object {$_.LastWriteTime -lt (Get-Date).AddHours(-24)}
```

### Disk Space Monitoring

**Alert if incoming/ exceeds threshold:**
```python
@shared_task
def check_incoming_disk_usage():
    """
    Alert if incoming/ directory exceeds 10 GB.
    """
    media_root = get_media_root()
    incoming_dir = media_root / "incoming"

    total_size = sum(f.stat().st_size for f in incoming_dir.rglob('*') if f.is_file())
    total_gb = total_size / (1024**3)

    if total_gb > 10:
        logger.warning(f"⚠️  incoming/ directory is {total_gb:.2f} GB - cleanup may be needed")
```

---

## Troubleshooting

### Files Not Being Cleaned Up

**Symptoms:**
- `incoming/` directory growing large
- Old files accumulating

**Solutions:**
1. Check Celery Beat is running: `celery -A celery_app beat`
2. Verify cleanup task is scheduled: Check `beat_schedule` in celeryconfig.py
3. Manually run cleanup: `cleanup_incoming_files.delay()`

### Permission Issues

**Symptoms:**
```
PermissionError: Cannot write to /mnt/sync/disaffected/incoming/nat/
```

**Solutions:**
```bash
# Fix ownership
sudo chown -R showbuild:showbuild /mnt/sync/disaffected/incoming/

# Fix permissions
chmod -R 775 /mnt/sync/disaffected/incoming/
```

### Worker Can't Access Files

**Symptoms:**
```
FileNotFoundError: /mnt/sync/disaffected/incoming/nat/video.mp4 (Linux)
FileNotFoundError: Z:\incoming\nat\video.mp4 (Windows)
```

**Solutions:**
- **Linux:** Verify `/mnt/sync/disaffected/` is mounted
- **Windows:** Verify `Z:` drive is mapped: `net use Z:`
- Check file exists: `ls /mnt/sync/disaffected/incoming/nat/`

---

## Best Practices

### ✅ Do:
- Use descriptive subdirectory names (nat, images, audio)
- Delete files after successful processing
- Run automatic cleanup daily
- Monitor disk usage
- Create directories with 775 permissions

### ❌ Don't:
- Store permanent files in `incoming/`
- Use `incoming/` as an archive
- Create deeply nested subdirectories
- Store processed outputs in `incoming/`
- Ignore disk space warnings

---

## Summary

**`incoming/` is a temporary staging area:**
- Files land here briefly after upload
- Workers process them
- Outputs go to permanent locations
- Incoming files are deleted
- Structure grows organically as needed

**Current subdirectories:**
- `nat/` - Natural sound video clips (SOT/NATSOT)

**Future subdirectories (add as needed):**
- `images/`, `audio/`, `graphics/`, `documents/`, `raw/`

---

*This directory structure is designed to scale organically as Show-Build evolves.*
