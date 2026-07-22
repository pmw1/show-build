// Retry queue for captures that failed to send (offline, server down).
// Stored in chrome.storage.local; drained by a 1-minute alarm with exponential
// backoff. client_capture_id makes server-side replays idempotent.

import { createCapture } from './api.js';

const KEY = 'captureQueue';
const DRAIN_ALARM = 'sb-queue-drain';
const BACKOFF_MINUTES = [1, 2, 5, 15];
const MAX_AGE_MS = 24 * 60 * 60 * 1000;
// Malformed-request statuses that will never succeed on retry.
const DROP_STATUSES = new Set([400, 404, 409, 413, 422]);

export async function getQueue() {
  const o = await chrome.storage.local.get({ [KEY]: [] });
  return o[KEY];
}

async function setQueue(q) {
  await chrome.storage.local.set({ [KEY]: q });
}

export async function enqueue(episode, payload) {
  const q = await getQueue();
  q.push({ episode, payload, attempts: 0, queuedAt: Date.now(), nextAttemptAt: Date.now() });
  await setQueue(q);
  await chrome.alarms.create(DRAIN_ALARM, { periodInMinutes: 1 });
  return q.length;
}

export async function drainQueue() {
  const q = await getQueue();
  if (!q.length) {
    await chrome.alarms.clear(DRAIN_ALARM);
    return { sent: 0, remaining: 0, dropped: 0 };
  }

  const now = Date.now();
  const keep = [];
  let sent = 0;
  let dropped = 0;

  for (const item of q) {
    if (now - item.queuedAt > MAX_AGE_MS) { dropped++; continue; }
    if (item.nextAttemptAt > now) { keep.push(item); continue; }
    try {
      await createCapture(item.episode, item.payload);
      sent++;
    } catch (e) {
      if (e.status && DROP_STATUSES.has(e.status)) { dropped++; continue; }
      item.attempts++;
      const mins = BACKOFF_MINUTES[Math.min(item.attempts - 1, BACKOFF_MINUTES.length - 1)];
      item.nextAttemptAt = now + mins * 60000;
      keep.push(item);
    }
  }

  await setQueue(keep);
  if (!keep.length) await chrome.alarms.clear(DRAIN_ALARM);
  return { sent, remaining: keep.length, dropped };
}
