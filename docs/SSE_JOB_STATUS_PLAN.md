# Replace Polling With Server-Sent Events for Job Status

## Problem

The frontend currently learns about Celery job state changes (SOT processing,
LLM content generation, GFX rendering, etc.) by **polling**. Multiple
independent pollers run simultaneously:

| Source | Endpoint(s) | Interval |
|---|---|---|
| `useJobMonitor.startPolling` (admin badge in top bar) | `/api/celery-jobs/active`, `/api/celery-jobs/recent?limit=20`, `/api/llm-notifications/unseen` | 5s |
| `useSOTProcessing.startPolling` (per loaded episode) | `/api/sot/active-jobs/{ep}` | 3s |
| `PlaceholderCueCard.vue` (per pending cue card on screen) | `/api/sot/job-status/{assetId}` and GFX equivalent | per-card, ~3-5s |
| `useMessages.startPolling` | `/api/messages/inbox`, `/api/users` | 30s / 60s |
| `useSystemHealth.startPolling` | health endpoints | varies |

On a typical episode like 0273 with ~20 placeholder dots on screen, the
combined rate is **5–10 requests per second** even when nothing is happening.

### Why this hurts

1. **Single-worker bottleneck.** With `WEB_CONCURRENCY=1` (current default in
   `docker-compose.yml`) every poll occupies the only worker. Real requests
   (loading an episode, saving a script) queue behind the polls. Episode-load
   times measured at 5–13s while the box was 99% idle. Bumping to
   `WEB_CONCURRENCY=4` masked the symptom but didn't fix the cause: the
   workers are still spending most of their time answering "no, nothing
   changed" hundreds of times per minute.
2. **Wrong direction of travel.** Only the server knows when a Celery task
   transitions state. The client cannot. Asking repeatedly is wasted work.
3. **Latency floor.** Even when the server sees a state change instantly,
   the user waits up to 3–5 seconds for the next poll cycle to surface it.
4. **Scales poorly.** N users × M cards × every-3s is polynomial in tab
   count and screen content. It will get worse, not better, as the team
   grows or as more LLM/processing features are added.

### Why polling looked "rapid-fire" in the logs

It isn't faster than 3-5 seconds per source — it's that **multiple sources
stack up**. JobMonitor (3 endpoints every 5s) + SOTProcessing (1 endpoint
every 3s) + per-card status (one per visible placeholder, every 3-5s) +
health checks + the server's own outbound httpx calls (Ollama tags,
fishspeech health, etc.) made inside many of those handlers.

## Solution outline: Server-Sent Events (SSE)

Invert the relationship. Client opens **one** long-lived HTTP connection,
server pushes events down it as they happen. Connection stays open for hours.

### Why SSE specifically (not WebSocket)

| Property | SSE | WebSocket |
|---|---|---|
| Direction | server → client only | bidirectional |
| Protocol | plain HTTP (works with current nginx + JWT) | upgrade handshake, separate auth |
| Reconnect | browser does it automatically | hand-rolled |
| FastAPI support | `StreamingResponse(media_type="text/event-stream")` | `WebSocket` route + lifecycle code |
| Best for | "tell me when something changes" | "two-way chat" |

For job status, the client never *sends* anything — it just listens. SSE
wins on simplicity. WebSocket would only earn its place if/when we add
collaborative editing (live cursors, ephemeral typing presence in the same
paragraph). That can come later as a parallel transport.

### Backend shape

A new router exposes one endpoint:

```
GET /api/events/stream
```

Returns a `StreamingResponse` whose generator subscribes to Redis pub/sub
channels and yields SSE-formatted lines as messages arrive. Two channel
families:

- `broadcast:jobs` — all-users updates (Celery state changes)
- `user:{user_id}` — private notifications (e.g. "your LLM description finished")

The publishers are **already in place** — Celery tasks update
`processing_jobs` / `sot_processing_jobs` / `media_assets` rows when
state changes. The fix is to add a one-line `redis.publish("broadcast:jobs",
json.dumps({...}))` in the same handlers that update those tables.

Sketch (do not paste verbatim — needs auth/error handling):
```python
@router.get("/api/events/stream")
async def event_stream(user = Depends(get_current_user_or_key)):
    async def gen():
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"user:{user.id}", "broadcast:jobs")
        # Send a keepalive every 15s so nginx/proxies don't drop the connection.
        async for msg in pubsub.listen():
            if msg["type"] != "message":
                continue
            yield f"event: {msg['channel']}\ndata: {msg['data']}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")
```

### Frontend shape

A single composable `useEventStream.js` opens **one** `EventSource` for
the whole app, dispatches events to per-feature subscribers.

```js
const es = new EventSource('/api/events/stream', { withCredentials: true })
es.addEventListener('broadcast:jobs', (e) => {
  const job = JSON.parse(e.data)
  jobMonitorStore.update(job)         // updates badge instantly
  if (job.asset_id) cueCards.notify(job)  // updates the right placeholder
})
es.addEventListener(`user:${myId}`, (e) => { /* LLM-finished toasts */ })
```

Then **delete**:
- `useJobMonitor.startPolling` interval
- `useSOTProcessing.startPolling` interval
- `PlaceholderCueCard.vue` per-card `setInterval` polls

