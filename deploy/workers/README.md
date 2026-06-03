# Worker images — multi-flavor refactor (DRAFT)

**Status:** DRAFT in worktree `draft/worker-multi-image` (off main @ abf92fc).
Authored by the showtime session for the show-build session to review + land.
Does NOT touch the existing `/Dockerfile` (which has UNTOUCHABLE ZONE markers and
is the FastAPI **app/server** image, not a worker image).
**Date:** 2026-06-02.

---

## Why multiple images

Today show-build effectively has TWO accidental image shapes:
1. `/Dockerfile` (`tiangolo/uvicorn-gunicorn-fastapi:python3.11`, + wkhtmltopdf,
   FastAPI, google, etc.) — used by `server`, `llm-content-worker`, `celery-beat`
   (all `build: context: .`). Heavy, NO ffmpeg binary.
2. The `python:3.11-slim` + apt-ffmpeg image the remote deploy script
   (`scripts/deploy_celery_worker.sh`) generates inline — used by the kairo/proxima
   **media** workers.

Worker PROCESSES are already distinct (each picks queues via `-Q`). The CODE is a
true superset — every worker can import every task; `requirements.txt` is all-light
(web/db/google + `ffmpeg-python` which is just a wrapper; the real ffmpeg *binary*
is a system-layer concern). So the only thing that legitimately differs between
workers is the **system layer**: which ffmpeg (none / CPU / nvenc) and whether CUDA
is present. That's exactly a flavor axis.

**Decision (Kevin 2026-06-02): refactor into deliberate image FLAVORS.** Only the
video-encoding workers carry ffmpeg+CUDA; the rest stay lean.

---

## The flavors

All flavors COPY the same `app/` (superset of tasks). They differ only in base +
system packages. A worker process still selects its work via `-Q <queues>`.

| flavor | base | ffmpeg | use | workers |
|---|---|---|---|---|
| **base** | `python:3.11-slim` | none | light tasks, no media | `llm-content` (llm_content), `celery-beat`, future light workers |
| **media-cpu** | `python:3.11-slim` | apt ffmpeg (libx264) | CPU video on non-GPU hosts | media/SOT/fsq on CPU-only hosts |
| **media-gpu** | `nvidia/cuda:12.4.1-runtime-ubuntu22.04` | ffmpeg + nvenc | GPU-first video, CPU failover | media/SOT/fsq on GPU hosts (kairo, prefect, proxima if carded) |

Notes:
- The **app/server** keeps using the existing `/Dockerfile` — out of scope here.
  (It's the FastAPI app, not a Celery worker image; leave its UNTOUCHABLE ZONES.)
- `media-gpu` and `media-cpu` share the SAME app code + the SAME GPU-first/CPU-
  failover ffmpeg helper (see `ffmpeg_accel.py`). On `media-cpu` the nvenc path
  simply never succeeds, so it always takes libx264 — identical code, the failover
  degrades gracefully. So in practice `media-cpu` is optional: a `media-gpu` image
  on a CPU host also works (nvenc fails → CPU), just carrying unused CUDA layers.
  Keep `media-cpu` for lean CPU-only hosts; use `media-gpu` where a card exists.
- CUDA 12.4 runtime chosen as forward-compatible with recent drivers (3060/3090/
  5090). Bump if a host driver is older than the CUDA minor requires.

---

## Files in this dir

- `worker.base.Dockerfile`     — base flavor
- `worker.media-cpu.Dockerfile`— CPU ffmpeg flavor
- `worker.media-gpu.Dockerfile`— CUDA + nvenc flavor
- `workers.yml`                — declared fleet: host → flavor → queues → concurrency → gpu/mounts
- `build-push.sh`              — build all flavors, tag `<sha>` + `latest`, push to Gitea
- (helper) `app/services/ffmpeg_accel.py` — GPU-first/CPU-failover ffmpeg wrapper
  (lives in app/ so all media workers share it; see that file's header)

## How a worker runs (unchanged contract)
`celery -A celery_app worker -Q <queues> --concurrency=N --hostname=<name>@<host>`
— same as today. Only the IMAGE (flavor) and the `-Q`/host differ, declared in
`workers.yml` and rendered into each host's compose.
