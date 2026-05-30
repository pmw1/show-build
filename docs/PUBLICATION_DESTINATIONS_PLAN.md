# Publication Destinations Plan (Distribution Matrix)

**Status:** STUB — captured 2026-05-08, not yet designed
**Owner:** TBD
**Scope:** larger than the public-API plan; touches media-distribute project

## What this is

Show-build becomes the **source of truth for what is published where, in
what state, under what gate.** Downstream tools — the public API, the
media-distribute fanout project, RSS feeds, podcast distribution, etc.
— consume the matrix rather than each having their own publishing
state model.

## Concept (rough, captured from conversation 2026-05-08)

Each *publishable thing* (episode, VOD video, segment-as-VOD, clip)
has zero or more **publication destination** rows. Each destination
row is independently settable — same VOD might be public on YouTube,
paywalled on disaffected.com, and not pushed to TikTok at all.

### VOD videos as a first-class entity

VOD videos are not just exports of the rundown — they're independently
publishable entities with their own slugs, posters, descriptions, and
destination matrix.

VOD types (initial):
- `episode` — the full broadcast as a single video
- `segment` — one rundown segment as a standalone piece
- `clip` — a short cut (1–3 min) from inside a segment
- (extensible)

### Destinations (initial)

- `disaffected.com` — where on the site (homepage, episode page,
  segment page, archive, members feed, …)
- `youtube`
- `twitter` / `x`
- `instagram` (reels, feed)
- `tiktok`
- `facebook`
- `omny` (podcast)
- `rumble`
- (extensible — should align with media-distribute project's existing
  distributor list)

### Per-destination state

| Field | Values | Notes |
|---|---|---|
| `state` | draft / scheduled / live / unpublished | per destination |
| `access_tier` | public / free_member / supporter / patron / … | only meaningful for destinations with tier models (disaffected.com); ignored for platforms with their own visibility model (YouTube uses unlisted/members-only/etc.) |
| `scheduled_at` | timestamp | when to publish (if state=scheduled) |
| `published_at` | timestamp | when it went live |
| `unpublished_at` | timestamp | when it came down |
| `external_id` | string | YouTube video ID, Tweet ID, etc. |
| `external_url` | string | resolved URL on the destination |
| `destination_location` | string | platform-specific subroute (which playlist on YT, which page on disaffected.com) |

## Schema sketch (NOT FINAL)

```
vod_videos
  id, asset_id, slug
  episode_id (nullable — clips can stand alone)
  vod_type: 'episode' | 'segment' | 'clip' | …
  source_segment_id (nullable)
  duration, source_video_path
  title, description, poster_*

publication_destinations
  id
  subject_type: 'episode' | 'vod_video'
  subject_id
  destination: 'disaffected.com' | 'youtube' | 'twitter' | …
  destination_location (nullable)
  state: 'draft' | 'scheduled' | 'live' | 'unpublished'
  access_tier: 'public' | 'free_member' | …
  scheduled_at, published_at, unpublished_at (nullable)
  external_id, external_url (nullable)
  updated_at, updated_by
  UNIQUE (subject_type, subject_id, destination, destination_location)

access_tiers
  slug (PK)
  name, rank, public (bool)
```

## Relationship to the public-API plan

The public API surface (`docs/WEBSITE_PUBLIC_API_PLAN.md`) only consumes
the `disaffected.com` rows of the matrix. For v1, the public API has its
own narrow `access_tier` column on episodes/segments (decision #11 —
resolved 2026-05-08); when this distribution-matrix lands, that column
becomes a derived value computed from
`publication_destinations.access_tier WHERE destination='disaffected.com'`.

The API contract doesn't change — only the internal source of truth
moves from a single column to a row in the matrix.

## Relationship to media-distribute

Media-distribute (`/home/kevin/media-distribute`, see relay KB #73)
already has distributor modules for YouTube, Instagram, Facebook,
TikTok, Twitter/X, Omny, and Rumble. Today it consumes prepared media
files; with this plan, it consumes the matrix instead — pulling
`publication_destinations` rows where `state='scheduled'` and
`scheduled_at <= NOW()` and `external_id IS NULL`, performing the push,
writing back the `external_id` + `external_url` + `published_at`.

Sync direction:
- show-build is canonical for **intent** (what should be where, when, in what state)
- media-distribute is canonical for **execution outcome** (it ran, here's the platform's response)
- show-build's `publication_destinations` row gets updated by media-distribute on completion

## Open questions (not yet decided)

1. **Where does the producer set destination state?** Per-episode UI in
   the editor? A dedicated "Publication" view? Bulk-set via a
   distribution dashboard?
2. **Migration from the current `episodes.publish_status`** — is that
   column still meaningful, or does it become a derived view?
3. **Scheduling semantics** — does "scheduled for 2026-05-09 19:00 UTC
   on YouTube" mean "media-distribute will push at that time" or
   "media-distribute uses YouTube's native scheduled-publish feature"?
   (Probably both, configurable per-destination.)
4. **Webhook + status reconciliation** — if YouTube unpublishes our
   video for a copyright claim, do we know? media-distribute would
   need to poll or receive webhooks.
5. **Per-tier feeds** — does each tier get its own RSS / podcast feed,
   or is gating purely on-page?

## Why this is a separate doc

- The public-API plan can ship without this (it has its own narrow
  `access_tier` model that's forward-compatible)
- Touches a separate project (media-distribute) and a separate
  codebase, so the plan owner is plausibly different
- The design space is genuinely larger — a distribution matrix is
  weeks of work; the public API is a couple of weeks
- Keeping them separate keeps each doc focused enough to read in
  one sitting

## Next step

Pick this up after public-API v1 ships, OR if a concrete need arises
(e.g. "we need to schedule a YouTube push for next Tuesday and have
that show up in the dashboard").
