# Dual Rundown Architecture Decision

## Problem Statement

Show-Build currently has two different rundown systems that need to coexist:

1. **Filesystem-based**: Markdown files in `episodes/{episode_number}/rundown/` folder
2. **Database-based**: Rundown entries in the database with asset IDs

## Architecture Decision

### Primary Storage: Markdown Files (Source of Truth)
- **Location**: `episodes/{episode_number}/rundown/*.md`
- **Format**: Markdown with YAML frontmatter
- **Content**: Segment scripts, cues, notes, metadata
- **Benefits**: 
  - Human-readable
  - Version control friendly
  - Obsidian compatible
  - Portable between systems

### Secondary Storage: Database (Performance Cache)
- **Location**: Database tables (rundown-related models)
- **Format**: Structured relational data
- **Content**: Mirrored metadata from markdown files + additional performance data
- **Benefits**:
  - Fast queries during showtime
  - Relational integrity
  - Complex aggregations
  - Real-time updates

## Data Flow Architecture

### Frontend → Markdown Files → Database
1. **Frontend editing** updates markdown files directly
2. **File system watchers** detect changes
3. **Synchronization service** parses markdown and updates database
4. **Database serves** fast queries for showtime operations

### Synchronization Rules

#### Markdown File Operations:
- **Renaming/Enumeration**: Frontend renames files to maintain order
- **Content Updates**: Frontend modifies YAML frontmatter and script content  
- **File Creation/Deletion**: Frontend manages file lifecycle

#### Database Mirroring:
- **Metadata Sync**: Parse YAML frontmatter → database fields
- **Content Hash**: Store markdown content hash for change detection
- **Additional Fields**: Database can store computed/derived data not in markdown

## Implementation Strategy

### Phase 1: Markdown-First (Current)
- Frontend primarily works with markdown files
- Database sync is secondary/optional
- ContentEditor.vue manages markdown files

### Phase 2: Hybrid Sync 
- Implement file watchers for automatic sync
- Database becomes reliable cache
- Frontend can query database for performance

### Phase 3: Seamless Integration
- Frontend uses database for fast reads
- All writes go through sync layer
- Markdown files remain authoritative

## Conflict Resolution

### When Systems Diverge:
1. **Markdown files are authoritative** 
2. Database sync service rebuilds from markdown
3. Manual conflict resolution through frontend
4. Backup/restore mechanisms for both systems

## Benefits of Dual Architecture

1. **Best of Both Worlds**: Human-readable files + fast database queries
2. **Resilience**: Either system can be rebuilt from the other
3. **Performance**: Database for showtime, files for editing
4. **Compatibility**: Maintains Obsidian workflow compatibility
5. **Scalability**: Can optimize each system for its use case

## Technical Implementation Notes

- File system watchers using Node.js `chokidar` or Python `watchdog`
- Markdown parsing with frontmatter extraction
- Database upsert operations with conflict resolution
- Content hashing for efficient change detection
- Event-driven sync architecture

This dual approach ensures we maintain the flexibility of markdown files while gaining the performance benefits of a database system.