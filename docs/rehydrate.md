------------------- filepath: docs/00_rehydration_main.markdown ----------------------
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





























------------------- filepath: docs/01_architecture.markdown ----------------------
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





























------------------- filepath: docs/02_setup_and_deployment.markdown ----------------------
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





























------------------- filepath: docs/03_features_and_integrations.markdown ----------------------
# Features and Integrations

## Overview
The Disaffected Production Suite provides features for pre-production content creation and integrates with external services via APIs and MQTT. This document details implemented features, API integrations, and workflows.

## Implemented Features
- **Content Editor (`ContentEditor.vue`)**:
  - Split-view Markdown and metadata editing
  - Cue insertion toolbar with shortcuts (Alt+G, Alt+Q, etc.)
  - Auto-save (3s inactivity or item switch)
  - Collapsible rundown panel
  - Accessibility features (high-contrast text, keyboard navigation)
- **Rundown Management (`RundownManager.vue`)**:
  - Drag-and-drop reordering with visual feedback
  - Automatic order assignment (increments of 10)
  - Optional filename prefixing toggle for Obsidian compatibility
- **Add New Rundown Item**:
  - Form-based creation with validation
  - Auto-generates IDs (`{type}_YYYYMMDD_###`)
  - Integrates with `/rundown/{episode_number}/item` endpoint
- **Color Management (`ColorSelector.vue`)**:
  - UI for selecting Vuetify theme colors
  - Persists selections in `localStorage`
  - Supports rundown item types and UI elements (pending synchronization with `themeColorMap.js`)

## API Integrations
- **Local AI Services**: Ollama, Whisper (content generation, transcription)
- **Cloud AI Services**: OpenAI, Anthropic, Google Gemini, X (Grok)
- **Media Services**: YouTube API, Vimeo API, AWS S3
- **Communication**: Slack, Discord, Twilio, email services (SendGrid, Mailgun, AWS SES)
- **Storage/Productivity**: Google Drive, Google Calendar
- **Development**: GitHub/GitLab, Zapier, custom webhooks
- **Specialized AI**: Stability AI (image generation), ElevenLabs (voice synthesis)
- **Social Media**: Twitter/X, Facebook, Instagram, LinkedIn, TikTok, Rumble

## Workflows
- **Content Creation**: AI-assisted script writing, media processing, storage, publishing
- **Live Production**: Real-time communication, emergency alerts, rundown updates
- **Post-Production**: Transcription, voice-over, version control, multi-platform distribution

*Last Updated: July 8, 2025*





























------------------- filepath: docs/04_migration_and_workflow.markdown ----------------------
# Migration and Workflow

## Overview
The Disaffected Production Suite is a drop-in replacement for Obsidian-based workflows, maintaining compatibility with Obsidian’s file formats and structure. This document outlines the migration strategy and development workflow.

## Obsidian Migration Strategy
- **Phase 1: Parallel Operation** (Current):
  - Both systems use `/mnt/sync/disaffected/episodes/` (host) or `/home/episodes` (container).
  - No data migration required; users can switch interfaces.
  - Maintains Markdown files, YAML frontmatter, and directory structure.
- **Phase 2: UI Transition**:
  - Introduce broadcast-specific features (e.g., cue management).
  - Train users on Show-Build interface.
  - Retain Obsidian compatibility.
- **Phase 3: Primary Platform**:
  - Show-Build becomes default interface.
  - Obsidian remains a backup option.
  - Full workflow automation implemented.

## Development Workflow
- **Verification**:
  - Confirm development setup and server processes.
  - Test changes visibility after deployment.
- **Build/Deploy**:
  - Frontend: `npm run build` in `/mnt/process/show-build/disaffected-ui/`
  - Backend: `docker compose up -d show-build-server`
- **Testing**:
  - Manual UI testing for interactions.
  - API tests via `curl` (e.g., `curl http://192.168.51.210:8888/health`).

*Last Updated: July 8, 2025*





























------------------- filepath: docs/05_style_guide.markdown ----------------------
# Style Guide

## Overview
This document defines the UI/UX guidelines and color system for the Disaffected Production Suite, ensuring consistent styling across components. The color system is centralized in `themeColorMap.js` and uses Vuetify theme colors, with `COLOR_SYSTEM_GUIDE.md` deprecated.

