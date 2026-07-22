<template>
  <div class="fsq-preview-layout fsq-preview-layout--stacked">
    <!-- Top Row: Preview + Action Buttons side by side -->
    <div class="fsq-top-row">
      <!-- Preview -->
      <div class="fsq-preview-side">
        <div
          class="fsq-large-preview"
          :class="{ 'clickable': cueData.mediaUrl }"
          @click.stop="cueData.mediaUrl && $emit('open-fsq-preview')"
        >
          <!-- Video Background -->
          <video
            class="fsq-preview-video-bg"
            autoplay
            loop
            muted
            playsinline
          >
            <source :src="fsqBackgroundVideoUrl" type="video/mp4">
          </video>
          <!-- When a CURRENT generated PNG exists, key the ACTUAL image over the
               background video — the preview IS the render, pixel for pixel
               (the PNG carries the black bar + text on alpha, exactly as it
               keys downstream). The HTML recreation below is only the live
               WYSIWYG fallback while params are dirty or no PNG exists yet. -->
          <img
            v-if="showRenderedPng"
            :src="cueData.mediaUrl"
            class="fsq-preview-rendered-png"
            alt="FSQ render"
            draggable="false"
          />
          <template v-else>
            <!-- Black bar overlay -->
            <div class="fsq-preview-black-bar" :style="fsqBlackBarStyle"></div>
            <!-- Quote text overlay (live preview) -->
            <div class="fsq-preview-quote-overlay" :style="fsqPreviewStyle">
              <div class="fsq-preview-quote-wrapper">
                <div class="fsq-preview-quote-text" :style="fsqPreviewTextStyle">{{ cueData.quote }}</div>
              </div>
              <div v-if="cueData.attribution" class="fsq-preview-attribution" :style="fsqPreviewAttributionStyle">— {{ cueData.attribution }}</div>
            </div>
          </template>
          <!-- Click indicator if PNG exists -->
          <div v-if="cueData.mediaUrl" class="fsq-preview-click-hint">
            <v-icon size="20" color="white">mdi-magnify-plus</v-icon>
            <span>View Full</span>
          </div>
          <!-- PNG Generated indicator -->
          <div v-if="cueData.mediaUrl" class="fsq-png-indicator">
            <v-icon size="12" color="success">mdi-check-circle</v-icon>
            <span>PNG</span>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="fsq-controls-side">
        <v-btn
          block
          size="small"
          :variant="'elevated'"
          :color="!fsqDirty && cueData.mediaUrl ? 'success' : 'primary'"
          @click.stop="$emit('generate-png')"
          :loading="generatingPNG"
          :disabled="!fsqDirty && cueData.mediaUrl"
          class="mb-2"
        >
          <v-icon size="small" start>{{ !fsqDirty && cueData.mediaUrl ? 'mdi-check-circle' : (cueData.mediaUrl ? 'mdi-sync' : 'mdi-creation') }}</v-icon>
          {{ !fsqDirty && cueData.mediaUrl ? 'Up to Date' : (cueData.mediaUrl ? 'Regenerate' : 'Generate PNG') }}
        </v-btn>

        <!-- Pop the render up in a modal, layered over the same background
             video the inline preview uses (the existing preview modal). -->
        <v-btn
          v-if="cueData.mediaUrl"
          block
          size="small"
          variant="text"
          color="primary"
          class="mb-2"
          @click.stop="$emit('open-fsq-preview')"
        >
          <v-icon size="small" start>mdi-television-play</v-icon>
          Preview
        </v-btn>

        <v-btn
          v-if="!readonly"
          block
          size="small"
          variant="text"
          color="primary"
          class="mb-2"
          @click.stop="$emit('edit-fsq', cueData)"
        >
          <v-icon size="small" start>mdi-pencil</v-icon>
          Edit FSQ
        </v-btn>

        <!-- View / Download show only when a CURRENT (not-dirty) PNG exists.
             Any edit flips fsqDirty true → these hide until a new PNG renders. -->
        <v-btn
          v-if="cueData.mediaUrl && !fsqDirty"
          block
          size="small"
          variant="text"
          color="deep-purple"
          class="mb-2"
          @click.stop="$emit('view-png')"
        >
          <v-icon size="small" start>mdi-eye</v-icon>
          View PNG
        </v-btn>

        <v-btn
          v-if="cueData.mediaUrl && !fsqDirty"
          block
          size="small"
          variant="text"
          color="deep-purple"
          class="mb-2"
          @click.stop="$emit('download-png')"
        >
          <v-icon size="small" start>mdi-download</v-icon>
          Download PNG
        </v-btn>

        <!-- Status Indicator -->
        <div v-if="fsqGenerationStatus" class="fsq-status-chip mb-2">
          <v-chip size="x-small" :color="fsqStatusChipColor" variant="tonal">
            <v-icon size="x-small" start :class="{ 'mdi-spin': fsqGenerationStatus === 'generating' }">{{ fsqStatusChipIcon }}</v-icon>
            {{ fsqStatusText }}
          </v-chip>
        </div>
      </div>
    </div>

    <!-- Bottom: Collapsible Style Controls -->
    <div class="fsq-adjustments-toggle" @click.stop="adjustmentsOpen = !adjustmentsOpen">
      <v-icon size="small" class="fsq-toggle-icon" :class="{ 'fsq-toggle-icon--open': adjustmentsOpen }">mdi-chevron-right</v-icon>
      <span class="fsq-toggle-label">Adjustments</span>
      <div class="fsq-toggle-line"></div>
    </div>
    <div v-show="adjustmentsOpen" class="fsq-compact-controls fsq-compact-controls--wide" @click.stop>
      <!-- Font Size Slider - full width. Slider operates in REAL canvas
           pixels (60-300px on a 1080px canvas) so the displayed value
           matches the rendered PNG size exactly. The underlying storage
           still uses the legacy 1/4-scale UI value (mapped via a computed
           getter/setter), so existing data and the downstream regenerate
           pipeline keep working without migration. -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">Quote Size</span>
        <v-slider
          v-model="localFontSizePx"
          :min="60"
          :max="300"
          :step="4"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitParamChange('fontSize', localFontSize)"
        />
        <span class="fsq-slider-value">{{ localFontSizePx }}px</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-fsq', { param: 'fontSize', value: localFontSize })">
          Apply All FSQ
          <v-tooltip activator="parent" location="top">Set this font size on every FSQ in the episode</v-tooltip>
        </v-btn>
      </div>
      <!-- Attribution Size Slider - same real-px treatment as Quote Size. -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">Attrib Size</span>
        <v-slider
          v-model="localAttributionSizePx"
          :min="32"
          :max="240"
          :step="4"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitParamChange('attributionSize', localAttributionSize)"
        />
        <span class="fsq-slider-value">{{ localAttributionSizePx }}px</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-fsq', { param: 'attributionSize', value: localAttributionSize })">
          Apply All FSQ
          <v-tooltip activator="parent" location="top">Set this attribution size on every FSQ in the episode</v-tooltip>
        </v-btn>
      </div>
      <!-- Black Box Height Slider - full width -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">Black Box</span>
        <v-slider
          v-model="localBoxHeight"
          :min="0"
          :max="100"
          :step="1"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitParamChange('boxHeight', $event)"
        />
        <span class="fsq-slider-value">{{ localBoxHeight }}%</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-fsq', { param: 'boxHeight', value: localBoxHeight })">
          Apply All FSQ
          <v-tooltip activator="parent" location="top">Set this box height on every FSQ in the episode</v-tooltip>
        </v-btn>
      </div>
      <!-- Opacity Slider -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">Opacity</span>
        <v-slider
          v-model="localBoxOpacity"
          :min="0"
          :max="100"
          :step="1"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitParamChange('boxOpacity', $event)"
        />
        <span class="fsq-slider-value">{{ localBoxOpacity }}%</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-fsq', { param: 'boxOpacity', value: localBoxOpacity })">
          Apply All FSQ
          <v-tooltip activator="parent" location="top">Set this opacity on every FSQ in the episode</v-tooltip>
        </v-btn>
      </div>
      <!-- Spacing Slider -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">Spacing</span>
        <v-slider
          v-model="localLineSpacing"
          :min="1"
          :max="100"
          :step="1"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitParamChange('lineSpacing', $event)"
        />
        <span class="fsq-slider-value">{{ localLineSpacing }}%</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-fsq', { param: 'lineSpacing', value: localLineSpacing })">
          Apply All FSQ
          <v-tooltip activator="parent" location="top">Set this line spacing on every FSQ in the episode</v-tooltip>
        </v-btn>
      </div>

      <!-- Other controls -->
      <div class="fsq-controls-grid">
        <!-- Font Family -->
        <div class="fsq-grid-item">
          <span class="fsq-grid-label">Font</span>
          <v-select
            v-model="localFontFamily"
            :items="fontFamilyOptions"
            density="compact"
            hide-details
            variant="outlined"
            class="fsq-grid-input"
            @update:model-value="emitParamChange('fontFamily', $event)"
          />
        </div>

        <!-- Alignment -->
        <div class="fsq-grid-item">
          <span class="fsq-grid-label">Align</span>
          <v-btn-toggle
            v-model="localAlignment"
            mandatory
            density="compact"
            color="primary"
            class="fsq-grid-toggle"
            @update:model-value="emitParamChange('alignment', $event)"
          >
            <v-btn value="left" size="x-small">
              <v-icon size="small">mdi-format-align-left</v-icon>
            </v-btn>
            <v-btn value="center" size="x-small">
              <v-icon size="small">mdi-format-align-center</v-icon>
            </v-btn>
            <v-btn value="right" size="x-small">
              <v-icon size="small">mdi-format-align-right</v-icon>
            </v-btn>
          </v-btn-toggle>
        </div>

        <!-- Revert -->
        <div class="fsq-grid-item">
          <span class="fsq-grid-label">&nbsp;</span>
          <v-btn
            block
            size="x-small"
            variant="text"
            color="grey"
            @click.stop="revertFsqChanges"
          >
            <v-icon size="small" start>mdi-undo</v-icon>
            Revert
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Delete button - bottom right of FSQ placeholder -->
    <div v-if="!readonly" class="fsq-footer-row">
      <v-spacer></v-spacer>
      <v-btn
        size="small"
        variant="text"
        color="error"
        class="fsq-delete-btn"
        @click.stop="$emit('delete')"
      >
        <v-icon size="small" start>mdi-delete</v-icon>
        Delete
        <v-tooltip activator="parent" location="top">Delete this cue</v-tooltip>
      </v-btn>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { FSQ_DEFAULTS, FSQ_FONT_MAP, FSQ_COLORS, FSQ_PNG_SCALE, fsqPreviewCanvasHeightUnit, computeLineHeight, computeBlackBarStyle } from '../../../../utils/fsqLayout.js';

