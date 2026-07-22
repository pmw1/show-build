import { getSettings, setSettings } from '../lib/settings.js';
import { listEpisodes } from '../lib/api.js';

const baseUrlEl = document.getElementById('baseUrl');
const apiKeyEl = document.getElementById('apiKey');
const statusEl = document.getElementById('status');

function showStatus(cls, msg) {
  statusEl.className = cls;
  statusEl.textContent = msg;
}

async function load() {
  const { baseUrl, apiKey } = await getSettings();
  baseUrlEl.value = baseUrl;
  apiKeyEl.value = apiKey;
}

async function save() {
  let baseUrl = baseUrlEl.value.trim().replace(/\/+$/, '') || 'https://showbuild.app';
  try {
    const origin = new URL(baseUrl).origin;
    // Non-default hosts need a host permission grant (user-gesture context).
    if (origin !== 'https://showbuild.app') {
      const granted = await chrome.permissions.request({ origins: [`${origin}/*`] });
      if (!granted) {
        showStatus('err', `Permission for ${origin} was declined — requests to it will be blocked.`);
      }
    }
  } catch {
    showStatus('err', 'Server URL is not a valid URL.');
    return;
  }
  await setSettings({ baseUrl, apiKey: apiKeyEl.value.trim() });
  showStatus('ok', 'Saved.');
}

async function test() {
  await save();
  showStatus('ok', 'Testing…');
  try {
    const eps = await listEpisodes();
    showStatus('ok', `Connected — ${eps.length} episodes visible. Latest: ${eps[0]?.number ?? 'n/a'}`);
  } catch (e) {
    showStatus('err', `Connection failed: ${e.message}${e.status ? ` (HTTP ${e.status})` : ''}`);
  }
}

document.getElementById('saveBtn').addEventListener('click', save);
document.getElementById('testBtn').addEventListener('click', test);
load();
