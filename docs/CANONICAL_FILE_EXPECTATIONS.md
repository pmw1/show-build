# Canonical File Expectations
## Semantic File Inventory Specification

**Status**: ✅ AUTHORITATIVE - File Classification Reference
**Version**: 1.0
**Date**: 2025-10-15
**Purpose**: Semantic categorization of expected episode files for intelligent inventory matching
**UFDP Index**: `file-expectations`, `semantic-inventory`, `file-classification`

---

## Overview

This document defines **what files we expect to exist** in an episode directory based on their **purpose and characteristics**, not their exact filenames. This enables intelligent file matching using LLM-based semantic analysis rather than rigid pattern matching.

Each file expectation is defined by:
- **Category**: Broad classification (capture, export, thumbnail, etc.)
- **Purpose**: What this file is used for
- **Characteristics**: Technical attributes that identify it
- **Location Hints**: Where we typically find it
- **Required**: Whether absence indicates a problem
- **Multiplicity**: Single file, multiple files, or optional

---

## Root Level Files

### Episode Metadata File
- **Category**: `metadata`
- **Purpose**: Contains episode metadata (number, title, air date, status, description)
- **Characteristics**:
  - Markdown format with YAML frontmatter
  - Contains fields: episode, title, air_date, duration, status
  - Human-readable episode information
- **Location Hints**: `{EPISODE}/info.md`, `{EPISODE}/metadata.md`, `{EPISODE}/README.md`
- **Required**: Yes (CRITICAL)
- **Multiplicity**: Single file
- **Validation**: Must contain YAML frontmatter with episode number

### Rundown Export File
- **Category**: `metadata`
- **Purpose**: Complete rundown structure export (regions, items, cues, media metadata)
- **Characteristics**:
  - JSON format
  - Contains: episode, regions, rundown_items, cues
  - Structured rundown data for external tools
- **Location Hints**: `{EPISODE}/{EPISODE}-rundown.json`, `{EPISODE}/rundown.json`
- **Required**: No (generated on demand)
- **Multiplicity**: Single file
- **Validation**: Valid JSON with rundown structure

---

## Capture Files (Raw Recordings)

### Block Capture - Primary
- **Category**: `capture`
- **Purpose**: Raw unedited recording of main show blocks
- **Characteristics**:
  - Video file (MOV, MP4, MKV)
  - Large file size (multi-GB)
  - High bitrate (5000+ kbps)
  - Contains "BLOCK" or "Block" in name or is in captures folder
  - May have letter designation (A, B, C)
- **Location Hints**: `captures/BLOCK-A.mov`, `captures/Block-A.mp4`, `BLOCK-A.mov`
- **Required**: No (may not exist for new episodes)
- **Multiplicity**: Multiple files (typically 2-3 blocks per episode)
- **Pattern Recognition**: Filename contains block identifier + letter/number

### Block Capture - Interrupted/Resumed
- **Category**: `capture`
- **Purpose**: Continuation of interrupted block recording
- **Characteristics**:
  - Video file (MOV, MP4, MKV)
  - Large file size
  - Contains block identifier with numeric suffix (B2, B3)
  - Similar timestamp to primary block file
- **Location Hints**: `captures/BLOCK-B2.mov`, `captures/Block-B-part2.mp4`
- **Required**: No (only if recording was interrupted)
- **Multiplicity**: Multiple possible per block
- **Pattern Recognition**: Block identifier + numeric continuation marker

### Break Capture
- **Category**: `capture`
- **Purpose**: Recording of breaks between main blocks
- **Characteristics**:
  - Video file (MOV, MP4, MKV)
  - Smaller than block files
  - Contains "BREAK" or "Break" in name
  - Numeric designation (1, 2)
- **Location Hints**: `captures/BREAK-1.mov`, `captures/Break1.mp4`
- **Required**: No
- **Multiplicity**: Multiple files (typically 1-2 breaks)
- **Pattern Recognition**: Contains "break" + number

---

## Thumbnail/Artwork Files

