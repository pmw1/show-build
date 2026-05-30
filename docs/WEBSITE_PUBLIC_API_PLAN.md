# Show-Build → Website Public API Plan

**Status:** ⏸️ ON HOLD as of 2026-05-08 — Kevin is drafting additional
requirements that need to be reconciled with this plan before
implementation continues. Do NOT proceed with Phase 2+ until reconciliation.

**Last active state:** v13 — all original 4 blockers resolved, Phase 1
scaffold landed (router package + 17 stub routes), migration drafted
but NOT applied. See "Pause state snapshot" below.

**Owner:** show-build-claude (in coordination with website team)
**Last updated:** 2026-05-08
**Pre-implementation blockers:** PAUSED pending Kevin's draft requirements

**Decisions resolved (Kevin, 2026-05-08):**
- #1 — SSG with build-time pull + webhook-purge on republish
- #2 — Hostnames: `api.disaffected.com` (API) + `media.disaffected.com` (assets), under `*.disaffected.com` wildcard cert. Brand domain confirmed `disaffected.com`.
- #3 — show-build does poster resizing via Celery `assets` queue (pre-generated WebP variants)
- #5 — `script_content` is **permanently FORBIDDEN** from public responses. Public segment text comes from `segment_transcripts` (whisper-medium + pyannote diarization, post-broadcast). See sibling doc `TRANSCRIPT_PIPELINE_PLAN.md` (TODO).
- #11 — Tier-gating supported, default `public`. Episodes and segments get an `access_tier` column (default `'public'`); each is independently flippable to a paid tier with a minimum required rank. The full distribution-matrix concept (per-destination state across YouTube, X, IG, TikTok, etc.) is captured in sibling doc `PUBLICATION_DESTINATIONS_PLAN.md` and is OUT OF SCOPE for the public-API v1.
- Admin freshness widget — lives on the website; show-build exposes response headers + admin endpoints

---

## ⏸️ Pause state snapshot (2026-05-08)

This plan is ON HOLD pending Kevin's incoming requirements draft.
When work resumes, the next session should:

1. **Read Kevin's new requirements doc** (TBD path — to be added when written)
2. **Reconcile** new requirements against this plan; flag conflicts
3. **Decide** which sections of this plan need rewriting vs. which still hold
4. **Resume** Phase 1 cleanup or start Phase 2 vertical slice

### What was last committed to disk before pause

- `docs/WEBSITE_PUBLIC_API_PLAN.md` (this doc) — v13, full design
- `docs/PUBLICATION_DESTINATIONS_PLAN.md` — stub for distribution matrix
- `app/alembic/versions/g015_public_api_publish_lifecycle.py` —
  migration drafted, alembic confirms as new head, **NOT YET APPLIED**
- `app/routers/public/` — 9 files, 8 sub-routers, 17 routes, all
  stubs returning 501, auth gates working
- `app/main.py` — public_router imported and mounted
- `ACTIVE_WORK_QUEUE.md` — Public API entry marked "Phase 1 scaffold landed"

### What was NOT done before pause

- Migration NOT applied (`alembic upgrade head` not run)
- No Pydantic public schemas written yet (just designed in this doc)
- No `public_query_service.py` separated from `_shared.py`
- No `public_asset_resolver.py`
- No RBAC seed for `public.*` permissions or `public-reader` role
- No field-leak guard test (`tests/test_public_api_no_leaks.py`)
- All 17 routes still return 501

### Reconciliation checklist for the resumption session

When Kevin's new requirements arrive, walk this checklist:

- [ ] Do the new requirements add new content types beyond episode /
      segment / transcript / tag / thumbnail? If yes, add to schema +
      Pydantic + URL surface
- [ ] Do they change the tier model (more tiers, different gating
      semantics)? If yes, update `access_tiers` seed + tier section
- [ ] Do they change the publish lifecycle (new states, new triggers)?
      If yes, update migration g015 BEFORE applying it
- [ ] Do they introduce a new auth model (browser-direct, OAuth, etc.)?
      If yes, the no-JWT rule may need revisiting
- [ ] Do they change the URL contract (versioning, locale prefixes,
      different verbs)? If yes, the 17 stub routes may need restructuring
- [ ] Are there fields the website needs that are currently FORBIDDEN
      by the leak guard? If yes, evaluate carefully — these are
      forbidden for security reasons

### How to resume cleanly

```bash
# 1. Read both plan docs + new requirements
cat docs/WEBSITE_PUBLIC_API_PLAN.md
cat docs/PUBLICATION_DESTINATIONS_PLAN.md
cat docs/<NEW_REQUIREMENTS>.md   # path TBD

# 2. Verify scaffold still healthy
docker exec show-build-server curl -s http://localhost:80/openapi.json \
  | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); \
    print(len([p for p in d.get('paths',{}) if '/public/v1' in p]),'public routes')"
# Expect: 17 public routes

# 3. Verify migration is still alembic head, NOT applied
docker exec -w /app show-build-server alembic heads     # expect g015...
docker exec -w /app show-build-server alembic current   # expect g014...

# 4. THEN start reconciliation
```

---

**All blockers resolved 2026-05-08. Public-API plan is ready to scaffold.**

## Reading order

This is a long doc. Read in this order:

1. **TL;DR** — executive summary, what + why
2. **Goal / Hard requirements** — design constraints
3. **Content surface** — what gets pulled, in what tiers
4. **Segregation rules** — how episode/segment/transcript/tag/thumbnail relate
5. **Security model + 3 layers of defense** — the threat-model
6. **Decision points** — the 12 questions the website team needs to answer
7. Everything else is implementation detail you can skim until scaffolding starts.

## Section index

