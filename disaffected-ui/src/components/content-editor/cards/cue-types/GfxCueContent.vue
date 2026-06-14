<template>
  <div class="fsq-preview-layout fsq-preview-layout--stacked">
    <!-- Top Row: Preview + Action Buttons side by side (mirrors FSQ) -->
    <div class="fsq-top-row">
      <!-- Preview -->
      <div class="fsq-preview-side">
        <div class="fsq-large-preview">
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
          <!-- Black bar overlay - reactive to box height/opacity sliders -->
          <div class="fsq-preview-black-bar" :style="gfxBlackBarStyle"></div>

          <!-- XPOST content overlay -->
          <div v-if="cueData.gfxType === 'xpost'" class="xpost-preview-overlay">
            <div class="xpost-author-row">
              <v-avatar v-if="xpostData.profilePhoto" size="28" class="mr-2">
                <v-img :src="xpostData.profilePhoto" />
              </v-avatar>
              <div class="xpost-author-info">
                <span class="xpost-display-name">{{ xpostData.name }}</span>
                <span v-if="xpostData.verified" class="xpost-verified">
                  <v-icon size="12" color="blue">mdi-check-decagram</v-icon>
                </span>
                <span class="xpost-handle">@{{ xpostData.username }}</span>
              </div>
            </div>
            <div class="xpost-text">{{ xpostData.text }}</div>
            <div class="xpost-meta-row">
              <span v-if="xpostData.datetime" class="xpost-date">{{ xpostData.datetime }}</span>
            </div>
            <div class="xpost-engagement-row">
              <span v-if="xpostData.views" class="xpost-metric"><v-icon size="12">mdi-eye-outline</v-icon> {{ formatMetric(xpostData.views) }}</span>
              <span v-if="xpostData.likes" class="xpost-metric"><v-icon size="12">mdi-heart-outline</v-icon> {{ formatMetric(xpostData.likes) }}</span>
              <span v-if="xpostData.retweets" class="xpost-metric"><v-icon size="12">mdi-repeat</v-icon> {{ formatMetric(xpostData.retweets) }}</span>
              <span v-if="xpostData.replies" class="xpost-metric"><v-icon size="12">mdi-comment-outline</v-icon> {{ formatMetric(xpostData.replies) }}</span>
              <span v-if="xpostData.bookmarks" class="xpost-metric"><v-icon size="12">mdi-bookmark-outline</v-icon> {{ formatMetric(xpostData.bookmarks) }}</span>
            </div>
          </div>

          <!-- Standard GFX content overlay - bar position+height tracks
               the Box H slider so the text rides inside the visible bar. -->
          <div
            v-else
            class="gfx-preview-overlay"
            :style="gfxOverlayPositionStyle"
          >
            <div
              v-if="cueData.gfxTitle"
              class="gfx-overlay-title"
              :style="{
                textAlign: cueData.titleAlign || 'center',
                fontFamily: fontMap[localGfxFontFamily] || fontMap['sans-serif'],
                fontSize: gfxTitleFontSizeStyle,
                lineHeight: gfxLineHeight,
                marginBottom: `${(localGfxLineSpacing / 100).toFixed(2)}em`
              }"
            >{{ cueData.gfxTitle }}</div>
            <div
              v-if="cueData.body"
              class="gfx-overlay-body"
              :style="{
                textAlign: localGfxAlignment,
                fontFamily: fontMap[localGfxFontFamily] || fontMap['sans-serif'],
                fontSize: gfxBodyFontSizeStyle,
                lineHeight: gfxLineHeight
              }"
            >{{ formatGfxBody(cueData.body) }}</div>
            <ul
              v-if="gfxActiveListItems.length"
              class="gfx-overlay-list"
              :style="{ textAlign: localGfxAlignment, fontFamily: fontMap[localGfxFontFamily] || fontMap['sans-serif'] }"
            >
              <li v-for="(item, i) in gfxActiveListItems" :key="i">{{ item }}</li>
            </ul>
            <div v-if="!cueData.gfxTitle && !cueData.body && !gfxActiveListItems.length" class="gfx-overlay-empty">No content</div>
          </div>
          <!-- PNG Generated indicator -->
          <div v-if="hasGfxAsset" class="fsq-png-indicator">
            <v-icon size="12" color="success">mdi-check-circle</v-icon>
            <span>PNG</span>
          </div>
        </div>
      </div>

      <!-- Action Buttons - discrete icon buttons, prominent and compact -->
      <div v-if="!readonly" class="fsq-controls-side gfx-actions-side">
        <div class="gfx-action-icons">
          <v-btn
            size="large"
            :variant="hasGfxAsset ? 'tonal' : 'elevated'"
            :color="hasGfxAsset ? 'amber-darken-2' : 'success'"
            icon
            @click.stop="$emit('generate-gfx')"
            :loading="generatingGfx"
            class="gfx-action-btn"
          >
            <v-icon size="large">{{ hasGfxAsset ? 'mdi-sync' : 'mdi-creation' }}</v-icon>
            <v-tooltip activator="parent" location="top">{{ hasGfxAsset ? 'Regenerate PNG' : 'Generate PNG' }}</v-tooltip>
          </v-btn>

          <v-btn
            size="large"
            variant="tonal"
            color="deep-purple"
            icon
            :disabled="!hasGfxAsset"
            @click.stop="$emit('download-gfx-png')"
            class="gfx-action-btn"
          >
            <v-icon size="large">mdi-download</v-icon>
            <v-tooltip activator="parent" location="top">{{ hasGfxAsset ? 'Download PNG' : 'No PNG to download yet' }}</v-tooltip>
          </v-btn>

          <v-btn
            size="large"
            variant="tonal"
            color="primary"
            icon
            @click.stop="$emit('edit-gfx', cueData)"
            class="gfx-action-btn"
          >
            <v-icon size="large">mdi-pencil</v-icon>
            <v-tooltip activator="parent" location="top">Edit GFX in modal</v-tooltip>
          </v-btn>
        </div>

        <!-- GFX Generation Status -->
        <div v-if="gfxGenerationStatus" class="fsq-status-chip mt-2">
          <v-chip size="small" :color="gfxStatusChipColor" variant="tonal">
            <v-icon size="x-small" start :class="{ 'mdi-spin': gfxGenerationStatus === 'generating' }">{{ gfxStatusChipIcon }}</v-icon>
            {{ gfxStatusText }}
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
      <!-- Body Font Size Slider -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">Body Size</span>
        <v-slider
          v-model="localGfxFontSize"
          :min="10"
          :max="60"
          :step="1"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitGfxParamChange('fontSize', $event + 'px')"
        />
        <span class="fsq-slider-value">{{ localGfxFontSize }}px</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-gfx', { param: 'fontSize', value: localGfxFontSize + 'px' })">
          Apply All GFX
          <v-tooltip activator="parent" location="top">Set this body size on every GFX in the episode</v-tooltip>
        </v-btn>
      </div>

      <!-- Title Font Size Slider -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">Title Size</span>
        <v-slider
          v-model="localGfxTitleFontSize"
          :min="10"
          :max="80"
          :step="1"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitGfxParamChange('titleFontSize', $event + 'px')"
        />
        <span class="fsq-slider-value">{{ localGfxTitleFontSize }}px</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-gfx', { param: 'titleFontSize', value: localGfxTitleFontSize + 'px' })">
          Apply All GFX
          <v-tooltip activator="parent" location="top">Set this title size on every GFX in the episode</v-tooltip>
        </v-btn>
      </div>

      <!-- Line Spacing Slider -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">Spacing</span>
        <v-slider
          v-model="localGfxLineSpacing"
          :min="10"
          :max="60"
          :step="5"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitGfxParamChange('lineSpacing', $event)"
        />
        <span class="fsq-slider-value">{{ localGfxLineSpacing }}%</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-gfx', { param: 'lineSpacing', value: localGfxLineSpacing })">
          Apply All GFX
          <v-tooltip activator="parent" location="top">Set this line spacing on every GFX in the episode</v-tooltip>
        </v-btn>
      </div>

      <!-- Box Height Slider -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">Box H</span>
        <v-slider
          v-model="localGfxBoxHeight"
          :min="50"
          :max="100"
          :step="5"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitGfxParamChange('boxHeight', $event)"
        />
        <span class="fsq-slider-value">{{ localGfxBoxHeight }}%</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-gfx', { param: 'boxHeight', value: localGfxBoxHeight })">
          Apply All GFX
          <v-tooltip activator="parent" location="top">Set this box height on every GFX in the episode</v-tooltip>
        </v-btn>
      </div>

      <!-- Box Opacity Slider -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">Box Op</span>
        <v-slider
          v-model="localGfxBoxOpacity"
          :min="50"
          :max="100"
          :step="5"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitGfxParamChange('boxOpacity', $event)"
        />
        <span class="fsq-slider-value">{{ localGfxBoxOpacity }}%</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-gfx', { param: 'boxOpacity', value: localGfxBoxOpacity })">
          Apply All GFX
          <v-tooltip activator="parent" location="top">Set this box opacity on every GFX in the episode</v-tooltip>
        </v-btn>
      </div>

      <!-- Vertical Shift Slider -->
      <div class="fsq-control-row fsq-slider-row fsq-slider-row--full">
        <span class="fsq-control-label">V-Shift</span>
        <v-slider
          v-model="localVerticalOffset"
          :min="-40"
          :max="40"
          :step="5"
          density="compact"
          hide-details
          thumb-label
          class="fsq-control-slider"
          @update:model-value="emitGfxParamChange('verticalOffset', $event)"
        />
        <span class="fsq-slider-value">{{ localVerticalOffset }}%</span>
        <v-btn size="x-small" variant="text" color="deep-purple" class="fsq-apply-all-btn" @click.stop="$emit('apply-all-gfx', { param: 'verticalOffset', value: localVerticalOffset })">
          Apply All GFX
          <v-tooltip activator="parent" location="top">Set this vertical shift on every GFX in the episode</v-tooltip>
        </v-btn>
      </div>

      <!-- Other controls: Font / Align / Render / Revert -->
      <div class="fsq-controls-grid">
        <!-- Font Family -->
        <div class="fsq-grid-item">
          <span class="fsq-grid-label">Font</span>
          <v-select
            v-model="localGfxFontFamily"
            :items="fontFamilyOptions"
            density="compact"
            hide-details
            variant="outlined"
            class="fsq-grid-input"
            @update:model-value="emitGfxParamChange('fontFamily', $event)"
          />
        </div>

        <!-- Alignment -->
        <div class="fsq-grid-item">
          <span class="fsq-grid-label">Align</span>
          <v-btn-toggle
            v-model="localGfxAlignment"
            mandatory
            density="compact"
            color="primary"
            class="fsq-grid-toggle"
            @update:model-value="emitGfxParamChange('textAlign', $event)"
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

        <!-- Render Mode -->
        <div class="fsq-grid-item">
          <span class="fsq-grid-label">Output</span>
          <v-btn-toggle
            v-model="localRenderMode"
            mandatory
            density="compact"
            color="lime"
            class="fsq-grid-toggle"
            @update:model-value="emitGfxParamChange('renderMode', $event)"
          >
            <v-btn value="png" size="x-small">
              <v-icon size="small">mdi-file-image</v-icon>
            </v-btn>
            <v-btn value="video" size="x-small">
              <v-icon size="small">mdi-video</v-icon>
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
            @click.stop="revertGfxChanges"
          >
            <v-icon size="small" start>mdi-undo</v-icon>
            Revert
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Delete button - bottom right -->
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
  hasGfxAsset: {
    type: Boolean,
    default: false
  },
  generatingGfx: {
    type: Boolean,
    default: false
  },
  gfxGenerationStatus: {
    type: String,
    default: null
  },
  fsqBackgroundVideoUrl: {
    type: String,
    default: '/assets/preview-background.mp4'
  },
  xpostData: {
    type: Object,
    default: () => ({})
  },
  gfxActiveListItems: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['edit-gfx', 'delete', 'generate-gfx', 'download-gfx-png', 'update-meta', 'apply-all-gfx']);

