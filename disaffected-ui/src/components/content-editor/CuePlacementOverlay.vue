<template>
  <!-- Phase 1: Between/Paragraph Selection -->
  <div v-if="show && phase === 1" class="cue-placement-overlay phase-1">
    <!-- Between-paragraph drop zones (with 20px vertical expansion) -->
    <div
      v-for="(zone, index) in betweenZones"
      :key="`between-${index}`"
      class="drop-zone between-zone"
      :class="{ 'highlighted': hoveredZone?.type === 'between' && hoveredZone?.index === index }"
      :style="zone.style"
      @mouseenter="hoveredZone = { type: 'between', index }"
      @click="handleBetweenZoneClick(index)"
    >
      <div class="zone-label">INSERT {{ cueType }} HERE</div>
    </div>

    <!-- Paragraph drop zones (full paragraph highlighting) -->
    <div
      v-for="(zone, index) in paragraphZones"
      :key="`paragraph-${index}`"
      class="drop-zone paragraph-zone"
      :class="{ 'highlighted': hoveredZone?.type === 'paragraph' && hoveredZone?.index === index }"
      :style="zone.style"
      @mouseenter="hoveredZone = { type: 'paragraph', index }"
      @click="handleParagraphZoneClick(index, zone)"
    >
      <div class="zone-label">INSERT {{ cueType }} IN PARAGRAPH</div>
    </div>

    <!-- Instructions -->
    <div class="instructions-overlay">
      <div class="instruction-box">
        <div class="instruction-text">
          <v-icon color="white" class="mr-2">mdi-information</v-icon>
          <span v-if="!hoveredZone">POSITION {{ cueType }} CUE - Click between paragraphs or within paragraph</span>
          <span v-else-if="hoveredZone.type === 'between'">Click to insert {{ cueType }} cue between paragraphs</span>
          <span v-else>Click to choose character position within paragraph</span>
        </div>
        <div class="cancel-hint">Press ESC to cancel</div>
      </div>
    </div>
  </div>

  <!-- Phase 2: Character-Level Cursor -->
  <div v-else-if="show && phase === 2" class="cue-placement-overlay phase-2">
    <!-- Paragraph content overlay with character cursor -->
    <div
      class="paragraph-content-overlay"
      :style="paragraphOverlayStyle"
      @mousemove="handleCharacterMouseMove"
      @click="handleCharacterClick"
    >
      <!-- Orange character cursor -->
      <div
        v-if="characterCursor.show"
        class="character-cursor"
        :style="characterCursor.style"
      ></div>

      <!-- Paragraph text with pushed character -->
      <div class="paragraph-preview" :style="paragraphTextStyle">
        {{ beforeCursorText }}<span class="pushed-char">{{ pushedChar }}</span>{{ afterCursorText }}
      </div>
    </div>

    <!-- Instructions -->
    <div class="instructions-overlay">
      <div class="instruction-box">
        <div class="instruction-text">
          <v-icon color="white" class="mr-2">mdi-cursor-text</v-icon>
          <span>Position cursor where {{ cueType }} cue should be inserted - Click to confirm</span>
        </div>
        <div class="cancel-hint">Press ESC to cancel</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap.js';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  cueType: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['place-cue', 'cancel', 'update:show']);

// data
const phase = ref(1); // 1 = between/paragraph selection, 2 = character-level cursor
const betweenZones = ref([]);
const paragraphZones = ref([]);
const hoveredZone = ref(null);
const selectedZoneIndex = ref(0); // Always have a zone selected (for arrow key navigation)
const selectedParagraph = ref(null); // For phase 2
const characterCursor = ref({
  show: false,
  position: 0,
  style: {}
});
const paragraphOverlayStyle = ref({});
const paragraphTextStyle = ref({});
const paragraphText = ref('');
let resizeObserver = null;
let scrollUpdateInterval = null;
const keyboardHandler = ref(null); // eslint-disable-line no-unused-vars

// computed
const beforeCursorText = computed(() => {
  if (!paragraphText.value) return '';
  return paragraphText.value.substring(0, characterCursor.value.position);
});

