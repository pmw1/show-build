# Media Pool Standard (authoritative)

The **media pool** is the single, unbound bag of reusable / released media for
Show-Build. It is distinct from the per-episode **asset tree**
(`/home/episodes/{ep}/assets/{video,audio,images,graphics}/…`, see
[`EPISODE_DIRECTORY_STANDARD.md`](EPISODE_DIRECTORY_STANDARD.md)) — the episode
tree holds the media a cue is *actively using*; the pool holds media that has been
*released from* a cue or uploaded *for reuse*, decoupled from any single cue.

## Location

| | Path |
|---|---|
| Container mount | `/home/pool` |
| Host (dev + live) | `/data/sync/media_assets/pool` (env `POOL_PATH`, default in both compose files) |
| Code root | `os.getenv("POOL_ROOT", "/home/pool")` + `ShowBuildPaths.pool_root` |
| Served URL prefix | `/pool/...` (FastAPI static mount in `app/main.py`; proxied in `vue.config.js` + `nginx.conf`) |

The container mount point (`/home/pool`) is intentionally stable so code never
hardcodes the host path; only the host side of the volume mount moves if the pool
is ever relocated again.

## Tree

```
/home/pool/                              (host: /data/sync/media_assets/pool)
├── episodes/{episode}/{file}            cue-released media + (future) loose per-episode uploads. FLAT — no assets/{video,audio,…} subdirs.
├── ads/{advertiserID}/{assetID}.{ext}   reusable ad media, per advertiser.            (SCAFFOLD — dir + path helper only; no upload/browse flow yet)
├── repo/{assetID}.{ext}                 other reusables: promos, CTAs, etc.           (SCAFFOLD — layout TBD)
└── whiteboard/{episode}/{file}          whiteboard media (relocated here from repo/whiteboard).
```

### Why flat under `episodes/`
The episode asset tree uses per-type subdirs (`video/`, `audio/`, …) because the
compiler/renderer look there by type. The pool does not — provenance lives in the
`asset_pool_files` row (`source`, `source_context`) and `asset_tags`, not in the
folder layout. A flat `episodes/{ep}/` keeps released media easy to browse/reuse.

## How media gets into the pool

- **Cue release** — deleting a cue with the "release to pool" disposition MOVES the
  cue's media (driven by the cue's own URL fields, never by globbing the AssetID)
  into `pool/episodes/{ep}/`. Endpoint: `POST /api/episodes/{ep}/cue-assets/move-to-pool`
  (`app/routers/episodes/cue_assets_router.py`). Each file gets an `AssetPoolFile`
  row (+ `AssetTag` rows for cue type / slug / episode) and a fresh `POOL…` AssetID.
- **Whiteboard media** — written to `pool/whiteboard/{ep}/` by the whiteboard
  routers (`app/routers/whiteboard/_shared.py`, `crud_router.py`,
  `social_media_router.py` episode branch). `WhiteboardItem.media_path` stays
  RELATIVE (`whiteboard/{ep}/{file}`); the serving URL is `"/pool/" + media_path`.
- **Ads / repo (reusables)** — scaffold only today: the directories and
  `ShowBuildPaths` helpers exist, but no upload/browse flow is wired yet.

> NOTE: the legacy non-episode whiteboard path `/mnt/sync/asset-pool` (served at
> `/asset-pool/...`, used by the social-media routers' non-episode branch) is a
> SEPARATE, older store and is **out of scope** of this pool. Do not conflate them.

## Path helpers — use these, don't hardcode

`app/core/paths.py` (`ShowBuildPaths`):

| Helper | Returns |
|---|---|
| `get_pool_root()` | `/home/pool` |
| `get_pool_episodes_dir(episode_id)` | `/home/pool/episodes/{ep}` |
| `get_pool_whiteboard_dir(episode_id)` | `/home/pool/whiteboard/{ep}` |
| `get_pool_ads_dir(advertiser_id)` | `/home/pool/ads/{advertiserID}` (scaffold) |
| `get_pool_repo_dir()` | `/home/pool/repo` (scaffold) |

`get_whiteboard_media_dir()` delegates to `get_pool_whiteboard_dir()` (single
source of truth).

## Database

- **`asset_pool_files`** (`AssetPoolFile`, `app/models_whiteboard.py`) — one row per
  pooled file: `asset_id` (FK → `asset_id_registry`), `file_path`,
  `original_filename`, `mime_type`, `file_size`, `thumbnail_path`, `source`
  (`'cue_release'`, `'whiteboard'`, `'twitter'`, `'youtube'`, …), `source_url`,
  `source_context` (JSON provenance).
- **`asset_tags`** (`AssetTag`) — free-form tags for browse/filter.
- AssetID prefix for pooled assets: **`POOL`** (`app/services/asset_id.py`
  `PREFIXES["pool"]`).

## Permissions / ownership

The pool tree must be writable by the container user **uid 1000 / gid 1001
(`disaffected`)**. Create new subtrees `chown 1000:1001` + `chmod 2775` (setgid so
container-created subdirs inherit the group).

## Dev vs Live

This standard is implemented on **dev** (`feat/script-editor-tiptap`,
dev.showbuild.app). The code + compose changes are shared with live, but the **live
data migration is deferred**: live still serves from the old pool host path until a
maintenance window repoints `docker-compose.yml` and migrates live files + the live
`showbuild` DB. The container path `/home/pool` is unchanged, so the code stays
live-compatible until then.

## Verification (dev)
1. `docker exec show-build-server-dev ls -la /home/pool` → `episodes ads repo whiteboard`, owned `1000:disaffected`.
2. Release a cue's media → file lands at `pool/episodes/{ep}/{file}`; `GET /pool/episodes/{ep}/{file}` → 200; `asset_pool_files` row with `asset_id` starting `POOL`.
3. Whiteboard create/load → media at `pool/whiteboard/{ep}/`; UI loads via `GET /pool/whiteboard/{ep}/{file}` → 200.