const props = defineProps({
  cueData: {
    type: Object,
    required: true
  },
  // Read-only render (version preview): hide edit/delete affordances (todo #35).
  readonly: {
    type: Boolean,
    default: false
  },
  fsqDirty: {
    type: Boolean,
    default: true
  },
  generatingPNG: {
    type: Boolean,
    default: false
  },
  fsqGenerationStatus: {
    type: String,
    default: null
  },
  fsqBackgroundVideoUrl: {
    type: String,
    default: '/assets/preview-background.mp4'
  }
});

const emit = defineEmits(['edit-fsq', 'delete', 'generate-png', 'download-png', 'view-png', 'open-fsq-preview', 'update-meta', 'apply-all-fsq']);

// Collapsible adjustments panel
const adjustmentsOpen = ref(false);

// Show the ACTUAL generated PNG keyed over the background whenever it is
// current; fall back to the HTML recreation only while editing (dirty) or
// before the first render exists.
const showRenderedPng = computed(() => !!props.cueData?.mediaUrl && !props.fsqDirty);

// data - FSQ editable parameters (local state)
const localFontFamily = ref(props.cueData?.fontFamily || FSQ_DEFAULTS.fontFamily);
const localFontSize = ref(parseInt(props.cueData?.fontSize) || FSQ_DEFAULTS.fontSize);
const localAttributionSize = ref(parseInt(props.cueData?.attributionSize) || FSQ_DEFAULTS.attributionSize);
const localBoxHeight = ref(parseInt(props.cueData?.boxHeight) || FSQ_DEFAULTS.boxHeight);
const localBoxOpacity = ref(parseInt(props.cueData?.boxOpacity) || FSQ_DEFAULTS.boxOpacity);
const localLineSpacing = ref(parseInt(props.cueData?.lineSpacing) || FSQ_DEFAULTS.lineSpacing);
const localAlignment = ref(props.cueData?.alignment || props.cueData?.style || FSQ_DEFAULTS.alignment);
const fontFamilyOptions = ref([
  { title: 'Sans-Serif', value: 'sans-serif' },
  { title: 'Serif', value: 'serif' }
]);

