# Architecture & Setup

Core technical architecture, deployment configuration, and system setup documentation.

---

## From: 01_architecture.markdown

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
---

## From: 02_setup_and_deployment.markdown

# Setup and Deployment

## Overview
This document outlines the setup and deployment process for the Disaffected Production Suite, including launch commands, dependency management, Docker configuration, and verification tests.

## Prerequisites
- **Node.js**: v16+ for frontend
- **Python**: 3.11 for backend
- **Docker**: For containerized deployment
- **Docker Compose**: V2 for multi-container orchestration
- **NPM**: For frontend package management

## Setup Instructions
1. **Clone Repository**:
   ```bash
   git clone /path/to/repository
   cd /mnt/process/show-build
   ```

2. **Install Frontend Dependencies**:
   ```bash
   cd disaffected-ui
   npm install --legacy-peer-deps
   ```

3. **Verify Docker Installation**:
   ```bash
   docker --version
   docker-compose --version
   ```

## Docker Configuration
- **Containers**:
  - `show-build-server`: FastAPI backend, runs on `http://192.168.51.210:8888/`
  - `mosquitto`: MQTT broker for real-time communication
  - Additional services: Whisper API, Node-RED
- **Volume Mounts**:
  - Host path `/mnt/sync/disaffected/episodes/` maps to `/home/episodes` in the `show-build-server` container for episode data.
  - Host path `/mnt/process/show-build/app/storage/` maps to `/app/storage/` for JSON storage (users, API keys).
- **Networking**:
  - Docker network: `video-post`
  - MQTT broker configured with `mosquitto.conf`:
    ```conf
    listener 1883 0.0.0.0
    allow_anonymous true
    ```
  - Backend accessible at `http://192.168.51.210:8888/` (host) or `http://show-build-server:8888/` (container).
- **Docker Compose Example**:
  ```yaml
  version: '3.8'
  services:
    show-build-server:
      image: show-build-fastapi
      volumes:
        - /mnt/sync/disaffected/episodes/:/home/episodes
        - /mnt/process/show-build/app/storage/:/app/storage
      ports:
        - "8888:8888"
      networks:
        - video-post
    mosquitto:
      image: eclipse-mosquitto
      volumes:
        - /mnt/process/show-build/tools/mosquitto.conf:/mosquitto/config/mosquitto.conf
      ports:
        - "1883:1883"
      networks:
        - video-post
  networks:
    video-post:
      driver: bridge
  ```

## Launch Commands
1. **Backend (FastAPI)**:
   ```bash
   cd /mnt/process/show-build
   docker compose up -d show-build-server
   ```
   - Runs at `http://192.168.51.210:8888/`
   - Health check: `curl http://192.168.51.210:8888/health`

2. **Frontend (Vue.js)**:
   ```bash
   cd /mnt/process/show-build/disaffected-ui
   npm run serve
   ```
   - Runs at `http://192.168.51.210:8080/`

## Configuration
- **vue.config.js**:
  ```javascript
  module.exports = {
    transpileDependencies: true,
    devServer: {
      host: '0.0.0.0',
      port: 8080,
      allowedHosts: 'all',
      proxy: {
        '/api': {
          target: 'http://192.168.51.210:8888',
          changeOrigin: true,
          secure: false,
          pathRewrite: { '^/api': '' }
        }
      }
    }
  }
  ```
- **Docker Compose**: Ensure `mosquitto.conf` is mounted and configured for remote access.

## Verification Tests
- **Frontend Access**:
  ```bash
  curl http://192.168.51.210:8080/
  ```
- **Backend Health**:
  ```bash
  curl http://192.168.51.210:8888/health
  ```
- **API Proxy**:
  ```bash
  curl http://192.168.51.210:8080/api/health
  ```

## Dependencies
- **Frontend**: Vue 3.2.13, Vuetify 3.8.8, Vue Router 4.5.1, Axios 1.9.0
- **Backend**: FastAPI, Python 3.11 (see `/app/requirements.txt`)
- **Infrastructure**: Docker, Eclipse Mosquitto MQTT

*Last Updated: July 8, 2025*
---

## From: PROJECT_ARCHITECTURE_REPORT.md


---

## From: 00_rehydration_main.markdown

# Disaffected Production Suite Rehydration Guide

## Overview
The Disaffected Production Suite is a web-based application for streamlining broadcast content creation for the "Disaffected" podcast and TV show, replacing Obsidian-based workflows while maintaining compatibility with Markdown files, YAML frontmatter, and directory structure. As of July 9, 2025, 18/19 critical issues are resolved, with cue modals (Issue 18), virtual scrolling, asset/template management, modal naming consistency, and Obsidian plugin alignment pending. The project uses Vue.js, FastAPI, MQTT, and Dockerized deployment, focusing on pre-production (scripting, asset management), production, and promotion phases.

