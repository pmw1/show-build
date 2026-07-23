// Turn a context-menu click (OnClickData + tab) into a CaptureCreate payload
// for POST /api/whiteboard/{ep}/captures.

// TLDs accepted for bare two-part domains ("x.com") with no scheme/www/path —
// keeps lone filenames like "convert.py" from being mistaken for URLs.
const COMMON_TLDS = new Set([
  'com', 'net', 'org', 'io', 'tv', 'app', 'dev', 'co', 'me', 'us', 'uk', 'ca',
  'au', 'de', 'fr', 'it', 'nl', 'es', 'se', 'ch', 'jp', 'cn', 'in', 'br', 'mx',
  'gov', 'edu', 'mil', 'info', 'biz', 'xyz', 'ly', 'fm', 'cc', 'gg', 'to', 'watch',
]);

// A selection that is just one URL — with or without a scheme, the way pages
// often print them as plain text — becomes a link capture.
export function asLoneUrl(raw) {
  let t = (raw || '').trim().replace(/[.,;]+$/, '');
  if (!t.includes('(')) t = t.replace(/\)+$/, ''); // sentence paren, not a wiki URL's
  if (/\s/.test(t)) return null;
  if (/^https?:\/\//i.test(t)) return t;
  const m = t.match(/^(www\.)?([a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+)(:\d+)?(\/\S*)?$/i);
  if (!m) return null;
  const host = m[2].toLowerCase();
  const tld = host.slice(host.lastIndexOf('.') + 1);
  if (m[1] || m[4] || COMMON_TLDS.has(tld)) return `https://${t}`;
  return null;
}

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
    const url = asLoneUrl(info.selectionText);
    if (url) {
      return { ...base, capture_kind: 'link', url }; // highlighted URL → link card
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
