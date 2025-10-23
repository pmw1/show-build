# Windows Worker Deployment Instructions

## Critical SQLAlchemy Fix Applied

**Issue:** Windows Celery worker crashes with `'Speaker' failed to locate a name` error.

**Fix:** Speaker model consolidated into `models_v2.py` to eliminate circular import dependencies.

---

## Manual Deployment (Required NOW)

**GitHub has secret scanning block - cannot push. Deploy manually using one of these methods:**

### Method 1: Git Pull (Recommended)

On Windows PowerShell:
```powershell
cd J:\show-build
git fetch origin
git reset --hard origin/dev-fork  # ⚠️ Discards local changes
```

### Method 2: PowerShell Sync Script

On Windows PowerShell:
```powershell
cd J:\show-build
.\sync-from-linux.ps1
```

### Method 3: SCP Direct Copy

From Linux:
```bash
# Critical SQLAlchemy fix
scp /mnt/process/show-build/app/models_v2.py kevin@HOME-MAIN:J:/show-build/app/
scp /mnt/process/show-build/app/models_speakers.py kevin@HOME-MAIN:J:/show-build/app/
scp /mnt/process/show-build/app/main.py kevin@HOME-MAIN:J:/show-build/app/

# SOT processing enhancements
scp /mnt/process/show-build/app/services/ffmpeg_tasks.py kevin@HOME-MAIN:J:/show-build/app/services/
scp /mnt/process/show-build/app/sot_router.py kevin@HOME-MAIN:J:/show-build/app/
scp /mnt/process/show-build/app/alembic/versions/1013_add_sot_processing_enhancements.py kevin@HOME-MAIN:J:/show-build/app/alembic/versions/
```

---

## After Sync: Run Migration & Restart Worker

**On Linux (show-build server):**
```bash
# Apply database migration for SOT enhancements
docker exec show-build-server python -m alembic upgrade head
```

**On Windows:**
1. Press `Ctrl+C` to stop current worker
2. Run: `.\start_worker.bat`
3. Verify no SQLAlchemy errors in output
4. Look for: `windows-HOME-MAIN@HOME-MAIN ready.`

---

## Verification

**Expected output (GOOD):**
```
[2025-10-22 XX:XX:XX,XXX: INFO/MainProcess] windows-HOME-MAIN@HOME-MAIN ready.
[2025-10-22 XX:XX:XX,XXX: INFO/MainProcess] Task services.ffmpeg_tasks.process_sot_video_multi_phase[...] received
[2025-10-22 XX:XX:XX,XXX: INFO/MainProcess] 🎬 Starting multi-phase processing on HOME-MAIN (Windows)...
```

**Error output (BAD - not fixed):**
```
ERROR: expression 'Speaker' failed to locate a name ('Speaker')
InvalidRequestError: When initializing mapper Mapper[Organization(organizations)]...
```

---

## SOT Processing Enhancements (Migration 1013)

**New features deployed to backend (2025-10-22):**

### Database Changes
- **15 Thumbnail Generation**: Generate 15 thumbnail candidates for user selection
- **Pre-Analysis**: Technical analysis of uploaded RAW file (duration, resolution, codec, etc.)
- **Post-Analysis**: Technical analysis of final processed file (verification)
- **Processing Report**: Comprehensive success/failure/warning tracking for all phases
- **Devel Mode**: Optional intermediate file retention for debugging

### New Database Fields (sot_processing_jobs table)
```sql
thumbnail_candidates  JSON    -- Array of 15 generated thumbnail filenames
selected_thumbnail    VARCHAR -- User-selected thumbnail (defaults to middle #8)
pre_analysis          JSON    -- Raw upload analysis metadata
post_analysis         JSON    -- Final output verification metadata
processing_report     JSON    -- Comprehensive phase-by-phase report
```

### API Changes
- `POST /api/sot/process/multi-phase` now accepts `devel_mode: bool` parameter
- Enhanced return payload includes pre_analysis, post_analysis, processing_report, thumbnail_options

---

## Changed Files

| File | Change |
|------|--------|
| `app/models_v2.py` | Added `Speaker` class (lines 136-199), SOT enhancements (lines 640-645) |
| `app/models_speakers.py` | Converted to compatibility shim |
| `app/services/ffmpeg_tasks.py` | SOT pipeline enhancements, devel_mode, 15 thumbnails, reporting |
| `app/sot_router.py` | Added `devel_mode` parameter to MultiPhaseProcessRequest (line 251) |
| `app/main.py` | Added Speaker to imports (line 39) |
| `app/alembic/versions/1013_add_sot_processing_enhancements.py` | NEW: Database migration for SOT enhancements |

---

## Future Automation

Once GitHub secret scanning is resolved:
- Automated sync via `scripts/deploy-to-windows-worker.sh`
- CI/CD via GitHub Actions (`.github/workflows/deploy-windows-worker.yml`)

---

## Troubleshooting

**Clock Drift Warning:**
```
WARNING: Substantial drift from celery@... may mean clocks are out of sync. Current drift is 14405 seconds.
```

**Fix:** Sync Windows system clock:
```powershell
# Run as Administrator
w32tm /resync
# OR set timezone
tzutil /s "Eastern Standard Time"
```

**Still Getting Import Errors:**

1. Verify files synced:
   ```powershell
   Get-FileHash J:\show-build\app\models_v2.py | Select Hash
   # Should be different from before sync
   ```

2. Check Python is finding correct files:
   ```powershell
   python -c "import sys; sys.path.insert(0, 'J:/show-build/app'); from models_v2 import Speaker; print(Speaker)"
   ```

3. Clear Python cache:
   ```powershell
   Remove-Item -Recurse -Force J:\show-build\app\__pycache__
   Remove-Item -Recurse -Force J:\show-build\app\services\__pycache__
   ```

---

**⏰ TIME SENSITIVE:** Deploy this fix ASAP to unblock SOT video processing on Windows worker.
