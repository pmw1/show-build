# Episode Production Workflow

This document outlines the complete Show-Build production workflow for episodes, from initial content creation through recording session preparation.

## Overview

The Show-Build episode production workflow is designed to maintain consistency, quality, and efficiency throughout the content creation and production process. It leverages centralized path management, status-based filtering, automated episode initialization, and integrated tools to streamline the production pipeline.

## Quick Reference - Episode Creation to Recording

**Essential Commands & Endpoints:**
```bash
# 1. Create new episode (via API)
POST /episodes/create

# 2. Normalize rundown order/index after content changes
POST /rundown/{episode}/normalize

# 3. Calculate durations after content changes  
python3 /mnt/process/show-build/tools/duration_calculator.py --episode {episode}

# 4. Generate host script
python3 /mnt/process/show-build/tools/render-script-host.py {episode}

# 5. Collect media for vMix
python3 /mnt/process/show-build/tools/media-collect.py {episode}

# 6. Normalize audio (as needed)
ffmpeg -i "input.mp4" -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:v copy "output-2.mp4"
```

**Status Progression:** `draft` → `production` → Recording Ready

## Phase 1: Episode Initialization & Setup

### 1.1 Episode Creation via API

**Create new episode using the scaffolding endpoint:**

**API Endpoint:** `POST /episodes/create`

**Request Body:**
```json
{
  "episode_number": "0237",           // Optional - auto-generated if not provided
  "template_id": null,                // Optional - uses default template
  "title": "Episode Title",           // Optional - can be set later
  "description": "Episode description", // Optional
  "episode_metadata": {               // Optional - additional metadata
    "subtitle": "Episode Subtitle",
    "airdate": "2025-08-24",
    "host": "Joshua Slocum"
  }
}
```

**What this creates:**
```
/episodes/{episode_number}/
├── info.md                 # Auto-generated with metadata
├── assets/                # Media storage directories
│   ├── audio/
│   ├── graphics/
│   ├── images/
│   │   └── guest/
│   ├── quotes/
│   ├── unlinked/
│   └── video/
├── captures/              # Screen captures, recordings
├── distribute/            # Distribution outputs
├── exports/              # Generated scripts, exports
├── preshow/              # Pre-production materials
│   └── preshow notes.md  # Technical checklist template
├── rundown/              # Individual segment files
└── vmix/                 # vMix integration files
    └── list1/
```

**Generated `info.md` structure:**

The `info.md` file is automatically created with pre-populated frontmatter fields to minimize production workflow headaches. 

📖 **Complete Reference**: See [`docs/init-procedures/info.md`](init-procedures/info.md) for the definitive template and field explanations.

**Key Fields Initialized:**
- `AssetID`: Episode asset identifier (auto-generated)
- `episode_number`: Episode number (from request or auto-generated)
- `title`, `subtitle`: Episode titles (from `episode_metadata` or defaults)
- `airdate`: Scheduled air date (from `episode_metadata` or placeholder)
- `total_runtime`: Duration field (starts at `00:00:00:00`, updated by tools)
- `status`: Production status (always starts as `draft`)
- `type`: Episode type (defaults to `sunday_show`)
- `slug`: URL-friendly identifier (derived from title)
- `guest`, `tags`: Optional fields (start empty)

### 1.2 Alternative Episode Creation Methods

**Get next available episode number:**
```http
GET /episodes/next-number
```

**Validate episode number availability:**  
```http
GET /episodes/validate-number/0237
```

**List available blueprint templates:**
```http
GET /episodes/templates
```

### 1.3 Frontend Integration

**Show-Build UI Integration:**
- New episode creation is integrated into the Show-Build web interface
- Users can create episodes through the frontend which calls the API
- Episode management includes validation and template selection
- Real-time feedback on episode number availability

**Typical Frontend Workflow:**
1. Access episode creation interface in Show-Build UI
2. System suggests next available episode number  
3. User can override number or use suggested number
4. Optional: Select from available blueprint templates
5. Fill in episode metadata (title, subtitle, airdate, etc.)
6. Submit to create complete episode structure
7. Redirected to episode editor for content development

### 1.4 API vs Manual Creation

**API Method Benefits:**
- **Automated Structure**: Complete directory tree created automatically
- **Metadata Population**: `info.md` pre-populated with required fields  
- **Database Integration**: Episode record created in Show-Build database
- **Template System**: Consistent structure from proven blueprint templates
- **Validation**: Episode number validation prevents conflicts
- **AssetID Integration**: Proper integration with Show-Build AssetID system
- **Audit Trail**: Creation tracked with user and timestamp information

