# Show-Build Documentation Index

## Quick Start
- [`CLAUDE.md`](../CLAUDE.md) - Main documentation for Claude Code
- [`DEBUG_FIRST.md`](../DEBUG_FIRST.md) - **START HERE** for any frontend issue
- [`README.md`](../README.md) - Project overview and setup

---

## Debugging & Troubleshooting

### Frontend Debugging
- **[`DEBUG_FIRST.md`](../DEBUG_FIRST.md)** ⭐ **READ THIS FIRST** - Catches 99% of issues
- [`DEBUGGING_STANDARDS.md`](DEBUGGING_STANDARDS.md) - Systematic debugging checklist
- [`VUE_TEMPLATE_REF_CONFLICTS.md`](VUE_TEMPLATE_REF_CONFLICTS.md) - Template ref naming conflicts (causes 80% of Vue issues)
- [`VUE_APP_MOUNTING_WARNING.md`](VUE_APP_MOUNTING_WARNING.md) - Duplicate Vue app instances

### Feature-Specific Debugging
- **[`LLM_GENERATOR_TROUBLESHOOTING.md`](LLM_GENERATOR_TROUBLESHOOTING.md)** - LLM test segment generator (Ctrl+Alt+Shift+3)
  - Authentication issues
  - Timeout errors
  - Mixed content blocking
  - Text not displaying
  - ⚠️ **Note**: Uses legacy patterns, see [`UNIVERSAL_LLM_FRAMEWORK_UFDP.md`](../UNIVERSAL_LLM_FRAMEWORK_UFDP.md) for new approach

---

## System Guides

### Core Systems
- **[`UNIVERSAL_LLM_FRAMEWORK_UFDP.md`](../UNIVERSAL_LLM_FRAMEWORK_UFDP.md)** ⭐ **Universal LLM Framework** - Unified AI state management (v1.0)
  - Visual feedback system (54 scope/state combinations)
  - Database-backed persistence
  - Notification center
  - Replaces fragmented `aiState`, `generatingItemIndex` patterns
- [`ASSETID_SYSTEM_GUIDE.md`](ASSETID_SYSTEM_GUIDE.md) - AssetID generation, conversion, scanning
- [`RBAC_AUTHENTICATION_GUIDE.md`](RBAC_AUTHENTICATION_GUIDE.md) - Role-based access control & authentication
- [`TEST_DATA_MANAGEMENT.md`](TEST_DATA_MANAGEMENT.md) - Test data vs production data separation

### Feature Guides
- **[`DASHBOARD_ARCHITECTURE.md`](DASHBOARD_ARCHITECTURE.md)** - Dashboard zones & readiness (**read before adding a dashboard panel**)
  - Three fixed zones (Tonight / Pipeline / System), drag scoped per zone
  - `/readiness` per-stage aggregation behind the on-air rail
  - Tally-light semantics and the async-prop gotcha
- [`CUE_BLOCK_INSERTION_PROTOCOL.md`](CUE_BLOCK_INSERTION_PROTOCOL.md) - Cue insertion UX (implemented)
- [`HEALTH_CHECK_PROGRESSIVE_LOADING.md`](HEALTH_CHECK_PROGRESSIVE_LOADING.md) - Progressive health check system (implemented)
  - Includes per-queue Celery consumer coverage (`uncovered_queues`)
- **[`PROMPT_OVERRIDE_SYSTEM.md`](PROMPT_OVERRIDE_SYSTEM.md)** - LLM Prompt Override System
  - Customize LLM prompts without modifying code
  - Database-backed override management
  - Template variable substitution
  - LLM route override (service/model selection)
  - Web UI for prompt management
- [`PROMPT_OVERRIDE_INTEGRATION_GUIDE.md`](PROMPT_OVERRIDE_INTEGRATION_GUIDE.md) - Integrating prompt overrides into code

---

## Training & Research

