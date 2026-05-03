<template>
  <div class="sot-container" :class="{ 'vo-container': isVO }">
    <!-- Inline Video Player (discreet, toggleable) -->
    <div v-if="showInlinePlayer && sotVideoUrl" class="sot-inline-player-container">
      <div class="sot-inline-player-header">
        <span class="sot-inline-player-title">{{ isVO ? 'B-Roll Preview' : 'Video Preview' }}</span>
        <v-btn
          icon
          size="x-small"
          variant="text"
          color="grey-darken-1"
          @click.stop="showInlinePlayer = false"
        >
          <v-icon size="small">mdi-close</v-icon>
        </v-btn>
      </div>
      <video
        ref="inlineVideoPlayerRef"
        :src="sotVideoUrl"
        controls
        class="sot-inline-video"
        @loadedmetadata="onVideoLoaded"
      ></video>
    </div>

    <!-- Thumbnail + Info Layout (when completed, has thumbnail, or has any display data) -->
    <div v-if="sotThumbnailUrl || isJobCompleted || displayDuration || displayVideoPath" class="sot-completed-layout">
      <!-- Left: Thumbnail with navigation -->
      <div class="sot-thumbnail-wrapper">
        <div class="sot-thumbnail-section">
          <img
            v-if="currentSotThumbnailUrl"
            :src="currentSotThumbnailUrl"
            class="sot-thumbnail-img sot-thumbnail-clickable"
            @click="$emit('open-sot-preview')"
            @error="handleSotThumbnailError"
          />
          <div v-else class="sot-thumbnail-placeholder">
            <v-icon size="48" color="grey-darken-1">mdi-video-outline</v-icon>
            <span class="sot-placeholder-text">No Thumbnail</span>
          </div>
          <!-- Processing overlay with spinner -->
          <div v-if="jobStatus && jobStatus.status === 'processing'" class="sot-processing-overlay">
            <v-progress-circular indeterminate size="36" width="3" color="white"></v-progress-circular>
            <span class="sot-processing-overlay-text">{{ jobStatus.current_phase || 'Processing...' }}</span>
          </div>
          <!-- Play overlay icon -->
          <div v-if="currentSotThumbnailUrl && !(jobStatus && jobStatus.status === 'processing')" class="sot-play-overlay" @click.stop="$emit('open-sot-preview')">
            <v-icon size="48" color="white">mdi-play-circle</v-icon>
          </div>
          <!-- VO Badge (VO only) -->
          <div v-if="isVO" class="vo-badge">
            <v-icon size="14" color="white">mdi-microphone-off</v-icon>
            <span>B-ROLL</span>
          </div>
          <!-- Completion badge -->
          <div v-if="jobStatus && jobStatus.status === 'completed'" class="sot-complete-badge" :style="isVO ? { bottom: '35px' } : {}">
            <v-icon size="16" color="white">mdi-check</v-icon>
            <span>Complete</span>
          </div>
        </div>
        <!-- Thumbnail Navigation Buttons -->
        <div v-if="sotThumbnailOptions.length > 1" class="sot-thumbnail-nav">
          <v-btn
            size="x-small"
            variant="outlined"
            color="primary"
            :disabled="currentThumbnailIndex === 0"
            @click.stop="prevThumbnail"
            class="sot-nav-btn"
          >
            <v-icon size="small">mdi-chevron-left</v-icon>
            Back
          </v-btn>
          <span class="sot-thumbnail-counter">{{ currentThumbnailIndex + 1 }} / {{ sotThumbnailOptions.length }}</span>
          <v-btn
            size="x-small"
            variant="outlined"
            color="primary"
            :disabled="currentThumbnailIndex >= sotThumbnailOptions.length - 1"
            @click.stop="nextThumbnail"
            class="sot-nav-btn"
          >
            Next
            <v-icon size="small">mdi-chevron-right</v-icon>
          </v-btn>
        </div>
      </div>

      <!-- Right: Info -->
      <div class="sot-info-section">
        <!-- Duration -->
        <div v-if="displayDuration" class="sot-info-row">
          <v-icon size="small" color="primary">mdi-timer-outline</v-icon>
          <span class="sot-info-label">Duration:</span>
          <span class="sot-info-value">{{ displayDuration }}</span>
        </div>

        <!-- Media URL -->
        <div v-if="displayVideoPath" class="sot-info-row">
          <v-icon size="small" color="primary">mdi-video</v-icon>
          <span class="sot-info-label">Video:</span>
          <span class="sot-info-value sot-media-path">{{ formatMediaPath(displayVideoPath) }}</span>
        </div>

        <!-- Processing Status -->
        <div v-if="displayProcessingStatus" class="sot-info-row">
          <v-icon size="small" :color="displayProcessingStatus.startsWith('FAILED') ? 'error' : isJobCompleted ? 'success' : 'info'">{{ displayProcessingStatus.startsWith('FAILED') ? 'mdi-alert-circle' : isJobCompleted ? 'mdi-check-circle' : 'mdi-progress-clock' }}</v-icon>
          <span class="sot-info-label" style="font-weight: 700;">Status:</span>
          <span class="sot-info-value" :style="{ color: displayProcessingStatus.startsWith('FAILED') ? '#D32F2F' : displayProcessingStatus === 'Completed' ? '#2E7D32' : '#1565C0' }">{{ displayProcessingStatus }}</span>
        </div>

        <!-- SOT-only: Transcription Preview -->
        <div v-if="!isVO && sotTranscription" class="sot-transcription-preview">
          <v-icon size="small" color="primary">mdi-text</v-icon>
          <span class="sot-transcription-text">{{ truncateTranscription(sotTranscription) }}</span>
          <v-tooltip activator="parent" location="top" max-width="400">
            <span style="white-space: pre-wrap;">{{ sotTranscription }}</span>
          </v-tooltip>
          <v-btn
            icon
            size="x-small"
            variant="text"
            color="primary"
            class="sot-transcription-copy-btn"
            :title="transcriptionCopied ? 'Copied!' : 'Copy full transcript'"
            @click.stop="copyTranscription"
          >
            <v-icon size="small">{{ transcriptionCopied ? 'mdi-check' : 'mdi-content-copy' }}</v-icon>
          </v-btn>
        </div>

        <!-- SOT-only: Enhanced Video Specs -->
        <div v-if="!isVO && jobStatus?.video_specs" class="sot-info-row">
          <v-icon size="small" color="secondary">mdi-cog</v-icon>
          <span class="sot-info-label">Specs:</span>
          <span class="sot-info-value sot-tech-specs">
            {{ jobStatus.video_specs.resolution }}
            <span v-if="jobStatus.video_specs.codec !== 'unknown' && jobStatus.video_specs.codec !== 'processing'"> &bull; {{ jobStatus.video_specs.codec }}</span>
            <span v-if="jobStatus.video_specs.file_size_mb"> &bull; {{ jobStatus.video_specs.file_size_mb }}MB</span>
          </span>
        </div>

        <!-- SOT-only: Audio Info -->
        <div v-if="!isVO && jobStatus?.audio_analysis" class="sot-info-row">
          <v-icon size="small" color="secondary">mdi-volume-high</v-icon>
          <span class="sot-info-label">Audio:</span>
          <span class="sot-info-value">{{ jobStatus.audio_analysis.channels }}</span>
        </div>

        <!-- SOT-only: Warnings Badge -->
        <div v-if="!isVO && jobStatus?.warnings?.length" class="sot-warnings-row">
          <v-chip
            v-for="(warning, idx) in jobStatus.warnings.slice(0, 2)"
            :key="idx"
            size="x-small"
            :color="warning.includes('low_sharpness') ? 'error' : 'warning'"
            variant="tonal"
            class="mr-1"
          >
            <v-icon size="x-small" start>{{ warning.includes('sharpness') ? 'mdi-blur' : 'mdi-alert' }}</v-icon>
            {{ formatWarningLabel(warning) }}
          </v-chip>
        </div>

        <!-- SOT-only: Thumbnail Sharpness Indicator -->
        <div v-if="!isVO && currentThumbnailSharpness" class="sot-info-row sot-sharpness-row">
          <v-icon size="small" :color="sharpnessColor">mdi-image-filter-hdr</v-icon>
          <span class="sot-info-label">Sharpness:</span>
          <span class="sot-info-value" :style="{ color: sharpnessColor }">{{ currentThumbnailSharpness.toFixed(0) }}</span>
          <v-tooltip activator="parent" location="top">
            Thumbnail sharpness score (higher = sharper). Below 100 may indicate blur.
          </v-tooltip>
        </div>

        <!-- VO-only: Type indicator -->
        <div v-if="isVO" class="sot-info-row vo-notice">
          <v-icon size="small" color="grey">mdi-microphone-off</v-icon>
          <span class="sot-info-label">Type:</span>
          <span class="sot-info-value">Voice Over (B-Roll)</span>
        </div>
      </div>

      <!-- SOT-only: Outcue Display - Full Width at Bottom -->
      <div v-if="!isVO && sotOutcue" class="sot-outcue-banner">
        <span class="sot-outcue-label">OUTCUE:</span>
        <span class="sot-outcue-text">{{ sotOutcue }}</span>
      </div>
    </div>

    <!-- Processing In Progress (no thumbnail yet) -->
    <div v-else-if="jobStatus && jobStatus.status === 'processing'" class="sot-processing-layout">
      <div class="sot-processing-placeholder">
        <div class="sot-processing-overlay" style="position: relative; border-radius: 8px;">
          <v-progress-circular indeterminate size="40" width="3" color="white"></v-progress-circular>
          <span class="sot-processing-overlay-text">{{ jobStatus.current_phase || 'Processing...' }}</span>
        </div>
      </div>
    </div>

    <!-- No Job Status Yet -->
    <div v-else class="sot-pending-layout">
      <v-icon size="48" color="grey-lighten-1">mdi-video-off-outline</v-icon>
      <span class="sot-pending-text">Awaiting processing</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  cueData: {
    type: Object,
    required: true
  },
  variant: {
    type: String,
    default: 'SOT',
    validator: (v) => ['SOT', 'VO'].includes(v)
  },
  jobStatus: {
    type: Object,
    default: null
  },
  sotThumbnailUrl: {
    type: String,
    default: ''
  },
  sotThumbnailOptions: {
    type: Array,
    default: () => []
  },
  currentSotThumbnailUrl: {
    type: String,
    default: ''
  },
  sotVideoUrl: {
    type: String,
    default: ''
  },
  sotTranscription: {
    type: String,
    default: ''
  },
  sotOutcue: {
    type: String,
    default: ''
  },
  isJobCompleted: {
    type: Boolean,
    default: false
  },
  displayDuration: {
    type: String,
    default: null
  },
  displayVideoPath: {
    type: String,
    default: null
  },
  displayProcessingStatus: {
    type: String,
    default: null
  },
  currentThumbnailSharpness: {
    type: Number,
    default: null
  },
  sharpnessColor: {
    type: String,
    default: 'grey'
  },
  initialThumbnailIndex: {
    type: Number,
    default: 7
  }
});

