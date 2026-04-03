# Show-Build Project: Database Migration Analysis

## Project Overview

Show-Build is a sophisticated broadcast content management system for the "Disaffected" podcast, built around an Obsidian-compatible markdown workflow with extensive automation. The system manages episode production from initial content creation through broadcast-ready output.

## Current Architecture

### File-Based System
```
/mnt/sync/disaffected/
├── episodes/
│   └── 0233/
│       ├── info.md (YAML frontmatter + episode metadata)
│       ├── rundown/*.md (segment scripts + cue blocks)
│       ├── assets/
│       │   ├── video/ (uploaded media)
│       │   ├── graphics/ (generated quote PNGs)
│       │   └── quotes/quotes.json
│       └── exports/ (compiled scripts, transcripts)
├── tools/python/ (CLI automation scripts)
└── [synced across 5+ machines via Syncthing]
```

### Current Workflow Pain Points

1. **Human Chaos Input**: Josh creates markdown files with:
   - Terrible slugs
   - Missing descriptions  
   - Malformed cue blocks
   - Inconsistent formatting

2. **Automated Enhancement Pipeline**: Background Python scripts:
   - LLM-generated descriptions and slug improvements
   - Cue block repair and formatting cleanup
   - Media processing (ffprobe/ffmpeg for vMix transcoding)
   - Audio normalization and Whisper transcription
   - Quote extraction and PNG generation
   - Runtime calculations

3. **Syncthing Conflicts**: Server processing + human editing = conflict files when both modify the same episode directory simultaneously

## Why Database Migration is Critical

### Current Problems

#### 1. **Processing Coordination Chaos**
- No way to coordinate multiple background scripts
- Scripts can overwrite each other's work
- No processing queue or job dependencies
- Duplicate work (re-generating same content)

#### 2. **Syncthing Conflict Hell**
- Server writes compiled scripts while humans edit
- Background media processing creates conflicts
- Manual conflict resolution required
- Risk of losing work when "someone has to be the loser"

#### 3. **No Processing State Management**
- Can't track what's been processed
- No caching of expensive operations (LLM calls, transcription)
- No way to resume interrupted processing
- No audit trail of automated changes

#### 4. **Scalability Issues**
- File system doesn't handle concurrent access
- Complex queries across episodes impossible
- No relationship tracking between assets/segments
- Performance degrades with large episode counts

## Proposed Database Architecture

### Core Philosophy
**Files remain source of truth for content, database coordinates all processing and caches metadata**

### Database Schema

```sql
-- Episode Management
Episodes: episode_number, title, airdate, status, total_runtime
RundownItems: episode_id, file_path, slug, content_hash, last_processed
CueBlocks: rundown_item_id, type, slug, asset_id, validation_status

-- Media Processing Pipeline  
Assets: file_path, type, duration, transcoded, normalized, transcribed
ProcessingJobs: job_type, status, priority, dependencies, result
ProcessingQueue: job_id, scheduled_time, worker_assigned

-- Content Enhancement
LLMCache: content_hash, prompt_type, generated_content, timestamp
ExtractedQuotes: episode_id, text, generated_image_path, source_file
MediaMetadata: asset_id, duration, resolution, codec, file_size

-- Coordination
FileLocks: file_path, locked_by, lock_type, expires_at
ProcessingHistory: file_path, operation, timestamp, before_hash, after_hash
```

### Processing Architecture

#### 1. **Smart Processing Queue**
```python
# Example processing pipeline
pipeline = [
    "slug_enhancement",      # LLM fixes terrible slugs
    "description_generation", # LLM writes missing descriptions  
    "cue_block_repair",      # Fix malformed cue blocks
    "media_analysis",        # ffprobe video metadata
    "transcoding",           # ffmpeg for vMix
    "audio_normalization",   # Broadcast audio standards
    "transcription",         # Whisper → markdown
    "quote_extraction",      # Parse transcripts for quotes
    "image_generation",      # PNG graphics from quotes
    "runtime_calculation"    # Total episode timing
]
```

#### 2. **File System Integration**
- **Files remain authoritative** for script content
- **Database caches parsed data** for performance
- **Processing writes back to files** after enhancement
- **Database prevents conflicts** through coordination

#### 3. **Coordination Layer**
```python
class ProcessingCoordinator:
    def can_process_file(self, file_path):
        # Check if human is editing
        # Check if other scripts are processing
        # Verify prerequisites are complete
        
    def queue_enhancement(self, episode_id, operations):
        # Add jobs with dependencies
        # Respect processing priority
        # Cache expensive operations (LLM, transcription)
```

## Migration Strategy

### Phase 1: Infrastructure Setup
1. **Database deployment** (PostgreSQL + Redis for job queue)
2. **API layer** for script coordination
3. **File watching** system to detect changes
4. **Basic job queue** implementation

### Phase 2: Processing Migration  
1. **Media processing** (ffmpeg/ffprobe → database coordination)
2. **LLM caching** (avoid regenerating same content)
3. **Quote extraction** → database storage
4. **File locking** coordination

### Phase 3: Full Pipeline Integration
1. **Smart processing queues** with dependencies
2. **Real-time status** via WebSocket
3. **Web interface** for monitoring/control
4. **Performance optimization**

### Phase 4: Advanced Features
1. **Multi-machine coordination** (distributed processing)
2. **Content versioning** and rollback
3. **Advanced analytics** on processing efficiency
4. **API integration** for external tools

## Expected Benefits

