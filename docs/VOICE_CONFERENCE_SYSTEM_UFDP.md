# Voice Conference Recording, Transcription & Diarization System
## Universal Framework Documentation Protocol (UFDP) v1.1

**Document Version:** 1.0
**Last Updated:** 2025-10-11
**System Status:** Production-Ready (Diarization: Pending Deployment)
**Maintainer:** Show-Build Development Team

---

## Executive Summary

The Voice Conference System integrates Asterisk PBX, Whisper transcription, and pyannote.audio speaker diarization to provide enterprise-grade conference recording with automated speaker identification and timestamped transcription for the Show-Build broadcast production workflow.

### Key Capabilities
- **Multi-Method Access**: Phone dial-in (PSTN) + browser-based WebRTC audio
- **Automated Recording**: All conferences automatically recorded to WAV format
- **Speaker Diarization**: AI-powered speaker identification and segmentation
- **Transcription Pipeline**: Automatic transcription with speaker labels
- **Episode Integration**: Conference recordings attached to Show-Build episodes

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VOICE CONFERENCE SYSTEM                      │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Participants   │      │   Show-Build     │      │    Asterisk     │
│                  │      │    Frontend      │      │   PBX Server    │
│ Phone Callers    │─────▶│                  │─────▶│  192.168.51.223 │
│ WebRTC Browsers  │      │ VoiceMeetingView │      │  DID: +1-802-   │
│                  │      │                  │      │   221-4885      │
└──────────────────┘      └──────────────────┘      └─────────────────┘
                                   │                         │
                                   │                         │
                          ┌────────▼────────┐       ┌────────▼────────┐
                          │   Show-Build    │       │   ConfBridge    │
                          │     Backend     │       │   Conference    │
                          │  192.168.51.210 │       │   Recording     │
                          │     :8888       │       │                 │
                          └─────────────────┘       └─────────────────┘
                                   │                         │
                                   │                         │
                  ┌────────────────┴──────────────┐         │
                  │                               │         │
         ┌────────▼────────┐            ┌────────▼─────────▼────┐
         │   Diarization   │            │   Whisper Service     │
         │    Service      │            │   (Transcription)     │
         │  pyannote.audio │            │                       │
         │   Port: 5002    │            │   [External Service]  │
         │  [To Be Set Up] │            │                       │
         └─────────────────┘            └───────────────────────┘
                  │                               │
                  └───────────────┬───────────────┘
                                  │
                          ┌───────▼────────┐
                          │   PostgreSQL   │
                          │   Database     │
                          │                │
                          │ • Conferences  │
                          │ • Participants │
                          │ • Transcripts  │
                          │ • Diarization  │
                          └────────────────┘
```

---

## Component Breakdown

### 1. Asterisk PBX Server (192.168.51.223)

**Purpose:** Telephony engine for conference bridging and call management

**Key Features:**
- **ConfBridge**: Multi-party conference rooms with audio mixing
- **AMI (Asterisk Manager Interface)**: Remote control API (Port 5038)
- **Dial-In Number**: +1-802-221-4885 (Flowroute DID)
- **WebRTC Support**: SIP over WebSockets for browser audio
- **Recording**: Automatic WAV recording to `/var/spool/asterisk/monitor/`

**Configuration Files:**
- `/etc/asterisk/extensions.conf` - Dialplan (see `asterisk_conference_dialplan.conf`)
- `/etc/asterisk/confbridge.conf` - Conference bridge settings
- `/etc/asterisk/http.conf` - WebRTC HTTP/WebSocket transport
- `/etc/asterisk/pjsip.conf` - SIP endpoints for WebRTC

**Database Configuration:**
```sql
-- Asterisk config stored in api_configs table
SELECT * FROM api_configs WHERE service = 'asterisk';

