<template>
  <!-- Outside-the-modal overlays (orange theme for VO). Only render
       when a video is loaded. -->
  <MediaModalOverlays
    :show="show"
    :media-loaded="!!blobUrl"
    :current-timecode="currentTimecode"
    :remaining-timecode="remainingTimecode"
    :current-action-display="currentActionDisplay"
    :trim-start="trimStart"
    :trim-end="trimEnd"
    :clip-duration="clipDuration"
    :show-speed-indicator="showSpeedIndicator"
    :playback-speed="playbackSpeed"
    :speed-label="speedLabel"
    :show-frame-counter="showFrameCounter"
    :current-frame-number="currentFrameNumber"
    :total-frames="totalFrames"
    :frame-step-direction="frameStepDirection"
    :thumbnail-timecode="thumbnailTimecode"
    :clipping-method="clippingMethod"
    :clips="clips"
    :clip-slug="clipSlug"
    :slug="slug"
    v-model:show-hotkeys="showHotkeys"
    @remove-clip="removeClip"
    @update-clip-slug="(p) => { clips[p.index].slug = p.slug }"
    :theme-colors="{
      in: '#2196F3', inDark: '#1976D2',
      out: '#FF5722', outDark: '#E64A19',
      clip: '#FF9800', clipDark: '#F57C00',
      thumb: '#9C27B0', thumbDark: '#7B1FA2',
      speed: '#FFB74D'
    }"
  />

  <v-dialog
    :model-value="show"
    @update:model-value="onDialogUpdate"
    max-width="1100"
    persistent
    scrollable
  >
    <v-card ref="modalCardRef" class="vo-modal-card">
      <!-- Header -->
      <v-toolbar density="compact" color="orange-darken-3" dark>
        <v-toolbar-title class="text-white">
          <v-icon start>mdi-microphone-off</v-icon>
          VO Cue — Voice Over (Video, no audio required)
        </v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="cancel" title="Cancel (ESC)">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-toolbar>

      <v-card-text class="pa-4">

        <!-- Top error bar -->
        <div v-if="topError" class="top-error" ref="topErrorEl">
          {{ topError }}
        </div>

        <!-- Type of Cut row -->
        <div class="cut-type-row mb-3">
          <div class="cut-type-label">Type of Cut:</div>
          <div class="cut-type-buttons">
            <button
              ref="firstCutModeButtonRef"
              :class="['cut-btn', { active: clippingMethod === 'none', focused: focusedCutMode === 'none' }]"
              @click="selectCutMode('none')"
              @focus="focusedCutMode = 'none'"
              @blur="focusedCutMode = null"
              @keydown="handleCutModeKeydown($event, 'none')"
            >
              <span class="cut-btn-label">NONE</span>
              <span class="cut-btn-key">N</span>
            </button>
            <button
              :class="['cut-btn', { active: clippingMethod === 'single-trim', focused: focusedCutMode === 'single-trim' }]"
              @click="selectCutMode('single-trim')"
              @focus="focusedCutMode = 'single-trim'"
              @blur="focusedCutMode = null"
              @keydown="handleCutModeKeydown($event, 'single-trim')"
            >
              <span class="cut-btn-label">SINGLE TRIM</span>
              <span class="cut-btn-key">S</span>
            </button>
            <button
              :class="['cut-btn', { active: clippingMethod === 'individual-clips', focused: focusedCutMode === 'individual-clips' }]"
              @click="selectCutMode('individual-clips')"
              @focus="focusedCutMode = 'individual-clips'"
              @blur="focusedCutMode = null"
              @keydown="handleCutModeKeydown($event, 'individual-clips')"
            >
              <span class="cut-btn-label">MULTIPLE CLIPS</span>
              <span class="cut-btn-key">M</span>
            </button>
          </div>
        </div>

        <!-- Form: slug + description (hidden in individual-clips mode in
             favor of the inline clip tool row) -->
        <v-row v-if="clippingMethod !== 'individual-clips'" dense>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="slug"
              label="Slug"
              hint="e.g. trump-walks-off"
              persistent-hint
              autofocus
              :error-messages="slugError"
              @update:model-value="slugError = ''"
              ref="slugFieldRef"
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="duration"
              label="Display Duration"
              hint="auto-filled from video; HH:MM:SS"
              persistent-hint
              readonly
            />
          </v-col>
          <v-col cols="12">
            <v-textarea
              v-model="description"
              label="Description"
              rows="2"
              auto-grow
              hide-details
            />
          </v-col>
        </v-row>

        <!-- Individual-clips top-row tools -->
        <div v-else class="individual-clips-tools">
          <v-row dense align="center">
            <v-col cols="12" md="4">
              <v-text-field
                ref="clipSlugInputRef"
                v-model="clipSlug"
                label="Clip Slug"
                hint="auto-generated if blank"
                persistent-hint
                density="compact"
                :class="{ 'clip-slug-attention': clipSlugNeedsAttention }"
                @input="handleClipSlugInput"
                @keydown.enter="handleClipSlugEnter"
              />
            </v-col>
            <v-col cols="6" md="3">
              <v-text-field
                ref="trimStartInputRef"
                v-model="trimStart"
                label="Time Start"
                density="compact"
                hide-details
              />
            </v-col>
            <v-col cols="6" md="3">
              <v-text-field
                ref="trimEndInputRef"
                v-model="trimEnd"
                label="Time End"
                density="compact"
                hide-details
              />
            </v-col>
            <v-col cols="12" md="2">
              <v-btn
                block
                color="orange-darken-1"
                @click="handleTakeClip"
                title="Take clip (Ctrl+Enter or Enter Enter)"
              >
                TAKE
              </v-btn>
            </v-col>
          </v-row>
          <div v-if="clips.length > 0" class="clips-badges mt-2">
            <v-chip
              v-for="(clip, idx) in clips"
              :key="`badge-${idx}`"
              closable
              color="orange-darken-2"
              variant="tonal"
              size="small"
              class="mr-2 mb-1"
              @click:close="removeClip(idx)"
            >
              {{ clip.slug }}
            </v-chip>
          </div>
        </div>

        <v-divider class="my-3" />

        <!-- Video preview + file picker -->
        <div class="video-section">
          <!-- File picker (when no video loaded) -->
          <div
            v-if="!blobUrl"
            class="video-dropzone"
            @click="triggerFileInput"
            @drop.prevent="handleDrop"
            @dragover.prevent
          >
            <v-icon size="56" color="grey-lighten-1">mdi-video-plus</v-icon>
            <div class="text-body-1 mt-2">Click or drop a video file to upload</div>
            <div class="text-caption text-grey">
              Accepted: MP4, MOV, MKV, WebM. Audio not required. (Press B to browse)
            </div>
            <input
              ref="fileInputRef"
              type="file"
              accept=".mp4,.mov,.mkv,.webm"
              style="display: none;"
              @change="handleFileUpload"
            />
          </div>

          <!-- Video player -->
          <div v-else class="video-player-wrapper">
            <video
              ref="videoPlayerRef"
              :src="blobUrl"
              class="video-player"
              @loadedmetadata="onVideoMetadata"
              @timeupdate="updateTimecode"
              @play="updatePlayPauseState"
              @pause="updatePlayPauseState"
              @error="onVideoError"
              controls
              preload="metadata"
            />

            <!-- Video info overlay -->
            <div ref="videoInfoOverlayRef" class="video-info-overlay" />

            <!-- Upload progress -->
            <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
              <div class="upload-progress-bar" :style="{ width: uploadProgress + '%' }" />
              <div class="upload-progress-text">Uploading {{ uploadProgress }}%</div>
            </div>
            <div v-if="uploadComplete" class="upload-complete">
              <v-icon size="16" color="green">mdi-check-circle</v-icon>
              Upload complete · ready to process
            </div>

            <v-btn
              size="x-small"
              variant="text"
              class="clear-video-btn"
              @click="clearVideo"
              title="Clear video"
            >
              <v-icon size="18">mdi-close</v-icon> Clear
            </v-btn>
          </div>
        </div>

        <!-- Waveform / timeline -->
        <transition name="waveform-slide">
          <div v-if="showWaveform" class="waveform-wrapper">
            <AudioWaveform
              :waveform-data="waveformData"
              :current-time="videoPlayerRef?.currentTime || 0"
              :duration="videoPlayerRef?.duration || 0"
              :height="60"
              background-color="rgba(0, 0, 0, 0.7)"
              wave-color="#FF8F00"
              progress-color="#FFB74D"
              playhead-color="#FF5722"
              :in-point="inPointSeconds"
              :out-point="outPointSeconds"
              region-color="#000000"
              region-background="rgba(255, 255, 255, 0.35)"
              @seek="handleWaveformSeek"
            />

            <!-- NO AUDIO overlay — VO content is video-only by design.
                 Scrubber and click-to-seek beneath remain functional. -->
            <div v-if="!hasAudio" class="no-audio-overlay" aria-label="No audio track">
              <span class="no-audio-text">NO AUDIO</span>
            </div>
          </div>
        </transition>

        <!-- 2x6 control grid -->
        <div v-if="blobUrl" class="control-grid mt-3">
          <div class="control-row">
            <button
              ref="markInBtnRef"
              class="grid-btn mark-in"
              @click="onMarkIn"
              title="Mark IN (I)"
            >
              <span class="btn-label">MARK IN</span>
              <span class="btn-key">I</span>
            </button>
            <button
              class="grid-btn go-to"
              @click="performGoToInAction"
              title="Go to IN (Q)"
            >
              <span class="btn-label">GO IN</span>
              <span class="btn-key">Q</span>
            </button>
            <button
              ref="playPauseBtnRef"
              class="grid-btn play-pause"
              @click="onPlayPause"
              title="Play / Pause (Space)"
            >
              <v-icon size="22">{{ isPlaying ? 'mdi-pause' : 'mdi-play' }}</v-icon>
              <span class="btn-key">SPC</span>
            </button>
            <button
              class="grid-btn preview"
              @click="onPreview"
              title="Preview IN→OUT (Shift+Space)"
            >
              <span class="btn-label">PREVIEW</span>
              <span class="btn-key">⇧SPC</span>
            </button>
            <button
              class="grid-btn go-to"
              @click="performGoToOutAction"
              title="Go to OUT (W)"
            >
              <span class="btn-label">GO OUT</span>
              <span class="btn-key">W</span>
            </button>
            <button
              ref="markOutBtnRef"
              class="grid-btn mark-out"
              @click="onMarkOut"
              title="Mark OUT (O)"
            >
              <span class="btn-label">MARK OUT</span>
              <span class="btn-key">O</span>
            </button>
          </div>

          <div class="control-row">
            <button class="grid-btn step" @click="performJumpBackTenSeconds" title="Back 10s (↓)">
              <span class="btn-label">−10 s</span>
            </button>
            <button class="grid-btn step" @click="performStepBackSecond" title="Back 1s (J)">
              <span class="btn-label">−1 s</span>
            </button>
            <button class="grid-btn step" @click="performStepBackFrame" title="Back 1 frame (←)">
              <span class="btn-label">−1 f</span>
            </button>
            <button class="grid-btn step" @click="performStepForwardFrame" title="Forward 1 frame (→)">
              <span class="btn-label">+1 f</span>
            </button>
            <button class="grid-btn step" @click="performStepForwardSecond" title="Forward 1s (L)">
              <span class="btn-label">+1 s</span>
            </button>
            <button class="grid-btn step" @click="performJumpForwardTenSeconds" title="Forward 10s (↑)">
              <span class="btn-label">+10 s</span>
            </button>
          </div>

          <!-- Trim point displays + current action overlay -->
          <div class="trim-display mt-2">
            <div class="trim-row">
              <span class="trim-label">IN:</span>
              <span class="trim-value">{{ trimStart }}</span>
              <span class="trim-label ml-3">OUT:</span>
              <span class="trim-value">{{ trimEnd }}</span>
              <span class="trim-label ml-3">Clip:</span>
              <span class="trim-value">{{ secondsToTimecode(clipDuration, false) }}</span>
              <v-spacer />
              <span class="trim-label">Now:</span>
              <span class="trim-value mono">{{ currentTimecode }}</span>
              <span class="trim-label ml-2">Dur:</span>
              <span class="trim-value mono">{{ durationTimecode }}</span>
            </div>
            <transition name="action-fade">
              <div v-if="currentActionDisplay" class="action-display">
                {{ currentActionDisplay }}
              </div>
            </transition>
          </div>
        </div>

      </v-card-text>

      <v-divider />

      <v-card-actions class="px-4 py-3">
        <v-spacer />
        <v-btn variant="text" @click="cancel">Cancel</v-btn>
        <v-btn
          color="orange-darken-3"
          variant="elevated"
          :disabled="!canSubmit || isSubmitting"
          :loading="isSubmitting"
          @click="submit"
        >
          <v-icon start>mdi-check</v-icon>
          {{ clippingMethod === 'individual-clips' ? `Insert ${clips.length} VO Cue${clips.length !== 1 ? 's' : ''}` : 'Insert VO Cue' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>


<script setup>
/**
 * VoModal — Voice Over cue creation modal.
 *
 * Full keyboard + preview + multi-clip parity with SotModal via shared
 * composables. VO-specific bits stay here:
 *   - /api/vo/upload/background + /api/vo/process endpoints
 *   - NO AUDIO overlay over the waveform area
 *   - Orange theme, no transcription / credits / thumbnails
 *
 * State + actions come from @composables/useTrimmableMediaModal.
 * Keyboard shortcuts from useMediaModalKeyboard. Multi-clip workflow
 * from useMediaModalClips. Focus trap from useFocusTrap.
 *
 * Cue insertion contract with ContentEditor:
 *   - emits `submit` (single VO cue payload) when clippingMethod !== 'individual-clips'
 *   - emits `submit-multiple` (array of VO payloads) when 'individual-clips'
 */
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios' // eslint-disable-line no-unused-vars

import AudioWaveform from '@/components/AudioWaveform.vue'
import { useWaveform } from '@/composables/useWaveform'
import { useTrimmableMediaModal } from '@/composables/useTrimmableMediaModal'
import { useMediaModalKeyboard } from '@/composables/useMediaModalKeyboard'
import { useMediaModalClips } from '@/composables/useMediaModalClips'
import { useFocusTrap } from '@/composables/useFocusTrap'
import { uploadVideoInBackground } from '@/utils/mediaUpload'
import { registerModalEsc } from '@/composables/useModalStack'
import { useDoubleEnterToSlug } from '@/composables/useDoubleEnterToSlug'
import MediaModalOverlays from '@/components/modals/shared/MediaModalOverlays.vue'
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'

// ---------------------------------------------------------------------------
// Props / emits — backward compatible; adds `submit-multiple`
// ---------------------------------------------------------------------------
const props = defineProps({
  show: Boolean,
  episode: String,
  duplicateSlugs: { type: Array, default: () => [] },
  cueType: { type: String, default: 'vo' }, // eslint-disable-line no-unused-vars
  // Optional prepopulation payload — e.g. when a SOT with no audio is converted
  // to a VO. Shape: { file: File, slug: string }.
  incomingData: { type: Object, default: null },
})
const emit = defineEmits(['update:show', 'submit', 'submit-multiple'])

const toast = useToast()

// ---------------------------------------------------------------------------
// Refs (template + DOM)
// ---------------------------------------------------------------------------
const modalCardRef = ref(null)
const videoPlayerRef = ref(null)
const fileInputRef = ref(null)
const slugFieldRef = ref(null)
const topErrorEl = ref(null) // eslint-disable-line no-unused-vars
const videoInfoOverlayRef = ref(null)
const markInBtnRef = ref(null)
const markOutBtnRef = ref(null)
const playPauseBtnRef = ref(null)
const trimStartInputRef = ref(null)
const trimEndInputRef = ref(null)
const clipSlugInputRef = ref(null)
const firstCutModeButtonRef = ref(null)

// ---------------------------------------------------------------------------
// Shared timeline composable — provides state + actions + utilities.
// Toast is wired so the composable emits its own IN/OUT/preview toasts.
// ---------------------------------------------------------------------------
const trim = useTrimmableMediaModal({
  videoPlayerRef,
  defaultFramerate: 30,
  toast,
  emitActionFeedback: true,
})
const {
  // State
  trimStart, trimEnd, duration, currentFramerate, isPlaying,
  currentTimecode, durationTimecode, remainingTimecode,
  currentActionDisplay, thumbnailTimecode,
  playbackSpeed, showSpeedIndicator, speedLabel,
  showFrameCounter, currentFrameNumber, totalFrames, frameStepDirection,
  // Multi-clip state
  clippingMethod, clipSlug, clips, clipCounter, // eslint-disable-line no-unused-vars
  // Computed
  clipDuration, inPointSeconds, outPointSeconds,
  // Pure utilities
  secondsToTimecode, formatFileSize,
  animateButtonPress,
  // Mark / go-to
  performGoToInAction, performGoToOutAction, handleWaveformSeek,
  // Frame stepping
  performStepBackFrame, performStepForwardFrame,
  performStepBackSecond, performStepForwardSecond,
  performJumpBackTenSeconds, performJumpForwardTenSeconds,
  // Live updates
  updateTimecode, updatePlayPauseState,
} = trim

// ---------------------------------------------------------------------------
// Waveform composable
// ---------------------------------------------------------------------------
const { waveformData, extractWaveform, clearWaveform } = useWaveform()
const showWaveform = ref(false)
const hasAudio = ref(false)

// ---------------------------------------------------------------------------
// Local form / upload state
// ---------------------------------------------------------------------------
const slug = ref('')
const slugError = ref('')
const description = ref('')
const blobUrl = ref('')
const originalFile = ref(null)
const uploadProgress = ref(0)
const uploadComplete = ref(false)
const tempJobId = ref(null)
const isSubmitting = ref(false)
const topError = ref('')
const videoSpecs = ref({})
let uploadAbortFn = null

// Cut-mode focus state
const focusedCutMode = ref(null)

// Hotkeys sidebar visibility (toggled by Ctrl+1)
const showHotkeys = ref(false)

// ---------------------------------------------------------------------------
// Computed — color values for validation feedback
// ---------------------------------------------------------------------------
const locatorFlashColor = computed(() => {
  const colorName = getColorValue('locatorflash') || 'deep-orange-accent-2'
  return resolveVuetifyColor(colorName)
})

// ---------------------------------------------------------------------------
// Multi-clip actions
// ---------------------------------------------------------------------------
const clipsApi = useMediaModalClips({
  videoPlayerRef,
  trim,
  toast,
  clipSlugInputRef,
  locatorFlashColor,
  slug,
})
const {
  clipSlugNeedsAttention,
  handleTakeClip,
  removeClip,
  handleDoubleEnterTake,
  handleClipSlugInput,
  handleClipSlugEnter,
} = clipsApi

// ---------------------------------------------------------------------------
// Derived
// ---------------------------------------------------------------------------
const canSubmit = computed(() => {
  if (!blobUrl.value || !uploadComplete.value) return false
  if (clippingMethod.value === 'individual-clips') {
    // Need at least one clip taken
    return clips.value.length > 0
  }
  return !!slug.value.trim()
})

// ---------------------------------------------------------------------------
// Cut-mode selection (mirrors SotModal pattern)
// ---------------------------------------------------------------------------
function selectCutMode(mode) {
  clippingMethod.value = mode
  console.log(`[VoModal] Cut mode → ${mode}`)
}

function handleCutModeKeydown(event, mode) {
  if (event.key === ' ' || event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    selectCutMode(mode)
  }
}

// ---------------------------------------------------------------------------
// File handling
// ---------------------------------------------------------------------------
function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleDrop(e) {
  const file = e.dataTransfer?.files?.[0]
  if (file) loadFile(file)
}

function handleFileUpload(e) {
  const file = e.target.files?.[0]
  if (file) loadFile(file)
}

async function loadFile(file) {
  originalFile.value = file
  if (blobUrl.value && blobUrl.value.startsWith('blob:')) {
    try { URL.revokeObjectURL(blobUrl.value) } catch (_e) { /* noop */ }
  }
  blobUrl.value = URL.createObjectURL(file)
  uploadComplete.value = false
  uploadProgress.value = 0
  tempJobId.value = null

  await nextTick()
  startBackgroundUpload(file)
}

async function startBackgroundUpload(file) {
  uploadProgress.value = 1
  uploadComplete.value = false
  const { promise, abort } = uploadVideoInBackground(file, '/api/vo/upload/background', {
    onProgress: (p) => { uploadProgress.value = p }
  })
  uploadAbortFn = abort
  try {
    const result = await promise
    tempJobId.value = result?.temp_job_id || null
    uploadProgress.value = 100
    uploadComplete.value = true
    toast.success('Upload complete')
  } catch (err) {
    if (err?.message === 'aborted') {
      uploadProgress.value = 0
      return
    }
    console.error('[VoModal] background upload failed:', err)
    uploadProgress.value = 0
    topError.value = `Upload failed: ${err?.message || 'unknown error'}`
    toast.error(topError.value)
  } finally {
    uploadAbortFn = null
  }
}

function clearVideo() {
  // Cancel any in-flight upload so its stale onload doesn't write to a
  // reset modal.
  if (uploadAbortFn) {
    try { uploadAbortFn() } catch (_e) { /* noop */ }
    uploadAbortFn = null
  }
  if (blobUrl.value && blobUrl.value.startsWith('blob:')) {
    try { URL.revokeObjectURL(blobUrl.value) } catch (_e) { /* noop */ }
  }
  blobUrl.value = ''
  originalFile.value = null
  uploadProgress.value = 0
  uploadComplete.value = false
  tempJobId.value = null
  showWaveform.value = false
  clearWaveform()
  hasAudio.value = false
}

// ---------------------------------------------------------------------------
// Video metadata + waveform extraction
// ---------------------------------------------------------------------------
function onVideoError() {
  const v = videoPlayerRef.value
  const err = v?.error
  if (!err) return
  const codes = { 1: 'aborted', 2: 'network error', 3: 'decode error (codec problem)', 4: 'format not supported by browser' }
  const label = codes[err.code] || `unknown (code ${err.code})`
  const detail = err.message ? ` — ${err.message}` : ''
  const filename = originalFile.value?.name || 'video'
  const reason = `Cannot play "${filename}" in browser: ${label}${detail}. Common causes: ProRes, HEVC/H.265 w/o hardware decode, raw DV. Try transcoding to H.264 MP4 first.`
  console.error('[VoModal]', reason, err)
  topError.value = reason
  if (toast?.error) toast.error(reason)
}

function onVideoMetadata() {
  const v = videoPlayerRef.value
  if (!v) return
  const w = v.videoWidth, h = v.videoHeight, dur = v.duration || 0
  videoSpecs.value = {
    resolution: w && h ? `${w}×${h}` : null,
    aspectRatio: w && h ? (w / h).toFixed(3) : null,
    duration: dur,
    framerate: 30,
    fileSize: originalFile.value?.size || null,
    filename: originalFile.value?.name || '',
  }
  currentFramerate.value = videoSpecs.value.framerate
  duration.value = secondsToTimecode(dur, false)

  if (videoInfoOverlayRef.value) {
    videoInfoOverlayRef.value.innerHTML = `
      <div><strong>${videoSpecs.value.filename || 'Video'}</strong></div>
      <div>Resolution: ${videoSpecs.value.resolution || '—'}</div>
      <div>Aspect: ${videoSpecs.value.aspectRatio || '—'}:1</div>
      <div>Duration: ${secondsToTimecode(dur, true)}</div>
      <div>Framerate: ${videoSpecs.value.framerate}fps</div>
      <div>Size: ${formatFileSize(videoSpecs.value.fileSize || 0)}</div>
    `
  }

  // Extract waveform. For silent VO it returns an empty array; show
  // the NO AUDIO overlay.
  setTimeout(async () => {
    try {
      const samples = await extractWaveform(videoPlayerRef.value, 500)
      hasAudio.value = Array.isArray(samples) && samples.some(x => x > 0)
      setTimeout(() => { showWaveform.value = true }, 200)
    } catch (err) {
      console.warn('[VoModal] waveform extraction failed:', err)
      hasAudio.value = false
      showWaveform.value = true
    }
  }, 100)
}

// ---------------------------------------------------------------------------
// Action wrappers — composable provides the primitive; we add UX skin
// ---------------------------------------------------------------------------
function onMarkIn() {
  trim.performMarkInAction()
  animateButtonPress(markInBtnRef.value)
}

function onMarkOut() {
  trim.performMarkOutAction()
  animateButtonPress(markOutBtnRef.value)
}

function onPlayPause() {
  trim.performPlayPauseAction()
  animateButtonPress(playPauseBtnRef.value)
}

function onPreview() {
  if (clipDuration.value <= 0) {
    toast.warning('Mark IN and OUT first')
    return
  }
  trim.performPreviewAction()
}

// ---------------------------------------------------------------------------
// Keyboard shortcuts
// ---------------------------------------------------------------------------
const kbd = useMediaModalKeyboard({
  show: () => props.show,
  videoPlayerRef,
  trim,
  onSubmit: () => submit(),
  onTake: () => handleTakeClip(),
  onPreviewIntoOut: () => onPreview(),
  onDoubleEnterTake: () => handleDoubleEnterTake(),
  onCutModeSelect: (mode) => selectCutMode(mode),
  onBrowseFile: () => triggerFileInput(),
  onToggleHotkeys: () => { showHotkeys.value = !showHotkeys.value },
  onEscape: () => handleEscapeKey(),
  trimStartInputRef,
  trimEndInputRef,
  clippingMethod,
})

// ---------------------------------------------------------------------------
// Focus trap
// ---------------------------------------------------------------------------
const focusTrap = useFocusTrap(modalCardRef)

// ESC handled by global modal stack — uniform with the other modals.
// useMediaModalKeyboard no longer handles ESC itself.
registerModalEsc(() => props.show, () => handleEscapeKey(), 'VoModal')
useDoubleEnterToSlug(() => props.show, slugFieldRef)

// ---------------------------------------------------------------------------
// Submission
// ---------------------------------------------------------------------------
async function submit() {
  if (isSubmitting.value) return
  if (!blobUrl.value || !uploadComplete.value) {
    toast.warning('Wait for upload to complete')
    return
  }

  // Multi-clip path
  if (clippingMethod.value === 'individual-clips') {
    if (clips.value.length === 0) {
      toast.warning('TAKE at least one clip first (Ctrl+Enter)')
      return
    }
    isSubmitting.value = true
    try {
      const multipleVos = clips.value.map((clip) => ({
        type: 'VO',
        slug: clip.slug,
        description: description.value,
        duration: secondsToTimecode(clip.duration_seconds, false),
        trimStart: clip.time_start,
        trimEnd: clip.time_end,
        tempJobId: tempJobId.value,
        hasAudio: hasAudio.value,
      }))
      emit('submit-multiple', multipleVos)
      resetForm()
      emit('update:show', false)
    } finally {
      isSubmitting.value = false
    }
    return
  }

  // Single submission path
  if (!slug.value.trim()) {
    slugError.value = 'Slug required'
    return
  }
  if (props.duplicateSlugs.includes(slug.value.trim())) {
    slugError.value = 'Slug already used in this episode'
    return
  }

  isSubmitting.value = true
  try {
    if (tempJobId.value) {
      try {
        await axios.post('/api/vo/process', {
          temp_job_id: tempJobId.value,
          episode: props.episode,
          slug: slug.value.trim(),
          trim_start: trimStart.value,
          trim_end: trimEnd.value,
        })
      } catch (err) {
        console.warn('[VoModal] /api/vo/process call failed (continuing with cue insert anyway):', err)
      }
    }

    const voCueData = {
      type: 'VO',
      slug: slug.value.trim(),
      description: description.value,
      duration: duration.value || '00:00:30',
      trimStart: trimStart.value,
      trimEnd: trimEnd.value,
      tempJobId: tempJobId.value,
      hasAudio: hasAudio.value,
    }
    emit('submit', voCueData)
    resetForm()
    emit('update:show', false)
  } finally {
    isSubmitting.value = false
  }
}

function cancel() {
  resetForm()
  emit('update:show', false)
}

function handleEscapeKey() {
  // ESC closes the modal directly (matches SotModal pattern, no
  // confirmation prompt). cancel() → resetForm() clears state.
  console.log('⎋ ESC pressed - closing VO modal')
  cancel()
}

function resetForm() {
  slug.value = ''
  slugError.value = ''
  description.value = ''
  topError.value = ''
  trimStart.value = '00:00:00'
  trimEnd.value = '00:00:00'
  clippingMethod.value = 'none'
  clipSlug.value = ''
  clips.value = []
  clipCounter.value = 1
  thumbnailTimecode.value = ''
  showHotkeys.value = false
  isSubmitting.value = false
  clearVideo()
}

function onDialogUpdate(v) {
  if (!v) cancel()
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------
onMounted(() => {
  if (props.show) {
    kbd.install()
    nextTick(() => { focusTrap.install() })
  }
})

watch(
  () => props.show,
  (newValue, oldValue) => {
    if (newValue && !oldValue) {
      kbd.install()
      // Prepopulate from a SOT→VO conversion: load the same file + slug.
      if (props.incomingData) {
        const { file, slug: incomingSlug } = props.incomingData
        if (incomingSlug) slug.value = incomingSlug
        if (file) {
          nextTick(() => { loadFile(file) })
        }
      }
      nextTick(() => {
        focusTrap.install()
        // Auto-focus first cut-mode button (NONE)
        requestAnimationFrame(() => requestAnimationFrame(() => {
          if (firstCutModeButtonRef.value) {
            firstCutModeButtonRef.value.focus()
            focusedCutMode.value = 'none'
          } else if (slugFieldRef.value) {
            slugFieldRef.value.focus?.()
          }
        }))
      })
    } else if (!newValue && oldValue) {
      kbd.uninstall()
      focusTrap.uninstall()
      resetForm()
    }
  }
)

onBeforeUnmount(() => {
  if (blobUrl.value && blobUrl.value.startsWith('blob:')) {
    try { URL.revokeObjectURL(blobUrl.value) } catch (_e) { /* noop */ }
  }
})
</script>


<style scoped>
.vo-modal-card {
  border-radius: 6px;
  overflow: hidden;
}

.top-error {
  background: #ffebee;
  border-left: 4px solid #c62828;
  color: #c62828;
  padding: 8px 12px;
  margin-bottom: 12px;
  font-weight: 600;
}

/* Cut-mode row */
.cut-type-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.cut-type-label {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.6);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.cut-type-buttons {
  display: flex;
  gap: 6px;
  flex: 1;
}
.cut-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 8px 12px;
  border: 2px solid rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.04);
  color: rgba(0, 0, 0, 0.7);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all 0.15s ease;
}
.cut-btn:hover {
  background: rgba(255, 152, 0, 0.08);
  border-color: rgba(255, 152, 0, 0.5);
}
.cut-btn.focused {
  border-color: #FF8F00;
  box-shadow: 0 0 0 2px rgba(255, 143, 0, 0.3);
  outline: none;
}
.cut-btn.active {
  background: #FF8F00;
  color: white;
  border-color: #E65100;
}
.cut-btn-key {
  font-size: 10px;
  opacity: 0.6;
}

/* Individual clips tools */
.individual-clips-tools {
  background: rgba(255, 152, 0, 0.05);
  border: 1px solid rgba(255, 152, 0, 0.2);
  border-radius: 4px;
  padding: 12px;
}
.clip-slug-attention {
  animation: clip-attention-pulse 0.4s ease-in-out 3;
}
@keyframes clip-attention-pulse {
  0%, 100% { box-shadow: none; }
  50% { box-shadow: 0 0 0 3px rgba(255, 87, 34, 0.5); }
}
.clips-badges {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

/* Video upload dropzone */
.video-section { position: relative; }
.video-dropzone {
  border: 2px dashed rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  padding: 36px 16px;
  text-align: center;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
  background: rgba(0, 0, 0, 0.02);
}
.video-dropzone:hover {
  background: rgba(255, 152, 0, 0.05);
  border-color: rgba(255, 152, 0, 0.5);
}
.video-player-wrapper {
  position: relative;
  background: #000;
  border-radius: 6px;
  overflow: hidden;
  min-height: 300px;
}
.video-player {
  display: block;
  width: 100%;
  height: 300px;
  max-height: 360px;
  background: #000;
  object-fit: contain;
}
.video-info-overlay {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 6px 10px;
  font-size: 11px;
  border-radius: 4px;
  pointer-events: none;
}
.upload-progress {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 4px;
  background: rgba(255, 255, 255, 0.15);
}
.upload-progress-bar {
  height: 100%;
  background: #4CAF50;
  transition: width 0.2s ease;
}
.upload-progress-text {
  position: absolute;
  bottom: 8px;
  right: 8px;
  font-size: 11px;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.7);
}
.upload-complete {
  position: absolute;
  top: 8px;
  right: 86px;
  font-size: 11px;
  color: #81C784;
  background: rgba(0, 0, 0, 0.6);
  padding: 4px 8px;
  border-radius: 3px;
  pointer-events: none;
  z-index: 5;
}
.clear-video-btn {
  position: absolute !important;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.6) !important;
  color: white !important;
  z-index: 14;
}