// Slider bridges: present-and-edit values in REAL canvas-pixel units while
// keeping the underlying refs in legacy 1/4-scale units (the unit downstream
// regenerate code, batch render, and stored cue blocks all expect). The
// slider's displayed/scrolled value matches the rendered PNG exactly, so
// "Quote Size 100px" really means 100 pixels on the 1080-tall canvas.
const localFontSizePx = computed({
  get: () => Math.round(localFontSize.value * FSQ_PNG_SCALE),
  set: (px) => { localFontSize.value = Math.max(1, Math.round(px / FSQ_PNG_SCALE)); }
});
const localAttributionSizePx = computed({
  get: () => Math.round(localAttributionSize.value * FSQ_PNG_SCALE),
  set: (px) => { localAttributionSize.value = Math.max(1, Math.round(px / FSQ_PNG_SCALE)); }
});

// computed
const fsqStatusText = computed(() => {
  const map = { queued: 'Queued', generating: 'Generating...', completed: 'Complete', failed: 'Failed' };
  return map[props.fsqGenerationStatus] || '';
});

const fsqStatusChipColor = computed(() => {
  const map = { queued: 'info', generating: 'warning', completed: 'success', failed: 'error' };
  return map[props.fsqGenerationStatus] || 'grey';
});

const fsqStatusChipIcon = computed(() => {
  const map = { queued: 'mdi-clock-outline', generating: 'mdi-loading', completed: 'mdi-check-circle', failed: 'mdi-alert-circle' };
  return map[props.fsqGenerationStatus] || 'mdi-help-circle';
});

