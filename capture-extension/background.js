// Service-worker entry. All listeners are registered at top level (MV3 rule);
// the handlers delegate to lib/ modules.

import { rebuildMenus, setEpisode, MENU } from './lib/menus.js';
import { buildCapturePayload } from './lib/capture.js';
import { createCapture, uploadMedia, listEpisodes } from './lib/api.js';
import { getSettings, setSettings } from './lib/settings.js';
import { enqueue, drainQueue, getQueue } from './lib/queue.js';
import { flashBadge, showQueueBadge, notify } from './lib/feedback.js';

chrome.runtime.onInstalled.addListener(() => {
  rebuildMenus();
  refreshEpisodes().catch(() => { /* no key yet — options page will prompt */ });
  chrome.alarms.create('sb-episodes-refresh', { periodInMinutes: 30 });
});

chrome.runtime.onStartup.addListener(() => {
  rebuildMenus();
});

// Popup/options change episode or the cached list → keep menus in sync.
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'sync' && (changes.episode || changes.episodeList)) rebuildMenus();
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'sb-queue-drain') {
    drainQueue().then(({ remaining }) => showQueueBadge(remaining));
  } else if (alarm.name === 'sb-episodes-refresh') {
    refreshEpisodes().catch(() => {});
  }
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  handleClick(info, tab).catch((e) => {
    console.error('capture failed', e);
    notify('Show-Build Capture', `Capture failed: ${e.message || e}`);
  });
});

async function handleClick(info, tab) {
  const id = String(info.menuItemId);

  if (id.startsWith(MENU.EP_PREFIX)) return setEpisode(id.slice(MENU.EP_PREFIX.length));
  if (id === MENU.EP_REFRESH) return refreshEpisodes();

  const { episode } = await getSettings();
  if (!episode) {
    notify('Show-Build Capture', 'No target episode set — pick one from the toolbar popup first.');
    return;
  }

  if (id === MENU.SHOT) return captureScreenshot(episode, tab);

  const cueType = id === MENU.SOT ? 'sot' : id === MENU.VO ? 'vo' : id === MENU.NAT ? 'nat' : null;
  if (id !== MENU.SEND && !cueType) return;

  const payload = buildCapturePayload(info, tab, cueType);
  if (payload.capture_kind === 'image' && payload.url && payload.url.startsWith('data:')) {
    return sendDataUrlImage(episode, payload);
  }
  return sendCapture(episode, payload);
}

async function sendCapture(episode, payload) {
  try {
    await createCapture(episode, payload);
    flashBadge('✓');
  } catch (e) {
    if (e.status === 401 || e.status === 403) {
      notify('Show-Build Capture', 'Authentication failed — check the API key in the extension options.');
      return;
    }
    // Network/server trouble: park it, the alarm retries with backoff.
    const count = await enqueue(episode, payload);
    showQueueBadge(count);
  }
}

// A data: <img> can't be fetched server-side — upload the bytes first, then
// send a capture that references the uploaded asset.
async function sendDataUrlImage(episode, payload) {
  const blob = await (await fetch(payload.url)).blob();
  const ext = (blob.type.split('/')[1] || 'png').replace('jpeg', 'jpg');
  const up = await uploadMedia(episode, blob, `capture.${ext}`, { sourceUrl: payload.page_url });
  await createCapture(episode, {
    ...payload,
    url: null,
    media_asset_id: up.asset_id,
    media_path: up.media_path,
    mime_type: up.mime_type,
    file_size: up.file_size,
  });
  flashBadge('✓');
}

async function captureScreenshot(episode, tab) {
  const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' });
  const blob = await (await fetch(dataUrl)).blob();
  const up = await uploadMedia(episode, blob, 'screenshot.png', { tags: 'screenshot', sourceUrl: tab.url });
  await createCapture(episode, {
    capture_kind: 'screenshot',
    title: tab.title || 'Screenshot',
    page_url: tab.url,
    page_title: tab.title,
    media_asset_id: up.asset_id,
    media_path: up.media_path,
    mime_type: up.mime_type,
    file_size: up.file_size,
    client_capture_id: crypto.randomUUID(),
    source: { agent: 'chrome-extension', version: chrome.runtime.getManifest().version },
  });
  flashBadge('✓');
}

async function refreshEpisodes() {
  const eps = await listEpisodes();
  const { episode } = await getSettings();
  await setSettings({
    episodeList: eps.slice(0, 10),
    episode: episode || eps[0]?.number || null,
  });
  await rebuildMenus();
}

// On SW cold start with items still queued, make the badge reflect reality.
getQueue().then((q) => showQueueBadge(q.length)).catch(() => {});
