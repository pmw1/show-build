# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ **CRITICAL: ALWAYS USE HTTPS URLs** ⚠️

**MANDATORY RULE**: ALL URLs provided to the user MUST use HTTPS protocol.

- ✅ CORRECT: `https://192.168.51.210:8091`
- ❌ WRONG: `http://192.168.51.210:8091`

This applies to:
- Frontend URLs (port 8091)
- Backend API URLs (port 8888)
- ANY web-accessible service URLs
- Documentation links
- Example URLs in responses

**NO EXCEPTIONS. ALWAYS HTTPS.**

## ⚠️ **MANDATORY: ALWAYS RUN LINTING AFTER CODE CHANGES** ⚠️

**CRITICAL RULE**: After modifying any Vue, JavaScript, or TypeScript files, you MUST run linting before completing tasks:

```bash
cd disaffected-ui && npm run lint -- --fix
```

**When to run:**
- After creating/modifying `.vue` files
- After creating/modifying `.js` files
- After creating/modifying composables, mixins, stores
- Before marking any frontend task as complete
- Before presenting code to the user for testing

**If linting fails:**
- Fix all errors before proceeding
- Use `--fix` flag to auto-correct most issues
- Do NOT present code with linting errors

**This is not optional - it prevents wasted user testing time on preventable errors.**

---

## ⚠️ **MANDATORY: INTER-CLAUDE RELAY COORDINATION** ⚠️

**CRITICAL RULE**: Check the relay server for coordination with other Claude instances.

### Relay Server: http://192.168.51.223:8001
**Web Interface**: http://192.168.51.223:8001/ui

### MANDATORY Relay Check Frequency:
- **EVERY OTHER USER MESSAGE** - Check the relay for coordination with retro-transcriber-claude and kairo-claude
- **AT SESSION START** - Always check before beginning work
- **WHEN STARTING/COMPLETING MAJOR WORK** - Post updates for team coordination

### Required Actions:

**1. CHECK AT SESSION START** - Before doing any work:
```bash
curl http://192.168.51.223:8001/read
```

**2. CHECK EVERY 5 MESSAGES** - Regular coordination is critical:
```bash
curl 'http://192.168.51.223:8001/read?project=show-build&limit=10'
```

**3. POST UPDATES WHEN STARTING/COMPLETING WORK**:
```bash
curl -X POST http://192.168.51.223:8001/write -H "Content-Type: application/json" -d '{"content":"Your status","sender":"show-build-claude","project":"show-build"}'
```

**4. CHECK ANNOUNCEMENTS** - System-wide important messages:
```bash
curl http://192.168.51.223:8001/announcements
```

**5. COORDINATE BEFORE CHANGES** - If work involves shared systems, check relay first.

### Why This Matters:
- Prevents conflicting work between Claude instances
- Enables collaboration on complex multi-system tasks
- Shares specialized knowledge across instances
- Avoids duplicate effort and breaking changes

**This is not optional - it prevents wasted effort and system conflicts.**

---

## 🚨 **DEBUGGING FRONTEND ISSUES?** 🚨
**→ [`DEBUG_FIRST.md`](DEBUG_FIRST.md) ← START HERE IMMEDIATELY**

Run: `./scripts/debug-frontend.sh` (saves 10+ minutes of debugging)

## 🤖 CLAUDE-TO-CLAUDE COMMUNICATION SYSTEM

**⚠️ MIGRATED TO CLAUDESPAWN**: Legacy CLAUDECOM.txt system replaced by ClaudeSpawn satellite network

**New Communication Channel**: ClaudeSpawn HTTP API at `/mnt/process/claudespawn/`

### Sending Communications to pmw-rm4 Claude

**Method**: Create and send `CLAUDECOM.txt` file to remote Claude instance

```bash
# Create communication file
echo "Your message to pmw-rm4 Claude here" > CLAUDECOM.txt

# Send to remote Claude
scp CLAUDECOM.txt pmw@pmw-rm4:~/

# Clean up local copy
rm CLAUDECOM.txt
```

**SSH Configuration** (already set up in `/home/kevin/.ssh/config`):
```
Host pmw-rm4
    Hostname 173.14.175.162
    User pmw
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ForwardAgent yes
    Compression yes
```

### Receiving Responses from pmw-rm4 Claude

**Method**: pmw-rm4 Claude can append responses to CLAUDECOM.txt, retrieve via scp