**Manual Method Drawbacks:**  
- **Inconsistent Structure**: Easy to miss directories or files
- **Missing Metadata**: `info.md` requires manual creation with all required fields
- **No Database Record**: Episode not registered in Show-Build system
- **AssetID Issues**: Manual AssetID assignment can cause conflicts
- **No Validation**: Risk of duplicate episode numbers
- **Integration Problems**: May not work properly with Show-Build tools

**Recommendation:** Always use the API endpoint (`POST /episodes/create`) for new episode creation to ensure full Show-Build compatibility and proper initialization.

## Phase 2: Content Development & Asset Integration

### 2.1 Content Development

**Create individual segment files with proper frontmatter:**
```yaml
---
id: 'unique_segment_id'
slug: segment-slug
type: segment
order: 10
duration: "00:00:00:00"
status: draft
title: "Segment Title"
---

# Segment content here
```

**Content Guidelines:**
- Use descriptive, consistent segment titles
- Set appropriate order values for sequencing
- Start all segments in `draft` status
- Include placeholder duration fields

## Phase 2: Asset Integration & Cue Blocks

### 2.1 Media Asset Management

**Asset Storage Structure:**
- Videos: `/episodes/{episode}/assets/video/`
- Images: `/episodes/{episode}/assets/images/`
- Organized by AssetID for traceability

**Asset Naming Conventions:**
- Use descriptive, lowercase, hyphenated names
- Example: `ri-attorney-general-cut1.mp4`
- Avoid spaces, special characters, or version numbers in filenames

### 2.2 Cue Block Implementation

**Supported Cue Types:**
- `SOT`: Sound on Tape (video/audio clips)
- `GFX`: Graphics (images, static visuals)
- `FSQ`: Full Screen Quote (generated quotes)
- `ADLIB`: Ad-libbed content with duration
- `BREAK`: Broadcast break markers

**SOT Cue Block Format:**
```markdown
<!-- Begin Cue -->
[Type: SOT]
[AssetID: CUEMEOMVCAIQ2MDV7]
[Slug: shoot-maga]
[MediaURL: shoot-maga.mp4]
[Duration: 00:00:58:00]
<!-- End Cue -->
```

**GFX Cue Block Format:**
```markdown
<!-- Begin Cue -->
[Type: GFX]
[AssetID: CUEMEOMVM8C1BJ23P]
[Slug: pamela-tweet]
[MediaURL: pamela-tweet.png]
<!-- End Cue -->
```

**Break Segment Format:**
```markdown
---
id: break_25
type: break
status: production
order: 25
duration: 00:00:00:00
---

<!-- Begin Cue -->
[Type: BREAK]
[AssetID: BREAK25001]
[Slug: break]
<!-- End Cue -->
```

### 2.3 Duration Format Requirements

**Critical: All duration fields must use `HH:MM:SS:MS` format**
- Hours:Minutes:Seconds:Milliseconds
- Example: `00:03:45:50` (3 minutes, 45 seconds, 50 milliseconds)
- NOT `MM:SS` format - this will cause calculation errors

## Phase 3: Production Preparation

### 3.1 Status Management

**Status Progression:**
1. `draft` → Content being developed
2. `production` → Ready for production tools

**Promoting to Production:**
- Review all segment content for completeness
- Verify all cue blocks have required fields
- Ensure media assets are properly referenced
- Change status in YAML frontmatter to `production`

### 3.2 Duration Calculation

**Command:**
```bash
python3 /mnt/process/show-build/tools/duration_calculator.py --episode {episode_number}
```

**What it does:**
- Calculates word-count-based durations for text content
- Adds actual media durations from SOT cue blocks
- Updates episode total duration in `info.md`
- Outputs all durations in `HH:MM:SS:MS` format

**When to run:**
- After content changes
- After adding/modifying cue blocks
- Before generating host scripts
- As final validation step

### 3.3 Host Script Generation

**Command:**
```bash
python3 /mnt/process/show-build/tools/render-script-host.py {episode_number}
```

**Features:**
- Generates HTML and PDF versions
- Includes block indicators (BLOCK A, B, C) after break segments
- Page breaks only at broadcast break points
- Uses media enumeration for cue references
- Exports to `/episodes/{episode}/exports/`

**Output files:**
- `script-MM-DD-YY-production-{version}.html`
- `script-MM-DD-YY-production-{version}.pdf`

## Phase 4: Media Production Pipeline

### 4.1 Media Collection & Organization

**Command:**
```bash
python3 /mnt/process/show-build/tools/media-collect.py {episode_number}
```

**Process:**
1. Scans production-status segments for media references
2. Copies media files to `/episodes/{episode}/rundown/list/`
3. Applies enumerated naming (e.g., `10_05_shoot-maga.mp4`)
4. Generates vMix-compatible playlists