// Collapsible adjustments panel
const adjustmentsOpen = ref(false);

// Local state (matches FSQ pattern). All sliders feed a `local*` ref that
// `update-meta` echoes back to the cue's persisted fields via the parent.
// Defaults match the modal and the PIL renderer's bake-in defaults so a
// freshly inserted cue's preview matches the rendered PNG before any user
// adjustment.
const localGfxFontSize = ref(parseInt(props.cueData?.fontSize) || 25);
const localGfxTitleFontSize = ref(parseInt(props.cueData?.titleFontSize) || 36);
const localGfxLineSpacing = ref(parseInt(props.cueData?.lineSpacing) || 30);   // % of font-size
const localGfxBoxHeight = ref(parseInt(props.cueData?.boxHeight) || 80);       // % of canvas
const localGfxBoxOpacity = ref(parseInt(props.cueData?.boxOpacity) || 75);     // 0-100
const localGfxFontFamily = ref(props.cueData?.fontFamily || 'sans-serif');
const localGfxAlignment = ref(props.cueData?.textAlign || 'center');
const localVerticalOffset = ref(parseInt(props.cueData?.verticalOffset) || 0);
const localRenderMode = ref(props.cueData?.renderMode || 'png');

const fontFamilyOptions = ref([
  { title: 'Sans-Serif', value: 'sans-serif' },
  { title: 'Serif', value: 'serif' },
  { title: 'Monospace', value: 'monospace' }
]);

