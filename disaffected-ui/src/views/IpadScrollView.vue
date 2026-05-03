<template>
  <div class="ipad-scroll-container" :class="{ 'inverted': isInverted }">
    <!-- Floating Controls (upper left corner) -->
    <div v-if="!loading && !error" class="floating-controls">
      <!-- Close Button with two-press confirmation -->
      <v-btn
        icon
        size="small"
        :color="closeButtonState === 'warning' ? 'error' : 'default'"
        class="control-btn close-btn"
        @click="handleCloseClick"
        elevation="2"
      >
        <v-icon>mdi-close</v-icon>
      </v-btn>

      <!-- Contrast Inversion Button -->
      <v-btn
        icon
        size="small"
        class="control-btn invert-btn"
        @click="toggleInversion"
        elevation="2"
      >
        <v-icon>{{ isInverted ? 'mdi-invert-colors-off' : 'mdi-invert-colors' }}</v-icon>
      </v-btn>

      <!-- Fullscreen Button -->
      <v-btn
        icon
        size="small"
        class="control-btn fullscreen-btn"
        @click="toggleFullscreen"
        elevation="2"
      >
        <v-icon>{{ isFullscreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen' }}</v-icon>
      </v-btn>

      <!-- Font Size Increase Button -->
      <v-btn
        icon
        size="small"
        class="control-btn font-increase-btn"
        @click="increaseFontSize"
        elevation="2"
      >
        <v-icon>mdi-plus</v-icon>
      </v-btn>

      <!-- Font Size Decrease Button -->
      <v-btn
        icon
        size="small"
        class="control-btn font-decrease-btn"
        @click="decreaseFontSize"
        elevation="2"
      >
        <v-icon>mdi-minus</v-icon>
      </v-btn>

      <!-- Text Color Toggle Button -->
      <v-btn
        icon
        size="small"
        class="control-btn color-toggle-btn"
        @click="toggleTextColor"
        elevation="2"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <!-- Extended top element (capsule/rounded rectangle) - extended down closer to bottom circles -->
          <rect x="9" y="4" width="6" height="12.5" rx="3" ry="3" />
          <!-- Bottom left circle -->
          <circle cx="9" cy="17" r="3" />
          <!-- Bottom right circle -->
          <circle cx="15" cy="17" r="3" />
        </svg>
      </v-btn>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <v-progress-circular indeterminate size="64" color="primary" />
      <p class="loading-text">Loading Script...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <v-icon size="64" color="error">mdi-alert-circle</v-icon>
      <h2>Error Loading Script</h2>
      <p>{{ error }}</p>
      <v-btn color="primary" @click="loadScript">
        <v-icon left>mdi-refresh</v-icon>
        Retry
      </v-btn>
    </div>

    <!-- Script Content -->
    <div v-else class="script-content" :class="{ 'text-yellow': textColor === 'yellow' }" v-html="sanitizedContent"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, getCurrentInstance } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const instance = getCurrentInstance()

const loading = ref(true)
const error = ref(null)
const htmlContent = ref('')
const episodeInfo = ref(null)
const closeButtonState = ref('normal') // 'normal' or 'warning'
let closeButtonTimer = null
const isInverted = ref(false)
const isFullscreen = ref(false)
const fontSizeMultiplier = ref(1.0) // Base = 1.0, range: 0.5 to 2.0 (0.5pt = ~0.026 change)
const textColor = ref('white') // 'white' or 'yellow'

const episodeNumber = computed(() => {
  return route.params.episodeNumber
})

const sanitizedContent = computed(() => {
  if (!htmlContent.value) return ''

  // Transform the HTML for iPad display
  // Note: Content comes from our own database/backend, so sanitization
  // is not strictly necessary, but we still transform for iPad display
  return transformForIpad(htmlContent.value)
})

function getContainer() {
  return instance?.proxy?.$el || document.querySelector('.ipad-scroll-container')
}

function handleCloseClick() {
  if (closeButtonState.value === 'normal') {
    // First press - turn red and start timer
    closeButtonState.value = 'warning'

    // Set timer to reset state after 3 seconds
    closeButtonTimer = setTimeout(() => {
      closeButtonState.value = 'normal'
      closeButtonTimer = null
    }, 3000)
  } else {
    // Second press within 3 seconds - close tab/window
    clearTimeout(closeButtonTimer)
    closeButtonTimer = null

    // Try multiple methods to close the tab
    // Method 1: Standard window.close()
    window.close()

    // Method 2: Try to open a blank page and close (for some browsers)
    setTimeout(() => {
      window.open('', '_self', '')
      window.close()
    }, 50)

    // Method 3: If still open after 200ms, navigate to about:blank
    // This effectively "closes" the tab for the user
    setTimeout(() => {
      if (!window.closed) {
        window.location.href = 'about:blank'
      }
    }, 200)
  }
}

function toggleInversion() {
  isInverted.value = !isInverted.value

  // Apply black background to body and app container to eliminate white sidebars
  if (isInverted.value) {
    document.body.style.setProperty('background-color', '#000000', 'important')
    document.body.style.setProperty('background', '#000000', 'important')
    const app = document.getElementById('app')
    if (app) {
      app.style.setProperty('background-color', '#000000', 'important')
      app.style.setProperty('background', '#000000', 'important')
    }
  } else {
    document.body.style.removeProperty('background-color')
    document.body.style.removeProperty('background')
    const app = document.getElementById('app')
    if (app) {
      app.style.removeProperty('background-color')
      app.style.removeProperty('background')
    }
  }
}

function toggleFullscreen() {
  // Use CSS-based fullscreen instead of browser API to avoid "swipe down to exit" conflict
  isFullscreen.value = !isFullscreen.value

  if (isFullscreen.value) {
    // Enter CSS fullscreen
    document.body.classList.add('css-fullscreen')
  } else {
    // Exit CSS fullscreen
    document.body.classList.remove('css-fullscreen')
  }
}

function setupFullscreenListener() {
  // No browser fullscreen listeners needed for CSS-based fullscreen
}

function removeFullscreenListener() {
  // Clean up CSS fullscreen if component unmounts while in fullscreen
  document.body.classList.remove('css-fullscreen')
}

function increaseFontSize() {
  // Increase by 1pt equivalent (1pt / 19pt base = ~0.053, using 0.1 for 2pt visible change)
  const increment = 0.1
  fontSizeMultiplier.value = Math.min(2.5, fontSizeMultiplier.value + increment)
  applyFontSize()
  console.log('Font size increased to:', fontSizeMultiplier.value)
}

function decreaseFontSize() {
  // Decrease by 1pt equivalent (using 0.1 for 2pt visible change)
  const decrement = 0.1
  fontSizeMultiplier.value = Math.max(0.5, fontSizeMultiplier.value - decrement)
  applyFontSize()
  console.log('Font size decreased to:', fontSizeMultiplier.value)
}

function toggleTextColor() {
  // Toggle between white and yellow text
  textColor.value = textColor.value === 'white' ? 'yellow' : 'white'
  applyTextColor()
  console.log('Text color changed to:', textColor.value)
}

function applyTextColor() {
  const container = getContainer()
  if (container) {
    const scriptContentEl = container.querySelector('.script-content')
    if (scriptContentEl) {
      // Apply color to all text elements in the content
      if (textColor.value === 'yellow') {
        scriptContentEl.style.setProperty('color', '#ffeb3b', 'important')
      } else {
        scriptContentEl.style.removeProperty('color')
      }
    }
  }
}

function applyFontSize() {
  // Apply font size multiplier to the content container
  // This changes actual font-size, causing proper text wrapping
  const container = getContainer()
  if (container) {
    const scriptContentEl = container.querySelector('.script-content')
    if (scriptContentEl) {
      // Set CSS variable that will cascade to all child elements
      scriptContentEl.style.setProperty('--font-size-multiplier', fontSizeMultiplier.value)

      // Also set font-size directly on the injected HTML elements
      const bodyElement = scriptContentEl.querySelector('body')

      if (bodyElement) {
        // Apply multiplier to body font-size
        bodyElement.style.fontSize = `calc(var(--base-font-size) * ${fontSizeMultiplier.value})`
      } else {
        // If no body element, apply to content container
        scriptContentEl.style.fontSize = `calc(var(--base-font-size, 19px) * ${fontSizeMultiplier.value})`
      }

      console.log('Applied font size multiplier:', fontSizeMultiplier.value)
    }
  }
}

async function loadScript() {
  loading.value = true
  error.value = null

  try {
    const authToken = localStorage.getItem('auth-token')
    const response = await axios.get(
      `/api/scripts/ipad-scroll/${episodeNumber.value}`,
      {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      }
    )

    if (response.data.success) {
      htmlContent.value = response.data.html_content
      episodeInfo.value = response.data.episode_info

      // Apply initial font size after content loads
      nextTick(() => {
        applyFontSize()
      })
    } else {
      error.value = 'Failed to load script content'
    }
  } catch (err) {
    console.error('Error loading iPad scroll content:', err)
    error.value = err.response?.data?.detail || err.message || 'Unknown error'
  } finally {
    loading.value = false
  }
}

function transformForIpad(html) {
  // Create a temporary div to manipulate HTML
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = html

  // Find and modify the style tag to add iPad-specific responsive sizing
  const styleTag = tempDiv.querySelector('style')
  if (styleTag) {
    // Add iPad-optimized styles with percentage-based font sizing
    const ipadStyles = `
      /* iPad Scroll - Responsive Typography */
      /* Base font size: responsive to viewport width with multiplier support */
      :root {
        --base-font-size: max(16px, min(4vw, 28px));
        --font-size-multiplier: 1.0;
      }

      body {
        font-size: calc(var(--base-font-size) * var(--font-size-multiplier)) !important;
        line-height: 1.6;
        margin: 0;
        padding: 20px;
        background: #ffffff;
        overflow-y: auto;
        overflow-x: hidden;
        -webkit-overflow-scrolling: touch;
        scroll-behavior: smooth;
        overscroll-behavior-y: contain;
      }

      /* Cover Page - Percentage-based sizing (base = 100%) */
      .cover-title {
        font-size: 221% !important; /* 42pt / 19pt = 221% */
        line-height: 1.2 !important;
      }

      .cover-subtitle {
        font-size: 126% !important; /* 24pt / 19pt = 126% */
      }

      .cover-guest {
        font-size: 74% !important; /* 14pt / 19pt = 74% */
      }

      /* Block Headers - BEGIN BLOCK indicator */
      .block-header {
        font-size: 147% !important; /* 28pt / 19pt = 147% */
        text-align: center;
        font-weight: bold;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        padding: 0.5em 0;
        border-top: 4px solid #1976d2;
        border-bottom: 4px solid #1976d2;
        background: #e3f2fd !important;
        color: #0d47a1 !important;
        letter-spacing: 0.15em;
        page-break-before: auto !important;
      }

      /* Block Footer - END BLOCK indicator */
      .block-end {
        font-size: 116% !important;
        text-align: center;
        font-weight: bold;
        margin-top: 1em;
        margin-bottom: 1em;
        padding: 0.4em 0;
        border-top: 3px solid #1565c0;
        border-bottom: 3px solid #1565c0;
        background: #e8eaf6 !important;
        color: #283593 !important;
        letter-spacing: 0.1em;
      }

      .block-number {
        font-size: 84% !important; /* 16pt / 19pt = 84% */
      }

      /* Segment Titles - 116% */
      .segment-title {
        font-size: 116% !important; /* 22pt / 19pt = 116% */
        margin-top: 1em;
        margin-bottom: 0.5em;
        font-weight: bold;
      }

      .segment-title-number {
        font-size: 63% !important; /* 12pt / 19pt = 63% */
      }

      /* End Segment divider (tease items) */
      .segment-end-divider {
        text-align: center;
        font-size: 63% !important;
        font-weight: bold;
        color: #888 !important;
        margin: 0.5em 0 0.3em 0;
        padding: 0.2em 0;
        letter-spacing: 0.15em;
        border-top: 1px solid #ccc;
      }

      .segment-tease .script-content {
        font-style: italic;
        color: #555 !important;
      }

      /* Speaker Names - 84% */
      .speaker-name {
        font-size: 84% !important; /* 16pt / 19pt = 84% */
        font-weight: bold;
        text-transform: uppercase;
        margin-top: 0.5em;
      }

      /* Paragraph Text - 95% */
      .paragraph {
        font-size: 95% !important; /* 18pt / 19pt = 95% */
        margin: 0.5em 0;
        line-height: 1.6;
      }

      /* SOT Elements - 100% base, 89% for meta */
      .sot-slug {
        font-size: 100% !important; /* 19pt / 19pt = 100% */
        font-weight: bold;
      }

      .sot-duration,
      .sot-transcription {
        font-size: 89% !important; /* 17pt / 19pt = 89% */
      }

      .sot-outcue {
        font-size: 100% !important; /* 19pt / 19pt = 100% */
        font-weight: bold;
        color: #d84315;
      }

      /* Cue Information */
      .cue-info {
        font-size: 100% !important; /* 19pt / 19pt = 100% */
      }

      .cue-meta {
        font-size: 89% !important; /* 17pt / 19pt = 89% */
        color: #666;
      }

      /* Image/Media Elements */
      .image-cue img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 1em auto;
      }

      /* FSQ Quotes */
      .fsq-quote {
        font-size: 100% !important; /* 19pt / 19pt = 100% */
        font-style: italic;
        margin: 1em 0;
        padding: 1em;
        background: #f5f5f5;
        border-left: 4px solid #1976d2;
      }

      /* Inline production notes - monospace, compact */
      .inline-note {
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 80% !important;
        color: #555 !important;
        margin: 2em 0 !important;
        line-height: 1.4 !important;
      }

      /* Break indicators between blocks */
      .break-indicator {
        text-align: center;
        font-size: 100% !important;
        font-weight: bold;
        padding: 0.4em 0;
        margin: 0.5em 0;
        background: #e8f5e9 !important;
        border: 2px dashed #4caf50 !important;
        color: #2e7d32 !important;
      }

      /* Ad break - distinct from generic breaks */
      .break-indicator.ad-break {
        background: #e3f2fd !important;
        border: 2px dashed #1976d2 !important;
        color: #0d47a1 !important;
      }

      .ad-label {
        font-weight: bold;
        font-size: 68% !important;
        background: #1976d2;
        color: #fff !important;
        padding: 2px 10px;
        border-radius: 4px;
        margin-right: 10px;
      }

      .ad-slug {
        font-weight: bold;
        font-size: 100% !important;
        color: #0d47a1;
      }

      .ad-duration {
        font-size: 63% !important;
        color: #64b5f6;
        margin-left: 10px;
      }

      /* Small Metadata */
      .duration,
      .timestamp,
      .metadata {
        font-size: 63% !important; /* 12pt / 19pt = 63% */
        color: #888;
      }

      /* Touch-Friendly Spacing */
      * {
        touch-action: pan-y;
      }

      /* Remove page breaks for continuous scroll */
      .page-break {
        display: none !important;
      }

      /* Hide print-specific elements */
      .footer,
      .page-number {
        display: none !important;
      }

      /* Responsive Images */
      img {
        max-width: 100%;
        height: auto;
      }

      /* Smooth Scrolling */
      html {
        scroll-behavior: smooth;
        overflow-y: auto;
        -webkit-overflow-scrolling: touch;
      }

      /* Container smooth scrolling */
      * {
        scroll-behavior: smooth;
      }

      /* iPad Landscape Optimization */
      @media (min-width: 768px) and (max-width: 1024px) and (orientation: landscape) {
        body {
          padding: 20px 60px;
        }
      }

      /* iPad Portrait Optimization */
      @media (min-width: 768px) and (max-width: 1024px) and (orientation: portrait) {
        body {
          padding: 20px 40px;
        }
      }
    `

    styleTag.textContent = styleTag.textContent + '\n' + ipadStyles
  }

  return tempDiv.innerHTML
}

onMounted(() => {
  loadScript()
  setupFullscreenListener()
})

onBeforeUnmount(() => {
  // Clear any pending timer
  if (closeButtonTimer) {
    clearTimeout(closeButtonTimer)
  }
  removeFullscreenListener()

  // Clean up body background styles
  document.body.style.removeProperty('background-color')
  document.body.style.removeProperty('background')
  const app = document.getElementById('app')
  if (app) {
    app.style.removeProperty('background-color')
    app.style.removeProperty('background')
  }
})
</script>

<style scoped>
.ipad-scroll-container {
  min-height: 100vh;
  background: #ffffff;
  position: relative;
  transition: background-color 0.3s ease, color 0.3s ease;
  --font-size-multiplier: 1.0;
  overflow-y: auto;
  overflow-x: hidden; /* Prevent horizontal scrolling */
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
  overscroll-behavior-y: contain;
}

/* CSS-based fullscreen mode (no browser API conflicts) */
:deep(body.css-fullscreen) {
  overflow: hidden;
}

/* Prevent horizontal scrolling globally */
:deep(body), :deep(html) {
  overflow-x: hidden !important;
}

:deep(body.css-fullscreen) .ipad-scroll-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 99999;
  margin: 0;
  padding: 0;
}