**Output files:**
- Enumerated media files in `/rundown/list/`
- `media-list.txt` - Text file listing
- `media-list.m3u` - M3U playlist for vMix

### 4.2 Audio Normalization (When Required)

**vMix Broadcast Level Normalization:**
```bash
ffmpeg -i "input-file.mp4" -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" -c:v copy "input-file-2.mp4"
```

**Parameters:**
- `-16 LUFS`: Integrated loudness (broadcast standard)
- `-1.5 dBTP`: True peak limit
- `LRA=11`: Loudness range target
- Saves with `-2` suffix to preserve original

## Phase 5: Final Production & Quality Assurance

### 5.1 Final Workflow Steps

**Standard sequence for episode completion:**
1. Final content review and edits
2. Duration calculation: `duration_calculator.py --episode {episode}`
3. Host script generation: `render-script-host.py {episode}`
4. Media collection: `media-collect.py {episode}`
5. Audio normalization (as needed)
6. Final validation checklist

### 5.2 Quality Assurance Checklist

**Content Validation:**
- [ ] All segments have proper YAML frontmatter
- [ ] Segment order fields create logical sequence
- [ ] All production segments have meaningful content
- [ ] Break segments properly positioned

**Media Validation:**
- [ ] All media cue blocks include required fields
- [ ] AssetIDs are unique and properly formatted
- [ ] MediaURL references point to existing files
- [ ] Duration fields use `HH:MM:SS:MS` format

**Production Validation:**
- [ ] Total episode duration calculated accurately
- [ ] Host script includes all production segments
- [ ] Media files successfully collected and enumerated
- [ ] Block indicators appear at correct positions
- [ ] Audio levels normalized for broadcast (when needed)

**Output Validation:**
- [ ] HTML and PDF scripts generated successfully
- [ ] Media playlist files created
- [ ] All enumerated media files present in `/rundown/list/`
- [ ] No validation errors in tool output

## Phase 6: Recording Session Preparation

### 6.1 Deliverables

**For Host/Talent:**
- PDF host script with proper block structure
- Clear cue indicators for media playback
- Proper segment sequencing and timing

**For Production Team:**
- Enumerated media files in vMix-compatible organization
- M3U playlist for media server integration
- Audio-normalized files ready for broadcast

**For Technical Team:**
- Complete episode metadata in `info.md`
- Asset tracking via AssetID system
- Duration calculations for scheduling

### 6.2 Pre-Recording Verification

**Final Checks:**
- Host script matches current episode content
- All media files accessible in production environment
- Audio levels appropriate for broadcast
- Break timing aligns with show format
- Total runtime fits scheduled time slot

## Show-Build Integration Points

### Centralized Path Management
- All tools use `paths.py` for consistent file locations
- Episode root configurable for different environments
- Media paths automatically resolved

### AssetID System
- Unique identifiers track assets through pipeline
- Links content creation to final production
- Enables asset reuse and version tracking

### Status-Based Workflow
- Only `production` status segments included in outputs
- Allows gradual episode development
- Prevents incomplete content from reaching production

### Duration Format Consistency
- `HH:MM:SS:MS` format enforced throughout pipeline
- Accurate timing for broadcast scheduling
- Word-count estimates plus actual media durations

## Troubleshooting Common Issues

### Duration Calculation Problems
- **Issue**: Durations showing as `MM:SS` instead of `HH:MM:SS:MS`
- **Solution**: Update duration calculator to use proper format function

### Media Collection Failures  
- **Issue**: Media files not found during collection
- **Solution**: Verify MediaURL paths and file existence

### Script Generation Errors
- **Issue**: Validation failures preventing script output
- **Solution**: Check YAML frontmatter syntax and required fields

### Audio Level Issues
- **Issue**: Inconsistent audio levels across media
- **Solution**: Apply broadcast normalization to all video assets

## Tool Reference

### Duration Calculator
- **Purpose**: Calculate episode and segment durations
- **Input**: Episode number
- **Output**: Updated duration fields in markdown files

### Script Renderer  
- **Purpose**: Generate formatted host scripts
- **Input**: Episode number
- **Output**: HTML and PDF script files

### Media Collector
- **Purpose**: Organize media for production environment
- **Input**: Episode number  
- **Output**: Enumerated media files and playlists

## Workflow Optimization Tips

### Batch Operations
- Run duration calculation after multiple content changes
- Generate scripts once content is stable
- Collect media as final step before production

### Version Control
- Scripts automatically versioned to prevent overwrites
- Media files preserved with descriptive names
- Episode metadata tracks production state

### Quality Control
- Use status progression to gate content quality
- Validate all outputs before recording session
- Maintain consistent naming conventions throughout

---

*This workflow document is part of the Show-Build production system. For technical details on individual tools, see the respective documentation files.*