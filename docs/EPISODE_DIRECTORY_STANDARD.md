# Episode Directory Structure Standard
## Canonical Specification for Show-Build File Organization

**Status**: ✅ AUTHORITATIVE - Single Source of Truth
**Version**: 1.0
**Date**: 2025-10-13
**Scope**: All episodes in `/mnt/sync/disaffected/episodes/{EPISODE}/`
**UFDP Index**: `file-structure`, `episode-organization`, `canonical-standard`

---

## Table of Contents

1. [Authority & Enforcement](#authority--enforcement)
2. [Complete Directory Tree](#complete-directory-tree)
3. [Root Level Files](#root-level-files)
4. [Projects Folder](#projects-folder)
5. [Captures Folder](#captures-folder)
6. [Thumbnails Folder](#thumbnails-folder)
7. [Assets Folder](#assets-folder)
8. [Rundown Folder](#rundown-folder)
9. [Scripts Folder](#scripts-folder)
10. [Exports Folder](#exports-folder)
11. [Naming Conventions](#naming-conventions)
12. [Hierarchy & Relationships](#hierarchy--relationships)
13. [Validation & Enforcement](#validation--enforcement)
14. [Migration & Consolidation](#migration--consolidation)

---

## 🗄️ Database-First Architecture (Current State)

**CRITICAL**: Show-Build is a **database-first** system. The PostgreSQL database is the **single source of truth** for all episode content, rundowns, and metadata.

### Data Storage Model

**Content Storage** (100% Database):
- ✅ **Episode metadata**: Stored in `episodes` table (title, air date, duration, status, etc.)
- ✅ **Rundown structure**: Stored in `rundowns` table (one or more rundowns per episode)
- ✅ **Rundown items**: Stored in `rundown_items` table (segments, ads, promos, transitions)
- ✅ **Script content**: Stored in `rundown_items.script_content` field (markdown with YAML frontmatter)
- ✅ **All metadata**: Stored in database fields, NOT filesystem files

**Media Storage** (Filesystem):
- ✅ **Video files**: Stored in `assets/video/`
- ✅ **Audio files**: Stored in `assets/audio/`
- ✅ **Image files**: Stored in `assets/images/`
- ✅ **Graphics**: Stored in `assets/graphics/`
- ✅ **X-post GFX renders**: Stored in `assets/gfx/xpost/` (full-frame PNG, `_key.png` keying variant, `src/` archival originals)

**Generated Artifacts** (Export/Optional):
- ⚠️ **Scripts** (`scripts/` directory): Generated from database, NOT source files
- ⚠️ **Rundown markdown** (`rundown/*.md`): Optional export feature (not currently implemented)
- ⚠️ **info.md**: Reserved for future filesystem sync (currently database-only)

### Important Distinctions

| Item | Source of Truth | Filesystem Role |
|------|----------------|-----------------|
| Episode metadata | PostgreSQL `episodes` table | Reserved for future export (`info.md`) |
| Rundown content | PostgreSQL `rundown_items.script_content` | Generated artifacts only (`scripts/`, `rundown/`) |
| Media assets | Filesystem (`assets/`) | Primary storage location |
| vMix projects | Filesystem (`projects/`) | Production software files |

**⚠️ WARNING**: Do NOT edit generated script files or rundown markdown files. Changes will be overwritten on next generation. Edit content in the database via the Show-Build UI.

---

## Authority & Enforcement

This document defines the **ONLY** acceptable directory structure and naming conventions for **media asset storage** in the Show-Build system.

**Canonical Source of Truth for Content**: PostgreSQL database
**Canonical Source of Truth for Media**: `/mnt/sync/disaffected/episodes/{EPISODE}/assets/`

### Principles

1. **Database is Canonical for Content**: Episode metadata, rundowns, and script content live in PostgreSQL
2. **Filesystem is Canonical for Media**: Video, audio, images, and graphics stored in `assets/` directory
3. **Google Drive is Mirror/Archive**: Google Drive serves as backup and archive, mirroring local structure
4. **Database Generates Files**: Scripts and rundown exports are **generated artifacts**, not source files
5. **Structure is Enforced**: Show-Build will not create non-compliant structures
6. **Manual Creation Prohibited**: Unless explicitly directed by admin, directories are created by Show-Build only

### Enforcement

- All file operations MUST conform to this standard
- Show-Build creates episodes using the blueprint defined here
- Consolidation tools normalize existing content to match
- Custodian scripts validate and fix compliance
- Non-compliant structures will be flagged and reported

---

## Complete Directory Tree

```
/mnt/sync/disaffected/episodes/{EPISODE}/          # e.g., 0244
│
├── info.md                                         # Episode metadata (REQUIRED)
├── {EPISODE}-rundown.json                         # Master rundown metadata
│
├── projects/                                       # Production software project files
│   ├── {EPISODE}.vmix                             # vMix project file
│   │
│   ├── teasers/                                   # Guest teaser projects
│   │   ├── {EPISODE}-teaser-{guestname}/
│   │   │   ├── {EPISODE}-teaser-{guestname}.aep
│   │   │   └── source/
│   │   │       └── (production media for this teaser)
│   │   │
│   │   └── {EPISODE}-teaser-{guestname2}/
│   │       ├── {EPISODE}-teaser-{guestname2}.aep
│   │       └── source/
│   │
│   └── graphics/                                  # Other After Effects projects
│       ├── {EPISODE}-titlecard/
│       │   ├── {EPISODE}-titlecard.aep
│       │   └── source/
│       │
│       └── {EPISODE}-custom-graphic/
│           ├── {EPISODE}-custom-graphic.aep
│           └── source/
│
├── captures/                                       # Raw vMix recordings
│   ├── orig/                                       # Original full-resolution recordings
│   │   ├── BLOCK-A.mov
│   │   ├── BLOCK-B.mov
│   │   ├── BLOCK-B2.mov                           # If recording interrupted
│   │   ├── BLOCK-C.mov
│   │   ├── BREAK-1.mov
│   │   └── BREAK-2.mov
│   └── preview/                                    # Lightweight preview/proxy versions
│       ├── BLOCK-A.mp4
│       ├── BLOCK-B.mp4
│       └── ...
│
├── thumbnails/                                     # Master artwork sources
│   ├── master-16x9.psd                            # Photoshop master (widescreen)
│   ├── master-16x9.png                            # High-res PNG (3840x2160)
│   ├── master-square.psd                          # Photoshop master (podcast)
│   └── master-square.png                          # High-res PNG (3000x3000)
│
├── assets/                                         # Final production assets
│   ├── video/
│   │   ├── 010-intro-clip.mp4
│   │   ├── 050-guest-teaser.mp4                  # Rendered from AE project
│   │   └── 090-outro-clip.mp4
│   │
│   ├── images/
│   │   ├── 020-title-card.png
│   │   └── 070-background.jpg
│   │
│   ├── audio/
│   │   └── 030-intro-music.mp3
│   │
│   ├── graphics/
│   │   ├── quotes/                               # Full-screen quote graphics
│   │   └── 040-lower-third.png
│   │
│   └── gfx/
│       └── xpost/                                # Rendered X-post tweet cards
│           ├── 020-@handle-12345678.png          #   full frame (gathered)
│           ├── 020-@handle-12345678_key.png      #   alpha key for vMix
│           └── src/{AssetID}/                    #   archival avatar/media originals
│
├── rundown/                                        # Rundown organization
│   └── media-list/                                # vMix playlist (symlinks)
│       ├── 010-010-SOT-{slug}-{AssetID}.mp4      # item 010, cue 010
│       ├── 010-020-GFX-{slug}-{AssetID}.png      # item 010, cue 020
│       ├── 020-030-IMG-{slug}-{AssetID}.jpg      # item 020, cue 030
│       └── ...
│
├── scripts/                                        # Generated script versions
│   ├── versions/                                  # Timestamped versions
│   │   ├── {YYYYMMDD_HHMMSS}/                    # e.g., 20251012_143000/
│   │   │   ├── host-hardcopy.pdf
│   │   │   ├── host-teleprompter.html
│   │   │   ├── director-script.html
│   │   │   ├── media-list.txt
│   │   │   ├── flat-text.txt
│   │   │   └── source.md
│   │   │
│   │   ├── 20251013_091500/
│   │   │   └── ...
│   │   │
│   │   └── 20251013_150000/                      # Latest version
│   │       └── ...
│   │
│   └── current/                                   # Symlinks to latest
│       ├── host-hardcopy.pdf → ../versions/{latest}/host-hardcopy.pdf
│       ├── host-teleprompter.html → ../versions/{latest}/host-teleprompter.html
│       ├── director-script.html → ../versions/{latest}/director-script.html
│       ├── media-list.txt → ../versions/{latest}/media-list.txt
│       ├── flat-text.txt → ../versions/{latest}/flat-text.txt
│       └── source.md → ../versions/{latest}/source.md
│
├── preshow/                                        # Preshow preparation materials
│   └── (notes, research, planning documents)
│
└── exports/                                        # Distribution-ready content
    ├── {EPISODE}-A.mp4                            # Block A video
    ├── {EPISODE}-A.mp3                            # Block A audio (192kbps)
    ├── {EPISODE}-B.mp4
    ├── {EPISODE}-B.mp3
    ├── {EPISODE}-C.mp4
    ├── {EPISODE}-C.mp3
    ├── {EPISODE}.mp4                              # Full episode video
    ├── {EPISODE}.mp3                              # Full episode audio
    ├── {EPISODE}.srt                              # Subtitles
    ├── {EPISODE}-poster-16x9.png                  # 1920x1080
    ├── {EPISODE}-poster-16x9-web.png              # 1280x720 (YouTube/Rumble)
    ├── {EPISODE}-poster-square.png                # 3000x3000 (podcasts)
    ├── {EPISODE}-poster-square-small.png          # 1400x1400
    ├── {EPISODE}-poster-vertical.png              # 1080x1920 (Instagram/TikTok)
    └── {EPISODE}-poster-facebook.png              # 1080x1080
```

---

## Root Level Files

### `info.md`

**Purpose**: Episode metadata
**Format**: Markdown with YAML frontmatter
**Location**: `{EPISODE}/info.md`
**⚠️ STATUS**: **RESERVED FOR FUTURE USE** - Currently database-only

### Database-First Architecture Note

**🚨 CRITICAL**: Episode metadata is stored in the **database**, not `info.md`:
- **Source of Truth**: Database table `episodes` (title, air_date, duration, status, etc.)
- **Current State**: `info.md` is generated by episode scaffold but **not actively read**
- **Future Feature**: Bidirectional sync between database and `info.md` (planned, not implemented)
- **Edit Location**: Use Show-Build UI to edit episode metadata in database

**Structure** (for reference/future implementation):
```yaml
---
episode: "0244"
episode_asset_id: "EPSMEEJ32D9UFK5BU"
title: "Episode Title"
air_date: "2025-10-12"
duration: "01:32:45"
status: "production"
---

# Episode 0244: Episode Title

Episode description and notes...
```

**Fields** (currently database-only):
- `episode`: 4-digit episode number (from `episodes.episode_number`)
- `episode_asset_id`: Server-generated AssetID (from `episodes.asset_id`)
- `title`: Episode title (from `episodes.title`)
- `air_date`: YYYY-MM-DD format (from `episodes.air_date`)
- `duration`: HH:MM:SS format (from `episodes.duration_formatted`)
- `status`: draft, production, completed, archived (from `episodes.status`)

### `{EPISODE}-rundown.json`

**Purpose**: Complete rundown metadata (regions, items, cues)
**Format**: JSON
**Location**: `{EPISODE}/{EPISODE}-rundown.json`
**Example**: `0244/0244-rundown.json`

**Structure**: See [Rundown Folder](#rundown-folder) section

---

## Projects Folder

**Purpose**: Production software project files
**Location**: `{EPISODE}/projects/`

### Main vMix Project

**File**: `{EPISODE}.vmix`
**Location**: `projects/{EPISODE}.vmix`
**Example**: `projects/0244.vmix`

### Teaser Projects

**Purpose**: Guest interview teaser After Effects projects
**Location**: `projects/teasers/{EPISODE}-teaser-{guestname}/`
**Naming**: Guest name lowercase, hyphens (e.g., `johndoe`, `sarah-smith`)

**Structure**:
```
projects/teasers/0244-teaser-sarahsmith/
├── 0244-teaser-sarahsmith.aep       # After Effects project
└── source/                           # Production media
    ├── interview-raw.mp4
    ├── guest-headshot.png
    ├── background.jpg
    └── show-logo.png
```

**Workflow**:
1. Copy master teaser template from shared media assets
2. Create episode-specific folder with guest name
3. Place source media in `source/` subdirectory
4. Customize After Effects project
5. Render to `assets/video/{NNN}-{guestname}-teaser.mp4`

### Graphics Projects

**Purpose**: Other After Effects projects (title cards, custom graphics)
**Location**: `projects/graphics/{EPISODE}-{type}/`

**Examples**:
```
projects/graphics/0244-titlecard/
projects/graphics/0244-lower-thirds/
projects/graphics/0244-end-credits/
```

**Same structure as teasers**:
- AE project file: `{EPISODE}-{type}.aep`
- Source media: `source/` subdirectory

### Future Projects

The `projects/` folder is extensible for other production software:
- DaVinci Resolve projects (`.drp`)
- Premiere Pro projects (`.prproj`)
- Other production tools

**Naming Convention**: `{EPISODE}-{project-type}.{ext}`

---

## Captures Folder

**Purpose**: Raw vMix recording captures (unedited)
**Location**: `{EPISODE}/captures/`

### Subdirectory Organization

Captures are organized into two subdirectories:

| Directory | Purpose |
|-----------|---------|
| `captures/orig/` | Original raw recordings directly from vMix — never modified |
| `captures/preview/` | Preview/proxy copies for quick review (lower bitrate, smaller files) |

All raw captures go into `orig/`. Preview copies (if generated) go into `preview/` using the same filename.

### Block Recordings

**Format**: `BLOCK-{LETTER}.mov`
**Examples**:
```
BLOCK-A.mov
BLOCK-B.mov
BLOCK-C.mov
```

**Interrupted Recordings**:
If recording is interrupted and restarted, append number:
```
BLOCK-B.mov       # First attempt
BLOCK-B2.mov      # Resumed after interruption
BLOCK-B3.mov      # If interrupted again
```

**During editing**, interrupted blocks are merged into single export file.

### Break Recordings

**Format**: `BREAK-{N}.mov`
**Examples**:
```
BREAK-1.mov
BREAK-2.mov
```

### File Format

- **Container**: QuickTime `.mov` (from vMix)
- **Codec**: H.264 or ProRes
- **Quality**: High bitrate for editing

**Important**: Captures are RAW recordings, not for distribution. Final edited versions go in `exports/`.

---

## Thumbnails Folder

**Purpose**: Master artwork source files for episode thumbnails/posters
**Location**: `{EPISODE}/thumbnails/`

### Master Files

#### 16:9 Widescreen (Video Platforms)
- `master-16x9.psd` - Photoshop source (layered)
- `master-16x9.png` - High-res PNG export (3840x2160 or 4K)

**Use**: YouTube, Rumble, video platforms

#### 1:1 Square (Podcast Platforms)
- `master-square.psd` - Photoshop source (layered)
- `master-square.png` - High-res PNG export (3000x3000)

**Use**: Apple Podcasts, Spotify, podcast platforms

### Design Notes

- **Two separate masters required**: 16:9 and 1:1 need different compositions (not just cropped)
- **PSD files**: Editable source for future changes
- **PNG files**: High-resolution exports for generating distribution formats
- **No distribution files here**: Final export formats go in `exports/` folder

### Distribution Format Generation

From these masters, Show-Build generates all required formats:
- 1920x1080 (high-quality 16:9)
- 1280x720 (YouTube/Rumble optimized)
- 3000x3000 (Apple Podcasts/Spotify)
- 1400x1400 (podcast minimum)
- 1080x1920 (Instagram/TikTok vertical)
- 1080x1080 (Facebook square)

**See**: [Exports Folder - Thumbnails](#thumbnails) for distribution formats

---

## Assets Folder

**Purpose**: Final production assets used in show (referenced in rundown cues)
**Location**: `{EPISODE}/assets/`

### Organization

Assets are organized by type:
```
assets/
├── video/
├── images/
├── audio/
└── graphics/
```

### Naming Convention

**Without AssetID** (temporary):
```
{NNN}-{slug}.{ext}
```
- `{NNN}`: 3-digit order number (010, 020, 030...)
- `{slug}`: Descriptive name (lowercase, hyphens)
- `{ext}`: File extension

**With AssetID** (permanent):
```
AST_{ASSETID}_{NNN}-{slug}.{ext}
```
- Prefix with `AST_` + AssetID from database
- Preserves original order/slug for readability

**Examples**:
```
assets/video/010-intro-clip.mp4
assets/video/AST_MEDABC123XYZ_050-guest-teaser.mp4
assets/images/020-title-card.png
assets/audio/030-intro-music.mp3
assets/graphics/040-lower-third.png
```

### Asset Types

#### Video (`assets/video/`)
- Edited video clips
- Rendered teasers from After Effects
- B-roll footage
- Stock video

**Formats**: `.mp4` (preferred), `.mov`

#### Images (`assets/images/`)
- Photos
- Screenshots
- Still graphics
- Backgrounds

**Formats**: `.png` (preferred for graphics), `.jpg` (photos)

#### Audio (`assets/audio/`)
- Music beds
- Sound effects
- Voice overs
- Audio clips

**Formats**: `.mp3`, `.wav`

#### Graphics (`assets/graphics/`)
- Lower thirds
- Overlays
- Animated graphics (exported frames)
- Title cards

**Subdirectories**:
- `quotes/` - Full-screen quote graphics (FSQ cue type)

**Formats**: `.png` (with transparency)

### Important Distinctions

**Production Assets vs Final Assets**:
- `projects/{type}/source/` = Production files (used to BUILD things)
- `assets/` = Final outputs (used IN the show)

**Example**:
- Production: `projects/teasers/0244-teaser-sarahsmith/source/interview-raw.mp4`
- Final: `assets/video/050-sarah-teaser.mp4` (rendered output)

---

## Rundown Folder

**Purpose**: Media playlist generation for vMix production workflow
**Location**: `{EPISODE}/rundown/`
**⚠️ STATUS**: **CURRENT**: media-list/ only; **FUTURE**: Optional rundown markdown export

### Database-First Architecture Note

**🚨 CRITICAL**: Rundown content lives in the **database**, not filesystem:
- **Source of Truth**: Database tables `rundowns` and `rundown_items`
- **Current Implementation**: Only `media-list/` folder is actively used (vMix playlists)
- **Future Feature**: Individual rundown item markdown files (`rundown/*.md`) will be optional exports
- **Edit Location**: Use Show-Build UI to edit rundown content in database

### Structure

```
rundown/
├── media-list/           # ✅ CURRENT: vMix playlist (symlinks to assets)
│   ├── 010-010-SOT-...
│   ├── 010-020-GFX-...
│   └── ...
│
└── (future: *.md files)  # ⚠️ FUTURE: Optional export of rundown items as markdown
```

### Media List

**Location**: `rundown/media-list/`
**Purpose**: Flat enumerated list of symlinks for vMix playlist loading
**Format**: Symlinks to actual media files in `assets/`

**Naming Convention**:
```
{parent-item}-{cue-order}-{CUE_TYPE}-{slug}-{AssetID}.{ext}
```

**Components**:
- `{parent-item}`: Rundown item this cue belongs to (010, 020, 030...)
- `{cue-order}`: Playback order (continues incrementing, does NOT restart per item)
- `{CUE_TYPE}`: SOT, GFX, IMG, FSQ, VO, NAT, PKG, etc.
- `{slug}`: Descriptive name
- `{AssetID}`: Database AssetID (e.g., CUEMEEFALU37XGFSZ)
- `{ext}`: File extension

**Examples**:
```
010-010-SOT-cold-open-CUEMEEFALU37XGFSZ.mp4 → ../../assets/video/010-cold-open.mp4
010-020-GFX-title-card-CUEGFX789XYZ123.png → ../../assets/graphics/020-title.png
020-030-IMG-background-CUEIMG012JKL345.jpg → ../../assets/images/030-bg.jpg
030-040-SOT-interview-CUESOT456GHI789.mp4 → ../../assets/video/040-interview.mp4
030-050-GFX-lower-third-CUEGFXABC789.png → ../../assets/graphics/050-lower.png
```

**Interpretation**:
- `010-010-SOT-...` = Rundown item 010, cue 010, SOT type
- `010-020-GFX-...` = Rundown item 010, cue 020, GFX type
- `020-030-IMG-...` = Rundown item 020, cue 030, IMG type
- `030-040-SOT-...` = Rundown item 030, cue 040, SOT type (continuous numbering)

### vMix Workflow

1. Open `rundown/media-list/` folder in vMix
2. Load all symlinks into playlist
3. Files appear in numerical order (010, 020, 030...)
4. Press play - show runs sequentially

### Rundown JSON Structure

**Location**: `{EPISODE}/{EPISODE}-rundown.json`

**Purpose**: Complete rundown metadata including:
- Regions (BLOCK-A, BREAK-1, BLOCK-B, etc.)
- Rundown items (segments, ads, coldopen, tease, etc.)
- Cues (actual media elements)
- Media metadata for vMix template selection

**Structure**:
```json
{
  "episode": "0244",
  "episode_asset_id": "EPSMEEJ32D9UFK5BU",
  "title": "Episode Title",
  "air_date": "2025-10-12",
  "duration": "01:32:45",

  "regions": [
    {
      "type": "BLOCK-A",
      "start_time": "00:00:00",
      "end_time": "00:25:30",
      "rundown_items": [10, 20, 30]
    },
    {
      "type": "BREAK-1",
      "start_time": "00:25:30",
      "end_time": "00:28:00",
      "rundown_items": [40]
    }
  ],

  "rundown_items": [
    {
      "order": 10,
      "asset_id": "SEGMGJ8N04M7ZXXXA",
      "type": "COLDOPEN",
      "slug": "intro",
      "title": "Cold Open",
      "duration": "00:00:45",
      "region": "BLOCK-A",
      "cues": [10, 20]
    },
    {
      "order": 20,
      "asset_id": "SEGMGJTEASE12345",
      "type": "TEASE",
      "slug": "upcoming",
      "title": "Coming Up",
      "duration": "00:00:15",
      "region": "BLOCK-A",
      "cues": [30]
    }
  ],

  "cues": [
    {
      "order": 10,
      "parent_item": 10,
      "asset_id": "CUEMEEFALU37XGFSZ",
      "cue_type": "SOT",
      "slug": "cold-open",
      "duration": "00:00:45",
      "file": "rundown/media-list/010-010-SOT-cold-open-CUEMEEFALU37XGFSZ.mp4",
      "media": {
        "resolution": "1920x1080",
        "aspect_ratio": "16:9",
        "codec": "h264",
        "bitrate": "5000kbps"
      },
      "vmix_template": "standard-fullscreen"
    },
    {
      "order": 20,
      "parent_item": 10,
      "asset_id": "CUEGFX789XYZ123",
      "cue_type": "GFX",
      "slug": "title-card",
      "duration": "00:00:05",
      "file": "rundown/media-list/010-020-GFX-title-card-CUEGFX789XYZ123.png",
      "vmix_template": "graphic-overlay"
    },
    {
      "order": 30,
      "parent_item": 20,
      "asset_id": "CUEIMG012JKL345",
      "cue_type": "IMG",
      "slug": "background",
      "duration": "00:00:15",
      "file": "rundown/media-list/020-030-IMG-background-CUEIMG012JKL345.jpg"
    }
  ]
}
```

### Hierarchy Explanation

```
Show (Disaffected)
└── Episode (0244)
    └── Regions (calculated dynamically)
        ├── BLOCK-A
        │   ├── Rundown Item 010-COLDOPEN
        │   │   ├── Cue 010-SOT
        │   │   └── Cue 020-GFX
        │   └── Rundown Item 020-TEASE
        │       └── Cue 030-IMG
        │
        ├── BREAK-1
        │   └── Rundown Item 040-AD
        │       └── Cue 040-SOT
        │
        └── BLOCK-B
            └── Rundown Item 050-SEG
                ├── Cue 050-SOT
                └── Cue 060-GFX
```

**Regions**:
- Calculated in real-time by Show-Build
- Based on rundown item sequence
- BLOCK, BREAK patterns
- Not physically stored, just logical grouping

**Rundown Items**:
- Stored in database only
- Enumerated by 10s (010, 020, 030...)
- Types: segment, coldopen, ad, promo, tease, reader, interview, break

**Cues**:
- Actual playable media elements
- Enumerated by 10s (010, 020, 030... continuous, no restart)
- Types: SOT, GFX, IMG, FSQ, VO, NAT, PKG, VOX, MUS, LIVE
- Each cue references parent_item

### Cue Types

**Media Cues**:
- `SOT` - Sound on Tape (video clip)
- `IMG` - Image
- `GFX` - Graphics
- `FSQ` - Full Screen Quote
- `VO` - Voice Over
- `NAT` - Natural sound
- `PKG` - Package (edited segment)
- `VOX` - Vox pop
- `MUS` - Music
- `LIVE` - Live feed

**Production Cues** (database only, not files):
- `CAMERA` - Camera cue
- `AUDIO_MIC` - Audio/microphone cue
- `LIGHTING` - Lighting cue
- `DIRECTOR` - Director note
- `TALENT` - Talent cue

---

## Scripts Folder

**Purpose**: Generated script versions in multiple formats
**Location**: `{EPISODE}/scripts/`
**⚠️ STATUS**: **GENERATED ARTIFACTS ONLY** - Scripts are generated from database, NOT source files

### Important: Database-Generated Content

**🚨 CRITICAL**: All scripts in this folder are **automatically generated** from the PostgreSQL database:
- **Source of Truth**: Database table `rundown_items.script_content`
- **Generation Trigger**: Manual or automatic script generation commands
- **DO NOT EDIT**: Manual edits to these files will be **lost** on next generation
- **Edit Location**: Use Show-Build UI to edit rundown content in database

### Structure

```
scripts/
├── versions/                       # All timestamped versions
│   ├── {YYYYMMDD_HHMMSS}/
│   │   ├── host-hardcopy.pdf
│   │   ├── host-teleprompter.html
│   │   ├── director-script.html
│   │   ├── media-list.txt
│   │   ├── flat-text.txt
│   │   └── source.md
│   │
│   ├── 20251013_091500/
│   │   └── ...
│   │
│   └── 20251013_150000/           # Latest
│       └── ...
│
└── current/                        # Symlinks to latest
    ├── host-hardcopy.pdf → ../versions/20251013_150000/host-hardcopy.pdf
    ├── host-teleprompter.html → ../versions/20251013_150000/host-teleprompter.html
    ├── director-script.html → ../versions/20251013_150000/director-script.html
    ├── media-list.txt → ../versions/20251013_150000/media-list.txt
    ├── flat-text.txt → ../versions/20251013_150000/flat-text.txt
    └── source.md → ../versions/20251013_150000/source.md
```

### Script Formats

#### 1. Host Hardcopy (`host-hardcopy.pdf`)
**Purpose**: Printed script for host to read from
**Format**: PDF, paginated
**Features**:
- Page numbers
- Host-only content (no production cues)
- Clear formatting for reading
- Optimized for printing

#### 2. Host Teleprompter (`host-teleprompter.html`)
**Purpose**: Scrolling teleprompter display
**Format**: HTML
**Features**:
- Large, readable font
- Distinct styling for read vs cue content
- Named anchors for jumping (`#coldopen`, `#segment1`, etc.)
- Optimized for scrolling

#### 3. Director Script (`director-script.html`)
**Purpose**: Director's production view
**Format**: HTML
**Features**:
- All production cues visible
- Camera cues, lighting notes
- Timecodes
- Media references
- Complete rundown view

#### 4. Media List (`media-list.txt`)
**Purpose**: Pre-flight checklist
**Format**: Plain text
**Contents**:
- Enumerated list of all media/cues
- File paths
- Durations
- Verification checklist

#### 5. Flat Text (`flat-text.txt`)
**Purpose**: LLM processing, word counting, analysis
**Format**: Plain text, no formatting
**Contents**:
- Script text only
- No markup, no formatting
- Clean for text analysis

#### 6. Source Markdown (`source.md`)
**Purpose**: Neutral backup format
**Format**: Markdown
**Contents**:
- Complete script with minimal markup
- Human-readable
- Version control friendly

### Versioning

**Timestamp Format**: `YYYYMMDD_HHMMSS`
**Examples**:
```
20251012_143000   # October 12, 2025 at 2:30:00 PM
20251013_091500   # October 13, 2025 at 9:15:00 AM
```

**Version Creation**:
- New timestamped folder for each script generation
- All 6 formats generated together
- Old versions preserved (never deleted)
- Audit trail of all script changes

**Current Folder**:
- Symlinks always point to latest version
- Easy access to "the" script
- Tools can read from `current/` without knowing timestamp

### Generation Workflow

**Single Source of Truth**: Database (Show-Build app)

**Script Generation Process**:
1. Host develops content in Show-Build Scratch feature
2. Content promoted to structured rundown items
3. User triggers script generation
4. Show-Build generates all 6 formats from database
5. Creates timestamped folder in `versions/`
6. Updates `current/` symlinks

**Regeneration**:
- Edit content in database
- Regenerate → new timestamped version
- Old versions preserved for history

---

## Preshow Folder

**Purpose**: Preshow preparation materials and planning documents
**Location**: `{EPISODE}/preshow/`

### Contents

This directory holds preshow preparation materials:
- Research notes and links
- Guest briefings and background information
- Topic outlines and talking points
- Planning documents
- Reference materials collected during episode preparation

### Usage Notes

- **Optional directory** - Not required for every episode
- **Human-managed content** - Unlike scripts/, this folder contains manually created materials
- **Pre-production focus** - Used during episode planning before production begins
- Files here are for reference during production, not for automated processing

### Preshow Folder (Legacy Note)

**Status**: ⚠️ Being phased out

Previously, the `preshow/` folder contained:
- Host's unstructured notes
- Google Docs exports
- Brainstorming content

**Now**: Host uses Show-Build Scratch feature internally
- All content stays in database
- No external files needed
- Structured from the start

**Migration**: Existing `preshow/` folders will be processed and removed during consolidation

---

## Exports Folder

**Purpose**: Distribution-ready content (final deliverables)
**Location**: `{EPISODE}/exports/`

### Block Videos

**Format**: `{EPISODE}-{LETTER}.mp4`

**Examples**:
```
0244-A.mp4     # Block A finalized video
0244-B.mp4     # Block B finalized video
0244-C.mp4     # Block C finalized video
```

**Details**:
- Edited/finalized versions (not raw captures)
- If raw capture was interrupted (BLOCK-B.mov + BLOCK-B2.mov), final export is merged: `0244-B.mp4`
- Container: MP4 (H.264)
- Resolution: 1920x1080
- Bitrate: 5000kbps or higher

### Block Audio

**Format**: `{EPISODE}-{LETTER}.mp3`

**Examples**:
```
0244-A.mp3
0244-B.mp3
0244-C.mp3
```

**Details**:
- Extracted from video
- Bitrate: 192kbps
- Stereo
- One audio file for each video block

### Full Episode

**Video**: `{EPISODE}.mp4`
**Audio**: `{EPISODE}.mp3`

**Examples**:
```
0244.mp4       # Complete episode (all blocks + breaks merged)
0244.mp3       # Complete episode audio
```

**Details**:
- Full episode is all blocks + breaks stitched together
- Video: MP4, 1920x1080, H.264
- Audio: MP3, 192kbps, stereo

### Subtitles

**Format**: `{EPISODE}.srt`

**Example**: `0244.srt`

**Details**:
- SubRip format (.srt)
- English language
- Full episode only (not per-block)
- May support additional formats in future (.vtt, .sub)

### Thumbnails

Distribution-ready thumbnail formats for various platforms:

#### High-Quality 16:9
**File**: `{EPISODE}-poster-16x9.png`
**Dimensions**: 1920x1080
**Use**: General high-quality widescreen

#### YouTube/Rumble Optimized
**File**: `{EPISODE}-poster-16x9-web.png`
**Dimensions**: 1280x720
**Size**: Under 2MB
**Use**: YouTube, Rumble video thumbnails

#### Podcast Platforms (Large)
**File**: `{EPISODE}-poster-square.png`
**Dimensions**: 3000x3000
**Size**: Under 500KB
**Use**: Apple Podcasts, Spotify

#### Podcast Platforms (Small)
**File**: `{EPISODE}-poster-square-small.png`
**Dimensions**: 1400x1400
**Use**: Minimum size for podcast platforms

#### Instagram/TikTok Vertical
**File**: `{EPISODE}-poster-vertical.png`
**Dimensions**: 1080x1920 (9:16)
**Use**: Instagram Stories, TikTok, vertical video

#### Facebook Square
**File**: `{EPISODE}-poster-facebook.png`
**Dimensions**: 1080x1080
**Use**: Facebook posts, square format

### Thumbnail Generation

**Source**: `thumbnails/master-16x9.psd` and `thumbnails/master-square.psd`

**Process**:
1. Designer creates masters in `thumbnails/` folder
2. Show-Build generates all 6 distribution formats
3. Exports to `exports/` folder with platform-specific optimization
4. Respects file size limits (2MB for video platforms, 500KB for podcasts)

---

## Naming Conventions

### Episode Numbers

**Format**: `{NNNN}` (4 digits, zero-padded)

**Examples**:
- `0001`
- `0244`
- `1234`

**Invalid**:
- `1` (not zero-padded)
- `244` (not 4 digits)
- `ep0244` (no prefix)

### AssetIDs

**Format**: 17-character alphanumeric (uppercase)

**Examples**:
- Episodes: `EPSMEEJ32D9UFK5BU`
- Segments: `SEGMGJ8N04M7ZXXXA`
- Cues: `CUEMEEFALU37XGFSZ`
- Ads: `ASTMEEFD8AX520WY1`

**Generation**: Server-generated via `/newAssetID` endpoint

**Usage**: Included in filenames for traceability

### Block Recordings

**Captures**: `BLOCK-{LETTER}.mov`
- Letters: A, B, C, D, etc. (uppercase)
- Interrupted: Append number (BLOCK-B2.mov)

**Exports**: `{EPISODE}-{LETTER}.mp4`
- Example: `0244-A.mp4`

### Break Recordings

**Captures**: `BREAK-{N}.mov`
- Numbers: 1, 2, 3, etc. (no zero-padding)

**Exports**: TBD (workflow still being defined)

### Guest Names

**Format**: Lowercase, hyphens for spaces

**Examples**:
- `johndoe`
- `sarah-smith`
- `mary-jane-watson`

**Usage**: Teaser project folders, asset slugs

### Slugs

**Format**: Lowercase, hyphens, descriptive

**Examples**:
- `cold-open`
- `main-interview`
- `guest-teaser`
- `lower-third`

**Invalid**:
- Spaces: `cold open` ❌
- CamelCase: `ColdOpen` ❌
- Underscores: `cold_open` ❌ (use hyphens)

### Timestamps

**Format**: `YYYYMMDD_HHMMSS`

**Examples**:
- `20251012_143000` (Oct 12, 2025, 2:30 PM)
- `20251013_091500` (Oct 13, 2025, 9:15 AM)

**Usage**: Script version folders

---

## Hierarchy & Relationships

### Content Hierarchy

```
Show (Disaffected)
└── Episode (AssetID: EPSMEEJ32D9UFK5BU)
    └── Regions (calculated dynamically)
        ├── BLOCK-A
        ├── BREAK-1
        ├── BLOCK-B
        └── BREAK-2
            └── Rundown Items (enumerated by 10s)
                ├── 010-COLDOPEN
                ├── 020-TEASE
                ├── 030-SEG
                └── 040-AD
                    └── Cues (enumerated by 10s, continuous)
                        ├── 010-SOT (media file)
                        ├── 020-GFX (media file)
                        ├── 030-IMG (media file)
                        └── 040-SOT (media file)
```

### Storage Locations

**Database** (Single Source of Truth):
- Episode metadata
- Rundown items
- Cues
- All content and relationships

**Files** (Generated from Database):
- Scripts (6 formats)
- Rundown JSON
- Media list symlinks

**Physical Media**:
- Captures (raw recordings)
- Assets (final media)
- Exports (distribution files)
- Thumbnails (artwork)

### Relationships

**Episode ← → Rundown Items**:
- One episode has many rundown items
- Each item belongs to one episode

**Rundown Items ← → Cues**:
- One item has many cues
- Each cue belongs to one item
- Referenced via `parent_item` field

**Cues ← → Assets**:
- Each cue references one asset file
- Assets may be reused across episodes

**Projects ← → Assets**:
- After Effects projects render to assets
- Source media in `projects/{type}/source/`
- Output in `assets/{type}/`

---

## Validation & Enforcement

### Validation API

**Endpoint**: `GET /api/episodes/{episode}/validate`

**Checks**:
- ✅ Episode directory exists
- ✅ All REQUIRED directories present
- ✅ `info.md` exists and has valid YAML
- ✅ All files follow naming conventions
- ✅ No forbidden directories (`.claude`, `.blackmagicsync-v2`, `temporary-files`, etc.)
- ✅ No invalid characters in filenames
- ✅ Symlinks in `rundown/media-list/` are valid
- ✅ Referenced assets exist

**Response**:
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "No full episode video found in exports/",
    "No subtitle file present"
  ]
}
```

### Auto-Normalization

**Endpoint**: `POST /api/episodes/{episode}/normalize`

**Actions**:
- Create missing REQUIRED directories
- Rename files to match conventions
- Move misplaced files to correct locations
- Fix invalid characters
- Generate missing `info.md` template
- Rebuild symlinks in `rundown/media-list/`

**Dry Run**: `POST /api/episodes/{episode}/normalize?dry_run=true`
- Returns preview of changes without executing

### Custodian Script

**Purpose**: Automated validation and cleanup
**Schedule**: Run weekly or on-demand
**Actions**:
- Scan all episodes for compliance
- Generate compliance report
- Flag non-compliant files for review
- Auto-fix where safe
- Alert on critical issues

**CLI**: `python custodian.py --scan-all --auto-fix`

---

## Migration & Consolidation

### Existing Content

**Status**: Existing episodes violate this standard
**Approach**: Gradual migration during consolidation

### Migration Phases

**Phase 1: Assessment**
1. Run validation on all episodes
2. Generate compliance report
3. Categorize issues (auto-fixable vs manual)

**Phase 2: Automated Fixes**
1. Run auto-normalize (dry-run first)
2. Review proposed changes
3. Execute safe fixes

**Phase 3: Manual Review**
1. Address ambiguous files
2. Resolve naming conflicts
3. Handle special cases

**Phase 4: Verification**
1. Re-run validation
2. Confirm compliance
3. Sync to Google Drive

### Google Drive Consolidation

**See**: `/docs/GOOGLE_DRIVE_CONSOLIDATION.md` (if exists)

**Overview**:
1. Scan both local and Google Drive
2. Compare file inventories
3. Identify duplicates and conflicts
4. Consolidate to local canonical structure
5. Mirror to Google Drive
6. Archive old episodes (4+ weeks)

**Retention Policy**:
- Weeks 0-4: Active in `/episodes/{EPISODE}/` (mirrored to Drive)
- Week 5+: Archived to `/Archive/{EPISODE}/` in Drive only

---

## Required vs Optional Components

### REQUIRED (Every Episode)

✅ `info.md` - Episode metadata file
✅ `projects/` - Directory (even if only vMix project)
✅ `captures/` - Directory (even if empty initially)
✅ `thumbnails/` - Directory with at least master files
✅ `assets/` - Directory with subdirectories (video, images, audio, graphics)
✅ `rundown/` - Directory
✅ `scripts/` - Directory
✅ `exports/` - Directory

### OPTIONAL (May Exist)

⚪ `{EPISODE}.vmix` - vMix project (in projects/)
⚪ `projects/teasers/` - Guest teaser projects
⚪ `projects/graphics/` - Custom graphics projects
⚪ Block recordings in `captures/` - May not exist yet
⚪ `{EPISODE}-rundown.json` - Generated when rundown is ready
⚪ `rundown/media-list/` - Generated from database
⚪ Script versions - Generated on demand
⚪ `exports/{EPISODE}.mp4` - Full episode (created after editing)
⚪ `exports/{EPISODE}.srt` - Subtitles (if created)
⚪ `preshow/` - Preshow preparation materials (notes, research, planning)

### FORBIDDEN (Must Never Exist)

❌ `.claude/` - Claude workspace directories
❌ `.blackmagicsync-v2/` - Sync metadata
❌ `temporary-files/` - Temp files
❌ `growing-temporary-files/` - Temp files
❌ `sync-*/` - Sync folders
❌ `New folder/` - Unnamed directories
❌ Files with trailing/leading spaces
❌ Files with non-ASCII characters (unless intentional)

---

## Directory Creation Blueprint

When Show-Build creates a new episode directory:

```bash
# Root level
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}
touch /mnt/sync/disaffected/episodes/{EPISODE}/info.md

# Projects
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/projects
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/projects/teasers
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/projects/graphics

# Captures
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/captures/orig
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/captures/preview

# Thumbnails
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/thumbnails

# Assets
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/assets/video
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/assets/images
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/assets/audio
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/assets/graphics
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/assets/graphics/quotes

# Rundown
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/rundown
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/rundown/media-list

# Scripts
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/scripts/versions
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/scripts/current

# Preshow
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/preshow

# Exports
mkdir -p /mnt/sync/disaffected/episodes/{EPISODE}/exports
```

---

## Google Drive Sync Rules

### Active Episodes (0-4 weeks old)

**Location**: `/Production/TV Show/episodes/{EPISODE}/`
**Sync**: Bidirectional mirror of local Syncthing
**Structure**: MUST match local structure exactly
**Updates**: Real-time or scheduled sync

### Archived Episodes (5+ weeks old)

**Location**: `/Production/Archive/{EPISODE}/`
**Sync**: One-way upload from local
**Structure**: MUST match standard structure
**Local Storage**: MAY be deleted after successful archive verification

### Retention Configuration

**Default**: 4 weeks in active episodes folder
**Configurable**: Via Settings > Google Services > Archive After (weeks)
**Range**: 2-8 weeks

### Sync Exclusions

**Never sync**:
- `.claude/` directories
- `.blackmagicsync-v2/` directories
- `temporary-files/` directories
- Any files > 5GB (handle separately)

---

## Document Maintenance

### Version Control

**Repository**: Show-Build Git repository
**Location**: `/docs/EPISODE_DIRECTORY_STANDARD.md`
**Branch**: `main`

### Change Process

1. Propose change via issue/PR
2. Team review and discussion
3. Update version number
4. Document changes in CHANGELOG
5. Announce breaking changes 2 weeks in advance
6. Merge and deploy

### Version History

- **v1.0** (2025-10-13): Initial specification

### Related Documentation

- `/docs/ASSETID_SYSTEM_GUIDE.md` - AssetID system reference
- `/docs/THUMBNAIL_GENERATION_RESEARCH.md` - Thumbnail automation research
- `/docs/GOOGLE_DRIVE_CONSOLIDATION.md` - File system consolidation strategy
- `/docs/RUNDOWN_SYSTEM.md` - Rundown structure and workflow
- `/UNIVERSAL_LLM_FRAMEWORK_UFDP.md` - Universal LLM Framework

---

## UFDP Index Tags

**Primary Tags**:
- `file-structure`
- `episode-organization`
- `canonical-standard`
- `directory-blueprint`

**Related Tags**:
- `naming-conventions`
- `asset-management`
- `rundown-structure`
- `script-generation`
- `thumbnail-system`
- `google-drive-sync`
- `validation`
- `normalization`

**Cross-References**:
- AssetID System
- Rundown Management
- Script Generation
- Thumbnail Automation
- Google Drive Integration

---

**END OF SPECIFICATION**

*This is the authoritative document for episode file organization in Show-Build.*
*All systems, tools, and workflows MUST conform to this standard.*
