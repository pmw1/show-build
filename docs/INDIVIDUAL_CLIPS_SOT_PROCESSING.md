# Individual Clips SOT Processing

**Last Updated:** 2026-01-21
**Status:** Implemented
**Replaces:** Parent-child cue system with complex backend insertion

---

## Overview

When users need to extract multiple clips from a single video upload, each clip is now processed as an **independent, first-class SOT cue** from the moment of creation. This replaces the previous approach where a single "parent" SOT was created and child cues were inserted by the backend after processing.

### Key Principle

> When user marks N clips, create N independent SOT cues at cursor position. Each processes and updates itself - no parent lookup needed.

---

## Architecture Comparison

### Previous Approach (Deprecated)

```
User marks 3 clips → Single parent SOT created
                          ↓
                    Backend processes all clips
                          ↓
                    Backend searches for parent cue by AssetID
                          ↓
                    Backend inserts 3 child cues after parent
                          ↓
                    FAILURE POINT: Parent cue lookup fails
```

**Problems:**
- Complex parent cue lookup in database
- Single point of failure for multi-clip jobs
- Sequential processing (no parallelism)
- Race conditions during cue insertion
- Tight coupling between clips and parent

### New Approach (Current)

```
User marks 3 clips → Frontend generates 3 AssetIDs
                          ↓
                    Frontend inserts 3 independent cue blocks
                          ↓
                    Frontend triggers 3 processing jobs (parallel)
                          ↓
                    Each worker updates its own cue by AssetID
                          ↓
                    SUCCESS: No parent lookup, parallel processing
```

**Benefits:**
- Simpler: No parent-child relationship
- Robust: No parent cue lookup that can fail
- Parallel: All clips process simultaneously
- Consistent: Uses same pipeline as single SOT
- Maintainable: Less code, fewer edge cases

---

## Data Flow

