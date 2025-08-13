# Show-Build API Endpoints Documentation

Complete reference for all API endpoints in the Show-Build broadcast content management system.

## Network Environment
- **Server**: Ubuntu 192.168.51.210 (accessed via SSH from Windows/WSL 192.168.51.225)
- **Frontend**: http://192.168.51.210:8080 (Vue.js dev server)
- **Backend API**: http://192.168.51.210:8888 (FastAPI in Docker)
- **MQTT Broker**: 192.168.51.210:1883
- **Documentation**: http://192.168.51.210:8888/docs/api

## Legend
- 🔒 = Requires authentication (JWT token or API key)
- 🔄 = Background processing with job tracking
- 📁 = File system operations
- 🎬 = Media processing

---

## 1. CORE SYSTEM ENDPOINTS

### Health & Info
- `GET /` - HTML landing page with API documentation
- `GET /health` - Basic health check
- `GET /show-info` - Show metadata (title, description, episode path)

### MQTT Communication  
- `POST /publish/` - Send MQTT messages to broker
- `GET /listen/` - Subscribe to MQTT topic stream

---

## 2. AUTHENTICATION SYSTEM (`auth/router.py`)

### User Management
- `POST /login` - JWT token authentication
- `POST /users` - Create new user account (admin only)
- `GET /users` - List all users (admin only)
- `GET /test-auth` - Test protected route access

### API Key Management
- `POST /apikey` - Generate API key for external access 🔒
- `GET /apikeys` - List all API keys (admin only) 🔒
- `GET /apikeys/debug` - Debug API key storage (admin only) 🔒
- `POST /debug/hash` - Debug password hashing

---

## 3. EPISODE MANAGEMENT

### Main Episode Endpoints (`main.py`) - **File-Based Legacy System**
- `GET /episodes` - List all episodes with metadata from `info.md` 📁
- `GET /episodes/{episode_number}/rundown` - Get rundown items with frontmatter 📁
- `GET /episodes/{episode_number}/info` - Get episode info from `info.md` 🔒📁
- `PUT /episodes/{episode_number}/info` - Update episode info in `info.md` 🔒📁
- `GET /rundown/{episode_number}/debug` - Debug rundown parsing issues 📁

### Enhanced Episode Router (`episodes_router.py`) - **Database-Driven Modern System**
- `GET /episodes/` - List episodes (database version) 🔒
- `GET /episodes/{episode_id}` - Get episode details 🔒
- `POST /episodes/{episode_id}/scaffold` - Create episode structure 🔒📁
- `GET /episodes/{episode_id}/rundown` - Get rundown files 🔒📁
- `POST /episodes/{episode_id}/compile` - **Background script compilation** 🔒🔄
- `GET /episodes/{episode_id}/compile/download` - Download compiled script 🔒📁
- `POST /episodes/{episode_id}/extract-quotes` - **Background quote extraction** 🔒🔄
- `GET /episodes/{episode_id}/quotes` - Get extracted quotes 🔒
- `GET /episodes/{episode_id}/assets/{asset_type}` - List episode assets 🔒📁

### Rundown Management (File-Based)
- `POST /rundown/{episode_number}/reorder` - Reorder segments (updates YAML) 📁
- `POST /rundown/{episode_number}/item` - Create new rundown item 📁

---

## 4. ADVANCED DATABASE PROCESSING SYSTEM

### **Background Job System** (`main.py`)
- `POST /episodes/{episode_id}/compile-script` - **Celery background script compilation** 🔒🔄
- `GET /jobs/{job_id}/status` - Check job progress and status 🔒
- `WebSocket /ws/{client_id}` - **Real-time job updates**

---

## 5. MEDIA PROCESSING

### File Uploads
- `POST /proc_vid` - Upload video files for processing (up to 50MB) 🎬
- `POST /upload_image` - Upload image files (PNG, JPG, GIF) 🎬
- `POST /next-id` - Generate unique asset IDs