const fontMap = {
  'sans-serif': 'Helvetica, Arial, sans-serif',
  'serif': 'Georgia, "Times New Roman", serif',
  'monospace': '"Courier New", Courier, monospace'
};

// Preview body font sizing — express as a fraction of the preview height so
// it stays roughly proportional to the rendered PNG.
const gfxBodyFontSizeStyle = computed(() => {
  // 25px in modal → ~3.2cqh feels close to PNG render. Scale linearly.
  const scaled = (localGfxFontSize.value / 25) * 3.2;
  return `${scaled.toFixed(2)}cqh`;
});

// Title font sizing — same proportional approach, anchored on 36px → 4cqh
// (the previous fixed default). Slider drives this live.
const gfxTitleFontSizeStyle = computed(() => {
  const scaled = (localGfxTitleFontSize.value / 36) * 4;
  return `${scaled.toFixed(2)}cqh`;
});

// Line-height for both title and body in the preview. Slider stores percent
// of font-size; CSS line-height is 1 + (percent / 100).
const gfxLineHeight = computed(() => {
  return (1 + (localGfxLineSpacing.value || 30) / 100).toFixed(2);
});

// Black bar overlay: positioned so the bar grows symmetrically around the
// canvas vertical center, matching how the PNG renderer places it. Opacity
// slider is 0-100, CSS rgba alpha is 0-1.
const gfxBlackBarStyle = computed(() => {
  const heightPct = Math.max(0, Math.min(100, localGfxBoxHeight.value || 80));
  const topPct = (100 - heightPct) / 2;
  const alpha = Math.max(0, Math.min(100, localGfxBoxOpacity.value || 75)) / 100;
  return {
    top: `${topPct}%`,
    height: `${heightPct}%`,
    background: `rgba(0, 0, 0, ${alpha})`
  };
});

