#!/usr/bin/env bash
# worker-entrypoint.sh — self-mounting worker bootstrap.
#
# The worker image mounts its own NFS share(s) at FIRST RUN (docker build cannot
# do privileged mounts), then maintains them (remount on failure) for the life of
# the container, then execs the celery worker.
#
# Requires the container to run with: --cap-add SYS_ADMIN  (least privilege that
# allows mount()). No host pre-mount needed — the worker is self-sufficient.
#
# Config via env (with sane defaults for the disaffected fleet):
#   NFS_SERVER     default 192.168.51.210
#   NFS_MOUNTS     space/comma list of "remote:local" pairs.
#                  default: /mnt/sync:/mnt/sync
#                  (add more, e.g. "/mnt/sync:/mnt/sync /mnt/process:/mnt/process")
#   NFS_OPTS       mount options. default: nfsvers=4.2,hard,proto=tcp,timeo=600,retrans=2,rw
#   NFS_REQUIRED   if "true" (default), refuse to start celery if a mount fails.
#   WORKER_MOUNT_WATCH_SECONDS  remount-check interval. default 30.
#   (everything after -- / remaining args is the celery command to exec)
set -uo pipefail

log() { echo "[worker-entrypoint] $*"; }

NFS_SERVER="${NFS_SERVER:-192.168.51.210}"
NFS_MOUNTS="${NFS_MOUNTS:-/mnt/sync:/mnt/sync}"
NFS_OPTS="${NFS_OPTS:-nfsvers=4.2,hard,proto=tcp,timeo=600,retrans=2,rw}"
NFS_REQUIRED="${NFS_REQUIRED:-true}"
WATCH="${WORKER_MOUNT_WATCH_SECONDS:-30}"

# normalize commas -> spaces
NFS_MOUNTS="${NFS_MOUNTS//,/ }"

mount_one() {
    local remote="$1" local_dir="$2"
    mkdir -p "$local_dir"
    # PREFERRED PATH: if the share is already present (bind-mounted in from a host
    # that mounts the NFS share, or already mounted), use it as-is. This is the
    # reliable model — the host owns the NFS client, the container just sees it.
    # In-container self-mount is only a FALLBACK for hosts that don't pre-mount,
    # and is unreliable when the host already holds the NFSv4 lease for this IP.
    if mountpoint -q "$local_dir"; then
        log "  ${local_dir} already present (bind/host mount) — using it"
        return 0
    fi
    if [ -n "$(ls -A "$local_dir" 2>/dev/null)" ]; then
        log "  ${local_dir} already populated (bind mount) — using it"
        return 0
    fi
    # Fallback: self-mount over NFS (requires --cap-add SYS_ADMIN + seccomp=unconfined;
    # may be refused if the host already holds this IP's NFSv4 lease).
    log "mounting ${NFS_SERVER}:${remote} -> ${local_dir} (${NFS_OPTS})"
    if mount -t nfs4 -o "$NFS_OPTS" "${NFS_SERVER}:${remote}" "$local_dir"; then
        log "  mounted ${local_dir}"
        return 0
    fi
    log "  FAILED to self-mount ${local_dir} (no bind present and NFS mount refused)"
    return 1
}

mount_all() {
    local ok=0
    for pair in $NFS_MOUNTS; do
        local remote="${pair%%:*}" local_dir="${pair##*:}"
        mount_one "$remote" "$local_dir" || ok=1
    done
    return $ok
}

# --- initial mount ---
if ! mount_all; then
    if [ "$NFS_REQUIRED" = "true" ]; then
        log "FATAL: required NFS mount(s) failed and NFS_REQUIRED=true. Refusing to start."
        log "  (check: NVIDIA toolkit? --cap-add SYS_ADMIN set? ${NFS_SERVER} reachable? export allows this host?)"
        exit 1
    fi
    log "WARNING: NFS mount(s) failed but NFS_REQUIRED=false — continuing without media."
fi

# --- background remount watcher (maintenance) ---
(
    while true; do
        sleep "$WATCH"
        for pair in $NFS_MOUNTS; do
            local_dir="${pair##*:}"; remote="${pair%%:*}"
            if ! mountpoint -q "$local_dir"; then
                log "mount $local_dir dropped — remounting"
                mount_one "$remote" "$local_dir" || true
            fi
        done
    done
) &
WATCHER_PID=$!

# clean unmount on stop
cleanup() {
    log "shutting down; killing watcher + unmounting"
    kill "$WATCHER_PID" 2>/dev/null || true
    for pair in $NFS_MOUNTS; do
        local_dir="${pair##*:}"
        mountpoint -q "$local_dir" && umount -l "$local_dir" 2>/dev/null || true
    done
}
trap cleanup TERM INT

# --- exec the celery worker (args passed by compose/CMD) ---
# The entrypoint runs as ROOT (mount() requires it, even with SYS_ADMIN). Drop to
# the unprivileged worker user for the actual celery process via gosu.
WORKER_USER="${WORKER_USER:-insider}"
log "starting worker as ${WORKER_USER}: $*"
if command -v gosu >/dev/null 2>&1 && [ "$(id -u)" = "0" ]; then
    exec gosu "$WORKER_USER" "$@"
else
    exec "$@"
fi