State still updates — it just updates *when something happens* instead of
every 3 seconds whether or not anything happened.

### Outcome

- **Idle traffic ≈ 0.** Server isn't doing work when nothing's happening.
- **Latency drops from up to 5s to <100ms** for state changes.
- **Scales linearly with users**, not polynomially with users × cards × pollers.
- **Single worker stops being a choke point** — even on `WEB_CONCURRENCY=1`
  the box is mostly idle.
- **Frees us to remove the WEB_CONCURRENCY=4 workaround** if we want, or
  keep it as headroom.

### Costs / things to handle

- **Connection budget.** Each SSE stream holds an async task in uvicorn
  (cheap, but not free). FastAPI handles thousands; we still need to set
  nginx `proxy_buffering off; proxy_read_timeout 24h;` for the `/api/events`
  location.
- **Redis pub/sub.** Already running for Celery + caching. Just need to
  start writing to broadcast/user channels in the places that already
  write to processing tables.
- **Reconnect semantics.** Browser auto-reconnects. We accept "may miss
  events while offline" for v1 — a one-shot poll on connect catches up.
  v2 can add `Last-Event-ID` resume if needed.
- **Auth.** Stock `EventSource` doesn't send `Authorization` headers.
  Two options: (a) cookie-based auth on this one endpoint, (b) the
  `event-source-polyfill` npm package. Show-build already has cookie
  session for JWT — option (a) is easiest.
- **nginx config.** Two-line change for the events location.

## Shorter step-by-step plan

### Phase 1 — minimal SSE for SOT job status (the noisiest poller)

This is the smallest version that delivers real value AND lays the
infrastructure for everything else.

1. **Backend**: create `app/routers/events_router.py`. Single endpoint
   `GET /api/events/stream`. Generator subscribes to Redis channel
   `broadcast:sot_jobs`. Yields events as they arrive. Send a keepalive
   comment line (`: ping\n\n`) every 15s.
2. **Backend**: in the SOT pipeline (`app/services/` SOT-related modules
   and Celery tasks that update `sot_processing_jobs`), add `redis.publish
   ("broadcast:sot_jobs", json.dumps({...}))` after each state update.
3. **nginx**: add `proxy_buffering off; proxy_read_timeout 24h;` to the
   `/api/events` location.
4. **Frontend**: create `disaffected-ui/src/composables/useEventStream.js`.
   Opens one `EventSource`, exposes `on(eventName, handler)`. Auto-reconnect
   on disconnect (`EventSource` does this natively).
5. **Frontend**: in `PlaceholderCueCard.vue` and `useSOTProcessing.js`,
   replace `setInterval(...)` with `useEventStream().on('broadcast:sot_jobs',
   handler)`. Keep one initial fetch on mount to catch state-at-load.
6. **Test**: open ep 0273, kick a SOT processing job, watch the placeholder
   dot update in <100ms. Check that closing/reopening the tab resumes
   correctly.
7. **Remove** the now-unused `setInterval` polling in `useSOTProcessing.js`
   and `PlaceholderCueCard.vue`.

**Estimated effort: 1 day.**

### Phase 2 — extend to Celery monitor + LLM notifications

8. Add `broadcast:jobs` channel for general Celery state (any queue).
   Publish from the central Celery task callbacks rather than per-task.
9. Add `user:{id}` channel for private notifications. Publish from
   `auto_description_service.py` and other LLM completion paths.
10. Frontend: subscribe in `useJobMonitor.js` and the LLM toast handler.
    Delete the polling intervals.

**Estimated effort: half a day.**

### Phase 3 — cleanup and tune

11. Drop `WEB_CONCURRENCY` back to 2 (or leave at 4 for headroom — measure first).
12. Add `Last-Event-ID` resume support if we observe missed events.
13. Document the channel taxonomy in `docs/SSE_CHANNELS.md` so future
    publishers know where to publish.

**Estimated effort: half a day.**

**Total: ~2 days.** Phase 1 alone delivers the biggest UX improvement
(per-card polling is the loudest source on a heavy episode).

## References

- Affected files (current pollers to remove):
  - `disaffected-ui/src/composables/useJobMonitor.js`
  - `disaffected-ui/src/composables/useSOTProcessing.js`
  - `disaffected-ui/src/components/content-editor/cards/PlaceholderCueCard.vue`
  - (and `useMessages.js`/`useSystemHealth.js` later, if desired)
- Existing infra to reuse:
  - Redis (already running for Celery + cache)
  - JWT cookie auth (already supported by FastAPI auth dependency)
  - `app/celery_app.py` — task callback hooks
  - `sot_processing_jobs` / `processing_jobs` tables (state already tracked)
- Related ICR discussion: relay message #274 (cue-wipe root-cause fix —
  separate issue, but documents the kind of silent-state-loss this
  architecture should also help surface faster).

---

*Authored: 2026-05-09 by `prefect-show-build-claude-c6e0ef`. Triggered by
the episode 0273 loading-spinner outage of the same day, where
`WEB_CONCURRENCY=1` plus stacked pollers blocked all users for several
minutes. The bump to `WEB_CONCURRENCY=4` was an immediate workaround;
this document is the durable fix.*
