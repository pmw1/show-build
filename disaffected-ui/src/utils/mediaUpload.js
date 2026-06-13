/**
 * uploadVideoInBackground — shared XHR scaffold for SOT/VO/etc. media uploads.
 *
 * Posts a file to the provided endpoint as multipart/form-data, surfaces
 * progress via callback, returns the parsed JSON response on success.
 *
 * Authorization header is read from localStorage:
 *   - 'auth-token' (Bearer)  — preferred
 *   - 'api_key'    (X-API-Key) — fallback
 * (matches the pattern both SotModal and VoModal use today)
 *
 * Returns { promise, abort } so callers can cancel mid-upload (used by
 * clearVideo / ESC-during-upload to prevent stale `load` events writing
 * to a reset modal).
 *
 * @param {File} file
 * @param {string} endpoint  e.g. '/api/sot/upload/background'
 * @param {object} [options]
 * @param {(percent:number) => void} [options.onProgress]
 * @returns {{ promise: Promise<object>, abort: () => void }}
 */
export function uploadVideoInBackground(file, endpoint, options = {}) {
  const { onProgress } = options
  const xhr = new XMLHttpRequest()
  let aborted = false

  const promise = new Promise((resolve, reject) => {
    if (!file) {
      reject(new Error('uploadVideoInBackground: file is required'))
      return
    }
    if (!endpoint) {
      reject(new Error('uploadVideoInBackground: endpoint is required'))
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    xhr.upload.addEventListener('progress', (e) => {
      if (aborted) return
      if (e.lengthComputable && typeof onProgress === 'function') {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    })

    xhr.addEventListener('load', () => {
      if (aborted) return
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText))
        } catch (err) {
          reject(new Error(`Response parse failed: ${err.message}`))
        }
      } else {
        reject(new Error(xhr.statusText || `HTTP ${xhr.status}`))
      }
    })

    xhr.addEventListener('error', () => {
      if (aborted) return
      reject(new Error('Network error'))
    })

    xhr.addEventListener('abort', () => {
      // Resolved as abort — callers check the abort() return path
      // separately (don't surface as a rejection-noise toast).
      reject(new Error('aborted'))
    })

    const token = localStorage.getItem('auth-token')
    const apiKey = localStorage.getItem('api_key')

    xhr.open('POST', endpoint, true)
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    } else if (apiKey) {
      xhr.setRequestHeader('X-API-Key', apiKey)
    }
    xhr.send(formData)
  })

  return {
    promise,
    abort() {
      aborted = true
      try { xhr.abort() } catch (_) { /* noop */ }
    }
  }
}

/**
 * uploadVideoChunked — chunked/resumable-ish upload for LARGE files (>100 MB).
 *
 * Why: when the app is reached via the Cloudflare tunnel (showbuild.app),
 * Cloudflare rejects any single request body over 100 MB with HTTP 413 at the
 * edge — before it reaches the server. A 658 MB SOT source can never upload in
 * one POST. This slices the file into <100 MB chunks, sends them sequentially
 * to `${baseEndpoint}/chunk`, then calls `${baseEndpoint}/complete` to assemble
 * them server-side into the same working file a single-shot upload produces.
 *
 * Mirrors uploadVideoInBackground's `{ promise, abort }` contract so callers
 * can cancel mid-upload.
 *
 * Progress is reported richly so the UI can show a detailed panel:
 *   onProgress({ percent, chunkIndex, totalChunks, bytesSent, totalBytes, etaSeconds })
 *   onStage(stage)  // 'uploading' | 'reassembling' | 'complete' | 'failed'
 *
 * @param {File} file
 * @param {string} baseEndpoint  e.g. '/api/sot/upload' (NOT including /chunk)
 * @param {object} [options]
 * @param {number} [options.chunkSize]  bytes per chunk (default 50 MB)
 * @param {(p:object) => void} [options.onProgress]
 * @param {(stage:string) => void} [options.onStage]
 * @param {number} [options.maxRetries]  per-chunk retry attempts (default 3)
 * @returns {{ promise: Promise<object>, abort: () => void }}
 */
