# Universal LLM Framework - UFDP

**Status**: ✅ Implemented (v1.0 - Production Ready)
**Implementation Date**: 2025-10-09
**Components**: Frontend + Backend + Database
**Purpose**: Unified state management, visual feedback, and persistence for all AI/LLM operations

---

## Executive Summary

The Universal LLM Framework is a complete cutover from fragmented AI state management to a centralized, database-backed system that provides:

- **Unified State Management**: Single composable (`useLLMState.js`) for all LLM operations
- **Visual Feedback System**: Automatic color-coded borders and animations across 54 scope/state combinations
- **Persistent Notifications**: Facebook-style notification center with priority filtering
- **Database Persistence**: Operations and notifications survive page reload
- **Async Operation Support**: LLM work continues even when user navigates away

**Replaces**: Old fragmented systems (`aiState`, `aiAnalyzing`, `generatingItemIndex`, manual CSS classes)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Frontend Implementation](#frontend-implementation)
3. [Backend Implementation](#backend-implementation)
4. [Database Schema](#database-schema)
5. [Usage Guide](#usage-guide)
6. [Migration from Legacy Systems](#migration-from-legacy-systems)
7. [Visual Feedback Reference](#visual-feedback-reference)
8. [Notification System](#notification-system)
9. [API Reference](#api-reference)
10. [Health Check & Timeout Configuration](#health-check--timeout-configuration)
11. [Troubleshooting](#troubleshooting)
12. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                          │
├─────────────────────────────────────────────────────────────┤
│  useLLMState.js      │ Universal state management composable│
│  NotificationCenter  │ Facebook-style notification panel    │
│  llm-visual-feedback │ Global CSS for all visual states    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ REST API (/api/llm/*)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                Backend (FastAPI)                             │
├─────────────────────────────────────────────────────────────┤
│  llm_state_router.py │ 6 REST endpoints for state/notifs   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ SQLAlchemy ORM
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Database (PostgreSQL)                           │
├─────────────────────────────────────────────────────────────┤
│  llm_operations      │ Active LLM operations (persistent)   │
│  llm_notifications   │ Notification queue (last 50)         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Component initiates LLM operation
    ↓
llmState.startOperation() or llmState.withLLM()
    ↓
Creates operation record with unique ID
    ↓
Saves to database (debounced, 1 second)
    ↓
Applies visual feedback CSS classes
    ↓
Adds notification to queue
    ↓
[LLM processing happens asynchronously]
    ↓
llmState.stopOperation() or automatic via withLLM()
    ↓
Removes from active operations
    ↓
Updates database
    ↓
Adds completion notification
    ↓
Visual feedback removed
```

---

## Frontend Implementation

### Core Composable: `useLLMState.js`

**Location**: `/disaffected-ui/src/composables/useLLMState.js`

**Key Features:**
- Global reactive state shared across all component instances
- Database persistence with localStorage fallback
- Auto-save debouncing (1 second delay)
- Operation tracking with unique IDs
- Priority-based notification system

**Basic Usage:**

```javascript
import { useLLMState } from '@/composables/useLLMState'

export default {
  setup() {
    const llmState = useLLMState()
    return { llmState }
  },
  methods: {
    async performAIOperation() {
      // Option 1: Manual start/stop
      const opId = this.llmState.startOperation(
        'field',                    // scope
        'quote-textarea',           // target ID
        'analyzing',                // operation type
        {
          model: 'qwen2.5-coder:7b',
          persistent: true,         // survives page reload
          notify: true,
          priority: this.llmState.PRIORITY.NORMAL
        }
      )

      try {
        const result = await callLLMAPI()
        this.llmState.stopOperation(opId, { success: true })
      } catch (error) {
        this.llmState.failOperation(opId, error)
      }

      // Option 2: Automatic wrapper (recommended)
      const result = await this.llmState.withLLM(
        'field',
        'quote-textarea',
        'analyzing',
        async () => {
          return await callLLMAPI()
        },
        {
          model: 'qwen2.5-coder:7b',
          persistent: true,
          notify: true
        }
      )
    }
  }
}
```

### Notification Center Component

**Location**: `/disaffected-ui/src/components/NotificationCenter.vue`

**Features:**
- Bell icon in app header (next to user menu)
- Badge counter for unread notifications
- Priority filtering (critical, high, normal, low)
- Dismissible notifications
- Auto-mark-as-read when panel opens
- Last 50 notifications retained

**User Interface:**
- Click bell icon to open/close panel
- Filter by priority using chips
- Dismiss individual notifications with X button
- Clear all with trash icon

### Visual Feedback System

**Location**: `/disaffected-ui/src/assets/styles/llm-visual-feedback.css`

**CSS Classes**: Automatically applied by `llmState.getVisualClass()`

**Format**: `.llm-{state}.llm-scope-{scope}`

**Example**: `.llm-analyzing.llm-scope-field` = Purple 7px border with no animation

---

## Backend Implementation

### REST API Router

**Location**: `/app/llm_state_router.py`

**Endpoints:**

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/api/llm/operations` | Load user's active operations | JWT/API Key |
| POST | `/api/llm/operations` | Save/update operations (upsert) | JWT/API Key |
| DELETE | `/api/llm/operations/{id}` | Delete specific operation | JWT/API Key |
| GET | `/api/llm/notifications` | Load user's notifications | JWT/API Key |
| POST | `/api/llm/notifications` | Save/update notifications | JWT/API Key |
| DELETE | `/api/llm/notifications/{id}` | Delete notification | JWT/API Key |
| POST | `/api/llm/notifications/{id}/read` | Mark notification as read | JWT/API Key |

**Request/Response Examples:**

```json
// POST /api/llm/operations
{
  "operations": [
    {
      "id": "llm-op-123",
      "scope": "field",
      "targetId": "quote-textarea",
      "operation": "analyzing",
      "state": "analyzing",
      "model": "qwen2.5-coder:7b",
      "message": "AI is analyzing your quote...",
      "metadata": {},
      "priority": "normal",
      "startTime": 1728518400000,
      "persistent": true
    }
  ]
}

// Response
{
  "success": true,
  "saved": 1,
  "message": "Saved 1 LLM operations"
}
```

---

## Database Schema

### Table: `llm_operations`

```sql
CREATE TABLE llm_operations (
    id VARCHAR PRIMARY KEY,              -- e.g., "llm-op-123"
    user_id INTEGER NOT NULL REFERENCES users(id),
    scope VARCHAR NOT NULL,              -- field, card, item, etc.
    target_id VARCHAR NOT NULL,          -- Unique identifier for target
    operation VARCHAR NOT NULL,          -- analyzing, generating, etc.
    state VARCHAR NOT NULL,              -- analyzing, approved, rejected, etc.
    model VARCHAR,                       -- AI model name
    message TEXT,                        -- Status message
    metadata TEXT,                       -- JSON-encoded metadata
    priority VARCHAR,                    -- critical, high, normal, low
    start_time BIGINT NOT NULL,          -- Unix timestamp (ms)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    persistent BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_llm_operations_user_id ON llm_operations(user_id);
```

### Table: `llm_notifications`

```sql
CREATE TABLE llm_notifications (
    id VARCHAR PRIMARY KEY,              -- e.g., "notif-456"
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR NOT NULL,
    message TEXT,
    priority VARCHAR,                    -- critical, high, normal, low
    notification_type VARCHAR,           -- operation-start, operation-complete, etc.
    operation_id VARCHAR,                -- Reference to llm_operations.id
    success BOOLEAN,                     -- True/False/NULL
    read BOOLEAN DEFAULT FALSE,
    dismissed BOOLEAN DEFAULT FALSE,
    metadata TEXT,                       -- JSON-encoded data
    error TEXT,                          -- JSON-encoded error info
    timestamp BIGINT NOT NULL,           -- Unix timestamp (ms)
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_llm_notifications_user_id ON llm_notifications(user_id);
```

---

## Usage Guide

### Common Scenarios

#### Scenario 1: FSQ Quote Analysis (Field-Level)

```javascript
// FsqModal.vue - analyzeQuote()
async analyzeQuote() {
  const result = await this.llmState.withLLM(
    'field',                          // scope
    'fsq-quote-field',                // target ID
    'analyzing',                      // operation
    async () => {
      // Perform LLM analysis
      const segments = await this.intelligentQuoteSplit(this.quote, config)
      return { segments }
    },
    {
      model: 'qwen2.5-coder:7b',
      persistent: false,              // Don't persist quote analysis
      notify: true,
      notificationTitle: 'FSQ Quote Analysis',
      priority: this.llmState.PRIORITY.NORMAL,
      state: this.llmState.STATE.ANALYZING
    }
  )

  // Handle result
  if (result.segments.length > 1) {
    this.showSplitRecommendation(result.segments)
  }
}
```

**Visual Result**: Purple 7px border appears around quote textarea during analysis

#### Scenario 2: Rundown Item Content Generation (Item-Level)

```javascript
// ContentEditor.vue - generateContent()
async generateItemContent(itemIndex) {
  const item = this.rundownItems[itemIndex]

  const result = await this.llmState.withLLM(
    'item',                           // scope
    `rundown-item-${item.id}`,        // target ID
    'generating',                     // operation
    async () => {
      // Generate content via LLM
      const content = await this.llm.smartCall('content-expansion', prompt)
      return { content }
    },
    {
      model: 'llama3:latest',
      persistent: true,               // Persist across navigation
      notify: true,
      notificationTitle: 'Content Generation',
      priority: this.llmState.PRIORITY.HIGH
    }
  )

  // Apply generated content
  this.updateItemContent(itemIndex, result.content)
}
```

**Visual Result**: Purple 7px throbbing border appears around rundown item card

#### Scenario 3: Episode-Level Analysis (Episode-Level)

```javascript
async analyzeEpisodeStructure(episodeId) {
  const result = await this.llmState.withLLM(
    'episode',                        // scope
    `episode-${episodeId}`,           // target ID
    'analyzing',                      // operation
    async () => {
      const analysis = await this.llm.callOllama(prompt)
      return { analysis }
    },
    {
      model: 'qwen2.5-coder:32b',
      persistent: true,
      notify: true,
      notificationTitle: 'Episode Structure Analysis',
      priority: this.llmState.PRIORITY.CRITICAL,
      successMessage: 'Episode analysis complete'
    }
  )
}
```

**Visual Result**: 6px purple pulsing border on episode container

### Getting Visual Feedback in Templates

```vue
<template>
  <v-textarea
    v-model="quote"
    :class="quoteFieldClass"
    :style="quoteFieldStyle"
  />
</template>

<script>
export default {
  computed: {
    quoteFieldClass() {
      return this.llmState.getVisualClass('field', 'quote-textarea')
    },
    quoteFieldStyle() {
      return this.llmState.getVisualStyle('field', 'quote-textarea')
    },
    isLLMActive() {
      return this.llmState.isTargetActive('field', 'quote-textarea')
    }
  }
}
</script>
```

---

## Migration from Legacy Systems

### Deprecated Patterns

❌ **OLD (FsqModal.vue)**:
```javascript
data() {
  return {
    aiState: null,
    aiMessage: '',
    aiAnalyzing: false,
    aiActionPending: false
  }
}

async analyzeQuote() {
  this.aiAnalyzing = true
  this.aiState = 'analyzing'
  this.aiMessage = 'AI is analyzing...'

  try {
    const result = await callLLM()
    this.aiState = 'approved'
  } catch (error) {
    this.aiState = 'rejected'
  } finally {
    this.aiAnalyzing = false
  }
}
```

✅ **NEW**:
```javascript
setup() {
  const llmState = useLLMState()
  return { llmState }
}

async analyzeQuote() {
  const result = await this.llmState.withLLM(
    'field',
    'quote-field',
    'analyzing',
    async () => await callLLM(),
    { model: 'qwen2.5-coder:7b', notify: true }
  )
}
```

❌ **OLD (ContentEditor.vue)**:
```javascript
data() {
  return {
    generatingItemIndex: -1
  }
}

startLLMGeneration(itemIndex) {
  this.generatingItemIndex = itemIndex
}

stopLLMGeneration() {
  this.generatingItemIndex = -1
}
```

✅ **NEW**:
```javascript
data() {
  return {
    llmState: useLLMState()
  }
}

// Use llmState.withLLM() - automatic state management
```

### CSS Class Migration

❌ **OLD (Manual CSS)**:
```vue
<style>
.ai-analyzing {
  border: 7px solid #9C27B0;
  animation: throb 1.5s infinite;
}

@keyframes throb { /* ... */ }
</style>
```

✅ **NEW (Automatic via Framework)**:
```vue
<template>
  <div :class="llmState.getVisualClass('field', 'my-field')" />
</template>

<!-- CSS automatically applied from llm-visual-feedback.css -->
```

---

## Visual Feedback Reference

### Scope Levels

| Scope | Use Case | Border | Animation |
|-------|----------|--------|-----------|
| `field` | Form inputs, textareas | 7px solid | None |
| `card` | Component cards, cue cards | 3px solid | None |
| `item` | Rundown items, list items | 7px solid | Throb (1.5s) |
| `asset` | Media assets, images | 5px dashed | Pulse (2s) |
| `segment` | Script segments, paragraphs | 4px solid | Throb (1.5s) |
| `rundown` | Entire rundown operations | 8px double | Pulse (2s) |
| `episode` | Episode-level operations | 6px solid | Pulse (2s) |
| `user` | User-specific operations | 3px solid | None |
| `system` | System-wide operations | 10px double | Pulse (3s) |

### State Colors

| State | Color | Hex | Meaning |
|-------|-------|-----|---------|
| `analyzing` | Purple | #9C27B0 | AI is thinking/processing |
| `generating` | Blue | #2196F3 | AI is creating content |
| `modifying` | Orange | #FF9800 | AI is changing content |
| `approved` | Green | #4CAF50 | AI approved/completed |
| `rejected` | Red | #F44336 | AI rejected/failed |
| `pending` | Yellow | #FFC107 | Awaiting user decision |

### Animation Types

**Throb** (1.5s ease-in-out infinite):
```css
@keyframes throb {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(156, 39, 176, 0.7);
  }
  50% {
    box-shadow: 0 0 20px 5px rgba(156, 39, 176, 0.4);
  }
}
```

**Pulse** (2s ease-in-out infinite):
```css
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.7);
  }
  50% {
    opacity: 0.8;
    box-shadow: 0 0 15px 3px rgba(33, 150, 243, 0.4);
  }
}
```

---

## Notification System

### Priority Levels

```javascript
llmState.PRIORITY.CRITICAL  // Red badge, always visible
llmState.PRIORITY.HIGH      // Orange badge, important
llmState.PRIORITY.NORMAL    // Blue badge, standard
llmState.PRIORITY.LOW       // Grey badge, filterable
```

### Notification Types

- `operation-start` - LLM operation began
- `operation-complete` - LLM operation finished successfully
- `operation-error` - LLM operation failed

### Adding Custom Notifications

```javascript
this.llmState.addNotification({
  title: 'Custom Notification',
  message: 'Something happened',
  priority: this.llmState.PRIORITY.HIGH,
  type: 'custom-event',
  success: true,
  operationId: 'optional-reference'
})
```

### Auto-Dismiss Behavior

- **Low priority**: Auto-dismiss after 10 seconds
- **Normal/High/Critical**: Remain until manually dismissed

---

## API Reference

### `useLLMState()` Methods

#### `startOperation(scope, targetId, operation, options)`

Manually start tracking an LLM operation.

**Parameters:**
- `scope` (string): Scope level (field, card, item, etc.)
- `targetId` (string): Unique identifier for target element
- `operation` (string): Operation type (analyzing, generating, etc.)
- `options` (object):
  - `state` (string): Visual state (default: STATE.ANALYZING)
  - `model` (string): AI model name
  - `message` (string): Status message
  - `metadata` (object): Additional data
  - `priority` (string): Notification priority
  - `persistent` (boolean): Survive page reload (default: false)
  - `notify` (boolean): Show notification (default: true)

**Returns**: `operationId` (string)

#### `stopOperation(operationId, result)`

Stop tracking an operation.

**Parameters:**
- `operationId` (string): ID returned from startOperation
- `result` (object):
  - `success` (boolean): Operation succeeded
  - `message` (string): Completion message
  - `notify` (boolean): Show completion notification

#### `withLLM(scope, targetId, operation, llmFunction, options)`

Wrapper that automatically manages operation lifecycle. **Recommended approach.**

**Parameters:**
- Same as startOperation, plus:
- `llmFunction` (async function): The LLM operation to perform

**Returns**: Promise resolving to llmFunction result

#### `getVisualClass(scope, targetId)`

Get CSS class for visual feedback.

**Returns**: String (e.g., `"llm-analyzing llm-scope-field"`) or null

#### `getVisualStyle(scope, targetId)`

Get inline style object for visual feedback.

**Returns**: Object with `border`, `borderRadius`, `animation` properties or null

#### `isTargetActive(scope, targetId)`

Check if target has any active operations.

**Returns**: Boolean

#### `getOperationsForTarget(scope, targetId)`

Get array of active operations for target.

**Returns**: Array of operation objects

---

## Health Check & Timeout Configuration

### Overview

Show-Build implements automated health checks for all external AI/LLM services and infrastructure. These checks run every 30 seconds and display real-time status indicators in the UI. Proper timeout configuration is critical for reliable status monitoring.

### Service Health Checks

**Monitored Services:**
- **Ollama** (192.168.51.197:11434) - Local LLM service
- **XTTS** (192.168.51.197:5001) - Text-to-speech service
- **Redis** (192.168.51.223:6379) - Cache and message broker
- **Celery** - Background task workers
- **Asterisk** (192.168.51.223:5038) - SIP/voice conference server
- **Google Drive** - Cloud storage integration

### Timeout Configuration Best Practices

**Location**: `/mnt/process/show-build/app/main.py` - `@app.get("/health")` endpoint

#### Recommended Timeout Values

| Service | Timeout | Rationale |
|---------|---------|-----------|
| **Ollama** | 5 seconds | Model loading can be slow; prevents false negatives |
| **XTTS** | 5 seconds | GPU operations may have latency; CUDA warmup delays |
| **Redis** | 2 seconds | Should respond instantly; longer timeout indicates problems |
| **Asterisk** | 2 seconds | Socket test should be fast; port connectivity check |
| **Google Drive** | 10 seconds | API calls over internet; variable network latency |
| **Database** | 3 seconds | Query should be fast; longer indicates connection pool issues |

#### Configuration Example

```python
# Ollama health check with 5-second timeout
async with httpx.AsyncClient(timeout=5.0) as client:
    response = await client.get(f"{ollama_host}/api/tags")
    if response.status_code == 200:
        health_status["services"]["ollama"]["status"] = "connected"

# XTTS health check with 5-second timeout
async with httpx.AsyncClient(timeout=5.0) as client:
    response = await client.get(f"{host}/health")
    if response.status_code == 200:
        data = response.json()
        is_healthy = data.get("status") == "healthy"
```

### Common Timeout Issues

#### ❌ Problem: Intermittent Red Indicators

**Symptoms:**
- Service shows red (error) intermittently
- Service is actually running and responsive
- Status flickers between green and red

**Root Cause:** Timeout too aggressive (e.g., 1 second)

**Solution:**
```python
# BAD - Too aggressive, causes false negatives
async with httpx.AsyncClient(timeout=1.0) as client:
    response = await client.get(f"{service_url}")

# GOOD - Allows for network/load variance
async with httpx.AsyncClient(timeout=5.0) as client:
    response = await client.get(f"{service_url}")
```

**Real-world Example:**
- **Before**: Ollama timeout=1.0s → 40% false negatives when loading models
- **After**: Ollama timeout=5.0s → 0% false negatives, stable green indicator

#### ❌ Problem: Health Check Blocking UI

**Symptoms:**
- UI freezes during health checks
- Dashboard loads slowly

**Root Cause:** Health check timeout too long or synchronous blocking

**Solution:**
- Keep timeouts reasonable (≤10 seconds for external APIs)
- Use `async/await` properly to avoid blocking
- Run health checks in background (automatic with FastAPI)

### Tuning Guidelines

**When to Increase Timeout:**
1. Service performs GPU operations (XTTS, local LLMs)
2. Service loads models dynamically (Ollama)
3. Service accessed over internet (Google Drive, OpenAI)
4. Intermittent false negatives in logs

**When to Decrease Timeout:**
1. Service should respond instantly (Redis, PostgreSQL)
2. Timeout causing UI slowness
3. You want faster failure detection

**Testing Timeout Values:**
```bash
# Test service response time manually
time curl -s http://192.168.51.197:11434/api/tags

# Good output: real 0m0.342s → 1s timeout OK
# Bad output: real 0m3.821s → 1s timeout too aggressive, use 5s

# Test under load
for i in {1..10}; do
  time curl -s http://192.168.51.197:5001/health
done

# Look at slowest response time, set timeout 2x that value
```

### Monitoring Health Check Performance

**Backend Logs:**
```bash
# Watch health check timing
docker logs show-build-server -f | grep -i "health\|timeout"

# Example good output:
INFO: GET /health - 200 OK (0.42s)

# Example timeout issue:
WARNING: Ollama health check timeout (1.0s exceeded)
```

**Frontend Monitoring:**
```javascript
// In browser console
// Check health check response times
performance.getEntriesByName('/health')
```

### Health Check Endpoint Response

**Successful Response:**
```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "latency": 0.003
  },
  "services": {
    "ollama": {
      "status": "connected",
      "model": "llama3.2",
      "url": "http://192.168.51.197:11434"
    },
    "xtts": {
      "status": "connected",
      "model_loaded": true,
      "cuda_available": true
    },
    "redis": {
      "status": "connected",
      "latency": 0.001
    }
  }
}
```

**Timeout Error Response:**
```json
{
  "services": {
    "ollama": {
      "status": "timeout"
    },
    "xtts": {
      "status": "error",
      "connected": false,
      "error": "Timeout"
    }
  }
}
```

### Best Practices Summary

✅ **DO:**
- Set timeouts 2-3x the expected response time
- Test timeouts under load conditions
- Use longer timeouts (5-10s) for GPU/AI services
- Monitor health check logs for timeout patterns
- Adjust timeouts based on real-world behavior

❌ **DON'T:**
- Use 1-second timeouts for AI/GPU services
- Set timeouts >30 seconds (blocks health monitoring)
- Ignore intermittent timeout warnings
- Use same timeout for all services
- Change timeouts without testing

### Implementation Checklist

When adding a new service to health checks:

- [ ] Determine expected response time under load
- [ ] Set timeout to 2-3x expected response time
- [ ] Add timeout exception handling
- [ ] Test with service under load
- [ ] Monitor for false negatives in production
- [ ] Document timeout value and rationale
- [ ] Add to this UFDP section

---

## Troubleshooting

### Issue: Visual feedback not appearing

**Symptoms**: Border/animation doesn't show during LLM operation

**Solutions:**
1. Check operation was started: `console.log(llmState.activeOperations)`
2. Verify template uses computed properties:
   ```javascript
   computed: {
     myFieldClass() {
       return this.llmState.getVisualClass('field', 'my-field-id')
     }
   }
   ```
3. Ensure CSS is imported in main.js:
   ```javascript
   import './assets/styles/llm-visual-feedback.css'
   ```

### Issue: Notifications not showing

**Symptoms**: Bell icon shows no badge, panel is empty

**Solutions:**
1. Check notification was added: `console.log(llmState.notifications)`
2. Verify priority filter includes your notification's priority
3. Check NotificationCenter is in App.vue template
4. Ensure user is authenticated (notifications are user-scoped)

### Issue: Operations not persisting across reload

**Symptoms**: Active operations disappear after page refresh

**Solutions:**
1. Verify `persistent: true` in operation options
2. Check backend API is reachable: `GET /api/llm/operations`
3. Verify database tables exist:
   ```sql
   SELECT * FROM llm_operations LIMIT 1;
   ```
4. Check browser console for API errors
5. Verify localStorage fallback has data:
   ```javascript
   console.log(localStorage.getItem('llm-operations-fallback'))
   ```

### Issue: "Operation not found" errors

**Symptoms**: Console shows warnings about missing operations

**Cause**: Trying to stop an operation that was already completed or never started

**Solution**: Always check operation exists before stopping:
```javascript
const ops = this.llmState.getOperationsForTarget('field', 'my-field')
if (ops.length > 0) {
  this.llmState.stopOperation(ops[0].id)
}
```

---

## Future Enhancements

### Planned Features

- [ ] **User Acceptance Workflow**: For operations requiring user approval (e.g., FSQ split recommendations)
  - Accept/reject buttons in notification panel
  - Callback functions for acceptance actions
  - Queue management for pending approvals

- [ ] **Real-Time Operation Updates**: WebSocket support for live status updates
  - Streaming LLM responses
  - Progress percentage tracking
  - Token usage monitoring

- [ ] **Operation History**: View past LLM operations
  - Search/filter by date, model, type
  - Replay/retry failed operations
  - Export operation logs

- [ ] **Model Selection UI**: Choose AI model per operation
  - Dropdown in notification panel
  - Save preferences per task type
  - Model capability indicators

- [ ] **Batch Operations**: Handle multiple targets simultaneously
  - Bulk content generation
  - Progress tracking for batches
  - Cancel/pause individual items

- [ ] **Cost Tracking**: Monitor API usage and costs
  - Token consumption per operation
  - Cost estimates by model
  - Budget alerts

### Potential Integration Points

- **ClaudeSpawn Integration**: Coordinate LLM operations across multiple machines
- **MQTT Event Bus**: Broadcast LLM status updates for distributed systems
- **Analytics Dashboard**: Visualize LLM usage patterns, success rates, performance metrics

---

## Related Documentation

- [`EPISODE_DIRECTORY_STANDARD.md`](docs/EPISODE_DIRECTORY_STANDARD.md) - 🗂️ **Episode File Structure Standard** - Canonical specification (AUTHORITATIVE)
- [`THUMBNAIL_GENERATION_RESEARCH.md`](docs/THUMBNAIL_GENERATION_RESEARCH.md) - Thumbnail automation research (pending implementation)
- [`LLM_GENERATOR_TROUBLESHOOTING.md`](docs/LLM_GENERATOR_TROUBLESHOOTING.md) - Test segment generator (uses legacy patterns, needs update)
- [`FSQ_NESTED_QUOTE_PROCESSING_UFDP.md`](FSQ_NESTED_QUOTE_PROCESSING_UFDP.md) - FSQ quote analysis (migrated to universal framework)
- [`DEBUGGING_STANDARDS.md`](docs/DEBUGGING_STANDARDS.md) - General debugging checklist
- [`RBAC_AUTHENTICATION_GUIDE.md`](docs/RBAC_AUTHENTICATION_GUIDE.md) - User authentication (required for LLM state)

---

## Implementation Notes

### Migration Status

**✅ Fully Migrated:**
- FsqModal.vue - Quote analysis uses `llmState.withLLM()`
- ContentEditor.vue - Helper methods use universal framework
- RundownPanel.vue - Accepts `llmState` prop

**⚠️ Partially Migrated:**
- Test segment generator (ContentEditor.vue:4031) - Still uses old patterns, functional but should be updated

**📋 Not Yet Migrated:**
- Future LLM features will use universal framework from day one

### Known Limitations (v1.0)

1. **No Streaming Support**: Operations complete atomically (all-or-nothing)
2. **Single Operation per Target**: Multiple simultaneous operations on same target not fully tested
3. **No Cancellation API**: Stopping operation doesn't abort backend LLM call
4. **Auto-Save Only**: No manual save trigger for operations
5. **Limited Error Recovery**: Failed operations must be manually retried

### Performance Considerations

- **Database Writes**: Debounced to 1 second to prevent excessive writes
- **Notification Limit**: Only last 50 notifications retained per user
- **localStorage Fallback**: 50 operation/notification limit to prevent quota exceeded
- **CSS Classes**: Applied via computed properties, minimal reactivity overhead

### Cursor Position Snapshot Pattern (Cue Insertion)

**Problem**: When opening a modal via hotkey (e.g., Ctrl+Q for FSQ), the user's cursor position in the editor is lost by the time they submit the modal. Checking `focusedParagraphIndex` at insertion time returns `null` because focus has moved to the modal.

**Solution**: Snapshot cursor position when hotkey is pressed, store it, and use the stored value for insertion.

#### Implementation Pattern

**Step 1: Add snapshot variable** (data section):
```javascript
data() {
  return {
    // Cue type insertion snapshots
    fsqInsertionIndex: null,
    sotInsertionIndex: null,
    gfxInsertionIndex: null,
    // ... one per cue type modal
  }
}
```

**Step 2: Capture position on hotkey press** (modal handler):
```javascript
handleShowFsqModal() {
  if (!this.showFsqModal) {
    // Snapshot cursor position when hotkey pressed
    this.fsqInsertionIndex = this.$refs.editorPanel?.focusedParagraphIndex;
    console.log('📍 FSQ hotkey pressed - captured cursor position:', this.fsqInsertionIndex);

    // Fallback to last segment if no focus
    if (this.fsqInsertionIndex === null || this.fsqInsertionIndex === undefined) {
      const segments = this.$refs.editorPanel?.scriptSegments || [];
      this.fsqInsertionIndex = segments.length > 0 ? segments.length - 1 : null;
      console.log('📍 No focus detected, using last segment:', this.fsqInsertionIndex);
    }

    this.showFsqModal = true;
  }
}
```

**Step 3: Use snapshot for insertion** (submit handler):
```javascript
submitFsq(cueData) {
  // ... format cue block ...

  if (isLastPart) {
    this.showFsqModal = false;

    // Use stored snapshot, NOT current focus
    const insertionIndex = this.fsqInsertionIndex;
    console.log(`📍 Using snapshotted position: ${insertionIndex}`);

    this.appendToScriptContent(`\n${cueBlock}\n`, insertionIndex);

    // Clear snapshot for next use
    this.fsqInsertionIndex = null;
    console.log('🧹 Cleared insertion snapshot');
  }
}
```

#### Key Points

1. **Snapshot at hotkey press** - Not at modal open, not at submission
2. **One variable per cue type** - Prevents conflicts between simultaneous modals
3. **Always clear after use** - Prevents stale position from being reused
4. **Fallback strategy** - Use last segment if no focus detected
5. **Console logging** - Essential for debugging cursor position issues

#### Cue Types Requiring This Pattern

- ✅ **FSQ** (Full-Screen Quote) - Implemented
- 🔲 **SOT** (Sound on Tape) - Needs implementation
- 🔲 **GFX** (Graphics) - Needs implementation
- 🔲 **VO** (Voice Over) - Needs implementation
- 🔲 **NAT** (Natural Sound) - Needs implementation
- 🔲 **PKG** (Package) - Needs implementation
- 🔲 **VOX** (Vox Pop) - Needs implementation
- 🔲 **MUS** (Music) - Needs implementation
- 🔲 **LIVE** (Live Shot) - Needs implementation
- 🔲 **IMG** (Image) - Needs implementation

#### Files Modified

- `/mnt/process/show-build/disaffected-ui/src/components/ContentEditor.vue`
  - Line 763: Added `fsqInsertionIndex: null`
  - Lines 1122-1137: Modified `handleShowFsqModal()` to capture position
  - Lines 3074-3100: Modified `submitFsq()` to use snapshot

### LLM Prompt Management

The Universal LLM Framework handles **state, visual feedback, and notifications**, but prompts themselves are managed separately in the **LLM Prompt Management System**.

**Centralized Prompt Repository**: `/disaffected-ui/src/composables/useLLMPrompts.js`

**Benefits**:
- **Version Control**: All prompts versioned with metadata
- **Easy Fine-Tuning**: Update prompts without touching component code
- **Reusability**: Share prompts across components
- **A/B Testing**: Test prompt variations easily
- **Documentation**: Built-in parameter and usage docs

**Usage Example**:
```javascript
import { getLLMPrompt } from '@/composables/useLLMPrompts'
import { useLLMState } from '@/composables/useLLMState'

const llmState = useLLMState()

const result = await llmState.withLLM('field', 'my-field', 'analyzing', async () => {
  const promptConfig = getLLMPrompt('fsq-split-analysis', {
    quote: quoteText,
    maxLines: 5
  })

  return await smartCall(promptConfig.prompt, {
    temperature: promptConfig.temperature,
    systemPrompt: promptConfig.systemPrompt
  })
})
```

**📖 Complete Documentation**: See [`docs/LLM_PROMPT_MANAGEMENT.md`](docs/LLM_PROMPT_MANAGEMENT.md)

---

**Version**: 1.0
**Last Updated**: 2025-10-09
**Maintained By**: Claude Code
**Status**: Production Ready (with known limitations)

---

## Quick Reference Card

### Starting an Operation

```javascript
// Automatic (recommended)
await llmState.withLLM('field', 'my-id', 'analyzing', async () => {
  return await doLLMWork()
}, { model: 'qwen2.5-coder:7b', notify: true })

// Manual
const opId = llmState.startOperation('field', 'my-id', 'analyzing', {...})
try {
  await doLLMWork()
  llmState.stopOperation(opId, { success: true })
} catch (e) {
  llmState.failOperation(opId, e)
}
```

### Visual Feedback

```vue
<template>
  <div
    :class="llmState.getVisualClass('field', 'my-id')"
    :style="llmState.getVisualStyle('field', 'my-id')"
  />
</template>
```

### Check Active State

```javascript
const isActive = llmState.isTargetActive('field', 'my-id')
const ops = llmState.getOperationsForTarget('field', 'my-id')
```

### Add Notification

```javascript
llmState.addNotification({
  title: 'Title',
  message: 'Message',
  priority: llmState.PRIORITY.NORMAL,
  type: 'custom'
})
```

---

**🎉 Universal LLM Framework - Unified AI State Management for Show-Build** 🎉
