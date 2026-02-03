# LLM Preprocessing Layer - UFDP

**Status**: Implemented
**Implementation Date**: 2026-01-26
**Components**: Frontend + Backend + Database
**Purpose**: Two-tier LLM architecture providing prechewed data for efficient downstream AI operations

---

## Executive Summary

The LLM Preprocessing Layer creates a **database-first** system that:

- **First-Pass Extraction**: Initial LLM analyzes raw segment content, extracts entities, summaries
- **Prechewed Data Storage**: PostgreSQL stores extracted data for reuse
- **Efficient Downstream Operations**: Episode descriptions, social posts use pre-extracted data
- **Stale Detection**: Hash-based change detection triggers re-extraction
- **Integration with Universal LLM Framework**: Uses `useLLMState` for operation tracking

**Integrates With**: `useLLMState.js`, `useLLMPrompts.js`, Prompt Override System

---

## Architecture Overview

### System Components

```
                    Frontend (Vue 3)
+-------------------------------------------------------------+
|  useLLMState.js          | Operation tracking for extraction|
|  useSegmentLLMData.js    | Composable for LLM data          |
|  useLLMPrompts.js        | Extraction prompt templates      |
+-----------------------------+-------------------------------+
                              |
                              | REST API (/api/segments/*)
                              |
+-----------------------------v-------------------------------+
|                Backend (FastAPI)                            |
+-------------------------------------------------------------+
|  segment_llm_router.py   | 7 REST endpoints for LLM data    |
|  segment_llm_extractor.py| Extraction service               |
+-----------------------------+-------------------------------+
                              |
                              | SQLAlchemy ORM
                              |
+-----------------------------v-------------------------------+
|              Database (PostgreSQL)                          |
+-------------------------------------------------------------+
|  segment_llm_data        | Prechewed data per segment       |
|  (linked to rundown_items)| Entities, summaries, quotes     |
+-------------------------------------------------------------+
```

### Data Flow

```
Raw segment content (script_content)
    |
    v
Trigger extraction (manual or batch)
    |
    v
POST /api/segments/{id}/extract
    |
    v
segment_llm_extractor.py processes with LLM
    |
    v
Structured response parsed (entities, summary, quotes)
    |
    v
Saves to segment_llm_data table
    |
    v
[Ready for downstream LLM operations]
    |
    v
GET /api/segments/episode/{ep}/llm-context
    |
    v
Template variables resolved from prechewed data
    |
    v
Episode description generated with minimal context
```

---

## Database Schema

### Table: `segment_llm_data`

**Purpose**: Stores prechewed LLM data per segment for efficient downstream operations

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `asset_id` | String(50) | Unique asset identifier (indexed) |
| `rundown_item_id` | Integer (FK) | Links to rundown_items.id (CASCADE delete) |
| `llm_description` | Text | LLM-optimized description |
| `llm_summary` | Text | 1-2 sentence summary |
| `key_quotes` | JSON | Array of notable quotes |
| `extracted_people` | JSON | `[{name, role, context}]` |
| `extracted_organizations` | JSON | `[{name, type, context}]` |
| `extracted_institutions` | JSON | `[{name, type}]` |
| `extracted_topics` | JSON | `["topic1", "topic2"]` |
| `source_content_hash` | String(64) | SHA256 for stale detection |
| `extraction_model` | String(100) | Model used for extraction |
| `extraction_timestamp` | DateTime | When extraction occurred |
| `confidence_score` | Float | 0.0-1.0 confidence |
| `token_count` | Integer | Approximate token count |
| `processing_status` | String(20) | pending/processing/completed/failed/stale |
| `processing_tier` | Integer | Highest completed tier (1, 2, 3...) |
| `derived_data` | JSON | Extensible storage for future tier analysis |
| `tier_metadata` | JSON | Per-tier processing info |
| `error_message` | Text | Error if failed |
| `needs_review` | Boolean | Flag for human review |
| `reviewed_by` | Integer (FK) | User who reviewed |
| `reviewed_at` | DateTime | Review timestamp |
| `is_test_data` | Boolean | Test data flag |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

**Indexes**:
- `ix_segment_llm_data_asset_id` (unique)
- `ix_segment_llm_data_rundown_item_id`
- `ix_segment_llm_data_processing_status`
- `ix_segment_llm_data_extraction_timestamp`
- `ix_segment_llm_data_processing_tier`

---

## API Endpoints

### REST API Router