### Model Training & Research (archived)
- See `docs/archived/` for: VOICE_MODEL_TRAINING_GUIDE, FINE_TUNE_GROK_SASS_GUIDE, GROK_QUANTIZATION_QUALITY_COMPARISON, IQ_QUANTIZATION_RESEARCH, WPM_AUDIO_ANALYSIS_TODO

---

## Architecture & Status

- [`SHOW_BUILD_STATUS_UFDP.md`](../SHOW_BUILD_STATUS_UFDP.md) - Universal Functional Design Pattern status
  - System architecture
  - Database-first approach
  - Implementation status

### Media storage
- **[`EPISODE_DIRECTORY_STANDARD.md`](EPISODE_DIRECTORY_STANDARD.md)** - Per-episode asset tree (authoritative)
- **[`MEDIA_POOL_STANDARD.md`](MEDIA_POOL_STANDARD.md)** - Unbound media pool: `media_assets/pool/{episodes,ads,repo,whiteboard}` (authoritative)
  - Cue-release + whiteboard media; flat per-episode layout
  - `ShowBuildPaths.get_pool_*` helpers; `/pool` static mount; `POOL` AssetID prefix

---

## Common Issues Quick Reference

| Issue | Document | Section |
|-------|----------|---------|
| Form values reset mysteriously | `VUE_TEMPLATE_REF_CONFLICTS.md` | Template Ref Conflicts |
| LLM generator times out | `LLM_GENERATOR_TROUBLESHOOTING.md` | Issue 2: 504 Gateway Timeout |
| "No LLM service enabled" | `LLM_GENERATOR_TROUBLESHOOTING.md` | Issue 1: No LLM Service |
| Logout loop on 401 errors | `LLM_GENERATOR_TROUBLESHOOTING.md` | Issue 4: Authentication Logout Loop |
| Mixed content blocked | `LLM_GENERATOR_TROUBLESHOOTING.md` | Issue 3: Mixed Content Blocking |
| Generated text not showing | `LLM_GENERATOR_TROUBLESHOOTING.md` | Issue 5: Text Not Displaying |
| Frontend unexplainable errors | `DEBUG_FIRST.md` | Quick Debug Command |
| API connectivity issues | `DEBUG_FIRST.md` | 99% of Frontend Issues |
| Vue mounting problems | `VUE_APP_MOUNTING_WARNING.md` | Duplicate App Instances |
| Reactivity breaks without cause | `VUE_TEMPLATE_REF_CONFLICTS.md` | Symptoms |
| Customize LLM prompts | `PROMPT_OVERRIDE_SYSTEM.md` | Creating Overrides |
| Override not working | `PROMPT_OVERRIDE_SYSTEM.md` | Troubleshooting |
| Route LLM to specific model | `PROMPT_OVERRIDE_SYSTEM.md` | LLM Route Override |

---

## Debug Command Quick Reference

```bash
# Frontend quick debug (catches 99% of issues)
./scripts/debug-frontend.sh

# Backend logs
docker logs show-build-server 2>&1 | tail -50

# Database query
docker exec show-build-postgres psql -U showbuild -d showbuild -c "SELECT ..."

# Ollama connectivity
curl -s http://192.168.51.197:11434/api/tags | jq '.models[].name'

# LLM proxy requests
docker logs show-build-server 2>&1 | grep "Proxying Ollama" | tail -10

# Authentication errors
docker logs show-build-server 2>&1 | grep "401\|JWT" | tail -20
```

---

## Keyboard Shortcuts Reference

| Shortcut | Action | File Location |
|----------|--------|---------------|
| `Ctrl+Alt+Shift+[1-9]` | Generate test segment (LLM) | `ContentEditor.vue:2309` |
| `Ctrl+S` | Save current item | `ContentEditor.vue` |
| `Delete` | Delete selected rundown item | `ContentEditor.vue` |
| Various cue shortcuts | Insert cue blocks | See `CUE_BLOCK_INSERTION_PROTOCOL.md` |

---

## File Structure Reference