export function uploadVideoChunked(file, baseEndpoint, options = {}) {
  const {
    onProgress,
    onStage,
    chunkSize = 50 * 1024 * 1024, // 50 MB — safely under Cloudflare's 100 MB cap
    maxRetries = 3,
  } = options

  let aborted = false
  let activeXhr = null

  const authHeaders = () => {
    const token = localStorage.getItem('auth-token')
    const apiKey = localStorage.getItem('api_key')
    if (token) return { name: 'Authorization', value: `Bearer ${token}` }
    if (apiKey) return { name: 'X-API-Key', value: apiKey }
    return null
  }

  // Client-generated job id ties the chunks together. Mirrors the backend's
  // own `sot_{ts}_{rand}` shape so it reads consistently in logs/DB.
  const ts = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)
  const rand = Math.random().toString(16).slice(2, 10)
  const tempJobId = `sot_${ts}_${rand}`

  const totalBytes = file.size
  const totalChunks = Math.ceil(totalBytes / chunkSize)

  // POST one chunk; resolves with parsed JSON, rejects on HTTP error / network.
  const postChunk = (blob, chunkIndex) => new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    activeXhr = xhr
    const fd = new FormData()
    fd.append('file', blob, `${tempJobId}.part${chunkIndex}`)
    fd.append('temp_job_id', tempJobId)
    fd.append('chunk_index', String(chunkIndex))
    fd.append('total_chunks', String(totalChunks))

    // Per-chunk byte progress feeds the aggregate ETA/percent.
    xhr.upload.addEventListener('progress', (e) => {
      if (aborted || !e.lengthComputable || typeof onProgress !== 'function') return
      const bytesSent = chunkIndex * chunkSize + e.loaded
      reportProgress(bytesSent)
    })
    xhr.addEventListener('load', () => {
      if (aborted) return
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText)) }
        catch (err) { reject(new Error(`Chunk ${chunkIndex} parse failed: ${err.message}`)) }
      } else if (xhr.status === 413) {
        reject(new Error(`HTTP 413 (chunk ${chunkIndex} still too large — lower chunkSize)`))
      } else {
        reject(new Error(xhr.statusText || `HTTP ${xhr.status} (chunk ${chunkIndex})`))
      }
    })
    xhr.addEventListener('error', () => { if (!aborted) reject(new Error(`Network error (chunk ${chunkIndex})`)) })
    xhr.addEventListener('abort', () => reject(new Error('aborted')))

    xhr.open('POST', `${baseEndpoint}/chunk`, true)
    const h = authHeaders()
    if (h) xhr.setRequestHeader(h.name, h.value)
    xhr.send(fd)
  })

  // Rolling-throughput ETA: bytes since first chunk / elapsed.
  let startTime = null
  const reportProgress = (bytesSent) => {
    if (typeof onProgress !== 'function') return
    const now = Date.now()
    if (startTime === null) startTime = now
    const elapsed = (now - startTime) / 1000
    const rate = elapsed > 0 ? bytesSent / elapsed : 0 // bytes/sec
    const remaining = Math.max(0, totalBytes - bytesSent)
    const etaSeconds = rate > 0 ? remaining / rate : null
    onProgress({
      percent: Math.min(99, Math.round((bytesSent / totalBytes) * 100)), // 100 reserved for complete
      chunkIndex: Math.min(totalChunks - 1, Math.floor(bytesSent / chunkSize)),
      totalChunks,
      bytesSent: Math.min(bytesSent, totalBytes),
      totalBytes,
      etaSeconds,
    })
  }

  const promise = (async () => {
    if (!file) throw new Error('uploadVideoChunked: file is required')
    if (!baseEndpoint) throw new Error('uploadVideoChunked: baseEndpoint is required')

    if (typeof onStage === 'function') onStage('uploading')

    for (let i = 0; i < totalChunks; i++) {
      if (aborted) throw new Error('aborted')
      const start = i * chunkSize
      const end = Math.min(start + chunkSize, totalBytes)
      const blob = file.slice(start, end)

      let attempt = 0
      // Retry a failed chunk a few times before giving up. Chunk 0 truncates
      // server-side, so re-sending chunk i overwrites/re-appends cleanly only
      // when i === current head; a mid-stream failure simply re-POSTs the same
      // index (append is idempotent enough for our sequential case because a
      // failed POST wrote nothing on the server side — it errored before close).
      for (;;) {
        try {
          await postChunk(blob, i)
          break
        } catch (err) {
          if (err.message === 'aborted') throw err
          attempt++
          if (attempt > maxRetries) {
            if (typeof onStage === 'function') onStage('failed')
            throw new Error(`Upload failed at chunk ${i + 1}/${totalChunks}: ${err.message}`)
          }
          // brief backoff
          await new Promise((r) => setTimeout(r, 500 * attempt))
        }
      }
    }

    if (aborted) throw new Error('aborted')

    // Finalize: assemble + create the job row.
    if (typeof onStage === 'function') onStage('reassembling')
    const resp = await fetch(`${baseEndpoint}/complete`, {
      method: 'POST',
      headers: (() => {
        const hh = { 'Content-Type': 'application/json' }
        const a = authHeaders()
        if (a) hh[a.name] = a.value
        return hh
      })(),
      body: JSON.stringify({
        temp_job_id: tempJobId,
        total_chunks: totalChunks,
        expected_size: totalBytes,
      }),
    })
    if (!resp.ok) {
      if (typeof onStage === 'function') onStage('failed')
      let detail = `HTTP ${resp.status}`
      try { detail = (await resp.json()).detail || detail } catch (_) { /* noop */ }
      throw new Error(`Reassembly failed: ${detail}`)
    }
    const result = await resp.json()

    if (typeof onProgress === 'function') {
      onProgress({ percent: 100, chunkIndex: totalChunks - 1, totalChunks, bytesSent: totalBytes, totalBytes, etaSeconds: 0 })
    }
    if (typeof onStage === 'function') onStage('complete')
    return result
  })()

  return {
    promise,
    abort() {
      aborted = true
      try { if (activeXhr) activeXhr.abort() } catch (_) { /* noop */ }
    },
  }
}