/* Waveform + NO AUDIO */
.waveform-wrapper {
  position: relative;
  width: 100%;
  margin-top: 12px;
  border-radius: 4px;
  overflow: hidden;
}
.no-audio-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.35) 50%, rgba(0,0,0,0.55) 100%);
  pointer-events: none;
  z-index: 5;
  user-select: none;
}
.no-audio-text {
  color: #FFA726;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 0.18em;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
  padding: 6px 14px;
  border: 2px solid rgba(255, 167, 38, 0.6);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.4);
}
.waveform-slide-enter-active {
  transition: transform 0.35s ease, opacity 0.35s ease;
}
.waveform-slide-enter-from {
  transform: translateY(15px);
  opacity: 0;
}

/* Control grid */
.control-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.control-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px;
}
.grid-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  height: 56px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 12px;
  color: white;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.grid-btn:active {
  transform: scale(0.95);
}
.grid-btn .btn-key {
  font-size: 10px;
  opacity: 0.7;
  letter-spacing: 0.05em;
}
.mark-in    { background: #2196F3; }
.mark-out   { background: #E64A19; }
.go-to      { background: #607D8B; }
.play-pause { background: #4CAF50; }
.preview    { background: #9C27B0; }
.step       { background: #455A64; }

.trim-display {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  padding: 8px 10px;
  font-size: 12px;
  position: relative;
}
.trim-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.trim-label {
  color: rgba(0, 0, 0, 0.55);
  font-weight: 600;
}
.trim-value {
  color: rgba(0, 0, 0, 0.85);
  font-weight: 700;
}
.trim-value.mono { font-family: 'Roboto Mono', monospace; }

.action-display {
  margin-top: 4px;
  font-size: 11px;
  color: #E65100;
  font-weight: 700;
  letter-spacing: 0.05em;
}
.action-fade-enter-active,
.action-fade-leave-active {
  transition: opacity 0.25s ease;
}
.action-fade-enter-from,
.action-fade-leave-to {
  opacity: 0;
}

/* Toast positioning — keep below the overlay timecode (matches SotModal) */
:deep(.Vue-Toastification__container) {
  top: 140px !important;
}
</style>