const emit = defineEmits(['open-sot-preview', 'update-meta']);

// data
const showInlinePlayer = ref(false);
const currentThumbnailIndex = ref(props.initialThumbnailIndex);
const transcriptionCopied = ref(false);

// Template ref
const inlineVideoPlayerRef = ref(null); // eslint-disable-line no-unused-vars

// computed
const isVO = computed(() => {
  return props.variant === 'VO';
});

// watch
watch(() => props.initialThumbnailIndex, (newVal) => {
  currentThumbnailIndex.value = newVal;
});

// methods
function formatMediaPath(path) {
  if (!path) return '';
  const parts = path.split('/');
  return parts[parts.length - 1] || path;
}

function formatWarningLabel(warning) {
  if (!warning) return '';
  if (warning.includes(':')) {
    const type = warning.split(':')[0];
    const typeLabels = {
      'low_sharpness': 'Blurry',
      'moderate_blur': 'Low Quality',
      'unbalanced_audio': 'Audio Issue',
      'large_file': 'Large File'
    };
    return typeLabels[type] || type;
  }
  return warning.length > 20 ? warning.substring(0, 20) + '...' : warning;
}

function truncateTranscription(text) {
  if (!text) return '';
  if (text.length <= 100) return text;
  return text.substring(0, 100) + '...';
}