### Master Thumbnail - Widescreen Source
- **Category**: `thumbnail`
- **Purpose**: Editable master artwork for video platforms (16:9 aspect ratio)
- **Characteristics**:
  - Photoshop file (PSD) or layered image format
  - High resolution (3840x2160 or similar)
  - 16:9 aspect ratio
  - Contains "master", "16x9", "widescreen", or "video" in name
- **Location Hints**: `thumbnails/master-16x9.psd`, `thumbnails/widescreen-master.psd`
- **Required**: No (may use PNG only)
- **Multiplicity**: Single file
- **Validation**: Widescreen aspect ratio, layered format

### Master Thumbnail - Widescreen Export
- **Category**: `thumbnail`
- **Purpose**: High-resolution export of widescreen artwork
- **Characteristics**:
  - PNG or JPG
  - High resolution (1920x1080 minimum)
  - 16:9 aspect ratio
  - Contains "master", "16x9", or similar
- **Location Hints**: `thumbnails/master-16x9.png`, `thumbnails/thumbnail-16x9.jpg`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: 16:9 aspect ratio, high resolution

### Master Thumbnail - Square Source
- **Category**: `thumbnail`
- **Purpose**: Editable master artwork for podcast platforms (1:1 aspect ratio)
- **Characteristics**:
  - Photoshop file (PSD) or layered format
  - High resolution (3000x3000 or similar)
  - 1:1 aspect ratio (square)
  - Contains "square", "podcast", or "1x1" in name
- **Location Hints**: `thumbnails/master-square.psd`, `thumbnails/podcast-master.psd`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: Square aspect ratio, layered format

### Master Thumbnail - Square Export
- **Category**: `thumbnail`
- **Purpose**: High-resolution export of square artwork
- **Characteristics**:
  - PNG or JPG
  - High resolution (1400x1400 minimum)
  - 1:1 aspect ratio (square)
  - Contains "square" or "podcast" in name
- **Location Hints**: `thumbnails/master-square.png`, `thumbnails/podcast.jpg`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: Square aspect ratio, high resolution

---

## Export Files (Distribution Ready)

### Block Video Export
- **Category**: `export`
- **Purpose**: Finalized edited video for distribution (per block)
- **Characteristics**:
  - MP4 video file
  - Standard resolution (1920x1080)
  - Contains episode number + block letter
  - Moderate file size (edited, not raw)
  - In exports folder or root
- **Location Hints**: `exports/{EPISODE}-A.mp4`, `{EPISODE}-Block-A.mp4`
- **Required**: No (created after editing)
- **Multiplicity**: Multiple (one per block)
- **Pattern Recognition**: Episode number + block identifier + .mp4

### Block Audio Export
- **Category**: `export`
- **Purpose**: Audio extracted from block video (MP3 format)
- **Characteristics**:
  - MP3 audio file
  - 192kbps bitrate typical
  - Contains episode number + block letter
  - Smaller file size (audio only)
- **Location Hints**: `exports/{EPISODE}-A.mp3`, `{EPISODE}-Block-A.mp3`
- **Required**: No
- **Multiplicity**: Multiple (one per block video)
- **Pattern Recognition**: Episode number + block identifier + .mp3

### Full Episode Video
- **Category**: `export`
- **Purpose**: Complete stitched episode (all blocks + breaks merged)
- **Characteristics**:
  - MP4 video file
  - Large file size (full episode)
  - Contains episode number without block letter
  - Standard resolution (1920x1080)
- **Location Hints**: `exports/{EPISODE}.mp4`, `{EPISODE}-full.mp4`, `{EPISODE}-complete.mp4`
- **Required**: No (final deliverable)
- **Multiplicity**: Single file
- **Validation**: Significantly larger than individual blocks

### Full Episode Audio
- **Category**: `export`
- **Purpose**: Full episode audio (podcast format)
- **Characteristics**:
  - MP3 audio file
  - 192kbps bitrate
  - Contains episode number
  - Largest audio file for episode