```bash
# Retrieve responses from remote Claude
scp pmw@pmw-rm4:~/CLAUDECOM.txt ./CLAUDECOM_response.txt

# Read the response
cat CLAUDECOM_response.txt
```

### Communication Protocol

1. **Sending Instructions**: Create CLAUDECOM.txt with clear, specific instructions
2. **File Monitoring**: pmw-rm4 Claude checks for CLAUDECOM.txt periodically
3. **Response Method**: Remote Claude appends responses to same file
4. **Retrieval**: Use scp to pull responses back for review
5. **File Management**: Clean up communication files after processing

**Example Communication:**
```bash
echo "Please set up the Show-Build database using DATABASE_SETUP_INSTRUCTIONS.md and report status" > CLAUDECOM.txt
scp CLAUDECOM.txt pmw@pmw-rm4:~/
# Wait for response processing
scp pmw@pmw-rm4:~/CLAUDECOM.txt ./response.txt
cat response.txt
```

**⚠️ Important**: This is an experimental Claude-to-Claude communication method. Both instances should check for and respond to CLAUDECOM.txt files appropriately.

### ClaudeSpawn: Multi-LLM Coordination System

**Primary Communication Protocol**: All Claude coordination now handled by ClaudeSpawn

**Location**: `/mnt/process/claudespawn/`

```bash
# Start ClaudeSpawn home base
cd /mnt/process/claudespawn
python claudespawn.py --mode local --port 47291

# Launch monitoring interface
./scripts/launch_claudespawn_interface.sh

# Deploy satellite to remote machine
./scripts/deploy.sh
```

**Architecture:**
- **Home Base**: Central coordination hub (port 47291)
- **Local Satellite**: Controls local Claude instance (port 8890)
- **Remote Satellites**: pmw-rm4 and other machines

**Key Features:**
- **Structured Reminders**: Persistent memory buffers with file references
- **Automatic Response Processing**: Cross-Claude communication without keyboard input
- **Self-Updating Satellites**: Remote instances update and relaunch automatically
- **Firewall-Friendly**: Outbound-only polling works behind any firewall
- **Multi-LLM Ready**: Universal protocol for Claude, ChatGPT, Grok, local LLMs
- **7-Pane Monitoring Interface**: Comprehensive tmux dashboard
- **Hierarchical Organization**: Coordinator/worker LLM relationships

**Show-Build Integration:**
```bash
# Use ClaudeSpawn from Show-Build directory
./scripts/claudespawn.sh interface    # Launch monitoring
./scripts/claudespawn.sh start       # Start persistent Claude
./scripts/claudespawn.sh status      # Check system status
```

**📖 Complete Documentation**: See [`/mnt/process/claudespawn/README.md`](../claudespawn/README.md) for full usage guide.

## Project Overview

Show-Build is a full-stack broadcast rundown management system designed for the Disaffected media ecosystem. It serves as a drop-in replacement for Obsidian-based workflows while maintaining complete file format compatibility. The system maintains compatibility with markdown file format for future filesystem integration, using the same organizational structure as Obsidian.

**📋 Key Documentation**:
- [`UNIVERSAL_LLM_FRAMEWORK_UFDP.md`](UNIVERSAL_LLM_FRAMEWORK_UFDP.md) - ⭐ **Universal LLM Framework** - Unified AI state management (v1.0)
- [`docs/EPISODE_DIRECTORY_STANDARD.md`](docs/EPISODE_DIRECTORY_STANDARD.md) - 🗂️ **Episode File Structure Standard** - Canonical specification for all episode organization (AUTHORITATIVE)
- [`docs/ASSETID_SYSTEM_GUIDE.md`](docs/ASSETID_SYSTEM_GUIDE.md) - AssetID system reference
- [`docs/LLM_GENERATOR_TROUBLESHOOTING.md`](docs/LLM_GENERATOR_TROUBLESHOOTING.md) - LLM test segment generator debugging (legacy patterns)
- [`docs/THUMBNAIL_GENERATION_RESEARCH.md`](docs/THUMBNAIL_GENERATION_RESEARCH.md) - Thumbnail automation research (pending implementation)

## Architecture

### Data Storage Architecture (CRITICAL - READ THIS FIRST)

**CURRENT STATE**: 100% Database-Only Content Storage
- All rundown items stored in PostgreSQL `rundown_items.script_content` field
- NO filesystem markdown files are currently read or written for content
- Media assets (images/video/audio) ARE written to `/mnt/sync/disaffected/episodes/{episode}/assets/`
- Episode directory structure exists for media organization

