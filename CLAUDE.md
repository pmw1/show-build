# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Show-Build is a broadcast content management system that replaces Obsidian workflows while maintaining Markdown file compatibility. It's a full-stack application with Vue.js frontend, FastAPI backend, and Docker deployment targeting the Disaffected media production environment.

## Common Development Commands

### Frontend (Vue.js)
```bash
cd disaffected-ui
npm install --legacy-peer-deps    # Install dependencies (note: legacy flag required)
npm run serve                     # Development server at http://192.168.51.210:8080
npm run build                     # Production build
npm run lint                      # ESLint checking
npm test                         # Run Jest unit tests
npm run test:watch               # Watch mode for tests
```

### Backend (FastAPI)
```bash
cd /mnt/process/show-build
docker compose up -d             # Start all services (FastAPI + MQTT broker)
docker compose up --build       # Rebuild and start containers
docker compose down              # Stop services
docker logs show-build-server    # View backend logs
```

### Python Tools
```bash
cd tools
python compile-script-dev.py 0225 [--validate]    # Compile episode scripts
```

### Health Checks
```bash
curl http://192.168.51.210:8888/health           # Backend API health
curl http://192.168.51.210:8080/                 # Frontend access
```

## Architecture Overview

### Core Stack
- **Frontend**: Vue 3 + Vuetify 3 + Vue Router at `disaffected-ui/`
- **Backend**: FastAPI + Python 3.11 at `app/`
- **Messaging**: Eclipse Mosquitto MQTT broker
- **Storage**: File-based at `/mnt/sync/disaffected/episodes/` with JSON storage for users/API keys
- **Authentication**: JWT with bcrypt hashing
- **Deployment**: Docker Compose with volume mounts

### Key Architectural Patterns

**Episode Data Structure**:
```
/mnt/sync/disaffected/episodes/
├── 0228/                    # Episode folders by number
│   ├── assets/             # Media files (audio/, video/, graphics/, images/)
│   ├── rundown/            # Script and rundown items
│   ├── info.md             # Episode metadata
│   └── exports/            # Processed outputs
```

**Modal System Pattern**: New cue types follow standardized pattern:
1. Modal component in `disaffected-ui/src/components/modals/{Type}Modal.vue`
2. Integration in `ContentEditor.vue` with v-model binding
3. Button in `EditorPanel.vue` toolbar
4. Backend endpoint `/preproc_{type}` for uploads

**Color System**: Centralized in `disaffected-ui/src/utils/themeColorMap.js` with Vuetify theme integration and configurable via `ColorSelector.vue`.

### Critical Components

**ContentEditor.vue**: Main split-view editor combining rundown management and Markdown editing with modal system for cue insertion (VO, NAT, PKG, GFX, FSQ, SOT).

**RundownManager.vue**: Drag-and-drop interface with virtual scrolling for performance with large rundowns.

**Authentication Flow**: JWT tokens stored in localStorage with 48-hour expiry, managed via `composables/useAuth.js` composable.

### Path Management
All Python scripts use centralized `tools/paths.py`:
```python
from paths import EPISODE_ROOT, BLUEPRINTS, VALID_CUE_TYPES
```

### Network Configuration
- Frontend dev: `192.168.51.210:8080` with API proxy to backend
- Backend API: `192.168.51.210:8888` 
- MQTT broker: `192.168.51.210:1883`
- Docker network: `video-post` for inter-container communication

### Data Persistence
- **Episode files**: Obsidian-compatible Markdown with YAML frontmatter
- **User accounts**: `app/storage/users.json` with bcrypt hashes
- **API configurations**: `app/storage/api_keys.json`
- **Asset naming**: Files renamed to match slugs (lowercase, hyphens)

### Testing Infrastructure
- Jest configuration in `disaffected-ui/jest.config.js`
- Mocks for axios and Vuetify in `tests/mocks/`
- Unit tests focus on `ContentEditor.vue` and `RundownManager.vue`

## Documentation System

### Documentation Organization
Project documentation is organized in the `docs/` folder with two approaches:

**Individual Files** - For specific topics:
- `docs/01_architecture.markdown` - Technical architecture details
- `docs/02_setup_and_deployment.markdown` - Installation and deployment
- `docs/AUTHENTICATION_GUIDE.md` - JWT and API key authentication
- `docs/MODAL_USAGE.md` - Modal system conventions
- `tools/README.md` - Python utilities documentation

**Themed Development Chunks** - For focused development work:
```bash
./generate_dev_docs.sh
# Creates 6 themed documentation files:
# - docs/dev_architecture.md (setup, deployment, technical stack)
# - docs/dev_features.md (components, modals, cue system)
# - docs/dev_workflow.md (development practices, style guides)
# - docs/dev_auth.md (authentication patterns)
# - docs/dev_issues.md (current tasks, known issues)
# - docs/dev_api.md (API documentation, integrations)
```

### Complete Context Options
**Full Documentation:**
```bash
./generate_rehydrate.sh
# Creates docs/rehydrate.md with all documentation concatenated
```

**Chunked by Size:**
```bash
./generate_rehydrate.sh --chunk --chunk-size 2048
# Creates docs/rehydrate_chunk_1.md, docs/rehydrate_chunk_2.md, etc.
```

Use themed chunks for focused development work, or full rehydration for comprehensive project context.

## Development Notes

### Docker Volume Mounts
Host `/mnt/sync/disaffected/episodes/` maps to container `/home/episodes` for episode data sharing.

### MQTT Integration
Used for preprocessing job coordination with configuration in `tools/mosquitto.conf`. Backend publishes via `preproc_mqtt_pub.py` and listens via `preproc_mqtt_listen.py`.

### Authentication Requirements
Protected endpoints require `Authorization: Bearer {token}` header. Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 2880 = 48 hours).

### Obsidian Compatibility
Maintains full file format compatibility - same Markdown files and directory structure work with both Show-Build and Obsidian.

### Development Workflow
When making changes:
1. Test both frontend (`npm run serve`) and backend (`docker compose up -d`) locally
2. Run linting (`npm run lint`) and tests (`npm test`) before commits
3. Verify Docker container startup after changes
4. Test authentication flows work properly
5. Test with actual episode data in `/mnt/sync/disaffected/episodes/`
6. Update documentation in `docs/` folder as needed
7. Regenerate `docs/rehydrate.md` if providing context to other LLMs