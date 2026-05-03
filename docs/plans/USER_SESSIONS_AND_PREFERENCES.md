# Plan: User Sessions, Preferences, and Inter-User Messaging

## Context

The app has working JWT auth (`models_user.User`, `models_user.UserSession`, `auth/utils.get_current_user_or_key`) and a `Settings` table that already includes a `user_id` column. But almost nothing is actually scoped to the user:

- The `Settings` table is always written with `user_id=None` (global). See `settings_colors_router.py:57, 160, 238, 320`.
- ~25 user-relevant prefs live only in `localStorage` (theme colors, dashboard layout, sidebar widths, dismissed notifications, settings sub-tab state, FSQ defaults, real-content-settings, TTS config, etc.). Lost on cache clear, doesn't follow the user to another browser/device.
- No way for users to know who else is online or send a quick message.

The goal: turn the app into a real multi-user environment where (a) preferences travel with the user, (b) users can see each other and message quickly, (c) admins can see who's active.

## Scope (3 phases — phase 1 unblocks the others)

### Phase 1 — Make `Settings` actually per-user (foundation)

The plumbing already exists. We just have to use it.

**Backend (`app/settings_colors_router.py` + new `app/routers/user_prefs_router.py`):**
- New endpoints `GET/PUT /api/user/prefs/{key}` and `GET /api/user/prefs` that read/write `Settings` rows scoped by the current JWT's `user_id`.
- Standard shape: `{ key: string, value: <json>, updated_at }`. The `value` is opaque JSON so any frontend pref can use it.
- Make `settings_colors_router` honor an optional `?scope=user` query param: when set, lookup/save row uses `user_id=current_user.id` instead of `None`. Default stays global so existing UIs don't break.

**Frontend (`disaffected-ui/src/composables/useUserPrefs.js` — NEW):**
- Single composable: `const { get, set, hydrate } = useUserPrefs()`.
- Reads from a reactive cache; falls back to a sensible default; writes through to the API and updates the cache.
- On login, `hydrate()` fetches all prefs in one round-trip and warms the cache.
- On logout, the cache is wiped.

**Migration of existing localStorage keys:**
Drop-in replacement on a per-key basis. Recommended first batch (highest-value, lowest-risk):
| localStorage key | New pref key | Owner UI |
|---|---|---|
| `dashboard-layout-v3` | `dashboard.layout` | `DashboardView.vue` |
| `themeColors` | `colors.profile` (already DB-backed; just flip `?scope=user` toggle) | `ColorSelector.vue` |
| `showbuild_interface_settings` | `interface.settings` | `InterfaceSettings.vue` |
| `settingsActiveTab`, `settingsAiSubTab`, `settingsContentSubTab` | `settings.tabs` | `SettingsView.vue` |
| `llm-dismissed-notifications` | `notifications.dismissed` | `NotificationCenter.vue` |
| `llm-routing-settings` | `llm.routing` | LLM components |
| `real-content-settings` | `content.editor` | `ContentEditor.vue` |
| `fsqSettings` | `fsq.defaults` | FSQ modal |
| `tts-config` | `tts.config` | TTS components |
| `customClockTz` | `clock.timezone` | LiveClock |

Do NOT migrate auth tokens (`auth-token`, etc.) — those stay in localStorage by design.

**Verification:** log in as user A in browser 1, change dashboard layout / theme color / sidebar widths. Open browser 2, log in as same user — the changes persist. Log in as user B — sees their own.

---

### Phase 2 — User profile + presence + activity

Now that `user_id` flows through everything, surface it.

**Backend:**
- Extend `User` model with: `display_name` (already exists), `avatar_url`, `color` (the chip color shown in messages/presence), `last_seen_at`.
- Touch `last_seen_at` on every authed request via a small dependency wrapper around `get_current_user_or_key` (cheap UPDATE, debounced to once per minute per user via Redis).
- New endpoint `GET /api/users` — returns `[{id, username, display_name, avatar_url, color, online}]` where `online = last_seen_at > now - 90s`.
- New endpoint `GET /api/users/me` — returns the current user's profile. Already partially exists in `auth/router.py`; extend.

