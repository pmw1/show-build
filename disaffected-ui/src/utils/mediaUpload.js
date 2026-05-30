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
