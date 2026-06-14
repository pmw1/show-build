# Worker Fleet Deployment Plan — get the multi-flavor workers running

**Status:** draft for review · **Author:** prefect-show-build-claude-63ebeb · 2026-06-04
**Goal:** Replace the single monolithic Celery worker (`celery-workers-celery-worker:latest`)
with the new multi-flavor fleet (`worker-base` / `worker-media-cpu` / `worker-media-gpu`),
starting on **dev**, proving it on a real SOT job, then rolling to **live**.

---

## Current state (verified 2026-06-04)

- **Images exist** in Gitea registry `192.168.51.206:3000` under both `kevin/` and
  `showbuild/` namespaces: `worker-base` (479MB), `worker-media-cpu` (905MB),
  `worker-media-gpu` (3.08GB), tags `latest` + `b695b49`.
- **Nothing runs them.** Both `show-build-assets-worker-dev` (dev) and
  `prefect-assets_worker` (live) use the OLD `celery-workers-celery-worker:latest`
  monolith. Every SOT/media job (incl. jobs 831/832) ran on the monolith.
- **Fleet definition** = `deploy/workers/workers.yml` (on `main` @ `995e179`; NOT yet
  on this branch's worktree). It declares a 4-host fleet (prefect/kairo/proxima/whisperbox).
- **Entrypoint** = `deploy/workers/worker-entrypoint.sh`: prefers an existing bind/host
  NFS mount, self-mounts only as fallback. `NFS_MOUNTS` default `/mnt/sync:/mnt/sync`.

## Conflicts the workers.yml does NOT account for (must resolve before landing)

1. **Broker DB index.** workers.yml defaults `redis://…@192.168.51.223:6379/0` (LIVE).
   Dev MUST use `/1` + `showbuild_dev`, or a new dev worker would eat LIVE jobs.
   → Dev worker overrides: Redis `/1`, `DATABASE_URL=…/showbuild_dev`.
2. **whisperbox (.210) is an ACTIVE worker** (corrected 2026-06-04). It runs the
   transcription stack (`whisper-worker`, `whisper-medium` faster-whisper CUDA,
   `diarize`) AND serves the NFS share (`/mnt/sync`, `/mnt/process`) that prefect
   binds. → KEEP the whisper worker entry (whisper queue, base flavor, redis-only,
   no DB). An earlier project-memory note wrongly said .210 was retired — it was not;
   only the web app moved to prefect. Note its whisper containers already run today
   (image `whisper-whisper-worker`), so the fleet refactor may just FORMALIZE the
   existing .210 worker rather than newly deploy one — confirm before changing .210.
3. **proxima (.208) + AgentBox/registry (.206)** were flagged DOWN (relay #719). Registry
   pulls need .206 up. → Phase 0 reachability gate.
4. **prefect has TWO GPUs** (RTX 3060 + RTX 5090), nvidia runtime present. workers.yml
   only knew the 3060. → can pin the media worker to a specific GPU; default `all` is fine.
5. **media_root**: workers.yml `=/mnt/sync/disaffected`; current dev worker resolves media
   under the same NFS tree (host has .210:/mnt/sync mounted). → keep `/mnt/sync` bind; verify
   paths resolve identically to the monolith before cutover.

---

## Plan — staged, dev-first, reversible at every step

### Phase 0 — Prereqs / gate (no changes)
- [ ] Registry reachable: `curl -sf http://192.168.51.206:3000/v2/` (else .206 is down → stop).
- [ ] prefect can pull each flavor: `docker pull …/worker-media-gpu:latest` (already local, re-verify).
- [ ] NFS bind present on prefect: `/mnt/sync` + `/mnt/process` mounted (VERIFIED today).
- [ ] nvidia runtime: `docker run --rm --gpus all …/worker-media-gpu nvidia-smi` succeeds.

### Phase 1 — DEV cutover (the real goal: next SOT uses the new workers)
Replace `assets-worker-dev` in `docker-compose.dev.yml` with TWO flavored dev services,
all pinned to dev broker `/1` + `showbuild_dev`:
- [ ] `assets-worker-dev` → image `…/worker-media-gpu:latest`, `--gpus all`,
      queues `media,assets_high,assets,assets_low,fsq`, concurrency 3,
      bind `/mnt/sync:/mnt/sync` (+ `/mnt/process` if tasks need it),
      env: dev Redis `/1`, `DATABASE_URL=…/showbuild_dev`, `MEDIA_ROOT=/mnt/sync/disaffected`.
- [ ] `llm-content-worker-dev` (optional, if dev exercises llm_content) → `worker-base`,
      queue `llm_content`, concurrency 1, dev broker `/1`.
- [ ] Keep the OLD monolith service definition commented (instant rollback).
- [ ] `docker compose -f docker-compose.dev.yml up -d` (recreate, not restart).
- [ ] Verify: worker banner shows the flavored image + correct queues + GPU visible
      (`nvidia-smi` inside the container lists a GPU); `celery inspect active_queues`.

### Phase 2 — Prove it
- [ ] Upload a test SOT on dev → confirm the job is consumed by the NEW worker
      (check `docker logs` of the flavored container for the task id; confirm GPU
      nvenc path hit via `ffmpeg_accel` logs), artifacts land on disk, status=completed.
- [ ] Confirm the GPU-first ffmpeg failover (`app/services/ffmpeg_accel.py`) actually
      used nvenc (not the CPU fallback) — grep worker logs.

### Phase 3 — Land the config in git
- [ ] Merge `main`'s `deploy/workers/` into this branch (it's missing here) OR cherry-pick,
      so `workers.yml` + Dockerfiles + entrypoint live on the dev branch too.
- [ ] Commit the dev-compose change. (Uncommitted-on-live drift is what bit us with the
      delete modal — do NOT repeat it.)

### Phase 4 — LIVE rollout (separate, explicit approval)
- [ ] Apply the same swap to live `docker-compose.yml`: `prefect-assets_worker` →
      `worker-media-gpu` (Redis `/0`, `showbuild`), plus `llm-content` → `worker-base`.
- [ ] Drop the whisperbox worker entry from any rendered live compose.
- [ ] kairo (.197) + proxima (.208) workers: only if those hosts are up and you want
      them in the pool — separate per-host deploy, not part of the prefect cutover.
- [ ] Watch a live SOT end-to-end before declaring done.

### Rollback
At any phase: re-enable the commented monolith service, `up -d`. The monolith image is
untouched and still in the registry.

---

## Open decisions for Kevin
1. **Scope now:** just **prefect dev** (Phase 1–2), or prefect dev + live (through Phase 4)?
2. **GPU pin:** let the media worker use `all` (both 3060 + 5090), or pin to one card so
   the 5090 stays free for other work?
3. **kairo/proxima** workers: in scope, or prefect-only for now?