-- Expected keys:
-- host: 192.168.51.223
-- amiPort: 5038
-- amiUsername: [AMI username]
-- amiSecret: [AMI password]
-- conferenceContext: conferences
-- recordingsPath: /var/spool/asterisk/monitor
-- dialInNumber: +1-802-221-4885
```

---

### 2. Show-Build Backend (192.168.51.210:8888)

**Purpose:** Conference orchestration, API endpoints, PIN validation

**Key Files:**
- `app/voice_conference_router.py` - FastAPI endpoints for conference management
- `app/services/asterisk_service.py` - Asterisk AMI client and service layer (moved from app root to services/)
- `asterisk_pin_validator.py` - PIN validation script called by Asterisk

**API Endpoints:**

#### `POST /api/voice/conference/create`
Create new conference for an episode

**Request:**
```json
{
  "episode_id": "0245",
  "title": "Interview with Dr. Jane Doe"
}
```

**Response:**
```json
{
  "success": true,
  "conference": {
    "conference_id": "ep-0245-abc123",
    "pin": "123456",
    "dial_in_number": "+1-802-221-4885",
    "webrtc_url": "sip:ep-0245-abc123@192.168.51.223",
    "recording_enabled": true,
    "created_at": "2025-10-11T14:30:00Z",
    "episode_id": "0245",
    "title": "Interview with Dr. Jane Doe",
    "participants": []
  }
}
```

#### `GET /api/voice/conference/{conference_id}`
Get conference details and participant list

**Response:**
```json
{
  "success": true,
  "conference": {
    "conference_id": "ep-0245-abc123",
    "pin": "123456",
    "episode_id": "0245",
    "title": "Interview with Dr. Jane Doe",
    "participants": [
      {
        "participant_id": "p-1",
        "caller_id": "+15551234567",
        "name": null,
        "join_method": "phone",
        "joined_at": "2025-10-11T14:32:00Z"
      },
      {
        "participant_id": "p-2",
        "caller_id": "WebRTC-42",
        "name": "John Producer",
        "join_method": "webrtc",
        "joined_at": "2025-10-11T14:33:00Z"
      }
    ]
  }
}
```

#### `POST /api/voice/conference/{conference_id}/join`
Join conference from browser (WebRTC)

**Request:**
```json
{
  "join_method": "webrtc"
}
```

**Response:**
```json
{
  "success": true,
  "participant_id": "p-3",
  "webrtc_config": {
    "sip_uri": "sip:ep-0245-abc123@192.168.51.223",
    "username": "WebRTC-42",
    "display_name": "John Producer"
  }
}
```

#### `POST /api/voice/conference/{conference_id}/identify`
Identify a participant by name (manual or from voice intro transcription)

**Request:**
```json
{
  "participant_id": "p-1",
  "name": "Dr. Jane Doe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Participant p-1 identified as Dr. Jane Doe"
}
```

#### `POST /api/voice/conference/{conference_id}/end`
End conference and trigger transcription/diarization pipeline

**Response:**
```json
{
  "success": true,
  "conference_id": "ep-0245-abc123",
  "recording_path": "/var/spool/asterisk/monitor/conf-ep-0245-abc123-20251011-143000.wav",
  "message": "Conference ended, recording saved"
}
```

#### `GET /api/voice/conference/`
List all active conferences (optionally filtered by `?episode_id=0245`)

**Response:**
```json
{
  "success": true,
  "conferences": [
    {
      "conference_id": "ep-0245-abc123",
      "episode_id": "0245",
      "title": "Interview with Dr. Jane Doe",
      "created_at": "2025-10-11T14:30:00Z",
      "participant_count": 3
    }
  ]
}
```

---

### 3. Show-Build Frontend (Vue 3)

**Component:** `disaffected-ui/src/views/VoiceMeetingView.vue`

**Features:**
- **Create Conference**: Select episode, generate PIN
- **Display Conference Info**: PIN, dial-in number, WebRTC join button
- **Participant List**: Real-time list with identification status
- **Audio Level Meters**: Visual feedback via `LEDMeter.vue` component
- **Manual Participant Identification**: Dialog to name unidentified callers
- **End Conference**: Trigger recording pipeline

**User Workflow:**
1. Navigate to Voice Meeting view
2. Select episode from dropdown
3. Click "Create Conference" → Generates PIN
4. Share PIN with participants for phone dial-in
5. Click "Join from Browser" for WebRTC participation
6. Monitor participants as they join
7. Manually identify participants if needed
8. Click "End Conference" when complete
9. System automatically processes recording

---

### 4. Speaker Diarization Service (Planned)

**Status:** ⚠️ **Not Yet Deployed** - See `DIARIZATION_SERVICE_REQUEST.md` for deployment spec

**Purpose:** AI-powered speaker identification and segmentation

**Technology:** pyannote.audio 3.1 (HuggingFace model)

**Endpoint:** `POST /diarize`

**Request:**
```json
{
  "audio_path": "/recordings/conf-ep-0245-abc123-20251011-143000.wav",
  "num_speakers": null,
  "min_speakers": 1,
  "max_speakers": 10
}
```

**Response:**
```json
{
  "success": true,
  "audio_duration": 1825.5,
  "num_speakers": 3,
  "segments": [
    {
      "speaker": "SPEAKER_00",
      "start": 0.5,
      "end": 45.2,
      "duration": 44.7
    },
    {
      "speaker": "SPEAKER_01",
      "start": 45.8,
      "end": 120.3,
      "duration": 74.5
    },
    {
      "speaker": "SPEAKER_02",
      "start": 121.0,
      "end": 185.6,
      "duration": 64.6
    }
  ],
  "processing_time": 42.3
}
```

**Integration Point:**
- Called by `trigger_transcription_pipeline()` in `voice_conference_router.py:29`
- Runs after conference ends, before transcription
- Results merged with Whisper transcription to produce speaker-labeled transcript

**Deployment Requirements:**
- Docker container with Python 3.10+, PyTorch, pyannote.audio
- HuggingFace API token (for model download)
- NFS mount access to `/var/spool/asterisk/monitor/`
- 2-4GB RAM, GPU optional but recommended

---

### 5. Transcription Pipeline (Integration)

**Flow:**
```
Conference Ends
    ↓