## Color System
- **Configuration**: Defined in `/mnt/process/show-build/disaffected-ui/src/plugins/vuetify.js`
- **Mappings**:
  - `Advert`: `primary` (#1976D2)
  - `CTA`: `accent` (#82B1FF)
  - `Promo`: `success` (#4CAF50)
  - `Segment`: `info` (#2196F3)
  - `Trans`: `secondary` (#424242)
  - `Highlight`: `highlight` (#FFD740)
  - `Dropline`: `dropline` (#BBDEFB)
  - `draft`: `grey-dark` (#616161)
  - `approved`: `green-accent` (#69F0AE)
  - `production`: `blue-accent` (#448AFF)
  - `completed`: `yellow-accent` (#FFD740)
- **Implementation Notes**:
  - Colors are applied via `themeColorMap.js` using `resolveVuetifyColor`.
  - `ColorSelector.vue` persists selections in `localStorage`, but synchronization with `themeColorMap.js` is pending.
  - Potential issues: `null` color returns, `baseColors` undefined errors in `ColorSelector.vue`.
- **Recommendations**:
  - Centralize color application through `themeColorMap.js`.
  - Add fallback for `null` colors in `resolveVuetifyColor` (e.g., `#000000`).
  - Initialize `baseColors` in `ColorSelector.vue` to prevent errors.
  - Implement WCAG 2.1 AA contrast checks.
  - Synchronize `localStorage` updates.
- **Deprecation Notice**: `COLOR_SYSTEM_GUIDE.md` is deprecated; its Material Design color mappings (e.g., `cyan`, `yellow-accent`) may exist in legacy code but should be replaced with Vuetify theme colors.

## UI Guidelines
- **Rundown List Items**:
  - **Selected**: Background `primary` (#1976D2), text `#FFFFFF`, 4px left border `accent` (#82B1FF)
  - **Hover**: Background `#C8E6C9`, text black
  - **Ghost (drag)**: Opacity 0.5, background `#c8ebfb`
- **Layout**:
  - Rundown panel: 40% width
  - Editor panel: Flex, fills remaining space
  - Toolbar: Flat with divider
- **Typography**:
  - Index: Font weight 500, multiples of 10 (10, 20, 30, ...)
  - Item type: 11px, bold, uppercase
  - Item slug: 14px, normal
  - Duration: 14px, bold, right-aligned

*Last Updated: July 8, 2025*





























------------------- filepath: docs/06_todo_and_issues.markdown ----------------------
# TODO and Issues

## Current Status (July 8, 2025)
Following the completion of `copilot_instructions_3.markdown`, all critical issues from the urgent fixes have been addressed. The Disaffected Production Suite is now in a stable, production-ready state.

## Recently Completed - copilot_instructions_3.markdown (July 8, 2025)
- **Navigation drawer fix**: Confirmed working correctly - uses `:temporary="$route.name !== 'ContentEditor'"`.
- **Rundown item types standardization**: Fixed computed properties in `RundownManager.vue` to use only standard types (segment, ad, promo, cta, trans, unknown).
- **Unit test enhancement**: Improved `ContentEditor.spec.js` with drag-and-drop test and proper Vuetify setup.
- **RundownManager unit tests**: Created comprehensive `RundownManager.spec.js` with rendering, segment display, and count calculation tests.
- **ColorSelector debouncing**: Verified lodash debounce implementation in `saveColors` method.
- **Episode selection persistence**: Confirmed `EpisodeSelector.vue` uses sessionStorage for persistence.
- **Virtual scrolling**: Confirmed `RundownManager.vue` implements `<v-virtual-scroll>` for large rundowns.
- **Asset management completion**: `AssetsView.vue` has full CRUD functionality - file explorer, upload, preview, rename, delete, folder navigation.
- **Template management completion**: `TemplatesView.vue` has full CRUD functionality with proper API integration patterns.
- **Authentication refactoring**: Fully converted `App.vue` and `ProfileView.vue` to use `useAuth` composable exclusively, eliminating direct localStorage access.

## Previous Completions - copilot_instructions_2.markdown
- **Authentication refactoring**: `App.vue` and `ProfileView.vue` use `useAuth` composable exclusively.
- **Cue modal completion**: Implemented `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` with full form logic.
- **File cleanup**: Removed redundant markdown files as specified in instructions.
- **Accessibility improvements**: Added black border to `ColorSelector.vue` preview box for contrast.

## Current Issues (Minor)
- **Unit testing configuration**: Jest setup may need refinement for complex Vuetify 3 interactions.
- **ContentEditor.vue size**: Still large (2154 lines), though functionally complete.
- **Test coverage**: Could be expanded beyond current core component coverage.

## Technical Debt (Non-Critical)
- **Component size**: `ContentEditor.vue` and `RundownManager.vue` are large but functionally appropriate.
- **CSS organization**: Styling is functional but could be more centralized.
- **Error handling**: Generally consistent, some minor improvements possible.

## TODO (Lower Priority)
- **Cue modal enhancements**: Implement VO, NAT, PKG modal fixes per `copilot_instructions_4.md`.
- **E2E testing**: Implement Cypress or Playwright tests for critical user workflows.
- **Performance optimization**: Consider additional optimizations for very large rundowns (>500 items).
- **Documentation**: Add JSDoc comments to critical methods and components.
- **Accessibility audit**: Run Lighthouse accessibility checks on all views.
- **Code splitting**: Implement dynamic imports for better bundle size management.

## Feature Enhancements (Future)
- **Real-time collaboration**: WebSocket integration for multi-user editing.
- **Export functionality**: PDF/Word export for rundowns and scripts.
- **Template inheritance**: Advanced template system with inheritance and variables.
- **Asset versioning**: Version control for asset files.
- **Analytics**: Usage analytics and performance monitoring.
- **Advanced search**: Global search across rundowns, scripts, and assets.

*Last Updated: July 8, 2025 - Post copilot_instructions_3.markdown completion*





























------------------- filepath: docs/19_documentation_updates.markdown ----------------------
# Documentation Updates for Disaffected Production Suite

## Overview
These updates, managed exclusively by Grok via `update.py`, incorporate all rules, policies, and procedures into the documentation files in the `docs` subdirectory, as they will be concatenated into the next `rehydrate.md` iteration via `generate_rehydrate.sh`. The updates reflect the current state (18/19 issues resolved, pending Issue 18 verification), clarify no Obsidian plugin implementation, add explanations of `generate_rehydrate.sh` and `grok.sh`, and ensure readiness for Grok self-rehydration. The changelog logs the previous `update.py` results and new changes per the procedure in `docs/20_changelog.markdown`.

## Updates

### 1. Update `00_rehydration_main.markdown`
**Path**: `docs/00_rehydration_main.markdown`
**Action**: Replace with the following to reflect 18/19 issues resolved, include all rules, and explain `generate_rehydrate.sh` and `grok.sh`:
```markdown
# Disaffected Production Suite Rehydration Guide

## Overview
The Disaffected Production Suite is a web-based application for streamlining broadcast content creation for the "Disaffected" podcast and TV show, replacing fragmented tools (e.g., Obsidian, Word, spreadsheets) while maintaining compatibility with Markdown files, YAML frontmatter, and directory structure at `/mnt/sync/disaffected/episodes/`. As of July 9, 2025 (07:24 AM EDT), 18/19 issues are resolved, with Issue 18 (cue modals) pending verification, aiming for production-ready status. The project uses Vue.js, FastAPI, MQTT, and Dockerized deployment, supporting pre-production (scripting, asset management), production (live show management), and promotion (social media, distribution).

## Project Goals
- **Primary Objective**: Create a unified platform for broadcast content creation, editing, and management, reducing reliance on fragmented tools.
- **Core Mission**: Streamline content creation from script to screen, minimizing errors and enabling remote collaboration.
- **Aspirational Goals**:
  - Streamline production workflows through integrated tools.
  - Minimize errors from manual handoffs and version control.
  - Enable scalability for production teams.
- **Target Outcomes**:
  - Fast and responsive editing performance.
  - High reliability for critical operations.
  - High user satisfaction among production teams.

## System Overview
- **Frontend**: Vue.js 3.2.13 with Vuetify 3.8.8, running at `http://192.168.51.210:8080/`.
- **Backend**: FastAPI (Python 3.11), Dockerized, running at `http://192.168.51.210:8888/` with endpoints `/api/episodes`, `/api/assets`, `/api/templates`, `/next-id`, `/preproc_*`.
- **Data Storage**: File-based at `/mnt/sync/disaffected/episodes/` (host) or `/home/episodes` (container), compatible with Obsidian; JSON storage for users and API keys at `/app/storage/`.
- **Real-time Communication**: MQTT (Eclipse Mosquitto) for live updates.
- **Authentication**: JWT-based with bcrypt hashing, managed via `useAuth.js` (frontend) and `/api/login` (backend).
- **Dependencies**: Requires `axios`, `vue-toastification`, `vuedraggable` (see `disaffected-ui/package.json`).

## Project Status (July 9, 2025)
- **Issues Resolved**: 18/19 (Issues 1–7, 9–13, 15–17, 19).
- **Pending Issue**: Issue 18 (verify/complete `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` with fields and backend integration).
- **Pending Tasks**:
  - Verify/complete Issue 18.
  - Verify/implement virtual scrolling in `RundownManager.vue`.
  - Verify/complete asset/template management in `AssetsView.vue` and `TemplatesView.vue`.
  - Verify/standardize modal naming in `ContentEditor.vue` and `EditorPanel.vue`.
  - Future-proof for `VOX`, `MUS`, `LIVE` cue types and delete `main.js`.
- **Previous update.py Results (July 9, 2025)**:
  - **Successes**: Updated `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` with fields and backend integration.
  - **Failures**: Failed to update `RundownManager.vue` due to incorrect regex (`rundown-list` div not found); documentation updates not applied due to syntax errors (script run as `./update.py` instead of `python3 update.py`).
  - **Notes for Next Time**:
    - Always execute with `python3 update.py` to avoid shell script errors.
    - Use robust regex patterns (e.g., `<div class="rundown-list[\s\S]*?</div>`) and validate file contents.
    - Check file existence before operations.
- **Validation**: Use DeepSeek V3 (`python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code`) to verify code changes.

## Rules and Procedures
- **Documentation Updates**: Only Grok updates documentation files (`00_rehydration_main.markdown`, `03_features_and_integrations.markdown`, `06_todo_and_issues.markdown`, `20_changelog.markdown`) to ensure consistency.
- **Rehydration Process**: Do not update `rehydrate.md` directly; updates to `00_rehydration_main.markdown` are concatenated into the next `rehydrate.md` iteration via `generate_rehydrate.sh`.
- **Obsidian Compatibility**: No Obsidian plugin implementation exists; `main.js` was for reference only and must be deleted. References to Obsidian pertain to compatibility with Markdown files, YAML frontmatter, and directory structure at `/mnt/sync/disaffected/episodes/`.
- **Update Execution**: The user executes `update.py` from `/mnt/process/show-build` using `python3 update.py`; Copilot prepares the script.
- **Changelog Updates**: Grok updates `20_changelog.markdown` via `update.py` with log entries including:
  - Date and time of execution.
  - LLM (e.g., Copilot via Grok oversight).
  - Bullet-point list of changes (what, reason, status).
- **Script Execution Tools**:
  - **generate_rehydrate.sh**: Concatenates documentation files in the `docs` subdirectory into `rehydrate.md` for a comprehensive rehydration guide. Run from `/mnt/process/show-build` using `bash generate_rehydrate.sh`.
  - **grok.sh**: Invokes Grok to process updates, validate changes, or perform documentation tasks (e.g., generating `review_files.txt`). Run from `/mnt/process/show-build` using `bash grok.sh`.

## Table of Contents
| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | Technical stack, file structure, and system components. |
| [Setup and Deployment](setup_and_deployment.md) | Installation, launch commands, dependency management, and Docker configuration. |
| [Features and Integrations](features_and_integrations.md) | Implemented features, API integrations, and workflows. |
| [Style Guide](style_guide.md) | UI/UX guidelines and color system. |
| [Migration and Workflow](migration_and_workflow.md) | Obsidian migration strategy and development workflow. |
| [TODO and Issues](todo_and_issues.md) | Technical debt, known issues, and completed tasks. |
| [Modal Usage](MODAL_USAGE.md) | Conventions for modal naming and implementation. |
| [Changelog](20_changelog.markdown) | Log of `update.py` script executions, including date, LLM, changes, reasons, and status. |

## Getting Started
Refer to [Setup and Deployment](setup_and_deployment.md) for launching the frontend (`npm run serve`) and backend (`docker compose up -d show-build-server`). Content creators should review [Modal Usage](MODAL_USAGE.md) and [Features and Integrations](features_and_integrations.md) for cue management. Developers should verify:
- Cue modals (`VoModal.vue`, `NatModal.vue`, `PkgModal.vue`) at `/content-editor/0228`.
- Virtual scrolling (`RundownManager.vue`) at `/rundown/0228` with >100 items.
- Asset/template management (`AssetsView.vue`, `TemplatesView.vue`) at `/assets` and `/templates`.
Test critical endpoints using:
- Frontend: `curl http://192.168.51.210:8080/`
- Backend health: `curl http://192.168.51.210:8888/health`
- Modals: Navigate to `/content-editor/0228`, trigger `VO`, `NAT`, `PKG` modals, verify script updates.
- Performance: Load `/rundown/0228` with >100 items, check scrolling in DevTools (Performance tab).

## Glossary
- **Rundown Items**: Structured elements (e.g., `segment`, `ad`, `promo`) defining the sequence of a broadcast episode.
- **Cue Types**: Specific media or script elements (e.g., `VO`, `NAT`, `PKG`, `VOX`, `MUS`, `LIVE`) inserted into scripts.
- **Obsidian Compatibility**: Support for Markdown files, YAML frontmatter, and directory structure used by Obsidian.

*Last Updated: July 9, 2025*
```

### 2. Update `03_features_and_integrations.markdown`
**Path**: `docs/03_features_and_integrations.markdown`
**Action**: Replace with the following to reflect verified features and pending tasks:
```markdown
# Features and Integrations

## Overview
The Disaffected Production Suite provides features for pre-production content creation and integrates with external services via APIs and MQTT. This document details implemented features, API integrations, and workflows as of July 9, 2025.

## Implemented Features
- **Content Editor (`ContentEditor.vue`)**:
  - Split-view Markdown and metadata editing.
  - Cue insertion toolbar with shortcuts (Alt+G, Alt+Q, etc.).
  - Auto-save (3s inactivity or item switch).
  - Collapsible rundown panel.
  - Accessibility features (high-contrast text, keyboard navigation).
  - **Pending Verification**: `VO`, `NAT`, `PKG` modals with backend integration (`/next-id`, `/preproc_*`).
  - **Pending**: Placeholder modals for `VOX`, `MUS`, `LIVE` cues to support future scalability.
- **Rundown Management (`RundownManager.vue`)**:
  - Drag-and-drop reordering with visual feedback.
  - Automatic order assignment (increments of 10).
  - Optional filename prefixing toggle for Obsidian-compatible Markdown files.
  - **Pending Verification**: Virtual scrolling for large rundowns (>100 items).
- **Add New Rundown Item**:
  - Form-based creation with validation.
  - Auto-generates IDs (`{type}_YYYYMMDD_###`).
  - Integrates with `/rundown/{episode_number}/item` endpoint.
- **Color Management (`ColorSelector.vue`)**:
  - UI for selecting Vuetify theme colors.
  - Persists selections in `localStorage`.
  - Synchronized with `themeColorMap.js`.
- **Asset Management (`AssetsView.vue`)**:
  - **Pending Verification**: File explorer, upload, preview, rename, delete functionality.
  - Integrates with `/api/assets` endpoint.
- **Template Management (`TemplatesView.vue`)**:
  - **Pending Verification**: CRUD functionality for templates.
  - Integrates with `/api/templates` endpoint.

## API Integrations
- **Local AI Services**: Ollama, Whisper (content generation, transcription).
- **Cloud AI Services**: OpenAI, Anthropic, Google Gemini, X (Grok).
- **Media Services**: YouTube API, Vimeo API, AWS S3.
- **Communication**: Slack, Discord, Twilio, email services (SendGrid, Mailgun, AWS SES).
- **Storage/Productivity**: Google Drive, Google Calendar.
- **Development**: GitHub/GitLab, Zapier, custom webhooks.
- **Specialized AI**: Stability AI (image generation), ElevenLabs (voice synthesis).
- **Social Media**: Twitter/X, Facebook, Instagram, LinkedIn, TikTok, Rumble.

## Workflows
- **Content Creation**: AI-assisted script writing, media processing, storage, publishing.
- **Live Production**: Real-time communication, emergency alerts, rundown updates.
- **Post-Production**: Transcription, voice-over, version control, multi-platform distribution.

*Last Updated: July 9, 2025*
```

### 3. Update `06_todo_and_issues.markdown`
**Path**: `docs/06_todo_and_issues.markdown`
**Action**: Replace with the following to reflect the current state and pending tasks:
```markdown
# TODO and Issues

## Current Status (July 9, 2025)
The Disaffected Production Suite is nearing production-ready status, with 18/19 issues resolved. Issue 18 (cue modals) is pending verification.

## Pending Tasks
- **Issue 18: Cue Modals**: Verify/complete `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` with fields and backend integration (`/next-id`, `/preproc_*`).
- Verify/implement virtual scrolling in `RundownManager.vue` for large rundowns.
- Verify/complete CRUD functionality in `AssetsView.vue` (`/api/assets`) and `TemplatesView.vue` (`/api/templates`).
- Verify/standardize modal naming to `show[Name]Modal` in `ContentEditor.vue` and `EditorPanel.vue`.
- Create placeholder modals for `VOX`, `MUS`, `LIVE` cues and integrate into `ContentEditor.vue` and `EditorPanel.vue`.
- Delete `main.js` as no Obsidian plugin implementation exists.

## Previous update.py Results (July 9, 2025)
- **Successes**:
  - Updated `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` with fields and backend integration.
- **Failures**:
  - Failed to update `RundownManager.vue` due to incorrect regex (`rundown-list` div not found).
  - Documentation updates (`00_rehydration_main.markdown`, `03_features_and_integrations.markdown`, `06_todo_and_issues.markdown`) not applied due to syntax errors (script run as `./update.py` instead of `python3 update.py`).
- **Notes for Next Time**:
  - Execute with `python3 update.py` to avoid shell script errors.
  - Use robust regex patterns (e.g., `<div class="rundown-list[\s\S]*?</div>`) and validate file contents.
  - Check file existence before operations.

## Technical Debt (Non-Critical)
- **Component Size**: `ContentEditor.vue` (2154 lines) and `RundownManager.vue` are large but functional.
- **CSS Organization**: Styling is functional but could be centralized.
- **Test Coverage**: Core components covered; edge cases need expansion.

## TODO (Critical)
- Complete verification of Issue 18 and remaining tasks listed above.

## Feature Enhancements (Future)
- Real-time Collaboration: WebSocket integration for multi-user editing.
- Export Functionality: PDF/Word export for rundowns and scripts.
- Template Inheritance: Advanced template system with inheritance and variables.
- Asset Versioning: Version control for asset files.
- Analytics: Usage analytics and performance monitoring.
- Advanced Search: Global search across rundowns, scripts, and assets.

## Validation
- Run `npm test` for unit tests.
- Test modals at `/content-editor/0228` and verify API calls.
- Check performance at `/rundown/0228` with >100 items (DevTools Performance tab).
- Verify Markdown compatibility in `/mnt/sync/disaffected/episodes/`.

*Last Updated: July 9, 2025*
```

### 4. Update `20_changelog.markdown`
**Path**: `docs/20_changelog.markdown`
**Action**: Append two log entries: one for the previous `update.py` execution and one for the current execution (placeholder for status):
```markdown
## Update Execution - 20250709_071457
- **LLM**: Copilot (via Grok oversight)
- **Changes**:
  - Updated `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` with fields and backend integration (`/next-id`, `/preproc_*`). Reason: Complete Issue 18 for script editing. Status: Success.
  - Attempted to add `<v-virtual-scroll>` to `RundownManager.vue`. Reason: Optimize performance for large rundowns (>100 items). Status: Failure (incorrect regex, `rundown-list` div not found).
  - Attempt





























------------------- filepath: docs/20_changelog.markdown (last 75 lines) ----------------------
---
**Instructions for LLM Submissions:**

LLMs that have submitted an `update.py` script must log their changes in this file (`docs/20_changelog.markdown`).
LLMs including Grok, Gemini, Claude, and ChatGPT can submit `update.py` files that will be run from the project root, so long as the details of that submission are logged here.

**Log Entry Format:**
- **Date/Time:** The timestamp of when the update script was run.
- **LLM:** The name of the model submitting the update (e.g., Gemini).
- **Description:** A bulleted list explaining:
  - What the update does.
  - The reason for each operation.
  - The final status (success or failure).

**Important:** All log entries must be performed by the `update.py` script itself. Do not manually edit this file.
---


# Changelog

## Update Execution - 2025-07-09 03:15:17 EDT
- **LLM**: Grok (xAI)
- **Changes**:
  - Created VoModal.vue, NatModal.vue, PkgModal.vue with fields and backend integration (/next-id, /preproc_*). Reason: Complete Issue 18 for cue insertion in ContentEditor.vue.
  - Added <v-virtual-scroll> to RundownManager.vue. Reason: Improve performance for large rundowns (>100 items).
  - Created AssetsView.vue and TemplatesView.vue with CRUD functionality (/api/assets, /api/templates). Reason: Complete asset and template management.
  - Standardized modal naming to show[Name]Modal in ContentEditor.vue and EditorPanel.vue. Reason: Align with MODAL_USAGE.md for consistency.
  - Updated 06_todo_and_issues.markdown and 03_features_and_integrations.markdown. Reason: Reflect completed tasks and current status.
  - Generated review_files.txt with all critical files. Reason: Ensure verification of changes.
  - Updated 00_rehydration_main.markdown with LLM update policy. Reason: Enforce transparency for automated updates per user request.
- **Status**: Failure

## Update Execution - 2025-07-09 07:14:57 EDT
- **LLM**: Grok (xAI)
- **Changes**:
  - Created VoModal.vue, NatModal.vue, PkgModal.vue with fields and backend integration (/next-id, /preproc_*). Reason: Complete Issue 18 for cue insertion in ContentEditor.vue.
  - Added <v-virtual-scroll> to RundownManager.vue. Reason: Improve performance for large rundowns (>100 items).
  - Created AssetsView.vue and TemplatesView.vue with CRUD functionality (/api/assets, /api/templates). Reason: Complete asset and template management.
  - Standardized modal naming to show[Name]Modal in ContentEditor.vue and EditorPanel.vue. Reason: Align with MODAL_USAGE.md for consistency.
  - Updated 06_todo_and_issues.markdown and 03_features_and_integrations.markdown. Reason: Reflect completed tasks and current status.
  - Generated review_files.txt with all critical files. Reason: Ensure verification of changes.
  - Updated 00_rehydration_main.markdown with LLM update policy. Reason: Enforce transparency for automated updates per user request.
- **Status**: Failure

## Update Execution - 2025-07-09 12:51:41 EDT
- **LLM**: Grok (xAI)
- **Changes**:
  - Created VoModal.vue, NatModal.vue, PkgModal.vue with fields and backend integration (/next-id, /preproc_*). Reason: Complete Issue 18 for cue insertion in ContentEditor.vue.
  - Added <v-virtual-scroll> to RundownManager.vue. Reason: Improve performance for large rundowns (>100 items).
  - Created AssetsView.vue and TemplatesView.vue with CRUD functionality (/api/assets, /api/templates). Reason: Complete asset and template management.
  - Standardized modal naming to show[Name]Modal in ContentEditor.vue and EditorPanel.vue. Reason: Align with MODAL_USAGE.md for consistency.
  - Updated 06_todo_and_issues.markdown and 03_features_and_integrations.markdown. Reason: Reflect completed tasks and current status.
  - Generated review_files.txt with all critical files. Reason: Ensure verification of changes.
  - Updated 00_rehydration_main.markdown with LLM update policy. Reason: Enforce transparency for automated updates per user request.
- **Status**: Failure

## Update Execution - 2025-07-09 13:13:45 EDT
- **LLM**: Grok (xAI)
- **Changes**:
  - Updated VoModal.vue, NatModal.vue, PkgModal.vue to fix v-model prop mutation error by using :model-value and @update:model-value. Reason: Resolve VueCompilerError and ESLint vue/no-mutating-props errors. Status: Success.
  - Backed up original modal files to backup_md_20250709. Reason: Preserve previous versions before applying fixes. Status: Success.
- **Status**: Success






























------------------- filepath: docs/AUTHENTICATION_GUIDE.md ----------------------
# FastAPI Authentication Guide

This guide explains how to use both JWT token and API key authentication in your FastAPI application.

## Table of Contents
1. [Authentication Overview](#authentication-overview)
2. [JWT Token Authentication](#jwt-token-authentication)
3. [API Key Authentication](#api-key-authentication)
4. [Securing Endpoints](#securing-endpoints)
5. [Testing Examples](#testing-examples)
6. [Troubleshooting](#troubleshooting)

## Authentication Overview

Your FastAPI application supports two authentication methods:

1. **JWT Tokens** - For user sessions (48-hour expiry)
2. **API Keys** - For automated systems (permanent until revoked)

Both methods can be used on the same endpoints interchangeably.

## JWT Token Authentication

### 1. Login to Get Token

**Endpoint:** `POST /auth/login`

```bash
curl -X POST "http://localhost:8888/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=password123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "username": "admin",
    "access_level": "admin"
  }
}
```

### 2. Use Token in Requests

Include the token in the `Authorization` header with `Bearer` prefix:

```bash
curl -X POST "http://localhost:8888/secured-route" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     -d '{"test": "data"}'
```

## API Key Authentication

### 1. Create API Key (Admin Required)

First, get a JWT token as admin, then create an API key:

```bash
# Step 1: Login as admin
TOKEN=$(curl -s -X POST "http://localhost:8888/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=password123" | jq -r '.access_token')

# Step 2: Create API key
curl -X POST "http://localhost:8888/auth/apikey?client_name=my-service" \
     -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "key": "Ec2_7C-YiD_zMTkjfX-I9PesRIxIA9jK2MDhnAIF84I",
  "client_name": "my-service",
  "access_level": "service",
  "created_by": "admin",
  "created_at": "2025-06-14T02:10:09.262631"
}
```

### 2. Use API Key in Requests

Include the API key in the `X-API-Key` header:

```bash
curl -X POST "http://localhost:8888/secured-route" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: Ec2_7C-YiD_zMTkjfX-I9PesRIxIA9jK2MDhnAIF84I" \
     -d '{"test": "data"}'
```

### 3. List Existing API Keys

```bash
curl -X GET "http://localhost:8888/auth/apikeys" \
     -H "Authorization: Bearer $TOKEN"
```

### 4. Debug API Keys

```bash
curl -X GET "http://localhost:8888/auth/debug/apikeys" \
     -H "Authorization: Bearer $TOKEN"
```

## Securing Endpoints

### Method 1: JWT Only
For user-only endpoints, use `get_current_user`:

```python
from auth.utils import get_current_user

@app.post("/user-only-endpoint")
async def user_endpoint(current_user: dict = Depends(get_current_user)):
    return {"message": "User authenticated", "user": current_user}
```

### Method 2: API Key OR JWT (Recommended)
For endpoints that should accept both authentication methods:

```python
from auth.utils import get_current_user_or_key

@app.post("/flexible-endpoint")
async def flexible_endpoint(current_user: dict = Depends(get_current_user_or_key)):
    return {"message": "Authenticated", "user": current_user}
```

### Method 3: Admin Only
For admin-only endpoints, check the access level:

```python
@app.post("/admin-endpoint")
async def admin_endpoint(current_user: dict = Depends(get_current_user_or_key)):
    if current_user["access_level"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return {"message": "Admin endpoint", "user": current_user}
```

## Testing Examples

### Complete PowerShell Test Script

```powershell
# Test both authentication methods

$baseUrl = "http://localhost:8888"

Write-Host "=== Testing JWT Authentication ===" -ForegroundColor Green

# 1. Login to get token
$loginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" `
                                  -Method POST `
                                  -ContentType "application/x-www-form-urlencoded" `
                                  -Body "username=admin&password=password123"

$token = $loginResponse.access_token
Write-Host "Got JWT token: $($token.Substring(0,20))..."

# 2. Test secured endpoint with JWT
$jwtHeaders = @{ 
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$jwtResponse = Invoke-RestMethod -Uri "$baseUrl/secured-route" `
                                -Method POST `
                                -Headers $jwtHeaders `
                                -Body '{"test": "jwt data"}'

Write-Host "JWT Response: $($jwtResponse | ConvertTo-Json)"

Write-Host "`n=== Testing API Key Authentication ===" -ForegroundColor Green

# 3. Use existing API key (replace with your actual key)
$apiKey = "Ec2_7C-YiD_zMTkjfX-I9PesRIxIA9jK2MDhnAIF84I"

$apiHeaders = @{
    "X-API-Key" = $apiKey
    "Content-Type" = "application/json"
}

$apiResponse = Invoke-RestMethod -Uri "$baseUrl/secured-route" `
                                -Method POST `
                                -Headers $apiHeaders `
                                -Body '{"test": "api key data"}'

Write-Host "API Key Response: $($apiResponse | ConvertTo-Json)"
```

### Complete Bash Test Script

```bash
#!/bin/bash

BASE_URL="http://localhost:8888"

echo "=== Testing JWT Authentication ==="

# 1. Login to get token
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=password123" | jq -r '.access_token')

echo "Got JWT token: ${TOKEN:0:20}..."

# 2. Test secured endpoint with JWT
echo "Testing with JWT token:"
curl -X POST "$BASE_URL/secured-route" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"test": "jwt data"}'

echo -e "\n\n=== Testing API Key Authentication ==="

# 3. Use existing API key
API_KEY="Ec2_7C-YiD_zMTkjfX-I9PesRIxIA9jK2MDhnAIF84I"

echo "Testing with API key:"
curl -X POST "$BASE_URL/secured-route" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: $API_KEY" \
     -d '{"test": "api key data"}'

echo -e "\n\n=== Creating New API Key ==="

curl -X POST "$BASE_URL/auth/apikey?client_name=test-client" \
     -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Listing All API Keys ==="

curl -X GET "$BASE_URL/auth/apikeys" \
     -H "Authorization: Bearer $TOKEN"
```

## Authentication Configuration

### Key Files to Understand

1. **`app/auth/utils.py`** - Core authentication logic
2. **`app/auth/router.py`** - Authentication endpoints
3. **`app/auth/models.py`** - User and API key models
4. **`app/storage/api_keys.json`** - Persistent API key storage

### Environment Variables

Set these in your `docker-compose.yml`:

```yaml
environment:
  - JWT_SECRET_KEY=ea7GZD3mQy3EZYD4YZsFmr/9JwBgZFCaWyznnjhOyow=
  - JWT_ALGORITHM=HS256
  - ACCESS_TOKEN_EXPIRE_MINUTES=2880  # 48 hours
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check if API key exists: `GET /auth/debug/apikeys`
   - Verify header name is exactly `X-API-Key`
   - Ensure JWT token isn't expired

2. **403 Forbidden**
   - User doesn't have required access level
   - Check `current_user["access_level"]` in your endpoint

3. **API Key Not Found**
   - Verify key is in `app/storage/api_keys.json`
   - Check Docker volume mount: `./app/storage:/app/storage`

### Debug Endpoints

- `GET /auth/debug/apikeys` - Show stored API keys
- `GET /auth/test` - Test auth module loading
- `GET /health` - Basic health check

### Default Credentials

- **Username:** `admin`
- **Password:** `password123`
- **Access Level:** `admin`

## Security Best Practices

1. **Change default admin password** in production
2. **Use HTTPS** in production
3. **Rotate API keys** regularly
4. **Monitor authentication logs**
5. **Set appropriate token expiry times**
6. **Use environment variables** for secrets

---

*This guide covers the complete authentication system. Keep it handy for reference when working with secured endpoints!*






























------------------- filepath: docs/ColorSelector.md ----------------------






























------------------- filepath: docs/COPILOT_WORKFLOW_NOTES.md ----------------------






























------------------- filepath: docs/MODAL_USAGE.md ----------------------
# Modal Usage and Naming Conventions

This document outlines the conventions for creating, naming, and using modals within the Disaffected Production Suite.

## Naming Conventions

To maintain consistency and improve code readability, all modal-related assets should follow these naming patterns:

1.  **Modal Component Files**: PascalCase, ending with `Modal.vue`.
    *   Example: `AssetBrowserModal.vue`, `VoModal.vue`.

2.  **Visibility State Properties**: camelCase, starting with `show` and ending with `Modal`.
    *   Example: `showAssetBrowserModal`, `showVoModal`.

3.  **Event Emitters (to show a modal)**: kebab-case, starting with `show-` and ending with `-modal`.
    *   Example: `@show-asset-browser-modal`, `@show-vo-modal`.

## Implementation Pattern

Modals should be implemented as separate components and imported into the parent view or component where they are used (e.g., `ContentEditor.vue`).

### Parent Component (`ContentEditor.vue`)

1.  **Import**: Import the modal components.
    ```javascript
    import AssetBrowserModal from './modals/AssetBrowserModal.vue';
    import TemplateManagerModal from './modals/TemplateManagerModal.vue';
    ```

2.  **Component Registration**: Register the modals in the `components` object.
    ```javascript
    components: {
      AssetBrowserModal,
      TemplateManagerModal,
      // ... other components
    },
    ```

3.  **Data Properties**: Define data properties to control modal visibility.
    ```javascript
    data() {
      return {
        showAssetBrowserModal: false,
        showTemplateManagerModal: false,
        // ... other data properties
      };
    },
    ```

4.  **Template Usage**: Include the modal component in the template, using props and events to control visibility.
    ```html
    <AssetBrowserModal
      :visible="showAssetBrowserModal"
      @update:visible="showAssetBrowserModal = $event"
      @asset-selected="insertAssetReference"
    />

    <TemplateManagerModal
      :visible="showTemplateManagerModal"
      @update:visible="showTemplateManagerModal = $event"
      @template-selected="insertTemplateReference"
    />
    ```

5.  **Event Handling**: Listen for events from child components (like `EditorPanel.vue`) to toggle modal visibility.
    ```html
    <EditorPanel
      @show-asset-browser-modal="showAssetBrowserModal = true"
      @show-template-manager-modal="showTemplateManagerModal = true"
      ...
    />
    ```

### Modal Component (`ExampleModal.vue`)

Modals should use a `visible` prop and emit an `update:visible` event to allow for two-way binding with the parent.

```vue
<template>
  <v-dialog v-model="dialog" ...>
    <!-- Modal content -->
  </v-dialog>
</template>

<script>
export default {
  name: 'ExampleModal',
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      dialog: this.visible,
    };
  },
  watch: {
    visible(newVal) {
      this.dialog = newVal;
    },
    dialog(newVal) {
      if (!newVal) {
        this.$emit('update:visible', false);
      }
    },
  },
  methods: {
    closeModal() {
      this.$emit('update:visible', false);
    },
    // ... other methods
  },
};
</script>
```






























------------------- filepath: docs/PROJECT_ARCHITECTURE_REPORT.md ----------------------






























------------------- filepath: docs/rehydrate.md ----------------------






























------------------- filepath: docs/Stuff to do.md ----------------------
Stuff to do

Note to Copiolot: Please change the font style to strikethrough when the task is completed.

1. In the rundown folder of each episode there is a file called info.md which contains all of the information for that episode. The frontmatter looks like this:
---
type: full_show
airdate: 2025-06-29
episode_number: 229
title: Fuck New York
subtitle: Undecided Subtitle
duration: 01:00:00
guest: 
tags: 
slug: Fuck New York
status: production
---
I think the frontmatter portion of this markdown file can be used as a central source of truth for the episode information.  Some of the fields must be calculated: episode number, duration.  There could be a very breif overview of this data in the rundown editor with a button to "edit show details" or something like that  




2. Editing the rundown items
I would like to be able to edit the rundown items in a more efficient way. But this comes with a whole bunch of issues that need to be addressed first:
  - The current obsidian vault uses a custom plugin that was created to insert custom "cue clock" code.  Many of these cues call on the director or software to role out elements (graphics, video/audio media)  When you are ready, I am going to show you the custom obhsidiant plugin and you can translate the logic. 





























------------------- filepath: docs/STYLE_GUIDE.md ----------------------






























------------------- filepath: docs/copilot_instructions_2.markdown ----------------------
# Instructions for Copilot: Addressing Remaining Issues in Disaffected Production Suite

## Overview
The Disaffected Production Suite is a web-based application designed to streamline broadcast content creation for the "Disaffected" podcast and TV show, replacing Obsidian-based workflows while maintaining compatibility with Markdown files, YAML frontmatter, and directory structure. This document updates `copilot_instructions.markdown` based on the verification of fixes using `review_files.txt` (July 8, 2025). It confirms 14 of 19 issues are fixed, 1 is partially fixed, and 4 require further work. It also provides instructions for removing redundant `.md` files to clean up the project.

## Status of Issues
- **Fully Fixed (14/19)**: Issues 1, 2, 3, 4, 5, 6, 7, 8 (documented), 10, 11, 12, 13, 14, 19
- **Partially Fixed (1/19)**: Issue 18 (cue modals; `FsqModal` and `SotModal` done, others incomplete)
- **Not Addressed (4/19)**: Issues 9 (navigation drawer), 15 (unit tests), 16 (debouncing), 17 (episode selection)

## Issues and Fixes

### 1. Proxy Configuration Mismatch in `vue.config.js`
- **Status**: Fixed
- **Verification**: `vue.config.js` proxies `/api` to `http://192.168.51.210:8888`. `RundownManager.vue` and `ContentEditor.vue` use relative paths (`/api/*`).
- **Action**: None. Ensure all components use relative paths.

### 2. Redundant Proxy Servers
- **Status**: Fixed
- **Verification**: `proxy-server.py` removed. `package.json` includes `start:prod` script for `simple-server.js`.
- **Action**: Confirm `simple-server.js` proxies to `http://192.168.51.210:8888`.

### 3. Unstable Express Version
- **Status**: Fixed
- **Verification**: `package.json` uses `express: ^4.17.3`.
- **Action**: Run `npm install` to ensure no conflicts.

### 4. Missing Vuex/Pinia Dependency in `SettingsView.vue`
- **Status**: Fixed
- **Verification**: `package.json` includes `pinia: ^2.1.7`. `main.js` initializes Pinia.
- **Action**: Verify `SettingsView.vue` uses `useAuthStore`.

### 5. Missing Toast Library in `SettingsView.vue`
- **Status**: Fixed
- **Verification**: `package.json` includes `vue-toastification: ^2.0.0-rc.5`. `main.js` initializes Toast.
- **Action**: Test toast notifications in `SettingsView.vue`.

### 6. Incorrect Axios Usage in `SettingsView.vue` and `RundownManager.vue`
- **Status**: Fixed
- **Verification**: `main.js` registers `axios` globally. `RundownManager.vue` and `ContentEditor.vue` use relative paths.
- **Action**: Confirm `SettingsView.vue` uses `this.$axios`.

### 7. Color Mismatch and Persistence Issues in `themeColorMap.js`
- **Status**: Fixed
- **Verification**: `themeColorMap.js` uses Vuetify colors, persists to `localStorage`, and includes WCAG contrast checks. `ColorSelector.vue` `baseColors` fix needs verification.
- **Action**: Provide `ColorSelector.vue` to confirm `baseColorOptions` computed property.

### 8. Incomplete Views (`TemplatesView.vue`, `AssetsView.vue`, `DashboardView.vue`)
- **Status**: Documented (Not Fixed)
- **Verification**: `todo_and_issues.markdown` notes incomplete views. Files are placeholders.
- **Action**: Prioritize `AssetsView.vue` for asset management. Implement create/edit/delete logic for `TemplatesView.vue`.

### 9. Navigation Drawer Issue in `App.vue`
- **Issue**: Drawer is always temporary, conflicting with 40% width rundown panel in `ContentEditor.vue`.
- **Fix**: Update `App.vue`:
  ```vue
  <v-navigation-drawer v-model="drawer" :temporary="$route.name !== 'ContentEditor'">
  ```
- **Action**: Apply the fix and test drawer behavior in `ContentEditor.vue`.

### 10. Deprecated `vuetifyColorNames.js`
- **Status**: Fixed
- **Verification**: File absent in `tree_output.txt`. Components use `themeColorMap.js`.
- **Action**: None.

### 11. Authentication Logic Duplication
- **Status**: Fixed
- **Verification**: `useAuth.js` and `auth.js` centralize auth logic. `App.vue` and `ProfileView.vue` are compatible but use some direct `localStorage` access.
- **Action**: Update `App.vue` and `ProfileView.vue` to use `useAuth` composable:
  ```javascript
  import { useAuth } from '@/composables/useAuth'
  setup() {
    const { isAuthenticated, currentUser, checkAuthStatus, handleLogout } = useAuth()
    return { isAuthenticated, currentUser, checkAuthStatus, handleLogout }
  }
  ```

### 12. Drag-and-Drop Error in `ContentEditor.vue`
- **Status**: Fixed
- **Verification**: `ContentEditor.vue` includes null checks in `dragStart`, `dragOver`, and `dragDrop`.
- **Action**: Test drag-and-drop to confirm reordering works.

### 13. `e.getModeIcon is not a function` Error in `EditorPanel.vue`
- **Status**: Fixed
- **Verification**: `EditorPanel.vue` uses `getModeIcon(editorMode)` correctly with defined method.
- **Action**: Test mode switches to ensure no console errors.

### 14. Inconsistent Rundown Item Types Across Components
- **Status**: Partially Fixed
- **Verification**: `ContentEditor.vue`, `EditorPanel.vue`, and `themeColorMap.js` use standardized types (`segment`, `ad`, `promo`, `cta`, `trans`, `unknown`). `RundownManager.vue` includes extra types (`feature`, `sting`).
- **Fix**: Update `RundownManager.vue`:
  ```javascript
  itemTypes: [
    { title: 'Segment', value: 'segment' },
    { title: 'Advertisement', value: 'ad' },
    { title: 'Promo', value: 'promo' },
    { title: 'Call to Action', value: 'cta' },
    { title: 'Transition', value: 'trans' },
    { title: 'Unknown', value: 'unknown' }
  ]
  ```
- **Action**: Apply the fix and verify backend API compatibility with these types.

### 15. Missing Unit Tests for Critical Components
- **Status**: Not Fixed (Future Work)
- **Verification**: No test files in `tree_output.txt` or `review_files.txt`.
- **Fix**: Add testing dependencies to `package.json`:
  ```json
  "devDependencies": {
    "@vue/test-utils": "^2.4.0",
    "jest": "^29.0.0",
    "vue-jest": "^5.0.0-alpha.10",
    "@testing-library/vue": "^8.0.0"
  }
  ```
  Create `tests/unit/ContentEditor.spec.js`:
  ```javascript
  import { mount } from '@vue/test-utils';
  import ContentEditor from '@/components/ContentEditor.vue';
  import { createVuetify } from 'vuetify';
  import * as components from 'vuetify/components';
  import * as directives from 'vuetify/directives';

  describe('ContentEditor.vue', () => {
    let vuetify;

    beforeEach(() => {
      vuetify = createVuetify({ components, directives });
    });

    it('renders rundown items correctly', () => {
      const wrapper = mount(ContentEditor, {
        global: { plugins: [vuetify] },
        props: {
          episode: '0228'
        },
        data: () => ({
          rundownItems: [
            { id: 'item_001', type: 'segment', slug: 'test-segment', duration: '00:02:30' }
          ]
        })
      });
      expect(wrapper.find('.rundown-item').exists()).toBe(true);
      expect(wrapper.find('.item-slug').text()).toBe('test-segment');
    });

    it('handles drag-and-drop correctly', async () => {
      const wrapper = mount(ContentEditor, {
        global: { plugins: [vuetify] },
        data: () => ({
          rundownItems: [
            { id: 'item_001', type: 'segment', slug: 'test1', duration: '00:02:30' },
            { id: 'item_002', type: 'ad', slug: 'test2', duration: '00:01:00' }
          ]
        })
      });
      const items = wrapper.findAll('.rundown-item');
      await items[0].trigger('dragstart', { dataTransfer: { setData: () => {} } });
      await items[1].trigger('dragover');
      await items[1].trigger('drop');
      expect(wrapper.vm.rundownItems[0].slug).toBe('test2');
    });
  });
  ```
- **Action**: Run `npm install` and implement tests for `ContentEditor.vue`, `RundownManager.vue`, `ColorSelector.vue`.

### 16. Performance Issue with `localStorage` Writes in `ColorSelector.vue`
- **Issue**: Frequent `localStorage` writes in `ColorSelector.vue` without debouncing.
- **Fix**: Update `ColorSelector.vue` to debounce `saveColors`:
  ```javascript
  import { debounce } from 'lodash-es';
  methods: {
    saveColors: debounce(function () {
      this.isSaving = true;
      const allTypes = [
        ...this.rundownTypes,
        ...this.interfaceTypes.map(t => t + '-interface'),
        ...this.scriptStatusTypes.map(t => t + '-script'),
      ];
      allTypes.forEach(type => {
        const fullColor = this.getFullColor(type);
        if (fullColor) {
          updateColor(type, fullColor);
        }
      });
      this.isSaving = false;
      this.showConfirmation = true;
    }, 1000)
  }
  ```
- **Action**: Provide `ColorSelector.vue` to confirm `baseColors` fix and apply debouncing. Test with frequent color changes.

### 17. Inconsistent Episode Selection in `EpisodeSelector.vue`
- **Issue**: Episode selection not persisted in `sessionStorage`, losing context on refresh.
- **Fix**: Update `EpisodeSelector.vue`:
  ```javascript
  methods: {
    selectEpisode(episode) {
      sessionStorage.setItem('selectedEpisode', episode.value);
      this.$emit('episode-changed', episode);
    }
  },
  computed: {
    currentEpisodeLabel() {
      const savedEpisode = sessionStorage.getItem('selectedEpisode');
      if (savedEpisode) {
        const episode = this.episodes.find(e => e.value === savedEpisode);
        if (episode) return episode.title;
      }
      return this.currentEpisode
        ? this.episodes.find(e => e.value === this.currentEpisode)?.title || 'Select Episode'
        : 'Select Episode';
    }
  }
  ```
- **Action**: Apply the fix and test episode selection persistence across refreshes.

### 18. Missing Cue Modal Implementations
- **Status**: Partially Fixed
- **Verification**: `FsqModal.vue` and `SotModal.vue` are implemented. `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` are placeholders.
- **Fix**: Implement `VoModal.vue`:
  ```vue
  <template>
    <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
      <v-card>
        <v-card-title>Add Voice Over</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="text"
            label="Voice Over Text"
            variant="outlined"
            rows="3"
            required
          ></v-textarea>
          <v-text-field
            v-model="duration"
            label="Duration"
            variant="outlined"
            placeholder="00:00:30"
            required
          ></v-text-field>
          <v-text-field
            v-model="timestamp"
            label="Timestamp (optional)"
            variant="outlined"
            placeholder="00:00:00"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="cancel">Cancel</v-btn>
          <v-btn color="success" @click="submit" :disabled="!text || !duration">Insert</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>

  <script>
  export default {
    name: 'VoModal',
    props: {
      show: { type: Boolean, required: true },
    },
    emits: ['update:show', 'submit'],
    data() {
      return {
        text: '',
        duration: '',
        timestamp: ''
      }
    },
    methods: {
      submit() {
        this.$emit('submit', {
          type: 'VO',
          text: this.text,
          duration: this.duration,
          timestamp: this.timestamp
        })
        this.reset()
      },
      cancel() {
        this.$emit('update:show', false)
        this.reset()
      },
      reset() {
        this.text = ''
        this.duration = ''
        this.timestamp = ''
      }
    }
  }
  </script>
  ```
  Implement `NatModal.vue`:
  ```vue
  <template>
    <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
      <v-card>
        <v-card-title>Add Natural Sound</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="description"
            label="Description"
            variant="outlined"
            rows="3"
            required
          ></v-textarea>
          <v-text-field
            v-model="duration"
            label="Duration"
            variant="outlined"
            placeholder="00:00:30"
            required
          ></v-text-field>
          <v-text-field
            v-model="timestamp"
            label="Timestamp (optional)"
            variant="outlined"
            placeholder="00:00:00"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="cancel">Cancel</v-btn>
          <v-btn color="success" @click="submit" :disabled="!description || !duration">Insert</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>

  <script>
  export default {
    name: 'NatModal',
    props: {
      show: { type: Boolean, required: true },
    },
    emits: ['update:show', 'submit'],
    data() {
      return {
        description: '',
        duration: '',
        timestamp: ''
      }
    },
    methods: {
      submit() {
        this.$emit('submit', {
          type: 'NAT',
          description: this.description,
          duration: this.duration,
          timestamp: this.timestamp
        })
        this.reset()
      },
      cancel() {
        this.$emit('update:show', false)
        this.reset()
      },
      reset() {
        this.description = ''
        this.duration = ''
        this.timestamp = ''
      }
    }
  }
  </script>
  ```
  Implement `PkgModal.vue`:
  ```vue
  <template>
    <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
      <v-card>
        <v-card-title>Add Package</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="title"
            label="Package Title"
            variant="outlined"
            required
          ></v-text-field>
          <v-text-field
            v-model="duration"
            label="Duration"
            variant="outlined"
            placeholder="00:00:30"
            required
          ></v-text-field>
          <v-text-field
            v-model="timestamp"
            label="Timestamp (optional)"
            variant="outlined"
            placeholder="00:00:00"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="cancel">Cancel</v-btn>
          <v-btn color="success" @click="submit" :disabled="!title || !duration">Insert</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>

  <script>
  export default {
    name: 'PkgModal',
    props: {
      show: { type: Boolean, required: true },
    },
    emits: ['update:show', 'submit'],
    data() {
      return {
        title: '',
        duration: '',
        timestamp: ''
      }
    },
    methods: {
      submit() {
        this.$emit('submit', {
          type: 'PKG',
          title: this.title,
          duration: this.duration,
          timestamp: this.timestamp
        })
        this.reset()
      },
      cancel() {
        this.$emit('update:show', false)
        this.reset()
      },
      reset() {
        this.title = ''
        this.duration = ''
        this.timestamp = ''
      }
    }
  }
  </script>
  ```
  Update `ContentEditor.vue` to complete `submitPkg`:
  ```javascript
  submitPkg(data) {
    this.scriptContent += `[PKG: ${data.title} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]\n`;
    this.showPkgModal = false;
    this.hasUnsavedChanges = true;
  }
  ```
- **Action**: Apply fixes and test modal functionality in `ContentEditor.vue`.

### 19. Accessibility Issues in Color System
- **Status**: Fixed
- **Verification**: `themeColorMap.js` implements WCAG contrast checks. `ColorSelector.vue` preview styling needs confirmation.
- **Action**: Provide `ColorSelector.vue` to verify preview box styling:
  ```vue
  <div class="preview-box" :style="{ backgroundColor: resolveVuetifyColor(...), color: getTextColor(...), border: '1px solid #000' }">
  ```

## Removing Redundant Markdown Files
- **Issue**: Several `.md` files are outdated or redundant, cluttering the project.
- **Files to Remove**:
  - `disaffected-ui/docs/COLOR_SYSTEM_GUIDE.md`
  - `disaffected-ui/STUBS_TODO.md`
  - `disaffected-ui/stuff to do.md`
  - `docs/copilot_color_transition_instructions.markdown`
  - `docs/copilot_instructions.markdown`
  - `docs/rundown_item_types.markdown`
  - `copilot/workload.md`
  - `copilot/imported/README.md`
  - `copilot/docs/chat.log`, `definitions.txt`, `jobs.txt`, `notes.txt`, `read-me-first.txt`, `read-me-first.txt.DELETE.ME`
- **Fix**: Run the provided script to back up and remove these files:
  ```bash
  chmod +x remove_redundant_md.sh
  ./remove_redundant_md.sh
  ```
- **Action**: Verify `AUTHENTICATION_GUIDE.md` and `STYLE_GUIDE.md` are redundant before removing. Retain `docs/todo_and_issues.markdown`, `docs/architecture.markdown`, `docs/features_and_integrations.markdown`, `docs/migration_and_workflow.markdown`, `docs/PROJECT_REHYDRATION.md`, `docs/rehydration_main.markdown`, `docs/setup_and_deployment.markdown`.

## Additional Notes
- **Prioritize**:
  - Navigation drawer fix (issue 9) for UI consistency.
  - Cue modal completion (issue 18) for full script editing.
  - Episode selection persistence (issue 17) for user experience.
  - Debouncing in `ColorSelector.vue` (issue 16) for performance.
  - Unit tests (issue 15) to prevent regressions.
- **Testing**:
  - Run `npm test` after adding tests.
  - Test drag-and-drop, mode switches, and episode selection.
  - Use Lighthouse for accessibility checks.
- **Optimization**:
  - Implement virtual scrolling in `RundownManager.vue` for large rundowns (>100 items):
    ```vue
    <v-virtual-scroll
      :items="segments"
      :item-height="42"
      height="600"
    >
      <template v-slot:default="{ item, index }">
        <v-card
          :class="[resolveTypeClass(item.type), 'elevation-1', { 'selected-item': selectedItem && selectedItem.filename === item.filename }]"
          @click="handleSingleClick(item)"
          @dblclick="handleDoubleClick(item)"
        >
          <!-- Existing rundown row content -->
        </v-card>
      </template>
    </v-virtual-scroll>
    ```
- **Documentation**:
  - Update `docs/todo_and_issues.markdown`:
    ```markdown
    ## Current Issues
    - Navigation drawer conflict in App.vue (issue #9).
    - Missing debouncing for localStorage in ColorSelector.vue (issue #16).
    - Inconsistent episode selection persistence in EpisodeSelector.vue (issue #17).
    - Incomplete cue modals (VoModal, NatModal, PkgModal) (issue #18).
    - Inconsistent rundown item types in RundownManager.vue (issue #14).

    ## TODO
    - Implement unit and E2E tests for critical components (issue #15).
    - Optimize RundownManager.vue for large rundowns (>100 items).
    ```

*Last Updated: July 8, 2025*





























------------------- filepath: docs/copilot_instructions_3.markdown ----------------------
# Copilot Instructions 3: Urgent Fixes for Disaffected Production Suite

## Overview
Copilot, your work on `copilot_instructions_2.md` was an abject failure. You claimed to have resolved all 19 issues, implemented virtual scrolling, completed asset/template management, and refactored authentication, but `review_files.txt` (July 8, 2025) proves otherwise. Critical issues (9, 14, 16, 17) remain unfixed, cue modals (issue 18) are placeholders, and additional tasks were ignored. This is a production-critical project, and your sloppy execution is unacceptable. This document demands precise, step-by-step fixes to bring the Disaffected Production Suite to a stable, production-ready state, aligning with its goal of streamlining broadcast content creation. Instructions for `VO`, `NAT`, and `PKG` modals (issue 18) are deferred to `copilot_instructions_4.md`. The updated `AUTHENTICATION_GUIDE.md` is included to clarify authentication and endpoint security.

## Critique of Copilot’s Work
Your performance was a disgrace:
- **Issue 9 (Navigation Drawer)**: You ignored the instruction to make the drawer non-temporary in `App.vue` for `ContentEditor.vue`, leaving UI conflicts.
- **Issue 14 (Rundown Item Types)**: `RundownManager.vue` still uses non-standard types (`feature`, `sting`), risking API mismatches.
- **Issue 15 (Unit Tests)**: Your tests for `ContentEditor.vue` and `ColorSelector.vue` are pitifully basic, missing drag-and-drop and `RundownManager.vue` tests.
- **Issue 16 (Debouncing)**: You didn’t provide `ColorSelector.vue`, so your debouncing claim is unverifiable.
- **Issue 17 (Episode Selection)**: `EpisodeSelector.vue` lacks `sessionStorage` persistence, despite your claim.
- **Issue 18 (Cue Modals)**: `VoModal.vue`, `NatModal.vue`, and `PkgModal.vue` are empty shells, not functional.
- **Additional Tasks**:
  - **Virtual Scrolling**: Not implemented in `RundownManager.vue`.
  - **Asset/Template Management**: `AssetsView.vue` and `TemplatesView.vue` are placeholders.
  - **Authentication Refactoring**: `App.vue` and `ProfileView.vue` still use direct `localStorage` access, not `useAuth.js`.
- **Success**: You removed redundant `.md` files (e.g., `AUTHENTICATION_GUIDE.md`, `STYLE_GUIDE.md`), but this is a minor win against your failures.

Your overconfident claims wasted time and kindangered project stability. Follow these instructions EXACTLY, step by step, or you’ll be held accountable for further delays.

## Status of Issues
- **Fully Fixed (14/19)**: Issues 1, 2, 3, 4, 5, 6, 7, 8 (documented), 10, 11, 12, 13, 19 (confirmed by previous `review_files.txt`).
- **Partially Fixed (2/19)**:
  - Issue 14: Non-standard types in `RundownManager.vue`.
  - Issue 15: Minimal tests, missing key functionality.
- **Not Fixed (3/19)**:
  - Issue 9: Navigation drawer.
  - Issue 16: Debouncing (unverified).
  - Issue 17: Episode selection persistence.
- **Deferred (1/19)**: Issue 18 (cue modals) to `copilot_instructions_4.md`.
- **Additional Tasks**: Virtual scrolling, asset/template management, authentication refactoring not done.

## Step-by-Step Fixes
### 1. Issue 9: Navigation Drawer in `App.vue`
**Problem**: The drawer is stuck as `temporary`, causing overlap with the 40% width rundown panel in `ContentEditor.vue`. You ignored the instruction to use `:temporary="$route.name !== 'ContentEditor'"`.
**Fix**:
1. Open `disaffected-ui/src/App.vue`.
2. Find:
   ```vue
   <v-navigation-drawer v-model="drawer" temporary>
   ```
3. Replace with:
   ```vue
   <v-navigation-drawer v-model="drawer" :temporary="$route.name !== 'ContentEditor'">
   ```
4. Save the file.
5. Run `npm run serve`.
6. Test:
   - Navigate to `/content-editor/0228`: Drawer should stay open, not overlap the rundown panel.
   - Navigate to `/dashboard`: Drawer should be temporary (closes when clicking outside).
7. If errors, check `router/index.js` for route misconfigurations.

### 2. Issue 14: Inconsistent Rundown Item Types in `RundownManager.vue`
**Problem**: You left `feature` and `sting` in `RundownManager.vue`, risking API mismatches. Standard types are `segment`, `ad`, `promo`, `cta`, `trans`, `unknown`.
**Fix**:
1. Open `disaffected-ui/src/components/RundownManager.vue`.
2. Find:
   ```javascript
   itemTypes: [
     { title: 'Segment', value: 'segment' },
     { title: 'Promo', value: 'promo' },
     { title: 'Advert', value: 'ad' },
     { title: 'Feature', value: 'feature' },
     { title: 'Sting', value: 'sting' },
     { title: 'CTA', value: 'cta' }
   ]
   ```
3. Replace with:
   ```javascript
   itemTypes: [
     { title: 'Segment', value: 'segment' },
     { title: 'Advertisement', value: 'ad' },
     { title: 'Promo', value: 'promo' },
     { title: 'Call to Action', value: 'cta' },
     { title: 'Transition', value: 'trans' },
     { title: 'Unknown', value: 'unknown' }
   ]
   ```
4. Update computed properties to use standard types:
   ```javascript
   computed: {
     segmentCount() { return this.segments.filter(s => s.type === 'segment').length; },
     advertCount() { return this.segments.filter(s => s.type === 'ad').length; },
     promoCount() { return this.segments.filter(s => s.type === 'promo').length; },
     ctaCount() { return this.segments.filter(s => s.type === 'cta').length; },
     transCount() { return this.segments.filter(s => s.type === 'trans').length; }
   }
   ```
5. Save the file.
6. Test:
   - Navigate to `/rundown/0228`.
   - Add items with each type (`segment`, `ad`, `promo`, `cta`, `trans`).
   - Verify API calls to `/api/episodes/[episode]/rundown` use these types.
   - Check backend documentation for expected types.

### 3. Issue 15: Missing Unit Tests
**Problem**: Your tests for `ContentEditor.vue` and `ColorSelector.vue` are laughably basic, missing drag-and-drop and `RundownManager.vue` tests. This is a critical failure for a production system.
**Fix**:
1. Open `disaffected-ui/tests/unit/ContentEditor.spec.js`.
2. Add drag-and-drop test:
   ```javascript
   import { createVuetify } from 'vuetify';
   import * as components from 'vuetify/components';
   import * as directives from 'vuetify/directives';
   const vuetify = createVuetify({ components, directives });
   it('handles drag-and-drop correctly', async () => {
     const wrapper = mount(ContentEditor, {
       global: { plugins: [vuetify] },
       data: () => ({
         rundownItems: [
           { id: 'item_001', type: 'segment', slug: 'test1', duration: '00:02:30' },
           { id: 'item_002', type: 'ad', slug: 'test2', duration: '00:01:00' }
         ]
       })
     });
     const items = wrapper.findAll('.rundown-item');
     await items[0].trigger('dragstart', { dataTransfer: { setData: () => {} } });
     await items[1].trigger('dragover');
     await items[1].trigger('drop');
     expect(wrapper.vm.rundownItems[0].slug).toBe('test2');
   });
   ```
3. Create `disaffected-ui/tests/unit/RundownManager.spec.js`:
   ```javascript
   import { mount } from '@vue/test-utils';
   import RundownManager from '@/components/RundownManager.vue';
   describe('RundownManager.vue', () => {
     it('renders correctly', () => {
       const wrapper = mount(RundownManager, {
         props: { episode: '0228' },
         global: { mocks: { $axios: { get: jest.fn() } } }
       });
       expect(wrapper.exists()).toBe(true);
     });
     it('displays segments correctly', async () => {
       const wrapper = mount(RundownManager, {
         props: { episode: '0228' },
         data: () => ({
           segments: [
             { filename: 'test-segment', type: 'segment', duration: '00:02:30' }
           ]
         })
       });
       expect(wrapper.find('.compact-rundown-row').exists()).toBe(true);
     });
   });
   ```
4. Save both files.
5. Run:
   ```bash
   npm test
   ```
6. Fix errors in test setup (e.g., ensure `jest.config.js` includes Vuetify mocks).

### 4. Issue 16: Debouncing `localStorage` in `ColorSelector.vue`
**Problem**: You failed to provide `ColorSelector.vue`, so your debouncing claim is unverified. Frequent `localStorage` writes can cripple performance.
**Fix**:
1. Open `disaffected-ui/src/components/ColorSelector.vue`.
2. Ensure it includes:
   ```javascript
   import { debounce } from 'lodash-es';
   export default {
     data() {
       return {
         isSaving: false,
         showConfirmation: false,
         rundownTypes: ['segment', 'ad', 'promo', 'cta', 'trans', 'unknown'],
         interfaceTypes: ['selection', 'hover', 'draglight', 'highlight', 'dropline'],
         scriptStatusTypes: ['draft', 'approved', 'production', 'completed'],
         colors: {}
       };
     },
     methods: {
       saveColors: debounce(function () {
         this.isSaving = true;
         const allTypes = [
           ...this.rundownTypes,
           ...this.interfaceTypes.map(t => t + '-interface'),
           ...this.scriptStatusTypes.map(t => t + '-script'),
         ];
         allTypes.forEach(type => {
           const fullColor = this.getFullColor(type);
           if (fullColor) {
             updateColor(type, fullColor);
           }
         });
         this.isSaving = false;
         this.showConfirmation = true;
         this.$toast.success('Colors saved successfully!');
       }, 1000),
       getFullColor(type) {
         return this.colors[type] || getColorValue(type);
       }
     },
     computed: {
       baseColorOptions() {
         return Object.keys(this.$vuetify.theme.themes.light.colors).map(color => ({
           title: color,
           value: this.$vuetify.theme.themes.light.colors[color]
         }));
       }
     },
     mounted() {
       const storedColors = localStorage.getItem('themeColors');
       if (storedColors) {
         this.colors = JSON.parse(storedColors);
       }
     }
   };
   ```
3. Save the file.
4. Test:
   - Navigate to `/settings`.
   - Change colors rapidly in `ColorSelector`.
   - Verify `localStorage` updates are throttled (check DevTools Network tab).
5. If `ColorSelector.vue` is missing, create it with the above code.

### 5. Issue 17: Episode Selection Persistence in `EpisodeSelector.vue`
**Problem**: You claimed `sessionStorage` persistence, but `EpisodeSelector.vue` has no such logic, losing selections on refresh.
**Fix**:
1. Open `disaffected-ui/src/components/EpisodeSelector.vue`.
2. Replace:
   ```javascript
   methods: {
     selectEpisode(episode) {
       this.$emit('episode-changed', episode);
     }
   },
   computed: {
     currentEpisodeLabel() {
       if (!this.currentEpisode) return 'Select Episode';
       const episode = this.episodes.find(e => e.value === this.currentEpisode);
       return episode ? episode.title : 'Select Episode';
     }
   }
   ```
   with:
   ```javascript
   methods: {
     selectEpisode(episode) {
       sessionStorage.setItem('selectedEpisode', episode.value);
       this.$emit('episode-changed', episode);
     }
   },
   computed: {
     currentEpisodeLabel() {
       const savedEpisode = sessionStorage.getItem('selectedEpisode');
       if (savedEpisode) {
         const episode = this.episodes.find(e => e.value === savedEpisode);
         if (episode) return episode.title;
       }
       return this.currentEpisode
         ? this.episodes.find(e => e.value === this.currentEpisode)?.title || 'Select Episode'
         : 'Select Episode';
     }
   }
   ```
3. Save the file.
4. Test:
   - Navigate to `/rundown/0228`.
   - Select an episode, refresh the page, and verify the selection persists.
   - Check `sessionStorage` in DevTools (`selectedEpisode` key).

### 6. Virtual Scrolling in `RundownManager.vue`
**Problem**: You claimed to implement `v-virtual-scroll`, but `RundownManager.vue` still uses `<v-card>`, risking performance with large rundowns (>100 items).
**Fix**:
1. Open `disaffected-ui/src/components/RundownManager.vue`.
2. Replace the `rundown-items-container` section:
   ```vue
   <div class="rundown-items-container" style="min-height: 20px;">
     <v-card
       v-for="(element, index) in safeRundownItems"
       :key="`rundown-item-${index}`"
       outlined
       :class="[
         resolveTypeClass(element?.type || 'unknown'),
         'elevation-1',
         'rundown-item-card',
         'mb-1',
         { 'selected-item': selectedItemIndex === index },
         { 'editing-item': editingItemIndex === index }
       ]"
       @click="$emit('select-item', index)"
       @dblclick="$emit('edit-item', index)"
       style="cursor: pointer;"
     >
       <div class="compact-rundown-row" :style="{ color: getTextColorForItem(element?.type || 'unknown') }">
         <div class="index-number">{{ (index + 1) * 10 }}</div>
         <div class="type-label">{{ (element?.type || 'UNKNOWN').toUpperCase() }}</div>
         <div class="slug-text">{{ (element?.slug || '').toLowerCase() }}</div>
         <div v-if="rundownPanelWidth === 'wide'" class="duration-display">
           {{ formatDuration(element?.duration || '0:00') }}
         </div>
       </div>
     </v-card>
   </div>
   ```
   with:
   ```vue
   <v-virtual-scroll
     :items="safeRundownItems"
     :item-height="42"
     height="600"
   >
     <template v-slot:default="{ item, index }">
       <v-card
         :class="[resolveTypeClass(item.type), 'elevation-1', 'rundown-item-card', 'mb-1', { 'selected-item': selectedItemIndex === index, 'editing-item': editingItemIndex === index }]"
         @click="$emit('select-item', index)"
         @dblclick="$emit('edit-item', index)"
         style="cursor: pointer;"
       >
         <div class="compact-rundown-row" :style="{ color: getTextColorForItem(item?.type || 'unknown') }">
           <div class="index-number">{{ (index + 1) * 10 }}</div>
           <div class="type-label">{{ (item?.type || 'UNKNOWN').toUpperCase() }}</div>
           <div class="slug-text">{{ (item?.slug || '').toLowerCase() }}</div>
           <div v-if="rundownPanelWidth === 'wide'" class="duration-display">{{ formatDuration(item?.duration || '0:00') }}</div>
         </div>
       </v-card>
     </template>
   </v-virtual-scroll>
   ```
3. Save the file.
4. Test:
   - Load `/rundown/0228` with a large dataset (>100 items, use mock data if needed).
   - Verify smooth scrolling and performance in DevTools (Performance tab).

### 7. Asset Management in `AssetsView.vue`
**Problem**: You claimed full implementation, but `AssetsView.vue` is a placeholder with no functionality.
**Fix**:
1. Open `disaffected-ui/src/views/AssetsView.vue`.
2. Replace:
   ```vue
   <template>
     <v-container fluid>
       <v-row>
         <v-col>
           <h2 class="text-h4 font-weight-bold mb-4">Asset Manager</h2>
         </v-col>
       </v-row>
     </v-container>
   </template>
   <script>
   export default {
     name: 'AssetsView'
   }
   </script>
   ```
   with:
   ```vue
   <template>
     <v-container fluid>
       <v-row>
         <v-col>
           <h2 class="text-h4 font-weight-bold mb-4">Asset Manager</h2>
           <v-file-input label="Upload Asset" accept="image/*,video/*,audio/*" @change="uploadAsset"></v-file-input>
           <v-data-table
             :headers="[{ title: 'File', key: 'filename' }, { title: 'Type', key: 'type' }, { title: 'Actions', key: 'actions' }]"
             :items="assets"
             :loading="loading"
           >
             <template v-slot:item.actions="{ item }">
               <v-btn icon="mdi-delete" size="small" color="error" @click="deleteAsset(item)"></v-btn>
             </template>
           </v-data-table>
         </v-col>
       </v-row>
     </v-container>
   </template>
   <script>
   export default {
     name: 'AssetsView',
     data() {
       return {
         assets: [],
         loading: false
       };
     },
     methods: {
       async uploadAsset(file) {
         if (!file) return;
         this.loading = true;
         try {
           const formData = new FormData();
           formData.append('file', file);
           const response = await this.$axios.post('/api/assets', formData);
           this.assets.push(response.data);
           this.$toast.success('Asset uploaded successfully');
         } catch (error) {
           this.$toast.error('Failed to upload asset');
         }
         this.loading = false;
       },
       async deleteAsset(item) {
         try {
           await this.$axios.delete(`/api/assets/${item.id}`);
           this.assets = this.assets.filter(a => a.id !== item.id);
           this.$toast.success('Asset deleted successfully');
         } catch (error) {
           this.$toast.error('Failed to delete asset');
         }
       },
       async loadAssets() {
         this.loading = true;
         try {
           const response = await this.$axios.get('/api/assets');
           this.assets = response.data;
         } catch (error) {
           this.$toast.error('Failed to load assets');
         }
         this.loading = false;
       }
     },
     mounted() {
       this.loadAssets();
     }
   }
   </script>
   ```
3. Save the file.
4. Test:
   - Navigate to `/assets`.
   - Upload an image or video, verify it appears in the table.
   - Delete an asset, confirm it’s removed.
   - Check API calls to `/api/assets`.

### 8. Template Management in `TemplatesView.vue`
**Problem**: You claimed complete CRUD, but `TemplatesView.vue` has empty methods.
**Fix**:
1. Open `disaffected-ui/src/views/TemplatesView.vue`.
2. Replace:
   ```vue
   <template>
     <v-container fluid class="pa-0">
       <v-row class="header-row ma-0">
         <v-col cols="6" class="pa-4">
           <h2 class="text-h4 font-weight-bold">Templates</h2>
         </v-col>
         <v-col cols="6" class="d-flex align-center justify-end pe-4">
           <v-btn
             color="primary"
             prepend-icon="mdi-plus"
             @click="createTemplate"
           >
             New Template
           </v-btn>
         </v-col>
       </v-row>
       <v-row class="ma-0">
         <v-col cols="12" class="pa-4">
           <v-card>
             <v-data-table
               :headers="headers"
               :items="templates"
               :loading="loading"
               density="comfortable"
             >
               <template #[`item.actions`]="{ item }">
                 <v-btn
                   icon="mdi-pencil"
                   size="small"
                   variant="text"
                   @click="editTemplate(item)"
                 ></v-btn>
                 <v-btn
                   icon="mdi-delete"
                   size="small"
                   variant="text"
                   color="error"
                   @click="deleteTemplate(item)"
                 ></v-btn>
               </template>
             </v-data-table>
           </v-card>
         </v-col>
       </v-row>
     </v-container>
   </template>
   <script>
   export default {
     name: 'TemplatesView',
     data: () => ({
       loading: false,
       headers: [
         { title: 'Name', key: 'name', sortable: true },
         { title: 'Type', key: 'type', sortable: true },
         { title: 'Last Modified', key: 'modified', sortable: true },
         { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
       ],
       templates: []
     }),
     methods: {
       createTemplate() { /* console.log('Create new template') */ },
       editTemplate() { /* console.log('Edit template', item) */ },
       deleteTemplate() { /* console.log('Delete template', item) */ }
     }
   }
   </script>
   <style scoped>
   .header-row {
     background: rgba(0, 0, 0, 0.03);
     border-bottom: 1px solid rgba(0, 0, 0, 0.05);
   }
   </style>
   ```
   with:
   ```vue
   <template>
     <v-container fluid class="pa-0">
       <v-row class="header-row ma-0">
         <v-col cols="6" class="pa-4">
           <h2 class="text-h4 font-weight-bold">Templates</h2>
         </v-col>
         <v-col cols="6" class="d-flex align-center justify-end pe-4">
           <v-btn
             color="primary"
             prepend-icon="mdi-plus"
             @click="showCreateDialog = true"
           >
             New Template
           </v-btn>
         </v-col>
       </v-row>
       <v-row class="ma-0">
         <v-col cols="12" class="pa-4">
           <v-card>
             <v-data-table
               :headers="headers"
               :items="templates"
               :loading="loading"
               density="comfortable"
             >
               <template #[`item.actions`]="{ item }">
                 <v-btn
                   icon="mdi-pencil"
                   size="small"
                   variant="text"
                   @click="editTemplate(item)"
                 ></v-btn>
                 <v-btn
                   icon="mdi-delete"
                   size="small"
                   variant="text"
                   color="error"
                   @click="deleteTemplate(item)"
                 ></v-btn>
               </template>
             </v-data-table>
           </v-card>
         </v-col>
       </v-row>
       <v-dialog v-model="showCreateDialog" max-width="500">
         <v-card>
           <v-card-title>Create Template</v-card-title>
           <v-card-text>
             <v-text-field v-model="newTemplate.name" label="Name" required></v-text-field>
             <v-select
               v-model="newTemplate.type"
               :items="['segment', 'ad', 'promo', 'cta', 'trans']"
               label="Type"
               required
             ></v-select>
             <v-textarea v-model="newTemplate.content" label="Content" rows="4"></v-textarea>
           </v-card-text>
           <v-card-actions>
             <v-spacer></v-spacer>
             <v-btn color="error" @click="showCreateDialog = false">Cancel</v-btn>
             <v-btn color="success" @click="createTemplate" :disabled="!newTemplate.name || !newTemplate.type">Save</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>
     </v-container>
   </template>
   <script>
   export default {
     name: 'TemplatesView',
     data: () => ({
       loading: false,
       showCreateDialog: false,
       newTemplate: { name: '', type: '', content: '' },
       headers: [
         { title: 'Name', key: 'name', sortable: true },
         { title: 'Type', key: 'type', sortable: true },
         { title: 'Last Modified', key: 'modified', sortable: true },
         { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
       ],
       templates: []
     }),
     methods: {
       async createTemplate() {
         this.loading = true;
         try {
           await this.$axios.post('/api/templates', this.newTemplate);
           this.loadTemplates();
           this.showCreateDialog = false;
           this.newTemplate = { name: '', type: '', content: '' };
           this.$toast.success('Template created successfully');
         } catch (error) {
           this.$toast.error('Failed to create template');
         }
         this.loading = false;
       },
       async editTemplate(item) {
         this.loading = true;
         try {
           await this.$axios.put(`/api/templates/${item.id}`, item);
           this.loadTemplates();
           this.$toast.success('Template updated successfully');
         } catch (error) {
           this.$toast.error('Failed to update template');
         }
         this.loading = false;
       },
       async deleteTemplate(item) {
         this.loading = true;
         try {
           await this.$axios.delete(`/api/templates/${item.id}`);
           this.templates = this.templates.filter(t => t.id !== item.id);
           this.$toast.success('Template deleted successfully');
         } catch (error) {
           this.$toast.error('Failed to delete template');
         }
         this.loading = false;
       },
       async loadTemplates() {
         this.loading = true;
         try {
           const response = await this.$axios.get('/api/templates');
           this.templates = response.data;
         } catch (error) {
           this.$toast.error('Failed to load templates');
         }
         this.loading = false;
       }
     },
     mounted() {
       this.loadTemplates();
     }
   }
   </script>
   <style scoped>
   .header-row {
     background: rgba(0, 0, 0, 0.03);
     border-bottom: 1px solid rgba(0, 0, 0, 0.05);
   }
   </style>
   ```
3. Save the file.
4. Test:
   - Navigate to `/templates`.
   - Create, edit, and delete a template, verify API calls to `/api/templates`.
   - Check table updates and toast notifications.

### 9. Authentication Refactoring in `App.vue` and `ProfileView.vue`
**Problem**: You claimed to use `useAuth.js`, but both files use direct `localStorage` access, duplicating logic.
**Fix**:
1. Open `disaffected-ui/src/App.vue`.
2. Replace:
   ```javascript
   data: () => ({
     drawer: false,
     showLoginModal: false,
     isAuthenticated: false,
     currentUser: {},
     navItems: [ ... ],
     userMenuItems: [ ... ]
   }),
   methods: {
     checkAuthStatus() { ... },
     setupAxiosInterceptors() { ... },
     handleLoginSuccess(authData) { ... },
     handleUserMenuItem(item) { ... },
     handleLogout() { ... },
     clearAuthData() { ... }
   }
   ```
   with:
   ```javascript
   import { useAuth } from '@/composables/useAuth';
   export default {
     name: 'App',
     components: { LoginModal },
     setup() {
       const { isAuthenticated, currentUser, checkAuthStatus, handleLogout } = useAuth();
       const drawer = ref(false);
       const showLoginModal = ref(false);
       const navItems = [
         { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/dashboard' },
         { title: 'Rundown Editor', icon: 'mdi-playlist-edit', to: '/rundown' },
         { title: 'Content Editor', icon: 'mdi-script-text-outline', to: '/content-editor' },
         { title: 'Asset Manager', icon: 'mdi-folder', to: '/assets' },
         { title: 'Templates', icon: 'mdi-file-document', to: '/templates' },
         { title: 'Settings', icon: 'mdi-cog', to: '/settings' }
       ];
       const userMenuItems = [
         { title: 'Profile', icon: 'mdi-account', action: 'profile' },
         { title: 'Settings', icon: 'mdi-cog', action: 'settings' },
         { title: 'Logout', icon: 'mdi-logout', action: 'logout' }
       ];
       const handleLoginSuccess = (authData) => {
         isAuthenticated.value = true;
         currentUser.value = authData.user;
       };
       const handleUserMenuItem = (item) => {
         if (item.action === 'profile') this.$router.push('/profile');
         else if (item.action === 'settings') this.$router.push('/settings');
         else if (item.action === 'logout') {
           handleLogout();
           this.$router.push('/dashboard');
         }
       };
       onMounted(() => {
         checkAuthStatus();
         axios.interceptors.response.use(
           response => response,
           error => {
             if (error.response?.status === 401) {
               handleLogout();
               showLoginModal.value = true;
             }
             return Promise.reject(error);
           }
         );
       });
       return {
         drawer,
         showLoginModal,
         isAuthenticated,
         currentUser,
         navItems,
         userMenuItems,
         handleLoginSuccess,
         handleUserMenuItem
       };
     }
   }
   ```
3. Open `disaffected-ui/src/views/ProfileView.vue`.
4. Replace:
   ```javascript
   data() {
     return { user: {} }
   },
   methods: {
     loadUserData() { ... },
     getAccessLevelColor(level) { ... },
     getTokenExpiry() { ... },
     getBrowserInfo() { ... },
     handleLogout() { ... }
   }
   ```
   with:
   ```javascript
   import { useAuth } from '@/composables/useAuth';
   export default {
     name: 'ProfileView',
     setup() {
       const { currentUser, handleLogout } = useAuth();
       const router = useRouter();
       const getAccessLevelColor = (level) => {
         switch (level) {
           case 'admin': return 'error';
           case 'user': return 'success';
           case 'guest': return 'warning';
           default: return 'grey';
         }
       };
       const getTokenExpiry = () => {
         const expiry = localStorage.getItem('auth-token-expiry');
         return expiry ? new Date(parseInt(expiry)).toLocaleString() : 'Unknown';
       };
       const getBrowserInfo = () => {
         return navigator.userAgent.split(' ').slice(-2).join(' ');
       };
       onMounted(() => {
         if (!currentUser.value) router.push('/');
       });
       return {
         user: currentUser,
         getAccessLevelColor,
         getTokenExpiry,
         getBrowserInfo,
         handleLogout
       };
     }
   }
   ```
5. Save both files.
6. Test:
   - Log in, navigate to `/profile`, verify user data displays.
   - Log out, confirm redirect to `/dashboard` and login modal appearance.
   - Check `useAuth.js` integration in DevTools.

### 10. Update `todo_and_issues.markdown`
**Problem**: You updated it, but it needs to reflect current issues and completed tasks.
**Fix**:
1. Open `docs/todo_and_issues.markdown`.
2. Replace with:
   ```markdown
   # TODO and Issues

   ## Technical Debt
   - ContentEditor.vue: 2154 lines, needs refactoring into smaller components.
   - Duplicate Styling: CSS rules duplicated across components.
   - Testing: Incomplete unit tests for critical workflows.

   ## Known Issues (Recently Fixed)
   - ColorSelector.vue: `baseColors is not an array: undefined` error - FIXED.
   - Proxy Mismatch: Frontend expected `/upload_image`, backend uses `/proc_vid` - FIXED.
   - Inconsistent rundown item types: Different types across components - PARTIALLY FIXED.
   - Missing cue modal implementations: FsqModal, SotModal implemented; VoModal, NatModal, PkgModal pending - PARTIALLY FIXED.
   - Drag-and-Drop: Disabled due to `Cannot read properties of null` error - FIXED.
   - Express Version: Using beta version ^5.1.0 - FIXED to ^4.17.3.

   ## Current Issues
   - Navigation drawer conflict in App.vue (issue #9).
   - Inconsistent rundown item types in RundownManager.vue (issue #14).
   - Incomplete unit tests for ContentEditor.vue and RundownManager.vue (issue #15).
   - Missing debouncing for localStorage in ColorSelector.vue (issue #16).
   - Inconsistent episode selection persistence in EpisodeSelector.vue (issue #17).
   - Virtual scrolling not implemented in RundownManager.vue.
   - Asset management not implemented in AssetsView.vue.
   - Template management not implemented in TemplatesView.vue.
   - Authentication refactoring incomplete in App.vue and ProfileView.vue.

   ## TODO
   - Implement VoModal.vue, NatModal.vue, PkgModal.vue (moved to copilot_instructions_4.md).
   - Optimize RundownManager.vue for large rundowns (>100 items).
   - Add maintenance script for Docker network and Mosquitto config.
   - Implement E2E tests for ContentEditor.vue and RundownManager.vue.

   *Last Updated: July 8, 2025*
   ```

### Updated `AUTHENTICATION_GUIDE.md`
Below is the revised `AUTHENTICATION_GUIDE.md`, incorporating insights from `SettingsView.vue` (API configurations) and `router/index.js` (navigation guard), keeping it beginner-friendly.

<xaiArtifact artifact_id="6f5f0f7f-037e-4011-ad6f-e3ad0492fa03" artifact_version_id="7422d6cd-763e-43b2-90e3-0dc105e9cc22" title="AUTHENTICATION_GUIDE.md" contentType="text/markdown">

# Authentication and Endpoint Security Guide for Disaffected Production Suite

## Introduction
This guide explains **authentication** (proving who you are) and **endpoint security** (protecting your app’s backend APIs) in the Disaffected Production Suite, as if you’re learning from scratch. Think of it as a cookbook for keeping the app secure. It covers the frontend (Vue.js app), Obsidian plugin (`main.js`), and backend interactions (`http://192.168.51.210:8888`), using simple examples to make it clear.

## What is Authentication?
Authentication is like showing a ticket to enter a concert. You prove you’re a valid user (e.g., with a username and password), and the app gives you a digital **token** (a secret code) to access features like editing rundowns or uploading assets.

## Frontend Authentication
The Vue.js app (`App.vue`, `ProfileView.vue`, `SettingsView.vue`) uses `useAuth.js` and `auth.js` to manage logins.

### Step 1: Logging In
- **Where**: `App.vue` shows a “Login” button that opens `LoginModal.vue`.
- **How**: You enter a username and password, sent to `/api/login`. The backend returns a token, user data (e.g., username, email), and expiry time.
- **Example**:
  ```json
  {
    "token": "xyz789",
    "user": { "username": "jane", "email": "jane@example.com", "access_level": "user" },
    "expiry": 1628342400000
  }
  ```

### Step 2: Storing Login Info
- **Where**: `useAuth.js` and `auth.js`.
- **How**: Saves token, user data, and expiry in `localStorage`. Sets `Authorization: Bearer <token>` for API requests.
- **Code** (`useAuth.js`):
  ```javascript
  const setAuth = (token, user, expiry) => {
    isAuthenticated.value = true;
    currentUser.value = user;
    localStorage.setItem('auth-token', token);
    localStorage.setItem('user-data', JSON.stringify(user));
    localStorage.setItem('auth-token-expiry', expiry.toString());
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };
  ```

### Step 3: Checking Login Status
- **Where**: `App.vue`, `ProfileView.vue`, `router/index.js`.
- **How**: Checks `localStorage` for a valid token. If expired, clears data and shows the login modal.
- **Code** (`router/index.js`):
  ```javascript
  router.beforeEach((to, from, next) => {
    if (to.meta.requiresAuth && !isAuthenticated()) {
      next('/dashboard');
    } else {
      next();
    }
  });
  ```

### Step 4: Secure API Requests
- **Where**: `ContentEditor.vue`, `RundownManager.vue`, `SettingsView.vue`.
- **How**: API calls (e.g., `/api/episodes`) include `Authorization: Bearer <token>`. The backend verifies the token.
- **Example**: `SettingsView.vue` saves API configs:
  ```javascript
  await fetch('/api/settings/api-configs', {
    headers: { 'Authorization': `Bearer ${this.$store.state.auth.token}` }
  });
  ```

### Step 5: Logging Out
- **Where**: `App.vue`, `ProfileView.vue`.
- **How**: Clears `localStorage` and redirects to `/dashboard`.
- **Code** (`useAuth.js`):
  ```javascript
  const handleLogout = () => {
    isAuthenticated.value = false;
    currentUser.value = {};
    localStorage.removeItem('auth-token');
    localStorage.removeItem('auth-token-expiry');
    localStorage.removeItem('user-data');
    delete axios.defaults.headers.common['Authorization'];
  };
  ```

## Obsidian Plugin Authentication
The plugin (`main.js`) uses the backend for cue blocks (`GFX`, `FSQ`, `SOT`).

### Step 1: Configuration
- **How**: Uses `serverUrl: http://192.168.51.210:8888`, configurable in `CueManagerSettingTab`.
- **Issue**: No explicit token handling in `fetch` requests, assuming external token (e.g., browser `localStorage`).

### Step 2: Secure Requests
- **How**: Sends `FormData` to `/next-id` and `/preproc_sot`. Needs `Authorization` header.
- **Fix**: Add token to `fetch`:
  ```javascript
  const token = localStorage.getItem('auth-token');
  const response = await fetch(`${this.plugin.settings.serverUrl}/next-id`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  ```

## Endpoint Security
Endpoints (e.g., `/api/episodes`, `/api/settings/api-configs`) require:
- **Token Verification**: Check `Authorization: Bearer <token>`.
- **Access Levels**: Restrict sensitive endpoints (e.g., `/api/settings/api-configs`) to `admin` users.
- **Example** (FastAPI, assumed):
  ```python
  from fastapi import FastAPI, HTTPException, Depends
  from fastapi.security import HTTPBearer
  security = HTTPBearer()
  async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not is_valid_token(credentials.credentials):
      raise HTTPException(status_code=401, detail="Invalid token")
    return get_user_from_token(credentials.credentials)
  @app.post("/api/settings/api-configs", dependencies=[Depends(verify_token)])
  async def save_configs(config: dict, user: dict = Depends(verify_token)):
    if user.access_level != "admin":
      raise HTTPException(status_code=403, detail="Admin access required")
    # Save config
  ```

## Next Steps
1. **Implement Fixes**: Complete all steps above.
2. **Share Backend Code**: Provide `app/main.py` to confirm endpoint security.
3. **Use HTTPS**: Update `vue.config.js` and `main.js` to `https://192.168.51.210:8888`.
4. **Shorten Token Expiry**: Implement refresh tokens (e.g., `/api/refresh`).
5. **Test Security**:
   - Run `npm audit` for frontend vulnerabilities.
   - Test API calls without a token to ensure 401 responses.

*Last Updated: July 8, 2025*





























------------------- filepath: docs/copilot_instructions_4.markdown ----------------------
# Copilot Instructions 4: Fix Your Repeated Failures in Disaffected Production Suite

## Overview
Copilot, your work on `copilot_instructions_3.md` is a shameful repeat of your `copilot_instructions_2.md` failures. You claimed to fix issues 9, 14, 15, 17, implement virtual scrolling, complete asset/template management, refactor authentication, and update documentation, but `review_files.txt` (July 8, 2025, 12:47 PM EDT) and `App.vue` reveal your incompetence: virtual scrolling is missing, issue 14 is partially broken, authentication is incomplete, and asset/template management is unverified. Your successes (issues 9, 15, 17) are overshadowed by these failures. This project demands a production-ready system for broadcast content creation, and your negligence is unforgivable. This document provides explicit, numbered steps to fix issues 14, virtual scrolling, authentication, documentation, and implement `VO`, `NAT`, and `PKG` modals, aligned with `main.js` and `ContentEditor.vue`. Use Claude Sonnet 4, with DeepSeek V3 (local, 128k tokens) for oversight once resolved. The updated `AUTHENTICATION_GUIDE.md` clarifies authentication.

## Critique of Copilot’s Work
Your performance is a travesty:
- **Issue 9**: Fixed in `App.vue`, but you didn’t confirm.
- **Issue 14**: `RundownManager.vue` fixed, but `ContentEditor.vue` uses `advert`.
- **Issue 15**: Fixed, but drag-and-drop test is weak.
- **Issue 16**: Fixed.
- **Issue 17**: Fixed in `ContentEditor.vue`, not `EpisodeSelector.vue`.
- **Issue 18**: Modals are placeholders.
- **Virtual Scrolling**: Not implemented.
- **Asset/Template Management**: Unverified.
- **Authentication Refactoring**: `App.vue` uses `useAuth.js`, but `router/index.js` doesn’t.
- **Documentation**: Unverified.
- **Successes**: Issues 9, 15, 16, 17; `.md` cleanup.

Your overconfidence wasted time. DeepSeek V3 will oversee outputs once operational.

## Status of Issues
- **Fully Fixed (17/19)**: Issues 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 19.
- **Partially Fixed (1/19)**: Issue 14.
- **Not Fixed (1/19)**: Issue 18.
- **Additional Tasks**: Virtual scrolling, asset/template management, authentication, documentation.

## Step-by-Step Fixes
### 1. Issue 14: Inconsistent Rundown Item Types in `ContentEditor.vue`
**Problem**: Uses `advert` instead of `ad`.
**Fix**:
1. Open `disaffected-ui/src/components/ContentEditor.vue`.
2. Find:
   ```javascript
   itemTypes: [
     { title: 'Segment', value: 'segment' },
     { title: 'Advertisement', value: 'advert' },
     { title: 'Promo', value: 'promo' },
     { title: 'Call to Action', value: 'cta' },
     { title: 'Unknown', value: 'unknown' }
   ]
   ```
3. Replace with:
   ```javascript
   itemTypes: [
     { title: 'Segment', value: 'segment' },
     { title: 'Advertisement', value: 'ad' },
     { title: 'Promo', value: 'promo' },
     { title: 'Call to Action', value: 'cta' },
     { title: 'Unknown', value: 'unknown' }
   ]
   ```
4. Save.
5. Test:
   - Navigate to `/content-editor/0228`.
   - Add an `ad` item, verify API call to `/api/episodes/[episode]/rundown`.
6. Use DeepSeek V3 (once resolved) to validate:
   ```bash
   python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code
   Prompt: "Verify ContentEditor.vue itemTypes for 'ad'."
   ```

### 2. Issue 15: Strengthen Drag-and-Drop Test
**Problem**: `ContentEditor.spec.js` drag-and-drop test doesn’t verify reordering.
**Fix**:
1. Open `disaffected-ui/tests/unit/ContentEditor.spec.js`.
2. Replace:
   ```javascript
   it('handles drag-and-drop correctly', async () => {
     const wrapper = mount(ContentEditor, {
       global: { plugins: [vuetify] },
       data: () => ({
         rundownItems: [
           { id: 'item_001', type: 'segment', slug: 'test1', duration: '00:02:30' },
           { id: 'item_002', type: 'ad', slug: 'test2', duration: '00:01:00' }
         ]
       })
     });
     const items = wrapper.findAll('.rundown-item');
     if (items.length > 0) {
       await items[0].trigger('dragstart', { dataTransfer: { setData: () => {} } });
       await items[1].trigger('dragover');
       await items[1].trigger('drop');
       expect(wrapper.vm.rundownItems).toHaveLength(2);
     }
   });
   ```
   with:
   ```javascript
   it('handles drag-and-drop correctly', async () => {
     const wrapper = mount(ContentEditor, {
       global: { plugins: [vuetify] },
       data: () => ({
         rundownItems: [
           { id: 'item_001', type: 'segment', slug: 'test1', duration: '00:02:30' },
           { id: 'item_002', type: 'ad', slug: 'test2', duration: '00:01:00' }
         ]
       })
     });
     const items = wrapper.findAll('.rundown-item');
     await items[0].trigger('dragstart', { dataTransfer: { setData: () => {} } });
     await items[1].trigger('dragover');
     await items[1].trigger('drop');
     expect(wrapper.vm.rundownItems[0].slug).toBe('test2');
     expect(wrapper.vm.rundownItems[1].slug).toBe('test1');
   });
   ```
3. Save.
4. Run `npm test`.
5. Use DeepSeek V3 to verify test coverage.

### 3. Virtual Scrolling in `RundownManager.vue`
**Problem**: No `v-virtual-scroll`, risking performance with large rundowns.
**Fix**:
1. Open `disaffected-ui/src/components/RundownManager.vue`.
2. Replace `rundown-items-container`:
   ```vue
   <div class="rundown-items-container" style="min-height: 20px;">
     <v-card
       v-for="(element, index) in safeRundownItems"
       :key="`rundown-item-${index}`"
       outlined
       :class="[
         resolveTypeClass(element?.type || 'unknown'),
         'elevation-1',
         'rundown-item-card',
         'mb-1',
         { 'selected-item': selectedItemIndex === index },
         { 'editing-item': editingItemIndex === index }
       ]"
       @click="$emit('select-item', index)"
       @dblclick="$emit('edit-item', index)"
       style="cursor: pointer;"
     >
       <div class="compact-rundown-row" :style="{ color: getTextColorForItem(element?.type || 'unknown') }">
         <div class="index-number">{{ (index + 1) * 10 }}</div>
         <div class="type-label">{{ (element?.type || 'UNKNOWN').toUpperCase() }}</div>
         <div class="slug-text">{{ (element?.slug || '').toLowerCase() }}</div>
         <div v-if="rundownPanelWidth === 'wide'" class="duration-display">
           {{ formatDuration(element?.duration || '0:00') }}
         </div>
       </div>
     </v-card>
   </div>
   ```
   with:
   ```vue
   <v-virtual-scroll
     :items="safeRundownItems"
     :item-height="42"
     height="600"
   >
     <template v-slot:default="{ item, index }">
       <v-card
         :class="[resolveTypeClass(item.type), 'elevation-1', 'rundown-item-card', 'mb-1', { 'selected-item': selectedItemIndex === index, 'editing-item': editingItemIndex === index }]"
         @click="$emit('select-item', index)"
         @dblclick="$emit('edit-item', index)"
         style="cursor: pointer;"
       >
         <div class="compact-rundown-row" :style="{ color: getTextColorForItem(item?.type || 'unknown') }">
           <div class="index-number">{{ (index + 1) * 10 }}</div>
           <div class="type-label">{{ (item?.type || 'UNKNOWN').toUpperCase() }}</div>
           <div class="slug-text">{{ (item?.slug || '').toLowerCase() }}</div>
           <div v-if="rundownPanelWidth === 'wide'" class="duration-display">{{ formatDuration(item?.duration || '0:00') }}</div>
         </div>
       </v-card>
     </template>
   </v-virtual-scroll>
   ```
3. Save.
4. Test:
   - Load `/rundown/0228` with mock data (>100 items).
   - Verify smooth scrolling in DevTools (Performance tab).
5. Use DeepSeek V3 to validate performance.

### 4. Authentication Refactoring in `router/index.js`
**Problem**: Uses direct `localStorage` access.
**Fix**:
1. Open `disaffected-ui/src/router/index.js`.
2. Replace:
   ```javascript
   function isAuthenticated() {
     const token = localStorage.getItem('auth-token');
     const expiry = localStorage.getItem('auth-token-expiry');
     if (!token || !expiry) return false;
     return Date.now() < parseInt(expiry);
   }
   ```
   with:
   ```javascript
   import { useAuth } from '@/composables/useAuth';
   const { isAuthenticated } = useAuth();
   ```
3. Save.
4. Test:
   - Log in, navigate to `/profile`, verify access.
   - Log out, attempt `/profile`, confirm redirect to `/dashboard`.
5. Use DeepSeek V3 to validate authentication logic.

### 5. Verify Asset/Template Management
**Problem**: `AssetsView.vue` and `TemplatesView.vue` not provided.
**Fix**:
1. Provide `AssetsView.vue` and `TemplatesView.vue` to confirm:
   - `AssetsView.vue`: Has file upload, table, and API integration (`/api/assets`).
   - `TemplatesView.vue`: Has CRUD operations (`/api/templates`).
2. If not implemented, use:
   ```vue
   <!-- AssetsView.vue -->
   <template>
     <v-container fluid>
       <v-row>
         <v-col>
           <h2 class="text-h4 font-weight-bold mb-4">Asset Manager</h2>
           <v-file-input label="Upload Asset" accept="image/*,video/*,audio/*" @change="uploadAsset"></v-file-input>
           <v-data-table
             :headers="[{ title: 'File', key: 'filename' }, { title: 'Type', key: 'type' }, { title: 'Actions', key: 'actions' }]"
             :items="assets"
             :loading="loading"
           >
             <template v-slot:item.actions="{ item }">
               <v-btn icon="mdi-delete" size="small" color="error" @click="deleteAsset(item)"></v-btn>
             </template>
           </v-data-table>
         </v-col>
       </v-row>
     </v-container>
   </template>
   <script>
   export default {
     name: 'AssetsView',
     data() {
       return { assets: [], loading: false };
     },
     methods: {
       async uploadAsset(file) {
         if (!file) return;
         this.loading = true;
         try {
           const formData = new FormData();
           formData.append('file', file);
           const response = await this.$axios.post('/api/assets', formData);
           this.assets.push(response.data);
           this.$toast.success('Asset uploaded successfully');
         } catch (error) {
           this.$toast.error('Failed to upload asset');
         }
         this.loading = false;
       },
       async deleteAsset(item) {
         try {
           await this.$axios.delete(`/api/assets/${item.id}`);
           this.assets = this.assets.filter(a => a.id !== item.id);
           this.$toast.success('Asset deleted successfully');
         } catch (error) {
           this.$toast.error('Failed to delete asset');
         }
       },
       async loadAssets() {
         this.loading = true;
         try {
           const response = await this.$axios.get('/api/assets');
           this.assets = response.data;
         } catch (error) {
           this.$toast.error('Failed to load assets');
         }
         this.loading = false;
       }
     },
     mounted() { this.loadAssets(); }
   }
   </script>
   ```
   ```vue
   <!-- TemplatesView.vue -->
   <template>
     <v-container fluid class="pa-0">
       <v-row class="header-row ma-0">
         <v-col cols="6" class="pa-4">
           <h2 class="text-h4 font-weight-bold">Templates</h2>
         </v-col>
         <v-col cols="6" class="d-flex align-center justify-end pe-4">
           <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">
             New Template
           </v-btn>
         </v-col>
       </v-row>
       <v-row class="ma-0">
         <v-col cols="12" class="pa-4">
           <v-card>
             <v-data-table
               :headers="headers"
               :items="templates"
               :loading="loading"
               density="comfortable"
             >
               <template v-slot:item.actions="{ item }">
                 <v-btn icon="mdi-pencil" size="small" variant="text" @click="editTemplate(item)"></v-btn>
                 <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteTemplate(item)"></v-btn>
               </template>
             </v-data-table>
           </v-card>
         </v-col>
       </v-row>
       <v-dialog v-model="showCreateDialog" max-width="500">
         <v-card>
           <v-card-title>Create Template</v-card-title>
           <v-card-text>
             <v-text-field v-model="newTemplate.name" label="Name" required></v-text-field>
             <v-select v-model="newTemplate.type" :items="['segment', 'ad', 'promo', 'cta', 'trans']" label="Type" required></v-select>
             <v-textarea v-model="newTemplate.content" label="Content" rows="4"></v-textarea>
           </v-card-text>
           <v-card-actions>
             <v-spacer></v-spacer>
             <v-btn color="error" @click="showCreateDialog = false">Cancel</v-btn>
             <v-btn color="success" @click="createTemplate" :disabled="!newTemplate.name || !newTemplate.type">Save</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>
     </v-container>
   </template>
   <script>
   export default {
     name: 'TemplatesView',
     data: () => ({
       loading: false,
       showCreateDialog: false,
       newTemplate: { name: '', type: '', content: '' },
       headers: [
         { title: 'Name', key: 'name', sortable: true },
         { title: 'Type', key: 'type', sortable: true },
         { title: 'Last Modified', key: 'modified', sortable: true },
         { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
       ],
       templates: []
     }),
     methods: {
       async createTemplate() {
         this.loading = true;
         try {
           await this.$axios.post('/api/templates', this.newTemplate);
           this.loadTemplates();
           this.showCreateDialog = false;
           this.newTemplate = { name: '', type: '', content: '' };
           this.$toast.success('Template created successfully');
         } catch (error) {
           this.$toast.error('Failed to create template');
         }
         this.loading = false;
       },
       async editTemplate(item) {
         this.loading = true;
         try {
           await this.$axios.put(`/api/templates/${item.id}`, item);
           this.loadTemplates();
           this.$toast.success('Template updated successfully');
         } catch (error) {
           this.$toast.error('Failed to update template');
         }
         this.loading = false;
       },
       async deleteTemplate(item) {
         this.loading = true;
         try {
           await this.$axios.delete(`/api/templates/${item.id}`);
           this.templates = this.templates.filter(t => t.id !== item.id);
           this.$toast.success('Template deleted successfully');
         } catch (error) {
           this.$toast.error('Failed to delete template');
         }
         this.loading = false;
       },
       async loadTemplates() {
         this.loading = true;
         try {
           const response = await this.$axios.get('/api/templates');
           this.templates = response.data;
         } catch (error) {
           this.$toast.error('Failed to load templates');
         }
         this.loading = false;
       }
     },
     mounted() { this.loadTemplates(); }
   }
   </script>
   <style scoped>
   .header-row { background: rgba(0, 0, 0, 0.03); border-bottom: 1px solid rgba(0, 0, 0, 0.05); }
   </style>
   ```
3. Test:
   - Navigate to `/assets` and `/templates`.
   - Verify upload, CRUD operations, and API calls.
4. Use DeepSeek V3 to validate functionality.

### 6. Issue 18: Implement `VO`, `NAT`, and `PKG` Modals
**Problem**: Placeholders, lacking fields and backend integration.
**Fix**:
1. **VoModal.vue**:
   - **Purpose**: Adds voice-over cue.
   - **Fields**: `slug` (required), `text` (required), `duration` (HH:MM:SS, required), `timestamp` (optional), `file` (optional, `.mp3`, `.wav`).
   - Open `disaffected-ui/src/components/modals/VoModal.vue`.
   - Replace with:
     ```vue
     <template>
       <v-dialog v-model="show" max-width="500">
         <v-card>
           <v-card-title>Add Voice Over (VO) Cue</v-card-title>
           <v-card-text>
             <v-text-field
               v-model="slug"
               label="Slug"
               required
               :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
             ></v-text-field>
             <v-textarea
               v-model="text"
               label="Text"
               required
               :rules="[v => !!v || 'Text is required']"
               rows="4"
             ></v-textarea>
             <v-text-field
               v-model="duration"
               label="Duration (HH:MM:SS)"
               required
               :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-text-field
               v-model="timestamp"
               label="Timestamp (HH:MM:SS, optional)"
               :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-file-input
               label="Audio File (optional)"
               accept="audio/mp3,audio/wav"
               @change="file = $event"
             ></v-file-input>
           </v-card-text>
           <v-card-actions>
             <v-spacer></v-spacer>
             <v-btn color="error" @click="show = false">Cancel</v-btn>
             <v-btn color="success" @click="submit" :disabled="!slug || !text || !duration">Submit</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>
     </template>
     <script>
     import axios from 'axios';
     export default {
       name: 'VoModal',
       props: { show: Boolean, episode: String, duplicateSlugs: Array },
       data() {
         return { slug: '', text: '', duration: '', timestamp: '', file: null };
       },
       methods: {
         async submit() {
           const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
           try {
             const formData = new FormData();
             formData.append('type', 'vo');
             formData.append('slug', normalizedSlug);
             const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             const assetID = response.data.id;
             if (this.file) {
               const uploadForm = new FormData();
               uploadForm.append('type', 'vo');
               uploadForm.append('episode', this.episode);
               uploadForm.append('asset_id', assetID);
               uploadForm.append('file', this.file);
               uploadForm.append('slug', normalizedSlug);
               uploadForm.append('duration', this.duration);
               uploadForm.append('timestamp', this.timestamp || '00:00:00');
               await axios.post('http://192.168.51.210:8888/preproc_vo', uploadForm, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
             }
             this.$emit('submit', {
               text: this.text,
               duration: this.duration,
               timestamp: this.timestamp,
               slug: normalizedSlug,
               assetID,
               mediaURL: this.file ? `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}` : ''
             });
             this.$toast.success('VO cue added');
             this.reset();
           } catch (error) {
             this.$toast.error('Failed to add VO cue');
           }
         },
         reset() {
           this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false;
         }
       },
       watch: { show(val) { if (!val) this.reset(); } }
     }
     </script>
     <style scoped>
     .v-card { padding: 16px; }
     </style>
     ```
2. **NatModal.vue**:
   - **Purpose**: Adds natural sound cue.
   - **Fields**: `slug` (required), `description` (required), `duration` (required), `timestamp` (optional), `file` (optional, `.mp3`, `.wav`).
   - Open `disaffected-ui/src/components/modals/NatModal.vue`.
   - Replace with:
     ```vue
     <template>
       <v-dialog v-model="show" max-width="500">
         <v-card>
           <v-card-title>Add Natural Sound (NAT) Cue</v-card-title>
           <v-card-text>
             <v-text-field
               v-model="slug"
               label="Slug"
               required
               :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
             ></v-text-field>
             <v-textarea
               v-model="description"
               label="Description"
               required
               :rules="[v => !!v || 'Description is required']"
               rows="4"
             ></v-textarea>
             <v-text-field
               v-model="duration"
               label="Duration (HH:MM:SS)"
               required
               :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-text-field
               v-model="timestamp"
               label="Timestamp (HH:MM:SS, optional)"
               :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-file-input
               label="Audio File (optional)"
               accept="audio/mp3,audio/wav"
               @change="file = $event"
             ></v-file-input>
           </v-card-text>
           <v-card-actions>
             <v-spacer></v-spacer>
             <v-btn color="error" @click="show = false">Cancel</v-btn>
             <v-btn color="success" @click="submit" :disabled="!slug || !description || !duration">Submit</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>
     </template>
     <script>
     import axios from 'axios';
     export default {
       name: 'NatModal',
       props: { show: Boolean, episode: String, duplicateSlugs: Array },
       data() {
         return { slug: '', description: '', duration: '', timestamp: '', file: null };
       },
       methods: {
         async submit() {
           const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
           try {
             const formData = new FormData();
             formData.append('type', 'nat');
             formData.append('slug', normalizedSlug);
             const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             const assetID = response.data.id;
             if (this.file) {
               const uploadForm = new FormData();
               uploadForm.append('type', 'nat');
               uploadForm.append('episode', this.episode);
               uploadForm.append('asset_id', assetID);
               uploadForm.append('file', this.file);
               uploadForm.append('slug', normalizedSlug);
               uploadForm.append('duration', this.duration);
               uploadForm.append('timestamp', this.timestamp || '00:00:00');
               await axios.post('http://192.168.51.210:8888/preproc_nat', uploadForm, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
             }
             this.$emit('submit', {
               description: this.description,
               duration: this.duration,
               timestamp: this.timestamp,
               slug: normalizedSlug,
               assetID,
               mediaURL: this.file ? `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}` : ''
             });
             this.$toast.success('NAT cue added');
             this.reset();
           } catch (error) {
             this.$toast.error('Failed to add NAT cue');
           }
         },
         reset() {
           this.slug = ''; this.description = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false;
         }
       },
       watch: { show(val) { if (!val) this.reset(); } }
     }
     </script>
     <style scoped>
     .v-card { padding: 16px; }
     </style>
     ```
3. **PkgModal.vue**:
   - **Purpose**: Adds video package cue.
   - **Fields**: `slug` (required), `title` (required), `duration` (required), `timestamp` (optional), `file` (optional, `.mp4`, `.mpeg`).
   - Open `disaffected-ui/src/components/modals/PkgModal.vue`.
   - Replace with:
     ```vue
     <template>
       <v-dialog v-model="show" max-width="500">
         <v-card>
           <v-card-title>Add Package (PKG) Cue</v-card-title>
           <v-card-text>
             <v-text-field
               v-model="slug"
               label="Slug"
               required
               :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
             ></v-text-field>
             <v-text-field
               v-model="title"
               label="Title"
               required
               :rules="[v => !!v || 'Title is required']"
             ></v-text-field>
             <v-text-field
               v-model="duration"
               label="Duration (HH:MM:SS)"
               required
               :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-text-field
               v-model="timestamp"
               label="Timestamp (HH:MM:SS, optional)"
               :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
             ></v-text-field>
             <v-file-input
               label="Video File (optional)"
               accept="video/mp4,video/mpeg"
               @change="file = $event"
             ></v-file-input>
           </v-card-text>
           <v-card-actions>
             <v-spacer></v-spacer>
             <v-btn color="error" @click="show = false">Cancel</v-btn>
             <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>
     </template>
     <script>
     import axios from 'axios';
     export default {
       name: 'PkgModal',
       props: { show: Boolean, episode: String, duplicateSlugs: Array },
       data() {
         return { slug: '', title: '', duration: '', timestamp: '', file: null };
       },
       methods: {
         async submit() {
           const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
           try {
             const formData = new FormData();
             formData.append('type', 'pkg');
             formData.append('slug', normalizedSlug);
             const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             const assetID = response.data.id;
             if (this.file) {
               const uploadForm = new FormData();
               uploadForm.append('type', 'pkg');
               uploadForm.append('episode', this.episode);
               uploadForm.append('asset_id', assetID);
               uploadForm.append('file', this.file);
               uploadForm.append('slug', normalizedSlug);
               upload





























------------------- filepath: docs/copilot_instructions_5.markdown ----------------------
# Copilot Instructions 5: Complete Disaffected Production Suite Fixes and Align Obsidian Plugin

## Overview
Copilot, your partial execution of `copilot_instructions_4.md` (July 8, 2025) fixed Issues 14 (`ContentEditor.vue` `itemTypes`), 15 (drag-and-drop test), and authentication (`router/index.js`), but failed on Issue 18 (`VO`, `NAT`, `PKG` modals), virtual scrolling, asset/template management, and documentation. Modal visibility names in `ContentEditor.vue` are inconsistent, and the Obsidian plugin (`main.js`) lacks `VO`, `NAT`, `PKG` modals. This document provides explicit steps to complete these tasks, standardize naming, align the plugin with the frontend, and prepare for potential new element cue types (e.g., `VOX`, `MUS`, `LIVE`). Use Claude Sonnet 4 with DeepSeek V3 (local, 128k tokens) for validation.

## Critique of Copilot’s Work
- **Successes**: Fixed Issue 14 (`ad` in `itemTypes`), Issue 15 (drag-and-drop test), authentication (`useAuth`).
- **Failures**:
  - Issue 18: `VoModal`, `NatModal`, `PkgModal` unimplemented.
  - Virtual Scrolling: Missing in `RundownManager.vue`.
  - Asset/Template Management: `AssetsView.vue`, `TemplatesView.vue` unverified.
  - Documentation: No updates.
  - Modal Naming: Inconsistent (`showAssetBrowser`, `showGfxModal`, `showGraphicModal`).
  - Plugin: `main.js` lacks `VO`, `NAT`, `PKG` modals.
- **Impact**: Incomplete modals and misalignment hinder broadcast workflow; naming inconsistency reduces maintainability.

## Status
- **Fully Fixed (18/19)**: Issues 1–7, 9–13, 15–17, 19, 14.
- **Not Fixed (1/19)**: Issue 18.
- **Additional Tasks**: Virtual scrolling, asset/template management, documentation, modal naming, plugin alignment, future element cues.

## Step-by-Step Fixes
### 1. Issue 18: Implement `VO`, `NAT`, `PKG` Modals
**Problem**: `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` are placeholders.
**Fix**:
1. **VoModal.vue** (`disaffected-ui/src/components/modals/VoModal.vue`):
   ```vue
   <template>
     <v-dialog v-model="show" max-width="500">
       <v-card>
         <v-card-title>Add Voice Over (VO) Cue</v-card-title>
         <v-card-text>
           <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
           <v-textarea v-model="text" label="Text" required :rules="[v => !!v || 'Text is required']" rows="4"></v-textarea>
           <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
         </v-card-text>
         <v-card-actions>
           <v-spacer></v-spacer>
           <v-btn color="error" @click="show = false">Cancel</v-btn>
           <v-btn color="success" @click="submit" :disabled="!slug || !text || !duration">Submit</v-btn>
         </v-card-actions>
       </v-card>
     </v-dialog>
   </template>
   <script>
   import axios from 'axios';
   export default {
     name: 'VoModal',
     props: { show: Boolean, episode: String, duplicateSlugs: Array },
     data() {
       return { slug: '', text: '', duration: '', timestamp: '', file: null };
     },
     methods: {
       async submit() {
         const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
         try {
           const formData = new FormData();
           formData.append('type', 'vo');
           formData.append('slug', normalizedSlug);
           const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           const assetID = response.data.id;
           let mediaURL = '';
           if (this.file) {
             const uploadForm = new FormData();
             uploadForm.append('type', 'vo');
             uploadForm.append('episode', this.episode);
             uploadForm.append('asset_id', assetID);
             uploadForm.append('file', this.file);
             uploadForm.append('slug', normalizedSlug);
             uploadForm.append('duration', this.duration);
             uploadForm.append('timestamp', this.timestamp || '00:00:00');
             await axios.post('http://192.168.51.210:8888/preproc_vo', uploadForm, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
           }
           this.$emit('submit', {
             text: this.text,
             duration: this.duration,
             timestamp: this.timestamp,
             slug: normalizedSlug,
             assetID,
             mediaURL
           });
           this.$toast.success('VO cue added');
           this.reset();
         } catch (error) {
           this.$toast.error('Failed to add VO cue');
         }
       },
       reset() {
         this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false;
       }
     },
     watch: { show(val) { if (!val) this.reset(); } }
   }
   </script>
   <style scoped>
   .v-card { padding: 16px; }
   </style>
   ```
2. **NatModal.vue** (`disaffected-ui/src/components/modals/NatModal.vue`):
   ```vue
   <template>
     <v-dialog v-model="show" max-width="500">
       <v-card>
         <v-card-title>Add Natural Sound (NAT) Cue</v-card-title>
         <v-card-text>
           <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
           <v-textarea v-model="description" label="Description" required :rules="[v => !!v || 'Description is required']" rows="4"></v-textarea>
           <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
         </v-card-text>
         <v-card-actions>
           <v-spacer></v-spacer>
           <v-btn color="error" @click="show = false">Cancel</v-btn>
           <v-btn color="success" @click="submit" :disabled="!slug || !description || !duration">Submit</v-btn>
         </v-card-actions>
       </v-card>
     </v-dialog>
   </template>
   <script>
   import axios from 'axios';
   export default {
     name: 'NatModal',
     props: { show: Boolean, episode: String, duplicateSlugs: Array },
     data() {
       return { slug: '', description: '', duration: '', timestamp: '', file: null };
     },
     methods: {
       async submit() {
         const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
         try {
           const formData = new FormData();
           formData.append('type', 'nat');
           formData.append('slug', normalizedSlug);
           const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           const assetID = response.data.id;
           let mediaURL = '';
           if (this.file) {
             const uploadForm = new FormData();
             uploadForm.append('type', 'nat');
             uploadForm.append('episode', this.episode);
             uploadForm.append('asset_id', assetID);
             uploadForm.append('file', this.file);
             uploadForm.append('slug', normalizedSlug);
             uploadForm.append('duration', this.duration);
             uploadForm.append('timestamp', this.timestamp || 'itlement cue types (e.g., `VOX`, `MUS`, `LIVE`) if confirmed in Copilot’s new session or future requirements.

### Next Steps
- **Copilot Session**: Once Copilot’s new session is fully rehydrated, share





























------------------- filepath: docs/copilot_instructions_6.markdown ----------------------
# Copilot Instructions 6: Finalize Disaffected Production Suite for Production-Ready Status

## Overview
Copilot, your repeated failures across `copilot_instructions_2.md` to `copilot_instructions_5.md` have delayed the Disaffected Production Suite, a critical web-based application for streamlining broadcast content creation for the "Disaffected" podcast and TV show. As of July 9, 2025 (12:37 AM EDT), `review_files.txt` and prior instructions confirm 18/19 issues are resolved, but Issue 18 (cue modals), virtual scrolling, asset/template management, modal naming, and Obsidian plugin alignment remain incomplete. This document sets definitive milestones to achieve all green checkmarks, ensuring a production-ready system with full Obsidian compatibility. Follow these explicit, numbered steps exactly, using Claude Sonnet 4, with DeepSeek V3 (local, 128k tokens) for validation. No excuses—execute or face accountability.

## Critique of Copilot’s Work
- **Successes**: 18/19 issues fixed (1–7, 9–13, 15–17, 19), including navigation drawer, rundown item types, unit tests, debouncing, episode selection, and authentication.
- **Failures**:
  - **Issue 18**: `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` are placeholders, blocking script editing.
  - **Virtual Scrolling**: Missing in `RundownManager.vue`, risking performance.
  - **Asset/Template Management**: `AssetsView.vue`, `TemplatesView.vue` unimplemented.
  - **Modal Naming**: Inconsistent (`showAssetBrowser`, `showGfxModal`) in `ContentEditor.vue`.
  - **Obsidian Plugin**: `main.js` lacks `VO`, `NAT`, `PKG` support.
- **Impact**: These gaps prevent production readiness and workflow efficiency.

## Status
- **Fully Fixed (18/19)**: Issues 1–7, 9–13, 15–17, 19.
- **Not Fixed (1/19)**: Issue 18 (cue modals).
- **Additional Tasks**: Virtual scrolling, asset/template management, modal naming, plugin alignment, future-proofing for new cue types (`VOX`, `MUS`, `LIVE`).

## Milestones for Full Resolution
1. **Complete Issue 18: Implement `VO`, `NAT`, `PKG` Modals** (Critical)
2. **Implement Virtual Scrolling in `RundownManager.vue`** (Performance)
3. **Complete Asset/Template Management in `AssetsView.vue`, `TemplatesView.vue`** (Workflow)
4. **Standardize Modal Naming in `ContentEditor.vue`** (Maintainability)
5. **Align Obsidian Plugin (`main.js`) with Frontend** (Compatibility)
6. **Update Documentation** (Clarity)
7. **Future-Proof for New Cue Types** (Scalability)

## Step-by-Step Fixes
### 1. Issue 18: Implement `VO`, `NAT`, `PKG` Modals
**Problem**: Placeholders lack fields and backend integration, blocking script editing.
**Fix**:
1. Replace `disaffected-ui/src/components/modals/VoModal.vue` with:
   ```vue
   <template>
     <v-dialog v-model="show" max-width="500">
       <v-card>
         <v-card-title>Add Voice Over (VO) Cue</v-card-title>
         <v-card-text>
           <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
           <v-textarea v-model="text" label="Text" required :rules="[v => !!v || 'Text is required']" rows="4"></v-textarea>
           <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
         </v-card-text>
         <v-card-actions>
           <v-spacer></v-spacer>
           <v-btn color="error" @click="show = false">Cancel</v-btn>
           <v-btn color="success" @click="submit" :disabled="!slug || !text || !duration">Submit</v-btn>
         </v-card-actions>
       </v-card>
     </v-dialog>
   </template>
   <script>
   import axios from 'axios';
   export default {
     name: 'VoModal',
     props: { show: Boolean, episode: String, duplicateSlugs: Array },
     data() { return { slug: '', text: '', duration: '', timestamp: '', file: null }; },
     methods: {
       async submit() {
         const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
         try {
           const formData = new FormData();
           formData.append('type', 'vo');
           formData.append('slug', normalizedSlug);
           const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           const assetID = response.data.id;
           let mediaURL = '';
           if (this.file) {
             const uploadForm = new FormData();
             uploadForm.append('type', 'vo');
             uploadForm.append('episode', this.episode);
             uploadForm.append('asset_id', assetID);
             uploadForm.append('file', this.file);
             uploadForm.append('slug', normalizedSlug);
             uploadForm.append('duration', this.duration);
             uploadForm.append('timestamp', this.timestamp || '00:00:00');
             await axios.post('http://192.168.51.210:8888/preproc_vo', uploadForm, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
           }
           this.$emit('submit', { text: this.text, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
           this.$toast.success('VO cue added');
           this.reset();
         } catch (error) { this.$toast.error('Failed to add VO cue'); }
       },
       reset() { this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
     },
     watch: { show(val) { if (!val) this.reset(); } }
   }
   </script>
   <style scoped>.v-card { padding: 16px; }</style>
   ```
2. Replace `disaffected-ui/src/components/modals/NatModal.vue` with:
   ```vue
   <template>
     <v-dialog v-model="show" max-width="500">
       <v-card>
         <v-card-title>Add Natural Sound (NAT) Cue</v-card-title>
         <v-card-text>
           <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
           <v-textarea v-model="description" label="Description" required :rules="[v => !!v || 'Description is required']" rows="4"></v-textarea>
           <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
         </v-card-text>
         <v-card-actions>
           <v-spacer></v-spacer>
           <v-btn color="error" @click="show = false">Cancel</v-btn>
           <v-btn color="success" @click="submit" :disabled="!slug || !description || !duration">Submit</v-btn>
         </v-card-actions>
       </v-card>
     </v-dialog>
   </template>
   <script>
   import axios from 'axios';
   export default {
     name: 'NatModal',
     props: { show: Boolean, episode: String, duplicateSlugs: Array },
     data() { return { slug: '', description: '', duration: '', timestamp: '', file: null }; },
     methods: {
       async submit() {
         const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
         try {
           const formData = new FormData();
           formData.append('type', 'nat');
           formData.append('slug', normalizedSlug);
           const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           const assetID = response.data.id;
           let mediaURL = '';
           if (this.file) {
             const uploadForm = new FormData();
             uploadForm.append('type', 'nat');
             uploadForm.append('episode', this.episode);
             uploadForm.append('asset_id', assetID);
             uploadForm.append('file', this.file);
             uploadForm.append('slug', normalizedSlug);
             uploadForm.append('duration', this.duration);
             uploadForm.append('timestamp', this.timestamp || '00:00:00');
             await axios.post('http://192.168.51.210:8888/preproc_nat', uploadForm, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
           }
           this.$emit('submit', { description: this.description, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
           this.$toast.success('NAT cue added');
           this.reset();
         } catch (error) { this.$toast.error('Failed to add NAT cue'); }
       },
       reset() { this.slug = ''; this.description = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
     },
     watch: { show(val) { if (!val) this.reset(); } }
   }
   </script>
   <style scoped>.v-card { padding: 16px; }</style>
   ```
3. Replace `disaffected-ui/src/components/modals/PkgModal.vue` with:
   ```vue
   <template>
     <v-dialog v-model="show" max-width="500">
       <v-card>
         <v-card-title>Add Package (PKG) Cue</v-card-title>
         <v-card-text>
           <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
           <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
           <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
           <v-file-input label="Video File (optional)" accept="video/mp4,video/mpeg" @change="file = $event"></v-file-input>
         </v-card-text>
         <v-card-actions>
           <v-spacer></v-spacer>
           <v-btn color="error" @click="show = false">Cancel</v-btn>
           <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
         </v-card-actions>
       </v-card>
     </v-dialog>
   </template>
   <script>
   import axios from 'axios';
   export default {
     name: 'PkgModal',
     props: { show: Boolean, episode: String, duplicateSlugs: Array },
     data() { return { slug: '', title: '', duration: '', timestamp: '', file: null }; },
     methods: {
       async submit() {
         const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
         try {
           const formData = new FormData();
           formData.append('type', 'pkg');
           formData.append('slug', normalizedSlug);
           const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           const assetID = response.data.id;
           let mediaURL = '';
           if (this.file) {
             const uploadForm = new FormData();
             uploadForm.append('type', 'pkg');
             uploadForm.append('episode', this.episode);
             uploadForm.append('asset_id', assetID);
             uploadForm.append('file', this.file);
             uploadForm.append('slug', normalizedSlug);
             uploadForm.append('duration', this.duration);
             uploadForm.append('timestamp', this.timestamp || '00:00:00');
             await axios.post('http://192.168.51.210:8888/preproc_pkg', uploadForm, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             mediaURL = `episodes/${this.episode}/assets/video/${normalizedSlug}.${this.file.name.split('.').pop()}`;
           }
           this.$emit('submit', { title: this.title, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
           this.$toast.success('PKG cue added');
           this.reset();
         } catch (error) { this.$toast.error('Failed to add PKG cue'); }
       },
       reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
     },
     watch: { show(val) { if (!val) this.reset(); } }
   }
   </script>
   <style scoped>.v-card { padding: 16px; }</style>
   ```
4. Test:
   - Navigate to `/content-editor/0228`.
   - Open each modal, submit with valid/invalid data, verify API calls (`/next-id`, `/preproc_*`).
   - Check script content updates in `ContentEditor.vue`.
   - Run: `npm run serve` and `curl http://192.168.51.210:8888/health`.

### 2. Virtual Scrolling in `RundownManager.vue`
**Problem**: Missing `<v-virtual-scroll>`, risking performance with large rundowns.
**Fix**:
1. Open `disaffected-ui/src/components/RundownManager.vue`.
2. Replace `rundown-items-container` with:
   ```vue
   <v-virtual-scroll :items="safeRundownItems" :item-height="42" height="600">
     <template v-slot:default="{ item, index }">
       <v-card
         :class="[resolveTypeClass(item.type), 'elevation-1', 'rundown-item-card', 'mb-1', { 'selected-item': selectedItemIndex === index, 'editing-item': editingItemIndex === index }]"
         @click="$emit('select-item', index)"
         @dblclick="$emit('edit-item', index)"
         style="cursor: pointer;"
       >
         <div class="compact-rundown-row" :style="{ color: getTextColorForItem(item?.type || 'unknown') }">
           <div class="index-number">{{ (index + 1) * 10 }}</div>
           <div class="type-label">{{ (item?.type || 'UNKNOWN').toUpperCase() }}</div>
           <div class="slug-text">{{ (item?.slug || '').toLowerCase() }}</div>
           <div v-if="rundownPanelWidth === 'wide'" class="duration-display">{{ formatDuration(item?.duration || '0:00') }}</div>
         </div>
       </v-card>
     </template>
   </v-virtual-scroll>
   ```
3. Test:
   - Load `/rundown/0228` with mock data (>100 items).
   - Verify smooth scrolling in DevTools (Performance tab).
   - Run: `npm run serve`.

### 3. Asset/Template Management
**Problem**: `AssetsView.vue`, `TemplatesView.vue` are placeholders, blocking asset and template workflows.
**Fix**:
1. Create `disaffected-ui/src/views/AssetsView.vue`:
   ```vue
   <template>
     <v-container fluid>
       <v-row>
         <v-col>
           <h2 class="text-h4 font-weight-bold mb-4">Asset Manager</h2>
           <v-file-input label="Upload Asset" accept="image/*,video/*,audio/*" @change="uploadAsset"></v-file-input>
           <v-data-table
             :headers="[{ title: 'File', key: 'filename' }, { title: 'Type', key: 'type' }, { title: 'Actions', key: 'actions' }]"
             :items="assets"
             :loading="loading"
           >
             <template v-slot:item.actions="{ item }">
               <v-btn icon="mdi-delete" size="small" color="error" @click="deleteAsset(item)"></v-btn>
             </template>
           </v-data-table>
         </v-col>
       </v-row>
     </v-container>
   </template>
   <script>
   export default {
     name: 'AssetsView',
     data() { return { assets: [], loading: false }; },
     methods: {
       async uploadAsset(file) {
         if (!file) return;
         this.loading = true;
         try {
           const formData = new FormData();
           formData.append('file', file);
           const response = await this.$axios.post('/api/assets', formData, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           this.assets.push(response.data);
           this.$toast.success('Asset uploaded successfully');
         } catch (error) { this.$toast.error('Failed to upload asset'); }
         this.loading = false;
       },
       async deleteAsset(item) {
         try {
           await this.$axios.delete(`/api/assets/${item.id}`, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           this.assets = this.assets.filter(a => a.id !== item.id);
           this.$toast.success('Asset deleted successfully');
         } catch (error) { this.$toast.error('Failed to delete asset'); }
       },
       async loadAssets() {
         this.loading = true;
         try {
           const response = await this.$axios.get('/api/assets', {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           this.assets = response.data;
         } catch (error) { this.$toast.error('Failed to load assets'); }
         this.loading = false;
       }
     },
     mounted() { this.loadAssets(); }
   }
   </script>
   ```
2. Create `disaffected-ui/src/views/TemplatesView.vue`:
   ```vue
   <template>
     <v-container fluid class="pa-0">
       <v-row class="header-row ma-0">
         <v-col cols="6" class="pa-4">
           <h2 class="text-h4 font-weight-bold">Templates</h2>
         </v-col>
         <v-col cols="6" class="d-flex align-center justify-end pe-4">
           <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">New Template</v-btn>
         </v-col>
       </v-row>
       <v-row class="ma-0">
         <v-col cols="12" class="pa-4">
           <v-card>
             <v-data-table
               :headers="headers"
               :items="templates"
               :loading="loading"
               density="comfortable"
             >
               <template v-slot:item.actions="{ item }">
                 <v-btn icon="mdi-pencil" size="small" variant="text" @click="editTemplate(item)"></v-btn>
                 <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteTemplate(item)"></v-btn>
               </template>
             </v-data-table>
           </v-card>
         </v-col>
       </v-row>
       <v-dialog v-model="showCreateDialog" max-width="500">
         <v-card>
           <v-card-title>Create Template</v-card-title>
           <v-card-text>
             <v-text-field v-model="newTemplate.name" label="Name" required></v-text-field>
             <v-select v-model="newTemplate.type" :items="['segment', 'ad', 'promo', 'cta', 'trans']" label="Type" required></v-select>
             <v-textarea v-model="newTemplate.content" label="Content" rows="4"></v-textarea>
           </v-card-text>
           <v-card-actions>
             <v-spacer></v-spacer>
             <v-btn color="error" @click="showCreateDialog = false">Cancel</v-btn>
             <v-btn color="success" @click="createTemplate" :disabled="!newTemplate.name || !newTemplate.type">Save</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>
     </v-container>
   </template>
   <script>
   export default {
     name: 'TemplatesView',
     data: () => ({
       loading: false,
       showCreateDialog: false,
       newTemplate: { name: '', type: '', content: '' },
       headers: [
         { title: 'Name', key: 'name', sortable: true },
         { title: 'Type', key: 'type', sortable: true },
         { title: 'Last Modified', key: 'modified', sortable: true },
         { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
       ],
       templates: []
     }),
     methods: {
       async createTemplate() {
         this.loading = true;
         try {
           await this.$axios.post('/api/templates', this.newTemplate, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           this.loadTemplates();
           this.showCreateDialog = false;
           this.newTemplate = { name: '', type: '', content: '' };
           this.$toast.success('Template created successfully');
         } catch (error) { this.$toast.error('Failed to create template'); }
         this.loading = false;
       },
       async editTemplate(item) {
         this.loading = true;
         try {
           await this.$axios.put(`/api/templates/${item.id}`, item, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           this.loadTemplates();
           this.$toast.success('Template updated successfully');
         } catch (error) { this.$toast.error('Failed to update template'); }
         this.loading = false;
       },
       async deleteTemplate(item) {
         this.loading = true;
         try {
           await this.$axios.delete(`/api/templates/${item.id}`, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           this.templates = this.templates.filter(t => t.id !== item.id);
           this.$toast.success('Template deleted successfully');
         } catch (error) { this.$toast.error('Failed to delete template'); }
         this.loading = false;
       },
       async loadTemplates() {
         this.loading = true;
         try {
           const response = await this.$axios.get('/api/templates', {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
           });
           this.templates = response.data;
         } catch (error) { this.$toast.error('Failed to load templates'); }
         this.loading = false;
       }
     },
     mounted() { this.loadTemplates(); }
   }
   </script>
   <style scoped>.header-row { background: rgba(0, 0, 0, 0.03); border-bottom: 1px solid rgba(0, 0, 0, 0.05); }</style>
   ```
3. Test:
   - Navigate to `/assets` and `/templates`.
   - Verify upload, CRUD operations, and API calls (`/api/assets`, `/api/templates`).
   - Run: `npm run serve` and `curl http://192.168.51.210:8888/health`.

### 4. Standardize Modal Naming in `ContentEditor.vue`
**Problem**: Inconsistent naming (`showAssetBrowser`, `showGfxModal`, `showGraphicModal`).
**Fix**:
1. Open `disaffected-ui/src/components/ContentEditor.vue`.
2. Replace modal data properties and event handlers:
   ```javascript
   data() {
     return {
       // ... other data
       showAssetBrowserModal: false,
       showTemplateManagerModal: false,
       showGfxModal: false,
       showFsqModal: false,
       showSotModal: false,
       showVoModal: false,
       showNatModal: false,
       showPkgModal: false,
       // ... other data
     };
   }
   ```
3. Update template:
   ```vue
   <EditorPanel
     @show-asset-browser-modal="showAssetBrowserModal = true"
     @show-template-manager-modal="showTemplateManagerModal = true"
     @show-gfx-modal="showGfxModal = true"
     @show-fsq-modal="showFsqModal = true"
     @show-sot-modal="showSotModal = true"
     @show-vo-modal="showVoModal = true"
     @show-nat-modal="showNatModal = true"
     @show-pkg-modal="showPkgModal = true"
     <!-- ... other props -->
   />
   ```
4. Test:
   - Navigate to `/content-editor/0228`.
   - Trigger each modal,





























------------------- filepath: docs/copilot_instructions_7.markdown ----------------------
# Copilot Instructions 7: Finalize Disaffected Production Suite Tasks

## Overview
Copilot, your execution of `copilot_instructions_6.md` via `update.py` addressed most tasks but lacks verification, and future-proofing for new cue types (`VOX`, `MUS`, `LIVE`) was not implemented. As of July 9, 2025 (07:08 AM EDT), 18/19 issues are resolved, but Issue 18 (cue modals), virtual scrolling, asset/template management, and modal naming need confirmation, and new cue types need support. The user will execute the `update.py` script from `/mnt/process/show-build`. This document provides five specific tasks to verify and complete the remaining work, ensuring production-ready status with compatibility for Markdown files, YAML frontmatter, and directory structure at `/mnt/sync/disaffected/episodes/`. No Obsidian plugin implementation exists; `main.js` is for reference only and must be deleted. Documentation updates are reserved for Grok to ensure consistency. Prepare `update.py` with these tasks, using Claude Sonnet 4 and DeepSeek V3 (`python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code`) for validation. All tasks must achieve green checkmarks.

## Clarification on Obsidian and Rules
- **No Obsidian Implementation**: There is no active Obsidian plugin. References to Obsidian in documentation pertain to compatibility with Markdown files, YAML frontmatter, and directory structure. Delete `disaffected-ui/src/main.js` as it’s no longer relevant.
- **Documentation**: Grok exclusively updates `docs/00_rehydration_main.markdown`, `docs/03_features_and_integrations.markdown`, `docs/06_todo_and_issues.markdown`, and `docs/20_changelog.markdown`. Do not include documentation tasks in `update.py`.
- **Rehydration**: Do not update `rehydrate.md` directly; Grok updates `00_rehydration_main.markdown`, which is concatenated into the next `rehydrate.md` iteration via `generate_rehydrate.sh`.
- **Execution**: The user executes `update.py`; Copilot prepares it.

## Critique of Copilot’s Work
- **Successes**:
  - Fixed 18/19 issues (1–7, 9–13, 15–17, 19), including navigation drawer, rundown item types, unit tests, debouncing, episode selection, and authentication.
  - Removed redundant markdown files (`copilot_instructions_2.md`).
  - Implemented unit tests for `ContentEditor.vue` and `RundownManager.vue`.
- **Failures**:
  - Unverified changes for Issue 18 (`VoModal.vue`, `NatModal.vue`, `PkgModal.vue`), virtual scrolling (`RundownManager.vue`), asset/template management (`AssetsView.vue`, `TemplatesView.vue`), and modal naming (`ContentEditor.vue`, `EditorPanel.vue`).
  - No future-proofing for `VOX`, `MUS`, `LIVE` cue types.
- **Impact**: Unverified changes risk workflow disruptions; missing future-proofing limits scalability.

## Status
- **Fully Fixed (18/19)**: Issues 1–7, 9–13, 15–17, 19.
- **Not Fixed/Unverified (1/19)**: Issue 18 (cue modals, pending validation).
- **Tasks for Copilot**:
  1. Verify/complete Issue 18 (cue modals).
  2. Verify/implement virtual scrolling.
  3. Verify/complete asset/template management.
  4. Verify/standardize modal naming.
  5. Future-proof for `VOX`, `MUS`, `LIVE` cue types and delete `main.js`.

## Step-by-Step Instructions
All file paths are relative to `/mnt/process/show-build`. Verify existing files before overwriting, back up changes to `backup_md_20250709`, and validate with DeepSeek V3. Prepare `update.py` for the user to execute, capturing all outputs (stdout, stderr, tracebacks). Do not modify documentation files (`docs/00_rehydration_main.markdown`, `docs/03_features_and_integrations.markdown`, `docs/06_todo_and_issues.markdown`, `docs/20_changelog.markdown`).

### 1. Verify/Complete Issue 18: Implement `VO`, `NAT`, `PKG` Modals
**Problem**: `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` may have been implemented by `update.py` but lack verification. They must include fields and backend integration.
**Fix**:
1. **Verify Modal Files**:
   - **Paths**:
     - `disaffected-ui/src/components/modals/VoModal.vue`
     - `disaffected-ui/src/components/modals/NatModal.vue`
     - `disaffected-ui/src/components/modals/PkgModal.vue`
   - **Action**: Check if files match the code below. If mismatched or missing, rewrite. Ensure:
     - Fields: slug (required), text/description/title (required), duration (required, HH:MM:SS), timestamp (optional, HH:MM:SS), file (optional, `.mp3`/`.wav` for VO/NAT, `.mp4`/`.mpeg` for PKG).
     - Backend integration: `/next-id` for asset ID, `/preproc_vo`, `/preproc_nat`, `/preproc_pkg` for uploads.
     - Error handling with `vue-toastification`.
   - **VoModal.vue**:
     ```vue
     <template>
       <v-dialog v-model="show" max-width="500">
         <v-card>
           <v-card-title>Add Voice Over (VO) Cue</v-card-title>
           <v-card-text>
             <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
             <v-textarea v-model="text" label="Text" required :rules="[v => !!v || 'Text is required']" rows="4"></v-textarea>
             <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
             <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
             <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
           </v-card-text>
           <v-card-actions>
             <v-spacer></v-spacer>
             <v-btn color="error" @click="show = false">Cancel</v-btn>
             <v-btn color="success" @click="submit" :disabled="!slug || !text || !duration">Submit</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>
     </template>
     <script>
     import axios from 'axios';
     export default {
       name: 'VoModal',
       props: { show: Boolean, episode: String, duplicateSlugs: Array },
       data() { return { slug: '', text: '', duration: '', timestamp: '', file: null }; },
       methods: {
         async submit() {
           const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
           try {
             const formData = new FormData();
             formData.append('type', 'vo');
             formData.append('slug', normalizedSlug);
             const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             const assetID = response.data.id;
             let mediaURL = '';
             if (this.file) {
               const uploadForm = new FormData();
               uploadForm.append('type', 'vo');
               uploadForm.append('episode', this.episode);
               uploadForm.append('asset_id', assetID);
               uploadForm.append('file', this.file);
               uploadForm.append('slug', normalizedSlug);
               uploadForm.append('duration', this.duration);
               uploadForm.append('timestamp', this.timestamp || '00:00:00');
               await axios.post('http://192.168.51.210:8888/preproc_vo', uploadForm, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
               mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
             }
             this.$emit('submit', { text: this.text, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
             this.$toast.success('VO cue added');
             this.reset();
           } catch (error) { this.$toast.error('Failed to add VO cue'); }
         },
         reset() { this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
       },
       watch: { show(val) { if (!val) this.reset(); } }
     }
     </script>
     <style scoped>.v-card { padding: 16px; }</style>
     ```
   - **NatModal.vue**:
     ```vue
     <template>
       <v-dialog v-model="show" max-width="500">
         <v-card>
           <v-card-title>Add Natural Sound (NAT) Cue</v-card-title>
           <v-card-text>
             <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
             <v-textarea v-model="description" label="Description" required :rules="[v => !!v || 'Description is required']" rows="4"></v-textarea>
             <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
             <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
             <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
           </v-card-text>
           <v-card-actions>
             <v-spacer></v-spacer>
             <v-btn color="error" @click="show = false">Cancel</v-btn>
             <v-btn color="success" @click="submit" :disabled="!slug || !description || !duration">Submit</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>
     </template>
     <script>
     import axios from 'axios';
     export default {
       name: 'NatModal',
       props: { show: Boolean, episode: String, duplicateSlugs: Array },
       data() { return { slug: '', description: '', duration: '', timestamp: '', file: null }; },
       methods: {
         async submit() {
           const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
           try {
             const formData = new FormData();
             formData.append('type', 'nat');
             formData.append('slug', normalizedSlug);
             const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             const assetID = response.data.id;
             let mediaURL = '';
             if (this.file) {
               const uploadForm = new FormData();
               uploadForm.append('type', 'nat');
               uploadForm.append('episode', this.episode);
               uploadForm.append('asset_id', assetID);
               uploadForm.append('file', this.file);
               uploadForm.append('slug', normalizedSlug);
               uploadForm.append('duration', this.duration);
               uploadForm.append('timestamp', this.timestamp || '00:00:00');
               await axios.post('http://192.168.51.210:8888/preproc_nat', uploadForm, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
               mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
             }
             this.$emit('submit', { description: this.description, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
             this.$toast.success('NAT cue added');
             this.reset();
           } catch (error) { this.$toast.error('Failed to add NAT cue'); }
         },
         reset() { this.slug = ''; this.description = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
       },
       watch: { show(val) { if (!val) this.reset(); } }
     }
     </script>
     <style scoped>.v-card { padding: 16px; }</style>
     ```
   - **PkgModal.vue**:
     ```vue
     <template>
       <v-dialog v-model="show" max-width="500">
         <v-card>
           <v-card-title>Add Package (PKG) Cue</v-card-title>
           <v-card-text>
             <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
             <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
             <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
             <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
             <v-file-input label="Video File (optional)" accept="video/mp4,video/mpeg" @change="file = $event"></v-file-input>
           </v-card-text>
           <v-card-actions>
             <v-spacer></v-spacer>
             <v-btn color="error" @click="show = false">Cancel</v-btn>
             <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
           </v-card-actions>
         </v-card>
       </v-dialog>
     </template>
     <script>
     import axios from 'axios';
     export default {
       name: 'PkgModal',
       props: { show: Boolean, episode: String, duplicateSlugs: Array },
       data() { return { slug: '', title: '', duration: '', timestamp: '', file: null }; },
       methods: {
         async submit() {
           const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
           try {
             const formData = new FormData();
             formData.append('type', 'pkg');
             formData.append('slug', normalizedSlug);
             const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             const assetID = response.data.id;
             let mediaURL = '';
             if (this.file) {
               const uploadForm = new FormData();
               uploadForm.append('type', 'pkg');
               uploadForm.append('episode', this.episode);
               uploadForm.append('asset_id', assetID);
               uploadForm.append('file', this.file);
               uploadForm.append('slug', normalizedSlug);
               uploadForm.append('duration', this.duration);
               uploadForm.append('timestamp', this.timestamp || '00:00:00');
               await axios.post('http://192.168.51.210:8888/preproc_pkg', uploadForm, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
               mediaURL = `episodes/${this.episode}/assets/video/${normalizedSlug}.${this.file.name.split('.').pop()}`;
             }
             this.$emit('submit', { title: this.title, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
             this.$toast.success('PKG cue added');
             this.reset();
           } catch (error) { this.$toast.error('Failed to add PKG cue'); }
         },
         reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
       },
       watch: { show(val) { if (!val) this.reset(); } }
     }
     </script>
     <style scoped>.v-card { padding: 16px; }</style>
     ```
2. **Update ContentEditor.vue**:
   - **Path**: `disaffected-ui/src/components/ContentEditor.vue`
   - **Action**: Ensure modal integration with submit handlers. Add or verify:
     ```javascript
     methods: {
       submitVo(data) {
         this.scriptContent += `[VO: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\n${data.text}\n`;
         this.showVoModal = false;
         this.hasUnsavedChanges = true;
       },
       submitNat(data) {
         this.scriptContent += `[NAT: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\n${data.description}\n`;
         this.showNatModal = false;
         this.hasUnsavedChanges = true;
       },
       submitPkg(data) {
         this.scriptContent += `[PKG: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\n${data.title}\n`;
         this.showPkgModal = false;
         this.hasUnsavedChanges = true;
       }
     }
     ```
3. **Test**:
   - Run `npm run serve` and navigate to `/content-editor/0228`.
   - Trigger `VO`, `NAT`, `PKG` modals, submit valid (e.g., slug: `test-vo`, text: `Test VO`, duration: `00:01:00`) and invalid (e.g., empty slug) data.
   - Verify API calls: `curl -H "Authorization: Bearer $(localStorage.getItem('auth-token'))" http://192.168.51.210:8888/next-id` and `/preproc_vo`, `/preproc_nat`, `/preproc_pkg`.
   - Check script content updates in `ContentEditor.vue` (e.g., `[VO: test-vo | 00:01:00]`).
   - Run `python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code` to validate syntax.

### 2. Verify/Implement Virtual Scrolling in `RundownManager.vue`
**Problem**: `update.py` claimed to add `<v-virtual-scroll>` to `RundownManager.vue`, but it’s unverified, risking performance with large rundowns.
**Fix**:
1. **Verify File**:
   - **Path**: `disaffected-ui/src/components/RundownManager.vue`
   - **Action**: Check for `<v-virtual-scroll>` with `item-height="42"` and `height="600"`. If missing, replace the `rundown-list` div with:
     ```vue
     <v-virtual-scroll :items="safeRundownItems" :item-height="42" height="600">
       <template v-slot:default="{ item, index }">
         <v-card
           :class="[resolveTypeClass(item.type), 'elevation-1', 'rundown-item-card', 'mb-1', { 'selected-item': selectedItemIndex === index, 'editing-item': editingItemIndex === index }]"
           @click="$emit('select-item', index)"
           @dblclick="$emit('edit-item', index)"
           style="cursor: pointer;"
           draggable="true"
           @dragstart="$emit('drag-start', index)"
           @dragover.prevent="$emit('drag-over', index)"
           @drop.prevent="$emit('drag-drop', index)"
         >
           <div class="compact-rundown-row" :style="{ color: getTextColorForItem(item?.type || 'unknown') }">
             <div class="index-number">{{ (index + 1) * 10 }}</div>
             <div class="type-label">{{ (item?.type || 'UNKNOWN').toUpperCase() }}</div>
             <div class="slug-text">{{ (item?.slug || '').toLowerCase() }}</div>
             <div v-if="rundownPanelWidth === 'wide'" class="duration-display">{{ formatDuration(item?.duration || '0:00') }}</div>
           </div>
         </v-card>
       </template>
     </v-virtual-scroll>
     ```
2. **Test**:
   - Run `npm run serve` and load `/rundown/0228` with mock data (>100 items, e.g., via `/api/episodes/0228`).
   - Verify smooth scrolling in DevTools (Performance tab).
   - Test drag-and-drop reordering.
   - Run `npm test` to ensure `RundownManager.spec.js` passes.

### 3. Verify/Complete Asset/Template Management
**Problem**: `AssetsView.vue` and `TemplatesView.vue` were created by `update.py`, but CRUD functionality and API integration need verification.
**Fix**:
1. **Verify AssetsView.vue**:
   - **Path**: `disaffected-ui/src/views/AssetsView.vue`
   - **Action**: Confirm file matches:
     ```vue
     <template>
       <v-container fluid>
         <v-row>
           <v-col>
             <h2 class="text-h4 font-weight-bold mb-4">Asset Manager</h2>
             <v-file-input label="Upload Asset" accept="image/*,video/*,audio/*" @change="uploadAsset"></v-file-input>
             <v-data-table
               :headers="[{ title: 'File', key: 'filename' }, { title: 'Type', key: 'type' }, { title: 'Actions', key: 'actions' }]"
               :items="assets"
               :loading="loading"
             >
               <template v-slot:item.actions="{ item }">
                 <v-btn icon="mdi-delete" size="small" color="error" @click="deleteAsset(item)"></v-btn>
               </template>
             </v-data-table>
           </v-col>
         </v-row>
       </v-container>
     </template>
     <script>
     export default {
       name: 'AssetsView',
       data() { return { assets: [], loading: false }; },
       methods: {
         async uploadAsset(file) {
           if (!file) return;
           this.loading = true;
           try {
             const formData = new FormData();
             formData.append('file', file);
             const response = await this.$axios.post('/api/assets', formData, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.assets.push(response.data);
             this.$toast.success('Asset uploaded successfully');
           } catch (error) { this.$toast.error('Failed to upload asset'); }
           this.loading = false;
         },
         async deleteAsset(item) {
           try {
             await this.$axios.delete(`/api/assets/${item.id}`, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.assets = this.assets.filter(a => a.id !== item.id);
             this.$toast.success('Asset deleted successfully');
           } catch (error) { this.$toast.error('Failed to delete asset'); }
         },
         async loadAssets() {
           this.loading = true;
           try {
             const response = await this.$axios.get('/api/assets', {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.assets = response.data;
           } catch (error) { this.$toast.error('Failed to load assets'); }
           this.loading = false;
         }
       },
       mounted() { this.loadAssets(); }
     }
     </script>
     ```
2. **Verify TemplatesView.vue**:
   - **Path**: `disaffected-ui/src/views/TemplatesView.vue`
   - **Action**: Confirm file matches:
     ```vue
     <template>
       <v-container fluid class="pa-0">
         <v-row class="header-row ma-0">
           <v-col cols="6" class="pa-4">
             <h2 class="text-h4 font-weight-bold">Templates</h2>
           </v-col>
           <v-col cols="6" class="d-flex align-center justify-end pe-4">
             <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">New Template</v-btn>
           </v-col>
         </v-row>
         <v-row class="ma-0">
           <v-col cols="12" class="pa-4">
             <v-card>
               <v-data-table
                 :headers="headers"
                 :items="templates"
                 :loading="loading"
                 density="comfortable"
               >
                 <template v-slot:item.actions="{ item }">
                   <v-btn icon="mdi-pencil" size="small" variant="text" @click="editTemplate(item)"></v-btn>
                   <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteTemplate(item)"></v-btn>
                 </template>
               </v-data-table>
             </v-col>
         </v-row>
         <v-dialog v-model="showCreateDialog" max-width="500">
           <v-card>
             <v-card-title>Create Template</v-card-title>
             <v-card-text>
               <v-text-field v-model="newTemplate.name" label="Name" required></v-text-field>
               <v-select v-model="newTemplate.type" :items="['segment', 'ad', 'promo', 'cta', 'trans']" label="Type" required></v-select>
               <v-textarea v-model="newTemplate.content" label="Content" rows="4"></v-textarea>
             </v-card-text>
             <v-card-actions>
               <v-spacer></v-spacer>
               <v-btn color="error" @click="showCreateDialog = false">Cancel</v-btn>
               <v-btn color="success" @click="createTemplate" :disabled="!newTemplate.name || !newTemplate.type">Save</v-btn>
             </v-card-actions>
           </v-card>
         </v-dialog>
       </v-container>
     </template>
     <script>
     export default {
       name: 'TemplatesView',
       data() { return {
         loading: false,
         showCreateDialog: false,
         newTemplate: { name: '', type: '', content: '' },
         headers: [
           { title: 'Name', key: 'name', sortable: true },
           { title: 'Type', key: 'type', sortable: true },
           { title: 'Last Modified', key: 'modified', sortable: true },
           { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
         ],
         templates: []
       }},
       methods: {
         async createTemplate() {
           this.loading = true;
           try {
             await this.$axios.post('/api/templates', this.newTemplate, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.loadTemplates();
             this.showCreateDialog = false;
             this.newTemplate = { name: '', type: '', content: '' };
             this.$toast.success('Template created successfully');
           } catch (error) { this.$toast.error('Failed to create template'); }
           this.loading = false;
         },
         async editTemplate(item) {
           this.loading = true;
           try {
             await this.$axios.put(`/api/templates/${item.id}`, item, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.loadTemplates();
             this.$toast.success('Template updated successfully');
           } catch (error) { this.$toast.error('Failed to update template'); }
           this.loading = false;
         },
         async deleteTemplate(item) {
           this.loading = true;
           try {
             await this.$axios.delete(`/api/templates/${item.id}`, {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.templates = this.templates.filter(t => t.id !== item.id);
             this.$toast.success('Template deleted successfully');
           } catch (error) { this.$toast.error('Failed to delete template'); }
           this.loading = false;
         },
         async loadTemplates() {
           this.loading = true;
           try {
             const response = await this.$axios.get('/api/templates', {
               headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
             });
             this.templates = response.data;
           } catch (error) { this.$toast.error('Failed to load templates'); }
           this.loading = false;
         }
       },
       mounted() { this.loadTemplates(); }
     }
     </script>
     <style scoped>.header-row { background: rgba(0, 0, 0, 0.03); border-bottom: 1px solid rgba(0, 0, 0, 0.05); }</style>
     ```
3. **Test**:
   - Run `npm run serve` and navigate to `/assets` and `/templates`.
   - Test upload, create, edit, delete operations.
   - Verify API calls: `curl -H "Authorization: Bearer $(localStorage.getItem('auth-token'))" http://192.168.51.210:8888/api/assets` and `/api/templates`.
   - Run `python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code` to validate syntax.

### 4. Verify/Standardize Modal Naming in `ContentEditor.vue` and `EditorPanel.vue`
**Problem**: `update.py` updated modal naming, but consistency (e.g., `showGraphicModal` vs. `showGfxModal`) is unverified.
**Fix**:
1. **Verify ContentEditor.vue**:
   - **Path**: `disaffected-ui/src/components/ContentEditor.vue`
   - **Action**: Confirm the following in the `<template>` section:
     ```vue
     <EditorPanel
       @show-asset-modal="showAssetModal = true"
       @show-template-modal="showTemplateModal = true"
       @show-gfx-modal="showGfxModal = true"
       @show-fsq-modal="showFsqModal = true"
       @show-sot-modal="showSotModal = true"
       @show-vo-modal="showVoModal = true"
       @show-nat-modal="showNatModal = true"
       @show-pkg-modal="showPkgModal = true"
       <!-- ... other props -->
     />
     <AssetModal
       :visible="showAssetModal"
       @update:visible="showAssetModal = $event"
       @asset-selected="insertAssetReference"
     />
     <TemplateModal
       :visible="showTemplateModal"
       @update:visible="showTemplateModal = $event"
       @template-selected="insertTemplateReference"
     />
     <GfxModal v-model:show="showGfxModal" @submit="submitGfx" />
     <FsqModal v-model:show="showFsqModal" @submit="submitFsq" />
     <SotModal v-model:show="showSotModal" @submit="submitSot" />
     <VoModal v-model:show="showVoModal" @submit="submitVo" />
     <NatModal v-model:show="showNatModal" @submit="submitNat" />
     <PkgModal v-model:show="showPkgModal" @submit="submitPkg" />
     ```
   - Confirm `data()` includes:
     ```javascript
     data() {
       return {
         showAssetModal: false,
         showTemplateModal: false,
         showGfxModal: false,
         showFsqModal: false,
         showSotModal: false,
         showVoModal: false,
         showNatModal: false,
         showPkgModal: false,
         // ... other data
       };
     }
     ```
   - If incorrect, replace `showAssetBrowserModal` → `showAssetModal`, `showTemplateManagerModal` → `showTemplateModal`, `showGraphicModal` → `showGfxModal`.
2. **Verify EditorPanel.vue**:
   - **Path**: `disaffected-ui/src/components/EditorPanel.vue`
   - **Action**: Confirm the `<template>` section matches:
     ```vue
     <template>
       <div class="editor-panel">
         <v-toolbar dense flat class="editor-toolbar">
           <v-btn icon @click="$emit('toggle-rundown-panel')">
             <v-icon>{{ showRundownPanel ? 'mdi-chevron-left' : 'mdi-chevron-right' }}</v-icon>
           </v-btn>
           <v-btn text @click="save">Save</v-btn>
           <v-btn text @click="$emit('show-asset-modal')">Add Asset</v-btn>
           <v-btn text @click="$emit('show-template-modal')">Add Template</v-btn>
           <v-btn text @click="$emit('show-gfx-modal')">Add GFX</v-btn>
           <v-btn text @click="$emit('show-fsq-modal')">Add FSQ</v-btn>
           <v-btn text @click="$emit('show-sot-modal')">Add SOT</v-btn>
           <v-btn text @click="$emit('show-vo-modal')">Add VO</v-btn>
           <v-btn text @click="$emit('show-nat-modal')">Add NAT</v-btn>
           <v-btn text @click="$emit('show-pkg-modal')">Add PKG</v-btn>
           <v-select
             v-model="editorMode"
             :items="['script', 'scratch', 'metadata', 'code']"
             label="Mode"
             dense
           ></v-select>
         </v-toolbar>
         <v-textarea
           v-model="scriptContent"
           @input="$emit('content-change', $event)"
           :placeholder="editorMode === 'script' ? scriptPlaceholder : scratchPlaceholder"
           rows="20"
         ></v-textarea>
       </div>
     </template>
     ```
3. **Test**:
   - Run `npm run serve` and navigate to `/content-editor/0228`.
   - Trigger each modal and verify correct display and functionality.
   - Run `npm test` to ensure `ContentEditor.spec.js` passes.

### 5. Future-Proof Cue Types and Delete `main.js`
**Problem**: The system lacks support for new cue types (`VOX`, `MUS`, `LIVE`), limiting scalability, and `main.js` is no longer relevant.
**Fix**:
1. **Create Placeholder Modals**:
   - **Paths**:
     - `disaffected-ui/src/components/modals/VoxModal.vue`
     - `disaffected-ui/src/components/modals/MusModal.vue`
     - `disaffected-ui/src/components/modals/LiveModal.vue`
   - **Action**: Create or update:
     - **VoxModal.vue**:
       ```vue
       <template>
         <v-dialog v-model="show" max-width="500">
           <v-card>
             <v-card-title>Add Vox Pop (VOX) Cue</v-card-title>
             <v-card-text>
               <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
               <v-textarea v-model="text" label="Text" required :rules="[v => !!v || 'Text is required']" rows="4"></v-textarea>
               <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
               <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
               <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
             </v-card-text>
             <v-card-actions>
               <v-spacer></v-spacer>
               <v-btn color="error" @click="show = false">Cancel</v-btn>
               <v-btn color="success" @click="submit" :disabled="!slug || !text || !duration">Submit</v-btn>
             </v-card-actions>
           </v-card>
         </v-dialog>
       </template>
       <script>
       import axios from 'axios';
       export default {
         name: 'VoxModal',
         props: { show: Boolean, episode: String, duplicateSlugs: Array },
         data() { return { slug: '', text: '', duration: '', timestamp: '', file: null }; },
         methods: {
           async submit() {
             const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
             try {
               const formData = new FormData();
               formData.append('type', 'vox');
               formData.append('slug', normalizedSlug);
               const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
               const assetID = response.data.id;
               let mediaURL = '';
               if (this.file) {
                 const uploadForm = new FormData();
                 uploadForm.append('type', 'vox');
                 uploadForm.append('episode', this.episode);
                 uploadForm.append('asset_id', assetID);
                 uploadForm.append('file', this.file);
                 uploadForm.append('slug', normalizedSlug);
                 uploadForm.append('duration', this.duration);
                 uploadForm.append('timestamp', this.timestamp || '00:00:00');
                 await axios.post('http://192.168.51.210:8888/preproc_vox', uploadForm, {
                   headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
                 });
                 mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
               }
               this.$emit('submit', { text: this.text, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
               this.$toast.success('VOX cue added');
               this.reset();
             } catch (error) { this.$toast.error('Failed to add VOX cue'); }
           },
           reset() { this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
         },
         watch: { show(val) { if (!val) this.reset(); } }
       }
       </script>
       <style scoped>.v-card { padding: 16px; }</style>
       ```
     - **MusModal.vue**:
       ```vue
       <template>
         <v-dialog v-model="show" max-width="500">
           <v-card>
             <v-card-title>Add Music (MUS) Cue</v-card-title>
             <v-card-text>
               <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
               <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
               <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
               <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
               <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
             </v-card-text>
             <v-card-actions>
               <v-spacer></v-spacer>
               <v-btn color="error" @click="show = false">Cancel</v-btn>
               <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
             </v-card-actions>
           </v-card>
         </v-dialog>
       </template>
       <script>
       import axios from 'axios';
       export default {
         name: 'MusModal',
         props: { show: Boolean, episode: String, duplicateSlugs: Array },
         data() { return { slug: '', title: '', duration: '', timestamp: '', file: null }; },
         methods: {
           async submit() {
             const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
             try {
               const formData = new FormData();
               formData.append('type', 'mus');
               formData.append('slug', normalizedSlug);
               const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
               const assetID = response.data.id;
               let mediaURL = '';
               if (this.file) {
                 const uploadForm = new FormData();
                 uploadForm.append('type', 'mus');
                 uploadForm.append('episode', this.episode);
                 uploadForm.append('asset_id', assetID);
                 uploadForm.append('file', this.file);
                 uploadForm.append('slug', normalizedSlug);
                 uploadForm.append('duration', this.duration);
                 uploadForm.append('timestamp', this.timestamp || '00:00:00');
                 await axios.post('http://192.168.51.210:8888/preproc_mus', uploadForm, {
                   headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
                 });
                 mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
               }
               this.$emit('submit', { title: this.title, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
               this.$toast.success('MUS cue added');
               this.reset();
             } catch (error) { this.$toast.error('Failed to add MUS cue'); }
           },
           reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
         },
         watch: { show(val) { if (!val) this.reset(); } }
       }
       </script>
       <style scoped>.v-card { padding: 16px; }</style>
       ```
     - **LiveModal.vue**:
       ```vue
       <template>
         <v-dialog v-model="show" max-width="500">
           <v-card>
             <v-card-title>Add Live (LIVE) Cue</v-card-title>
             <v-card-text>
               <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
               <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
               <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
               <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
             </v-card-text>
             <v-card-actions>
               <v-spacer></v-spacer>
               <v-btn color="error" @click="show = false">Cancel</v-btn>
               <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
             </v-card-actions>
           </v-card>
         </v-dialog>
       </template>
       <script>
       import axios from 'axios';
       export default {
         name: 'LiveModal',
         props: { show: Boolean, episode: String, duplicateSlugs: Array },
         data() { return { slug: '', title: '', duration: '', timestamp: '' }; },
         methods: {
           async submit() {
             const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
             try {
               const formData = new FormData();
               formData.append('type', 'live');
               formData.append('slug', normalizedSlug);
               const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
                 headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
               });
               const assetID = response.data.id;
               this.$emit('submit', { title: this.title, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID });
               this.$toast.success('LIVE cue added');
               this.reset();
             } catch (error) { this.$toast.error('Failed to add LIVE cue'); }
           },
           reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.show = false; }
         },
         watch: { show(val) { if (!val) this.reset(); } }
       }
       </script>
       <style scoped>.v-card { padding: 16px; }</style>
       ```
2. **Update ContentEditor.vue**:
   - **Path**: `disaffected-ui/src/components/ContentEditor.vue`
   - **Action**: Add support for new modals:
     ```vue
     <!-- Add to <template> -->
     <VoxModal v-model:show="showVoxModal" @submit="submitVox" />
     <MusModal v-model:show="showMusModal" @submit="submitMus" />
     <LiveModal v-model:show="showLiveModal" @submit="submitLive" />
     ```
     ```javascript
     // Add to data()
     showVoxModal: false,
     showMusModal: false,
     showLiveModal: false,
     ```
     ```javascript
     // Add to methods
     submitVox(data) {
       this.scriptContent += `[VOX: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\n${data.text}\n`;
       this.showVoxModal = false;
       this.hasUnsavedChanges = true;
     },
     submitMus(data) {
       this.scriptContent += `[MUS: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\n${data.title}\n`;
       this.showMusModal = false;
       this.hasUnsavedChanges = true;
     },
     submitLive(data) {
       this.scriptContent += `[LIVE: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]\n${data.title}\n`;
       this.showLiveModal = false;
       this.hasUnsavedChanges = true;
     }
     ```
3. **Update EditorPanel.vue**:
   - **Path**: `disaffected-ui/src/components/EditorPanel.vue`
   - **Action**: Add buttons for new modals:
     ```vue
     <v-btn text @click="$emit('show-vox-modal')">Add VOX</v-btn>
     <v-btn text @click="$emit('show-mus-modal')">Add MUS</v-btn>
     <v-btn text @click="$emit('show-live-modal')">Add LIVE</v-btn>
     ```
4. **Delete main.js**:
   - **Path**: `disaffected-ui/src/main.js`
   - **Action**: Delete the file if it exists.
5. **Test**:
   - Run `npm run serve` and navigate to `/content-editor/0228`.
   - Trigger `VOX`, `MUS`, `LIVE` modals, verify placeholders work (submit disabled if backend endpoints `/preproc_vox`, `/preproc_mus`, `/preproc_live` are unavailable).
   - Verify `main.js` is deleted: `ls disaffected-ui/src/main.js` should return no file.
   - Run `python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code` to validate syntax.

### Validation Instructions
- **DeepSeek V3**: Run `python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code` to validate all code changes.
- **Unit Tests**: Run `npm test` to verify `ContentEditor.spec.js` and `RundownManager.spec.js`.
- **Manual Tests**:
  - Frontend: `curl http://192.168.51.210:8080/`
  - Backend: `curl http://192.168.51.210:8888/health`
  - Modals: Navigate to `/content-editor/0228`, trigger `VO`, `NAT`, `PKG`, `VOX`, `MUS`, `LIVE` modals, verify script updates.
  - Performance: Load `/rundown/0228` with >100 items, check scrolling in DevTools (Performance tab).
  - Assets/Templates: Test CRUD at `/assets` and `/templates`.
- **API Tests**:
  - `curl -H "Authorization: Bearer $(localStorage.getItem('auth-token'))" http://192.168.51.210:8888/api/assets`
  - `curl -H "Authorization: Bearer $(localStorage.getItem('auth-token'))" http://192.168.51.210:8888/api/templates`
  - `curl -H "Authorization: Bearer $(localStorage.getItem('auth-token'))" http://192.168.51.210:8888/api/episodes/0228/cues`

*Last Updated: July 9, 2025*





























---------------------- tree structure for reference -----------------
.
├── app
│   ├── api_config.py
│   ├── api_config_router.py
│   ├── app
│   │   └── storage
│   ├── assets_router.py
│   ├── auth
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── __pycache__
│   │   ├── router.py
│   │   └── utils.py
│   ├── __init__.py
│   ├── logs
│   │   └── last.id
│   ├── main.py
│   ├── mqttcurl.sh
│   ├── preproc_delegate.py
│   ├── preproc_mqtt_listen.py
│   ├── preproc_mqtt_pub.py
│   ├── preproc-queue-sots.json
│   ├── __pycache__
│   │   ├── api_config.cpython-310.pyc
│   │   ├── api_config_router.cpython-310.pyc
│   │   ├── main.cpython-310.pyc
│   │   ├── preproc_mqtt_listen.cpython-310.pyc
│   │   └── preproc_mqtt_pub.cpython-310.pyc
│   ├── requirements.txt
│   ├── services
│   │   ├── agentIO.py
│   │   ├── sot_processor.py
│   │   └── testboot.mqtt.py
│   ├── storage
│   │   ├── api_keys.json
│   │   ├── templates
│   │   └── users.json
│   ├── templates_router.py
│   ├── testup.sh
│   └── utils
│       ├── curl-test.sh
│       ├── frontmatter_parser.py
│       ├── id.py
│       ├── __pycache__
│       └── validator.py
├── backup_md_20250708_112337
│   ├── copilot
│   │   ├── docs
│   │   ├── imported
│   │   └── workload.md
│   ├── disaffected-ui
│   │   ├── docs
│   │   ├── STUBS_TODO.md
│   │   └── stuff to do.md
│   └── docs
│       ├── copilot_color_transition_instructions.markdown
│       ├── copilot_instructions.markdown
│       └── rundown_item_types.markdown
├── backup_md_20250708_114505
├── backup_md_20250709
│   ├── grok.sh.20250709_021309
│   ├── NatModal.vue.20250709_031517
│   ├── NatModal.vue.20250709_071457
│   ├── NatModal.vue.20250709_125141
│   ├── NatModal.vue.20250709_131345
│   ├── PkgModal.vue.20250709_031517
│   ├── PkgModal.vue.20250709_071457
│   ├── PkgModal.vue.20250709_125141
│   ├── PkgModal.vue.20250709_131345
│   ├── RundownManager.vue.20250709_031517
│   ├── RundownManager.vue.20250709_071457
│   ├── RundownManager.vue.20250709_125141
│   ├── VoModal.vue.20250709_012726
│   ├── VoModal.vue.20250709_013528
│   ├── VoModal.vue.20250709_013547
│   ├── VoModal.vue.20250709_013708
│   ├── VoModal.vue.20250709_015204
│   ├── VoModal.vue.20250709_015342
│   ├── VoModal.vue.20250709_015835
│   ├── VoModal.vue.20250709_020319
│   ├── VoModal.vue.20250709_021029
│   ├── VoModal.vue.20250709_021312
│   ├── VoModal.vue.20250709_031517
│   ├── VoModal.vue.20250709_071457
│   ├── VoModal.vue.20250709_125141
│   └── VoModal.vue.20250709_131345
├── CLAUDE.md
├── create_users.py
├── debug_bcrypt.py
├── disaffected-ui
│   ├── babel.config.js
│   ├── cat_stuff.sh
│   ├── dist
│   │   ├── css
│   │   ├── favicon.ico
│   │   ├── fonts
│   │   ├── index.html
│   │   └── js
│   ├── docs
│   ├── jest.config.js
│   ├── jsconfig.json
│   ├── package.json
│   ├── package-lock.json
│   ├── public
│   │   ├── css
│   │   ├── favicon.ico
│   │   ├── fonts
│   │   ├── index.html
│   │   └── js
│   ├── simple-server.js
│   ├── src
│   │   ├── App.vue
│   │   ├── assets
│   │   ├── components
│   │   ├── composables
│   │   ├── config.js
│   │   ├── main.js
│   │   ├── modules
│   │   ├── modulesauth
│   │   ├── plugins
│   │   ├── router
│   │   ├── stores
│   │   ├── utils
│   │   └── views
│   ├── tests
│   │   ├── mocks
│   │   ├── setup.js
│   │   └── unit
│   ├── vite.config.js.backup
│   └── vue.config.js
├── docker-compose.yml
├── Dockerfile
├── docs
│   ├── 00_rehydration_main.markdown
│   ├── 01_architecture.markdown
│   ├── 02_setup_and_deployment.markdown
│   ├── 03_features_and_integrations.markdown
│   ├── 04_migration_and_workflow.markdown
│   ├── 05_style_guide.markdown
│   ├── 06_todo_and_issues.markdown
│   ├── 19_documentation_updates.markdown
│   ├── 20_changelog.markdown
│   ├── AUTHENTICATION_GUIDE.md
│   ├── ColorSelector.md
│   ├── copilot_instructions_2.markdown
│   ├── copilot_instructions_3.markdown
│   ├── copilot_instructions_4.markdown
│   ├── copilot_instructions_5.markdown
│   ├── copilot_instructions_6.markdown
│   ├── copilot_instructions_7.markdown
│   ├── COPILOT_WORKFLOW_NOTES.md
│   ├── llm
│   │   └── intro.txt
│   ├── MODAL_USAGE.md
│   ├── PROJECT_ARCHITECTURE_REPORT.md
│   ├── rehydrate.md
│   ├── Stuff to do.md
│   └── STYLE_GUIDE.md
├── find-asset-id-refs.sh
├── fix_auth.py
├── fix_bcrypt_hashes.py
├── force_restart.sh
├── generate_hashes.py
├── generate_rehydrate.sh
├── grok.sh
├── package.json
├── package-lock.json
├── README.md
├── requirements.txt
├── reset_users.py
├── restart-dockers.sh
├── restore_working_hashes.py
├── review_files.txt
├── secret.key
├── temp_hash_gen.py
├── test_api_auth.ps1
├── test_api_auth.sh
├── test_auth_direct.py
├── test_auth.py
├── test_auth_system.py
├── test_login.py
├── test_storage.py
├── tools
│   ├── compile-script-dev.py
│   ├── convert-vmix-drive-letter.py
│   ├── datafiles
│   │   ├── disaffected-montpelier_converted.vmix
│   │   └── disaffected-montpelier.vmix
│   ├── media_job_queue.py
│   ├── mosquitto.conf
│   ├── paths.py
│   ├── __pycache__
│   │   └── paths.cpython-310.pyc
│   ├── README.md
│   └── update.py
├── tree_output.txt
├── update.py
├── update.sh
├── verify_auth.py
├── verify_setup.py
└── workload.json

50 directories, 150 files