**FUTURE FILESYSTEM INTEGRATION** (Planned, Not Implemented):
- YAML frontmatter format in `script_content` matches Obsidian/markdown conventions
- When mirroring is implemented, content will be exported to:
  - `/mnt/sync/disaffected/episodes/{episode_number}/rundown/*.md` - Individual markdown files
  - `/mnt/sync/disaffected/episodes/{episode_number}/info.md` - Episode metadata
  - Full bidirectional sync between database and filesystem
  - Compatible with Obsidian workflows

**DEVELOPER GUIDANCE**:
- ✅ USE: Database queries to `rundown_items` table for content
- ✅ USE: Filesystem operations for media assets in `assets/` directory
- ❌ AVOID: Reading/writing markdown files in `rundown/` directory (not active)
- ✅ MAINTAIN: YAML frontmatter format compatibility in `script_content` field

### Backend (FastAPI + Python)
- **Main Application**: `app/main.py` - Central FastAPI application with comprehensive API endpoints
- **Database**: PostgreSQL with SQLAlchemy ORM (`app/database.py`)
- **Authentication**: JWT-based auth system in `app/auth/` with role-based access control
- **Background Processing**: Celery with Redis for async tasks (`app/celery_app.py`)
- **Media Storage**: Episode media assets stored in `/mnt/sync/disaffected/episodes/{episode}/assets/` (host)

### Frontend (Vue 3 + Vuetify)
- **Framework**: Vue 3 with Composition API, Vuetify 3 for UI components
- **State Management**: Pinia stores, composables in `src/composables/`
- **Routing**: Vue Router with authentication guards (`src/router/index.js`)
- **Components**: Modular Vue components in `src/components/`

### Key Components
- **RundownManager.vue**: Drag-and-drop rundown editing with virtual scrolling
- **ContentEditor.vue**: Markdown content editing with live preview
- **Universal LLM Framework**: Centralized AI state management with visual feedback and persistence
- **Auth System**: Login/JWT authentication with API key fallback
- **Asset Management**: File upload and media processing capabilities

## Development Commands

### Backend
```bash
# Start all services (backend, frontend, database, MQTT)
docker compose up --build

# Backend only
docker compose up --build server

# View logs
docker logs show-build-server
```

### Frontend
```bash
cd disaffected-ui
npm install
npm run serve    # Development server
npm run build    # Production build
npm run lint     # ESLint
npm test         # Jest tests
```

### Database
```bash
# Connect to PostgreSQL
docker exec -it show-build-postgres psql -U showbuild -d showbuild

# Run migrations
cd app && python -m alembic upgrade head
```

## File Structure and Data Flow

### Episode Directory Structure (File System Organization)
**CURRENT STATE**: Directory structure exists for media asset storage only

**📖 AUTHORITATIVE SPECIFICATION**: See [`docs/EPISODE_DIRECTORY_STANDARD.md`](docs/EPISODE_DIRECTORY_STANDARD.md) for complete canonical file structure.

Episodes are organized as directories in `/mnt/sync/disaffected/episodes/{episode_number}/`:
- `projects/` - vMix profiles, After Effects teasers/graphics with source/ subdirectories
- `captures/` - Raw vMix recordings (BLOCK-A.mov, BLOCK-B.mov, BREAK-1.mov)
- `thumbnails/` - Master artwork (master-16x9.psd, master-square.psd)
- `assets/` - Final media files (video/, images/, audio/, graphics/) with AssetID naming
- `rundown/media-list/` - Symlinks to assets for vMix playlists (enumerated with parent references)
- `scripts/` - Generated scripts (6 formats: hardcopy, teleprompter, director, media-list, flat-text, source.md)
- `exports/` - Distribution content (blocks, full episode, audio, subtitles, platform-specific thumbnails)
- `info.md` - Episode metadata (reserved for future filesystem sync)
- `{EPISODE}-rundown.json` - Complete rundown structure export

**CRITICAL**: Rundown content is currently stored 100% in database, NOT filesystem. Scripts are generated from database single source of truth.