## Project Goals
- **Primary Objective**: Create a unified platform for broadcast content creation, editing, and management, reducing reliance on fragmented tools (Obsidian, Word, spreadsheets).
- **Core Mission**: Streamline content creation from script to screen, supporting pre-production (scripting, asset management), production (live show management), and promotion (social media, distribution).
- **Aspirational Goals**:
  - Streamline production workflows through integrated tools.
  - Minimize errors from manual handoffs and version control.
  - Enable remote collaboration and scalability for production teams.
- **Target Outcomes**:
  - Achieve fast and responsive editing performance.
  - Ensure high reliability for critical operations.
  - Promote high user satisfaction among production teams.
  - Complete remaining tasks (cue modals, virtual scrolling, asset/template management) to achieve production-ready status.

## System Overview
- **Frontend**: Vue.js 3.2.13 with Vuetify 3.8.8, running at `http://192.168.51.210:8080/`.
- **Backend**: FastAPI (Python 3.11), Dockerized, running at `http://192.168.51.210:8888/` with endpoints `/api/episodes`, `/api/assets`, `/api/templates`, `/next-id`, `/preproc_*`.
- **Data Storage**: File-based at `/mnt/sync/disaffected/episodes/` (host) or `/home/episodes` (container), compatible with Obsidian; JSON storage for users and API keys at `/app/storage/`.
- **Real-time Communication**: MQTT (Eclipse Mosquitto) for live updates.
- **Authentication**: JWT-based with bcrypt hashing, managed via `useAuth.js` (frontend) and `/api/login` (backend).
- **Dependencies**: Requires `axios`, `vue-toastification`, `vuedraggable` (see `disaffected-ui/package.json`).

## Project Status (July 9, 2025)
- **Issues Resolved**: 18/19 (Issues 1–7, 9–13, 15–17, 19).
- **Pending Issue**: Issue 18 (implement `VoModal.vue`, `NatModal.vue`, `PkgModal.vue`).
- **Pending Tasks**:
  - Implement virtual scrolling in `RundownManager.vue` for performance.
  - Complete asset/template management in `AssetsView.vue`, `TemplatesView.vue`.
  - Standardize modal naming in `ContentEditor.vue` (e.g., `show[Name]Modal`).
  - Align Obsidian plugin (`main.js`) with frontend cue types (`VO`, `NAT`, `PKG`).
  - Prepare for potential new cue types (`VOX`, `MUS`, `LIVE`).
- **Validation**: Use DeepSeek V3 (`python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code`) to verify code changes.

## Table of Contents
The following documents are critical for rehydrating an LLM with the project’s context. Deprecated files (e.g., `COLOR_SYSTEM_GUIDE.md`, `rundown_item_types.md`) have been removed.

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | Technical stack, file structure, and system components. |
| [Setup and Deployment](setup_and_deployment.md) | Installation, launch commands, dependency management, and Docker configuration. |
| [Features and Integrations](features_and_integrations.md) | Implemented features, API integrations, and workflows. |
| [Style Guide](style_guide.md) | UI/UX guidelines and color system. |
| [Migration and Workflow](migration_and_workflow.md) | Obsidian migration strategy and development workflow. |
| [TODO and Issues](todo_and_issues.md) | Technical debt, known issues, and pending tasks (updated to reflect 18/19 issues resolved). |
| [Modal Usage](MODAL_USAGE.md) | Conventions for modal naming and implementation. |

## Getting Started
Refer to [Setup and Deployment](setup_and_deployment.md) for launching the frontend (`npm run serve`) and backend (`docker compose up -d show-build-server`). Content creators should review [Modal Usage](MODAL_USAGE.md) and [Features and Integrations](features_and_integrations.md) for cue management. Developers should start with [Architecture](architecture.md) and verify completion of cue modals (`VoModal.vue`, `NatModal.vue`, `PkgModal.vue`), virtual scrolling (`RundownManager.vue`), and asset/template management (`AssetsView.vue`, `TemplatesView.vue`). Test critical endpoints using:
- Frontend: `curl http://192.168.51.210:8080/`
- Backend health: `curl http://192.168.51.210:8888/health`
- Modals: Navigate to `/content-editor/0228`, trigger `VO`, `NAT`, `PKG` modals, verify script updates.
- Performance: Load `/rundown/0228` with >100 items, check scrolling in DevTools (Performance tab).

## Glossary
- **Rundown Items**: Structured elements (e.g., `segment`, `ad`, `promo`) defining the sequence of a broadcast episode.
- **Cue Types**: Specific media or script elements (e.g., `VO`, `NAT`, `PKG`) inserted into scripts.
- **Obsidian Compatibility**: Support for Markdown files, YAML frontmatter, and directory structure used by Obsidian.

*Last Updated: July 9, 2025*
---

