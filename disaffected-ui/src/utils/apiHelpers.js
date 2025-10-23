/**
 * API Helper Utilities
 *
 * Provides safe JSON parsing and error handling for API responses
 */

/**
 * Safely parse JSON response, handling HTML error pages
 *
 * @param {Response} response - Fetch API response object
 * @returns {Promise<Object>} Parsed JSON data
 * @throws {Error} With appropriate error message
 */
export async function safeJsonParse(response) {
  const contentType = response.headers.get('content-type')

  // Check if response is actually JSON
  if (contentType && contentType.includes('application/json')) {
    try {
      return await response.json()
    } catch (error) {
      throw new Error(`Failed to parse JSON response: ${error.message}`)
    }
  }

  // Response is not JSON (probably HTML error page)
  const text = await response.text()

  // Try to extract meaningful error from HTML
  const match = text.match(/<title>(.*?)<\/title>/i)
  if (match) {
    throw new Error(`Server returned HTML: ${match[1]}`)
  }

  // Generic error with status code
  throw new Error(`Server error: ${response.status} ${response.statusText}`)
}

/**
 * Fetch JSON with automatic error handling
 *
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<Object>} Parsed JSON response
 * @throws {Error} With user-friendly error message
 */
export async function fetchJson(url, options = {}) {
  try {
    // Add default headers
    const defaultHeaders = {
      'Content-Type': 'application/json'
    }

    // Add auth - try JWT token first, then API key
    const token = localStorage.getItem('token')
    const apiKey = localStorage.getItem('api_key')

    if (token) {
      defaultHeaders.Authorization = `Bearer ${token}`
    } else if (apiKey) {
      defaultHeaders['X-API-Key'] = apiKey
    } else {
      // Fallback to hardcoded API key for public endpoints
      defaultHeaders['X-API-Key'] = 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers
      }
    })

    // Handle non-OK responses
    if (!response.ok) {
      let errorMessage = `Request failed: ${response.status} ${response.statusText}`

      try {
        const errorData = await safeJsonParse(response)
        errorMessage = errorData.detail || errorData.message || errorMessage
      } catch {
        // If we can't parse error, use the generic message
      }

      throw new Error(errorMessage)
    }

    // Parse successful response
    return await safeJsonParse(response)

  } catch (error) {
    // Re-throw with context
    if (error.message.includes('Failed to fetch')) {
      throw new Error('Network error: Unable to reach server')
    }
    throw error
  }
}

/**
 * Create a fetch wrapper with base URL
 *
 * @param {string} baseUrl - Base URL for all requests
 * @returns {Function} Fetch function with base URL applied
 */
export function createApiClient(baseUrl) {
  return (endpoint, options = {}) => {
    const url = `${baseUrl}${endpoint}`
    return fetchJson(url, options)
  }
}

// Default API client for /api endpoints
export const api = createApiClient('/api')