async function copyTranscription() {
  const text = props.sotTranscription;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    transcriptionCopied.value = true;
    if (typeof window.notifyUserStandard === 'function') {
      window.notifyUserStandard('Transcript copied to clipboard', '#4CAF50', 2000);
    }
    setTimeout(() => { transcriptionCopied.value = false; }, 2000);
  } catch (err) {
    console.error('Failed to copy transcript:', err);
    if (typeof window.notifyUserStandard === 'function') {
      window.notifyUserStandard('Failed to copy transcript', '#F44336', 3000);
    }
  }
}

function handleSotThumbnailError() {
  console.warn('SOT thumbnail failed to load:', props.currentSotThumbnailUrl);
}

function onVideoLoaded() {
  console.log('Inline video loaded:', props.sotVideoUrl);
}

function prevThumbnail() {
  if (currentThumbnailIndex.value > 0) {
    currentThumbnailIndex.value--;
    emitSelectedThumbnail();
  }
}

function nextThumbnail() {
  if (currentThumbnailIndex.value < props.sotThumbnailOptions.length - 1) {
    currentThumbnailIndex.value++;
    emitSelectedThumbnail();
  }
}

function emitSelectedThumbnail() {
  const selectedUrl = props.currentSotThumbnailUrl;
  console.log(`Selected thumbnail ${currentThumbnailIndex.value + 1}: ${selectedUrl}`);
  emit('update-meta', {
    assetId: props.cueData.assetId || props.cueData.assetid,
    field: 'thumbnailUrl',
    value: selectedUrl
  });
}
</script>