**Frontend:**
- New "Account" panel in `ProfileView.vue` for editing display name, color, and avatar.
- Tiny presence indicator in the global app bar (user avatar + dot) that lists who else is online. Polls `/api/users` every 30s.

**Verification:** all logged-in users appear in the presence menu with green dots; logging out drops them off within ~2 minutes.

---

### Phase 3 — Inter-user quick messages

Pick a delivery model up front: **polling first, WebSocket later** (matches the existing pattern — relay, todos, announcements all poll). Polling is one new table + two endpoints + 30s timer; WebSocket is more infra than this feature deserves on day 1.

**Backend (new `app/routers/messages_router.py` + new model):**
```python
class UserMessage(Base):
    id: int (pk)
    from_user_id: int (fk users.id)
    to_user_id: int (fk users.id, nullable for broadcast)
    content: str
    sent_at: datetime
    read_at: datetime | None
    reply_to: int | None (fk user_messages.id)
```
Endpoints:
- `POST /api/messages` — send (`{to_user_id, content, reply_to?}`)
- `GET /api/messages/inbox` — messages where `to_user_id = me`, sorted newest first, with `unread` count
- `GET /api/messages/thread/{user_id}` — full thread between me and `user_id`
- `PATCH /api/messages/{id}/read` — mark read

**Frontend:**
- New `MessagesPanel.vue` opened from a chat-bubble icon in the app bar. Shows unread badge. Click → modal with thread list on the left, active conversation on the right.
- "Quick message" entry point: click any user in the presence menu → opens compose for that user.
- Poll `/api/messages/inbox` every 30s while authed; show desktop-style `v-snackbar` for new ones.

**Future (out of scope for this plan):**
- Group threads, attachments, typing indicators, read receipts beyond the simple flag, push notifications. Those land cleanly on the same model later.

**Verification:** user A sends a message to user B; user B sees a badge within 30s, can open the panel, reply, and the thread shows both messages with timestamps.

---

## Critical files

**New:**
- `app/routers/user_prefs_router.py`
- `app/routers/messages_router.py`
- `app/models/messages.py` (or append to existing model module)
- `disaffected-ui/src/composables/useUserPrefs.js`
- `disaffected-ui/src/components/MessagesPanel.vue`
- `disaffected-ui/src/components/PresenceMenu.vue`
- one alembic migration for `user_messages` table + the new `User` columns

**Modified:**
- `app/models_user.py` — add `display_name?, avatar_url, color, last_seen_at`
- `app/settings_colors_router.py` — accept `?scope=user`
- `app/auth/utils.py` — touch `last_seen_at` on each authed request (debounced)
- `app/main.py` — register new routers
- `disaffected-ui/src/stores/auth.js` — call `useUserPrefs.hydrate()` on login, wipe on logout
- `DashboardView.vue`, `ColorSelector.vue`, `InterfaceSettings.vue`, `SettingsView.vue`, `NotificationCenter.vue`, `ContentEditor.vue`, FSQ/TTS/LiveClock components — swap localStorage for `useUserPrefs`
- `App.vue` — add presence menu + messages icon to app bar

## Reused infrastructure

- `Settings` table + `user_id` column: already there.
- `UserSession` table: already there (login tracking).
- `get_current_user_or_key`: already covers JWT + API-key auth uniformly.
- Polling pattern: matches existing todos / announcements / relay code.

## Decisions to confirm before starting

1. **Pref scope precedence**: when both a global and per-user value exist for the same key, which wins? Recommend per-user, fall back to global (matches the way colors are intended to work).
2. **Message visibility**: are broadcast messages (to_user_id=null) admin-only, or can any user send to "everyone"? Recommend admin-only, otherwise it becomes spam.
3. **Avatar storage**: filesystem (alongside thumbnails) or Gravatar URL? Recommend Gravatar for v1 (zero ops cost) with optional uploaded avatar later.

## What I'm NOT planning here

- WebSocket / real-time (polling is fine for v1)
- Federated identity (SSO, SAML, OAuth) — current local JWT is enough
- Per-user RBAC overrides — `models_rbac.UserPermissionOverride` already exists; out of scope
- Inter-Claude relay changes — that's a separate channel