### Immediate Wins
- **No more Syncthing conflicts** on processed files
- **Processing coordination** prevents duplicate work  
- **LLM caching** saves cost and time
- **Media metadata** available instantly
- **Real-time processing status**

### Long-term Advantages
- **Scalable content production** pipeline
- **Audit trail** of all automated enhancements
- **Performance optimization** through caching
- **Advanced querying** across episodes
- **Multi-user coordination** for larger team

### Workflow Improvements
- **Josh can create chaos** without breaking production
- **Background scripts coordinate** intelligently
- **Real-time feedback** on processing status
- **Automated quality assurance** before broadcast
- **Historical tracking** of content evolution

## Implementation Complexity

### Low Risk (Files + Database Hybrid)
- Keep existing markdown workflow
- Add database for coordination only
- Gradual migration of processing scripts
- Fallback to file-only operation possible

### Medium Complexity
- Background job processing system
- WebSocket real-time updates  
- Multi-script coordination
- LLM integration and caching

### High Value
- Eliminates manual conflict resolution
- Scales to larger content production
- Enables sophisticated content pipeline
- Future-proofs the architecture

## Technical Implementation Details

### Database Models (Already Implemented)

```python
class Episode(Base):
    episode_number = Column(String(4), unique=True)
    title = Column(String(255))
    total_runtime = Column(Integer)  # seconds
    last_processed = Column(DateTime)
    
class ProcessingJob(Base):
    job_type = Column(String(50))  # "slug_fix", "transcription", etc.
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    status = Column(String(20))  # pending, running, completed, failed
    dependencies = Column(JSON)  # List of job_ids this depends on
    result = Column(JSON)  # Processing output

class LLMCache(Base):
    content_hash = Column(String(64), index=True)
    prompt_type = Column(String(50))  # "slug_fix", "description"
    generated_content = Column(Text)
    model_used = Column(String(50))
    timestamp = Column(DateTime)

class FileLock(Base):
    file_path = Column(String(500), unique=True)
    locked_by = Column(String(100))  # script name or user
    lock_type = Column(String(20))   # "read", "write", "processing"
    expires_at = Column(DateTime)
```

### Processing Coordinator Service

```python
class ProcessingCoordinator:
    def __init__(self, db_session, redis_client):
        self.db = db_session
        self.redis = redis_client
        
    def can_process_file(self, file_path: str, operation: str) -> bool:
        """Check if file can be safely processed."""
        # Check for active locks
        lock = self.db.query(FileLock).filter(
            FileLock.file_path == file_path,
            FileLock.expires_at > datetime.utcnow()
        ).first()
        
        if lock and lock.lock_type == "write":
            return False
            
        # Check for human editing (could use file timestamps)
        return True
        
    def queue_processing_pipeline(self, episode_id: str, operations: List[str]):
        """Queue a series of processing operations with dependencies."""
        jobs = []
        previous_job_id = None
        
        for operation in operations:
            job = ProcessingJob(
                episode_id=episode_id,
                job_type=operation,
                status="pending",
                dependencies=[previous_job_id] if previous_job_id else []
            )
            self.db.add(job)
            self.db.flush()  # Get the ID
            
            # Add to Redis queue
            self.redis.lpush("processing_queue", job.id)
            jobs.append(job)
            previous_job_id = job.id
            
        self.db.commit()
        return jobs
```

### File Watching Integration

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class EpisodeFileHandler(FileSystemEventHandler):
    def __init__(self, coordinator: ProcessingCoordinator):
        self.coordinator = coordinator
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if it's a rundown markdown file
        if (file_path.suffix == '.md' and 
            'rundown' in file_path.parts):
            
            episode_id = file_path.parts[-3]  # episodes/0233/rundown/file.md
            
            # Queue enhancement pipeline
            self.coordinator.queue_processing_pipeline(
                episode_id,
                ["slug_enhancement", "cue_block_repair", "quote_extraction"]
            )
```

### Migration Checklist

#### Phase 1: Infrastructure ✅
- [x] PostgreSQL database setup
- [x] SQLAlchemy models
- [x] Redis for job queue
- [x] Basic Celery workers
- [x] Docker compose configuration

#### Phase 2: Core Services (In Progress)
- [x] ProcessingJob model and API
- [x] WebSocket real-time updates
- [ ] File watching service
- [ ] LLM caching system
- [ ] File locking coordination
- [ ] Processing queue worker

#### Phase 3: Script Migration (Planned)
- [ ] Media analysis (ffprobe integration)
- [ ] Transcoding pipeline (ffmpeg)
- [ ] Audio normalization
- [ ] Whisper transcription
- [ ] Quote extraction
- [ ] PNG generation
- [ ] Runtime calculations

#### Phase 4: Advanced Features (Future)
- [ ] Multi-machine coordination
- [ ] Content versioning
- [ ] Performance analytics
- [ ] Advanced web interface

## Conclusion

The database migration isn't about replacing the successful markdown workflow - it's about **orchestrating the chaos** that makes that workflow magical. Josh's creative mess becomes broadcast-ready content through coordinated automation, and the database ensures that automation doesn't step on itself or create conflicts.

This evolution transforms Show-Build from a file-based system with processing scripts into a **coordinated content production pipeline** that scales with the ambitions of the show.

## Next Steps

1. **Review this document** for accuracy and completeness
2. **Start Phase 2 implementation** with file watching and processing coordination
3. **Migrate first processing script** (likely quote extraction) as proof of concept
4. **Test with real episode data** to validate approach
5. **Gradually migrate remaining scripts** one by one

The foundation is already in place - now we build the intelligent coordination layer that makes Josh's chaos into broadcast gold! ✨