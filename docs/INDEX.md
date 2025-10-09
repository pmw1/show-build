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

---

## System Guides

### Core Systems
- [`ASSETID_SYSTEM_GUIDE.md`](ASSETID_SYSTEM_GUIDE.md) - AssetID generation, conversion, scanning
- [`RBAC_AUTHENTICATION_GUIDE.md`](RBAC_AUTHENTICATION_GUIDE.md) - Role-based access control & authentication
- [`TEST_DATA_MANAGEMENT.md`](TEST_DATA_MANAGEMENT.md) - Test data vs production data separation

### Feature Guides
- [`CUE_BLOCK_INSERTION_PROTOCOL.md`](CUE_BLOCK_INSERTION_PROTOCOL.md) - Cue insertion UX (implemented)
- [`HEALTH_CHECK_PROGRESSIVE_LOADING.md`](HEALTH_CHECK_PROGRESSIVE_LOADING.md) - Progressive health check system (implemented)

---

## Training & Research

### Model Training
- [`VOICE_MODEL_TRAINING_GUIDE.md`](VOICE_MODEL_TRAINING_GUIDE.md) - Voice model training system (stubbed)
- [`FINE_TUNE_GROK_SASS_GUIDE.md`](FINE_TUNE_GROK_SASS_GUIDE.md) - Fine-tuning Grok for SASS
- [`GROK_QUANTIZATION_QUALITY_COMPARISON.md`](GROK_QUANTIZATION_QUALITY_COMPARISON.md) - Quantization quality analysis
- [`IQ_QUANTIZATION_RESEARCH.md`](IQ_QUANTIZATION_RESEARCH.md) - IQ quantization research

### Analysis Tools
- [`WPM_AUDIO_ANALYSIS_TODO.md`](WPM_AUDIO_ANALYSIS_TODO.md) - WPM audio analysis (needs Whisper)

---

## Architecture & Status

- [`SHOW_BUILD_STATUS_UFDP.md`](../SHOW_BUILD_STATUS_UFDP.md) - Universal Functional Design Pattern status
  - System architecture
  - Database-first approach
  - Implementation status

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
│   ├── VUE_TEMPLATE_REF_CONFLICTS.md     # Vue reactivity issues
│   ├── VUE_APP_MOUNTING_WARNING.md       # Vue mounting issues
│   ├── CUE_BLOCK_INSERTION_PROTOCOL.md   # Cue insertion UX
│   ├── HEALTH_CHECK_PROGRESSIVE_LOADING.md # Health check system
│   ├── VOICE_MODEL_TRAINING_GUIDE.md     # Voice training
│   ├── WPM_AUDIO_ANALYSIS_TODO.md        # WPM analysis
│   └── [quantization guides]
│
├── app/                        # FastAPI backend
│   ├── main.py                # Main application entry
│   ├── llm_proxy_router.py    # LLM proxy endpoint
│   ├── auth/                  # Authentication system
│   └── ...
│
├── disaffected-ui/            # Vue 3 frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── ContentEditor.vue  # Main editor component
│   │   ├── composables/
│   │   │   └── useLLM.js         # LLM integration
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

**Last Updated**: 2025-10-07
**Maintained By**: Claude Code Development Team