const pushedChar = computed(() => {
  if (!paragraphText.value || characterCursor.value.position >= paragraphText.value.length) return '';
  return paragraphText.value.charAt(characterCursor.value.position);
});

const afterCursorText = computed(() => {
  if (!paragraphText.value || characterCursor.value.position >= paragraphText.value.length) {
    return paragraphText.value.substring(characterCursor.value.position);
  }
  return paragraphText.value.substring(characterCursor.value.position + 1);
});

/**
 * Get currently selected zone (for arrow key navigation)
 * Always returns a zone - never null
 */
const currentSelectedZone = computed(() => {
  // Interleave between and paragraph zones
  const allZones = [];
  for (let i = 0; i < Math.max(betweenZones.value.length, paragraphZones.value.length); i++) {
    if (i < betweenZones.value.length) {
      allZones.push({ type: 'between', index: i, data: betweenZones.value[i] });
    }
    if (i < paragraphZones.value.length) {
      allZones.push({ type: 'paragraph', index: i, data: paragraphZones.value[i] });
    }
  }

  if (allZones.length === 0) return null;

  // Clamp index to valid range
  const clampedIndex = Math.max(0, Math.min(selectedZoneIndex.value, allZones.length - 1));
  return allZones[clampedIndex];
});

// watch
watch(() => props.show, (newVal) => {
  console.log('🎨 CuePlacementOverlay: Show changed to', newVal);
  if (newVal) {
    phase.value = 1;
    selectedZoneIndex.value = 0; // Start with first zone selected
    selectedParagraph.value = null;
    characterCursor.value = { show: false, position: 0, style: {} };
    nextTick(() => {
      nextTick(() => {
        calculateZones();
        // Auto-select first zone
        if (currentSelectedZone.value) {
          hoveredZone.value = {
            type: currentSelectedZone.value.type,
            index: currentSelectedZone.value.index
          };
        }
        setupResizeObserver();
        startContinuousUpdate();
      });
    });
  } else {
    cleanup();
  }
});

// lifecycle
onMounted(() => {
  console.log('CuePlacementOverlay: Component mounted');
  document.addEventListener('keydown', handleKeydown);
  window.addEventListener('scroll', handleScroll, true);
});

onBeforeUnmount(() => {
  console.log('CuePlacementOverlay: Component unmounting');
  cleanup();
  document.removeEventListener('keydown', handleKeydown);
  window.removeEventListener('scroll', handleScroll, true);
});

// methods
function calculateZones() {
  betweenZones.value = [];
  paragraphZones.value = [];

  const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
  const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

  // Find all paragraph elements
  const paragraphs = document.querySelectorAll('.speaker-paragraph');
  console.log('🎨 Found', paragraphs.length, 'speaker paragraphs');

  if (paragraphs.length === 0) {
    console.error('🎨 No .speaker-paragraph elements found!');
    return;
  }

  const newBetweenZones = [];
  const newParagraphZones = [];

  paragraphs.forEach((paragraph, index) => {
    const rect = paragraph.getBoundingClientRect();

    // Create between-zone BEFORE this paragraph (expanded 20px vertically)
    newBetweenZones.push({
      paragraphIndex: index,
      style: {
        position: 'absolute',
        top: `${rect.top + scrollTop - 20}px`,
        left: `${rect.left + scrollLeft}px`,
        width: `${rect.width}px`,
        height: '40px', // 20px expansion (10px above + 10px below the gap)
        zIndex: 10000
      }
    });

    // Create paragraph zone (full paragraph coverage)
    newParagraphZones.push({
      element: paragraph,
      paragraphIndex: index,
      style: {
        position: 'absolute',
        top: `${rect.top + scrollTop}px`,
        left: `${rect.left + scrollLeft}px`,
        width: `${rect.width}px`,
        height: `${rect.height}px`,
        zIndex: 10000
      }
    });
  });

  // Add final between-zone after last paragraph
  if (paragraphs.length > 0) {
    const lastParagraph = paragraphs[paragraphs.length - 1];
    const lastRect = lastParagraph.getBoundingClientRect();
    newBetweenZones.push({
      paragraphIndex: paragraphs.length,
      style: {
        position: 'absolute',
        top: `${lastRect.bottom + scrollTop}px`,
        left: `${lastRect.left + scrollLeft}px`,
        width: `${lastRect.width}px`,
        height: '40px',
        zIndex: 10000
      }
    });
  }

  betweenZones.value = newBetweenZones;
  paragraphZones.value = newParagraphZones;

  console.log('🎨 Created', betweenZones.value.length, 'between-zones and', paragraphZones.value.length, 'paragraph zones');
}

