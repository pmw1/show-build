// Context-menu tree. One explicit root titled with the target episode; a
// change of episode does a full cheap rebuild so the title, radio state, and
// list stay in sync. Menus persist across service-worker suspends — creation
// only happens from onInstalled/onStartup/explicit rebuilds.

import { getSettings, setSettings } from './settings.js';

export const MENU = {
  ROOT: 'sb-root',
  SEND: 'sb-send',
  SOT: 'sb-sot',
  VO: 'sb-vo',
  NAT: 'sb-nat',
  SHOT: 'sb-shot',
  EP_MENU: 'sb-ep-menu',
  EP_REFRESH: 'sb-ep-refresh',
  EP_PREFIX: 'sb-ep-',
};

const ALL_CONTEXTS = ['selection', 'link', 'image', 'video', 'page'];
// SOT/VO/NAT also on link/page: on YouTube/X pages the <video> element only
// yields a useless blob: URL, so the page/link URL is what the server needs.
const VIDEO_CONTEXTS = ['video', 'link', 'page'];

function create(props) {
  return new Promise((resolve) => {
    chrome.contextMenus.create(props, () => {
      void chrome.runtime.lastError; // duplicate-id errors are harmless here
      resolve();
    });
  });
}

export async function rebuildMenus() {
  await new Promise((r) => chrome.contextMenus.removeAll(r));
  const { episode, episodeList } = await getSettings();
  const epLabel = episode ? `Ep ${episode}` : 'no episode set';

  await create({ id: MENU.ROOT, title: `Show-Build → ${epLabel}`, contexts: ALL_CONTEXTS });
  await create({ id: MENU.SEND, parentId: MENU.ROOT, title: 'Send to Whiteboard', contexts: ALL_CONTEXTS });
  await create({ id: MENU.SOT, parentId: MENU.ROOT, title: 'Send video as SOT', contexts: VIDEO_CONTEXTS });
  await create({ id: MENU.VO, parentId: MENU.ROOT, title: 'Send video as VO', contexts: VIDEO_CONTEXTS });
  await create({ id: MENU.NAT, parentId: MENU.ROOT, title: 'Send video as NAT', contexts: VIDEO_CONTEXTS });
  await create({ id: MENU.SHOT, parentId: MENU.ROOT, title: 'Capture visible tab (screenshot)', contexts: ['page', 'selection'] });
  await create({ id: 'sb-sep', parentId: MENU.ROOT, type: 'separator', contexts: ALL_CONTEXTS });
  await create({ id: MENU.EP_MENU, parentId: MENU.ROOT, title: 'Target episode', contexts: ALL_CONTEXTS });

  for (const ep of (episodeList || []).slice(0, 10)) {
    await create({
      id: `${MENU.EP_PREFIX}${ep.number}`,
      parentId: MENU.EP_MENU,
      type: 'radio',
      checked: ep.number === episode,
      title: `${ep.number}${ep.title ? ' — ' + ep.title.slice(0, 40) : ''}`,
      contexts: ALL_CONTEXTS,
    });
  }
  await create({ id: MENU.EP_REFRESH, parentId: MENU.EP_MENU, title: 'Refresh episode list…', contexts: ALL_CONTEXTS });
}

export async function setEpisode(episode) {
  await setSettings({ episode });
  await rebuildMenus();
}