**Base Path**: `/api/segments`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/{rundown_item_id}/llm-data` | Get prechewed data for segment |
| POST | `/{rundown_item_id}/extract` | Trigger extraction for segment |
| PUT | `/{rundown_item_id}/llm-data` | Manual update of LLM data |
| DELETE | `/{rundown_item_id}/llm-data` | Clear data for re-extraction |
| POST | `/batch-extract` | Bulk extraction for multiple segments |
| GET | `/episode/{episode_number}/llm-context` | Episode prechewed data |
| GET | `/llm-data/stale` | List stale segments |
| GET | `/{rundown_item_id}/stale` | Check stale status for one segment |

### Request/Response Examples

**POST /api/segments/123/extract**
```json
{
  "model": "mistral:7b",
  "force": false
}
```

**Response**
```json
{
  "success": true,
  "rundown_item_id": 123,
  "processing_status": "completed",
  "extraction_timestamp": "2026-01-26T10:30:00Z",
  "data": {
    "llm_summary": "Discussion on AI regulation featuring tech policy expert Dr. Smith.",
    "extracted_people": [
      {"name": "Dr. Jane Smith", "role": "Guest", "context": "AI Policy Expert at MIT"}
    ],
    "extracted_organizations": [
      {"name": "MIT", "type": "institution", "context": "Research university"}
    ],
    "extracted_topics": ["AI regulation", "tech policy", "government oversight"],
    "key_quotes": ["AI regulation must balance innovation with safety"]
  }
}
```

**GET /api/segments/episode/249/llm-context**
```json
{
  "success": true,
  "context": {
    "episode_number": "249",
    "segment_count": 5,
    "segments": [
      {
        "rundown_item_id": 123,
        "title": "AI Regulation Deep Dive",
        "llm_summary": "...",
        "processing_status": "completed"
      }
    ],
    "aggregated": {
      "all_people": [...],
      "all_organizations": [...],
      "all_topics": [...],
      "all_quotes": [...]
    },
    "template_variables": {
      "segment_summaries": "...",
      "guest_names": "Dr. Jane Smith, John Doe",
      "topics": "AI regulation, tech policy, ...",
      "organizations": "MIT, Acme Corp"
    }
  }
}
```

---

## Frontend Implementation

### Composable: `useSegmentLLMData.js`

**Location**: `/disaffected-ui/src/composables/useSegmentLLMData.js`

**Functions**:

| Function | Description |
|----------|-------------|
| `getLLMData(itemId, useCache)` | Fetch LLM data with caching |
| `extractLLMData(itemId, options)` | Trigger extraction |
| `checkStale(itemId)` | Check stale status (async) |
| `isStale(itemId)` | Check stale status (sync from cache) |
| `batchExtract(itemIds, options)` | Batch extraction |
| `getEpisodeLLMContext(episodeNumber)` | Get episode context |
| `getStaleSegments(episodeNumber)` | List stale segments |
| `deleteLLMData(itemId)` | Delete for re-extraction |
| `updateLLMData(itemId, updates)` | Manual update |
| `clearCache(itemId)` | Clear cache |
| `isExtracting(itemId)` | Check if extraction in progress |

**Usage Example**:

```javascript
import { useSegmentLLMData } from '@/composables/useSegmentLLMData'

export default {
  setup() {
    const {
      getLLMData,
      extractLLMData,
      isStale,
      batchExtract,
      getEpisodeLLMContext
    } = useSegmentLLMData()

    return {
      getLLMData,
      extractLLMData,
      isStale,
      batchExtract,
      getEpisodeLLMContext
    }
  },

  methods: {
    async triggerExtraction(segmentId) {
      const result = await this.extractLLMData(segmentId, {
        model: 'mistral:7b',
        force: false,
        notify: true
      })
      console.log('Extraction result:', result)
    },

    async prepareEpisodeForAI(episodeNumber) {
      // Get all stale segments
      const staleItems = await this.getStaleSegments(episodeNumber)

      if (staleItems.length > 0) {
        // Batch extract stale items
        const itemIds = staleItems.map(s => s.rundown_item_id)
        await this.batchExtract(itemIds)
      }

      // Now get the full episode context
      const context = await this.getEpisodeLLMContext(episodeNumber)
      return context.template_variables
    }
  }
}
```

---

## Prompt Configuration

### Extraction Prompt Override

Add to `prompt_overrides` table:

| Field | Value |
|-------|-------|
| category | `extract` |
| operation_key | `extract-segment-llm-data` |
| temperature | 0.2 |
| max_tokens | 2000 |
| suggested_service | `ollama` |
| suggested_model | `mistral:7b` |

**Default System Prompt**:
```
You are an expert content analyst for broadcast media production. Your task is to extract structured data from segment scripts to support downstream LLM operations like episode descriptions and social media posts.

