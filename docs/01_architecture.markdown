# Disaffected Production Suite Architecture

## Overview
The Disaffected Production Suite is a web-based application for broadcast content creation, replacing Obsidian workflows while maintaining compatibility with its Markdown-based file structure. It uses a modern stack with Vue.js for the frontend, FastAPI for the backend, and MQTT for real-time communication, all deployed via Docker.

## Technical Stack
- **Frontend**:
  - Framework: Vue.js 3.2.13, Vuetify 3.8.8, Vue Router 4.5.1, Axios 1.9.0
  - Location: `/mnt/process/show-build/disaffected-ui/`
  - Build System: Vue CLI
- **Backend**:
  - Framework: FastAPI, Python 3.11
  - Location: `/mnt/process/show-build/app/`
  - Deployment: Docker (`show-build-server` image)
- **Real-time Communication**: Eclipse Mosquitto MQTT
- **Storage**: File-based at `/mnt/sync/disaffected/episodes/` (host) or `/home/episodes` (container), JSON storage for users and API keys (`/app/storage/`)
- **Authentication**: JWT-based with bcrypt hashing
- **Deployment**: Docker Compose with services (FastAPI, MQTT, Whisper API, Node-RED)

## File Structure
```
/mnt/process/show-build/
├── app/                           # Backend FastAPI application
│   ├── main.py                   # Core FastAPI app
│   ├── utils/
│   │   ├── validator.py         # YAML frontmatter validation
│   │   └── id.py                # Asset ID generation
│   ├── auth/                    # Authentication logic
│   └── storage/                 # JSON storage (users, API keys)
├── disaffected-ui/               # Frontend Vue.js application
│   ├── src/
│   │   ├── components/
│   │   │   ├── ContentEditor.vue     # Main split-view editor
│   │   │   ├── RundownManager.vue    # Rundown reordering
│   │   │   ├── ColorSelector.vue     # Color configuration UI
│   │   │   └── content-editor/      # Modular editor components
│   │   │       ├── ShowInfoHeader.vue  # Episode metadata header
│   │   │       ├── RundownPanel.vue    # Rundown sidebar
│   │   │       └── EditorPanel.vue     # Content editing area
│   │   ├── composables/
│   │   │   └── useContentEditor.js  # Shared editor state logic
│   │   ├── utils/
│   │   │   ├── themeColorMap.js     # Color system
│   │   │   └── vuetifyColorNames.js # Color name mappings
│   │   └── plugins/
│   │       └── vuetify.js          # Theme configuration
├── docs/                          # Documentation
└── docker-compose.yml             # Container orchestration
```

## Data Architecture
- **Location**: `/mnt/sync/disaffected/episodes/` (host) or `/home/episodes` (container)
- **Structure**:
  - Episode folders: `0228/`, `0229/`, `0230/`, etc.
  - Subdirectories per episode:
    - `assets/`: Media files (`audio/`, `graphics/`, `images/`, `video/`, `quotes/`, `thumbnails/`)
    - `captures/`: Raw recordings
    - `exports/`: Processed outputs
    - `info.md`: Episode metadata
    - `preshow/`: Pre-show materials
    - `rundown/`: Script and rundown items
- **Asset Naming**: Files renamed to match slugs (lowercase, hyphens for spaces, e.g., `show-logo.png`).

## Key Components
- **ContentEditor.vue**: Split-view editor for Markdown and metadata, with cue insertion toolbar.
- **RundownManager.vue**: Drag-and-drop rundown reordering.
- **ColorSelector.vue**: UI for configuring Vuetify theme colors.
- **main.py**: FastAPI backend with endpoints for rundown management, authentication, and uploads.
- **themeColorMap.js**: Centralized color management for rundown items and UI elements.

*Last Updated: July 8, 2025*