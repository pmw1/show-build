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

<script>
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap.js';

export default {
  name: 'CuePlacementOverlay',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    cueType: {
      type: String,
      required: true
    }
  },
  emits: ['place-cue', 'cancel'],
  data() {
    return {
      phase: 1, // 1 = between/paragraph selection, 2 = character-level cursor
      betweenZones: [],
      paragraphZones: [],
      hoveredZone: null,
      selectedParagraph: null, // For phase 2
      characterCursor: {
        show: false,
        position: 0,
        style: {}
      },
      paragraphOverlayStyle: {},
      paragraphTextStyle: {},
      paragraphText: '',
      resizeObserver: null,
      scrollUpdateInterval: null
    };
  },
  computed: {
    beforeCursorText() {
      if (!this.paragraphText) return '';
      return this.paragraphText.substring(0, this.characterCursor.position);
    },
    pushedChar() {
      if (!this.paragraphText || this.characterCursor.position >= this.paragraphText.length) return '';
      return this.paragraphText.charAt(this.characterCursor.position);
    },
    afterCursorText() {
      if (!this.paragraphText || this.characterCursor.position >= this.paragraphText.length) {
        return this.paragraphText.substring(this.characterCursor.position);
      }
      return this.paragraphText.substring(this.characterCursor.position + 1);
    }
  },
  watch: {
    show(newVal) {
      console.log('🎨 CuePlacementOverlay: Show changed to', newVal);
      if (newVal) {
        this.phase = 1;
        this.hoveredZone = null;
        this.selectedParagraph = null;
        this.characterCursor = { show: false, position: 0, style: {} };
        this.$nextTick(() => {
          this.$nextTick(() => {
            this.calculateZones();
            this.setupResizeObserver();
            this.startContinuousUpdate();
          });
        });
      } else {
        this.cleanup();
      }
    }
  },
  mounted() {
    console.log('CuePlacementOverlay: Component mounted');
    document.addEventListener('keydown', this.handleKeydown);
    window.addEventListener('scroll', this.handleScroll, true);
  },
  beforeUnmount() {
    console.log('CuePlacementOverlay: Component unmounting');
    this.cleanup();
    document.removeEventListener('keydown', this.handleKeydown);
    window.removeEventListener('scroll', this.handleScroll, true);
  },
  methods: {
    calculateZones() {
      this.betweenZones = [];
      this.paragraphZones = [];

      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

      // Find all paragraph elements
      const paragraphs = document.querySelectorAll('.speaker-paragraph');
      console.log('🎨 Found', paragraphs.length, 'speaker paragraphs');

      if (paragraphs.length === 0) {
        console.error('🎨 No .speaker-paragraph elements found!');
        return;
      }

      paragraphs.forEach((paragraph, index) => {
        const rect = paragraph.getBoundingClientRect();

        // Create between-zone BEFORE this paragraph (expanded 20px vertically)
        this.betweenZones.push({
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
        this.paragraphZones.push({
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
        this.betweenZones.push({
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

      console.log('🎨 Created', this.betweenZones.length, 'between-zones and', this.paragraphZones.length, 'paragraph zones');
    },

    handleBetweenZoneClick(index) {
      console.log('🎯 Between-zone clicked:', index);
      this.$emit('place-cue', {
        type: 'between',
        index: index,
        cueType: this.cueType
      });
      this.$emit('update:show', false);
    },

    handleParagraphZoneClick(index, zone) {
      console.log('🎯 Paragraph zone clicked:', index);

      // Enter Phase 2: Character-level cursor
      this.phase = 2;
      this.selectedParagraph = zone;
      this.hoveredZone = null;

      // Get paragraph text from textarea
      const textarea = zone.element.querySelector('textarea');
      if (!textarea) {
        console.error('🎨 No textarea found in paragraph!');
        return;
      }

      this.paragraphText = textarea.value || '';

      // Position overlay over the paragraph
      const rect = zone.element.getBoundingClientRect();
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

      this.paragraphOverlayStyle = {
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
      this.paragraphTextStyle = {
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
    },

    handleCharacterMouseMove(event) {
      if (!this.selectedParagraph) return;

      const textarea = this.selectedParagraph.element.querySelector('textarea');
      if (!textarea) return;

      const textareaRect = textarea.getBoundingClientRect();
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

      // Calculate approximate character position based on mouse X position
      const relativeX = event.clientX - textareaRect.left;
      const charWidth = 8.5; // Approximate monospace character width
      const position = Math.max(0, Math.min(Math.floor(relativeX / charWidth), this.paragraphText.length));

      this.characterCursor.position = position;

      // Position cursor
      this.characterCursor = {
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
    },

    handleCharacterClick() {
      console.log('🎯 Character position clicked:', this.characterCursor.position);

      const paragraphIndex = this.selectedParagraph.paragraphIndex;

      this.$emit('place-cue', {
        type: 'paragraph',
        index: paragraphIndex,
        characterOffset: this.characterCursor.position,
        cueType: this.cueType
      });
      this.$emit('update:show', false);
    },

    handleKeydown(event) {
      if (event.key === 'Escape') {
        console.log('🚫 ESC pressed - cancelling drop locator');
        this.$emit('cancel');
        this.$emit('update:show', false);
      }
    },

    handleScroll() {
      // Recalculate zones on scroll to keep them positioned correctly
      if (this.show) {
        if (this.phase === 1) {
          this.calculateZones();
        } else if (this.phase === 2) {
          // Recalculate phase 2 overlay position on scroll
          this.updatePhase2Position();
        }
      }
    },

    updatePhase2Position() {
      if (!this.selectedParagraph) return;

      const paragraph = this.selectedParagraph.element;
      const textarea = paragraph.querySelector('textarea');
      if (!textarea) return;

      const rect = paragraph.getBoundingClientRect();
      const textareaRect = textarea.getBoundingClientRect();
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

      // Update paragraph overlay position
      this.paragraphOverlayStyle = {
        position: 'absolute',
        top: `${rect.top + scrollTop}px`,
        left: `${rect.left + scrollLeft}px`,
        width: `${rect.width}px`,
        height: `${rect.height}px`,
        zIndex: 10001,
        cursor: 'text'
      };

      // Update paragraph text style
      this.paragraphTextStyle = {
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
    },

    setupResizeObserver() {
      if (this.resizeObserver) return;

      this.resizeObserver = new ResizeObserver(() => {
        if (this.show && this.phase === 1) {
          this.calculateZones();
        }
      });

      const container = document.querySelector('.script-mode-container');
      if (container) {
        this.resizeObserver.observe(container);
      }
    },

    startContinuousUpdate() {
      // Update zones continuously while overlay is active (every 100ms)
      // This ensures zones stay aligned even during rapid scrolling
      this.scrollUpdateInterval = setInterval(() => {
        if (this.show && this.phase === 1) {
          this.calculateZones();
        } else if (this.show && this.phase === 2) {
          this.updatePhase2Position();
        }
      }, 100);
    },

    cleanup() {
      if (this.resizeObserver) {
        this.resizeObserver.disconnect();
        this.resizeObserver = null;
      }
      if (this.scrollUpdateInterval) {
        clearInterval(this.scrollUpdateInterval);
        this.scrollUpdateInterval = null;
      }
      this.phase = 1;
      this.hoveredZone = null;
      this.selectedParagraph = null;
      this.characterCursor = { show: false, position: 0, style: {} };
    },

    // Theme color helpers
    getDragLightColor() {
      return resolveVuetifyColor(getColorValue('drag-light'));
    },
    getDroplineColor() {
      return resolveVuetifyColor(getColorValue('dropline'));
    },
    getDroplineBackground() {
      return resolveVuetifyColor(getColorValue('dropline-bg'));
    }
  }
};
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

/* Between-paragraph zones */
.between-zone {
  background-color: rgba(33, 150, 243, 0.05);
  border-color: rgba(33, 150, 243, 0.2);
}

.between-zone.highlighted {
  background-color: rgba(33, 150, 243, 0.25);
  border-color: rgba(33, 150, 243, 0.8);
  border-width: 3px;
  border-style: solid;
  box-shadow: 0 0 20px rgba(33, 150, 243, 0.4);
}

.between-zone.highlighted .zone-label {
  opacity: 1;
  color: #2196f3;
  background: rgba(255, 255, 255, 0.95);
}

/* Paragraph zones */
.paragraph-zone {
  background-color: rgba(76, 175, 80, 0.05);
  border-color: rgba(76, 175, 80, 0.2);
}

.paragraph-zone.highlighted {
  background-color: rgba(76, 175, 80, 0.25);
  border-color: rgba(76, 175, 80, 0.8);
  border-width: 3px;
  border-style: solid;
  box-shadow: 0 0 20px rgba(76, 175, 80, 0.4);
}

.paragraph-zone.highlighted .zone-label {
  opacity: 1;
  color: #4caf50;
  background: rgba(255, 255, 255, 0.95);
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