/* Ensure floating controls are above fullscreen content */
:deep(body.css-fullscreen) .floating-controls {
  z-index: 999999;
}

/* Inverted mode - swap background and text colors */
.ipad-scroll-container.inverted {
  background: #000000 !important;
  color: #ffffff !important;
}

/* Apply black background to body and all parent elements */
.inverted ~ body,
.inverted {
  background: #000000 !important;
}

:deep(body:has(.ipad-scroll-container.inverted)) {
  background: #000000 !important;
  background-color: #000000 !important;
}

:deep(#app:has(.ipad-scroll-container.inverted)) {
  background: #000000 !important;
  background-color: #000000 !important;
}

.ipad-scroll-container.inverted :deep(*) {
  color: #ffffff !important;
  background-color: #000000 !important;
}

.ipad-scroll-container.inverted :deep(html),
.ipad-scroll-container.inverted :deep(body) {
  background: #000000 !important;
  background-color: #000000 !important;
}

/* Script content area - ensure black background */
.ipad-scroll-container.inverted .script-content {
  background: #000000 !important;
  background-color: #000000 !important;
}

/* Block indicators - keep distinctive styling in inverted mode */
.ipad-scroll-container.inverted :deep(.block-header) {
  background-color: #1a237e !important;
  color: #90caf9 !important;
  border-color: #42a5f5 !important;
}

