# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Show-Build is a full-stack broadcast rundown management system designed for the Disaffected media ecosystem. It serves as a drop-in replacement for Obsidian-based workflows while maintaining complete file format compatibility. The system operates on the same markdown files and organizational structure as Obsidian.

## Architecture

### Backend (FastAPI + Python)
- **Main Application**: `app/main.py` - Central FastAPI application with comprehensive API endpoints
- **Database**: PostgreSQL with SQLAlchemy ORM (`app/database.py`)
- **Authentication**: JWT-based auth system in `app/auth/` with role-based access control
- **Background Processing**: Celery with Redis for async tasks (`app/celery_app.py`)
- **File Storage**: Episode data stored in `/home/episodes` (container) or `/mnt/sync/disaffected/episodes/` (host)

### Frontend (Vue 3 + Vuetify)
- **Framework**: Vue 3 with Composition API, Vuetify 3 for UI components
- **State Management**: Pinia stores, composables in `src/composables/`
- **Routing**: Vue Router with authentication guards (`src/router/index.js`)
- **Components**: Modular Vue components in `src/components/`

### Key Components
- **RundownManager.vue**: Drag-and-drop rundown editing with virtual scrolling
- **ContentEditor.vue**: Markdown content editing with live preview
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

### Episode Data Structure
Episodes are stored as directories in `/home/episodes/{episode_number}/`:
- `rundown/` - Individual markdown files for each rundown item
- `info.md` - Episode metadata with YAML frontmatter
- `assets/` - Media files and assets

### Rundown Items
Each rundown item is a markdown file with YAML frontmatter:
```yaml
---
id: '12345'
slug: segment-title
type: segment
order: 10
duration: "00:03:30"
status: draft
title: "Segment Title"
---
# Content here
```

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

## Database Models

### Core Models
- **User**: Authentication and user management (`app/models_user.py`)
- **Organization/Show/Episode**: Content hierarchy (`app/models_v2.py`)
- **AssetIDRegistry**: Asset tracking system (`app/models_assetid.py`)
- **ProcessingJob**: Background job tracking (`app/models.py`)

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
4. Test changes at `http://localhost:8080` (frontend) and `http://localhost:8888` (backend)

### Health Check
- Backend health: `GET /health`
- Database connectivity included in health response

## Color System and Theming

Colors are centralized in `disaffected-ui/src/utils/themeColorMap.js`:
- **Segment Types**: Each type (segment, ad, promo, etc.) has dedicated colors
- **Status Colors**: draft, approved, production, completed states
- **Implementation**: Uses Vuetify theme colors with fallbacks

## Key Configuration Files

- `docker-compose.yml` - Multi-service Docker setup
- `app/requirements.txt` - Python dependencies
- `disaffected-ui/package.json` - Node.js dependencies
- `app/database.py` - Database connection configuration
- `disaffected-ui/src/plugins/vuetify.js` - Vuetify theme configuration

## File Compatibility

The system maintains **complete Obsidian compatibility**:
- Same markdown file format
- Identical YAML frontmatter structure
- Same directory organization
- No data migration required

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
3. Apply migration: `alembic upgrade head`

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

### Episode Data Loading Issues
- **Race Condition Logic**: Avoid implementing race condition prevention logic in `ContentEditor.vue` that blocks duplicate calls. This can prevent legitimate episode loading. The component should handle loading states naturally without blocking subsequent calls.
- **Field Name Consistency**: Frontend expects `duration` field from episode info.md files, not `total_runtime`. Ensure all components use `duration` consistently.
- **Loading State Management**: Initialize `loadingRundown: false` in ContentEditor.vue data to prevent blocking initial episode loads.

### Logs
- Backend: `docker logs show-build-server`
- Frontend: Browser console and network tab
- Database: `docker logs show-build-postgres`