import { getSettings, setSettings } from '../lib/settings.js';
import { listEpisodes, listCaptures, createCapture, uploadMedia } from '../lib/api.js';
import { getQueue, drainQueue } from '../lib/queue.js';

const episodeSel = document.getElementById('episodeSel');
const msgEl = document.getElementById('msg');
const capturesEl = document.getElementById('captures');
const queueRow = document.getElementById('queueRow');
const queueCount = document.getElementById('queueCount');

const STALLED_MS = 10 * 60 * 1000;

function setMsg(text) { msgEl.textContent = text; }

function sourcePayload(extra = {}) {
  return {
    client_capture_id: crypto.randomUUID(),
    source: { agent: 'chrome-extension', version: chrome.runtime.getManifest().version },
    ...extra,
  };
}

async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function renderEpisodes() {
  const { episode, episodeList } = await getSettings();
  episodeSel.innerHTML = '';
  if (!episodeList.length) {
    const opt = document.createElement('option');
    opt.textContent = 'No episodes — set API key in options';
    episodeSel.appendChild(opt);
    return;
  }
  for (const ep of episodeList) {
    const opt = document.createElement('option');
    opt.value = ep.number;
    opt.textContent = `${ep.number}${ep.title ? ' — ' + ep.title.slice(0, 32) : ''}`;
    if (ep.number === episode) opt.selected = true;
    episodeSel.appendChild(opt);
  }
  // A previously-chosen episode that fell out of the draft/production list
  // stays selectable rather than silently misreporting the target.
  if (/^\d{4}$/.test(episode || '') && !episodeList.some((e) => e.number === episode)) {
    const opt = document.createElement('option');
    opt.value = episode;
    opt.textContent = `${episode} — (current)`;
    opt.selected = true;
    episodeSel.appendChild(opt);
  }
}

async function renderCaptures() {
  const { episode } = await getSettings();
  capturesEl.innerHTML = '';
  if (!episode) return;
  let data;
  try {
    data = await listCaptures(episode, 'all', 15);
  } catch (e) {
    setMsg(`Could not load captures: ${e.message}`);
    return;
  }
  const now = Date.now();
  for (const c of data.captures.slice().reverse()) {
    const div = document.createElement('div');
    div.className = 'cap';
    const stalled = c.status === 'processing' && now - Date.parse(c.created_at) > STALLED_MS;
    const chip = stalled ? 'failed' : c.status;
    const label = stalled ? 'stalled' : c.status;
    const title = c.title || c.preview_title || c.text_content || c.url || c.capture_kind;
    div.innerHTML = `<span class="title"></span><span class="chip ${chip}">${label}</span>`;
    div.querySelector('.title').textContent = `[${c.item_type}] ${title}`;
    capturesEl.appendChild(div);
  }
  if (!data.captures.length) {
    capturesEl.innerHTML = '<div class="cap"><span class="title">No captures yet for this episode.</span></div>';
  }
}

async function renderQueue() {
  const q = await getQueue();
  queueRow.style.display = q.length ? 'block' : 'none';
  queueCount.textContent = `${q.length} capture${q.length === 1 ? '' : 's'}`;
}

episodeSel.addEventListener('change', async () => {
  await setSettings({ episode: episodeSel.value });
  renderCaptures();
});

document.getElementById('refreshBtn').addEventListener('click', async () => {
  setMsg('Refreshing episodes…');
  try {
    const eps = await listEpisodes();
    const { episode } = await getSettings();
    await setSettings({ episodeList: eps.slice(0, 10), episode: episode || eps[0]?.number || null });
    await renderEpisodes();
    setMsg('');
  } catch (e) {
    setMsg(`Refresh failed: ${e.message}`);
  }
});

document.getElementById('capturePageBtn').addEventListener('click', async () => {
  const { episode } = await getSettings();
  if (!episode) return setMsg('Pick an episode first.');
  const tab = await activeTab();
  setMsg('Sending…');
  try {
    await createCapture(episode, sourcePayload({
      capture_kind: 'page', url: tab.url, title: tab.title, page_url: tab.url, page_title: tab.title,
    }));
    setMsg('Page sent.');
    renderCaptures();
  } catch (e) {
    setMsg(`Failed: ${e.message}`);
  }
});

document.getElementById('screenshotBtn').addEventListener('click', async () => {
  const { episode } = await getSettings();
  if (!episode) return setMsg('Pick an episode first.');
  const tab = await activeTab();
  setMsg('Capturing…');
  try {
    const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' });
    const blob = await (await fetch(dataUrl)).blob();
    const up = await uploadMedia(episode, blob, 'screenshot.png', { tags: 'screenshot', sourceUrl: tab.url });
    await createCapture(episode, sourcePayload({
      capture_kind: 'screenshot', title: tab.title || 'Screenshot',
      page_url: tab.url, page_title: tab.title,
      media_asset_id: up.asset_id, media_path: up.media_path,
      mime_type: up.mime_type, file_size: up.file_size,
    }));
    setMsg('Screenshot sent.');
    renderCaptures();
  } catch (e) {
    setMsg(`Failed: ${e.message}`);
  }
});

document.getElementById('optionsBtn').addEventListener('click', () => chrome.runtime.openOptionsPage());

document.getElementById('retryLink').addEventListener('click', async (ev) => {
  ev.preventDefault();
  setMsg('Retrying queued captures…');
  const { sent, remaining } = await drainQueue();
  setMsg(`Sent ${sent}, ${remaining} still queued.`);
  renderQueue();
  renderCaptures();
});

renderEpisodes();
renderCaptures();
renderQueue();
