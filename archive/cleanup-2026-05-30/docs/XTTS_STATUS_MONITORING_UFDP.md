# XTTS Status Monitoring Integration - UFDP

**Feature**: Real-time XTTS service status monitoring in Show-Build UI
**Status**: ✅ Implemented
**Last Updated**: 2025-10-03

## Overview

Show-Build now monitors the XTTS (Text-to-Speech) service in real-time and displays its status in the top toolbar status grid alongside backend and database indicators.

## XTTS Service Details

### Service Location
- **Host**: `http://192.168.51.197:5001`
- **Container**: Docker container running Coqui-AI XTTS v2
- **Model**: `tts_models/multilingual/multi-dataset/xtts_v2`

### Available Endpoints

#### Health Check (Used for Status Monitoring)
```
GET http://192.168.51.197:5001/health
```
**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "cuda_available": true,
  "cuda_device_count": 1,
  "cuda_device_name": "NVIDIA GeForce RTX 3060"
}
```

#### Speakers List
```
GET http://192.168.51.197:5001/speakers
```
**Response:**
```json
{
  "speakers": [
    "Ana Florence",
    "Andrew Chipper",
    "Gracie Wise",
    "Viktor Eka",
    "Daisy Studious",
    "Claribel Dervla"
  ]
}
```

#### TTS Synthesis (OpenAI-Compatible)
```
POST http://192.168.51.197:5001/v1/audio/speech
Content-Type: application/json

{
  "input": "Text to synthesize",
  "model": "tts-1",
  "voice": "alloy",
  "speed": 1.0
}
```

#### TTS Synthesis (Native XTTS)
```
POST http://192.168.51.197:5001/synthesize
Content-Type: application/x-www-form-urlencoded

text=Text+to+synthesize&speaker_id=Ana+Florence&language=en
```

#### API Info
```
GET http://192.168.51.197:5001/info
```
Returns comprehensive endpoint documentation.

## Show-Build Integration

### Backend Implementation

**File**: `/mnt/process/show-build/app/xtts_router.py`

The XTTS router provides status checking and configuration retrieval:

```python
@router.get("/api/xtts/status", response_model=XTTSStatusResponse)
async def get_xtts_status(current_user: dict = Depends(get_current_user_or_key)):
    """
    Check XTTS service connectivity and status

    Tests connectivity by calling the /health endpoint which returns
    model status, CUDA availability, and device information.
    """
```

**Status Check Process:**
1. Load XTTS configuration from `api_configs.json`
2. Verify host is configured and service is enabled
3. Call XTTS `/health` endpoint with 5-second timeout
4. Verify `status == "healthy"` and `model_loaded == true`
5. Optionally fetch speaker count from `/speakers`
6. Return comprehensive status response

**Response Schema:**
```python
{
  "connected": bool,              # True if service is healthy
  "host": str,                    # XTTS service URL
  "speakers_available": int,      # Number of available speakers (optional)
  "quota_remaining": int,         # Always null for XTTS (no quota)
  "error_message": str,           # Error details if not connected
  "service_version": str          # "XTTS v2"
}
```

### Frontend Implementation

**File**: `/mnt/process/show-build/disaffected-ui/src/App.vue`

**Status Monitoring:**
```javascript
const xttsStatus = ref('disconnected')

const checkXttsStatus = async () => {
  try {
    const response = await axios.get('/api/xtts/status', { timeout: 5000 })
    if (response.data.connected) {
      if (response.data.quota_remaining !== undefined &&
          response.data.quota_remaining < 100) {
        xttsStatus.value = 'depleted'
      } else {
        xttsStatus.value = 'connected'
      }
    } else {
      xttsStatus.value = 'disconnected'
    }
  } catch (error) {
    xttsStatus.value = 'disconnected'
  }
}

// Check on mount and every 30 seconds
onMounted(async () => {
  await checkXttsStatus()
  setInterval(checkXttsStatus, 30000)
})
```

**UI Display:**
```vue
<div class="grid-cell" :class="{
  'xtts-connected': xttsStatus === 'connected',
  'xtts-depleted': xttsStatus === 'depleted',
  'xtts-disconnected': xttsStatus === 'disconnected'
}">
  XTTS