Return valid JSON only. Be precise with entity names and roles. Extract meaningful quotes that capture key points.
```

**Default User Prompt Template**:
```
Analyze this segment content and extract structured data:

SEGMENT: {{segment_title}}
EPISODE: {{episode_number}}

CONTENT:
{{content}}

Return JSON in this exact format:
{
  "llm_summary": "1-2 sentence summary",
  "llm_description": "Detailed description (3-5 sentences)",
  "extracted_people": [{"name": "", "role": "", "context": ""}],
  "extracted_organizations": [{"name": "", "type": "", "context": ""}],
  "extracted_institutions": [{"name": "", "type": ""}],
  "extracted_topics": ["topic1", "topic2"],
  "key_quotes": ["Quote 1", "Quote 2"],
  "confidence": 0.85
}
```

---

## Template Variable Resolution

When building prompts for downstream operations, these variables are resolved from prechewed data:

| Variable | Resolution |
|----------|------------|
| `{{segment_summaries}}` | Join all `llm_summary` with newlines |
| `{{guest_names}}` | Filter `extracted_people` where role contains "Guest" |
| `{{topics}}` | Deduplicated `extracted_topics` across segments |
| `{{key_quotes}}` | Aggregated `key_quotes` (limit 5) |
| `{{organizations}}` | Names from `extracted_organizations` |
| `{{institutions}}` | Names from `extracted_institutions` |
| `{{all_people}}` | All `extracted_people` with roles |

---

## Files Reference

### Created Files

| File | Purpose |
|------|---------|
| `app/models_segment_llm.py` | SegmentLLMData SQLAlchemy model |
| `app/alembic/versions/1021_add_segment_llm_data.py` | Database migration |
| `app/segment_llm_router.py` | FastAPI router with 8 endpoints |
| `app/services/segment_llm_extractor.py` | Extraction service |
| `disaffected-ui/src/composables/useSegmentLLMData.js` | Frontend composable |
| `docs/LLM_PREPROCESSING_LAYER.md` | This documentation |

### Modified Files

| File | Changes |
|------|---------|
| `app/main.py` | Register segment_llm_router |

---

## Verification

### 1. Database Migration
```bash
cd /mnt/process/show-build/app && alembic upgrade head
```

### 2. Verify Table
```bash
docker exec show-build-postgres psql -U showbuild -d showbuild -c "\d segment_llm_data"
```

### 3. Test API Endpoints
```bash
# Get LLM data (will return stale status if no data)
curl https://192.168.51.210:8888/api/segments/1/llm-data \
  -H "Authorization: Bearer YOUR_TOKEN"

# Trigger extraction
curl -X POST https://192.168.51.210:8888/api/segments/1/extract \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b"}'

# Get episode context
curl https://192.168.51.210:8888/api/segments/episode/249/llm-context \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check stale segments
curl https://192.168.51.210:8888/api/segments/llm-data/stale \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Multi-Tier Processing (Future)

The system supports multiple processing tiers for progressive enrichment:

### Tier 1 (Implemented)
- Entity extraction (people, organizations, institutions)
- Topic extraction
- Summary generation
- Key quote extraction

### Tier 2 (Future)
- Sentiment analysis per entity
- Relationship mapping
- Controversy/sensitivity scoring
- Fact-check flags

### Tier 3 (Future)
- Cross-segment entity tracking
- Topic trends over time
- Guest appearance history
- Content similarity scoring

**How it works:**
- `processing_tier` column tracks highest completed tier
- `derived_data` JSON stores tier 2+ analysis results
- `tier_metadata` JSON stores per-tier processing info
- Each tier can use different models/prompts

---

## Troubleshooting

### Extraction Times Out
- Check Ollama connectivity: `curl http://192.168.51.197:11434/api/tags`
- Increase timeout in extraction service
- Try smaller model

### Stale Data Not Detected
- Verify content hash is being computed correctly
- Check `source_content_hash` matches current content

### Cache Issues
- Clear frontend cache: `clearCache(itemId)` or `clearCache()`
- Cache TTL is 5 minutes by default

### Extraction Returns Malformed JSON
- Check extraction prompt in `prompt_overrides` table
- Review LLM response in server logs
- Ensure model supports JSON output well
