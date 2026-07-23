// Fetch wrapper for the Show-Build API: base URL + X-API-Key from settings.

import { getSettings } from './settings.js';

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status; // 0 = network/timeout, else HTTP status
  }
}

async function request(path, { method = 'GET', json, formData, timeoutMs = 30000 } = {}) {
  const { baseUrl, apiKey } = await getSettings();
  if (!apiKey) throw new ApiError(401, 'No API key configured — open the extension options.');

  const headers = { 'X-API-Key': apiKey };
  let body;
  if (json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(json);
  } else if (formData) {
    body = formData; // browser sets multipart boundary
  }

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  let resp;
  try {
    resp = await fetch(`${baseUrl}${path}`, { method, headers, body, signal: ctrl.signal });
  } catch (e) {
    throw new ApiError(0, e.message || 'Network error');
  } finally {
    clearTimeout(timer);
  }

  if (!resp.ok) {
    let detail = '';
    try { detail = (await resp.json()).detail || ''; } catch { /* non-JSON error body */ }
    throw new ApiError(resp.status, detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

// Only episodes actively being built are capture targets.
const VISIBLE_STATUSES = new Set(['draft', 'production']);

export async function listEpisodes() {
  const data = await request('/api/episodes/');
  return (data.episodes || [])
    .filter((e) => VISIBLE_STATUSES.has((e.status || '').toLowerCase()))
    .map((e) => ({ number: e.episode_number, title: e.title || '' }));
}

export function createCapture(episode, payload) {
  return request(`/api/whiteboard/${episode}/captures`, { method: 'POST', json: payload, timeoutMs: 20000 });
}

export function getCapture(episode, id) {
  return request(`/api/whiteboard/${episode}/captures/${id}`);
}

export function listCaptures(episode, status = 'all', limit = 15) {
  return request(`/api/whiteboard/${episode}/captures?status=${status}&limit=${limit}`);
}

// Pre-upload a blob (screenshots, data: images) so the capture just references it.
export function uploadMedia(episode, blob, filename, { tags, sourceUrl } = {}) {
  const fd = new FormData();
  fd.append('file', blob, filename);
  if (tags) fd.append('tags', tags);
  fd.append('source', 'extension');
  if (sourceUrl) fd.append('source_url', sourceUrl);
  return request(`/api/whiteboard/${episode}/upload-media`, { method: 'POST', formData: fd, timeoutMs: 120000 });
}