Recording Saved: /var/spool/asterisk/monitor/conf-{id}-{timestamp}.wav
    ↓
trigger_transcription_pipeline() called
    ↓
┌────────────────────────────┐
│ 1. Diarization Service     │ → Speaker segments with timestamps
│    (pyannote.audio)        │
└────────────────────────────┘
    ↓
┌────────────────────────────┐
│ 2. Whisper Service         │ → Full transcript with timestamps
│    (External)              │
└────────────────────────────┘
    ↓
┌────────────────────────────┐
│ 3. Merge Transcription     │ → Speaker-labeled transcript
│    with Speaker Labels     │
└────────────────────────────┘
    ↓
┌────────────────────────────┐
│ 4. Store in Database       │
│    • conference_transcripts│
│    • speaker_segments      │
└────────────────────────────┘
    ↓
Display in Show-Build UI
```

**Database Schema (Proposed):**

```sql
-- Conference metadata
CREATE TABLE voice_conferences (
    id SERIAL PRIMARY KEY,
    conference_id VARCHAR(50) UNIQUE NOT NULL,
    episode_id VARCHAR(10) REFERENCES episodes(episode_number),
    pin VARCHAR(6) NOT NULL,
    title VARCHAR(255),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    recording_path TEXT,
    status VARCHAR(20) DEFAULT 'active'
);

-- Participants
CREATE TABLE conference_participants (
    id SERIAL PRIMARY KEY,
    conference_id VARCHAR(50) REFERENCES voice_conferences(conference_id),
    participant_id VARCHAR(20) NOT NULL,
    caller_id VARCHAR(50),
    name VARCHAR(255),
    user_id INTEGER REFERENCES users(id),
    join_method VARCHAR(20),
    joined_at TIMESTAMP,
    left_at TIMESTAMP
);

-- Transcription results
CREATE TABLE conference_transcripts (
    id SERIAL PRIMARY KEY,
    conference_id VARCHAR(50) REFERENCES voice_conferences(conference_id),
    full_transcript TEXT,
    whisper_model VARCHAR(50),
    transcribed_at TIMESTAMP DEFAULT NOW(),
    audio_duration FLOAT
);

-- Speaker diarization segments
CREATE TABLE speaker_segments (
    id SERIAL PRIMARY KEY,
    conference_id VARCHAR(50) REFERENCES voice_conferences(conference_id),
    speaker_label VARCHAR(20),
    participant_id VARCHAR(20),
    start_time FLOAT,
    end_time FLOAT,
    duration FLOAT,
    transcript_text TEXT
);
```

---

## Configuration & Setup

### Prerequisites

1. **Asterisk Server**: Running Asterisk 18+ with ConfBridge module
2. **Flowroute DID**: Configured to route to Asterisk server
3. **Network Access**: Show-Build backend can reach Asterisk AMI port (5038)
4. **NFS Mount** (Optional): Shared access to Asterisk recordings directory

### Step 1: Configure Asterisk

**Install Required Modules:**
```bash
# On Asterisk server
asterisk -rx "module load app_confbridge"
asterisk -rx "module load res_http_websocket"
asterisk -rx "module load chan_pjsip"
```

**Deploy Dialplan:**
Copy contents of `asterisk_conference_dialplan.conf` to `/etc/asterisk/extensions.conf`:

```bash
# On Show-Build server
scp asterisk_conference_dialplan.conf root@192.168.51.223:/etc/asterisk/extensions_conference.conf