function handleBetweenZoneClick(index) {
  console.log('🎯 Between-zone clicked:', index);
  emit('place-cue', {
    type: 'between',
    index: index,
    cueType: props.cueType
  });
  emit('update:show', false);
}

function handleParagraphZoneClick(index, zone) {
  console.log('🎯 Paragraph zone clicked:', index);

  // Enter Phase 2: Character-level cursor
  phase.value = 2;
  selectedParagraph.value = zone;
  hoveredZone.value = null;

  // Get paragraph text from textarea
  const textarea = zone.element.querySelector('textarea');
  if (!textarea) {
    console.error('🎨 No textarea found in paragraph!');
    return;
  }

  paragraphText.value = textarea.value || '';

  // Position overlay over the paragraph
  const rect = zone.element.getBoundingClientRect();
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
  const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

  paragraphOverlayStyle.value = {
    position: 'absolute',
    top: `${rect.top + scrollTop}px`,
    left: `${rect.left + scrollLeft}px`,
    width: `${rect.width}px`,
    height: `${rect.height}px`,
    zIndex: 10001,
    cursor: 'text'
  };

  // Style for paragraph preview text
  const textareaRect = textarea.getBoundingClientRect();
  paragraphTextStyle.value = {
    position: 'absolute',
    top: `${textareaRect.top - rect.top}px`,
    left: `${textareaRect.left - rect.left}px`,
    width: `${textareaRect.width}px`,
    fontFamily: textarea.style.fontFamily || 'monospace',
    fontSize: textarea.style.fontSize || '14px',
    lineHeight: textarea.style.lineHeight || '1.5',
    padding: '8px',
    whiteSpace: 'pre-wrap',
    wordWrap: 'break-word'
  };

  console.log('🎯 Entered Phase 2 - Character-level cursor mode');
}

function handleCharacterMouseMove(event) {
  if (!selectedParagraph.value) return;

  const textarea = selectedParagraph.value.element.querySelector('textarea');
  if (!textarea) return;

  const textareaRect = textarea.getBoundingClientRect();
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

  // Calculate approximate character position based on mouse X position
  const relativeX = event.clientX - textareaRect.left;
  const charWidth = 8.5; // Approximate monospace character width
  const position = Math.max(0, Math.min(Math.floor(relativeX / charWidth), paragraphText.value.length));

  characterCursor.value.position = position;

  // Position cursor
  characterCursor.value = {
    show: true,
    position: position,
    style: {
      position: 'absolute',
      left: `${relativeX}px`,
      top: `${event.clientY - textareaRect.top + scrollTop}px`,
      width: '3px',
      height: '20px',
      backgroundColor: '#ff6600',
      zIndex: 10002
    }
  };
}

function handleCharacterClick() {
  console.log('🎯 Character position clicked:', characterCursor.value.position);

  const paragraphIndex = selectedParagraph.value.paragraphIndex;

  emit('place-cue', {
    type: 'paragraph',
    index: paragraphIndex,
    characterOffset: characterCursor.value.position,
    cueType: props.cueType
  });
  emit('update:show', false);
}

function handleKeydown(event) {
  if (event.key === 'Escape') {
    console.log('🚫 ESC pressed - cancelling drop locator with ABORT flash');

    // Flash red "ABORT" message
    import('@/composables/useScreenFlash').then(({ useScreenFlash }) => {
      const { flashUrgent } = useScreenFlash();
      flashUrgent('ABORT', '#F44336', 500);
    });

    emit('cancel');
    emit('update:show', false);
    return;
  }

  // Arrow keys for zone navigation (Phase 1 only)
  if (phase.value === 1) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      navigateDown();
      return;
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault();
      navigateUp();
      return;
    }

    // Enter or Shift+Enter to confirm selection
    if (event.key === 'Enter') {
      event.preventDefault();
      confirmCurrentZone();
      return;
    }
  }
}