### Step-by-Step Process

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER INTERACTION (SotModal.vue)                              │
├─────────────────────────────────────────────────────────────────┤
│  • User uploads video file (background upload starts)           │
│  • User selects "Individual Clips" clipping method              │
│  • User marks IN/OUT points for each clip                       │
│  • User clicks "Insert and Begin Processing"                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. ASSETID GENERATION (SotModal.vue → handleAddCue)             │
├─────────────────────────────────────────────────────────────────┤
│  • For EACH clip in clips array:                                │
│    - Call generateAssetId() to get unique ID from backend       │
│    - Build complete SOT data object with:                       │
│      · assetId: unique per clip                                 │
│      · slug: from clip definition                               │
│      · trimStart/trimEnd: clip's timecodes                      │
│      · sourceJobId: reference to upload job                     │
│      · jobType: 'single_trim'                                   │
│  • Emit 'submit-multiple' event with array of SOT objects       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CUE BLOCK INSERTION (ContentEditor.vue → submitMultipleSots) │
├─────────────────────────────────────────────────────────────────┤
│  • For EACH SOT in array (sequential to maintain order):        │
│    - Build cue block with metadata:                             │
│      · [AssetID: ABC123]                                        │
│      · [SourceJobId: sot_20260121_...]                          │
│      · [OriginalTrimStart/End: ...]                             │
│      · [ProcessingStatus: Queued]                               │
│    - Insert at cursor position via EditorPanel                  │
│  • Save all cues to database (single save operation)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. PROCESSING DISPATCH (ContentEditor.vue → triggerSOTProcessing│
├─────────────────────────────────────────────────────────────────┤
│  • For EACH SOT (parallel via Promise.all):                     │
│    - POST /api/sot/process/multi-phase                          │
│    - job_type: 'single_trim'                                    │
│    - trim_start/trim_end: clip's specific times                 │
│    - asset_id: clip's unique AssetID                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. WORKER PROCESSING (ffmpeg_tasks.py → single_trim workflow)   │
├─────────────────────────────────────────────────────────────────┤
│  • Each job runs independently on available worker              │
│  • Standard single_trim pipeline:                               │
│    - Phase 0: FFprobe analysis                                  │
│    - Phase 0.5: Audio extraction + Whisper transcription        │
│    - Phase 1: Video trimming                                    │
│    - Phase 2: Audio normalization                               │
│    - Phase 4: Thumbnail + MP3 generation                        │
│    - Phase 5: Final file placement + cue update                 │
│  • Updates cue block by AssetID (no parent lookup)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cue Block Format

Each clip's cue block includes source reference metadata for future re-trimming:

```markdown
<!-- Begin Cue -->
[Type: SOT]
[AssetID: ABC123]
[Slug: senator-intro]
[Description: Opening remarks from Senator]
[MediaURL: /episodes/0250/assets/video/ABC123.mp4]
[Duration: 00:00:30]
[TrimStart: 00:00:05]
[TrimEnd: 00:00:35]
[SourceJobId: sot_20260121_143022_xyz]
[OriginalTrimStart: 00:00:05]
[OriginalTrimEnd: 00:00:35]
[Transcription: "Thank you for having me today..."]
[ThumbnailURL: /episodes/0250/assets/images/ABC123_thumb.jpg]
[Credits: {}]
[ProcessingStatus: Complete]
<!-- End Cue -->
```

### New Metadata Fields

| Field | Purpose |
|-------|---------|
| `SourceJobId` | Reference to original upload job for re-trimming |
| `OriginalTrimStart` | Original trim point (preserved if user adjusts later) |
| `OriginalTrimEnd` | Original trim point (preserved if user adjusts later) |
| `ProcessingStatus` | Current state: Queued, Processing, Complete, Failed |

---

## File Changes

### Frontend

#### `disaffected-ui/src/components/modals/SotModal.vue`

**Changes:**
1. Added `'submit-multiple'` to emits array (line 921)
2. Modified `handleAddCue()` function:

```javascript
// INDIVIDUAL CLIPS MODE: Generate separate SOT for each clip
if (clippingMethod.value === 'individual-clips') {
  const multipleSots = []
  for (const clip of clips.value) {
    const clipAssetId = await generateAssetId()

    const clipSotData = {
      assetId: clipAssetId,
      slug: clip.slug,
      trimStart: clip.time_start || '00:00:00',
      trimEnd: clip.time_end || '00:00:00',
      sourceJobId: tempJobId.value,
      originalTrimStart: clip.time_start,
      originalTrimEnd: clip.time_end,
      jobType: SOT_JOB_TYPES.SINGLE_TRIM,
      clippingMethod: 'single-trim'  // Process as simple single trim
      // ... other fields
    }
    multipleSots.push(clipSotData)
  }

  emit('submit-multiple', multipleSots)
  return
}
```

#### `disaffected-ui/src/components/ContentEditor.vue`

**Changes:**
1. Added event handler to SotModal component (line 229):
```vue
@submit-multiple="submitMultipleSots"
```

2. Added `submitMultipleSots(sotsArray)` method:
```javascript
async submitMultipleSots(sotsArray) {
  // Insert cues sequentially to maintain order
  for (const data of sotsArray) {
    const sotCue = `<!-- Begin Cue -->
[Type: SOT]
[AssetID: ${data.assetId}]
[Slug: ${data.slug}]
[SourceJobId: ${data.sourceJobId}]
[OriginalTrimStart: ${data.originalTrimStart}]
[OriginalTrimEnd: ${data.originalTrimEnd}]
[ProcessingStatus: Queued]
<!-- End Cue -->`;

    await this.$refs.editorPanel.handleSotCueSubmit(sotCue)
  }

  // Save once after all insertions
  await this.saveCurrentItem()

  // Trigger processing in parallel
  await Promise.all(sotsArray.map(data =>
    this.triggerSOTProcessing(data)
  ))
}
```

### Backend

#### `app/sot_router.py`

**Changes:**
Modified `/api/sot/process/multi-phase` endpoint to support child clip jobs:

```python
# Check if this is a child clip request (different asset_id than the parent)
is_child_clip = (
    parent_job.status != 'uploaded' and
    parent_job.asset_id != request.asset_id
)

if is_child_clip:
    # Create a new child job record for this clip
    # Child shares parent's working directory but has its own tracking
    child_job_id = f"{request.temp_job_id}_{uuid4()[:8]}"

    job = SOTProcessingJob(
        temp_job_id=child_job_id,
        episode=request.episode,
        slug=request.slug,
        asset_id=request.asset_id,
        status='uploaded',
        working_directory=parent_job.working_directory,  # Share working dir
        source_asset_id=parent_job.source_asset_id
    )
```

This allows multiple clips from the same upload to each have their own job record while sharing the same source video file.

#### `app/services/ffmpeg_tasks.py`

**Changes:**
1. Deprecated `_process_individual_clips()` function
2. Deprecated `_insert_multiple_cue_blocks()` function

Both functions now:
- Log deprecation warnings
- Raise `DeprecationWarning` exception
- Preserve legacy code below for reference

```python
def _process_individual_clips(...):
    """
    DEPRECATED: This function is no longer used.
    Individual clips are now processed as independent SOTs
    via the frontend's submit-multiple event.
    """
    logger.warning("⚠️ DEPRECATED: _process_individual_clips() called")
    raise DeprecationWarning(
        "individual_clips workflow is deprecated. "
        "Use the updated frontend that emits independent SOT cues."
    )
```

---

## API Usage

### Processing Request (per clip)

```http
POST /api/sot/process/multi-phase
Content-Type: application/json

{
  "temp_job_id": "sot_20260121_143022_xyz",
  "episode": "0250",
  "slug": "senator-intro",
  "asset_id": "ABC123",
  "trim_start": "00:00:05",
  "trim_end": "00:00:35",
  "job_type": "single_trim",
  "clips": null
}
```

**Note:** The `clips` field is `null` for the new approach. Each clip is its own independent job with its own trim times.

---

## Testing Checklist

### Single Clip (Regression Test)
- [ ] Upload video, mark single trim, submit
- [ ] Verify single cue block appears
- [ ] Verify processing completes
- [ ] Verify cue block updates with media/transcription

### Multiple Clips (New Feature)
- [ ] Open SotModal, select "Individual Clips" mode
- [ ] Mark 2-3 clips with different slugs and timecodes
- [ ] Submit and verify:
  - [ ] N cue blocks appear at cursor position (in order)
  - [ ] Each cue has unique AssetID
  - [ ] Each cue shows "Processing..." status
  - [ ] All processing jobs start (check network tab)
- [ ] After processing:
  - [ ] Each cue block updates independently
  - [ ] Each has correct MediaURL, Duration, Transcription
  - [ ] Thumbnails generated for each

### Database Verification
```sql
-- Check for multiple jobs from same upload
SELECT temp_job_id, slug, asset_id, status, job_type
FROM sot_processing_jobs
WHERE temp_job_id LIKE 'sot_20260121%'
ORDER BY created_at;
```

### Re-trim Test (Future Feature)
- [ ] Verify `SourceJobId` metadata present in cue block
- [ ] Verify `OriginalTrimStart/End` preserved
- [ ] (Future) Test re-trimming from original source

---

## Migration Notes

### Existing Individual Clips Jobs

Jobs created before this change that use `job_type: 'individual_clips'` will fail with a `DeprecationWarning`. These jobs should be:

1. Cancelled in the database
2. Re-created using the updated frontend

```sql
-- Find deprecated jobs
SELECT * FROM sot_processing_jobs
WHERE job_type = 'individual_clips'
AND status != 'completed';

-- Mark as cancelled
UPDATE sot_processing_jobs
SET status = 'cancelled',
    error_message = 'Workflow deprecated - recreate using updated frontend'
WHERE job_type = 'individual_clips'
AND status NOT IN ('completed', 'failed', 'cancelled');
```

### Frontend Compatibility

The backend still accepts `job_type: 'individual_clips'` in the API request, but will reject it with a clear error message directing users to update their frontend.

---

## Related Documentation

- [SOT Processing Overview](./SOT_PROCESSING.md)
- [AssetID System Guide](./ASSETID_SYSTEM_GUIDE.md)
- [Celery Worker Setup](./CELERY_WORKER_SETUP.md)
- [Architecture Decisions](./ARCHITECTURE_DECISIONS.md)
