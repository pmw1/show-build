<template>
  <v-dialog
    :model-value="show"
    @update:model-value="onDialogUpdate"
    max-width="1100"
    persistent
    scrollable
  >
    <v-card class="vo-modal-card">
      <!-- Header -->
      <v-toolbar density="compact" color="orange-darken-3" dark>
        <v-toolbar-title class="text-white">
          <v-icon start>mdi-microphone-off</v-icon>
          VO Cue — Voice Over (Video, no audio required)
        </v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="cancel" title="Cancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-toolbar>

      <v-card-text class="pa-4">

        <!-- Top error bar -->
        <div v-if="topError" class="top-error" ref="topErrorEl">
          {{ topError }}
        </div>

        <!-- Form: slug + description -->
        <v-row dense>
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
              Accepted: MP4, MOV, MKV, WebM. Audio not required.
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
              @timeupdate="onTimeupdate"
              @play="onPlay"
              @pause="onPause"
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

            <!-- NO AUDIO overlay — appears on top of the waveform area
                 because VO content is video-only by design. The scrubber,
                 in/out markers, and click-to-seek under it still work. -->
            <div v-if="!hasAudio" class="no-audio-overlay" aria-label="No audio track">
              <span class="no-audio-text">NO AUDIO</span>
            </div>
          </div>
        </transition>

        <!-- 2x6 control grid: row 1 mark/go/play/preview, row 2 stepping -->
        <div v-if="blobUrl" class="control-grid mt-3">
          <!-- Row 1 -->
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
              title="Preview IN→OUT (P)"
            >
              <span class="btn-label">PREVIEW</span>
              <span class="btn-key">P</span>
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

          <!-- Row 2 -->
          <div class="control-row">
            <button class="grid-btn step" @click="onStepBack10s" title="Back 10s (J)">
              <span class="btn-label">−10 s</span>
            </button>
            <button class="grid-btn step" @click="onStepBack1s" title="Back 1s (←)">
              <span class="btn-label">−1 s</span>
            </button>
            <button class="grid-btn step" @click="onStepBack1f" title="Back 1 frame (Shift+←)">
              <span class="btn-label">−1 f</span>
            </button>
            <button class="grid-btn step" @click="onStepForward1f" title="Forward 1 frame (Shift+→)">
              <span class="btn-label">+1 f</span>
            </button>
            <button class="grid-btn step" @click="onStepForward1s" title="Forward 1s (→)">
              <span class="btn-label">+1 s</span>
            </button>
            <button class="grid-btn step" @click="onStepForward10s" title="Forward 10s (L)">
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
          Insert VO Cue
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>


<script setup>
/**
 * VoModal — Voice Over cue creation modal.
 *
 * Modeled on SotModal (same overall UX: file upload, video player,
 * waveform timeline with in/out markers, mark-in/out + frame stepping
 * 2x6 control grid, trim display) but VO-specific:
 *   - Audio is NOT required. When the source has no audio track, a
 *     "NO AUDIO" overlay appears over the waveform area (the markers,
 *     scrubber, and click-to-seek under it remain functional).
 *   - Backend route is /api/vo/upload/background + /api/vo/process
 *     instead of the SOT pipeline.
 *   - No transcription, no audio normalization, no MP3 extraction —
 *     those phases are skipped by process_vo_video on the server.
 *   - Single-trim only (no individual-clips / montage modes).
 *
 * State + utilities + action primitives (mark-in/out, play/pause,
 * frame stepping, etc.) come from the shared @composables/
 * useTrimmableMediaModal composable. Modal-specific UX (toasts,
 * NO AUDIO overlay, button-press animations) is wrapped on top
 * here. SotModal will adopt the same composable in a follow-up.
 */
import { ref, computed, watch, nextTick } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios'

import AudioWaveform from '@/components/AudioWaveform.vue'
import { useWaveform } from '@/composables/useWaveform'
import { useTrimmableMediaModal } from '@/composables/useTrimmableMediaModal'

// ---------------------------------------------------------------------------
// Props / emits — drop-in compatible with the previous VoModal
// ---------------------------------------------------------------------------
const props = defineProps({
  show: Boolean,
  episode: String,
  duplicateSlugs: { type: Array, default: () => [] },
  cueType: { type: String, default: 'vo' },
})
const emit = defineEmits(['update:show', 'submit'])

const toast = useToast()

// ---------------------------------------------------------------------------
// Refs (template + DOM)
// ---------------------------------------------------------------------------
const videoPlayerRef = ref(null)
const fileInputRef = ref(null)
const slugFieldRef = ref(null) // eslint-disable-line no-unused-vars
const topErrorEl = ref(null) // eslint-disable-line no-unused-vars
const videoInfoOverlayRef = ref(null)
const markInBtnRef = ref(null)
const markOutBtnRef = ref(null)
const playPauseBtnRef = ref(null)

// ---------------------------------------------------------------------------
// Shared timeline composable — provides state + actions + utilities
// ---------------------------------------------------------------------------
const trim = useTrimmableMediaModal({ videoPlayerRef })
const {
  trimStart, trimEnd, duration, currentFramerate, isPlaying,
  currentTimecode, durationTimecode, currentActionDisplay,
  clipDuration, inPointSeconds, outPointSeconds,
  secondsToTimecode, formatFileSize,
  animateButtonPress,
  performGoToInAction, performGoToOutAction, handleWaveformSeek,
  updateTimecode, updatePlayPauseState,
} = trim

// ---------------------------------------------------------------------------
// Waveform composable (handles audio extraction; flat for silent videos)
// ---------------------------------------------------------------------------
const { waveformData, extractWaveform, clearWaveform } = useWaveform()
const showWaveform = ref(false)
const hasAudio = ref(false) // gates the NO AUDIO overlay

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

