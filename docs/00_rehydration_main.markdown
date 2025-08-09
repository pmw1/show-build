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