.ipad-scroll-container.inverted :deep(.block-end) {
  background-color: #1a237e !important;
  color: #9fa8da !important;
  border-color: #5c6bc0 !important;
}

.ipad-scroll-container.inverted :deep(.break-indicator) {
  background-color: #1b5e20 !important;
  color: #a5d6a7 !important;
  border-color: #66bb6a !important;
}

.ipad-scroll-container.inverted :deep(.break-indicator.ad-break) {
  background-color: #0d47a1 !important;
  color: #90caf9 !important;
  border-color: #42a5f5 !important;
}

.ipad-scroll-container.inverted :deep(.ad-label) {
  background-color: #1976d2 !important;
  color: #ffffff !important;
}

.ipad-scroll-container.inverted :deep(.segment-title) {
  border-color: #ffffff !important;
}

.ipad-scroll-container.inverted :deep(.segment-end-divider) {
  color: #666 !important;
  border-color: #444 !important;
}

.ipad-scroll-container.inverted :deep(.segment-tease .script-content) {
  color: #aaa !important;
}

.ipad-scroll-container.inverted :deep(.inline-note) {
  color: #aaa !important;
}

/* Images should NOT be inverted - they need to display in original colors */
.ipad-scroll-container.inverted :deep(img) {
  filter: none !important;
  background-color: transparent !important;
}

