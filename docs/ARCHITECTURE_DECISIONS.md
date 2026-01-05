# Architecture Decisions & Analysis

**Status**: Active Decision Document
**Date**: 2026-01-01
**Purpose**: Record key architectural decisions and their rationale

---

## 🎯 Decision 1: Remove Obsidian Compatibility Requirement

### **Decision**: Approved ✅

**Context:**
- Original vision: Show-Build as drop-in replacement for Obsidian
- Current reality: 100% database-first architecture
- YAML frontmatter format maintained in `rundown_items.script_content` for potential future use
- Episode directory structure exists for media asset organization only

**Analysis:**

**Current State:**
- All rundown content stored in PostgreSQL (`rundown_items.script_content`)
- NO filesystem markdown files currently read or written for content
- Media assets ARE written to filesystem (`/mnt/sync/disaffected/episodes/{episode}/assets/`)
- Episode directory structure functional for media organization

**Implications of Removing Obsidian Compatibility:**

✅ **Benefits:**
1. Simplifies architecture - single source of truth (database)
2. Removes unnecessary file I/O overhead
3. Eliminates dual-sync complexity (database ↔ filesystem)
4. Allows database-optimized query performance
5. Enables real-time collaboration without file conflicts
6. Cleaner API design without filesystem translation layer
7. Reduces maintenance burden (no file format conversion)

⚠️ **Tradeoffs:**
1. Loses external editor integration (Obsidian, VS Code, etc.)
2. Content not portable as markdown files
3. Cannot use git for content version control
4. Increases database dependency (but already 100% dependent)
5. No offline editing capability (requires database connection)

**Recommendation:** ✅ **APPROVE - Remove Obsidian Compatibility Requirement**

**Rationale:**
- System already operates 100% database-first
- Benefits significantly outweigh tradeoffs
- Future markdown export capability can be added as optional feature if needed
- Database provides superior capabilities for broadcast production workflows

**Implementation Impact:**
- **Documentation:** Update all references to "Obsidian compatibility"
- **Episode Directory Standard:** Clarify that structure is for media only
- **Future Filesystem Integration:** Mark as "optional export feature" not "core requirement"
- **API Design:** Optimize for database operations without filesystem translation

---

## 🔌 Decision 2: Remove MQTT Infrastructure

### **Decision**: Approved ✅

**Context:**
- MQTT broker (eclipse-mosquitto) currently running in Docker
- Legacy from older preprocessing/job coordination system
- Celery + Redis now handles all async task processing

**Analysis:**

**Current MQTT Usage:**
```
MQTT Files:
- app/preproc_mqtt_listen.py (legacy preprocessing listener)
- app/preproc_mqtt_pub.py (legacy preprocessing publisher)
- app/services/testboot.mqtt.py (test file)
- app/main.py (imports MQTT, has /publish/ endpoint)

Docker:
- mqtt-broker container running (4 weeks uptime)
- Connections every ~5 minutes (health checks)
- No actual message traffic observed in logs
```

**Current Celery/Redis Usage:**
```
Celery Configuration:
- 7 queues: assets_high, assets, assets_low, compilation, quotes, media, fsq
- Task routing with priority support
- 16 files actively using Celery
- Well-configured time limits, monitoring, acks
- Redis backend for results and state

Active Tasks:
- Script compilation (services.script_compilation)
- Quote extraction (services.quote_extraction)
- Asset processing (services.asset_processing)
- FSQ PNG generation (services.asset_processing.generate_fsq_png)
- FFmpeg operations (services.ffmpeg_tasks)
- Cleanup jobs (celery_cleanup)
```

**Celery vs MQTT Capabilities:**

