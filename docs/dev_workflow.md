# Development Workflow

Development practices, coding standards, migration strategies, and style guides.

---

## From: 04_migration_and_workflow.markdown

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
---

## From: 05_style_guide.markdown

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
---

## From: STYLE_GUIDE.md


---