```
show-build/
├── CLAUDE.md                    # Main Claude Code instructions
├── DEBUG_FIRST.md              # ⭐ Start here for debugging
├── README.md                   # Project overview
├── SHOW_BUILD_STATUS_UFDP.md  # System architecture & status
│
├── docs/
│   ├── INDEX.md                           # This file
│   ├── ASSETID_SYSTEM_GUIDE.md           # AssetID system
│   ├── DEBUGGING_STANDARDS.md            # Debugging checklist
│   ├── LLM_GENERATOR_TROUBLESHOOTING.md # ⭐ LLM generator debugging
│   ├── RBAC_AUTHENTICATION_GUIDE.md      # Authentication & RBAC
│   ├── TEST_DATA_MANAGEMENT.md           # Test data handling
│   ├── PROMPT_OVERRIDE_SYSTEM.md         # ⭐ LLM prompt override system
│   ├── PROMPT_OVERRIDE_INTEGRATION_GUIDE.md # Prompt override integration
│   ├── VUE_TEMPLATE_REF_CONFLICTS.md     # Vue reactivity issues
│   ├── VUE_APP_MOUNTING_WARNING.md       # Vue mounting issues
│   ├── CUE_BLOCK_INSERTION_PROTOCOL.md   # Cue insertion UX
│   ├── HEALTH_CHECK_PROGRESSIVE_LOADING.md # Health check system
│   ├── archived/                          # Deprecated docs (migrations, research, stubs)
│   └── [quantization guides]
│
├── app/                        # FastAPI backend
│   ├── main.py                # App entry (~238 lines): middleware, static mounts, router registration
│   ├── models/                # Domain-split SQLAlchemy models (enums, organization, episode, etc.)
│   ├── routers/               # Modularized router packages
│   │   ├── episodes/          # 8 sub-routers (crud, metadata, rundown, versioning, etc.)
│   │   ├── settings/          # 5 sub-routers (general, media_paths, interface, etc.)
│   │   ├── whiteboard/        # 4 sub-routers (crud, media, social_media, node_links)
│   │   ├── health_router.py   # Health check endpoints
│   │   ├── upload_router.py   # File upload endpoints
│   │   ├── legacy_router.py   # File-based legacy endpoints
│   │   └── misc_router.py     # Miscellaneous endpoints
│   ├── services/              # Business logic (rbac, housekeeping, asterisk, link_preview, etc.)
│   ├── llm_proxy_router.py    # LLM proxy endpoint
│   ├── prompts_router.py      # Prompt override API
│   ├── auth/                  # Authentication system
│   └── ...
│
├── disaffected-ui/            # Vue 3 frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ContentEditor.vue  # Main editor component
│   │   │   └── PromptManager.vue  # Prompt override UI
│   │   ├── composables/
│   │   │   ├── useLLM.js         # LLM integration
│   │   │   └── useLLMPrompts.js  # Prompt override composable
│   │   └── ...
│   └── public/
│       └── index.html            # HTTPS redirect
│
└── scripts/
    └── debug-frontend.sh         # Frontend debug tool
```

---

## Contributing to Documentation

When adding new documentation:

1. **Create the document** in `/docs/` directory
2. **Add to this index** with appropriate category
3. **Link from CLAUDE.md** if it's critical
4. **Add to Common Issues** table if it solves a specific problem
5. **Include diagnostic commands** and code examples
6. **Reference file locations** with line numbers
7. **Add "Last Updated" date** at bottom of doc

---

## Quick Access: LLM Prompt Override System

**Location**: Settings → AI & LLM → LLM Prompts

**Key Features**:
- Override any LLM prompt without code changes
- Specify service/model routing per operation
- Template variable substitution with {{variable}} syntax
- View default prompts before overriding
- Enable/disable overrides instantly

**Documentation**:
- Full guide: [`PROMPT_OVERRIDE_SYSTEM.md`](PROMPT_OVERRIDE_SYSTEM.md)
- Integration: [`PROMPT_OVERRIDE_INTEGRATION_GUIDE.md`](PROMPT_OVERRIDE_INTEGRATION_GUIDE.md)

---

**Last Updated**: 2025-10-09
**Maintained By**: Claude Code Development Team