const fsqBlackBarStyle = computed(() => {
  return computeBlackBarStyle(localBoxHeight.value, localBoxOpacity.value);
});

const fsqPreviewStyle = computed(() => {
  const alignment = localAlignment.value || FSQ_DEFAULTS.alignment;
  return {
    textAlign: alignment,
    justifyContent: alignment === 'center' ? 'center' : alignment === 'right' ? 'flex-end' : 'flex-start'
  };
});

const fsqPreviewTextStyle = computed(() => {
  const fontFamily = localFontFamily.value || FSQ_DEFAULTS.fontFamily;
  const fontSize = localFontSize.value || FSQ_DEFAULTS.fontSize;
  const lineSpacing = localLineSpacing.value || FSQ_DEFAULTS.lineSpacing;
  const alignment = localAlignment.value || FSQ_DEFAULTS.alignment;
  // Size as a fraction of the preview's container height — same fraction the
  // PNG renderer occupies of the 1080px canvas. Makes preview WYSIWYG.
  return {
    fontFamily: FSQ_FONT_MAP[fontFamily] || FSQ_FONT_MAP['sans-serif'],
    fontSize: fsqPreviewCanvasHeightUnit(fontSize),
    lineHeight: computeLineHeight(lineSpacing),
    color: FSQ_COLORS.text,
    textAlign: alignment,
    width: '100%'
  };
});

const fsqPreviewAttributionStyle = computed(() => {
  const fontFamily = localFontFamily.value || FSQ_DEFAULTS.fontFamily;
  const alignment = localAlignment.value || FSQ_DEFAULTS.alignment;
  const quoteFontSize = localFontSize.value || FSQ_DEFAULTS.fontSize;
  // If an explicit attribution size is set, use it; otherwise derive from
  // the quote font × attributionRatio (matches renderer's auto-fallback).
  const effectiveSize = localAttributionSize.value
    || quoteFontSize * FSQ_DEFAULTS.attributionRatio;
  return {
    fontFamily: FSQ_FONT_MAP[fontFamily] || FSQ_FONT_MAP['sans-serif'],
    fontSize: fsqPreviewCanvasHeightUnit(effectiveSize),
    color: FSQ_COLORS.attribution,
    marginTop: '8px',
    textAlign: alignment === 'center' ? 'right' : 'left',
    width: '100%'
  };
});

// methods
function emitParamChange(paramName, value) {
  console.log(`FSQ param changed: ${paramName} = ${value}`);
  emit('update-meta', {
    assetId: props.cueData.assetId,
    field: paramName,
    value: value
  });
}

function revertFsqChanges() {
  console.log('Reverting FSQ changes to saved values');
  localFontFamily.value = props.cueData?.fontFamily || 'sans-serif';
  localFontSize.value = parseInt(props.cueData?.fontSize) || 34;
  localAttributionSize.value = parseInt(props.cueData?.attributionSize) || 16;
  localBoxHeight.value = parseInt(props.cueData?.boxHeight) || 75;
  localBoxOpacity.value = parseInt(props.cueData?.boxOpacity) || 75;
  localLineSpacing.value = parseInt(props.cueData?.lineSpacing) || 22;
  localAlignment.value = props.cueData?.alignment || props.cueData?.style || 'center';
}

defineExpose({ localFontSize, localAttributionSize, localBoxHeight, localBoxOpacity, localLineSpacing, localAlignment, localFontFamily });
</script>