# On Asterisk server
echo "#include extensions_conference.conf" >> /etc/asterisk/extensions.conf
asterisk -rx "dialplan reload"
```

**Deploy PIN Validator:**
```bash
# On Show-Build server
scp asterisk_pin_validator.py root@192.168.51.223:/usr/local/bin/
ssh root@192.168.51.223 "chmod +x /usr/local/bin/asterisk_pin_validator.py"
ssh root@192.168.51.223 "pip3 install requests"
```

**Configure ConfBridge:**
Add to `/etc/asterisk/confbridge.conf`:

```ini
[default_bridge]
type=bridge
max_members=50
record_conference=yes
record_file=/var/spool/asterisk/monitor/conf-${CONFBRIDGE(bridge,name)}-%Y%m%d-%H%M%S.wav
mixing_interval=20
video_mode=follow_talker

[default_user]
type=user
marked=no
startmuted=no
music_on_hold_when_empty=yes
quiet=no
announce_user_count=yes
announce_user_count_all=yes
announce_only_user=yes
dtmf_passthrough=yes
```

### Step 2: Configure Show-Build Backend

**Add Asterisk Configuration to Database:**

```sql
-- Insert Asterisk service config
INSERT INTO api_configs (service, category, config_key, config_value, is_enabled) VALUES
('asterisk', 'telephony', 'host', '192.168.51.223', true),
('asterisk', 'telephony', 'amiPort', '5038', true),
('asterisk', 'telephony', 'amiUsername', 'your_ami_user', true),
('asterisk', 'telephony', 'amiSecret', 'your_ami_password', true),
('asterisk', 'telephony', 'conferenceContext', 'conferences', true),
('asterisk', 'telephony', 'recordingsPath', '/var/spool/asterisk/monitor', true),
('asterisk', 'telephony', 'dialInNumber', '+1-802-221-4885', true),
('asterisk', 'telephony', 'enabled', 'true', true);
```

**Create AMI User on Asterisk:**

Add to `/etc/asterisk/manager.conf`:

```ini
[showbuild]
secret = your_ami_password
deny=0.0.0.0/0.0.0.0
permit=192.168.51.210/255.255.255.255
read = system,call,log,verbose,command,agent,user,config
write = system,call,log,verbose,command,agent,user,config,originate
```

Reload AMI:
```bash
asterisk -rx "manager reload"
```

### Step 3: Deploy Diarization Service

**Option A: Same Host as Whisper (Recommended)**
- Follow instructions in `DIARIZATION_SERVICE_REQUEST.md`
- Coordinate with team managing Whisper service

**Option B: Standalone Docker Container**

```bash
# On target server
mkdir -p /opt/speaker-diarization
cd /opt/speaker-diarization

# Create Dockerfile
cat > Dockerfile <<'EOF'
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5002

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5002"]
EOF

# Create requirements.txt
cat > requirements.txt <<'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pyannote.audio==3.1.0
torch==2.1.0
python-multipart==0.0.6
EOF

# Copy app.py from DIARIZATION_SERVICE_REQUEST.md example code
# (See document for full application code)

# Build and run
docker build -t speaker-diarization .
docker run -d \
  --name speaker-diarization \
  -p 5002:5002 \
  -v /var/spool/asterisk/monitor:/recordings:ro \
  -e HUGGINGFACE_TOKEN=your_hf_token \
  -e API_KEY=FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY \
  --restart unless-stopped \
  speaker-diarization