| Feature | MQTT | Celery + Redis | Winner |
|---------|------|----------------|--------|
| Task Queuing | ❌ Not designed for this | ✅ Purpose-built | Celery |
| Priority Queues | ⚠️ Manual implementation | ✅ Native support | Celery |
| Task Results | ❌ Requires custom backend | ✅ Built-in result backend | Celery |
| Task Retries | ❌ Manual implementation | ✅ Automatic retry logic | Celery |
| Task Monitoring | ❌ Requires external tools | ✅ Flower, events, monitoring | Celery |
| Time Limits | ❌ No native support | ✅ Soft/hard limits | Celery |
| Worker Management | ❌ Manual | ✅ Worker pools, autoscaling | Celery |
| Cross-Platform | ✅ Great for IoT/embedded | ✅ Works on all platforms | Tie |
| Resource Overhead | ✅ Lightweight | ⚠️ Heavier (but manageable) | MQTT |
| Payload Size | ⚠️ Small messages (KB) | ✅ Large payloads (MB) | Celery |

**MQTT Use Cases (What It's Good For):**
- ✅ Pub/sub messaging patterns
- ✅ IoT device communication
- ✅ Real-time notifications to multiple subscribers
- ✅ Lightweight messaging with minimal overhead
- ✅ Unreliable network environments (QoS levels)

**Show-Build Requirements:**
- ✅ Background task processing (Celery wins)
- ✅ Result tracking and retrieval (Celery wins)
- ✅ Task prioritization (Celery wins)
- ✅ Retry and failure handling (Celery wins)
- ✅ Worker orchestration (Celery wins)
- ❌ Pub/sub to external systems (not needed)
- ❌ IoT device integration (not applicable)

**Recommendation:** ✅ **APPROVE - Remove MQTT Infrastructure**

**Rationale:**
1. **MQTT is not actively used** - Only health check connections observed
2. **Celery superior for all current requirements** - Task queuing, prioritization, results
3. **Reduces complexity** - One less service to maintain
4. **Celery already handles everything** - Well-configured and production-ready
5. **No loss of functionality** - All current features work through Celery

**Migration Path:**

1. ✅ **Verify no active MQTT usage** (DONE - only health checks)
2. ⬜ Remove MQTT imports from `app/main.py`
3. ⬜ Remove `/publish/` endpoint from `app/main.py`
4. ⬜ Delete legacy MQTT files:
   - `app/preproc_mqtt_listen.py`
   - `app/preproc_mqtt_pub.py`
   - `app/services/testboot.mqtt.py`
5. ⬜ Remove `paho-mqtt>=1.6.1` from `app/requirements.txt`
6. ⬜ Remove `mqtt-broker` service from `docker-compose.yml`
7. ⬜ Remove MQTT dependency from server in `docker-compose.yml` (`depends_on`)
8. ⬜ Stop and remove MQTT container: `docker stop mqtt-broker && docker rm mqtt-broker`
9. ⬜ Update documentation to reflect Celery-only architecture

**Potential Future Needs:**
- If pub/sub to external systems needed: Use Redis pub/sub (already have Redis)
- If real-time browser notifications needed: Use WebSockets (already in codebase)
- If IoT integration needed: Can add MQTT back as isolated component

---

## 🎨 System 3: Whiteboard/Brainstorm System

### **Overview**: Visual brainstorming and asset pool management

**Status**: ✅ Production Ready (renamed from "Scratchpad" to "Whiteboard")

**Purpose:**
The Whiteboard system provides a visual canvas for content creators to:
- Brainstorm ideas before structured rundown creation
- Collect media assets (images, videos, audio, links)
- Organize research and reference materials
- Preview and annotate social media content
- Build an asset pool for later use in episodes

### **Database Tables:**

**Core Tables:**
- `whiteboards` - Workspace container (linked to episode or standalone)
- `whiteboard_items` - Individual cards on the canvas
- `whiteboard_node_links` - Visual connections between cards
- `asset_pool_files` - Media files with AssetID tracking
- `asset_tags` - Tags for organizing assets

**Key Features:**

#### Content Card Types (9 types):
1. **Text** - Plain text notes (keyboard shortcut: T)
2. **Link** - URL cards with automatic link preview generation
3. **Image** - Image upload with caption (keyboard shortcut: I)
4. **Video** - Video file upload with thumbnail (keyboard shortcut: V)
5. **Audio** - Audio file upload (keyboard shortcut: A)
6. **HTML** - HTML content preview (keyboard shortcut: H)
7. **Code** - Syntax-highlighted code blocks (keyboard shortcut: C)
8. **Markdown** - Markdown rendering (keyboard shortcut: M)
9. **Social Media** - Rich preview of X/Twitter posts with metadata

#### Canvas Features:
- **Drag and drop positioning** - Free-form canvas layout
- **Resizable cards** - Adjustable width for each card
- **Z-index management** - Layer ordering
- **Collapsible cards** - Minimize to save space
- **Parent-child relationships** - Nested item hierarchies
- **Visual node links** - Connect related cards with arrows
- **Custom card titles** - Override default titles

#### Link Preview System:
- **Automatic metadata extraction** - Title, description, image, favicon
- **Domain detection** - Shows source domain
- **Social media enhancement** - Rich Twitter/X card recreation
- **Preview caching** - Stores preview data in database

#### Asset Pool Integration:
- **AssetID assignment** - Every uploaded file gets unique AssetID
- **Tagging system** - Organize assets with custom tags
- **Source tracking** - Records origin (whiteboard, manual_upload, twitter, youtube)
- **Thumbnail generation** - Auto-creates thumbnails for media
- **MIME type detection** - File type identification
- **File size tracking** - Storage usage monitoring

#### Workspace Management:
- **Episode-linked workspaces** - Associate whiteboard with specific episode
- **Standalone workspaces** - General brainstorming not tied to episode
- **Workspace ID generation** - Unique identifiers for each workspace
- **Auto-save** - Periodic saving to database
- **Load from database** - Restore complete workspace state

### **Frontend Component:**

**File**: `/disaffected-ui/src/views/ScratchpadView.vue` (2134 lines)
**Route**: `/whiteboard` (requires authentication)

**UI Features:**
- Infinite canvas with pan and zoom
- Toolbar with quick-add buttons
- Keyboard shortcuts for rapid card creation
- Drag handles for positioning
- Delete, duplicate, and edit controls per card
- Clear all functionality
- Responsive design

### **Backend API:**

**Router**: `/app/whiteboard_router.py`
**Endpoints** (under `/api/whiteboard/`):
- `POST /generate-workspace-id` - Create new workspace ID
- `GET /{workspace_identifier}` - Load whiteboard by episode or workspace ID
- `POST /save` - Save complete whiteboard state
- `PUT /items/{item_id}` - Update individual card
- `DELETE /items/{item_id}` - Delete card
- `POST /upload-asset` - Upload media file to asset pool
- `GET /asset-pool` - List all assets in pool
- `POST /node-links` - Create visual connection between cards
- `GET /node-links/{whiteboard_id}` - Get all connections
- `DELETE /node-links/{link_id}` - Remove connection

**External Service Integration:**
- `link_preview_service.py` - Fetches metadata from URLs
- AssetID service integration for unique file identifiers

### **Use Cases:**

1. **Pre-Production Research**
   - Collect links, images, quotes for episode
   - Organize by topic or segment
   - Tag assets for easy retrieval

2. **Social Media Content Curation**
   - Paste X/Twitter URLs
   - Auto-generates rich preview cards
   - Preserves author info, timestamps, media

3. **Script Development**
   - Brainstorm segment ideas as text cards
   - Link related concepts visually
   - Graduate ideas to structured rundown

4. **Asset Library Building**
   - Upload images, videos, audio
   - Tag for organization (topics, guests, themes)
   - Reference in multiple episodes

5. **Reference Material Collection**
   - Store code snippets
   - Save HTML previews
   - Keep markdown notes

### **Migration History:**
- **Original name**: "Scratchpad"
- **Renamed to**: "Whiteboard" (database migration: `5765d66b2c1f`)
- **Asset pool added**: Migration `1012` added asset pool tables
- **Parent-child support**: Extended for nested items

### **Production Status:**
- ✅ Fully functional and tested
- ✅ Database migrations applied
- ✅ Frontend component complete
- ✅ API endpoints operational
- ✅ AssetID integration working

### **Potential Enhancements:**
- [ ] Export whiteboard as PDF/image
- [ ] Collaborative editing (multiple users simultaneously)
- [ ] Templates for common whiteboard layouts
- [ ] Integration with rundown items (drag from whiteboard to rundown)
- [ ] AI-powered organization suggestions
- [ ] Search across all whiteboards
- [ ] Version history/snapshots

---

## 📋 Implementation Checklist

### Phase 1: Documentation Updates (Week 1)
- [ ] Update CLAUDE.md - Remove Obsidian compatibility references
- [ ] Update EPISODE_DIRECTORY_STANDARD.md - Clarify media-only structure
- [ ] Update UNIVERSAL_LLM_FRAMEWORK_UFDP.md - Remove filesystem sync references
- [ ] Update README.md - Reflect database-first architecture
- [ ] Create ACTIVE_WORK_QUEUE.md - Track ongoing implementation tasks

### Phase 2: MQTT Removal (Week 1)
- [ ] Remove MQTT imports from app/main.py
- [ ] Remove /publish/ endpoint
- [ ] Delete preproc_mqtt_listen.py
- [ ] Delete preproc_mqtt_pub.py
- [ ] Delete testboot.mqtt.py
- [ ] Remove paho-mqtt from requirements.txt
- [ ] Remove mqtt-broker from docker-compose.yml
- [ ] Test all async operations still work via Celery
- [ ] Stop and remove mqtt-broker container

### Phase 3: Code Cleanup (Week 2)
- [ ] Remove any remaining MQTT references in comments
- [ ] Update health check to remove MQTT monitoring
- [ ] Verify Celery handles all async tasks
- [ ] Test FSQ generation pipeline
- [ ] Test SOT processing pipeline
- [ ] Test script compilation
- [ ] Test quote extraction

### Phase 4: Architecture Documentation (Week 2)
- [ ] Document Celery queue architecture
- [ ] Create diagrams for async task flow
- [ ] Document worker deployment (Kairo, Windows)
- [ ] Update PROJECT_ARCHITECTURE_REPORT.md

---

## 🎯 Strategic Direction

### New Core Principles:

1. **Database-First Architecture**
   - PostgreSQL is the single source of truth
   - All content stored in database tables
   - Filesystem used only for binary media assets

2. **Celery-Only Async Processing**
   - All background tasks via Celery + Redis
   - Priority queue system for task management
   - Worker pools for distributed processing

3. **Optional Export Capabilities**
   - Markdown export as utility feature (not core)
   - Script generation in 6 formats (on-demand)
   - Media list enumeration for vMix integration

4. **Production-Grade Features**
   - RBAC authentication
   - Universal LLM Framework
   - AssetID tracking system
   - Audit trails and versioning

### What This Enables:

✅ **Real-time Collaboration** - Multiple users editing same episode
✅ **Advanced Queries** - SQL-powered search and filtering
✅ **Transactional Integrity** - ACID guarantees on content changes
✅ **Performance Optimization** - Database-level caching and indexing
✅ **API-First Design** - Clean REST API without filesystem translation
✅ **Simplified Deployment** - Fewer services to manage
✅ **Better Monitoring** - Celery Flower, database metrics

---

## 📊 Impact Summary

### Services Removed:
- ❌ MQTT Broker (eclipse-mosquitto)

### Services Retained:
- ✅ PostgreSQL (database)
- ✅ Redis (Celery backend + caching)
- ✅ Celery (async tasks)
- ✅ FastAPI (backend API)
- ✅ Vue 3 (frontend)
- ✅ Nginx (frontend serving)
- ✅ Syncthing (media file sync)
- ✅ Whisper API (transcription)
- ✅ FFmpeg Worker (video processing)

### Complexity Reduction:
- **Before**: 9 services, dual storage (DB + files), MQTT + Celery async
- **After**: 8 services, single storage (DB), Celery-only async
- **Reduction**: -11% service count, -50% async systems, -50% storage systems

---

## ✅ Approval Status

**Decision 1 (Obsidian Compatibility):** ✅ APPROVED
**Decision 2 (MQTT Removal):** ✅ APPROVED

**Next Steps:** Create ACTIVE_WORK_QUEUE.md and begin implementation

---

**Document Version:** 1.0
**Last Updated:** 2026-01-01
**Maintained By:** Show-Build Development Team
