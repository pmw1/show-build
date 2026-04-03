# Show-Build Tools Recommendations

**Date**: 2026-01-20
**Analysis Scope**: Complete system analysis of tools, services, scripts, and infrastructure
**Purpose**: Identify gaps and recommend new tools for the broadcast production workflow

---

## Executive Summary

Show-Build is a mature database-first broadcast production platform with **33+ existing tools** across 6 categories. This analysis identifies **15 high-impact tool opportunities** that would significantly enhance production efficiency.

**Current Tool Inventory**:
- Script Generation & Rendering: 5 tools
- Media Asset Processing: 6 tools
- AssetID Management: 4 tools
- Content Organization: 5 tools
- Utility & Maintenance: 3 tools
- Backend Services: 12 services
- API Routers: 46+ endpoints

---

## Current Tools Inventory

### 1. Script Generation (`/tools/`)

| Tool | Purpose | Status |
|------|---------|--------|
| `render-script-host.py` | HTML/PDF host scripts from markdown | Active |
| `render-script-production.py` | Technical rundown scripts | Active |
| `render_fsq_png.py` | FSQ quote PNG generation | Active |
| `render_quotes_pdf.py` | Quote PDF via ReportLab | Active |
| `extract_fsq_quotes.py` | Extract FSQ cue blocks to JSON | Active |

### 2. Media Processing (`/tools/`)

| Tool | Purpose | Status |
|------|---------|--------|
| `extract_sots.py` | FFmpeg SOT extraction with padding | Active |
| `update_sot_durations.py` | Update durations via ffprobe | Active |
| `media-collect.py` | Symlink collection for vMix | Active |
| `enumerate_media_files.py` | Copy media with enumerated names | Active |
| `fsq_duration_scanner.py` | Validate FSQ duration fields | Active |
| `media_job_queue.py` | Job queue management | Active |

### 3. AssetID System (`/tools/`)

| Tool | Purpose | Status |
|------|---------|--------|
| `assetid_generator.py` | Generate AssetIDs via API | Active |
| `assetid_decoder.py` | Decode AssetID components | Active |
| `production_assetid_converter.py` | Convert legacy formats | Active |

### 4. Backend Services (`/app/services/`)

| Service | Purpose | Queue |
|---------|---------|-------|
| `ffmpeg_tasks.py` | Cross-platform FFmpeg processing | media |
| `host_script_generator.py` | Database-driven script generation | - |
| `script_compilation.py` | Server-side compilation | compilation |
| `episode_scaffold.py` | Episode creation from templates | - |
| `asset_id.py` | AssetID management | - |
| `file_inventory_scanner_v2.py` | Directory scanning (v2) | - |

---

## Recommended New Tools

### Priority 1: High Impact (Recommended Immediately)

#### 1.1 Asset Metadata Validator
**Purpose**: Scan all cue blocks and report missing/invalid fields before rendering
**Impact**: Prevent 80% of rendering errors
**Implementation**: Python CLI + API endpoint

```bash
# Proposed usage
python tools/validate_metadata.py 0250 --fix
```

**Validates**:
- Required fields per cue type (SOT needs source, duration; FSQ needs quote, attribution)
- Asset file existence (SOT mp4 files exist at referenced paths)
- Duration format consistency (HH:MM:SS)
- AssetID registration status

**Estimated Effort**: 2-3 days

---

#### 1.2 Duration Reconciliation Tool
**Purpose**: Compare database durations vs. actual media file durations
**Impact**: Accurate production timing, scheduling reliability
**Implementation**: Python CLI with ffprobe integration

```bash
# Proposed usage
python tools/reconcile_durations.py 0250 --update
```

**Features**:
- Scans all SOT cues in episode
- Reads actual duration from media files via ffprobe
- Reports discrepancies > 1 second
- Optional auto-update to database

**Estimated Effort**: 1-2 days

---

#### 1.3 Rundown Diff Tool
**Purpose**: Compare two rundown versions, highlight changes
**Impact**: Quality assurance before production
**Implementation**: Python CLI with colored terminal output

```bash
# Proposed usage
python tools/rundown_diff.py 0250 0249  # Compare episodes
python tools/rundown_diff.py 0250 --before "2026-01-19"  # Compare to snapshot
```

**Features**:
- Segment additions/deletions
- Timing changes
- Cue block modifications
- Export to HTML diff view

**Estimated Effort**: 2-3 days

---

#### 1.4 Segment Template Library Tool
**Purpose**: Save, search, and reuse verified segment blocks
**Impact**: Reduce manual entry by 30-40% for recurring content
**Implementation**: CLI + API + Database table

```bash
# Proposed usage
python tools/segment_library.py save 0250 "intro" --name "Standard Show Intro"
python tools/segment_library.py insert 0251 "Standard Show Intro" --position 1
python tools/segment_library.py list --type "intro"
```

**Features**:
- Save segments with metadata tags
- Version tracking for templates
- Search by type, tags, show
- Insert with variable substitution (episode number, date, etc.)

**Estimated Effort**: 3-4 days

---

#### 1.5 Production Report Generator
**Purpose**: Generate episode summary with timing, asset counts, status
**Impact**: Production oversight, stakeholder communication
**Implementation**: Python CLI with PDF/HTML output

