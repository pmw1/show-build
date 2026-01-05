import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Intelligent Clipboard Image Detection Composable
 *
 * Detects and handles multiple types of image paste operations:
 * - Direct binary images (screenshots, copied image files)
 * - HTML clipboard format (Google Docs embedded images)
 * - File references (dragged files)
 * - URL-embedded images (plain text URLs)
 *
 * Provides real-time feedback for multi-step operations (download, convert, process)
 * with minimum 300ms display time per step.
 *
 * @example
 * const {
 *   buttonLabel,
 *   buttonColor,
 *   statusMessage,
 *   pasteImage,
 *   isProcessing
 * } = useClipboardImageDetection({
 *   onImageReady: (file, filename) => {
 *     // Handle the processed image file
 *   }
 * })
 */
export function useClipboardImageDetection(options = {}) {
  const {
    onImageReady = null,
    autoProbeClipboard = true,
    minStepDuration = 300 // Minimum ms to display each step
  } = options

  // Reactive state
  const detectedTypes = ref([])
  const primaryType = ref(null)
  const buttonLabel = ref('Paste from Clipboard')
  const buttonColor = ref('primary')
  const statusMessage = ref('')
  const isProcessing = ref(false)
  const error = ref(null)

  // Paste type constants
  const PASTE_TYPES = {
    DIRECT_BINARY: 'direct-binary',
    HTML_CLIPBOARD: 'html-clipboard',
    FILE_REFERENCE: 'file-reference',
    URL_EMBEDDED: 'url-embedded',
    CLIPBOARD_PICKLING: 'clipboard-pickling'
  }

  const TYPE_LABELS = {
    [PASTE_TYPES.DIRECT_BINARY]: 'Paste Direct Image',
    [PASTE_TYPES.HTML_CLIPBOARD]: 'Paste HTML Clipboard Image',
    [PASTE_TYPES.FILE_REFERENCE]: 'Paste File Image',
    [PASTE_TYPES.URL_EMBEDDED]: 'Paste Image from URL',
    [PASTE_TYPES.CLIPBOARD_PICKLING]: 'Paste Structured Image'
  }

  /**
   * Probe clipboard to detect available paste types
   */
  async function probeClipboard() {
    console.log('🔍 Probing clipboard for image types...')
    const types = []

    try {
      // Check for direct binary images AND HTML via Clipboard API
      if (navigator.clipboard && navigator.clipboard.read) {
        try {
          const clipboardItems = await navigator.clipboard.read()
          for (const item of clipboardItems) {
            console.log('📋 Clipboard item types:', item.types)
            for (const type of item.types) {
              if (type.startsWith('image/')) {
                types.push(PASTE_TYPES.DIRECT_BINARY)
                console.log('✓ Found direct binary image:', type)
              }
              // Check for HTML format (Google Docs copies as text/html)
              if (type === 'text/html') {
                try {
                  const htmlBlob = await item.getType('text/html')
                  const htmlText = await htmlBlob.text()
                  if (htmlText && htmlText.includes('<img')) {
                    types.push(PASTE_TYPES.HTML_CLIPBOARD)
                    console.log('✓ Found HTML clipboard with image tag')
                  }
                } catch (htmlErr) {
                  console.log('Could not read HTML content:', htmlErr.message)
                }
              }
            }
          }
        } catch (clipError) {
          console.log('Clipboard API read failed (may need permission):', clipError.message)
          // When clipboard API fails, assume paste might work - be optimistic
          // Google Docs copying often fails probing but works on actual paste
          types.push(PASTE_TYPES.HTML_CLIPBOARD)
          console.log('✓ Assuming HTML clipboard may be available (probe failed but paste may work)')
        }
      }

      // Check for URL in plain text clipboard
      if (navigator.clipboard && navigator.clipboard.readText) {
        try {
          const text = await navigator.clipboard.readText()
          if (text) {
            // Check for direct image URL
            if (text.match(/^https?:\/\/.+\.(jpg|jpeg|png|gif|webp|svg)/i)) {
              types.push(PASTE_TYPES.URL_EMBEDDED)
              console.log('✓ Found URL-embedded image')
            }
            // Check for HTML in plain text (sometimes happens)
            if (text.includes('<img') && !types.includes(PASTE_TYPES.HTML_CLIPBOARD)) {
              types.push(PASTE_TYPES.HTML_CLIPBOARD)
              console.log('✓ Found HTML in plain text')
            }
          }
        } catch (textError) {
          console.log('Text read failed:', textError.message)
        }
      }

    } catch (err) {
      console.error('Clipboard probe error:', err)
    }

    // Remove duplicates
    detectedTypes.value = [...new Set(types)]

    // Set primary type (priority order)
    if (types.includes(PASTE_TYPES.DIRECT_BINARY)) {
      primaryType.value = PASTE_TYPES.DIRECT_BINARY
    } else if (types.includes(PASTE_TYPES.FILE_REFERENCE)) {
      primaryType.value = PASTE_TYPES.FILE_REFERENCE
    } else if (types.includes(PASTE_TYPES.HTML_CLIPBOARD)) {
      primaryType.value = PASTE_TYPES.HTML_CLIPBOARD
    } else if (types.includes(PASTE_TYPES.URL_EMBEDDED)) {
      primaryType.value = PASTE_TYPES.URL_EMBEDDED
    } else {
      // Even if nothing detected, be optimistic - user might paste from Google Docs
      primaryType.value = PASTE_TYPES.HTML_CLIPBOARD
      console.log('📋 No specific type detected, defaulting to HTML clipboard (try pasting anyway)')
    }

    // Update button label - always show a usable button
    buttonLabel.value = TYPE_LABELS[primaryType.value] || 'Paste from Clipboard'
    buttonColor.value = 'primary'
    console.log('📋 Primary paste type:', primaryType.value)

    return types
  }

  /**
   * Display a status message for minimum duration
   */
  async function showStatus(message, color = 'info', duration = minStepDuration) {
    statusMessage.value = message
    buttonLabel.value = message
    buttonColor.value = color
    console.log(`📊 Status: ${message}`)

    await new Promise(resolve => setTimeout(resolve, duration))
  }

  /**
   * Handle direct binary image paste
   */
  async function handleDirectBinaryPaste(event) {
    console.log('🖼️ Handling direct binary paste')

    // Try Clipboard API first
    if (navigator.clipboard && navigator.clipboard.read) {
      try {
        const clipboardItems = await navigator.clipboard.read()
        for (const item of clipboardItems) {
          for (const type of item.types) {
            if (type.startsWith('image/')) {
              await showStatus('Processing image...', 'info')
              const blob = await item.getType(type)
              const file = new File([blob], 'pasted-image.png', { type })
              return { file, filename: 'pasted-image.png' }
            }
          }
        }
      } catch (err) {
        console.error('Clipboard API failed:', err)
      }
    }

    // Fallback to paste event if provided
    if (event && event.clipboardData) {
      // Check files first
      if (event.clipboardData.files && event.clipboardData.files.length > 0) {
        for (const file of event.clipboardData.files) {
          if (file.type.startsWith('image/')) {
            await showStatus('Processing image...', 'info')
            return { file, filename: file.name || 'pasted-image.png' }
          }
        }
      }

      // Check items
      if (event.clipboardData.items) {
        for (const item of event.clipboardData.items) {
          if (item.type.startsWith('image/') && item.kind === 'file') {
            const file = item.getAsFile()
            if (file) {
              await showStatus('Processing image...', 'info')
              return { file, filename: 'pasted-image.png' }
            }
          }
        }
      }
    }

    throw new Error('No binary image data found')
  }

  /**
   * Handle HTML clipboard format (Google Docs)
   */
  async function handleHTMLClipboardPaste(event) {
    console.log('📄 Handling HTML clipboard paste')

    let html = null

    // Try to get HTML from clipboard event first
    if (event && event.clipboardData) {
      html = event.clipboardData.getData('text/html')
      console.log('📄 Got HTML from clipboard event, length:', html?.length || 0)
    }

    // Fallback to Clipboard API read() for HTML blob
    if ((!html || html.trim() === '') && navigator.clipboard && navigator.clipboard.read) {
      try {
        const clipboardItems = await navigator.clipboard.read()
        for (const item of clipboardItems) {
          if (item.types.includes('text/html')) {
            const htmlBlob = await item.getType('text/html')
            html = await htmlBlob.text()
            console.log('📄 Got HTML from Clipboard API read(), length:', html?.length || 0)
            break
          }
        }
      } catch (readErr) {
        console.log('Clipboard API read() failed:', readErr.message)
      }
    }

    // Last resort: check plain text for HTML
    if ((!html || html.trim() === '') && navigator.clipboard && navigator.clipboard.readText) {
      try {
        const text = await navigator.clipboard.readText()
        if (text && text.includes('<img')) {
          html = text
          console.log('📄 Got HTML from plain text clipboard')
        }
      } catch (textErr) {
        console.log('Plain text read failed:', textErr.message)
      }
    }

    if (!html || html.trim() === '') {
      console.error('❌ No HTML content found on clipboard')
      throw new Error('No HTML content found on clipboard. Try: Right-click image → Copy Image (not Copy)')
    }

    console.log('📄 HTML content (first 500 chars):', html.substring(0, 500))

    // Parse HTML to extract image URL
    const parser = new DOMParser()
    const doc = parser.parseFromString(html, 'text/html')
    const images = doc.querySelectorAll('img')

    console.log('📄 Found', images.length, 'image tags in HTML')

    if (images.length === 0) {
      console.error('❌ No image tags found in HTML content')
      // Log full HTML for debugging
      console.error('📄 Full HTML:', html)
      throw new Error('No image found in clipboard HTML. Make sure you right-click the image and select "Copy Image"')
    }

    const imageUrl = images[0].src
    console.log('📄 Extracted image URL:', imageUrl?.substring(0, 100) + '...')

    // Validate URL
    if (!imageUrl || (!imageUrl.startsWith('http://') && !imageUrl.startsWith('https://') && !imageUrl.startsWith('data:'))) {
      console.error('❌ Invalid image URL:', imageUrl)
      throw new Error('Invalid image URL in HTML content')
    }

    // Handle data URLs (base64 encoded images)
    if (imageUrl.startsWith('data:')) {
      console.log('📄 Processing data URL (base64 image)')
      await showStatus('Converting data URL...', 'info')

      try {
        // Convert data URL to blob
        const response = await fetch(imageUrl)
        const blob = await response.blob()
        const contentType = blob.type || 'image/png'
        const extension = contentType.split('/')[1] || 'png'

        await showStatus('Processing image...', 'info')
        const file = new File([blob], `google-docs-image.${extension}`, { type: contentType })
        console.log('✅ Successfully converted data URL to file')
        return { file, filename: file.name }
      } catch (err) {
        console.error('❌ Failed to convert data URL:', err)
        throw new Error('Failed to process base64 image')
      }
    }

    // Handle regular HTTP(S) URLs
    await showStatus('Downloading from source...', 'info')
    console.log('📄 Downloading image from URL:', imageUrl)

    // Download image from URL
    const response = await fetch(imageUrl, {
      mode: 'cors',
      credentials: 'omit'
    })

    if (!response.ok) {
      console.error('❌ Download failed with status:', response.status)
      throw new Error(`Failed to download image: HTTP ${response.status}`)
    }

    await showStatus('Converting to file...', 'info')

    const blob = await response.blob()
    const contentType = response.headers.get('content-type') || 'image/png'
    const extension = contentType.split('/')[1] || 'png'

    console.log('📄 Downloaded blob, type:', contentType, 'size:', blob.size)

    await showStatus('Processing image...', 'info')

    const file = new File([blob], `google-docs-image.${extension}`, { type: contentType })
    console.log('✅ Successfully created file from downloaded image')
    return { file, filename: file.name }
  }

  /**
   * Handle URL-embedded paste
   */
  async function handleURLEmbeddedPaste(event) {
    console.log('🔗 Handling URL-embedded paste')

    let url = null

    // Try to get URL from clipboard event
    if (event && event.clipboardData) {
      url = event.clipboardData.getData('text/plain')
    }

    // Fallback to Clipboard API
    if (!url && navigator.clipboard && navigator.clipboard.readText) {
      url = await navigator.clipboard.readText()
    }

    if (!url || !url.match(/^https?:\/\/.+\.(jpg|jpeg|png|gif|webp|svg)/i)) {
      throw new Error('No valid image URL found on clipboard')
    }

    await showStatus('Validating URL...', 'info')
    console.log('Image URL:', url)

    await showStatus('Downloading...', 'info')

    const response = await fetch(url, {
      mode: 'cors',
      credentials: 'omit'
    })

    if (!response.ok) {
      throw new Error(`Failed to download image: HTTP ${response.status}`)
    }

    await showStatus('Processing...', 'info')

    const blob = await response.blob()
    const contentType = response.headers.get('content-type') || 'image/png'
    const filename = url.split('/').pop() || 'url-image.png'

    const file = new File([blob], filename, { type: contentType })
    return { file, filename }
  }

  /**
   * Main paste handler - routes to appropriate method based on detected type
   * @param {ClipboardEvent} event - Paste event
   * @param {boolean} silent - If true, don't re-throw errors (for global paste handler)
   */
  async function pasteImage(event = null, silent = false) {
    if (isProcessing.value) {
      console.log('⏳ Already processing, ignoring duplicate paste')
      return
    }

    isProcessing.value = true
    error.value = null
    buttonColor.value = 'info'

    try {
      let result = null

      // If no type detected, try to detect from event
      let typeToUse = primaryType.value

      if (!typeToUse && event && event.clipboardData) {
        // Debug: Log all clipboard types
        console.log('🔍 Clipboard types available:', Array.from(event.clipboardData.types))
        console.log('🔍 Clipboard files count:', event.clipboardData.files?.length || 0)

        // Log clipboard items for debugging
        if (event.clipboardData.items) {
          console.log('🔍 Clipboard items:')
          for (const item of event.clipboardData.items) {
            console.log(`  - Type: ${item.type}, Kind: ${item.kind}`)
          }
        }

        // Quick detection from paste event
        if (event.clipboardData.files && event.clipboardData.files.length > 0) {
          console.log('✓ Detected DIRECT_BINARY (files)')
          typeToUse = PASTE_TYPES.DIRECT_BINARY
        } else if (event.clipboardData.types.includes('text/html')) {
          console.log('✓ Detected HTML_CLIPBOARD (text/html)')
          typeToUse = PASTE_TYPES.HTML_CLIPBOARD
        } else if (event.clipboardData.types.includes('text/plain')) {
          const text = event.clipboardData.getData('text/plain')
          console.log('🔍 Plain text content (first 200 chars):', text.substring(0, 200))
          if (text.match(/^https?:\/\//)) {
            console.log('✓ Detected URL_EMBEDDED')
            typeToUse = PASTE_TYPES.URL_EMBEDDED
          }
        }
      }

      // Route to appropriate handler
      switch (typeToUse) {
        case PASTE_TYPES.DIRECT_BINARY:
          result = await handleDirectBinaryPaste(event)
          break
        case PASTE_TYPES.HTML_CLIPBOARD:
          result = await handleHTMLClipboardPaste(event)
          // If HTML method returns null, try other methods
          if (!result && event.clipboardData) {
            console.log('📄 HTML method returned null, trying URL fallback...')
            // Try URL embedded as fallback
            const urlText = event.clipboardData.getData('text/plain')
            if (urlText && (urlText.startsWith('http://') || urlText.startsWith('https://'))) {
              console.log('📄 Found URL in plain text, trying URL_EMBEDDED handler')
              result = await handleURLEmbeddedPaste(event)
            }
          }
          break
        case PASTE_TYPES.URL_EMBEDDED:
          result = await handleURLEmbeddedPaste(event)
          break
        default:
          console.error('❌ No supported image format detected')
          console.error('Available types:', typeToUse, primaryType.value)
          if (event && event.clipboardData) {
            console.error('Clipboard types:', Array.from(event.clipboardData.types))
          }
          throw new Error('No supported image format detected on clipboard. Try copying the image directly (right-click > Copy Image) or use Select File instead.')
      }

      // Check if we got a result
      if (!result) {
        throw new Error('No image data found in clipboard')
      }

      // Success!
      await showStatus('Image ready!', 'success')

      // Call callback with result
      if (onImageReady && result) {
        onImageReady(result.file, result.filename)
      }

      return result

    } catch (err) {
      console.error('❌ Paste error:', err)
      error.value = err.message
      buttonColor.value = 'error'
      buttonLabel.value = 'Paste Failed - Try Again'
      statusMessage.value = err.message

      if (!silent) {
        throw err
      }

    } finally {
      // Reset processing state after a delay
      setTimeout(() => {
        isProcessing.value = false
        if (!error.value) {
          // Re-probe clipboard for next paste
          probeClipboard()
        }
      }, 500)
    }
  }

  /**
   * Global paste event listener - only processes image pastes
   */
  function handleGlobalPaste(event) {
    // Ignore paste events in text input fields (content editor, forms, etc.)
    const target = event.target
    if (target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target.contentEditable === 'true' ||
        target.closest('[contenteditable="true"]')) {
      // Let normal text paste happen
      return
    }

    console.log('📋 Global paste event detected (non-text field)')
    pasteImage(event, true).catch(err => {
      console.warn('Paste event failed (silently handled):', err.message)
      // Silently handle global paste errors - don't break the page
    })
  }

  // Lifecycle
  onMounted(() => {
    if (autoProbeClipboard) {
      probeClipboard()
    }

    // Listen for paste events globally when component is active
    window.addEventListener('paste', handleGlobalPaste)
  })

  onUnmounted(() => {
    window.removeEventListener('paste', handleGlobalPaste)
  })

  return {
    // State
    detectedTypes,
    primaryType,
    buttonLabel,
    buttonColor,
    statusMessage,
    isProcessing,
    error,

    // Methods
    pasteImage,
    probeClipboard,

    // Constants
    PASTE_TYPES,
    TYPE_LABELS
  }
}
