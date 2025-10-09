# Progressive Health Check Loading (UFDP)

**Universal Frontend Design Pattern for Fast Application Initialization**

## Problem Statement

Health checks that sequentially test multiple services (Database, Ollama, Redis, Celery, NFS, XTTS) can take 5-10 seconds when services are slow or timing out. This creates a poor user experience on page load:

- All status indicators show red initially (alarming)
- User cannot interact with application until all services checked
- Slow secondary services (Ollama, XTTS) block critical services (DB, Backend)

## Solution: Progressive Loading

**Priority-Based Health Checks** - Check and display critical services immediately, then load secondary services in background.

### Service Priority Levels

**Critical (Phase 1)** - Required for application to function:
- `BACK` (Backend API status)
- `DB1` (PostgreSQL database)

**Secondary (Phase 2)** - Nice to have, non-blocking:
- `OLLAMA` (Local LLM inference)
- `REDIS` (Message broker)
- `CELERY` (Background workers)
- `NFS` (Network file storage)
- `XTTS` (Text-to-speech service)

## Implementation

### Frontend: Progressive Health Check

**Location**: `disaffected-ui/src/composables/useSystemHealth.js`

```javascript
/**
 * Progressive health check - checks critical services first
 */
const fetchHealthProgressive = async () => {
  isLoading.value = true
  lastError.value = null

  // Phase 1: Check backend + database (critical services)
  try {
    const response = await axios.get('/health/critical', { timeout: 3000 })

    health.value.status = response.data.status
    health.value.timestamp = response.data.timestamp
    health.value.services.database = response.data.services.database

    console.log('✅ Critical services (BACK, DB) loaded')
  } catch (error) {
    console.error('Critical health check failed:', error)
    if (health.value.timestamp === null) {
      // First check - keep as unknown
      return
    }
  }

  // Phase 2: Check remaining services in background (non-blocking)
  setTimeout(async () => {
    try {
      const response = await axios.get('/health/secondary', { timeout: 5000 })

      // Update secondary services
      if (response.data.services) {
        health.value.services = {
          ...health.value.services,
          ...response.data.services
        }
      }

      console.log('✅ Secondary services (Ollama, Redis, Celery, etc.) loaded')
    } catch (error) {
      console.error('Secondary health check failed:', error)
    } finally {
      isLoading.value = false
    }
  }, 100) // Small delay to let UI update first
}
```

### Backend: Split Health Endpoints

**Location**: `app/main.py`

#### Original Endpoint (Fallback)
```python
@app.get("/health")
async def health_check():
    # Checks ALL services sequentially (slow)
    # Returns complete health status
    ...
```

#### Critical Services Endpoint (Fast)
```python
@app.get("/health/critical")
async def health_check_critical():
    # Only checks: Backend status + Database
    # Returns in <1 second
    ...
```

#### Secondary Services Endpoint (Background)
```python
@app.get("/health/secondary")
async def health_check_secondary():
    # Checks: Ollama, Redis, Celery, NFS, XTTS
    # Can take 2-5 seconds, runs in background
    ...
```

### Timeout Optimization

Reduced timeouts for faster failure detection:

| Service | Old Timeout | New Timeout | Reason |
|---------|-------------|-------------|--------|
| Ollama HTTP | 5.0s | 2.0s | Health check only needs quick ping |
| XTTS HTTP | 5.0s | 2.0s | Health check only needs quick ping |
| Redis Socket | 5.0s | 2.0s | Local network should be fast |

**File**: `app/main.py` lines 375, 430-431, 567

## User Experience Flow

### Before (Sequential Loading)
```
[Page Load]
  ↓
[All indicators RED] ← Alarming!
  ↓
Wait 7-10 seconds... ← Frustrating!
  ↓
[All indicators turn GREEN]
  ↓
User can interact
```

### After (Progressive Loading)
```
[Page Load]
  ↓
[Initialization overlay: "Initializing status check..."]
  ↓
<1 second: DB + Backend check
  ↓
[BACK = GREEN, DB1 = GREEN] ← User can proceed!
[Overlay fades out]
  ↓
2-5 seconds in background...
  ↓
[OLLAMA/REDIS/CELERY/etc. turn GREEN]
```

## Initialization Overlay

Shows during initial critical health check to prevent red indicator flash.

