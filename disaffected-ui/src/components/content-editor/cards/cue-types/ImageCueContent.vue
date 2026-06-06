<!--
  ImageCueContent — the IMAGE-specific body of a cue card (IMG and other image
  cue types). A per-type CONTENT child of PlaceholderCueCard (the single CueCard
  shell), exactly like FsqCueContent / SotCueContent / GfxCueContent. The shell
  owns the header, footer, status border, collapse, and delete flow; this
  component owns ONLY the image preview + the Meta/Technical/Modify tab panels.

  Ported out of the former standalone ImageCueCard.vue (#49) so every cue type
  renders through one shell and chrome can't drift between two components.
-->
<template>
  <div class="image-container">
    <!-- Loading Placeholder -->
    <div v-if="!imageLoaded && !imageError && imageUrl" class="image-loading">
      <v-progress-circular indeterminate size="32" width="3" color="primary"></v-progress-circular>
      <span class="loading-text">Loading media<span class="loading-dots"></span></span>
    </div>
    <!-- Loaded Image -->
    <img
      v-show="imageUrl && !imageError"
      :src="resolveImagePath(imageUrl)"
      :alt="cueData.slug"
      class="cue-image"
      @error="handleImageError"
      @load="handleImageLoad"
    />
    <!-- Error States -->
    <div v-if="imageError" class="image-error">
      <v-icon color="warning">mdi-image-broken</v-icon>
      <span class="error-text">Image not found</span>
    </div>
    <div v-else-if="!imageUrl" class="image-error">
      <v-icon color="info">mdi-image-off</v-icon>
      <span class="error-text">No image URL found</span>
    </div>

    <!-- Tab Buttons (on top of image, above footer) -->
    <div v-if="imageUrl && imageLoaded && !readonly" class="tab-buttons">
      <button
        class="tab-button"
        :class="{ active: activeTab === 'meta' }"
        @click.stop="toggleTab('meta')"
      >
        Meta Info
      </button>
      <button
        class="tab-button"
        :class="{ active: activeTab === 'technical' }"
        @click.stop="toggleTab('technical')"
      >
        Technical Info
      </button>
      <button
        class="tab-button"
        :class="{ active: activeTab === 'modify' }"
        @click.stop="toggleTab('modify')"
      >
        Modify
      </button>
    </div>

    <!-- Sliding Panels -->
    <transition name="slide-up">
      <div v-if="activeTab === 'meta'" class="info-panel meta-panel" @click.stop>
        <div class="panel-content">
          <!-- Editable Meta Fields -->
          <div class="edit-field">
            <label class="edit-label">DESCRIPTION:</label>
            <input
              v-model="editableDescription"
              type="text"
              class="edit-input"
              placeholder="Brief description..."
            />
          </div>

          <div class="edit-field">
            <label class="edit-label">CREDIT:</label>
            <input
              v-model="editableCredit"
              type="text"
              class="edit-input"
              placeholder="Photo credit..."
            />
          </div>

          <div class="edit-field">
            <label class="edit-label">CAPTION:</label>
            <textarea
              v-model="editableCaption"
              class="edit-textarea"
              rows="2"
              placeholder="Image caption..."
            ></textarea>
          </div>

          <div class="edit-field">
            <label class="edit-label">DURATION:</label>
            <input
              v-model="editableDuration"
              type="text"
              class="edit-input"
              placeholder="00:00:05"
            />
          </div>

          <div class="edit-field">
            <label class="edit-label">TAGS:</label>
            <input
              v-model="editableTags"
              type="text"
              class="edit-input"
              placeholder="tag1, tag2, tag3"
            />
          </div>

          <!-- Save/Cancel Buttons -->
          <div class="edit-actions">
            <button class="edit-btn cancel-btn" @click.stop="cancelMetaEdit">
              Cancel
            </button>
            <button class="edit-btn save-btn" @click.stop="saveMetaEdit">
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="slide-up">
      <div v-if="activeTab === 'technical'" class="info-panel technical-panel" @click.stop>
        <div class="panel-content">
          <div v-if="imageWidth && imageHeight" class="info-item">
            <span class="info-label">DIMENSIONS:</span>
            <span class="info-value">{{ imageWidth }} × {{ imageHeight }} px</span>
          </div>
          <div v-if="imageSize" class="info-item">
            <span class="info-label">FILE SIZE:</span>
            <span class="info-value">{{ formatFileSize(imageSize) }}</span>
          </div>
          <div v-if="imageFormat" class="info-item">
            <span class="info-label">FORMAT:</span>
            <span class="info-value">{{ imageFormat }}</span>
          </div>
          <div v-if="imageColorDepth" class="info-item">
            <span class="info-label">COLOR DEPTH:</span>
            <span class="info-value">{{ imageColorDepth }}</span>
          </div>
        </div>
      </div>
    </transition>

    <transition name="slide-up">
      <div v-if="activeTab === 'modify'" class="info-panel modify-panel" @click.stop>
        <div class="panel-content">
          <div class="modify-tools">
            <button class="modify-tool-btn" @click.stop="handleCrop">
              <v-icon size="small">mdi-crop</v-icon>
              Crop
            </button>
            <button class="modify-tool-btn" @click.stop="handleEnhance">
              <v-icon size="small">mdi-auto-fix</v-icon>
              Enhance
            </button>
            <button class="modify-tool-btn" @click.stop="handleResize">
              <v-icon size="small">mdi-resize</v-icon>
              Resize
            </button>
            <button class="modify-tool-btn" @click.stop="handleComfyUI">
              <v-icon size="small">mdi-robot</v-icon>
              ComfyUI
            </button>
          </div>
          <div class="comfy-note">
            <v-icon size="small" color="info">mdi-information</v-icon>
            <span>ComfyUI workflows coming soon</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- Image path line (was the standalone card's footer; the shell footer
         shows duration, so we surface the path here under the image). -->
    <div class="image-path-row">
      <v-icon size="small" class="path-icon">mdi-file-image</v-icon>
      <span class="path-text">{{ imageUrl || 'No image path' }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';

const props = defineProps({
  cueData: {
    type: Object,
    required: true,
    default: () => ({})
  },
  // Read-only render (version preview): hide edit affordances (todo #35).
  readonly: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['modify', 'update-meta']);

// ── Reactive state ──
const imageError = ref(false);
const imageLoaded = ref(false);
const imageLoading = ref(false);
const activeTab = ref(null);
const imageWidth = ref(null);
const imageHeight = ref(null);
const imageSize = ref(null);
const imageFormat = ref(null);
const imageColorDepth = ref('24-bit');
const tags = ref('');
// Editable meta fields
const editableDescription = ref('');
const editableCredit = ref('');
const editableCaption = ref('');
const editableDuration = ref('');
const editableTags = ref('');

// ── Computed ──
const imageUrl = computed(() => {
  // Check multiple possible locations for the image URL.
  // MediaURL gets parsed to lowercase 'mediaurl' by cueParser.
  return props.cueData.rawData?.mediaurl ||
         props.cueData.rawData?.mediaUrl ||
         props.cueData.mediaUrl ||
         props.cueData.mediaurl ||
         props.cueData.imageSrc ||
         props.cueData.rawData?.imageSrc ||
         '';
});

// ── Watch ──
watch(imageUrl, (newUrl, oldUrl) => {
  if (newUrl !== oldUrl) {
    imageLoaded.value = false;
    imageError.value = false;
    imageLoading.value = !!newUrl;
  }
}, { immediate: true });

// ── Methods ──
function resolveImagePath(imagePath) {
  if (!imagePath) return '';
  if (imagePath.startsWith('http')) return imagePath;
  if (imagePath.startsWith('/')) return imagePath;
  return `/${imagePath}`;
}

function handleImageError() {
  imageError.value = true;
  imageLoaded.value = false;
  imageLoading.value = false;
}

function handleImageLoad(event) {
  imageError.value = false;
  imageLoaded.value = true;
  imageLoading.value = false;

  const img = event.target;
  imageWidth.value = img.naturalWidth;
  imageHeight.value = img.naturalHeight;

  const url = imageUrl.value;
  if (url) {
    const extension = url.split('.').pop().split('?')[0].toUpperCase();
    imageFormat.value = extension;
  }

  fetchImageMetadata();
}

async function fetchImageMetadata() {
  try {
    const response = await fetch(resolveImagePath(imageUrl.value), { method: 'HEAD' });
    if (response.ok) {
      const contentLength = response.headers.get('Content-Length');
      if (contentLength) {
        imageSize.value = parseInt(contentLength, 10);
      }
    }
  } catch (error) {
    console.log('Could not fetch image metadata:', error);
  }
}

function toggleTab(tab) {
  if (activeTab.value === tab) {
    activeTab.value = null;
  } else {
    activeTab.value = tab;
    if (tab === 'meta') {
      nextTick(() => initializeMetaFields());
    }
  }
}

function initializeMetaFields() {
  editableDescription.value = props.cueData.rawData?.description || '';
  editableCredit.value = props.cueData.rawData?.credit || '';
  editableCaption.value = props.cueData.rawData?.caption || '';
  editableDuration.value = props.cueData.rawData?.duration || props.cueData.duration || '00:00:15:00';
  editableTags.value = tags.value || '';
}

function saveMetaEdit() {
  emit('update-meta', {
    cueData: props.cueData,
    metadata: {
      description: editableDescription.value,
      credit: editableCredit.value,
      caption: editableCaption.value,
      duration: editableDuration.value,
      tags: editableTags.value
    }
  });
  activeTab.value = null;
}

function cancelMetaEdit() {
  activeTab.value = null;
  nextTick(() => initializeMetaFields());
}

function formatFileSize(bytes) {
  if (!bytes) return 'Unknown';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function handleCrop()    { emit('modify', { action: 'crop', cueData: props.cueData }); }
function handleEnhance() { emit('modify', { action: 'enhance', cueData: props.cueData }); }
function handleResize()  { emit('modify', { action: 'resize', cueData: props.cueData }); }
function handleComfyUI() { emit('modify', { action: 'comfyui', cueData: props.cueData }); }
</script>

<style scoped>
/* Image content styles ported verbatim from the former ImageCueCard.vue so the
   IMG body renders identically inside the shared shell. */
.image-container {
  position: relative;
  width: 100%;
  background: #1a1a1a;
}

.image-loading,
.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 160px;
  color: #ccc;
}

.loading-text,
.error-text {
  font-size: 13px;
}

.cue-image {
  display: block;
  width: 100%;
  height: auto;
  max-height: 480px;
  object-fit: contain;
  background: #1a1a1a;
}

.tab-buttons {
  display: flex;
  gap: 2px;
  background: rgba(0, 0, 0, 0.6);
  padding: 4px;
}

.tab-button {
  flex: 1;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #ddd;
  background: rgba(255, 255, 255, 0.08);
  border: none;
  cursor: pointer;
  transition: background 0.15s ease;
}

.tab-button:hover {
  background: rgba(255, 255, 255, 0.18);
}

.tab-button.active {
  background: rgba(255, 255, 255, 0.28);
  color: #fff;
}

.info-panel {
  background: rgba(20, 20, 20, 0.96);
  color: #eee;
  padding: 12px;
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.info-label {
  color: #9e9e9e;
  font-weight: 600;
}

.info-value {
  color: #fff;
}

.edit-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.edit-label {
  font-size: 11px;
  font-weight: 600;
  color: #9e9e9e;
}

.edit-input,
.edit-textarea {
  width: 100%;
  padding: 5px 8px;
  font-size: 13px;
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.edit-textarea {
  resize: vertical;
}

.edit-actions,
.modify-tools {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.edit-btn,
.modify-tool-btn {
  flex: 1;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

.modify-tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

.modify-tool-btn:hover {
  background: rgba(255, 255, 255, 0.22);
}

.save-btn {
  color: #fff;
  background: #2e7d32;
}

.cancel-btn {
  color: #fff;
  background: #616161;
}

.comfy-note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 11px;
  color: #9e9e9e;
}

.image-path-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  font-size: 11px;
  color: #aaa;
  background: rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

.path-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Slide-up transition for the panels */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.2s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
