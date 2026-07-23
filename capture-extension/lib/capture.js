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

// X serves timeline images as small variants (?name=small); request the
// original so the pool gets full resolution.
export function upgradeImageUrl(url) {
  try {
    const u = new URL(url);
    if (u.hostname === 'pbs.twimg.com' && u.searchParams.has('name')) {
      u.searchParams.set('name', 'orig');
      return u.toString();
    }
  } catch { /* not a parseable URL — leave as-is */ }
  return url;
}

// If a right-clicked image sits inside a social post, this returns the post's
// canonical URL (X photo permalinks are normalized back to the status URL) so
// the generic "Send to Whiteboard" can capture the WHOLE post. Image-only
// capture is the explicit "Send just this image" item.
export function socialPostUrl(u) {
  if (!u) return null;
  try {
    const url = new URL(u);
    const h = url.hostname.toLowerCase();
    if (/(^|\.)(twitter\.com|x\.com)$/.test(h)) {
      const m = url.pathname.match(/^(\/[^/]+\/status\/\d+)/);
      return m ? `${url.origin}${m[1]}` : null;
    }
    if (/(^|\.)instagram\.com$/.test(h) && /^\/(p|reel)\//.test(url.pathname)) return u.split('?')[0];
    if (/(^|\.)tiktok\.com$/.test(h) && url.pathname.includes('/video/')) return u.split('?')[0];
    if (/(^|\.)(facebook\.com|fb\.watch)$/.test(h)) return u;
  } catch { /* not a parseable URL */ }
  return null;
}

// Explicit image-only capture (the "Send just this image" menu item): always
// uses srcUrl, ignoring any co-present link/selection/post context.
export function buildImagePayload(info, tab) {
  return {
    capture_kind: 'image',
    url: info.srcUrl.startsWith('data:') ? info.srcUrl : upgradeImageUrl(info.srcUrl),
    page_url: info.pageUrl || tab?.url || null,
    page_title: tab?.title || null,
    client_capture_id: crypto.randomUUID(),
    source: { agent: 'chrome-extension', version: chrome.runtime.getManifest().version },
  };
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
    // An image inside a social post: "Send to Whiteboard" means the WHOLE
    // post (server downloads all media + metadata). The wrapping link (X
    // timeline) or the page itself (lightbox) identifies the post.
    const post = socialPostUrl(info.linkUrl) || socialPostUrl(page_url);
    if (post) {
      return { ...base, capture_kind: 'page', url: post };
    }
    // Plain image elsewhere: data: URLs are pre-uploaded by the background
    // handler; remote URLs are fetched server-side (immune to page CORS).
    const url = info.srcUrl.startsWith('data:') ? info.srcUrl : upgradeImageUrl(info.srcUrl);
    return { ...base, capture_kind: 'image', url };
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
