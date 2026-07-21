# Dashboard Architecture: Zones & Readiness

**Route**: `/dashboard` → `disaffected-ui/src/views/DashboardView.vue`

## The #1 Thing to Understand

**The dashboard answers one question: _can we air tonight, and if not, what's
blocking?_**

It is not a launcher. Navigation is the sidebar's job, and duplicating it here
is how this page previously filled ~60% of its surface with buttons while 151
failed SOT jobs had no representation at all.

Before adding anything, ask: *does this help someone decide whether tonight's
show is ready?* If it only helps them get somewhere, it belongs in the nav.

## Layout: three fixed zones

Zones are **fixed and ordered by urgency**. Only their contents rearrange.

```
┌──────────────────────────────────────────────────────────────┐
│  OnAirRail          ← always first, never draggable          │
│  0283 · title · SCRIPTS 9/9 · SOT 48/54 · TIMED 10/11 · clock│
├──────────────────────────────────────────────────────────────┤
│  TONIGHT     the on-air episode          (poll 30s)          │
│    [pinned]  CurrentShow · Blockers · NextShow               │
├──────────────────────────────────────────────────────────────┤
│  PIPELINE    work in flight              (poll 15s active)   │
│    [drag]    JobFeed · Todo · Announcements                  │
├──────────────────────────────────────────────────────────────┤
│  SYSTEM      infrastructure              (poll 60s)          │
│    [drag]    QueueCoverage · Services · Shortcuts            │
└──────────────────────────────────────────────────────────────┘
```

**Why zones instead of free columns.** The old layout let any block land in any
column. That means the panel you need in a hurry has moved somewhere else.
Scoping drag *within* a zone keeps muscle memory intact while still letting
people arrange their own space.

Each `<draggable>` uses a **per-zone group** (`:group="'zone-' + zone.id"`).
This is what prevents cross-zone drags — do not change it to a shared group
name without re-reading this section.

## Adding a panel

This is the extension point. A new panel names its zone and inherits that
zone's placement rules and poll cadence — there is no per-panel layout code.

1. Add the block id to `DEFAULT_LAYOUT[zoneId]` in `DashboardView.vue`.
2. Render it in the `<draggable>` `#item` template, matched on `element`.
3. Put `dash-drag-handle` on the panel's `v-card-title` (or
   `dash-drag-handle-wrap` on the component) so it can be grabbed.

`KNOWN_BLOCKS` is derived from `DEFAULT_LAYOUT`, so step 1 is what makes the
block real. A block missing from a user's saved layout is appended to its
default zone on load — meaning **a panel added in a later release still
appears for existing users** rather than being invisible to everyone who has
ever dragged something.

### Layout persistence

- Stored per-user at pref key **`dashboard.zones`** via `useUserPrefs`.
- The shape is a zone map (`{tonight: [], pipeline: [...], system: [...]}`),
  not the pre-zone array-of-columns. The key was renamed precisely so an old
  stored value can't be misread as the new shape.
- `_validateAndApply()` drops unknown and `RETIRED_BLOCKS` ids, and guards
  against the same block appearing in two zones.
- Pre-zone layouts carried no zone information, so nothing is migrated
  forward — the legacy `dashboard-layout-v3` localStorage key is simply
  cleared on load.

## Readiness: the data behind the rail

`GET /api/episodes/{ep}/readiness`
(`app/routers/episodes/metadata_router.py`) is the single request behind both
`OnAirRail` and `BlockersPanel`. Full payload documented in
[`API_ENDPOINTS.md`](API_ENDPOINTS.md#episode-progress).

It aggregates existing state — it introduces **no new tables and no new
writes**:

| Stage | Source | Counts as done when |
|---|---|---|
| `rundown` | `rundown_items` | item exists |
| `scripts` | `rundown_items.script_content` | ≥20 chars of markdown |
| `sots` | `sot_processing_jobs.status` | `completed` |
| `graphics` | `celery_job_log` (`fsq`/`gfx`) | `completed` |
| `timing` | `rundown_items.duration` | parses to a duration |

Two rules worth preserving:

- **`ad`, `break` and `transition` items are excluded from `scripts`.** They
  legitimately have no script; counting them makes a ready show look unready.
- **A stage with `total: 0` renders as absent, not as complete.** A hollow
  green chip for work that doesn't exist is worse than no chip.

## Semantics that carry meaning

These aren't styling choices — changing them changes what an operator reads.

- **Tally colors follow broadcast tally-light convention**: green ready, amber
  attention, red fault. Any `fault` turns the whole rail red, so a glance at
  the top of the page is sufficient. If the rail is all green, you can close
  the tab.
- **The rail's episode number is deliberately NOT tinted** by status. Coloring
  `0283` red reads as "this episode is broken" rather than "a stage needs
  attention." Border, tallies and clock carry the state.
- **Blockers deep-link to the fix**, not to a generic page: script/timing
  problems go to the content editor, job failures to the tools job view. A
  blocker you can't act on is just an alarm.

## Gotchas

**Props resolve asynchronously.** `railEpisodeNumber` is null on mount while
episodes load. Both `OnAirRail` and `BlockersPanel` therefore `watch` their
`episode` prop — without it the panel fetches with `null`, renders empty, and
waits for the next poll tick. This bug shipped once and was invisible to
lint, build, and unit-level checks; it only showed up when the page was
actually rendered.

**Queue coverage arrives in Phase 2.** The Queue Coverage panel reads
`health.services.celery.queues`, which comes from `/health/secondary`. It is
briefly empty on load. See
[`HEALTH_CHECK_PROGRESSIVE_LOADING.md`](HEALTH_CHECK_PROGRESSIVE_LOADING.md#celery-queue-coverage).

**`.zone-grid:empty` is load-bearing.** Tonight has no draggable blocks today,
and without the `:empty` collapse its `min-height` leaves a gap that reads as
a rendering bug.

**Verify in a browser.** A clean `eslint` and a successful `vue-cli-service
build` do not prove this page works — both passed while the rail was entirely
missing from the DOM.

## Room to grow

The zone model is the seam for planned work:

- **SSE (todo #24)** — zones centralize refresh cadence, so replacing polling
  is one change at the zone level rather than a per-panel rewrite.
- **Per-role dashboards** — RBAC already exists; zone visibility becomes a role
  attribute (a producer sees Tonight; an engineer leads with System).
- **Multi-show** — the rail is per-episode, so two shows in production means
  two rails and nothing else changes.
- **Publish stage** — `publish_status`, `omny_publish_status` and
  `yt_privacy_status` already exist on the Episode model and want a Pipeline
  panel once post-production is in scope.
- **Alerting** — anything that turns a tally red is, by definition, worth a
  push notification.

## Key files

| File | Role |
|---|---|
| `views/DashboardView.vue` | Zone definitions, layout persistence, panel dispatch |
| `components/OnAirRail.vue` | Fixed rail: identity, tallies, countdown |
| `components/BlockersPanel.vue` | Actionable blockers with deep links |
| `components/JobFeedPanel.vue` | Celery jobs; failures pinned to top |
| `routers/episodes/metadata_router.py` | `/readiness` aggregation |
| `routers/health_router.py` | Per-queue consumer coverage |
