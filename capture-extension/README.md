# Show-Build Capture (Chrome extension)

Send content from any web page into a Show-Build episode — right-click a
selection, link, image, or video (or use the toolbar popup) and it lands in
the episode's **media pool** and **whiteboard capture inbox**. Social posts
(X/Twitter, TikTok, YouTube, Instagram, Facebook, Rumble, SoundCloud) are
downloaded **server-side** with full media + metadata; videos can be typed
**SOT** or **VO** to run through the existing processing pipelines
(transcode, thumbnails, Whisper transcription for SOTs).

Captures are concurrency-safe by design: the extension never writes
whiteboard cards directly (the board save is full-replace). It POSTs to the
capture inbox (`/api/whiteboard/{ep}/captures`); the whiteboard UI drains
pending captures into cards and acks them after a successful save. Until that
UI integration lands, captured media is already visible in the episode's
Asset Pool panel. See `docs/CAPTURE_INBOX_HANDOFF.md`.

## Install (load unpacked)

1. Clone/pull this repo on the machine running Chrome.
2. `chrome://extensions` → enable **Developer mode** → **Load unpacked** →
   pick this `capture-extension/` folder.
3. Click the extension's ⚙ options:
   - **Server URL** — leave as `https://showbuild.app` (works from anywhere
     via the tunnel). A LAN URL (`https://192.168.51.238:8888`) also works but
     Chrome must first trust its self-signed cert: open the URL in a tab once
     and accept the warning. Non-default URLs trigger a one-time host
     permission prompt.
   - **API key** — mint one as an admin:
     `POST /api/auth/apikey?client_name=<your-name>` (or ask whoever runs the
     server). Stored in `chrome.storage.local` only — never synced.
   - **Test connection** should report the number of visible episodes.
4. Open the toolbar popup and pick the target episode.

## Use

Right-click anywhere → **Show-Build → Ep NNNN**:

| Menu item | What happens |
|---|---|
| Send to Whiteboard | Selection → text card (a highlighted URL becomes a link card); link → link card with OpenGraph preview; image → server fetches it into the pool; video/social URL → server-side download (yt-dlp / X API) with full metadata; page → link card. |
| Send video as SOT / VO | Same as a video capture, plus the file is fed through the SOT (transcode + transcribe) or VO pipeline. |
| Send video as NAT | Video transfers in tagged NAT; NAT has no processing pipeline (text-only cue type), so this is a tag for later use. |
| Capture visible tab | Screenshot → uploaded as an image capture. |
| Target episode | Switch episode (10 most recent) or refresh the list. |

Toolbar popup: episode picker, capture-page / screenshot buttons, the last 15
captures with status chips (processing → pending → placed), and the offline
retry queue (failed sends retry automatically with backoff for 24 h; sends
are idempotent via `client_capture_id`).

## Architecture

Plain MV3, ES modules, no build step. `background.js` registers the context
menus and delegates to `lib/` (settings, api, menus, capture-payloads, retry
queue, feedback). The backend counterpart is
`app/routers/whiteboard/captures_router.py` (capture inbox + enrichment +
SOT/VO dispatch) and the `whiteboard_captures` table (migration g026).

A future phone path (PWA share-target) reuses the same capture API — nothing
here is Chrome-specific server-side.