### Asset Management (`assets_router.py`)
- `GET /api/assets` - List assets in directory tree 🔒📁
- `POST /api/assets/folder` - Create new folder 🔒📁
- `POST /api/assets/upload` - Upload multiple files 🔒🎬
- `PUT /api/assets/rename` - Rename asset 🔒📁
- `DELETE /api/assets` - Delete asset 🔒📁
- `GET /api/assets/{file_path:path}` - Download/serve asset file 🔒📁

---

## 6. WORKFLOW CONFIGURATION

### API Configuration (`api_config_router.py`)
- `GET /api-configs` - Get all API configurations 🔒
- `POST /api-configs` - Save API configurations 🔒
- `GET /api-configs/{workflow}` - Get workflow-specific config 🔒
- `POST /api-configs/service` - Update service configuration 🔒
- `POST /test/{service}` - Test external API connections 🔒
- `DELETE /api-configs` - Reset all configurations 🔒

### Template System (`templates_router.py`)
- `GET /api/templates` - List all templates 🔒
- `POST /api/templates` - Create new template 🔒
- `PUT /api/templates/{template_id}` - Update template 🔒
- `DELETE /api/templates/{template_id}` - Delete template 🔒

---

## 7. LEGACY/TEST ENDPOINTS

### Development/Debug
- `GET /protected-endpoint` - Test auth protection 🔒
- `POST /secured-route` - Test secured operations 🔒

---

## ARCHITECTURAL INSIGHTS

### 🔄 Dual System Architecture
The Show-Build system operates with two parallel architectures:

**File-Based Legacy System** (`main.py`)
- Direct file manipulation and YAML frontmatter parsing
- Immediate synchronous responses
- Compatible with existing Obsidian workflows
- Production-ready and stable

**Database-Driven Modern System** (`episodes_router.py` + background services)
- Background Celery job processing
- PostgreSQL database for rich metadata
- Real-time WebSocket progress updates
- Designed for coordination and conflict prevention

### 🔒 Authentication Model
- **JWT Tokens**: Browser-based authentication via `/login`
- **API Keys**: Machine-to-machine authentication via `/apikey`
- **Permission Levels**: Admin vs regular user access
- **Dual Auth Support**: Most endpoints accept either token type

### 🎬 Processing Pipeline Comparison

| Feature | Legacy System | Modern System |
|---------|---------------|---------------|
| Script Compilation | Synchronous, immediate | Background jobs with progress |
| Quote Extraction | File-based only | Database + background processing |
| Conflict Prevention | Manual coordination | Automated job queuing |
| Real-time Updates | None | WebSocket notifications |
| Scalability | Limited | Highly scalable |

### 📁 File System Integration
- **Episode Storage**: `/home/episodes/{episode_number}/`
- **Asset Storage**: `/shared_media/`
- **Configuration**: JSON files in `app/storage/`
- **Obsidian Compatibility**: Full markdown + YAML frontmatter support
- **Docker Volumes**: Host filesystem mounted into containers

### 🚀 Background Processing Features
- **Job Types**: Script compilation, quote extraction, media processing
- **Progress Tracking**: 0-100% completion with status messages
- **Error Handling**: Detailed error messages and job failure tracking
- **Real-time Communication**: WebSocket updates push job status to clients
- **Job Persistence**: All job history stored in PostgreSQL database

---

## MIGRATION STATUS

### ✅ Implemented and Ready
- Complete database schema (Episodes, Jobs, Assets, etc.)
- Background job processing with Celery
- WebSocket real-time updates
- Enhanced Docker Compose stack
- Script compilation service migrated from CLI

### 🔄 Dual Operation Mode
- Both file-based and database systems coexist
- Gradual migration path available
- No breaking changes to existing workflows
- Legacy endpoints remain fully functional

### 📋 Next Steps for Full Migration
1. Deploy enhanced Docker stack with PostgreSQL + Redis
2. Test background processing with real episode data
3. Migrate remaining CLI tools to background services
4. Add file watching for automatic processing triggers
5. Phase out legacy endpoints gradually

---

*Last updated: 2025-08-10*
*Show-Build Version: Enhanced Database Integration*