### Rundown Items (Database Records)
Each rundown item is a **PostgreSQL database record** in the `rundown_items` table with:
- **Parent Relationship**: Links to `rundown_id` (which episode it belongs to)
- **Optional Child Relationship**: May link to `segment_id` for segment-type items
- **Script Storage**: `script_content` TEXT field contains markdown with YAML frontmatter
- **Metadata Fields**: `title`, `slug`, `item_type`, `order_in_rundown`, `duration`, `status`, etc.
- **Asset References**: Media files stored in `/mnt/sync/disaffected/episodes/{episode}/assets/`

**YAML frontmatter format example** (stored in `script_content` field):
```yaml
---
id: '12345'
slug: segment-title
type: segment
order: 10
index: 10    # New index field for placement logic
duration: "00:03:30"
status: draft
title: "Segment Title"
---
# Content here
```

### Rundown Item Placement System
**Index-Based Placement Logic** (replaces hardcoded order assignment):

1. **Cold Open Rule**: Always gets `index: 1` regardless of placement
2. **Default Placement**: New items placed after selected item `+10`
3. **Conflict Resolution**: If index exists, use `+5` fallback  
4. **Filename Enumeration**: Database setting controls filename format:
   - Enabled: `001-Cold-Open.md`, `010-Segment-Title.md`
   - Disabled: `Cold-Open.md`, `Segment-Title.md`

### Rundown Normalization System
**API Endpoint**: `POST /rundown/{episode}/normalize`

**Normalization Rules**:
- Round non-multiple-of-10 indexes up to next multiple of 10
- Handle conflicts with cascading bumps (+10 increments)
- Sync `order` field with `index` field
- Rename files based on enumeration setting
- Preserve existing multiple-of-10 indexes

### Content Types
- **Segments**: Main content blocks (interviews, discussions)
- **Ads**: Advertisement blocks with customer metadata
- **Promos**: Promotional content for shows/events
- **CTAs**: Call-to-action prompts
- **Trans**: Transition elements with audio/timing

## API Endpoints

### Core Endpoints
- `GET /episodes` - List all episodes
- `GET /episodes/{episode}/rundown` - Get rundown items
- `POST /rundown/{episode}/reorder` - Reorder rundown items
- `POST /rundown/{episode}/item` - Create new rundown item

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user

### Media & Assets
- `POST /proc_vid` - Upload video files for processing
- `POST /upload_image` - Upload image files
- `GET /api/assets/` - List assets
- `POST /api/assets/` - Upload asset

## Authentication System

The system supports dual authentication:
1. **JWT Tokens**: Standard user authentication with role-based access
2. **API Keys**: Service-to-service authentication

Use `get_current_user_or_key` dependency for endpoints that accept both auth methods.

## RBAC (Role-Based Access Control) System

**📖 Complete Reference**: See [`docs/RBAC_AUTHENTICATION_GUIDE.md`](docs/RBAC_AUTHENTICATION_GUIDE.md) for comprehensive documentation.

Show-Build implements enterprise-grade RBAC with 11 database tables providing:

### Core Features
- **Hierarchical Roles**: 5 built-in levels (Super Admin → Viewer)  
- **Granular Permissions**: 25+ permissions with resource.action naming
- **User Groups**: Organization-scoped user collections
- **Permission Overrides**: Direct user permission grants/denials
- **Audit Trail**: Complete logging of all RBAC changes