- **Location Hints**: `exports/{EPISODE}.mp3`, `{EPISODE}-full.mp3`, `{EPISODE}-podcast.mp3`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: Duration matches full video

### Subtitle File
- **Category**: `export`
- **Purpose**: Subtitle/caption file for full episode
- **Characteristics**:
  - SRT, VTT, or SUB format
  - Text-based subtitle format
  - Contains episode number
  - Small file size (text only)
- **Location Hints**: `exports/{EPISODE}.srt`, `{EPISODE}-subtitles.srt`
- **Required**: No
- **Multiplicity**: Single file (per format)
- **Validation**: Valid subtitle format

### Distribution Thumbnail - 16:9 High Quality
- **Category**: `export`
- **Purpose**: High-quality widescreen thumbnail for distribution
- **Characteristics**:
  - PNG or JPG
  - 1920x1080 resolution
  - 16:9 aspect ratio
  - Contains "poster", "thumbnail", "16x9"
- **Location Hints**: `exports/{EPISODE}-poster-16x9.png`, `exports/thumbnail-1920x1080.png`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: Exact 1920x1080 resolution

### Distribution Thumbnail - 16:9 Web Optimized
- **Category**: `export`
- **Purpose**: Web-optimized widescreen thumbnail (YouTube, Rumble)
- **Characteristics**:
  - PNG or JPG
  - 1280x720 resolution
  - 16:9 aspect ratio
  - File size under 2MB
  - Contains "web", "720", "youtube"
- **Location Hints**: `exports/{EPISODE}-poster-16x9-web.png`, `exports/youtube-thumbnail.jpg`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: 1280x720, under 2MB

### Distribution Thumbnail - Square Large
- **Category**: `export`
- **Purpose**: Large square thumbnail for podcast platforms
- **Characteristics**:
  - PNG or JPG
  - 3000x3000 resolution
  - 1:1 aspect ratio
  - Contains "square", "podcast", "3000"
- **Location Hints**: `exports/{EPISODE}-poster-square.png`, `exports/podcast-3000x3000.png`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: 3000x3000, square

### Distribution Thumbnail - Square Small
- **Category**: `export`
- **Purpose**: Minimum size square thumbnail for podcasts
- **Characteristics**:
  - PNG or JPG
  - 1400x1400 resolution
  - 1:1 aspect ratio
  - Contains "square", "small", "1400"
- **Location Hints**: `exports/{EPISODE}-poster-square-small.png`, `exports/podcast-1400x1400.png`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: 1400x1400, square

### Distribution Thumbnail - Vertical
- **Category**: `export`
- **Purpose**: Vertical format for Instagram/TikTok
- **Characteristics**:
  - PNG or JPG
  - 1080x1920 resolution
  - 9:16 aspect ratio (vertical)
  - Contains "vertical", "story", "tiktok", "instagram"
- **Location Hints**: `exports/{EPISODE}-poster-vertical.png`, `exports/instagram-story.jpg`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: 1080x1920, vertical orientation

### Distribution Thumbnail - Facebook Square
- **Category**: `export`
- **Purpose**: Square format optimized for Facebook
- **Characteristics**:
  - PNG or JPG
  - 1080x1080 resolution
  - 1:1 aspect ratio
  - Contains "facebook", "1080"
- **Location Hints**: `exports/{EPISODE}-poster-facebook.png`, `exports/facebook-1080x1080.jpg`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: 1080x1080, square

---

## Project Files (Production Software)

### vMix Project File
- **Category**: `project`
- **Purpose**: vMix production project file for live show
- **Characteristics**:
  - VMIX file format
  - Contains episode number
  - Production configuration
- **Location Hints**: `projects/{EPISODE}.vmix`, `{EPISODE}.vmix`
- **Required**: No
- **Multiplicity**: Single file
- **Validation**: Valid VMIX format

### After Effects Teaser Project
- **Category**: `project`
- **Purpose**: Guest interview teaser production project
- **Characteristics**:
  - AEP file (After Effects Project)
  - Contains "teaser" and guest name
  - In teasers subfolder