<style scoped>
.sot-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  background-color: rgba(var(--v-theme-surface-variant), 0.05);
  border-radius: 4px;
}

.vo-container {
  border-left: 3px solid #9C27B0;
}

.sot-completed-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.sot-thumbnail-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 0 0 200px;
}

.sot-thumbnail-section {
  position: relative;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  background-color: #1a1a2e;
}

.sot-thumbnail-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.sot-nav-btn {
  flex: 0 0 auto;
  min-width: 60px !important;
  font-size: 0.7rem !important;
  text-transform: none !important;
}

.sot-thumbnail-counter {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 500;
  text-align: center;
  flex: 1;
}

.sot-thumbnail-img {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  display: block;
  transition: transform 0.2s ease;
}

.sot-thumbnail-section:hover .sot-thumbnail-img {
  transform: scale(1.02);
}

.sot-thumbnail-placeholder {
  width: 100%;
  aspect-ratio: 16/9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background-color: rgba(0, 0, 0, 0.1);
}

.sot-placeholder-text {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
}

.sot-play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.3);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.sot-thumbnail-section:hover .sot-play-overlay {
  opacity: 1;
}

.sot-complete-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background-color: #4CAF50;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  border-radius: 2px;
}

.vo-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background-color: #9C27B0;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  border-radius: 2px;
}

.vo-notice {
  color: #7B1FA2;
  font-style: italic;
}

.sot-info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sot-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.sot-info-label {
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 500;
  min-width: 60px;
}

.sot-info-value {
  color: rgba(var(--v-theme-on-surface), 0.87);
  font-weight: 500;
}

.sot-media-path {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.sot-tech-specs {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.8rem;
}

.sot-warnings-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.sot-sharpness-row {
  margin-top: 4px;
}

.sot-transcription-preview {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 8px;
  padding: 8px;
  background-color: rgba(var(--v-theme-surface), 0.3);
  border-left: 3px solid rgb(var(--v-theme-primary));
  border-radius: 4px;
}

.sot-transcription-text {
  flex: 1;
  font-size: 0.85rem;
  line-height: 1.4;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-style: italic;
}

.sot-outcue-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.15) 0%, rgba(255, 152, 0, 0.1) 100%);
  border: 2px solid #ffc107;
  border-radius: 6px;
  width: 100%;
}

.sot-outcue-banner .sot-outcue-label {
  font-size: 0.8rem;
  font-weight: 800;
  color: #ff8f00;
  text-transform: uppercase;
  letter-spacing: 1px;
  white-space: nowrap;
}

.sot-outcue-banner .sot-outcue-text {
  flex: 1;
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.95);
  font-style: italic;
}

.sot-processing-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  z-index: 5;
  border-radius: inherit;
}

.sot-processing-overlay-text {
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.sot-processing-placeholder {
  width: 100%;
  min-height: 120px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sot-processing-layout {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  border-radius: 4px;
}

.sot-processing-info {
  flex: 1;
}

.sot-processing-phase {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.87);
  text-transform: capitalize;
}

.sot-processing-message {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 4px;
}

.sot-pending-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  background-color: rgba(var(--v-theme-surface-variant), 0.1);
  border: 2px dashed rgba(var(--v-theme-outline), 0.2);
  border-radius: 4px;
}

.sot-pending-text {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
}

.sot-inline-player-container {
  width: 100%;
  margin-bottom: 12px;
  border-radius: 4px;
  overflow: hidden;
  background: #1a1a2e;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.sot-inline-player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sot-inline-player-title {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.sot-inline-video {
  width: 100%;
  display: block;
  max-height: 200px;
  background: #000;
}

.sot-thumbnail-clickable {
  cursor: pointer;
}
</style>