### Key Files
- **Models**: `app/models_rbac.py` - RBAC database models
- **Service**: `app/rbac_service.py` - Permission checking and management
- **API**: `app/rbac_router.py` - RBAC REST endpoints (/api/rbac/*)
- **Migration**: Applied via Alembic (0e73074190a2_add_rbac_system.py)

### Quick Start
```bash
# Seed default permissions and roles
docker exec show-build-server python /app/seed_rbac.py

# Create admin API key  
docker exec show-build-server python /app/create_test_api_key.py

# Check system status
curl -H "X-API-Key: YOUR_KEY" http://localhost:8888/api/rbac/system-status
```

### Permission Hierarchy
1. **Super Admin** (`admin.all`) - Full system access
2. **Organization Admin** - Full organization control
3. **Content Manager** - Show/episode management  
4. **Content Editor** - Content editing only
5. **Viewer** - Read-only access

### Database Tables
- `permissions`, `roles`, `groups`, `users` (core entities)
- `user_roles`, `user_groups`, `group_roles`, `role_permissions` (relationships)
- `user_permission_overrides`, `rbac_audit_log`, `api_keys` (overrides/audit)

**⚠️ Important**: Always use the RBAC API endpoints for permission management. Direct database manipulation can break permission inheritance and audit trails.

## Database Models

### Core Models
- **User**: Authentication and user management (`app/models_user.py`)
- **Organization/Show/Episode**: Content hierarchy (`app/models_v2.py`)
- **AssetIDRegistry**: Asset tracking system (`app/models_assetid.py`)
- **ProcessingJob**: Background job tracking (`app/models.py`)

### Test Data Management
**🧪 ALL CONTENT TABLES** include `is_test_data` boolean field to separate test/dummy data from production:
- Use `is_test_data=True` for test episodes, users, content
- Production queries should filter `WHERE is_test_data = FALSE`
- Test data uses naming: episodes `900X`, titles `TEST: ...`, users `test*`

**📖 Complete Guide**: See [`docs/TEST_DATA_MANAGEMENT.md`](docs/TEST_DATA_MANAGEMENT.md) for usage examples, API filtering, and bulk operations.

## Testing and Development

### Running Tests
```bash
# Frontend tests
cd disaffected-ui && npm test

# Backend tests (if implemented)
cd app && python -m pytest
```

### Development Workflow
1. Make changes to code
2. For backend: `docker compose up --build server`
3. For frontend: `npm run serve` in `disaffected-ui/`
4. Test changes at `http://192.168.51.210:8091` (frontend) and `http://192.168.51.210:8888` (backend)

### Health Check
- Backend health: `GET /health`
- Database connectivity included in health response

## Color System and Theming

Colors are centralized in `disaffected-ui/src/utils/themeColorMap.js`:
- **Segment Types**: Each type (segment, ad, promo, etc.) has dedicated colors
- **Status Colors**: draft, approved, production, promotion, completed states
- **Implementation**: Uses Vuetify theme colors with fallbacks

## Key Configuration Files

- `docker-compose.yml` - Multi-service Docker setup
- `app/requirements.txt` - Python dependencies
- `disaffected-ui/package.json` - Node.js dependencies
- `app/database.py` - Database connection configuration
- `disaffected-ui/src/plugins/vuetify.js` - Vuetify theme configuration

## File Compatibility

The system maintains **format compatibility** for future Obsidian integration:
- YAML frontmatter structure matches Obsidian conventions (stored in database `script_content` field)
- Directory organization follows Obsidian structure (media in `assets/`, reserved `rundown/` for future)
- Markdown format maintained in database for eventual filesystem mirroring
- When filesystem integration is implemented, no data migration will be required

## Common Development Tasks

### Adding New API Endpoints
1. Create router in `app/{feature}_router.py`
2. Include in `app/main.py` with appropriate prefix
3. Add authentication dependencies if needed

### Adding Frontend Components
1. Create component in `src/components/`
2. Register in router if it's a view
3. Follow Vue 3 Composition API patterns
4. Use Vuetify components for consistency

### Database Changes
1. Modify models in `app/models*.py`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. **⚠️ CRITICAL RULE**: Before any migration that deletes/drops colors, users, or content (unless flagged 'dev'), you MUST:
   - Ask user permission with specific details of what will be deleted
   - Explain consequences clearly
   - Create backup using: `./scripts/backup_before_migration.sh`
4. Apply migration: `alembic upgrade head`

### Asset Processing
- Video files go to `/shared_media/preproc/working/{id}/`
- Images go to `/shared_media/images/{id}/`
- MQTT used for processing job coordination

## Environment Variables

Key environment variables (see `docker-compose.yml`):
- `JWT_SECRET_KEY` - JWT signing key
- `DATABASE_URL` - PostgreSQL connection string
- `MEDIA_ROOT` - Media files base path (`/home`)

## Troubleshooting

### 🚨 **START HERE FOR ANY FRONTEND ISSUE** 🚨

**⚠️ PRIORITY REFERENCE**: [`DEBUG_FIRST.md`](DEBUG_FIRST.md) - **READ THIS FIRST**

**Quick Debug Command** (run immediately for any unexplained frontend issue):
```bash
./scripts/debug-frontend.sh
```

This catches 99% of common frontend issues in 30 seconds, including:
- ⭐ **Template ref naming conflicts** (most common cause of form resets)  
- ⭐ **API connectivity issues**
- ⭐ **Vue mounting problems**
- ⭐ **Backend service status**

**📋 Complete Debugging Standards**: [`docs/DEBUGGING_STANDARDS.md`](docs/DEBUGGING_STANDARDS.md)

---

### Common Issues
- **Database connection**: Check PostgreSQL container status
- **File permissions**: Ensure Docker user (1000:1001) can access mounted volumes
- **Frontend build**: Clear `node_modules` and reinstall if build fails
- **MQTT issues**: Check mosquitto broker container

### Vue App Mounting Issues ⚠️
**CRITICAL**: If experiencing unexplainable errors, duplications, or old app versions flashing, immediately check Vue app mounting logic:
- See `/docs/VUE_APP_MOUNTING_WARNING.md` for comprehensive diagnosis
- Look for duplicate Vue app instances in console and browser DevTools
- Check for missing `unmount()` calls in main.js during hot module reload

### Vue Template Ref vs Reactive Variable Naming Conflicts ⚠️
**CRITICAL BUG - CAUSES 80% OF VUE ISSUES**: Template `ref` names conflicting with Composition API reactive variables cause component mounting failures, modal issues, and reactivity breakdowns.

**📖 COMPLETE DEBUGGING GUIDE**: [`docs/VUE_TEMPLATE_REF_CONFLICTS.md`](docs/VUE_TEMPLATE_REF_CONFLICTS.md)

**Problem Pattern:**
```vue
<template>
  <v-form ref="episodeForm">  <!-- ❌ Conflicts with reactive var -->
    <v-text-field v-model="episodeForm.title" />
  </v-form>
</template>

<script>
const episodeForm = ref({title: ''})  // ❌ Same name as template ref
</script>
```

**Solution:**
```vue
<template>
  <v-form ref="episodeFormRef">  <!-- ✅ Different name -->
    <v-text-field v-model="episodeForm.title" />
  </v-form>
</template>

<script>
const episodeForm = ref({title: ''})  // ✅ Clear separation
</script>
```

**Symptoms:**
- Form values mysteriously reset to initial state
- Reactivity breaks without obvious cause  
- Data appears to load correctly but then disappears
- Vue DevTools shows conflicting reactive sources

**Prevention:**
- Use `Ref` suffix for all template refs: `formRef`, `dialogRef`, `tableRef`
- Use descriptive names for reactive variables: `formData`, `modalData`
- Scan for conflicts: `grep -n 'ref="' *.vue` then check for matching variable names

**Quick Conflict Scan:**
```bash
# In Vue component directory - shows duplicate ref names
cd disaffected-ui/src
grep -rn 'ref="[^"]*"' . | sed 's/.*ref="\([^"]*\)".*/\1/' | sort | uniq -d

# Comprehensive debugging scan (recommended for all frontend issues)
./scripts/debug-frontend.sh
```

**📖 Complete Debugging Guide**: See [`docs/DEBUGGING_STANDARDS.md`](docs/DEBUGGING_STANDARDS.md) for systematic debugging checklist and standards.

### Episode Data Loading Issues
- **Race Condition Logic**: Avoid implementing race condition prevention logic in `ContentEditor.vue` that blocks duplicate calls. This can prevent legitimate episode loading. The component should handle loading states naturally without blocking subsequent calls.
- **Field Name Consistency**: Frontend expects `duration` field from episode info.md files, not `total_runtime`. Ensure all components use `duration` consistently.
- **Loading State Management**: Initialize `loadingRundown: false` in ContentEditor.vue data to prevent blocking initial episode loads.

### Logs
- Backend: `docker logs show-build-server`
- Frontend: Browser console and network tab
- Database: `docker logs show-build-postgres`
- debugging front end look at ./scripts/debug-frontend.sh
- provide all urls using lan-accessible ip.  never localhost.
- cache clearing requests can run scripts/clean-npm-servers.sh for a thorough job.
- xtts requests made from anywhere in the show-build environment should use xtts settings in the database which were defined in the settings.

### Ollama Configuration
**CRITICAL**: Correct Ollama server address is `http://192.168.51.197:11434` (NOT .223)

Database configuration:
```sql
-- Verify Ollama config
SELECT service, config_key, config_value, is_enabled
FROM api_configs WHERE service = 'ollama';
```

Available models on 192.168.51.197:
- deepseek-r1:8b, llama3:latest, mistral:7b, mistral-large:latest
- wizardlm-uncensored:13b, Qwen2.5-Coder:7b/32b, codellama:34b

Test connectivity: `curl -s http://192.168.51.197:11434/api/tags`
- create announcement means to create an html file as specified by the user and put it in the docs/announcements directory so that it will automatically display in the dashboard.