<style scoped>
/* FSQ Preview Layout - Stacked: preview+buttons on top, controls below */
.fsq-preview-layout {
  display: flex;
  gap: 12px;
  width: 100%;
  padding: 8px;
}

.fsq-preview-layout--stacked {
  flex-direction: column;
  gap: 8px;
}

.fsq-top-row {
  display: flex;
  gap: 12px;
  width: 100%;
}

.fsq-preview-side {
  flex: 0 0 65%;
}

.fsq-large-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 4px;
  overflow: hidden;
  background: #000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  /* Size containment so descendant `cqh` units resolve against this box's
     height. Together with the fixed 16/9 aspect ratio this makes the
     preview text occupy the same canvas-fraction as the PNG renderer. */
  container-type: size;
}

.fsq-large-preview.clickable {
  cursor: pointer;
}

.fsq-preview-video-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

/* The real render, keyed over the background video. The PNG is a full
   1920x1080 frame with alpha, and the box is fixed 16/9 — so contain fills it
   exactly and the preview is pixel-faithful to what keys downstream. */
.fsq-preview-rendered-png {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  z-index: 3;
  pointer-events: none;
}

.fsq-preview-black-bar {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  background: rgba(0, 0, 0, 0.75);
  z-index: 2;
}

.fsq-preview-quote-overlay {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4.5% 10%;
  z-index: 3;
  box-sizing: border-box;
}

.fsq-preview-quote-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  min-height: 0;
  overflow: hidden;
}

.fsq-preview-quote-text {
  word-wrap: break-word;
  overflow: hidden;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
}

.fsq-preview-attribution {
  text-align: inherit;
  flex-shrink: 0;
  padding-top: 4%;
}

.fsq-preview-click-hint {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  padding: 4px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  z-index: 4;
  font-size: 11px;
  color: white;
}

.fsq-large-preview:hover .fsq-preview-click-hint {
  opacity: 1;
}

.fsq-png-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  padding: 2px 6px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  z-index: 4;
  font-size: 10px;
  color: #4caf50;
}

.fsq-controls-side {
  flex: 0 0 35%;
  display: flex;
  flex-direction: column;
}

.fsq-status-chip {
  display: flex;
  justify-content: center;
}

.fsq-adjustments-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 2px 8px;
  user-select: none;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.fsq-adjustments-toggle:hover {
  opacity: 1;
}

.fsq-toggle-icon {
  transition: transform 0.2s;
}

.fsq-toggle-icon--open {
  transform: rotate(90deg);
}

.fsq-toggle-label {
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.5);
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.fsq-toggle-line {
  flex: 1;
  height: 1px;
  background: rgba(0, 0, 0, 0.12);
}

.fsq-compact-controls {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(0, 0, 0, 0.02);
  padding: 8px;
  border-radius: 4px;
}

.fsq-compact-controls--wide {
  width: 100%;
}

.fsq-control-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fsq-control-label {
  flex: 0 0 50px;
  font-size: 11px;
  color: rgba(0, 0, 0, 0.6);
  text-transform: uppercase;
  font-weight: 500;
}

.fsq-slider-row {
  flex-wrap: nowrap;
}

.fsq-slider-row--full {
  width: 100%;
}

.fsq-control-slider {
  flex: 1;
  min-width: 0;
}

.fsq-slider-value {
  flex: 0 0 40px;
  font-size: 11px;
  color: rgba(0, 0, 0, 0.7);
  text-align: right;
}

.fsq-apply-all-btn {
  flex: 0 0 auto;
  font-size: 10px !important;
  text-transform: none;
  letter-spacing: 0;
  padding: 0 6px !important;
  min-width: 0 !important;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.fsq-apply-all-btn:hover {
  opacity: 1;
}

.fsq-controls-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  width: 100%;
}

.fsq-grid-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.fsq-grid-label {
  font-size: 10px;
  color: rgba(0, 0, 0, 0.6);
  text-transform: uppercase;
  font-weight: 500;
  line-height: 1;
}

.fsq-grid-input {
  width: 100%;
}

.fsq-grid-input :deep(.v-field__input) {
  font-size: 12px;
  min-height: 28px;
  padding: 4px 8px;
}

.fsq-grid-input :deep(.v-field__append-inner) {
  padding-top: 2px;
}

.fsq-grid-toggle {
  width: 100%;
}

.fsq-footer-row {
  display: flex;
  align-items: center;
  padding: 4px 8px 2px;
}

.fsq-delete-btn {
  font-size: 13px !important;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.fsq-delete-btn:hover {
  opacity: 1;
}
</style>