</div>
```

**Status Colors:**
- 🟢 **Green** (`xtts-connected`): Service healthy, model loaded
- 🟡 **Yellow** (`xtts-depleted`): Service connected but quota low (not used for XTTS)
- 🔴 **Red** (`xtts-disconnected`): Service unreachable or unhealthy

### Configuration Storage

**File**: `/mnt/process/show-build/app/storage/api_configs.json`

XTTS configuration is stored in the encrypted API configuration:
```json
{
  "preproduction": {
    "ai_services": {
      "xtts": {
        "host": "http://192.168.51.197:5001",
        "endpoint": "/v1/audio/speech",
        "language": "en",
        "speed": 1.0,
        "speaker": "",
        "enabled": false
      }
    }
  }
}
```

**Configuration Management:**
- Encrypted using Fernet symmetric encryption
- Encryption key stored in `app/storage/encryption.key`
- Managed by `APIConfigManager` in `api_config.py`
- Can be updated via Settings UI (future implementation)

## Monitoring & Health

### Status Check Intervals
- **Frontend**: Checks every 30 seconds
- **Timeout**: 5 seconds per check
- **Retries**: None (single check per interval)

### Error Handling
- Connection timeout → `disconnected`
- Connection refused → `disconnected`
- HTTP errors → `disconnected`
- Model not loaded → `disconnected`
- Service disabled in config → `disconnected` with message

### Logging
Backend logs all XTTS status checks:
```
INFO: XTTS service healthy at http://192.168.51.197:5001
WARNING: XTTS service unhealthy: status=unhealthy, model_loaded=False
ERROR: XTTS connection timeout to http://192.168.51.197:5001/health
```

## Voice Mapping

OpenAI-compatible voice names map to XTTS speakers:

| OpenAI Voice | XTTS Speaker      |
|--------------|-------------------|
| `alloy`      | Ana Florence      |
| `echo`       | Andrew Chipper    |
| `fable`      | Gracie Wise       |
| `onyx`       | Viktor Eka        |
| `nova`       | Daisy Studious    |
| `shimmer`    | Claribel Dervla   |
| `default`    | Ana Florence      |

## Testing

### Manual Status Check
```bash
# Check backend endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8888/api/xtts/status

# Check XTTS service directly
curl http://192.168.51.197:5001/health
curl http://192.168.51.197:5001/speakers
```

### Expected Behavior
1. Status indicator should appear in top toolbar (4th position)
2. Initial color should be red (disconnected) until first check completes
3. After 5 seconds, should turn green if XTTS is healthy
4. Status should update every 30 seconds
5. Disconnected services should show red immediately

## Troubleshooting

### XTTS Shows Red (Disconnected)

**Check XTTS service is running:**
```bash
curl http://192.168.51.197:5001/health
```

**Check Show-Build can reach XTTS:**
```bash
docker exec show-build-server curl http://192.168.51.197:5001/health
```

**Check configuration:**
```bash
docker exec show-build-server cat /app/storage/api_configs.json | grep -A 8 '"xtts"'
```

**Enable XTTS in configuration:**
1. Edit `app/storage/api_configs.json`
2. Set `"enabled": true` in XTTS config
3. Restart Show-Build server

### Status Not Updating

**Check browser console:**
```javascript
// Should see request every 30 seconds
GET http://localhost:8888/api/xtts/status
```

**Check backend logs:**
```bash
docker logs show-build-server | grep -i xtts
```

### Connection Timeout

**Increase timeout** in `App.vue`:
```javascript
const response = await axios.get('/api/xtts/status', { timeout: 10000 })
```

## Future Enhancements

- [ ] Add speaker count display on hover
- [ ] Add detailed error messages in UI tooltip
- [ ] Add "Enable XTTS" button in status grid
- [ ] Add XTTS configuration UI in Settings
- [ ] Add voice sample testing interface
- [ ] Add synthesis queue monitoring
- [ ] Add CUDA utilization metrics

## Related Documentation

- [API Configuration Management](docs/API_CONFIG_MANAGEMENT.md)
- [Settings System](docs/SETTINGS_SYSTEM.md)
- [Status Monitoring Architecture](docs/STATUS_MONITORING.md)

## Change Log

**2025-10-03**: Initial implementation
- Created XTTS status router
- Added frontend status monitoring
- Integrated with status grid UI
- Documented all endpoints and configuration
