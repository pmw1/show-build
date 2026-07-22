// Settings storage. Everything syncs across the user's Chrome profiles except
// the API key, which stays in storage.local (never sync secrets).

const SYNC_DEFAULTS = {
  baseUrl: 'https://showbuild.app',
  episode: null,        // 4-digit episode string, e.g. "0284"
  episodeList: [],      // [{number, title}] cache for the menus/popup
};

export async function getSettings() {
  const sync = await chrome.storage.sync.get(SYNC_DEFAULTS);
  const local = await chrome.storage.local.get({ apiKey: '' });
  return { ...sync, apiKey: local.apiKey };
}

export async function setSettings(patch) {
  const { apiKey, ...rest } = patch;
  if (apiKey !== undefined) await chrome.storage.local.set({ apiKey });
  if (Object.keys(rest).length) await chrome.storage.sync.set(rest);
}
