// Turn a context-menu click (OnClickData + tab) into a CaptureCreate payload
// for POST /api/whiteboard/{ep}/captures.

const LONE_URL_RE = /^https?:\/\/\S+$/i;

export function buildCapturePayload(info, tab, cueType = null) {
  const page_url = info.pageUrl || tab?.url || null;
  const page_title = tab?.title || null;
  const base = {
    page_url,
    page_title,
    client_capture_id: crypto.randomUUID(),
    source: { agent: 'chrome-extension', version: chrome.runtime.getManifest().version },
  };

  if (cueType) {
    // Typed video capture: srcUrl only when it's a real fetchable URL —
    // blob:/data: video sources mean "capture the page URL server-side".
    const src = info.srcUrl && !info.srcUrl.startsWith('blob:') && !info.srcUrl.startsWith('data:')
      ? info.srcUrl : null;
    return { ...base, capture_kind: 'video', url: src || info.linkUrl || page_url, intended_cue_type: cueType };
  }

  if (info.selectionText !== undefined && info.selectionText !== '') {
    const text = info.selectionText.trim();
    if (LONE_URL_RE.test(text)) {
      return { ...base, capture_kind: 'link', url: text }; // highlighted URL → link card
    }
    return { ...base, capture_kind: 'selection', text_content: info.selectionText };
  }

  if (info.mediaType === 'image' && info.srcUrl) {
    // data: URLs are pre-uploaded by the background handler; remote URLs are
    // fetched server-side (immune to page CORS / referer checks).
    return { ...base, capture_kind: 'image', url: info.srcUrl };
  }

  if (info.mediaType === 'video' && info.srcUrl) {
    const url = info.srcUrl.startsWith('blob:') ? page_url : info.srcUrl;
    return { ...base, capture_kind: 'video', url };
  }

  if (info.linkUrl) {
    return { ...base, capture_kind: 'link', url: info.linkUrl };
  }

  return { ...base, capture_kind: 'page', url: page_url, title: page_title };
}
