# Episode Data Architecture

## Overview
The Show-Build system separates **show-level configuration** from **episode-specific data** to maintain clean data organization and avoid redundancy.

## Data Separation

### Show-Level Fields (stored in show configuration)
These fields apply to the entire show and rarely change:
- `omnystudio_program_id` - The show's Omnystudio program identifier
- `omnystudio_category` - Default category (e.g., "podcast")
- `youtube_category_id` - YouTube category for the show
- `youtube_default_language` - Default language code
- `youtube_playlist_id` - The show's YouTube playlist
- `host` - Regular host(s) of the show
- `age_rating` - Default age rating for the show

### Episode-Specific Fields (stored in episode metadata)
These fields vary per episode and are stored in each episode's `info.md`:

```yaml
---
assetid: 1001
show_id: 100  # Required - Links to the parent show's AssetID
rundown_id: 237000  # Required - Links to the rundown's AssetID (auto-generated as episode_number + 000)
episode_number: "0237"
type: sunday_show
airdate: 2025-08-10
title: "Episode Title Here"
subtitle: "Episode Subtitle"
slug: "episode-237-title-slug"
description: "Full description of this specific episode"
duration: "01:00:00"
guest: "Guest Name (if any)"
tags:
  - topic1
  - topic2
omnystudio_visibility: public
omnystudio_publish_status: draft
omnystudio_publish_datetime: "2025-08-10 09:00:00"
youtube_privacy_status: private
youtube_title: "Custom YouTube Title (optional)"
youtube_description: "Custom YouTube description (optional)"
youtube_tags: "tag1, tag2, tag3"
social_hashtags: "#podcast #episode237"
twitter_thread: true
instagram_reel: false
facebook_post: true
explicit: false
content_warnings: "Discussion of sensitive topics"
publish_status: draft
schedule_datetime: "2025-08-10 09:00:00"
visibility: public
recording_date: "2025-08-08"
producer: "Producer Name"
editor: "Editor Name"
notes: "Internal production notes"
server_messages: "System messages and logs"
---
```

## AssetID Relationships

### Two-Way Linking: Shows ↔ Episodes ↔ Rundowns
The system uses bidirectional AssetID relationships for complete traceability:

#### Episode Fields:
- **assetid**: Unique identifier for the episode itself
- **show_id**: Links to the parent show (required)
- **rundown_id**: Links to the episode's rundown (required)

#### Rundown Fields:
- **assetid**: Unique identifier for the rundown
- **show_id**: Links back to the parent show (required)
- **episode_id**: Links back to the episode using this rundown

This two-way relationship enables:
- **Complete traceability**: Navigate from show → episode → rundown and back
- **Rundown reuse**: Rundowns can reference their parent show while being used by different episodes
- **Query flexibility**: Find all episodes of a show, all rundowns for a show, or which episodes use a specific rundown
- **Data integrity**: Maintain relationships even if content is moved or archived

### Example Relationship Structure
```
Show (assetid: 100)
    ↓
Episode 0237 (assetid: 1001)
    - show_id: 100 (links back to show)
    - rundown_id: 237000 (links to rundown)
    ↓
Rundown (assetid: 237000)
    - show_id: 100 (links back to show)
    - episode_id: 1001 (links back to episode)
    ↓
    ├── Segment 1 (assetid: 3001)
    ├── Segment 2 (assetid: 3002)
    └── Segment 3 (assetid: 3003)
```

### Auto-generation Rules
- **rundown_id**: If not provided, defaults to `{episode_number}000` (e.g., episode 0237 gets rundown_id 237000)
- **show_id**: Must be provided or retrieved from show configuration
- **episode_id** (in rundown): Automatically set when rundown is created for an episode

## Script Storage Strategy

### The Two-Layer Approach

1. **Segmented Storage (Source of Truth)**
   - Scripts are stored in individual segment files: `/episodes/0237/rundown/*.md`
   - Each segment has its own script section
   - Allows collaborative editing of different segments
   - Maintains granular version control

2. **Compiled Script (Generated)**
   - Full script is compiled from all segments
   - Can be cached in `info.md` or exported separately
   - Generated on-demand via API: `GET /api/episodes/{number}/script`
   - Available in multiple formats: markdown, HTML, plain text

### Example Segment File Structure
```markdown
---
id: '0237001'
slug: opening
type: segment
order: 10
duration: 00:05:00
title: Opening
---

## Notes
Opening segment notes

## Script
Welcome to episode 237 of the show. Today we're discussing...

[Actual script content goes here]

## Resources
- Link to research
- Reference materials
```

### Script Compilation Flow
```
rundown/
├── 10 Opening.md       ─┐
├── 20 Interview.md      ├─► Compile ─► Full Script
├── 30 Analysis.md       │              (markdown/html/text)
└── 40 Closing.md       ─┘
```

## Database Considerations

### Why File-Based Storage Works
- **Obsidian Compatibility**: Maintains full compatibility with Obsidian workflows
- **Version Control**: Git-friendly text files for tracking changes
- **Portability**: Easy to backup, migrate, or share episode folders
- **Performance**: File system is efficient for this use case
- **Flexibility**: Scripts can be edited with any text editor

### When to Consider Database Storage
If you need:
- **Real-time collaboration** with conflict resolution
- **Full-text search** across all episodes instantly
- **Complex queries** (e.g., "all episodes with guest X discussing topic Y")
- **Audit trails** with detailed change history
- **API performance** for thousands of concurrent users

### Hybrid Approach (Recommended)
- **Files**: Primary storage for content (scripts, metadata)
- **Database**: Index for search, relationships, and performance
- **Cache**: Redis for compiled scripts and frequently accessed data

## API Endpoints

### Episode Management
- `POST /api/episodes/{number}/create` - Create new episode with metadata
- `PUT /api/episodes/{number}/info` - Update episode metadata
- `DELETE /api/episodes/{number}` - Delete episode (moves to trash)

### Script Management
- `GET /api/episodes/{number}/script` - Get compiled script
  - Query params: `format=markdown|html|text`
- `PUT /api/episodes/{number}/script` - Update segment script
  - Body: `{segment_file: "10 Opening.md", script_content: "..."}`

### Rundown Management
- `GET /api/episodes/{number}/rundown` - Get all segments
- `POST /api/rundown/{number}/item` - Create new segment
- `PUT /api/rundown/{number}/reorder` - Reorder segments

## Benefits of This Architecture

1. **Clean Separation**: Show config vs episode data
2. **No Redundancy**: Show-level fields stored once
3. **Flexibility**: Scripts can be edited at segment or full level
4. **Compatibility**: Works with existing Obsidian workflows
5. **Scalability**: Can add database layer when needed
6. **Version Control**: Git-friendly text files
7. **Backup-Friendly**: Simple file/folder structure

## Migration Path

If you later need database storage:

1. **Phase 1**: Add database indexing while keeping files as source
2. **Phase 2**: Sync changes bidirectionally
3. **Phase 3**: Optionally move to database as primary storage

The current architecture provides excellent flexibility while maintaining simplicity and compatibility with your existing workflows.