- [TL;DR](#tldr-for-the-website-team)
- [Goal](#goal)
- [Hard requirements](#hard-requirements)
- [Content surface — what gets pulled](#content-surface--what-gets-pulled)
- [Segregation: how each content type maps](#segregation-how-each-content-type-maps)
- [Security model](#security-model)
- [Implementation plan (sharp)](#implementation-plan-sharp)
- [Concrete file layout](#concrete-file-layout-mirrors-existing-house-style)
- [Schema reality check](#schema-reality-check-2026-05-07) — most columns already exist
- [Core query predicate](#core-query-predicate-single-source-of-truth)
- [Public Pydantic schemas](#public-pydantic-schemas-the-security-boundary)
- [Tier gating (decision #11)](#tier-gating-decision-11)
- [Field-leak guard test](#field-leak-guard-test-the-actual-enforcement-mechanism)
- [`script_content` sanitizer — REMOVED](#script_content-sanitizer--removed-decision-5-resolved)
- [Auth specifics](#auth-specifics--rbac-seed--key-issuance--rate-limit)
- [Asset URL resolver](#asset-url-resolver-filesystem--public-url)
- [Poster variant generator](#poster-variant-generator-celery-assets-queue)
- [Admin freshness signaling](#admin-freshness-signaling)
- [Publish-event lifecycle](#publish-event-lifecycle-the-chain-of-side-effects)
- [Webhook delivery contract](#webhook-delivery--the-contract-for-the-website-team)
- [ETag strategy](#etag-strategy)
- [Response budget targets](#response-budget-targets)
- [Decision points — needed from website team](#decision-points--needed-from-website-team-to-start-scaffolding)
- [Risks](#risks--things-to-not-screw-up)
- [Next concrete steps](#next-concrete-steps)

## TL;DR (for the website team)

We will expose show-build content through a **read-only, key-gated**
HTTP API at `https://api.disaffected.com/public/v1` and a separate
**media origin** at `https://media.disaffected.com` for poster images,
SOT clips, and transcript files. The website's server-side fetcher
(SSG/SSR) authenticates with an API key; nothing public ever touches
show-build's editor surface.

**Content surface, ordered by priority:**
1. Episode index + detail (with poster set, SEO block, tags, segment list)
2. Segment detail (independently URL-addressable, inherits SEO/poster from
   parent episode unless overridden)
3. Transcripts per segment (plain/VTT/SRT/JSON, served as static files
   from media origin)
4. Tag pages (initially synthesized from CSV, normalized later)
5. Sitemap.xml + RSS (generated from the index)
6. Search + related (Tier 2)

**How types segregate:**
- Episode is the publish unit. Nothing publishes unless the episode does.
- Segments have their own slug + publish flag (`inherit`/`published`/
  `draft`/`unpublished`).
- Transcripts belong to segments. Episode "transcript" is computed.
- Tags exist on both — segment is canonical, episode aggregates.
- Thumbnails: episode has the canonical 4-ratio poster set; segments
  may override; resolver returns the resolved set per request.
- Production-only content (cues GFX/VO/NAT/BUMP/FSQ, internal notes,
  generation history, tone confidence) NEVER reaches public.

**Defense in depth (3 layers):**
1. Pydantic public schemas (allow-list, tested) — no field can leak.
2. Path resolver — public URLs never include `/home/episodes/` or
   internal asset_ids.
3. Materialization task — only files copied into `{episode}/public/`
   on publish are reachable from the media origin. Anything not
   materialized is unreachable regardless of what URL gets generated.

**What we need from the website team to start scaffolding** — see the
"Decision points" section near the bottom.

---

## Goal

Expose a **read-only, narrow, cacheable** HTTP API from show-build that the
public website (disaffected.com / etc.) can pull from to populate episode
pages, segment pages, transcripts, tag indexes, SEO metadata, and thumbnail
URLs — **without exposing the production editor surface** or any
unpublished/draft content.

## Hard requirements

1. **Read-only.** No POST/PATCH/DELETE on this surface. Editing is
   internal-only via the existing routers.
2. **Published-only.** Default filter is `episode.status = 'published'` AND
   a per-segment publish flag. Drafts never leak.
3. **Stable URL shape** — slugs, not internal UUIDs, in public paths.
4. **Cacheable** — strong `ETag`, `Cache-Control: public, max-age=…`,
   `Last-Modified`. Website can cache/CDN aggressively.
5. **No admin auth required for public reads** — but rate-limited and
   gated by an API key for the website's server-side fetcher (so we can
   revoke / rotate / monitor).
6. **Single egress host:** `https://api.disaffected.com` (or
   `https://192.168.51.238:8888/public/v1` on the LAN until DNS lands).
   Note: prefect host IP is `.238`, NOT `.207`. CLAUDE.md is stale.

---

## Content surface — what gets pulled

### Tier 1 — Core (ship first)

| Resource | Path | Why |
|---|---|---|
| Episode index | `GET /public/v1/episodes` | Listing pages, RSS, sitemap |
| Episode detail | `GET /public/v1/episodes/{slug}` | Episode page hero + metadata |
| Segment list (per episode) | `GET /public/v1/episodes/{slug}/segments` | Chapters / segment nav |
| Segment detail | `GET /public/v1/segments/{segment_slug}` | Standalone segment page |
| Transcript (per segment) | `GET /public/v1/segments/{segment_slug}/transcript` | Body copy, accessibility, search |
| Thumbnails (per episode) | `GET /public/v1/episodes/{slug}/thumbnails` | OG image, hero, 16x9 poster |
| Tag index | `GET /public/v1/tags` | Tag landing pages |
| Tag detail | `GET /public/v1/tags/{tag_slug}` | Episodes/segments under a tag |
| Sitemap feed | `GET /public/v1/sitemap.xml` | SEO; emits changefreq + lastmod |
| RSS feed | `GET /public/v1/rss.xml` | Podcast-style discovery |

### Tier 2 — Enrichment (ship second)

| Resource | Path | Why |
|---|---|---|
| Search | `GET /public/v1/search?q=…&type=episode\|segment\|transcript` | Site search |
| Related segments | `GET /public/v1/segments/{slug}/related` | "Watch next" |
| Quotes | `GET /public/v1/segments/{slug}/quotes` | Pull-quote blocks |
| SOTs | `GET /public/v1/segments/{slug}/sots` | Sourced video clips |
| Guests / hosts | `GET /public/v1/people/{slug}` | Bio pages |

### Tier 3 — Future

- WebSub / push notifications when an episode publishes
- GraphQL gateway (only if Tier 1+2 REST proves insufficient)

---

## Segregation: how each content type maps

This is the part the user flagged as unclear. Here is the model:

```
Episode (publish unit, has slug, status, publish_date, season/episode #)
 ├── Thumbnails (poster_16x9, og_image, hero_1x1) — selected & named in DB
 ├── Tags[] (many-to-many, tags also have slugs)
 ├── SEO block (title, description, canonical_url, og:*, twitter:*)
 └── RundownItem[] = the ordered list of segments
       └── Segment (own slug, own publish flag, own SEO block, own thumbnail override)
             ├── Transcript (whisper output, diarized JSON, plain-text fallback)
             ├── Cues[] (SOT, FSQ, GFX, VO, NAT, BUMP, …)
             │     └── each cue can have its own asset (video clip, image, audio)
             ├── Quotes[] (extracted pull-quotes)
             └── Tags[] (segment-level tags, optional override of episode tags)
```

**Key segregation rules:**

1. **Episode is the publish unit.** A segment cannot be published unless its
   parent episode is published. (Enforced in the public query — JOIN +
   filter both flags.)
2. **Segment is independently URL-addressable** but inherits episode SEO
   defaults. Segment-level SEO overrides episode-level when set.
3. **Transcript belongs to the segment, not the episode.** Episode
   "transcript" = concatenation of segment transcripts in rundown order
   (computed view, not stored separately).
4. **Tags live at both levels.** Episode tags = union of all segment tags
   plus episode-only tags. Public API exposes both: a segment lists its own
   tags; an episode lists its own + aggregated.
5. **Thumbnails:** episode has the canonical poster + OG; segments may
   override with their own. The `/thumbnails` endpoint always returns the
   resolved set (override-or-inherit).
6. **Cues are NOT exposed publicly by default.** They are production
   metadata. Exception: SOTs and quotes get explicit endpoints because
   those are real public content. GFX/FSQ/VO/NAT/BUMP stay internal.

---

## Security model

### AuthN/AuthZ

- **Website server-side fetcher** uses a long-lived API key (existing
  `api_key` system in show-build, role = `public_reader`).
- **No JWT** on this surface — JWTs are for editor users.
- **No browser-side calls to show-build directly.** The website's SSR/SSG
  layer fetches at build time or via a thin BFF route. Prevents key leak.
- Rate limit per key: 600 req/min burst, 60 req/min sustained.
- `public_reader` role permissions: `episodes:read:published`,
  `segments:read:published`, `transcripts:read:published`,
  `tags:read`, `thumbnails:read:published`, `sitemap:read`.

### Network

- Behind nginx/reverse proxy with TLS only. HTTP redirects to HTTPS.
- CORS: locked to the website's domains (`disaffected.com`,
  `*.disaffected.com`, `localhost:3000` for dev).
- Asset URLs (thumbnails, transcript audio, SOT clips) point to a
  **separate static origin** with signed-URL or hashed-path access. The
  API never streams binary; it returns URLs.

### Data hygiene

- A pre-publish guard scrubs PII fields before exposure (host notes,
  internal slack/email, draft titles).
- An explicit `public_payload` view layer (Pydantic schema or DB view) —
  never `model_dump()` an ORM object directly into the response. This
  prevents accidental column leaks when new fields are added.
- A `published_at` timestamp + `unpublished_at` timestamp drive cache
  invalidation. Website CDN purges on `unpublished_at` set.

---

## Implementation plan (sharp)

### Phase 0 — Coordination (this week)
- [ ] Confirm with website team: SSG vs SSR, build-time pull vs
      runtime, how often they rebuild.
- [ ] Confirm domain: `api.disaffected.com` vs path-prefix on existing host.
- [ ] Confirm asset CDN: do thumbnails/transcripts go through the same
      origin or a separate static bucket?

### Phase 1 — Backend skeleton
- [ ] New router package `app/routers/public/` with sub-routers:
      `episodes_public.py`, `segments_public.py`, `transcripts_public.py`,
      `tags_public.py`, `thumbnails_public.py`, `feeds_public.py`.
- [ ] New Pydantic schemas in `app/schemas/public/` — strict,
      explicit field allow-lists, no ORM passthrough.
- [ ] New service `app/services/public_query_service.py` — owns the
      "is publishable?" predicate, the slug resolution, the ETag computation.
- [ ] New role `public_reader` + API key issuance in RBAC.
- [ ] Mount under `/public/v1/*`. Keep separate from `/api/*`.

### Phase 2 — Episode + segment surface (Tier 1 minus transcripts)
- [ ] `GET /public/v1/episodes` — paginated, sortable by publish_date.
- [ ] `GET /public/v1/episodes/{slug}` — full detail.
- [ ] `GET /public/v1/episodes/{slug}/segments` — ordered by rundown.
- [ ] `GET /public/v1/segments/{slug}` — segment detail with episode link.
- [ ] `GET /public/v1/episodes/{slug}/thumbnails` — resolved thumbnail set.
- [ ] ETag + Last-Modified on every response.

### Phase 3 — Transcripts
- [ ] Decide storage shape: store transcripts in `transcripts` table with
      columns `segment_id`, `text_plain`, `vtt`, `srt`, `json_diarized`,
      `language`, `generated_at`, `published`.
- [ ] Background job (Celery `compilation` queue) that runs whisper output
      → publishable transcript artifacts when an episode goes published.
- [ ] `GET /public/v1/segments/{slug}/transcript?format=plain|vtt|srt|json`
      — returns the requested format with appropriate `Content-Type`.

### Phase 4 — Tags + SEO + Feeds
- [ ] `GET /public/v1/tags`, `/tags/{slug}` — listing + episodes/segments.
- [ ] `GET /public/v1/sitemap.xml` — auto-generated, includes all
      published episodes + segments + tag pages, with lastmod from
      `published_at`/`updated_at`.
- [ ] `GET /public/v1/rss.xml` — episode feed with enclosures.
- [ ] SEO block returned inline on episode/segment detail responses
      (canonical_url, og:title, og:description, og:image, twitter:card,
      structured_data JSON-LD).

### Phase 5 — Search + related (Tier 2)
- [ ] Postgres FTS or Meilisearch index over title/description/transcript.
- [ ] `GET /public/v1/search?q=…&type=…&limit=…`.
- [ ] `GET /public/v1/segments/{slug}/related` — naive tag-overlap scoring
      first, vector similarity later.

### Phase 6 — Cache + ops
- [ ] CDN in front (Cloudflare or nginx microcache).
- [ ] Webhook on publish/unpublish to purge CDN keys.
- [ ] Metrics: per-endpoint p50/p95, cache hit ratio, error rate.

---

## Decision points — needed from website team to start scaffolding

These are blockers. Each one materially changes the API contract or the
materialization task. Listed by what they affect:

| # | Status | Decision | Resolution / default |
|---|---|---|---|
| 1 | ✅ RESOLVED 2026-05-08 | SSG vs SSR vs hybrid | **SSG** with build-time pull + webhook-purge on republish. Plus admin-only freshness widget on the website (show-build exposes `X-Showbuild-*` headers + `/_admin/purge` + `/_admin/rematerialize`). |
| 2 | ✅ RESOLVED 2026-05-08 | Public hostnames | `api.disaffected.com` + `media.disaffected.com` under `*.disaffected.com` wildcard cert |
| 3 | ✅ RESOLVED 2026-05-08 | Image variants | **show-build resizes via Celery `assets` queue.** Pre-generated WebP variants per ratio; `srcset` returned in API. |
| 4 | open | Transcript embedding | Default: both inline JSON + static VTT URL |
| 5 | ✅ RESOLVED 2026-05-08 | Script body exposure | `script_content` permanently FORBIDDEN. Public text comes from `segment_transcripts` (whisper+diarization). No opt-in path exists. |
| 6 | open | Search in v1? | Default: defer to Tier 2 |
| 7 | open | Related segments | Default: tag-overlap; vector similarity later |
| 8 | open | Pagination flavor | Default: cursor |
| 9 | open | Multilingual at launch? | Default: English-only |
| 10 | open | Webhook target URL + secret | Default: placeholder until website team provides |
| 11 | ✅ RESOLVED 2026-05-08 | Public vs paywall/member-tier? | Tiering IN. `access_tier` column on episodes + segments, default `'public'`. `access_tiers` lookup table (slug, name, rank). Public listings always show paywalled items with `requires_tier` info; gated fields omitted unless `X-Viewer-Tier-Rank` header authorizes. Full distribution-matrix design in sibling doc `PUBLICATION_DESTINATIONS_PLAN.md` (out of scope for v1). |
| 12 | open | Cross-platform IDs (YouTube, GUID) | Default: include them |

**All 4 blockers resolved as of 2026-05-08. Plan is ready to scaffold.**
Remaining open items (transcript embedding format, search ship/defer,
related segments algorithm, pagination flavor, multilingual,
webhook target URL/secret, cross-platform IDs) are all defaultable
and iterable — none of them break the contract.

## Open questions for the website team

1. **Do you want pull (you fetch on build) or push (we webhook you on publish)?**
   Recommend pull-with-webhook-purge: simpler, idempotent, you stay in
   control of build cadence.
2. **Thumbnail formats?** We can serve original + auto-resized variants
   (`?w=1280&format=webp`) via an image proxy, or you can do it your end.
3. **Transcript formats?** plain text is universal; VTT for on-page
   players; JSON-diarized if you want speaker labels rendered.
4. **Multilingual?** If yes, we need a `language` query param and locale
   slugs in URLs from day one — much harder to retrofit.
5. **Pagination style?** Cursor-based recommended (`?cursor=…&limit=…`)
   over offset for stable scrolling at scale.
6. **Schema versioning?** `/public/v1` allows `/v2` later. Lock the v1
   shape as a contract once published.

---

## Risks / things to not screw up

- **Don't expose internal IDs.** Slugs only on public surface. UUID
  exposure invites scraping and ties our internal model to the website.
- **Don't leak draft fields.** Use the explicit Pydantic allow-list
  approach. Never `model_dump()` an ORM row.
- **Don't reuse editor JWT auth.** A leaked editor token must not grant
  public-surface access (it would, by default — that's why we use a
  separate role and key).
- **Don't ship without rate limiting.** The first time a script hits
  `/public/v1/episodes?limit=10000` we'll regret it.
- **Don't co-mingle public asset URLs with internal `/home/episodes`
  paths.** Public URLs must be a separate origin / signed.

---

## Concrete file layout (mirrors existing house style)

```
app/
  routers/
    public/
      __init__.py              # APIRouter(prefix="/public/v1") + sub-router includes
      _shared.py               # is_publishable(), resolve_slug(), etag helpers, deps
      episodes_public.py       # GET /episodes, /episodes/{slug}
      segments_public.py       # GET /episodes/{slug}/segments, /segments/{slug}
      transcripts_public.py    # GET /segments/{slug}/transcript
      thumbnails_public.py     # GET /episodes/{slug}/thumbnails
      tags_public.py           # GET /tags, /tags/{slug}
      feeds_public.py          # GET /sitemap.xml, /rss.xml
      schemas/
        __init__.py
        episode.py             # PublicEpisode, PublicEpisodeListItem
        segment.py             # PublicSegment, PublicSegmentListItem
        transcript.py          # PublicTranscript (plain/vtt/srt/json variants)
        thumbnail.py           # PublicThumbnailSet
        tag.py                 # PublicTag, PublicTagDetail
        seo.py                 # SeoBlock (shared, embedded in episode/segment)
  services/
    public_query_service.py    # All "publishable?" + slug resolution logic
```

Mounting in `app/main.py`:
```python
from app.routers.public import router as public_router
app.include_router(public_router)
```

## Schema reality check (2026-05-07)

Good news: most of what I assumed I'd need to add **already exists**.
The actual delta is much smaller.

### Already in place on `episodes`
- `slug` (VARCHAR(100), NOT NULL) ✅
- `publish_status` (VARCHAR(20), default `'draft'`) ✅
- `schedule_datetime` (TIMESTAMPTZ — covers "scheduled publish time") ✅
- `visibility` (`public`/`unlisted`/`private`) ✅
- `subtitle`, `description`, `tags` (CSV string), `notes` ✅
- `poster_16x9`, `poster_1x1`, `poster_9x16`, `poster_4x5` ✅
- `explicit`, `content_warnings`, `guest_*` ✅

### Already in place on `rundown_items`
- `slug` (VARCHAR(100), NOT NULL) ✅
- `subtitle`, `description`, `tags` (CSV) ✅
- `script_content` (full markdown body) ✅
- `tone`, `tone_rationale`, `tone_confidence` ✅
- `llm_generated_fields`, `description_gen_history` ✅

### Actual migration delta — `g015_public_api_publish_lifecycle.py`

```python
# Episodes: add explicit publish timestamps + SEO overrides + canonical URL
op.add_column('episodes', sa.Column('published_at', sa.DateTime(timezone=True)))
op.add_column('episodes', sa.Column('unpublished_at', sa.DateTime(timezone=True)))
op.add_column('episodes', sa.Column('seo_title', sa.String(200)))
op.add_column('episodes', sa.Column('seo_description', sa.Text))
op.add_column('episodes', sa.Column('canonical_url', sa.String(500)))
op.create_index(
    'idx_episodes_published_status',
    'episodes', ['publish_status', 'published_at'],
    postgresql_where=sa.text("publish_status = 'published'")
)
op.create_unique_constraint('uq_episodes_slug', 'episodes', ['slug'])

# Rundown items: per-segment publish flag (inherit from episode by default)
op.add_column('rundown_items', sa.Column(
    'publish_status', sa.String(20), server_default='inherit', nullable=False
))
op.add_column('rundown_items', sa.Column('seo_title', sa.String(200)))
op.add_column('rundown_items', sa.Column('seo_description', sa.Text))
op.add_column('rundown_items', sa.Column('og_poster_path', sa.String(500)))  # override only
op.create_index(
    'idx_rundown_items_episode_slug',
    'rundown_items', ['rundown_id', 'slug'],
    unique=True
)

# Access tier lookup (decision #11) — producers can rename/reorder
# without code changes. Seed with 'public' (rank 0) at migration time;
# additional tiers ('free_member', 'supporter', 'patron') added by ops.
op.create_table(
    'access_tiers',
    sa.Column('slug', sa.String(32), primary_key=True),
    sa.Column('name', sa.String(80), nullable=False),
    sa.Column('rank', sa.Integer, nullable=False, unique=True),
    sa.Column('public', sa.Boolean, nullable=False, server_default='false'),
)
op.execute("INSERT INTO access_tiers (slug, name, rank, public) "
           "VALUES ('public', 'Public', 0, true)")

# Episodes + segments get an access_tier with default 'public'.
# When this distribution-matrix lands (PUBLICATION_DESTINATIONS_PLAN.md),
# this column becomes a derived value from publication_destinations
# WHERE destination='disaffected.com'. Until then, it's the simple
# source of truth for the public API.
op.add_column('episodes', sa.Column(
    'access_tier', sa.String(32),
    sa.ForeignKey('access_tiers.slug'),
    nullable=False, server_default='public',
))
op.add_column('rundown_items', sa.Column(
    'access_tier', sa.String(32),
    sa.ForeignKey('access_tiers.slug'),
    nullable=False, server_default='public',
))

# Transcripts table — NEW. Currently transcripts are scattered.
op.create_table(
    'segment_transcripts',
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('rundown_item_id', sa.Integer,
              sa.ForeignKey('rundown_items.id', ondelete='CASCADE'),
              nullable=False, index=True),
    sa.Column('language', sa.String(10), server_default='en', nullable=False),
    sa.Column('text_plain', sa.Text, nullable=False),
    sa.Column('vtt', sa.Text),
    sa.Column('srt', sa.Text),
    sa.Column('json_diarized', postgresql.JSONB),
    sa.Column('source', sa.String(40)),  # 'whisper-medium', 'manual', etc.
    sa.Column('generated_at', sa.DateTime(timezone=True),
              server_default=sa.func.now(), nullable=False),
    sa.Column('published', sa.Boolean, server_default='false', nullable=False),
    sa.UniqueConstraint('rundown_item_id', 'language',
                        name='uq_segment_transcripts_segment_lang'),
)
```

**Open question on tags:** episode + segment `tags` are currently
comma-separated strings, NOT a normalized `tags` table. For Tier 1 we can
parse the CSV at query time and synthesize tag-slug pages on the fly.
**Tier 2 should normalize** — separate migration `g016_normalize_tags`
introducing `tags(id, slug, name, public)` and `episode_tags` /
`segment_tags` join tables, with a backfill from the CSV columns. Defer
this until tag landing pages are actually on the website roadmap.

**No `unpublished_at` from-`visibility` mapping yet:** `visibility =
'private'` is editor-only intent and should also block publication. The
`is_publishable` predicate filters BOTH `publish_status = 'published'`
AND `visibility = 'public'`.

## Core query predicate (single source of truth)

```python
# app/services/public_query_service.py

def episode_is_publishable_q(q):
    """Apply to any Episode query to filter to publicly-visible rows."""
    return q.filter(
        Episode.publish_status == 'published',
        Episode.visibility == 'public',
        Episode.is_test_data == False,
        Episode.is_dummy == False,
        Episode.published_at <= func.now(),
        or_(Episode.unpublished_at == None, Episode.unpublished_at > func.now()),
    )

def segment_is_publishable_q(q):
    """Segment is publishable iff its episode is publishable AND segment
    publish_status is 'inherit' or 'published' (not 'draft'/'unpublished').
    Joins via Rundown -> Episode (rundown_items.rundown_id -> rundowns.episode_id)."""
    return (
        episode_is_publishable_q(q.join(Rundown).join(Episode))
        .filter(
            RundownItem.publish_status.in_(['inherit', 'published']),
            RundownItem.is_test_data == False,
        )
    )
```

Every public endpoint MUST start its query through one of these helpers.
Reviewers should reject any public endpoint that does its own filtering.

## Public Pydantic schemas (the security boundary)

These are the EXACT field allow-lists. Anything not listed here does not
leave show-build. Reviewers reject any PR that uses `from_orm` /
`model_validate` directly off an Episode/RundownItem and serializes the
whole thing — every public response goes through one of these.

### `schemas/seo.py`
```python
class SeoBlock(BaseModel):
    title: str                       # episode.seo_title or fallback to title
    description: Optional[str]       # episode.seo_description or fallback to description
    canonical_url: Optional[HttpUrl]
    og_title: str                    # = title
    og_description: Optional[str]    # = description
    og_image: Optional[HttpUrl]      # resolved poster URL (separate origin)
    og_type: Literal['video.episode', 'video.other'] = 'video.episode'
    twitter_card: Literal['summary_large_image'] = 'summary_large_image'
    structured_data: dict            # JSON-LD: BroadcastEvent / VideoObject
```

### `schemas/thumbnail.py`
```python
class PublicPosterVariants(BaseModel):
    """One ratio's worth of pre-generated WebP sizes. Generated by the
    public.generate_poster_variants Celery task (queue: assets) at
    publish time. NEVER on demand."""
    default: HttpUrl                 # full-size, the canonical OG image URL
    sizes: dict[int, HttpUrl]        # {1920: url, 1280: url, 640: url, 320: url}
    srcset: str                      # ready-to-paste into <img srcset="..."/>
                                     # e.g. "url-320 320w, url-640 640w, url-1280 1280w, url-1920 1920w"

class PublicThumbnailSet(BaseModel):
    poster_16x9: Optional[PublicPosterVariants]   # web/YouTube/og:image default
    poster_1x1:  Optional[PublicPosterVariants]   # IG feed
    poster_9x16: Optional[PublicPosterVariants]   # Stories/TikTok/Reels
    poster_4x5:  Optional[PublicPosterVariants]   # FB/Twitter cards
    # NEVER expose internal filesystem paths. Resolver converts
    # episode.poster_16x9 ('/home/episodes/1234/posters/x.png') into
    # 'https://media.disaffected.com/e/{slug}/posters/poster_16x9-{width}.webp'
```

**Variant matrix** (decided 2026-05-08, can be tuned per ratio later):

| Ratio | Sizes generated | Why |
|---|---|---|
| `16x9` | 1920, 1280, 640, 320 | Most common surface (hero, cards, og:image, thumbnails) |
| `1x1`  | 1080, 512           | IG feed + small avatar fallback |
| `9x16` | 1080, 540           | Stories/Reels + half-size for previews |
| `4x5`  | 1080, 540           | Social cards + half-size for previews |

Originals stay on disk in their original format; only WebP variants are
materialized into `{episode}/public/posters/`. Quality 85 by default
(adjustable per-episode via a future override field if needed).

### `schemas/episode.py`
```python
class PublicEpisodeListItem(BaseModel):
    """Lightweight — used in /episodes index, /tags/{slug}, sitemap."""
    slug: str
    title: str
    subtitle: Optional[str]
    episode_number: Optional[int]
    season: Optional[int]            # derived from season_id -> Season.number
    duration_seconds: Optional[int]  # = actual_duration or target_duration
    published_at: datetime
    updated_at: datetime
    tags: List[str]                  # parsed from CSV
    poster_16x9: Optional[HttpUrl]   # quick render in lists; full set on detail
    explicit: bool
    access_tier: str                 # 'public' or a paid tier slug
    requires_tier: Optional['AccessTierSummary'] = None  # set when access_tier != 'public'

class AccessTierSummary(BaseModel):
    slug: str                        # e.g. 'supporter'
    name: str                        # e.g. 'Supporter'
    rank: int                        # 0=public, higher = more privileged

class PublicEpisode(PublicEpisodeListItem):
    """Full episode detail — used on /episodes/{slug}."""
    description: str
    content_warnings: Optional[str]
    guest_name: Optional[str]
    guest_bio: Optional[str]
    guest_website: Optional[HttpUrl]
    air_date: Optional[datetime]
    thumbnails: PublicThumbnailSet
    seo: SeoBlock
    segment_count: int
    segments: Optional[List['PublicSegmentListItem']] = None  # opt-in via ?include=segments
```

### `schemas/segment.py`
```python
class PublicSegmentListItem(BaseModel):
    slug: str
    episode_slug: str                # parent episode slug
    title: str
    subtitle: Optional[str]
    order: int                       # = order_in_rundown
    duration: Optional[str]          # 'HH:MM:SS' as stored
    duration_seconds: Optional[int]  # parsed for clients that want a number
    tags: List[str]
    has_transcript: bool
    poster_16x9: Optional[HttpUrl]   # override or inherited from episode

class PublicSegment(PublicSegmentListItem):
    description: str                 # public-safe rundown_items.description
    tone: Optional[str]              # public-friendly only if tone in PUBLIC_TONES
    seo: SeoBlock
    quotes: List['PublicQuote'] = []
    sots: List['PublicSot'] = []     # cue assets exposed publicly
    related: Optional[List[PublicSegmentListItem]] = None
    # Public segment text comes from segment_transcripts, NOT script_content.
    # See `PublicTranscript` for the transcript shape and the transcript endpoint.
    # `has_transcript` (inherited from PublicSegmentListItem) signals availability.
```

**Critical exclusions** — fields on the ORM that MUST NOT serialize:
- `notes` (internal production notes, episode + segment)
- `script_content` — **PERMANENTLY FORBIDDEN.** This is the pre-recorded
  production script (with stage directions, producer notes, cue blocks,
  unaired material). It is the production source of truth and never
  reaches the public API. Public segment text comes from
  `segment_transcripts` (whisper-medium + pyannote diarization,
  post-broadcast). No flag, no opt-in, no sanitizer path exists.
  See `TRANSCRIPT_PIPELINE_PLAN.md` for the transcript pipeline.
- `server_message`, `priority`, `message`, `link` (rundown_items)
- `tone_rationale`, `tone_confidence`, `auto_generate_attempts`,
  `description_gen_history`, `llm_generated_fields`, `description_model`
- `is_test_data`, `is_dummy`, `template_id`, `template_name`
- `producer`, `editor`, `recording_date` (production metadata, not public)
- `speaker_id`, internal asset IDs

A unit test enforces this: instantiate a fully-populated `Episode` and
`RundownItem` from a fixture, dump through `PublicEpisode`/`PublicSegment`,
assert that none of the exclusion-list field names appear anywhere in
the serialized JSON. New ORM columns can never accidentally leak.

### `schemas/transcript.py`
```python
class PublicTranscript(BaseModel):
    segment_slug: str
    language: str
    text_plain: str                  # always present
    vtt: Optional[str]               # only when ?format=vtt requested
    srt: Optional[str]
    json_diarized: Optional[List[dict]]
    word_count: int
    generated_at: datetime
    source: Optional[Literal['whisper-medium', 'manual', 'edited']]
```

Endpoint contract:
- `GET /segments/{slug}/transcript` → defaults to `text_plain`, response
  is JSON envelope.
- `GET /segments/{slug}/transcript.vtt` → raw VTT, `Content-Type: text/vtt`
- `GET /segments/{slug}/transcript.srt` → raw SRT, `Content-Type: text/srt`
- `GET /segments/{slug}/transcript.json` → JSON envelope including
  `json_diarized` if present and segment is published.

### `schemas/tag.py`
```python
class PublicTag(BaseModel):
    slug: str                        # slugified from CSV value
    name: str                        # display form
    episode_count: int
    segment_count: int

class PublicTagDetail(PublicTag):
    episodes: List[PublicEpisodeListItem]
    segments: List[PublicSegmentListItem]
```

### Field-leak guard test (the actual enforcement mechanism)

Pydantic schemas alone aren't enough — a future engineer can add a field
to `PublicSegment` and not realize it's sensitive. This test makes the
exclusion list a hard CI gate: a fixture row populated with sentinel
strings on every restricted column gets serialized through the public
schemas, and the serialized JSON is grepped for any sentinel.

```python
# tests/test_public_api_no_leaks.py

# Fields that MUST NEVER appear in any /public/v1 response.
# Each name maps to a sentinel string we'll plant on the fixture row,
# then assert the sentinel does not appear anywhere in the JSON output.
EPISODE_FORBIDDEN = {
    'notes':              'SENTINEL_EP_NOTES_LEAK',
    'producer':           'SENTINEL_EP_PRODUCER_LEAK',
    'editor':             'SENTINEL_EP_EDITOR_LEAK',
    'recording_date':     None,  # datetime — checked by absence of key
    'template_id':        'SENTINEL_EP_TPL_ID',
    'template_name':      'SENTINEL_EP_TPL_NAME',
    'is_test_data':       None,
    'is_dummy':           None,
}

SEGMENT_FORBIDDEN = {
    # PERMANENTLY FORBIDDEN — pre-recorded script with stage directions,
    # producer notes, cue blocks, unaired material. Public text comes
    # from segment_transcripts (post-broadcast whisper+diarization).
    'script_content':           'SENTINEL_SEG_SCRIPT_CONTENT_LEAK',
    'notes':                    'SENTINEL_SEG_NOTES',
    'server_message':           'SENTINEL_SEG_SERVER_MSG',
    'priority':                 'SENTINEL_SEG_PRIORITY',
    'message':                  'SENTINEL_SEG_MESSAGE',
    'tone_rationale':           'SENTINEL_SEG_TONE_RATIONALE',
    'tone_confidence':          None,
    'auto_generate_attempts':   None,
    'description_gen_history':  ['SENTINEL_SEG_GEN_HISTORY'],
    'llm_generated_fields':     ['SENTINEL_SEG_LLM_FIELDS'],
    'description_model':        'SENTINEL_SEG_MODEL_NAME',
    'speaker_id':               None,
}

@pytest.fixture
def loaded_episode(db):
    """Create one published episode + one segment with EVERY column populated,
    using sentinel strings on forbidden fields."""
    ep = Episode(
        slug='leak-test',
        title='Leak Test Episode',
        publish_status='published',
        published_at=now_utc(),
        visibility='public',
        description='public description',
        notes=EPISODE_FORBIDDEN['notes'],
        producer=EPISODE_FORBIDDEN['producer'],
        editor=EPISODE_FORBIDDEN['editor'],
        template_id=EPISODE_FORBIDDEN['template_id'],
        template_name=EPISODE_FORBIDDEN['template_name'],
        is_test_data=False,  # has to be False to be publishable
        # ... every other column populated normally
    )
    seg = RundownItem(
        slug='leak-test-seg',
        title='Leak Test Segment',
        publish_status='published',
        description='public segment description',
        script_content=SEGMENT_FORBIDDEN['script_content'],  # full sentinel string for grep test
        notes=SEGMENT_FORBIDDEN['notes'],
        server_message=SEGMENT_FORBIDDEN['server_message'],
        priority=SEGMENT_FORBIDDEN['priority'],
        message=SEGMENT_FORBIDDEN['message'],
        tone_rationale=SEGMENT_FORBIDDEN['tone_rationale'],
        description_gen_history=SEGMENT_FORBIDDEN['description_gen_history'],
        llm_generated_fields=SEGMENT_FORBIDDEN['llm_generated_fields'],
        description_model=SEGMENT_FORBIDDEN['description_model'],
        # ...
    )
    db.add_all([ep, seg]); db.commit()
    return ep

def _all_sentinels():
    out = []
    for table in (EPISODE_FORBIDDEN, SEGMENT_FORBIDDEN):
        for v in table.values():
            if isinstance(v, str): out.append(v)
            elif isinstance(v, list): out.extend(x for x in v if isinstance(x, str))
    return out

def test_episode_detail_does_not_leak_forbidden_fields(client, loaded_episode):
    r = client.get('/public/v1/episodes/leak-test',
                   headers={'X-API-Key': PUBLIC_TEST_KEY})
    assert r.status_code == 200
    body = r.text  # raw JSON text — sentinel grep
    for sentinel in _all_sentinels():
        assert sentinel not in body, f"LEAK: {sentinel} appeared in response"

def test_episode_detail_does_not_leak_forbidden_field_NAMES(client, loaded_episode):
    """Even with empty values, the field NAME shouldn't appear as a JSON key."""
    r = client.get('/public/v1/episodes/leak-test?include=segments',
                   headers={'X-API-Key': PUBLIC_TEST_KEY})
    data = r.json()
    flat_keys = _all_keys_recursive(data)
    forbidden_names = set(EPISODE_FORBIDDEN) | set(SEGMENT_FORBIDDEN)
    leaked = forbidden_names & flat_keys
    assert not leaked, f"LEAK: forbidden field names in keys: {leaked}"

def test_script_content_never_appears_in_any_public_response(client, loaded_episode):
    """script_content is FORBIDDEN at every public endpoint, no opt-in path."""
    sentinel = SEGMENT_FORBIDDEN['script_content']
    for path in [
        '/public/v1/episodes/leak-test',
        '/public/v1/episodes/leak-test?include=segments',
        '/public/v1/episodes/leak-test/segments',
        '/public/v1/segments/leak-test-seg',
        '/public/v1/segments/leak-test-seg?include=body',     # opt-in must not work
        '/public/v1/segments/leak-test-seg?include=script',   # any future include
    ]:
        r = client.get(path, headers={'X-API-Key': PUBLIC_TEST_KEY})
        assert sentinel not in r.text, f"LEAK at {path}: script_content reached public"
        # body field must not exist in segment responses at all
        if 'segments/leak-test-seg' in path:
            assert 'body' not in (r.json() if r.headers.get('content-type','').startswith('application/json') else {}), \
                f"PublicSegment must not have a 'body' field — script is never public"
```

Add a similar test for the segment list endpoint and the transcript
endpoint. The path-leak guard is parallel:

```python
def test_no_response_contains_internal_paths(client, loaded_episode):
    r = client.get('/public/v1/episodes/leak-test',
                   headers={'X-API-Key': PUBLIC_TEST_KEY})
    body = r.text
    assert '/home/episodes/' not in body
    assert '/srv/show-build' not in body
    # internal asset_id format is e.g. 'EP-1234' or UUID — episode.asset_id
    # should not appear in any public response (slug only)
    assert loaded_episode.asset_id not in body
```

This pair of tests is the hill we die on. They run in CI on every PR.
A future engineer adding a column to `Episode` doesn't need to know
this plan exists — if they accidentally include it in a public schema,
the test fails the build with a precise message naming the leaked field.

### `script_content` sanitizer — REMOVED (decision #5 resolved)

There is no sanitizer because there is no public path to `script_content`.
The pre-recorded production script (with stage directions, producer
notes, cue blocks, unaired material) stays internal forever.

**Public segment text comes from `segment_transcripts`** — generated
post-broadcast from the actual recording via whisper-medium + pyannote
diarization, with human-confirmed speaker labels. Because the
transcript starts from audio that already aired publicly, it has no
production-internals leak class — there are no stage directions in
audio recordings.

See `TRANSCRIPT_PIPELINE_PLAN.md` (TODO — to be written) for:
- Whisper service integration (host TBD, see ACTIVE_WORK_QUEUE.md)
- pyannote diarization integration
- Per-segment audio extraction + alignment
- Speaker-labeling tool (lives under `/tools` route)
- Celery task chain on `compilation` queue
- `segment_transcripts` lifecycle (draft → labeled → published)

## Auth wiring (reuses existing api_key system)

```python
# in _shared.py
from app.auth.dependencies import require_api_key_with_permission

require_public_read = require_api_key_with_permission('public:read')

# usage:
@router.get('/episodes')
async def list_episodes(_: ApiKey = Depends(require_public_read), ...):
    ...
```

New permission `public:read` added to RBAC seed. New role `public_reader`
gets only this permission. One API key per consumer (website prod,
website staging, sitemap crawler).

## Asset URL resolver (filesystem → public URL)

Internal storage layout (already in production):
```
/home/episodes/{episode_asset_id}/
  posters/
    poster_16x9.png
    poster_1x1.png
    poster_9x16.png
    poster_4x5.png
  assets/
    video/   {assetID}.mp4         (SOT clips)
    images/  {assetID}.png         (FSQ, GFX backgrounds)
    audio/   {assetID}.mp3         (NAT, music beds)
    graphics/{assetID}.png         (lower-thirds, etc.)
  transcripts/
    {rundown_item_asset_id}.json   (whisper diarized)
    {rundown_item_asset_id}.vtt
```

DB columns store **relative-or-absolute filesystem paths** today
(`episodes.poster_16x9 = '/home/episodes/.../posters/poster_16x9.png'`).
These paths CANNOT leak to the public — they expose the internal mount
structure and asset_ids that double as cache keys for production.

### Resolver contract

```python
# app/services/public_asset_resolver.py

class PublicAssetResolver:
    """Translates internal asset paths into public-facing URLs.

    NEVER returns a URL that hits the show-build origin directly.
    All public asset traffic goes through the media origin
    (https://media.disaffected.com) which is a thin nginx in front of a
    sync'd copy of /home/episodes/{slug}/public/.
    """

    PUBLIC_BASE = "https://media.disaffected.com"   # configurable

    def episode_poster(self, episode: Episode, ratio: str) -> Optional[HttpUrl]:
        """Return URL for the episode poster, or None if missing/private."""
        path = getattr(episode, f'poster_{ratio}', None)
        if not path:
            return None
        return self._resolve(episode_slug=episode.slug,
                             kind='poster',
                             ratio=ratio,
                             ext=Path(path).suffix)

    def segment_poster(self, segment: RundownItem, episode: Episode,
                       ratio: str) -> Optional[HttpUrl]:
        """Segment override or inherited episode poster."""
        if segment.og_poster_path:
            return self._resolve(episode_slug=episode.slug,
                                 segment_slug=segment.slug,
                                 kind='poster',
                                 ratio=ratio,
                                 ext=Path(segment.og_poster_path).suffix)
        return self.episode_poster(episode, ratio)

    def cue_asset(self, cue: Cue, episode: Episode) -> Optional[HttpUrl]:
        """SOT clip, FSQ image, etc. Only called for cue types that
        are explicitly public (SOT, quote-image)."""
        kind_dir = {'SOT': 'video', 'FSQ': 'images',
                    'NAT': 'audio', 'GFX': 'graphics'}.get(cue.cue_type)
        if not kind_dir:
            return None
        return self._resolve(episode_slug=episode.slug,
                             kind=kind_dir,
                             asset_id=cue.asset_id,
                             ext=cue.file_extension)

    def transcript(self, segment: RundownItem, episode: Episode,
                   format: str) -> Optional[HttpUrl]:
        """Used when transcript is served as a static file rather than
        DB-backed. Only for VTT/SRT — JSON envelope stays inline."""
        if format not in ('vtt', 'srt'):
            return None
        return self._resolve(episode_slug=episode.slug,
                             segment_slug=segment.slug,
                             kind='transcript',
                             ext=f'.{format}')

    def _resolve(self, **parts) -> HttpUrl:
        """Build a stable, content-addressable URL.

        Schema: {PUBLIC_BASE}/e/{episode_slug}/[s/{segment_slug}/]{kind}_{ratio_or_id}.{ext}

        Example: https://media.disaffected.com/e/the-cult-of-ai/poster_16x9.webp
        Example: https://media.disaffected.com/e/the-cult-of-ai/s/opening-monologue/transcript.vtt
        Example: https://media.disaffected.com/e/the-cult-of-ai/sots/abc123.mp4
        """
        ...
```

### Why a separate origin

1. **Path-leak prevention.** Public URLs never reveal `/home/episodes/`,
   asset-id internal hex, or any infrastructure detail.
2. **Independent cache TTLs.** Image CDN can hold posters for a year;
   API responses revalidate hourly.
3. **Independent rate limits.** A poster being hotlinked from social
   does not eat into API quota.
4. **Different access model.** Static files behind signed URLs (HMAC
   over `{episode_slug, segment_slug, kind, exp}`) for any
   not-yet-published preview links. Public-published assets are
   plain-public.
5. **Independent invalidation.** Webhook on republish purges the slug
   path on the media origin; API CDN purges its own keys.

### Origin sync mechanism

Three options, in order of recommendation:

**A) nginx alias from same host (simplest).**
A virtualhost `media.disaffected.com` on the same prefect host that
`alias`-maps `/e/{slug}/...` → `/home/episodes/{episode_asset_id}/public/...`.
A Celery task `materialize_public_assets(episode_id)` runs on
publish/unpublish and copies (or symlinks) the public-safe files into
`{episode_dir}/public/` with the slug-friendly names. **Recommended for
launch — no new infra.**

**B) Object storage (S3/R2/MinIO).**
Same materialize task pushes to a bucket. CDN in front. Better for
scale, more moving parts. Migrate to this when traffic justifies it.

**C) Direct serve from show-build origin under a `/media/...` prefix.**
**Rejected.** Couples public traffic to API origin, exposes internal
structure if alias rules drift, makes invalidation harder.

### Materialization task (option A)

```python
# app/tasks/public_materialize.py — Celery 'compilation' queue
@celery_app.task(name='public.materialize_episode')
def materialize_episode(episode_id: int):
    """Run on publish_status -> 'published' AND on unpublished -> any change.
    Idempotent: re-running produces same output."""
    ep = db.query(Episode).get(episode_id)
    pub_dir = Path(f'/home/episodes/{ep.asset_id}/public')

    if ep.publish_status != 'published' or ep.visibility != 'public':
        # Tear down any prior materialization
        if pub_dir.exists():
            shutil.rmtree(pub_dir)
        cdn_purge(f'/e/{ep.slug}/')
        return

    pub_dir.mkdir(parents=True, exist_ok=True)
    # 1. Posters: dispatched to assets queue for parallel resize/encode.
    #    See public.generate_poster_variants below — runs in parallel
    #    with the rest of materialize, joined before invalidate_caches.
    poster_job = generate_poster_variants.delay(episode_id)

    # 2. Per-segment public assets
    for ri in [r for r in ep.rundown_items
               if r.publish_status in ('inherit', 'published')]:
        seg_dir = pub_dir / 's' / ri.slug
        seg_dir.mkdir(parents=True, exist_ok=True)
        # Transcript files
        if (t := get_published_transcript(ri.id)):
            (seg_dir / 'transcript.vtt').write_text(t.vtt or '')
            (seg_dir / 'transcript.srt').write_text(t.srt or '')
            (seg_dir / 'transcript.txt').write_text(t.text_plain)
        # SOT/FSQ clips: only for cues marked public
        for cue in ri.public_cues():
            link_or_copy(cue.source_path, seg_dir / 'sots' / f'{cue.asset_id}.mp4')

    cdn_purge(f'/e/{ep.slug}/')
```

This is the single point that decides what reaches the public origin.
**Anything not materialized cannot be served**, even if a path leaks
into a response — defense in depth.

### Poster variant generator (Celery `assets` queue)

```python
# app/tasks/public_materialize.py
VARIANT_WIDTHS = {
    '16x9': [1920, 1280, 640, 320],
    '1x1':  [1080, 512],
    '9x16': [1080, 540],
    '4x5':  [1080, 540],
}

@celery_app.task(name='public.generate_poster_variants', queue='assets')
def generate_poster_variants(episode_id: int):
    """Pre-generate WebP variants for every poster ratio.
    Idempotent: skips files whose mtime is newer than the source."""
    ep = db.query(Episode).get(episode_id)
    pub_dir = Path(f'/home/episodes/{ep.asset_id}/public/posters')
    pub_dir.mkdir(parents=True, exist_ok=True)

    for ratio, widths in VARIANT_WIDTHS.items():
        src = getattr(ep, f'poster_{ratio}', None)
        if not src or not Path(src).exists():
            continue
        # Full-size canonical
        full_dst = pub_dir / f'poster_{ratio}.webp'
        if _stale(full_dst, src):
            generate_webp(src, full_dst, width=None, quality=85)
        # Sized variants
        for w in widths:
            dst = pub_dir / f'poster_{ratio}-{w}.webp'
            if _stale(dst, src):
                generate_webp(src, dst, width=w, quality=85)

def _stale(dst: Path, src: str) -> bool:
    return not dst.exists() or dst.stat().st_mtime < Path(src).stat().st_mtime
```

This runs on the existing `assets` queue (same queue as the SOT-thumbnail
worker). Episodes typically have 4 ratios × ~3 sizes = ~12 WebP encodes
per publish — well within current worker capacity.

## Tier gating (decision #11)

### Model

- Every episode and every segment has `access_tier`, FK to `access_tiers.slug`. Default `'public'`.
- `access_tiers` is a small lookup: `(slug, name, rank, public)`. Producers can add/rename/reorder via admin UI without code changes. Rank ordinal — viewer with rank ≥ content rank gets in.
- For v1: episodes and segments only. Future distribution-matrix
  (`PUBLICATION_DESTINATIONS_PLAN.md`) will replace this with per-destination tiering.

### Listings ALWAYS show paywalled content

Listing endpoints (`/episodes`, `/tags/{slug}`, sitemap) return paywalled
items the same as public ones, with `access_tier` and `requires_tier`
populated. The website renders "🔒 Patron" badges and "Subscribe to
watch" CTAs. **Discovery is never gated; access is.**

### Detail responses redact gated fields when caller is below the tier

Caller indicates the viewer's tier via header:

```
X-Viewer-Tier-Rank: 2     # the website's server-side fetcher derived this from its own auth
```

If absent or `0`, treat viewer as anonymous public.

For an episode/segment with `access_tier_rank > viewer_rank`:
- ALWAYS returned: `slug, title, subtitle, description, tags, poster_*,
  published_at, access_tier, requires_tier, episode_number, season, explicit, duration_seconds`
- REDACTED: `transcript`, `quotes`, `sots`, `body`-equivalents, `related`,
  any URL fields that point to gated media (video stream, downloads)
- Response includes `gate: {required_tier, required_rank, message}` so
  the website can render the paywall UI

```
GET /public/v1/episodes/the-cult-of-ai
X-Viewer-Tier-Rank: 0
→ 200 — metadata visible, transcript/sots/quotes redacted, gate object present

GET /public/v1/episodes/the-cult-of-ai
X-Viewer-Tier-Rank: 2          (website knows this user is a Supporter)
→ 200 — full content
```

### New public endpoint — tier registry

```
GET /public/v1/access-tiers
→ [{slug:'public',     name:'Public',     rank:0, public:true},
   {slug:'free_member',name:'Free Member',rank:1, public:false},
   {slug:'supporter',  name:'Supporter',  rank:2, public:false},
   {slug:'patron',     name:'Patron',     rank:3, public:false}]
```

Lets the website render consistent tier badges + drives the chat-room
gate (Discord OAuth + tier check both consume this list). Show-build is
canonical for the tier registry across the platform.

### Trust model for `X-Viewer-Tier-Rank`

The website's server-side fetcher vouches for the viewer; show-build
trusts the header **only when the API key is `public-reader` or higher
permission**. The website's identity provider (Patreon / Memberful /
Discord roles / custom — undecided, see `PUBLICATION_DESTINATIONS_PLAN.md`)
is upstream of show-build. Browser-direct calls cannot set this header
(CORS-locked + no API key in browser).

### Field-leak guard — tiering interaction

Add tests that:
1. Anonymous (`X-Viewer-Tier-Rank: 0`) request to a `tier='supporter'`
   episode — assert no transcript text, no SOT URLs, no quote bodies in response.
2. Authorized (rank ≥ required) request — assert all gated fields present.
3. `requires_tier` always populated when `access_tier != 'public'`,
   regardless of viewer auth.

## Auth specifics — RBAC seed + key issuance + rate limit

### Permission and role to seed

Add to `app/services/rbac_service.py :: seed_default_permissions` —
matches the existing `(name, display_name, resource, action, scope)` tuple
pattern:

```python
# Public API (read-only website surface)
("public.episodes.read",    "Read Published Episodes",    "public", "read", "global"),
("public.segments.read",    "Read Published Segments",    "public", "read", "global"),
("public.transcripts.read", "Read Published Transcripts", "public", "read", "global"),
("public.tags.read",        "Read Public Tags",           "public", "read", "global"),
("public.feeds.read",       "Read Public Feeds (sitemap/RSS)", "public", "read", "global"),
```

And one new role:

```python
("Public Reader", "public-reader",
 "Read-only public-API consumer (website server-side fetcher)",
 9,        # display_order — keep below all editor roles
 True,     # is_system
 None,     # organization scope
 [
   "public.episodes.read",
   "public.segments.read",
   "public.transcripts.read",
   "public.tags.read",
   "public.feeds.read",
 ]),
```

`scope='global'` is correct — published content is org-agnostic for the
public surface; org-level filtering is editor-only.

### Key issuance flow (one key per consumer)

1. Operator creates a service user (e.g. `website-prod`,
   `website-staging`, `sitemap-crawler`) via existing user admin.
2. Assigns role `public-reader`.
3. Issues an API key bound to that user via the existing
   `api_keys` table (no schema change needed). Key is a 32-byte
   secret, stored hashed (Argon2/bcrypt — whatever the existing
   pattern is); shown once at creation.
4. Key gets a label and a `revoked_at` column for clean rotation.
5. Operator pastes key into the website's environment as
   `SHOWBUILD_API_KEY` — never commit, never log.

### Auth wiring at the endpoint

```python
# app/routers/public/_shared.py
from app.auth.dependencies import require_api_key_with_permission

# Each endpoint grabs the narrowest possible permission
require_episode_read    = require_api_key_with_permission("public.episodes.read")
require_segment_read    = require_api_key_with_permission("public.segments.read")
require_transcript_read = require_api_key_with_permission("public.transcripts.read")
require_tag_read        = require_api_key_with_permission("public.tags.read")
require_feed_read       = require_api_key_with_permission("public.feeds.read")
```

Why narrow per-resource: lets us issue a key that can fetch transcripts
but NOT episode metadata (use case: a third-party transcription
display) or vice versa.

**No JWT acceptance on /public/v1.** Editor sessions must not
accidentally authorize public-API calls — protects against a leaked
JWT being used to scrape published content.

### Rate limit

Token-bucket per-key, stored in Redis (already in stack). Two buckets
per key:

| Bucket | Capacity | Refill | Why |
|---|---|---|---|
| `burst` | 60 | 1/sec | Smooth out a build process hitting many endpoints in quick succession |
| `sustained` | 600 | 10/min | Cap an hour-long burst at ~36k requests, an SSG full-rebuild's worth |

Headers on every response:
```
X-RateLimit-Limit-Burst:     60
X-RateLimit-Remaining-Burst: 47
X-RateLimit-Reset-Burst:     1709123456
X-RateLimit-Limit-Sustained:     600
X-RateLimit-Remaining-Sustained: 412
X-RateLimit-Reset-Sustained:     1709123896
```

429 response body:
```json
{"error": "rate_limit_exceeded", "retry_after_seconds": 13,
 "bucket": "burst"}
```

Per-key buckets can be tuned in `api_configs` if a particular consumer
needs more (the sitemap crawler is a candidate for elevated sustained).

### Key rotation runbook

1. Issue new key (label = `website-prod-2`).
2. Update website env var, deploy.
3. Confirm new key sees traffic (check `api_key_audit` table).
4. Revoke old key (set `revoked_at`).
5. Confirm old key now returns 401.

Document this in `docs/RBAC_AUTHENTICATION_GUIDE.md` once the public
surface ships.

### CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://disaffected.com",
        "https://www.disaffected.com",
        "https://staging.disaffected.com",
        "http://localhost:3000",  # dev
    ],
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["X-API-Key", "If-None-Match", "If-Modified-Since"],
    max_age=86400,
)
```

Note: CORS only matters for browser-direct calls. Per the design, the
website's server-side fetcher (Node SSG/SSR) is not subject to CORS.
The CORS allow-list exists as a defense-in-depth measure if a frontend
team accidentally tries to call us from the browser; they'll get a CORS
error instead of leaking the API key into client JS.

## Admin freshness signaling

The website renders an admin-only chip showing cache state on each
episode/segment page (visible only to users it has authenticated as
admin on its own side — show-build does not gate this). The widget
itself lives on the website. Show-build's job is to expose the data
and the actions.

### Response headers (on every `/public/v1/*` response)

```
X-Showbuild-Cache-Generated: 2026-05-08T12:35:00Z   # when this response body was assembled
X-Showbuild-Source-Updated:  2026-05-08T12:30:00Z   # max(updated_at) of underlying rows
X-Showbuild-Materialized-At: 2026-05-08T12:34:00Z   # mtime of {episode}/public/ dir
```

These let the website show three timestamps without making three calls.
SSG bakes them into the page footer at build time; SSR-rendered pages
read them per request.

### Admin endpoints

Separate from the read endpoints. Different permission, separate API
key — a leaked reader key cannot trigger purges or rematerialization.

```
GET  /public/v1/_admin/freshness?slug={slug}
        → {cache_generated, source_updated, materialized_at,
           queue_state: {materialize: 'idle'|'queued'|'running',
                         poster_variants: '...'}}

POST /public/v1/_admin/purge?slug={slug}
        → 202 Accepted
        Triggers: CDN purge for /e/{slug}/* on api + media origins,
                  internal Redis cache DEL for episode + listings.
        Does NOT re-materialize (use the next endpoint for that).

POST /public/v1/_admin/rematerialize?slug={slug}
        → 202 Accepted, body: {job_id: "celery-uuid"}
        Re-runs public.materialize_episode + generate_poster_variants
        + invalidate_caches in sequence.
```

### New permission + role (add to RBAC seed)

```python
("public.admin", "Public API Admin (cache + materialize)",
 "public", "admin", "global"),

# New role:
("Public Surface Admin", "public-surface-admin",
 "Can purge/rematerialize public-API caches",
 9, True, None,
 ["public.admin",
  "public.episodes.read", "public.segments.read",
  "public.transcripts.read", "public.tags.read",
  "public.feeds.read"]),
```

The website uses TWO API keys:
- `website-prod` (role `public-reader`) for normal traffic — long-lived
- `website-admin` (role `public-surface-admin`) for the freshness widget — only used in admin sessions

### What the website team builds (informational, not our work)

- A small admin chip displayed on every episode/segment page in the website's admin chrome
- Reads the three `X-Showbuild-*` headers (baked at build time for SSG)
- Buttons: "Purge cache" → calls `/_admin/purge`; "Rematerialize" → calls
  `/_admin/rematerialize`; "Trigger site rebuild" → hits the website's own
  deploy hook (Vercel/Netlify/GH Actions — entirely on the website's side)
- Visible only when the website's own admin auth says the current user is an admin

## ETag strategy

Episode/segment ETag = `sha256(updated_at + published_at + asset_versions)`
truncated to 16 hex. Cheap to compute, changes on any meaningful edit.
Listings use `MAX(updated_at)` across the result set + filter params.

## Publish-event lifecycle (the chain of side effects)

When an editor flips an episode from `draft`/`scheduled` to `published`,
or from `published` back to `unpublished`, a deterministic chain runs.
Every step is idempotent: replaying the same publish event must produce
the same output. Failures are observable via `jobs` table; the editor UI
shows publish-state per stage.

```
[1] PATCH /api/episodes/{id}  body={publish_status: "published"}
        |
        | (in transaction)
        | - validate: episode has slug, title, at least one segment,
        |             at least 1 published transcript? (config flag)
        | - set episode.published_at = NOW()
        | - clear episode.unpublished_at
        | - persist
        |
        v
[2] DB AFTER UPDATE trigger / SQLAlchemy event hook
        |
        | publishes Celery event to 'compilation' queue:
        | - public.materialize_episode(episode_id)
        |
        v
[3] Celery: public.materialize_episode
        |
        | a. tear down stale {episode}/public/ if status != published
        | b. otherwise: rebuild posters (PNG -> WebP), copy public-cue
        |    assets, write transcripts to disk, generate sitemap row,
        |    write OG image variants
        | c. on success: chain to public.invalidate_caches
        | d. on failure: write to jobs table with stage='materialize',
        |    raise alert (existing alerting), DO NOT proceed to invalidate
        |
        v
[4] Celery: public.invalidate_caches
        |
        | a. CDN purge for /e/{slug}/* (api + media origins)
        | b. internal Redis cache: DEL public:episode:{slug},
        |    public:episodes:list, public:sitemap, public:rss
        | c. emit notification on chain to public.notify_consumers
        |
        v
[5] Celery: public.notify_consumers
        |
        | For every webhook configured in api_configs (workflow=public,
        | category=consumer):
        |   POST {target_url} with HMAC signature header
        |        body: {event: "episode.published",
        |               episode_slug: "...", episode_id: 123,
        |               published_at: "...", api_url: "..."}
        |
        | The website's job is to call back to /public/v1/episodes/{slug}
        | for full data. The webhook is a HEADS-UP, not a delivery.
```

### Failure handling per stage

| Stage | If it fails | Recovery |
|---|---|---|
| 1 (DB write) | Editor sees error, no side effects fire | Editor retries; nothing to undo |
| 3 (materialize) | Episode is `published` in DB but no public files exist. **Public API still serves** — but media URLs 404 | Auto-retry 3x with backoff; manual re-run via admin button |
| 4 (cache invalidate) | Stale data served until next TTL | Auto-retry; TTL bounds damage to ~5 min |
| 5 (notify) | Webhook target offline | Per-target dead-letter queue, replays on next publish; consumer can also poll |

### Webhook delivery — the contract for the website team

```http
POST https://disaffected.com/_webhooks/showbuild HTTP/1.1
Content-Type: application/json
X-ShowBuild-Event: episode.published
X-ShowBuild-Delivery: 7c0e... (UUID, idempotency key)
X-ShowBuild-Timestamp: 1709123456
X-ShowBuild-Signature: sha256=hex...
   (HMAC-SHA256 over `{timestamp}.{raw_body}` using shared secret)

{
  "event": "episode.published",
  "occurred_at": "2026-05-08T12:34:56Z",
  "episode": {
    "id": 1234,
    "slug": "the-cult-of-ai",
    "season": 4,
    "episode_number": 12,
    "title": "The Cult of AI",
    "published_at": "2026-05-08T12:34:00Z"
  },
  "links": {
    "self":         "https://api.disaffected.com/public/v1/episodes/the-cult-of-ai",
    "segments":     "https://api.disaffected.com/public/v1/episodes/the-cult-of-ai/segments",
    "thumbnails":   "https://api.disaffected.com/public/v1/episodes/the-cult-of-ai/thumbnails"
  }
}
```

Event types we'll emit:
- `episode.published`
- `episode.unpublished`
- `episode.updated` — content change on already-published episode
- `segment.published` / `segment.unpublished` (for per-segment changes)
- `transcript.ready` — transcript materialized after episode publish

### Webhook receiver requirements (website team handles)

1. Verify HMAC signature using shared secret. Reject if mismatch.
2. Reject requests where `|now - X-ShowBuild-Timestamp| > 5 minutes`.
3. Idempotency: store `X-ShowBuild-Delivery` UUIDs for 7 days; if seen,
   200 immediately without re-processing.
4. Respond 2xx within 5 seconds — long work happens after responding.
5. On 2xx, the website triggers its own rebuild path (Vercel/Netlify
   deploy hook, ISR revalidation, or invalidate own cache key).

### Why webhook + pull instead of push-with-payload

We send the event but NOT the full episode body. The website fetches
back through the public API. This:
- Avoids transmitting potentially large payloads through the webhook
- Forces the website to use the same contract any other consumer would
- Means API field allow-list is the single point of leak control
  (if we'd shipped full payloads in webhooks, that would be a second
  leak surface to audit)

## Response budget targets

- p95 < 200ms for episode/segment detail (Postgres-only, no media touch)
- p95 < 500ms for transcripts (text payload up to ~150KB)
- p95 < 800ms for sitemap (full enumeration, but heavily cached)

## Next concrete steps

1. **Wait for website-side requirements** (rendering model, build cadence,
   thumbnail variants, locale plans) — do NOT scaffold code blind.
2. **In parallel, draft the Alembic migration** for the schema additions
   above as a separate branch. Migration is the longest-lead item and is
   independent of API shape.
3. **Once requirements land:** scaffold the router package + schemas
   exactly as laid out, wire `public:read` permission, add 1 endpoint
   end-to-end (`GET /public/v1/episodes`) as a vertical slice, then fan
   out to the rest of Tier 1.