```

**Add Diarization Config to Show-Build Database:**

```sql
INSERT INTO api_configs (service, category, config_key, config_value, is_enabled) VALUES
('diarization', 'ai_services', 'url', 'http://[diarization-host]:5002', true),
('diarization', 'ai_services', 'apiKey', 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY', true),
('diarization', 'ai_services', 'timeout', '600', true),
('diarization', 'ai_services', 'enabled', 'true', true);
```

### Step 4: Verify Installation

**Test 1: Asterisk AMI Connection**
```bash
curl -X POST http://192.168.51.210:8888/api/voice/conference/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY" \
  -d '{"episode_id": "0245", "title": "Test Conference"}'
```

**Test 2: Dial-In from Phone**
- Dial +1-802-221-4885
- Enter PIN from Test 1 response
- Verify connection to conference

**Test 3: Diarization Service**
```bash
curl -X POST http://[diarization-host]:5002/diarize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY" \
  -d '{"audio_path": "/recordings/test-audio.wav", "num_speakers": null}'
```

**Test 4: End-to-End Workflow**
1. Create conference via UI
2. Dial in from phone
3. Say "This is [Your Name]" at the beginning
4. Have a brief conversation
5. End conference via UI
6. Check backend logs for transcription pipeline execution
7. Verify recording saved in `/var/spool/asterisk/monitor/`

---

## Usage Guide

### For Producers: Creating a Conference

1. **Navigate to Voice Meeting**
   - Open Show-Build UI at http://192.168.51.210:8091
   - Click "Voice Meeting" in navigation menu

2. **Select Episode**
   - Choose episode from dropdown (e.g., "0245 - October Special")

3. **Create Conference**
   - Click "Create Conference" button
   - System generates 6-digit PIN (e.g., `123456`)

4. **Share Conference Details**
   - **Dial-In Number**: +1-802-221-4885
   - **PIN**: Display PIN prominently for participants
   - **WebRTC**: Send browser link to internal team members

5. **Join from Browser (Optional)**
   - Click "Join from Browser (WebRTC)" for producer participation
   - Grant browser microphone permission when prompted

6. **Monitor Conference**
   - Watch participant list as callers join
   - View audio level meters for active speakers
   - Manually identify participants if needed (click "Identify" button)

7. **End Conference**
   - Click "End Conference" when complete
   - System automatically saves recording and triggers transcription

### For Participants: Joining via Phone

1. **Dial Conference Number**
   - Call +1-802-221-4885

2. **Enter PIN**
   - When prompted, enter 6-digit PIN
   - Press # to confirm

3. **State Your Name**
   - System will ask "Please state your name"
   - Speak clearly: "This is Dr. Jane Doe"
   - This helps with speaker identification

4. **Join Conference**
   - You'll hear "Now joining the conference"
   - Speak naturally - all audio is recorded

5. **DTMF Commands (Optional)**
   - `*1` - Mute/unmute yourself
   - `*4` - Decrease listening volume
   - `*6` - Increase listening volume
   - `*7` - Decrease speaking volume
   - `*9` - Increase speaking volume

### For Guests: Joining via Browser

1. **Receive WebRTC Link**
   - Producer sends browser link (if WebRTC enabled)

2. **Grant Permissions**
   - Browser will request microphone access
   - Click "Allow"

3. **Join Conference**
   - Audio automatically connects
   - Speak clearly for best quality

---

## Speaker Identification Methods

### Method 1: Voice Introduction (Automatic)

**How It Works:**
- Asterisk dialplan prompts caller to state their name
- Records 3-30 second audio clip: `/tmp/conference-intro-{uniqueid}.wav`
- Whisper transcribes introduction: "This is Dr. Jane Doe"
- Backend extracts name via regex: `"(?:this is|my name is|i'm|i am)\s+(.+?)(?:\.|$)"`
- Name automatically associated with participant

**Advantages:**
- Fully automated
- No manual intervention needed
- Works for phone dial-in

**Limitations:**
- Requires clear audio
- Transcription may have errors
- Not applicable for WebRTC joins (no voice prompt)

### Method 2: Manual Identification (UI)

**How It Works:**
- Producer clicks "Identify" button next to unidentified participant
- Dialog prompts for participant name
- Manual entry updates database immediately

**Advantages:**
- 100% accurate
- Works for any join method
- Can fix transcription errors

**Use Cases:**
- WebRTC participants (no voice intro)
- Transcription failed or inaccurate
- Participant didn't understand voice prompt

### Method 3: Speaker Diarization Mapping (Post-Call)

**How It Works:**
- Diarization service labels speakers: `SPEAKER_00`, `SPEAKER_01`, `SPEAKER_02`
- Audio segments mapped to caller IDs by join time correlation
- Producer reviews transcript and maps speaker labels to names

**Advantages:**
- Most accurate for multi-speaker conversations
- Handles overlapping speech
- Provides precise timestamps

**Workflow:**
1. Conference ends, recording processed
2. Diarization outputs speaker segments
3. UI displays: "SPEAKER_00 (joined 14:32, +15551234567): [transcript]"
4. Producer clicks "This is Dr. Jane Doe"
5. All `SPEAKER_00` segments labeled "Dr. Jane Doe"

---

## Troubleshooting

### Issue: Cannot Create Conference

**Symptoms:**
- "Create Conference" button returns error
- Backend logs show AMI connection failures

**Solutions:**
1. **Verify Asterisk Service Status:**
   ```bash
   ssh root@192.168.51.223 "asterisk -rx 'core show version'"
   ```

2. **Check AMI Configuration:**
   ```sql
   SELECT * FROM api_configs WHERE service = 'asterisk';
   ```

3. **Test AMI Connection:**
   ```bash
   telnet 192.168.51.223 5038
   ```
   Expected: Asterisk welcome banner

4. **Verify AMI Credentials:**
   ```bash
   ssh root@192.168.51.223 "asterisk -rx 'manager show users'"
   ```

### Issue: Phone Dial-In Fails

**Symptoms:**
- Call to +1-802-221-4885 doesn't connect
- Gets busy signal or "number not in service"

**Solutions:**
1. **Check DID Routing (Flowroute):**
   - Log in to Flowroute dashboard
   - Verify DID routes to Asterisk server IP

2. **Verify Asterisk Dialplan:**
   ```bash
   ssh root@192.168.51.223 "asterisk -rx 'dialplan show from-flowroute'"
   ```

3. **Check Asterisk Logs:**
   ```bash
   ssh root@192.168.51.223 "tail -f /var/log/asterisk/full"
   ```

### Issue: PIN Validation Fails

**Symptoms:**
- Caller enters PIN but hears "Invalid PIN"
- Valid conference exists in database

**Solutions:**
1. **Verify PIN Validator Script:**
   ```bash
   ssh root@192.168.51.223 "python3 /usr/local/bin/asterisk_pin_validator.py 123456"
   ```
   Expected output: `valid` or `invalid`

2. **Check Show-Build Backend Connectivity:**
   ```bash
   ssh root@192.168.51.223 "curl -H 'X-API-Key: FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY' http://192.168.51.210:8888/api/voice/conference/"
   ```

3. **Review Asterisk Dialplan Logs:**
   ```bash
   ssh root@192.168.51.223 "asterisk -rx 'core set verbose 5'"
   # Make test call
   ssh root@192.168.51.223 "asterisk -rx 'core set verbose 0'"
   ```

### Issue: WebRTC Audio Not Working

**Symptoms:**
- "Join from Browser" button does nothing
- Microphone not detected

**Solutions:**
1. **Check Browser Permissions:**
   - Open browser settings
   - Verify microphone access granted for Show-Build domain

2. **Verify HTTPS:**
   - WebRTC requires HTTPS or localhost
   - Check SSL certificate validity

3. **Test SIP Configuration:**
   ```bash
   ssh root@192.168.51.223 "asterisk -rx 'pjsip show endpoints'"
   ```

4. **Check WebRTC Transport:**
   ```bash
   ssh root@192.168.51.223 "asterisk -rx 'http show status'"
   ```

### Issue: Recording Not Saved

**Symptoms:**
- Conference ends but no recording file created
- `recording_path` is null

**Solutions:**
1. **Verify ConfBridge Recording Setting:**
   ```bash
   ssh root@192.168.51.223 "asterisk -rx 'confbridge show profile default_bridge'"
   ```
   Expected: `record_conference=yes`

2. **Check Permissions:**
   ```bash
   ssh root@192.168.51.223 "ls -la /var/spool/asterisk/monitor/"
   ssh root@192.168.51.223 "sudo chown -R asterisk:asterisk /var/spool/asterisk/monitor/"
   ```

3. **Verify Disk Space:**
   ```bash
   ssh root@192.168.51.223 "df -h /var/spool/asterisk"
   ```

### Issue: Diarization Service Unreachable

**Symptoms:**
- Conference ends but no speaker segments generated
- Backend logs show "Diarization service not enabled" or connection errors

**Solutions:**
1. **Verify Diarization Service Status:**
   ```bash
   curl http://[diarization-host]:5002/health
   ```

2. **Check Database Configuration:**
   ```sql
   SELECT * FROM api_configs WHERE service = 'diarization';
   ```

3. **Test Diarization Endpoint:**
   ```bash
   curl -X POST http://[diarization-host]:5002/diarize \
     -H "Content-Type: application/json" \
     -H "X-API-Key: FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY" \
     -d '{"audio_path": "/recordings/test.wav", "num_speakers": null}'
   ```

4. **Review Show-Build Logs:**
   ```bash
   docker logs show-build-server | grep -i diarization
   ```

---

## Performance & Scaling

### Resource Usage

**Asterisk Server:**
- **CPU**: ~5-10% per active conference (10 participants)
- **RAM**: ~50MB per conference
- **Bandwidth**: ~64kbps per participant (G.711 codec)
- **Disk**: ~10MB per minute of recording (WAV, 16kHz mono)

**Diarization Service:**
- **CPU**: 100% for duration of processing (single-threaded)
- **RAM**: 2-4GB peak during model inference
- **GPU**: Optional, reduces processing time by 5-10x
- **Processing Speed**: ~0.2x realtime (10 minutes of audio = 50 minutes processing)

**Database:**
- **Storage**: ~1KB per participant record
- **Storage**: ~50KB per minute of transcript
- **Queries**: Low frequency, OLTP workload

### Scaling Recommendations

**Current Capacity:**
- **Concurrent Conferences**: 5-10 (Asterisk capacity)
- **Max Participants per Conference**: 50 (ConfBridge limit)
- **Daily Recordings**: 10-20 hours

**Scaling Strategies:**

1. **Horizontal Asterisk Scaling:**
   - Deploy multiple Asterisk servers
   - Load balance via SIP proxy (Kamailio, OpenSIPS)
   - Use shared database for conference state

2. **Diarization Queue:**
   - Implement Celery task queue for async processing
   - Multiple diarization workers on separate hosts
   - Priority queue: urgent vs. batch processing

3. **Recording Storage:**
   - Archive recordings to S3/object storage after 30 days
   - Implement retention policy (delete after 1 year)
   - Compress recordings (FLAC for lossless, Opus for lossy)

4. **Database Optimization:**
   - Index on `conference_id`, `episode_id`, `created_at`
   - Partition `speaker_segments` by date
   - Archive old conferences to separate table

---

## Security Considerations

### PIN Security

**Current Implementation:**
- **PIN Format**: 6-digit numeric (000000-999999)
- **Entropy**: ~20 bits (1,000,000 possible PINs)
- **Brute Force**: 1,000,000 attempts to guarantee success

**Mitigations:**
1. **Rate Limiting**: Max 3 PIN attempts per call (see `asterisk_conference_dialplan.conf:46`)
2. **Short Lifespan**: Conference PINs only valid during active conference
3. **Monitoring**: Log all PIN validation attempts

**Recommendations:**
- Implement exponential backoff for repeated failures from same caller ID
- Alert on >10 failed PIN attempts within 1 hour
- Consider alphanumeric PINs for increased entropy

### Audio Recording Compliance

**Legal Requirements:**
- **Two-Party Consent**: Check state/country recording laws
- **Disclosure**: Inform participants that call is recorded
- **Storage**: Encrypt recordings at rest
- **Access Control**: Restrict recording access to authorized users only

**Current Implementation:**
- Audio prompt: "This call will be recorded" (add to dialplan)
- File permissions: Asterisk user only (`chmod 600`)
- Database RBAC: Episode-level access control

**Recommendations:**
- Add explicit consent flow (press 1 to accept recording)
- Implement audit log for recording access
- Auto-delete recordings after 90 days (configurable retention)
- Encrypt recordings with AES-256 (GPG or dm-crypt)

### API Authentication

**Current Implementation:**
- **API Key**: `X-API-Key` header for all endpoints
- **Single Key**: Shared across all services
- **No Expiration**: Key valid indefinitely

**Recommendations:**
- Implement JWT tokens for user-specific access
- Rotate API key quarterly
- Implement per-service API keys (Asterisk, Diarization, Whisper)
- Add request signing for critical operations

---

## Future Enhancements

### Phase 1: Core Features (Current)
- ✅ Asterisk conference creation and management
- ✅ Phone dial-in via PSTN
- ✅ WebRTC browser audio (planned)
- ✅ Participant tracking
- ⏳ Speaker diarization (deployment pending)
- ⏳ Whisper transcription integration

### Phase 2: Enhanced Identification (Q1 2026)
- Voice introduction transcription
- Automatic name extraction from intro
- Speaker-to-caller-ID correlation
- Post-call speaker mapping UI

### Phase 3: Real-Time Features (Q2 2026)
- Live transcription during call
- Real-time speaker identification
- Live captions in VoiceMeetingView
- WebSocket updates for participant list

### Phase 4: Advanced Analysis (Q3 2026)
- Sentiment analysis per speaker
- Topic extraction and timestamps
- Action item detection
- Automated meeting minutes

### Phase 5: Integration (Q4 2026)
- Export transcripts to episode rundowns
- Insert FSQ quotes directly from transcript
- Speaker voice cloning for XTTS
- Conference recording as episode audio source

---

## API Reference

### Authentication

All API endpoints require authentication via one of:
- **API Key**: `X-API-Key: FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY`
- **JWT Token**: `Authorization: Bearer {token}`

### Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/voice/conference/create` | Create new conference |
| GET | `/api/voice/conference/{id}` | Get conference details |
| POST | `/api/voice/conference/{id}/join` | Join via WebRTC |
| POST | `/api/voice/conference/{id}/identify` | Identify participant |
| POST | `/api/voice/conference/{id}/end` | End conference |
| GET | `/api/voice/conference/` | List active conferences |

### Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing or invalid API key)
- `404` - Not Found (conference doesn't exist)
- `500` - Internal Server Error (check logs)
- `503` - Service Unavailable (Asterisk unreachable)

---

## Monitoring & Logging

### Backend Logs

**View Real-Time Logs:**
```bash
docker logs -f show-build-server | grep -i conference
```

**Key Log Messages:**
- `Conference created: ep-0245-abc123` - Conference created successfully
- `Added participant p-1 (+15551234567)` - Participant joined
- `Identified participant p-1 as Dr. Jane Doe` - Manual identification
- `Conference ended: ep-0245-abc123` - Conference terminated
- `Starting transcription pipeline` - Post-call processing started
- `Diarization complete: 3 speakers, 42 segments` - Diarization succeeded

### Asterisk Logs

**View Call Logs:**
```bash
ssh root@192.168.51.223 "tail -f /var/log/asterisk/full"
```

**Enable Verbose Logging:**
```bash
ssh root@192.168.51.223 "asterisk -rx 'core set verbose 5'"
```

### Metrics to Monitor

1. **Conference Creation Rate**: Conferences created per day
2. **Participant Count**: Average participants per conference
3. **Duration**: Average conference length
4. **Recording Size**: Total storage consumed
5. **Transcription Success Rate**: Percentage of recordings successfully transcribed
6. **Diarization Accuracy**: Manual corrections per transcript

---

## Support & Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Review conference logs for errors
- Check disk space on Asterisk server
- Archive completed transcripts

**Monthly:**
- Rotate API keys
- Update HuggingFace models (diarization)
- Review and delete old recordings

**Quarterly:**
- Asterisk security updates
- Review participant identification accuracy
- Analyze usage patterns for scaling decisions

### Contact Information

**Technical Issues:**
- Check `docs/INDEX.md` for complete documentation index
- Review `docs/LLM_GENERATOR_TROUBLESHOOTING.md` for AI service debugging

**System Status:**
- Asterisk: http://192.168.51.223 (if web interface enabled)
- Show-Build Backend: http://192.168.51.210:8888/health
- Diarization Service: http://[host]:5002/health

---

## Changelog

### Version 1.0 (2025-10-11)
- Initial UFDP documentation
- Complete system architecture documented
- API endpoints reference created
- Configuration and setup guide completed
- Troubleshooting section added
- Security considerations documented

---

## Appendix A: Asterisk Dialplan Reference

See `asterisk_conference_dialplan.conf` for complete dialplan implementation.

**Key Contexts:**
- `[from-flowroute]` - Incoming call handler
- `[conference-entry]` - PIN entry system
- `[validate-pin]` - PIN validation via Show-Build API
- `[join-conference]` - Conference bridge entry

## Appendix B: Database Schema

See "Transcription Pipeline" section for proposed database tables.

## Appendix C: Diarization Service Deployment

See `DIARIZATION_SERVICE_REQUEST.md` for complete deployment specification.

---

**End of Documentation**