- **Location Hints**: `projects/teasers/{EPISODE}-teaser-{guest}/{EPISODE}-teaser-{guest}.aep`
- **Required**: No
- **Multiplicity**: Multiple (one per guest)
- **Pattern Recognition**: "teaser" + guest identifier + .aep

### After Effects Graphics Project
- **Category**: `project`
- **Purpose**: Custom graphics/titles production project
- **Characteristics**:
  - AEP file (After Effects Project)
  - Contains graphics type (titlecard, lower-third, etc.)
  - In graphics subfolder
- **Location Hints**: `projects/graphics/{EPISODE}-titlecard/{EPISODE}-titlecard.aep`
- **Required**: No
- **Multiplicity**: Multiple (various graphics)
- **Pattern Recognition**: Graphics type + .aep

---

## Asset Files (Production Media)

### Video Asset
- **Category**: `asset`
- **Purpose**: Final video clip used in show (edited, ready for playback)
- **Characteristics**:
  - MP4 or MOV video file
  - In assets/video folder
  - Moderate file size (edited clip, not raw)
  - May contain AssetID prefix or order number
- **Location Hints**: `assets/video/{NNN}-{slug}.mp4`, `assets/video/AST_{ID}_{slug}.mp4`
- **Required**: No
- **Multiplicity**: Multiple (many clips per episode)
- **Pattern Recognition**: Order number or AssetID + descriptive slug

### Image Asset
- **Category**: `asset`
- **Purpose**: Still image used in show (photo, screenshot, graphic)
- **Characteristics**:
  - PNG or JPG image file
  - In assets/images folder
  - May contain AssetID or order number
- **Location Hints**: `assets/images/{NNN}-{slug}.png`, `assets/images/AST_{ID}_{slug}.jpg`
- **Required**: No
- **Multiplicity**: Multiple
- **Pattern Recognition**: Order number or AssetID + descriptive slug

### Audio Asset
- **Category**: `asset`
- **Purpose**: Audio clip used in show (music, sound effect, voiceover)
- **Characteristics**:
  - MP3 or WAV audio file
  - In assets/audio folder
  - May contain AssetID or order number
- **Location Hints**: `assets/audio/{NNN}-{slug}.mp3`, `assets/audio/AST_{ID}_{slug}.wav`
- **Required**: No
- **Multiplicity**: Multiple
- **Pattern Recognition**: Order number or AssetID + descriptive slug

### Graphics Asset
- **Category**: `asset`
- **Purpose**: Graphics overlay (lower third, title card, overlay)
- **Characteristics**:
  - PNG file (usually with transparency)
  - In assets/graphics or assets/gfx folder
  - May contain AssetID or order number
- **Location Hints**: `assets/graphics/{NNN}-{slug}.png`, `assets/gfx/AST_{ID}_{slug}.png`
- **Required**: No
- **Multiplicity**: Multiple
- **Pattern Recognition**: Order number or AssetID + descriptive slug

---

## Script Files (Generated Outputs)

### Host Hardcopy Script
- **Category**: `script`
- **Purpose**: Printed script for host to read from
- **Characteristics**:
  - PDF file
  - Contains "host", "hardcopy", "print"
  - In scripts/current or scripts/versions folder
- **Location Hints**: `scripts/current/host-hardcopy.pdf`, `scripts/versions/{timestamp}/host-hardcopy.pdf`
- **Required**: No (generated on demand)
- **Multiplicity**: Multiple versions
- **Validation**: PDF format, printable

### Host Teleprompter Script
- **Category**: `script`
- **Purpose**: HTML script for teleprompter display
- **Characteristics**:
  - HTML file
  - Contains "teleprompter", "prompter"
  - Large readable font
- **Location Hints**: `scripts/current/host-teleprompter.html`, `scripts/versions/{timestamp}/teleprompter.html`
- **Required**: No
- **Multiplicity**: Multiple versions
- **Validation**: HTML format