/* Floating Controls - Vertically Centered */
.floating-controls {
  position: fixed;
  top: 50%;
  left: 16px;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 999999;
  pointer-events: auto; /* Ensure buttons are always clickable */
}

.control-btn {
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(10px);
  border-radius: 50%;
  transition: all 0.2s ease;
}

.inverted .control-btn {
  background: rgba(0, 0, 0, 0.8) !important;
  color: #ffffff !important;
}

.inverted .control-btn svg {
  color: #ffffff !important;
  fill: #ffffff !important;
}

.inverted .control-btn .v-icon {
  color: #ffffff !important;
}

.control-btn:hover {
  transform: scale(1.1);
}

.close-btn {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* Red state for close button warning */
.close-btn.v-btn--variant-elevated {
  transition: background-color 0.2s ease, color 0.2s ease;
}

.invert-btn {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  text-align: center;
}

.loading-text {
  margin-top: 20px;
  font-size: 1.2rem;
  color: #666;
}

.inverted .loading-text {
  color: #ffffff;
}

.error-container h2 {
  margin: 20px 0 10px;
  color: #d32f2f;
}

.inverted .error-container h2 {
  color: #ff6b6b;
}

.error-container p {
  margin-bottom: 20px;
  color: #666;
}

.inverted .error-container p {
  color: #cccccc;
}

.script-content {
  /* Content styling handled by injected styles */
  /* This wrapper just provides a container */
}

/* Ensure smooth touch scrolling with momentum */
.script-content {
  -webkit-overflow-scrolling: touch;
  overflow-y: auto;
  overflow-x: hidden; /* Prevent horizontal scrolling */
  scroll-behavior: smooth;
  overscroll-behavior-y: contain;
  --font-size-multiplier: 1.0;
  margin-left: 10%; /* Prevent overlap with floating control buttons */
  padding: 3%; /* Prevent content clipping */
  position: relative;
  z-index: 1; /* Below floating controls */
  font-size: calc(var(--base-font-size, 19px) * var(--font-size-multiplier, 1.0));
}

/* Smooth scroll for all scrollable elements */
.script-content :deep(*) {
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}

/* Make sure CSS variable cascades to injected HTML */
.script-content :deep(html),
.script-content :deep(body) {
  --font-size-multiplier: inherit;
}

/* Ensure injected body respects font size multiplier */
.script-content :deep(body) {
  font-size: calc(var(--base-font-size, 19px) * var(--font-size-multiplier, 1.0)) !important;
}

/* Text color toggle - yellow mode */
.script-content.text-yellow :deep(*) {
  color: #ffeb3b !important;
}
</style>