/**
 * Navigate to next zone (down arrow)
 */
function navigateDown() {
  const allZones = getAllZones();
  if (allZones.length === 0) return;

  selectedZoneIndex.value = Math.min(selectedZoneIndex.value + 1, allZones.length - 1);
  hoveredZone.value = currentSelectedZone.value ? {
    type: currentSelectedZone.value.type,
    index: currentSelectedZone.value.index
  } : null;

  // Scroll zone into view if needed
  scrollZoneIntoView(currentSelectedZone.value);
}

/**
 * Navigate to previous zone (up arrow)
 */
function navigateUp() {
  selectedZoneIndex.value = Math.max(selectedZoneIndex.value - 1, 0);
  hoveredZone.value = currentSelectedZone.value ? {
    type: currentSelectedZone.value.type,
    index: currentSelectedZone.value.index
  } : null;

  // Scroll zone into view if needed
  scrollZoneIntoView(currentSelectedZone.value);
}

/**
 * Get all zones in interleaved order
 */
function getAllZones() {
  const allZones = [];
  for (let i = 0; i < Math.max(betweenZones.value.length, paragraphZones.value.length); i++) {
    if (i < betweenZones.value.length) {
      allZones.push({ type: 'between', index: i, data: betweenZones.value[i] });
    }
    if (i < paragraphZones.value.length) {
      allZones.push({ type: 'paragraph', index: i, data: paragraphZones.value[i] });
    }
  }
  return allZones;
}

/**
 * Confirm current zone selection (Enter key)
 */
function confirmCurrentZone() {
  if (!currentSelectedZone.value) return;

  if (currentSelectedZone.value.type === 'between') {
    handleBetweenZoneClick(currentSelectedZone.value.index);
  } else {
    handleParagraphZoneClick(currentSelectedZone.value.index, currentSelectedZone.value.data);
  }
}

/**
 * Scroll zone into view
 */
function scrollZoneIntoView(zone) {
  if (!zone || !zone.data) return;

  // Find the zone element by its position
  const zoneElements = document.querySelectorAll('.drop-zone');
  for (const el of zoneElements) {
    const rect = el.getBoundingClientRect();
    const zoneTop = parseFloat(zone.data.style.top);

    if (Math.abs(rect.top + window.pageYOffset - zoneTop) < 5) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      break;
    }
  }
}

function handleScroll() {
  // Recalculate zones on scroll to keep them positioned correctly
  if (props.show) {
    if (phase.value === 1) {
      calculateZones();
    } else if (phase.value === 2) {
      // Recalculate phase 2 overlay position on scroll
      updatePhase2Position();
    }
  }
}

function updatePhase2Position() {
  if (!selectedParagraph.value) return;

  const paragraph = selectedParagraph.value.element;
  const textarea = paragraph.querySelector('textarea');
  if (!textarea) return;

  const rect = paragraph.getBoundingClientRect();
  const textareaRect = textarea.getBoundingClientRect();
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
  const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

  // Update paragraph overlay position
  paragraphOverlayStyle.value = {
    position: 'absolute',
    top: `${rect.top + scrollTop}px`,
    left: `${rect.left + scrollLeft}px`,
    width: `${rect.width}px`,
    height: `${rect.height}px`,
    zIndex: 10001,
    cursor: 'text'
  };

  // Update paragraph text style
  paragraphTextStyle.value = {
    position: 'absolute',
    top: `${textareaRect.top - rect.top}px`,
    left: `${textareaRect.left - rect.left}px`,
    width: `${textareaRect.width}px`,
    fontFamily: textarea.style.fontFamily || 'monospace',
    fontSize: textarea.style.fontSize || '14px',
    lineHeight: textarea.style.lineHeight || '1.5',
    padding: '8px',
    whiteSpace: 'pre-wrap',
    wordWrap: 'break-word'
  };
}

function setupResizeObserver() {
  if (resizeObserver) return;

  resizeObserver = new ResizeObserver(() => {
    if (props.show && phase.value === 1) {
      calculateZones();
    }
  });

  const container = document.querySelector('.script-mode-container');
  if (container) {
    resizeObserver.observe(container);
  }
}