### Director Script
- **Category**: `script`
- **Purpose**: Complete production script with all cues
- **Characteristics**:
  - HTML file
  - Contains "director"
  - Includes production cues, timing
- **Location Hints**: `scripts/current/director-script.html`, `scripts/versions/{timestamp}/director.html`
- **Required**: No
- **Multiplicity**: Multiple versions
- **Validation**: HTML format

### Media List
- **Category**: `script`
- **Purpose**: Pre-flight checklist of all media
- **Characteristics**:
  - TXT file
  - Contains "media-list", "checklist"
  - Plain text format
- **Location Hints**: `scripts/current/media-list.txt`, `scripts/versions/{timestamp}/media-list.txt`
- **Required**: No
- **Multiplicity**: Multiple versions
- **Validation**: Plain text

### Flat Text Script
- **Category**: `script`
- **Purpose**: Plain text for LLM processing/analysis
- **Characteristics**:
  - TXT file
  - Contains "flat", "text", "plain"
  - No formatting markup
- **Location Hints**: `scripts/current/flat-text.txt`, `scripts/versions/{timestamp}/flat-text.txt`
- **Required**: No
- **Multiplicity**: Multiple versions
- **Validation**: Plain text, no markup

### Source Markdown Script
- **Category**: `script`
- **Purpose**: Neutral format backup (version control friendly)
- **Characteristics**:
  - MD (Markdown) file
  - Contains "source"
  - Minimal markup
- **Location Hints**: `scripts/current/source.md`, `scripts/versions/{timestamp}/source.md`
- **Required**: No
- **Multiplicity**: Multiple versions
- **Validation**: Valid markdown

---

## LLM Matching Instructions

When using an LLM to match files to expectations:

### Matching Process
1. **Gather file metadata**: filename, path, size, extension, dimensions (if image/video)
2. **Present file info to LLM** with expectation definition
3. **Ask**: "Does this file match the expectation? Consider purpose, characteristics, and location."
4. **Confidence scoring**: LLM should return confidence level (0-100%)
5. **Accept matches** above 80% confidence
6. **Flag ambiguous** matches (50-80%) for manual review
7. **Reject** matches below 50%

### LLM Prompt Template
```
You are analyzing episode files to determine if they match semantic expectations.

EXPECTATION:
- Category: {category}
- Purpose: {purpose}
- Characteristics: {characteristics}
- Location Hints: {location_hints}

FILE FOUND:
- Path: {file_path}
- Filename: {filename}
- Extension: {extension}
- Size: {size}
- Dimensions: {dimensions} (if applicable)
- Location: {folder_path}

Does this file match the expectation? Consider:
1. Does the purpose align?
2. Do the technical characteristics match?
3. Is it in a plausible location?
4. Does the filename suggest this purpose?

Respond with JSON:
{
  "matches": true/false,
  "confidence": 0-100,
  "reasoning": "Brief explanation",
  "alternative_expectation": "If this doesn't match, what might it be?"
}
```

### Edge Cases
- **Multiple candidates**: Choose highest confidence, flag others
- **No candidates**: Mark expectation as "unfulfilled"
- **Unexpected files**: Categorize as "unclassified" for later review
- **Renamed files**: LLM should recognize purpose despite non-standard naming

---

## Mapping Output Format (UFDP)

Once files are matched to expectations, generate a mapping file:

**Location**: `{EPISODE}/{EPISODE}-file-mapping.yaml`

