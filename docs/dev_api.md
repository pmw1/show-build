# API & Integration

API documentation, integration patterns, and change history.

---

## From: 19_documentation_updates.markdown

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
---

## From: 20_changelog.markdown

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

---