function startContinuousUpdate() {
  // Update zones continuously while overlay is active (every 100ms)
  // This ensures zones stay aligned even during rapid scrolling
  scrollUpdateInterval = setInterval(() => {
    if (props.show && phase.value === 1) {
      calculateZones();
    } else if (props.show && phase.value === 2) {
      updatePhase2Position();
    }
  }, 100);
}

function cleanup() {
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  if (scrollUpdateInterval) {
    clearInterval(scrollUpdateInterval);
    scrollUpdateInterval = null;
  }
  phase.value = 1;
  hoveredZone.value = null;
  selectedParagraph.value = null;
  characterCursor.value = { show: false, position: 0, style: {} };
}

// Theme color helpers
function getDragLightColor() { // eslint-disable-line no-unused-vars
  return resolveVuetifyColor(getColorValue('drag-light'));
}
function getDroplineColor() { // eslint-disable-line no-unused-vars
  return resolveVuetifyColor(getColorValue('dropline'));
}
function getDroplineBackground() { // eslint-disable-line no-unused-vars
  return resolveVuetifyColor(getColorValue('dropline-bg'));
}
</script>

<style scoped>
/* Phase 1: Between/Paragraph Selection */
.cue-placement-overlay.phase-1 {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 9999;
}

.drop-zone {
  pointer-events: all;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: 2px dashed transparent;
}

.drop-zone .zone-label {
  opacity: 0;
  font-size: 11px;
  font-weight: bold;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  pointer-events: none;
  transition: opacity 0.15s ease;
  white-space: nowrap;
}

/* Between-paragraph zones - uses draglight for shadow, dragline for border */
.between-zone {
  background-color: transparent;
  border: 2px dotted #C8E6C9; /* dropline color */
  margin: 1em 0; /* Push content away visually */
}

.between-zone.highlighted {
  background-color: #B2EBF2; /* draglight color */
  border: 3px dotted #4CAF50; /* dragline color - solid green */
  border-style: dotted;
  box-shadow: 0 4px 12px rgba(178, 235, 242, 0.6); /* draglight shadow */
  margin: 1em 0; /* Maintain spacing when highlighted */
}

.between-zone.highlighted .zone-label {
  opacity: 1;
  color: #1B5E20;
  background: rgba(255, 255, 255, 0.95);
  font-weight: bold;
}

/* Paragraph zones - uses draglight for shadow, dragline for border */
.paragraph-zone {
  background-color: transparent;
  border: 2px dotted #C8E6C9; /* dropline color */
  margin: 1em 0; /* Push content away visually */
}

.paragraph-zone.highlighted {
  background-color: rgba(178, 235, 242, 0.4); /* draglight color with transparency */
  border: 3px dotted #4CAF50; /* dragline color - solid green */
  border-style: dotted;
  box-shadow: 0 4px 12px rgba(178, 235, 242, 0.6); /* draglight shadow */
  margin: 1em 0; /* Maintain spacing when highlighted */
}

.paragraph-zone.highlighted .zone-label {
  opacity: 1;
  color: #1B5E20;
  background: rgba(255, 255, 255, 0.95);
  font-weight: bold;
}

/* Phase 2: Character-Level Cursor */
.cue-placement-overlay.phase-2 {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 9999;
}

.paragraph-content-overlay {
  pointer-events: all;
  background-color: rgba(255, 255, 255, 0.95);
  border: 3px solid #ff6600;
  box-shadow: 0 0 30px rgba(255, 102, 0, 0.5);
  border-radius: 4px;
  overflow: hidden;
}

.paragraph-preview {
  color: #333;
  user-select: none;
  pointer-events: none;
}

.pushed-char {
  background-color: rgba(255, 102, 0, 0.3);
  padding: 0 2px;
  margin: 0 2px;
  display: inline-block;
}

.character-cursor {
  pointer-events: none;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0.3; }
}

/* Instructions Overlay */
.instructions-overlay {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10003;
  pointer-events: none;
}

.instruction-box {
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
  text-align: center;
}

.instruction-text {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.cancel-hint {
  font-size: 11px;
  color: #ffcc00;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>