**Location**: `disaffected-ui/src/components/InitializationOverlay.vue`

**Features**:
- 75% dark background with 8px blur
- Spinner + "Initializing status check..." message
- Small subtext: "If this is happening frequently, please let Kevin know."
- Auto-hides when `health.status !== 'unknown'` (critical services loaded)
- Failsafe: Auto-hides after 5 seconds even if check fails

**Trigger Logic**:
- Shows immediately on mount (`show = true`)
- Hides 300ms after critical services respond
- Never blocks user - just provides visual feedback

## Status Indicator State Logic

**Location**: `disaffected-ui/src/App.vue`

### State Classes

Each indicator has 3 possible states:

| State | Class | Color | Meaning |
|-------|-------|-------|---------|
| Unknown | `*-unknown` | Gray (#757575) | Checking... |
| Connected | `*-connected` | Green (#4CAF50) | Healthy |
| Error | `*-disconnected` | Red (#F44336) | Failed |

**Critical Fix**: Indicators now only show RED on actual errors, not on initial unknown state.

### Backend Indicator
```vue
<div class="grid-cell" :class="{
  'backend-connected': health.status === 'healthy',
  'backend-disconnected': health.status === 'error',
  'backend-unknown': health.status === 'unknown'
}">
  BACK
</div>
```

### Database Indicator
```vue
<div class="grid-cell" :class="{
  'db-connected': health.services?.database === 'connected',
  'db-disconnected': health.services?.database === 'error' || ...,
  'db-unknown': health.services?.database === 'unknown' || !health.services?.database
}">
  DB1
</div>
```

## Benefits

### Performance
- **Critical services light up in <1 second** (was 7-10 seconds)
- **Non-blocking UI** - user can start working immediately
- **Parallel loading** - secondary services load while user works

### User Experience
- **No red flash** - initialization overlay prevents alarming indicators
- **Clear feedback** - overlay explains what's happening
- **Progressive disclosure** - see critical status first, details follow
- **Error reporting** - subtext encourages reporting frequent issues

### Reliability
- **Timeout protection** - faster timeouts prevent hanging
- **Graceful degradation** - secondary service failures don't block app
- **Failsafe overlay** - auto-hides even if health check fails completely

## Configuration

### Adjust Timeouts

Edit `app/main.py`:

```python
# Ollama timeout (line 375)
async with httpx.AsyncClient(timeout=2.0) as client:

# Redis timeout (lines 430-431)
socket_connect_timeout=2,
socket_timeout=2,

# XTTS timeout (line 567)
async with httpx.AsyncClient(timeout=2.0) as client:
```

### Adjust Overlay Duration

Edit `disaffected-ui/src/components/InitializationOverlay.vue`:

```javascript
// Hide 300ms after critical services load (line 10)
setTimeout(() => {
  show.value = false
}, 300)  // ← Adjust this value

// Failsafe timeout (line 37)
setTimeout(() => {
  if (show.value) {
    show.value = false
  }
}, 5000)  // ← Adjust this value
```

### Adjust Phase 2 Delay

Edit `disaffected-ui/src/composables/useSystemHealth.js`:

```javascript
// Delay before checking secondary services (line 215)
setTimeout(async () => {
  // Check Ollama, Redis, etc.
}, 100)  // ← Adjust this value
```

## Troubleshooting

### Overlay stays visible too long
- Check network tab - is `/health/critical` responding?
- Check backend logs - is database connection failing?
- Verify backend container is healthy: `docker ps`

### Indicators still flash red
- Check `App.vue` status indicator logic
- Verify `*-unknown` CSS classes exist
- Check console for health check errors

### Secondary services never load
- Check `/health/secondary` endpoint response
- Verify Ollama/Redis/Celery are accessible
- Check backend logs for timeout errors

### Health check still slow
- Reduce timeouts further in `main.py`
- Check if any service is hanging (use backend logs)
- Consider disabling slow services in config

## Future Enhancements

Potential improvements:

- **WebSocket health updates** - Real-time status changes without polling
- **Service-specific retry logic** - Auto-retry failed secondary services
- **Configurable polling intervals** - Faster for critical, slower for secondary
- **Health history** - Track uptime/downtime over time
- **User preferences** - Let user choose which services to monitor

---

**Document Version**: 1.0
**Last Updated**: 2025-01-07
**Status**: Implemented
