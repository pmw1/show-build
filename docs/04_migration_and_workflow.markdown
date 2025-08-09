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