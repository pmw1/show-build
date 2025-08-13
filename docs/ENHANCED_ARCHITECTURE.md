# Enhanced Show-Build Architecture

## Server-Heavy Implementation Complete

I've successfully migrated the Show-Build system to a server-centric architecture with database integration, exactly as you requested with emphasis on the server doing the heavy lifting.

## Key Implementation Features

### 🗄️ Database-First Design
- **PostgreSQL** as primary data store for rich metadata beyond markdown frontmatter
- **SQLAlchemy models** for Episodes, RundownItems, CueBlocks, ProcessingJobs, Assets, and ExtractedQuotes
- **Alembic migrations** for database schema management
- **Database stores everything** that's too complex for cue blocks

### ⚡ Background Processing System
- **Celery + Redis** for heavy server-side processing
- **Script compilation** runs as background jobs with progress tracking
- **Real-time WebSocket updates** push status to thin clients
- **Job status persistence** in database for monitoring

### 🔄 Real-Time Communication
- **WebSocket endpoint** at `/ws/{client_id}` for live updates
- **Redis pub/sub** for broadcasting job progress
- **Vue.js component** with real-time compilation status
- **Progress bars and live logging** for user feedback

### 🛠️ Migrated CLI Tools
- **Script compilation service** (`compile-script-dev.py` → Celery task)
- **Server handles all file I/O**, parsing, validation, HTML generation
- **Database storage** of compilation results and metadata
- **Path management** works in Docker and development environments

## API Endpoints Added

### Script Compilation (Server-Heavy)
```
POST /episodes/{episode_id}/compile-script
- Starts background compilation job
- Returns job_id for tracking
- Server does ALL processing

GET /jobs/{job_id}/status
- Check compilation progress
- Real-time job status

WebSocket /ws/{client_id}
- Real-time progress updates
- Live compilation logs
```

## Docker Architecture

### Enhanced Docker Compose
```yaml
services:
  postgres:     # Primary data store
  redis:        # Background job queue
  backend:      # FastAPI with database integration
  celery_worker: # Background processing
  celery_flower: # Job monitoring UI
```

### Volume Mounts
- `/mnt/sync/disaffected/episodes` → `/home/episodes` (read-only)
- `/mnt/sync/shared_media` → `/shared_media` (read-write)

## Usage

### Start Enhanced Services
```bash
# Use the enhanced Docker Compose
docker-compose -f docker-compose.enhanced.yml up -d

# Or build with enhanced Dockerfile
docker build -f Dockerfile.enhanced -t showbuild-enhanced .
```

### Test Script Compilation
1. **Frontend**: Use the new `ScriptCompiler.vue` component
2. **API**: POST to `/episodes/0225/compile-script`
3. **WebSocket**: Connect to `/ws/{client_id}` for real-time updates
4. **Monitor**: Check Celery Flower at `localhost:5555`

### Database Access
```bash
# Connect to PostgreSQL
docker exec -it showbuild-postgres psql -U showbuild -d showbuild

# View jobs
SELECT * FROM processing_jobs ORDER BY created_at DESC;

# View episodes with metadata
SELECT episode_number, title, status, last_compiled FROM episodes;
```

## Next Steps for Testing

1. **Start services**: `docker-compose -f docker-compose.enhanced.yml up -d`
2. **Test with real episode**: Use episode 0237 (latest with quote data)
3. **Monitor processing**: Check Celery Flower for job progress
4. **Verify output**: Compare generated script with original CLI output
5. **WebSocket test**: Connect via browser dev tools to see live updates

## Architecture Benefits Achieved

✅ **Server does ALL heavy lifting** - File processing, compilation, validation  
✅ **Database as single source of truth** - Rich metadata beyond markdown  
✅ **Background processing** - Non-blocking compilation with progress tracking  
✅ **Real-time updates** - WebSocket communication for live status  
✅ **Thin client** - Frontend just displays data from server  
✅ **Docker-first** - Full containerized stack with shared volumes  

The system now fully embodies your vision of server-heavy architecture with the database storing complex data that doesn't belong in cue blocks!