// ---------------------------------------------------------------------------
// Derived
// ---------------------------------------------------------------------------
const canSubmit = computed(() => {
  return !!slug.value.trim()
    && !!blobUrl.value
    && uploadComplete.value
})

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
  // Free any previous blob
  if (blobUrl.value && blobUrl.value.startsWith('blob:')) {
    try { URL.revokeObjectURL(blobUrl.value) } catch (_e) { /* noop */ }
  }
  blobUrl.value = URL.createObjectURL(file)
  uploadComplete.value = false
  uploadProgress.value = 0
  tempJobId.value = null

  await nextTick()
  // Player will fire @loadedmetadata which calls onVideoMetadata.
  startBackgroundUpload(file)
}

async function startBackgroundUpload(file) {
  const form = new FormData()
  form.append('file', file)
  form.append('episode', props.episode || '')

  try {
    const xhr = new XMLHttpRequest()
    xhr.upload.onprogress = (evt) => {
      if (evt.lengthComputable) {
        uploadProgress.value = Math.round((evt.loaded / evt.total) * 100)
      }
    }
    const result = await new Promise((resolve, reject) => {
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try { resolve(JSON.parse(xhr.responseText)) }
          catch (e) { reject(e) }
        } else { reject(new Error(`Upload failed: ${xhr.status}`)) }
      }
      xhr.onerror = () => reject(new Error('Upload network error'))
      xhr.open('POST', '/api/vo/upload/background')
      const token = localStorage.getItem('auth-token')
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      xhr.send(form)
    })
    tempJobId.value = result?.temp_job_id || null
    uploadProgress.value = 100
    uploadComplete.value = true
    toast.success('Upload complete')
  } catch (err) {
    console.error('[VoModal] background upload failed:', err)
    uploadProgress.value = 0
    topError.value = `Upload failed: ${err?.message || 'unknown error'}`
    toast.error(topError.value)
  }
}

function clearVideo() {
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
// MEDIA_ERR_* code → human label. The browser's <video> element fails
// silently on unsupported codecs (ProRes, HEVC w/o hw decode, AV1 on old
// Chromium, raw DV, etc.) — we surface the reason here as both a toast
// and topError bar so users aren't left staring at a black box.
function onVideoError() {
  const v = videoPlayerRef.value
  const err = v?.error
  if (!err) return
  const codes = {
    1: 'aborted',
    2: 'network error',
    3: 'decode error (codec problem)',
    4: 'format not supported by browser',
  }
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
    framerate: 30, // VO assumes 30fps unless detected later
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

  // Try to extract a waveform. For silent VO it returns an empty array; we
  // detect that and show the NO AUDIO overlay over the timeline panel.
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

function onTimeupdate() { updateTimecode() }
function onPlay() { updatePlayPauseState() }
function onPause() { updatePlayPauseState() }

// ---------------------------------------------------------------------------
// Action wrappers — composable provides the primitive; we add VO UX skin
// ---------------------------------------------------------------------------
function onMarkIn() {
  trim.performMarkInAction()
  animateButtonPress(markInBtnRef.value)
  toast.info(`IN @ ${trimStart.value}`, { timeout: 1500 })
}

function onMarkOut() {
  trim.performMarkOutAction()
  animateButtonPress(markOutBtnRef.value)
  toast.warning(`OUT @ ${trimEnd.value}`, { timeout: 1500 })
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

function onStepBack1f()  { trim.performStepBackFrame() }
function onStepForward1f() { trim.performStepForwardFrame() }
function onStepBack1s()  { trim.performStepBackSecond() }
function onStepForward1s() { trim.performStepForwardSecond() }
function onStepBack10s() { trim.performJumpBackTenSeconds() }
function onStepForward10s() { trim.performJumpForwardTenSeconds() }

// ---------------------------------------------------------------------------
// Submission
// ---------------------------------------------------------------------------
async function submit() {
  if (isSubmitting.value) return
  if (!slug.value.trim()) {
    slugError.value = 'Slug required'
    return
  }
  // Slug uniqueness against previously-known cues
  if (props.duplicateSlugs.includes(slug.value.trim())) {
    slugError.value = 'Slug already used in this episode'
    return
  }

  isSubmitting.value = true
  try {
    // Trigger backend processing on the already-uploaded temp job, if we
    // have one. The actual cue-block creation happens in the parent's
    // submitVo handler after the emit fires.
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

function resetForm() {
  slug.value = ''
  slugError.value = ''
  description.value = ''
  topError.value = ''
  trimStart.value = '00:00:00'
  trimEnd.value = '00:00:00'
  isSubmitting.value = false
  clearVideo()
}

function onDialogUpdate(v) {
  if (!v) cancel()
}

// Reset on close
watch(() => props.show, (val) => {
  if (!val) resetForm()
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

/* Video upload dropzone */
.video-section {
  position: relative;
}

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
  /* Deterministic height so controls below don't overlay an empty/short
     video element while metadata is loading or if the file fails to decode.
     Matches SotModal's 300px pattern. */
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
  bottom: 0;
  left: 0;
  right: 0;
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
  /* Sit to the left of the Clear button (top:8px right:8px, ~70px wide) */
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

/* Waveform area + NO AUDIO overlay */
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
  background: linear-gradient(
    135deg,
    rgba(0, 0, 0, 0.55) 0%,
    rgba(0, 0, 0, 0.35) 50%,
    rgba(0, 0, 0, 0.55) 100%
  );
  pointer-events: none; /* let clicks reach the AudioWaveform underneath */
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

/* Control grid (2 rows × 6 cells) */
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
.trim-value.mono {
  font-family: 'Roboto Mono', monospace;
}

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
</style>