**Format**:
```yaml
---
episode: "0244"
scan_timestamp: "2025-10-15T05:30:00Z"
scan_version: "1.0"
llm_model: "llama3.2"
source_system: "syncthing" # or "google_drive"

expectations:
  - expectation_id: "metadata.episode_info"
    category: "metadata"
    purpose: "Episode metadata file"
    matched: true
    confidence: 95
    file_path: "info.md"
    file_size: 2048
    reasoning: "Contains YAML frontmatter with episode metadata"

  - expectation_id: "capture.block_primary"
    category: "capture"
    purpose: "Block A raw recording"
    matched: true
    confidence: 88
    file_path: "captures/BLOCK-A.mov"
    file_size: 5368709120
    reasoning: "Large MOV file in captures folder with BLOCK-A designation"

  - expectation_id: "export.full_episode_video"
    category: "export"
    purpose: "Full episode video export"
    matched: false
    confidence: 0
    file_path: null
    reasoning: "No file found matching full episode video criteria"

  - expectation_id: "thumbnail.master_widescreen_source"
    category: "thumbnail"
    purpose: "Master 16:9 artwork source"
    matched: true
    confidence: 75
    file_path: "thumbnails/episode-artwork-16x9.psd"
    file_size: 15728640
    reasoning: "PSD file with 16:9 in name, flagged for review due to non-standard naming"
    needs_review: true

unclassified_files:
  - file_path: "old-backup.zip"
    file_size: 1048576
    reason: "No matching expectation found"
  - file_path: "notes.txt"
    file_size: 512
    reason: "User-created file, not in canonical standard"

statistics:
  total_expectations: 45
  matched: 23
  unmatched: 18
  needs_review: 4
  unclassified_files: 2
  total_files_scanned: 27
```

---

## Stray File Patterns (Non-Canonical)

Files that don't match canonical expectations but are commonly found. These should be flagged for review/cleanup:

### Temporary/Cache Files
- **Pattern**: `.DS_Store`, `Thumbs.db`, `desktop.ini`, `.localized`
- **Category**: `stray.system`
- **Action**: Safe to delete
- **Reasoning**: OS-generated metadata files

### Backup/Version Files
- **Pattern**: `*.bak`, `*_backup`, `*_old`, `* Copy`, `* (1)`, `~$*`
- **Category**: `stray.backup`
- **Action**: Review before deleting (may contain important data)
- **Reasoning**: Manual backup files or auto-save copies

### Sync Conflict Files
- **Pattern**: `* conflict *`, `* conflicted copy *`, `*_CONFLICT_*`
- **Category**: `stray.sync_conflict`
- **Action**: Requires manual resolution
- **Reasoning**: File sync conflicts from Syncthing/Drive/Dropbox

### Compressed Archives
- **Pattern**: `*.zip`, `*.rar`, `*.7z`, `*.tar.gz`
- **Category**: `stray.archive`
- **Action**: Review contents, may be old backups
- **Reasoning**: Archived files, often outdated

### Sync Metadata Directories
- **Pattern**: `.syncthing*`, `.stfolder`, `.blackmagicsync-v2/`, `.stversions/`
- **Category**: `stray.sync_metadata`
- **Action**: Safe to exclude from inventory (system folders)
- **Reasoning**: Sync service metadata

### Temporary Work Directories
- **Pattern**: `temporary-files/`, `growing-temporary-files/`, `temp/`, `tmp/`
- **Category**: `stray.temp_directory`
- **Action**: Review contents, likely safe to delete
- **Reasoning**: Temporary working directories

### Unnamed/Default Directories
- **Pattern**: `New Folder`, `New folder (1)`, `Untitled folder`
- **Category**: `stray.unnamed`
- **Action**: Review contents before action
- **Reasoning**: User-created folders without proper naming

### Editor Workspace Directories
- **Pattern**: `.claude/`, `.vscode/`, `.idea/`, `__pycache__/`
- **Category**: `stray.editor_workspace`
- **Action**: Safe to exclude from inventory
- **Reasoning**: Code editor metadata

### Partial Downloads
- **Pattern**: `*.part`, `*.crdownload`, `*.tmp`, `*.download`
- **Category**: `stray.partial`
- **Action**: Incomplete downloads, safe to delete
- **Reasoning**: Interrupted file transfers

### Log Files
- **Pattern**: `*.log`, `error.txt`, `debug.txt`
- **Category**: `stray.log`
- **Action**: Review for debugging info, then delete
- **Reasoning**: Application log files