// Text overlay sits inside the visible black bar (same top/height), plus the
// vertical-offset shift.
const gfxOverlayPositionStyle = computed(() => {
  const heightPct = Math.max(0, Math.min(100, localGfxBoxHeight.value || 80));
  const topPct = (100 - heightPct) / 2;
  return {
    top: `${topPct}%`,
    height: `${heightPct}%`,
    transform: `translateY(${localVerticalOffset.value}%)`
  };
});

// computed
const gfxStatusText = computed(() => {
  const map = { queued: 'Queued', generating: 'Generating...', completed: 'Complete', failed: 'Failed' };
  return map[props.gfxGenerationStatus] || '';
});

const gfxStatusChipColor = computed(() => {
  const map = { queued: 'blue-grey', generating: 'amber', completed: 'success', failed: 'error' };
  return map[props.gfxGenerationStatus] || 'grey';
});

const gfxStatusChipIcon = computed(() => {
  const map = { queued: 'mdi-clock-outline', generating: 'mdi-cog', completed: 'mdi-check-circle', failed: 'mdi-alert-circle' };
  return map[props.gfxGenerationStatus] || 'mdi-help-circle';
});

// methods
function formatMetric(n) {
  if (!n) return '0';
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

function formatGfxBody(body) {
  if (!body) return '';
  const unescaped = body.replace(/\\n/g, '\n');
  return unescaped.length > 200 ? unescaped.substring(0, 200) + '...' : unescaped;
}

function emitGfxParamChange(paramName, value) {
  console.log(`GFX param changed: ${paramName} = ${value}`);
  emit('update-meta', {
    assetId: props.cueData.assetId,
    field: paramName,
    value: value
  });
}

function revertGfxChanges() {
  localGfxFontSize.value = parseInt(props.cueData?.fontSize) || 25;
  localGfxTitleFontSize.value = parseInt(props.cueData?.titleFontSize) || 36;
  localGfxLineSpacing.value = parseInt(props.cueData?.lineSpacing) || 30;
  localGfxBoxHeight.value = parseInt(props.cueData?.boxHeight) || 80;
  localGfxBoxOpacity.value = parseInt(props.cueData?.boxOpacity) || 75;
  localGfxFontFamily.value = props.cueData?.fontFamily || 'sans-serif';
  localGfxAlignment.value = props.cueData?.textAlign || 'center';
  localVerticalOffset.value = parseInt(props.cueData?.verticalOffset) || 0;
  localRenderMode.value = props.cueData?.renderMode || 'png';
}

defineExpose({
  localGfxFontSize, localGfxTitleFontSize, localGfxLineSpacing,
  localGfxBoxHeight, localGfxBoxOpacity, localGfxFontFamily,
  localGfxAlignment, localVerticalOffset, localRenderMode
});
</script>

<style scoped>
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
  container-type: size;
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

.fsq-preview-black-bar {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  background: rgba(0, 0, 0, 0.75);
  z-index: 2;
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

/* XPOST Preview Overlay */
.xpost-preview-overlay {
  position: absolute;
  top: 6%;
  left: 0;
  width: 100%;
  height: 88%;
  display: flex;
  flex-direction: column;
  padding: 3% 6%;
  z-index: 3;
  box-sizing: border-box;
  overflow: hidden;
  color: white;
}

.xpost-author-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.xpost-author-info {
  display: flex;
  align-items: baseline;
  gap: 4px;
  flex-wrap: wrap;
}

.xpost-display-name {
  font-weight: bold;
  font-size: 0.75rem;
}

.xpost-handle {
  font-size: 0.65rem;
  opacity: 0.7;
}

.xpost-text {
  font-size: 0.7rem;
  line-height: 1.3;
  white-space: pre-wrap;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  margin-bottom: 4px;
}

.xpost-meta-row {
  font-size: 0.55rem;
  opacity: 0.6;
  margin-bottom: 2px;
}

.xpost-engagement-row {
  display: flex;
  gap: 8px;
  font-size: 0.6rem;
  opacity: 0.8;
  margin-top: auto;
}

.xpost-metric {
  display: flex;
  align-items: center;
  gap: 2px;
}

/* GFX Preview Overlay */
.gfx-preview-overlay {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4% 8%;
  z-index: 3;
  box-sizing: border-box;
  overflow: hidden;
  color: white;
  transition: transform 0.15s;
}

.gfx-overlay-title {
  color: white;
  font-weight: bold;
  font-size: 4cqh;
  margin-bottom: 0.4em;
  text-align: center;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
}

.gfx-overlay-body {
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.4;
  white-space: pre-wrap;
  text-align: center;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
}

.gfx-overlay-list {
  list-style: disc;
  padding-left: 1.5em;
  margin: 0;
  color: rgba(255, 255, 255, 0.95);
  font-size: 2.8cqh;
  line-height: 1.5;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
}

.gfx-overlay-list li {
  margin-bottom: 0.2em;
}

.gfx-overlay-empty {
  color: rgba(255, 255, 255, 0.3);
  font-style: italic;
  font-size: 3cqh;
  text-align: center;
  margin-top: 2em;
}

/* Controls side */
.fsq-controls-side {
  flex: 0 0 35%;
  display: flex;
  flex-direction: column;
}

/* GFX action icons — discrete, prominent, side-by-side. Replaces the
   previous stack of full-width text buttons. */
.gfx-actions-side {
  justify-content: flex-start;
  align-items: stretch;
}

.gfx-action-icons {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: flex-start;
  padding: 4px 0;
  flex-wrap: wrap;
}

.gfx-action-btn {
  width: 48px;
  height: 48px;
  flex: 0 0 auto;
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
  grid-template-columns: repeat(4, 1fr);
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