```bash
# Proposed usage
python tools/production_report.py 0250 --format pdf
```

**Outputs**:
- Total runtime with block breakdown
- Asset inventory (SOTs, FSQs, GFX by count)
- Missing/incomplete items
- Segment status summary
- Speaker time allocation

**Estimated Effort**: 2 days

---

### Priority 2: Medium Impact (Next Sprint)

#### 2.1 SOT Sync Validator
**Purpose**: Verify SOT trimming accuracy matches cue metadata
**Implementation**: FFprobe + database comparison

```bash
python tools/validate_sot_sync.py 0250
```

---

#### 2.2 Quote Metadata Enricher
**Purpose**: Add speaker attribution, source context to FSQ quotes
**Implementation**: LLM-assisted metadata extraction

```bash
python tools/enrich_quotes.py 0250 --llm ollama
```

---

#### 2.3 Media Proxy Generator
**Purpose**: Create low-res proxies for faster preview/editing
**Implementation**: FFmpeg batch transcoding

```bash
python tools/generate_proxies.py 0250 --resolution 720p
```

---

#### 2.4 Transcription Archiver
**Purpose**: Store/search transcriptions from completed episodes
**Implementation**: Database table + search API

```bash
python tools/archive_transcription.py 0250 --segment "interview-jones"
python tools/search_transcripts.py "climate policy" --episodes 0240-0250
```

---

#### 2.5 Asset Health Dashboard
**Purpose**: System-wide asset status monitoring
**Implementation**: API endpoint + Vue component

**Displays**:
- Missing assets by episode
- Broken asset references
- Unused assets (cleanup candidates)
- Storage utilization

---

### Priority 3: Future Enhancements

| Tool | Purpose | Effort |
|------|---------|--------|
| A/B Script Comparison | Side-by-side script versions | 2 days |
| Broadcast Log Generator | FCC-compliant documentation | 3 days |
| Content Reusability Analyzer | Find repurposable segments | 2 days |
| Asset Deprecation Tracker | Track unused assets | 1 day |
| Bulk Metadata Editor | Update cue fields in batch | 2 days |

---

## Infrastructure Recommendations

### 3.1 Unified Debug Endpoint
**Current**: `./scripts/debug-frontend.sh` exists for frontend
**Gap**: No equivalent for backend system health
**Recommendation**: Add `/api/debug/health-extended` endpoint

```json
{
  "database": {"status": "ok", "latency_ms": 12},
  "redis": {"status": "ok", "latency_ms": 1},
  "celery": {"workers": 3, "queued_tasks": 7},
  "storage": {"media_root_accessible": true, "free_gb": 450},
  "external_apis": {
    "ollama": {"status": "ok", "models": 8},
    "xtts": {"status": "ok"},
    "whisper": {"status": "timeout"}
  }
}
```

---

### 3.2 API Documentation Generator
**Current**: 46+ API endpoints with no centralized documentation
**Gap**: No auto-generated API spec
**Recommendation**: Enable FastAPI's built-in OpenAPI

```python
# main.py addition
app = FastAPI(
    title="Show-Build API",
    version="2.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
```

Access at: `https://192.168.51.210:8888/api/docs`

---

### 3.3 Test Data Lifecycle Tool
**Current**: `is_test_data` flag exists but not fully utilized
**Gap**: No automatic cleanup or management
**Recommendation**: Add cleanup commands

```bash
python tools/test_data.py list        # Show all test data
python tools/test_data.py cleanup     # Remove test data older than 30 days
python tools/test_data.py seed        # Create fresh test dataset
```

---

## Celery Queue Optimization

### Current Queues (7)
- `assets_high`, `assets`, `assets_low` - Asset processing tiers
- `compilation` - Script compilation
- `quotes` - Quote extraction
- `media` - FFmpeg/video processing
- `fsq` - FSQ PNG generation

### Recommended Additions

| Queue | Purpose | Worker |
|-------|---------|--------|
| `validation` | Metadata validation tasks | Any |
| `reporting` | Report generation (non-blocking) | Kairo |
| `archive` | Long-running archive operations | Windows |

---

## Implementation Roadmap

### Week 1-2
1. Asset Metadata Validator (1.1)
2. Duration Reconciliation Tool (1.2)
3. Unified Debug Endpoint (3.1)

### Week 3-4
1. Rundown Diff Tool (1.3)
2. Production Report Generator (1.5)
3. API Documentation Generator (3.2)

### Week 5-6
1. Segment Template Library (1.4)
2. SOT Sync Validator (2.1)
3. Test Data Lifecycle Tool (3.3)

### Month 2+
- Medium priority tools (2.2-2.5)
- Future enhancements (Priority 3)

---

## Summary

**Immediate Wins**:
- Asset Metadata Validator prevents rendering failures
- Duration Reconciliation ensures accurate timing
- Debug endpoint provides operational visibility

**Strategic Investments**:
- Segment Template Library reduces repetitive work
- Transcription Archiver enables content mining
- API documentation improves developer experience

**Total Estimated Effort**: ~30 developer-days for Priority 1+2 tools

---

*Document maintained by show-build-claude. Last updated: 2026-01-20*
