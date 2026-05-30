# NFS Infrastructure for Show-Build Distributed Processing

> **📖 About This Document**
>
> This is **technical infrastructure documentation** for the Network File System (NFS) setup that enables distributed media processing in Show-Build. This document explains how workers on remote machines (kairo, proxima) access episode files stored on the central server (whisper) without duplicating data.
>
> **If you're looking to:**
> - **Understand why we use NFS** → See [Section 1: Overview](#1-overview)
> - **Set up NFS from scratch** → See [Section 3: Installation](#3-installation)
> - **Add a new worker machine** → See [Section 4: Client Configuration](#4-client-configuration)
> - **Troubleshoot NFS issues** → See [Section 7: Troubleshooting](#7-troubleshooting)
> - **Understand security** → See [Section 6: Security](#6-security)
>
> **UFDP Format**: This document follows the Unified Feature Documentation Protocol with hierarchical section indexing.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Installation & Configuration](#3-installation--configuration)
4. [Client Configuration](#4-client-configuration)
5. [Docker Integration](#5-docker-integration)
6. [Security](#6-security)
7. [Troubleshooting](#7-troubleshooting)
8. [Performance Tuning](#8-performance-tuning)
9. [Monitoring](#9-monitoring)

---

## 1. Overview

### 1.1 What is NFS?

**Network File System (NFS)** is a distributed file system protocol that allows client machines to access files over a network as if they were on local storage. Originally developed by Sun Microsystems in 1984, it's the industry standard for shared storage in Unix/Linux environments.

### 1.2 Why NFS for Show-Build?

**Problem Statement:**
- Whisper (192.168.51.197) stores all episode data in `/mnt/sync/disaffected/episodes/`
- Celery workers on kairo (192.168.51.197) and proxima need to read video files and write processed outputs
- Workers are dockerized and shouldn't have redundant copies of 100GB+ of media files

**Solution: NFS provides:**
1. **Single Source of Truth** - All episode data lives on whisper's `/mnt/sync` physical disk
2. **Zero Duplication** - Workers mount the same directory over the network
3. **Atomic Operations** - FFmpeg writes directly to final location, no rsync needed
4. **Transparent Access** - Docker containers see `/home/episodes` as a normal directory
5. **Scalability** - Add new workers by just mounting the NFS share

### 1.3 Alternative Approaches (Why Not These?)

| Approach | Why We Rejected It |
|----------|-------------------|
| **rsync** | Duplicates data across machines, wastes bandwidth, complex state management |
| **Samba/CIFS** | Windows-oriented protocol, slower than NFS on Linux, more overhead |
| **Object Storage (S3)** | Requires API calls for every operation, ffmpeg can't write directly |
| **Syncthing** | Bidirectional sync delays, conflicts, not designed for this use case |
| **Local storage only** | Requires copying files before/after processing, defeats purpose of distributed system |

---

## 2. Architecture

### 2.1 NFS Roles in Show-Build

```
┌─────────────────────────────────────────────────────────────────┐
│                         WHISPER (NFS Server)                     │
│                         192.168.51.197                           │
│                                                                  │
│  ┌──────────────────┐         ┌─────────────────────────────┐  │
│  │   /mnt/sync      │         │   NFS Server Process        │  │
│  │   (Physical      │◄────────│   - Exports /mnt/sync       │  │
│  │    Disk /dev/sdb)│         │   - Port 2049               │  │
│  │                  │         │   - Access: 192.168.51.0/24 │  │
│  └──────────────────┘         └─────────────────────────────┘  │
│         │                                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │
          │ NFS Protocol (TCP 2049)
          │
          ├──────────────────────────┬────────────────────────────┐
          │                          │                            │
          ▼                          ▼                            ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  KAIRO (NFS Client) │    │ PROXIMA (NFS Client)│    │  FUTURE (NFS Client)│
│  192.168.51.197     │    │  192.168.51.XXX     │    │  192.168.51.XXX     │
│                     │    │                     │    │                     │
│  /mnt/sync ────┐    │    │  /mnt/sync ────┐    │    │  /mnt/sync ────┐    │
│  (NFS Mount)   │    │    │  (NFS Mount)   │    │    │  (NFS Mount)   │    │
│                │    │    │                │    │    │                │    │
│  Docker:       │    │    │  Docker:       │    │    │  Docker:       │    │
│  ┌───────────┐ │    │    │  ┌───────────┐ │    │    │  ┌───────────┐ │    │
│  │  Celery   │ │    │    │  │  Celery   │ │    │    │  │  Celery   │ │    │
│  │  Worker   │ │    │    │  │  Worker   │ │    │    │  │  Worker   │ │    │
│  │           │ │    │    │  │           │ │    │    │  │           │ │    │
│  │  Volume:  │ │    │    │  │  Volume:  │ │    │    │  │  Volume:  │ │    │
│  │  /mnt/sync│◄┼────┘    │  │  /mnt/sync│◄┼────┘    │  │  /mnt/sync│◄┼────┘
│  │  ↓        │ │         │  │  ↓        │ │         │  │  ↓        │ │
│  │  /home/   │ │         │  │  /home/   │ │         │  │  /home/   │ │
│  │  episodes │ │         │  │  episodes │ │         │  │  episodes │ │
│  └───────────┘ │         │  └───────────┘ │         │  └───────────┘ │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

### 2.2 Data Flow

**Scenario: User uploads SOT video for processing**

```
1. USER (Browser)
   │
   │ HTTP POST /api/sot/upload
   │ (video file, episode="0245", slug="interview-smith")
   ▼
2. WHISPER (FastAPI Server)
   │
   ├─ Saves to /tmp/sot_uploads/0245_interview-smith_video.mp4
   │
   ├─ Submits Celery task to Redis queue:
   │  {
   │    "task": "process_sot_video",
   │    "args": ["/tmp/sot_uploads/0245_interview-smith_video.mp4",
   │             "0245", "interview-smith"],
   │    "queue": "media"
   │  }
   │
   └─ Returns task_id to user

3. REDIS (farmhouse:6379)
   │
   │ Task queued in "media" queue
   │
   └─ BLPOP operation waits for worker

4. KAIRO (Celery Worker - polls Redis)
   │
   ├─ Receives task from Redis
   │
   ├─ Reads input: /tmp/sot_uploads/0245_interview-smith_video.mp4
   │  (This is LOCAL to whisper, NOT accessible from kairo)
   │
   ├─ **PROBLEM WITH OLD DESIGN** ❌
   │  Worker can't read whisper's /tmp directory!
   │
   └─ **SOLUTION WITH NFS** ✅
      │
      ├─ Input should be on NFS: /mnt/sync/temp/uploads/
      │  (Both whisper and kairo can access)
      │
      ├─ Process with FFmpeg:
      │  - Generate thumbnail
      │  - Extract audio
      │  - Trim/process video
      │
      └─ Write outputs to NFS:
         /mnt/sync/disaffected/episodes/0245/assets/sots/
         ├── interview-smith-thumb.jpg
         ├── interview-smith.mp3
         └── interview-smith.mp4

5. WHISPER (Receives completion via Redis result backend)
   │
   ├─ Task result stored in Redis
   │
   ├─ Frontend polls GET /api/sot/tasks/{task_id}/status
   │
   └─ Returns file paths to user:
      {
        "thumbnail_path": "0245/assets/sots/interview-smith-thumb.jpg",
        "audio_path": "0245/assets/sots/interview-smith.mp3",
        "video_path": "0245/assets/sots/interview-smith.mp4",
        "duration": 125.4
      }
```

### 2.3 Directory Structure (NFS Shared)

```
/mnt/sync/                          (NFS exported from whisper)
├── disaffected/
│   └── episodes/                   (Mounted as /home/episodes in containers)
│       ├── 0241/
│       │   ├── info.md
│       │   ├── rundown/
│       │   └── assets/
│       │       ├── sots/           (SOT video outputs)
│       │       ├── fsq/            (Full screen quote images)
│       │       └── vo/             (Voice-over audio)
│       ├── 0242/
│       └── 0243/
└── temp/                           (Temporary processing area)
    └── uploads/                    (Shared upload staging)
```

---

## 3. Installation & Configuration

### 3.1 Server Setup (Whisper)

**Step 1: Install NFS server**

```bash
# Install NFS kernel server package
sudo apt update
sudo apt install -y nfs-kernel-server

# Verify installation
dpkg -l | grep nfs-kernel-server
```

**Step 2: Configure exports**

Edit `/etc/exports` to define what directories to share:

```bash
# Open exports file
sudo nano /etc/exports

# Add this line (explanation below):
/mnt/sync 192.168.51.0/24(rw,sync,no_subtree_check,no_root_squash)
```

**Export options explained:**

| Option | Meaning |
|--------|---------|
| `/mnt/sync` | Directory to share |
| `192.168.51.0/24` | Allow entire subnet (192.168.51.1-254) |
| `rw` | Read-write access (clients can create/modify files) |
| `sync` | Write changes to disk before responding (safer, slightly slower) |
| `no_subtree_check` | Don't verify file is in exported subtree (performance) |
| `no_root_squash` | Allow root on client to act as root on server (needed for Docker) |

**Step 3: Apply configuration**

```bash
# Reload exports without restarting
sudo exportfs -a

# Verify exports are active
sudo exportfs -v

# Expected output:
# /mnt/sync     192.168.51.0/24(rw,wdelay,no_root_squash,no_subtree_check,sec=sys,...)
```

**Step 4: Start NFS server**

```bash
# Enable NFS server to start on boot
sudo systemctl enable nfs-kernel-server

# Start NFS server
sudo systemctl start nfs-kernel-server

# Verify status
sudo systemctl status nfs-kernel-server

# Expected output: "Active: active (exited)"
```

**Step 5: Configure firewall (if UFW enabled)**

```bash
# Check if UFW is active
sudo ufw status

# If active, allow NFS from local network
sudo ufw allow from 192.168.51.0/24 to any port nfs

# Reload firewall
sudo ufw reload
```

### 3.2 Verify Server is Sharing

```bash
# Show what directories are currently exported
showmount -e localhost

# Expected output:
# Export list for localhost:
# /mnt/sync 192.168.51.0/24
```

---

## 4. Client Configuration

### 4.1 Client Setup (Kairo, Proxima, etc.)

**Step 1: Install NFS client**

```bash
# Install NFS common package (includes mount.nfs)
sudo apt update
sudo apt install -y nfs-common

# Verify installation
dpkg -l | grep nfs-common
```

**Step 2: Create mount point**

```bash
# Create directory to mount NFS share
sudo mkdir -p /mnt/sync

# Set permissions (will be overridden by NFS mount)
sudo chmod 755 /mnt/sync
```

**Step 3: Test manual mount**

```bash
# Mount NFS share manually (for testing)
sudo mount -t nfs whisper:/mnt/sync /mnt/sync

# Verify mount succeeded
mount | grep nfs

# Expected output:
# whisper:/mnt/sync on /mnt/sync type nfs4 (rw,relatime,...)

# Test access
ls -la /mnt/sync/disaffected/episodes/

# You should see episode directories
```

**Step 4: Make mount permanent**

```bash
# Add to /etc/fstab for automatic mounting on boot
echo "whisper:/mnt/sync /mnt/sync nfs defaults,_netdev 0 0" | sudo tee -a /etc/fstab

# Options explained:
# - defaults: rw,suid,dev,exec,auto,nouser,async
# - _netdev: wait for network before mounting (critical for NFS)
# - 0 0: no dump, no fsck
```

**Step 5: Test automatic mounting**

```bash
# Unmount to test fstab
sudo umount /mnt/sync

# Mount using fstab entry
sudo mount -a

# Verify it mounted
mount | grep nfs
```

### 4.2 Client Health Check Script

Create `/usr/local/bin/check_nfs_mount.sh`:

```bash
#!/bin/bash
# NFS mount health check for Show-Build workers

MOUNT_POINT="/mnt/sync"
NFS_SERVER="whisper:/mnt/sync"

if ! mountpoint -q "$MOUNT_POINT"; then
    echo "ERROR: $MOUNT_POINT is not mounted"
    echo "Attempting to mount..."
    mount -a

    if ! mountpoint -q "$MOUNT_POINT"; then
        echo "CRITICAL: Failed to mount NFS share"
        exit 1
    fi
fi

# Test read access
if ! ls "$MOUNT_POINT/disaffected/episodes" > /dev/null 2>&1; then
    echo "ERROR: Cannot read NFS mount"
    exit 1
fi

# Test write access (create temporary file)
TEST_FILE="$MOUNT_POINT/temp/.nfs_test_$(date +%s)"
if ! touch "$TEST_FILE" 2>/dev/null; then
    echo "ERROR: Cannot write to NFS mount"
    exit 1
fi
rm -f "$TEST_FILE"

echo "OK: NFS mount is healthy"
exit 0
```

Make executable and add to cron:

```bash
sudo chmod +x /usr/local/bin/check_nfs_mount.sh

# Add to crontab (check every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/check_nfs_mount.sh") | crontab -
```

---

## 5. Docker Integration

### 5.1 Updated Docker Compose (Celery Worker)

**File: `~/celery-worker-media/docker-compose.yml` (on kairo/proxima)**

```yaml
version: '3.8'

services:
  celery-worker:
    container_name: kairo-celery
    image: show-build-worker-celery-media
    restart: unless-stopped

    command: >
      celery -A celery_app worker
      --loglevel=info
      --concurrency=4
      --queues=media
      --hostname=media@kairo

    environment:
      - REDIS_URL=redis://:showbuild2025@192.168.51.223:6379/0
      - CELERY_BROKER_URL=redis://:showbuild2025@192.168.51.223:6379/0
      - CELERY_RESULT_BACKEND=redis://:showbuild2025@192.168.51.223:6379/0

    volumes:
      # NFS mounts (must be mounted on host first!)
      - /mnt/sync/disaffected/episodes:/home/episodes:rw
      - /mnt/sync/shared_media:/shared_media:rw
      - /mnt/sync/temp:/tmp/sot_uploads:rw  # NEW: shared temp directory

    networks:
      - show-build-network

networks:
  show-build-network:
    driver: bridge
```

**Key changes:**
1. Volume mounts now point to NFS-mounted host directories
2. Added `/mnt/sync/temp:/tmp/sot_uploads` for shared upload staging
3. No need for rsync - Docker sees NFS files directly

### 5.2 Whisper Server Updates

**Updated: `/mnt/process/show-build/docker-compose.yml`**

Create shared temp directory:

```bash
# On whisper
sudo mkdir -p /mnt/sync/temp/uploads
sudo chmod 777 /mnt/sync/temp/uploads
```

Update server container to use shared temp:

```yaml
services:
  server:
    # ... existing config ...
    volumes:
      - /mnt/sync/disaffected/episodes:/home/episodes:rw
      - /mnt/sync/shared_media:/shared_media:rw
      - /mnt/sync/temp/uploads:/tmp/sot_uploads:rw  # NEW: shared temp
```

### 5.3 Why Docker Needs `no_root_squash`

**Problem:** Docker containers run processes as various UIDs (often root UID 0)

**Without `no_root_squash`:**
- Container writes file as root (UID 0)
- NFS server maps root → nobody (UID 65534)
- Files owned by nobody:nogroup
- Other containers can't access files

**With `no_root_squash`:**
- Container writes file as root (UID 0)
- NFS server preserves UID 0
- Files owned by root:root
- All containers (running as root) can access

**Security note:** This is safe because:
1. NFS is only accessible on trusted LAN (192.168.51.0/24)
2. All machines are under your control
3. Alternative (UID mapping) is complex and breaks Docker

---

## 6. Security

### 6.1 Access Control

**Current configuration:**
```
/mnt/sync 192.168.51.0/24(rw,sync,no_subtree_check,no_root_squash)
```

**Security measures:**

1. **Network restriction:** Only 192.168.51.0/24 subnet can access
2. **Firewall:** Only allow NFS from known IPs (optional enhancement)
3. **Physical security:** All machines on private LAN

**Tighter security (optional):**

```bash
# Restrict to specific IPs instead of subnet
/mnt/sync 192.168.51.197(rw,sync,no_subtree_check,no_root_squash) 192.168.51.223(rw,sync,no_subtree_check,no_root_squash)
```

### 6.2 Firewall Configuration

**On whisper (NFS server):**

```bash
# Allow NFS from specific IPs
sudo ufw allow from 192.168.51.197 to any port nfs
sudo ufw allow from 192.168.51.223 to any port nfs

# Block NFS from all other sources
sudo ufw deny nfs
```

### 6.3 Encryption (NFSv4 + Kerberos)

**Current setup:** Unencrypted NFSv4 (fine for trusted LAN)

**If you need encryption later:**

```bash
# Install Kerberos
sudo apt install krb5-user nfs4-acl-tools

# Configure Kerberos KDC
# (Complex setup - only needed for untrusted networks)
```

**Recommendation:** For your use case (private LAN), encryption is overkill. If you need it later, use WireGuard VPN instead of Kerberos.

---

## 7. Troubleshooting

### 7.1 Common Issues

#### Issue: "mount.nfs: Connection refused"

**Cause:** NFS server not running or firewall blocking

**Solution:**
```bash
# On server (whisper)
sudo systemctl status nfs-kernel-server
sudo systemctl restart nfs-kernel-server

# Check if port 2049 is listening
sudo ss -tulpn | grep 2049
```

#### Issue: "mount.nfs: access denied"

**Cause:** Client IP not in allowed range

**Solution:**
```bash
# On server, check exports
sudo exportfs -v

# Verify client IP matches allowed range
# Example: Client 192.168.51.197 must match 192.168.51.0/24
```

#### Issue: "Stale file handle"

**Cause:** Server rebooted or NFS share was unmounted/remounted

**Solution:**
```bash
# On client
sudo umount -f /mnt/sync
sudo mount -a

# If unmount fails (busy)
sudo umount -l /mnt/sync  # Lazy unmount
sudo mount -a
```

#### Issue: "Permission denied" when writing files

**Cause:** UID/GID mismatch or wrong export options

**Solution:**
```bash
# On server, verify no_root_squash is set
sudo exportfs -v | grep no_root_squash

# If not present, add to /etc/exports and reload
sudo exportfs -ra
```

#### Issue: Docker container can't see NFS files

**Cause:** NFS not mounted on host before Docker starts

**Solution:**
```bash
# Verify host mount
mount | grep /mnt/sync

# Restart Docker container
docker compose restart celery-worker
```

### 7.2 Diagnostic Commands

```bash
# On server (whisper)
# ==================

# Show active NFS exports
sudo exportfs -v

# Show NFS server statistics
nfsstat -s

# Show connected clients
sudo netstat -an | grep 2049

# On client (kairo/proxima)
# =========================

# Show available NFS exports from server
showmount -e whisper

# Show current NFS mounts
mount | grep nfs

# Test NFS mount performance
dd if=/dev/zero of=/mnt/sync/test.dat bs=1M count=100
# Should achieve 50-100 MB/s on gigabit LAN

# Check NFS mount staleness
stat /mnt/sync/disaffected/episodes
```

### 7.3 Performance Issues

**Symptom:** Slow file access over NFS

**Diagnosis:**
```bash
# Check network latency
ping whisper

# Should be <1ms on LAN

# Check NFS read performance
time dd if=/mnt/sync/test.dat of=/dev/null bs=1M count=100

# Check NFS write performance
time dd if=/dev/zero of=/mnt/sync/test.dat bs=1M count=100

# Expected: 50-100 MB/s on gigabit LAN
```

**Tuning options (add to /etc/fstab):**
```
whisper:/mnt/sync /mnt/sync nfs rsize=8192,wsize=8192,timeo=14,_netdev 0 0
```

- `rsize=8192`: Read buffer size (experiment with 8192, 16384, 32768)
- `wsize=8192`: Write buffer size
- `timeo=14`: Timeout (default is 600, lower = faster failure detection)

---

## 8. Performance Tuning

### 8.1 Server-Side Tuning

**Increase NFS threads:**

```bash
# Edit /etc/default/nfs-kernel-server
sudo nano /etc/default/nfs-kernel-server

# Change RPCNFSDCOUNT from 8 to 16 (or 32 for high load)
RPCNFSDCOUNT=16

# Restart NFS
sudo systemctl restart nfs-kernel-server
```

**Enable NFS caching:**

```bash
# Check current cache statistics
nfsstat -rc

# Kernel automatically manages cache, but you can tune:
sudo sysctl -w vm.dirty_ratio=15
sudo sysctl -w vm.dirty_background_ratio=5
```

### 8.2 Client-Side Tuning

**Mount options for better performance:**

```
whisper:/mnt/sync /mnt/sync nfs vers=4.2,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,_netdev 0 0
```

- `vers=4.2`: Force latest NFS version
- `rsize/wsize=1048576`: 1MB buffers (for high-bandwidth networks)
- `hard`: Don't give up on retries (safer for database-like workloads)
- `retrans=2`: Retry twice before timeout

**Async writes (faster but riskier):**

```bash
# Add to /etc/exports on server
/mnt/sync 192.168.51.0/24(rw,async,no_subtree_check,no_root_squash)

# async = respond to client before writing to disk
# Risk: power loss before sync could lose data
# Benefit: 2-3x faster writes
```

---

## 9. Monitoring

### 9.1 NFS Statistics

**On server:**

```bash
# Show NFS server stats
nfsstat -s

# Key metrics:
# - calls: Total NFS operations
# - badcalls: Failed operations (should be near 0)
# - read/write: File operations

# Watch stats in real-time
watch -n 1 'nfsstat -s | grep -A 10 "Server nfs"'
```

**On client:**

```bash
# Show NFS client stats
nfsstat -c

# Watch active NFS operations
watch -n 1 'nfsstat -c | grep -A 10 "Client nfs"'
```

### 9.2 Health Monitoring Script

Create `/usr/local/bin/monitor_nfs_health.sh`:

```bash
#!/bin/bash
# NFS health monitoring for Show-Build

LOG_FILE="/var/log/nfs_health.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if mount is active
if ! mountpoint -q /mnt/sync; then
    log "CRITICAL: NFS mount is DOWN"
    # Send alert (email, webhook, etc.)
    exit 1
fi

# Check read performance (should complete in <1 second on LAN)
START=$(date +%s%N)
ls -la /mnt/sync/disaffected/episodes > /dev/null 2>&1
END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))  # Convert to milliseconds

if [ $DURATION -gt 1000 ]; then
    log "WARNING: NFS read took ${DURATION}ms (expected <1000ms)"
fi

# Check write performance
TEST_FILE="/mnt/sync/temp/.health_check_$(date +%s)"
START=$(date +%s%N)
touch "$TEST_FILE" 2>/dev/null
END=$(date +%s%N)
rm -f "$TEST_FILE"
DURATION=$(( (END - START) / 1000000 ))

if [ $DURATION -gt 1000 ]; then
    log "WARNING: NFS write took ${DURATION}ms (expected <1000ms)"
fi

log "OK: NFS mount healthy (read/write functional)"
exit 0
```

Add to cron:

```bash
sudo chmod +x /usr/local/bin/monitor_nfs_health.sh

# Run every 5 minutes
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/monitor_nfs_health.sh") | crontab -
```

### 9.3 Integration with Show-Build Health Endpoint

The `/health` endpoint already checks database, Redis, Celery. We can add NFS check:

**In `app/main.py`:**

```python
# Add to health_status dict
"nfs": {
    "status": "unknown",
    "mount_point": "/home/episodes",
    "readable": False,
    "writable": False
}

# Test NFS health
try:
    from pathlib import Path
    import os

    episodes_dir = Path("/home/episodes")

    # Check if directory exists and is readable
    if episodes_dir.exists() and os.access(episodes_dir, os.R_OK):
        health_status["services"]["nfs"]["readable"] = True

    # Check if writable
    test_file = episodes_dir / ".health_check"
    try:
        test_file.touch()
        test_file.unlink()
        health_status["services"]["nfs"]["writable"] = True
        health_status["services"]["nfs"]["status"] = "connected"
    except:
        health_status["services"]["nfs"]["status"] = "read_only"

except Exception as e:
    health_status["services"]["nfs"]["status"] = f"error: {str(e)[:50]}"
```

---

## Summary

This NFS infrastructure provides:

✅ **Shared storage** - All workers access same episode files
✅ **Zero duplication** - Data lives once on whisper's disk
✅ **Docker-friendly** - Simple volume mounts, no special configuration
✅ **Scalable** - Add workers by installing nfs-common and mounting
✅ **Reliable** - Industry-standard protocol used by enterprises worldwide
✅ **Future-proof** - Easy migration path to distributed filesystems later

**Next Steps:**
1. Run installation commands on whisper (Section 3.1)
2. Configure kairo as NFS client (Section 4.1)
3. Update Docker configurations (Section 5)
4. Test with SOT video upload workflow