### Export Rejects/Drafts
- **Pattern**: Files in root starting with `draft-`, `test-`, `old-`, `backup-`
- **Category**: `stray.draft`
- **Action**: Review and move to proper location or delete
- **Reasoning**: Work-in-progress files left in wrong location

### Misplaced Captures
- **Pattern**: Video files (`.mov`, `.mp4`) in root instead of `captures/`
- **Category**: `stray.misplaced_capture`
- **Action**: Move to `captures/` folder
- **Reasoning**: Capture file in wrong location

### Misplaced Exports
- **Pattern**: Files matching export patterns in wrong folder
- **Category**: `stray.misplaced_export`
- **Action**: Move to `exports/` folder
- **Reasoning**: Export file in wrong location

### Unrecognized Project Files
- **Pattern**: `.prproj` (Premiere), `.drp` (Resolve), `.fcpx` (Final Cut) outside `projects/`
- **Category**: `stray.misplaced_project`
- **Action**: Move to `projects/` folder
- **Reasoning**: Project file in wrong location

### Random User Files
- **Pattern**: `notes.txt`, `todo.md`, `script-ideas.docx`
- **Category**: `stray.user_notes`
- **Action**: Review and decide if belongs in `preshow/` or elsewhere
- **Reasoning**: User working files without canonical purpose

### Source Media (Not Final Assets)
- **Pattern**: Raw footage, screen recordings, unedited files in wrong location
- **Category**: `stray.source_media`
- **Action**: Move to `projects/{type}/source/` or delete if no longer needed
- **Reasoning**: Production source files misplaced

### Duplicate Files (Same Content, Different Names)
- **Pattern**: Detected via hash comparison
- **Category**: `stray.duplicate`
- **Action**: Keep one canonical version, delete duplicates
- **Reasoning**: Same file stored multiple times

---

## LLM Classification Prompt for Stray Files

When the LLM encounters a file that doesn't match any canonical expectation:

```
You are analyzing an unclassified file in an episode directory.

FILE FOUND:
- Path: {file_path}
- Filename: {filename}
- Extension: {extension}
- Size: {size}
- Location: {folder_path}
- Modified Date: {modified}

This file does not match any canonical expectation. Classify it as one of:
1. stray.system - OS/system file (safe to ignore)
2. stray.backup - Backup/old version (review before delete)
3. stray.sync_conflict - Sync conflict (needs resolution)
4. stray.archive - Compressed archive (review contents)
5. stray.sync_metadata - Sync service metadata (ignore)
6. stray.temp_directory - Temporary folder (review/delete)
7. stray.unnamed - Unnamed folder (review contents)
8. stray.editor_workspace - Editor metadata (ignore)
9. stray.partial - Incomplete download (delete)
10. stray.log - Log file (review/delete)
11. stray.draft - Draft/work-in-progress (relocate or delete)
12. stray.misplaced_capture - Capture in wrong folder (relocate)
13. stray.misplaced_export - Export in wrong folder (relocate)
14. stray.misplaced_project - Project file in wrong folder (relocate)
15. stray.user_notes - User working files (review)
16. stray.source_media - Production source misplaced (relocate)
17. stray.duplicate - Duplicate of canonical file (delete)
18. stray.unknown - Cannot determine purpose (manual review)

Respond with JSON:
{
  "category": "stray.{subcategory}",
  "confidence": 0-100,
  "reasoning": "Why you classified it this way",
  "suggested_action": "ignore|delete|relocate|review",
  "relocation_target": "folder_path (if action is relocate)",
  "safety": "safe|caution|dangerous" # How risky is the suggested action
}
```

---

## Next Steps

1. ✅ Create this specification document
2. ⏸️ Implement LLM-based file matcher for Syncthing
3. ⏸️ Generate UFDP mapping file for local filesystem
4. ⏸️ **PAUSE**: Review results before proceeding
5. ⏸️ Extend to Google Drive filesystem
6. ⏸️ Compare mappings between systems
7. ⏸️ Design merge strategy

---

**END OF SPECIFICATION**

*This document defines semantic file expectations for intelligent episode inventory.*
