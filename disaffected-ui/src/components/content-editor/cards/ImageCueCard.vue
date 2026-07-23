<template>
  <v-card
    class="cue-card image-cue-card"
    :class="[
      { 'selected': selected },
      getAnalysisClass
    ]"
    :style="getCardStyle"
    variant="elevated"
    @click="$emit('select')"
  >
    <!-- Card Header -->
    <v-card-title class="cue-card-header" :style="headerStyle">
      <v-icon size="small" class="drag-handle" style="cursor: grab; margin-right: 8px; color: white;">mdi-drag-vertical</v-icon>
      <div class="cue-type-badge" :style="badgeStyle">
        {{ cueData.type }}
      </div>
      <div class="cue-slug-section">
        <div class="cue-slug-text">
          {{ cueData.slug || 'No Slug' }}
        </div>
        <div v-if="cueData.rawData?.assetid" class="cue-asset-id-header">
          {{ cueData.rawData.assetid }}
        </div>
      </div>
      <v-spacer></v-spacer>
      <div class="cue-actions">
        <v-btn
          size="small"
          variant="text"
          @click.stop="$emit('edit')"
          class="action-btn"
          color="white"
        >
          Edit
        </v-btn>
        <v-btn
          size="small"
          variant="text"
          @click.stop="$emit('delete')"
          class="action-btn delete-btn"
          color="white"
        >
          Delete
        </v-btn>
      </div>
    </v-card-title>

    <!-- Card Content -->
    <v-card-text class="cue-card-content">
      <!-- Image Display -->
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
        <div v-if="imageUrl && imageLoaded" class="tab-buttons">
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
      </div>
    </v-card-text>

    <!-- Card Footer -->
    <v-card-actions class="cue-card-footer" :style="headerStyle">
      <v-spacer></v-spacer>
      <div class="image-path">
        <v-icon size="small" class="path-icon">mdi-file-image</v-icon>
        <span class="path-text">{{ imageUrl || 'No image path' }}</span>
      </div>
    </v-card-actions>

  </v-card>
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '../../../utils/themeColorMap.js';

export default {
  name: 'ImageCueCard',
  emits: ['select', 'edit', 'delete', 'modify', 'update-meta'],
  props: {
    cueData: {
      type: Object,
      required: true,
      default: () => ({})
    },
    selected: {
      type: Boolean,
      default: false
    },
    orderNumber: {
      type: [String, Number],
      default: null
    }
  },
  data() {
    return {
      imageError: false,
      imageLoaded: false,
      imageLoading: false,
      activeTab: null,
      imageWidth: null,
      imageHeight: null,
      imageSize: null,
      imageFormat: null,
      imageColorDepth: '24-bit',
      tags: '',
      // Editable meta fields
      editableDescription: '',
      editableCredit: '',
      editableCaption: '',
      editableDuration: '',
      editableTags: ''
    };
  },
  computed: {
    imageUrl() {
      // Check multiple possible locations for the image URL
      // MediaURL field gets parsed to 'mediaurl' (all lowercase) by cueParser
      return this.cueData.rawData?.mediaurl ||
             this.cueData.rawData?.mediaUrl ||
             this.cueData.mediaUrl ||
             this.cueData.mediaurl ||
             this.cueData.imageSrc ||
             this.cueData.rawData?.imageSrc ||
             '';
    },

    cueTypeColor() {
      if (!this.cueData.type) return 'grey';
      const colorName = getColorValue(this.cueData.type.toLowerCase());
      return resolveVuetifyColor(colorName);
    },

    cueTypeStyle() {
      const backgroundColor = this.cueTypeColor;
      return {
        backgroundColor: backgroundColor,
        color: 'white'
      };
    },

    headerStyle() {
      const backgroundColor = this.cueTypeColor;
      return {
        backgroundColor: backgroundColor,
        color: 'white'
      };
    },

    badgeStyle() {
      const baseColor = this.cueTypeColor;
      // Only lighten if we have a valid hex color string
      const lighterColor = (typeof baseColor === 'string' && baseColor.startsWith('#'))
        ? this.lightenColor(baseColor, 20)
        : baseColor;
      return {
        backgroundColor: lighterColor || '#666',
        color: 'white'
      };
    },

    /**
     * Get CSS class for analysis state
     */
    getAnalysisClass() {
      const state = this.cueData?.analysisState;
      if (state === 'analyzing') return 'cue-analyzing';
      if (state === 'needs_review') return 'cue-needs-review';
      return '';
    },

    /**
     * Get card style including analysis state border
     */
    getCardStyle() {
      const state = this.cueData?.analysisState;

      if (state === 'analyzing') {
        // Purple 7px border while analyzing
        return {
          borderColor: '#9C27B0',
          borderWidth: '7px',
          borderStyle: 'solid'
        };
      } else if (state === 'needs_review') {
        // Red 7px border when needs review
        return {
          borderColor: '#D32F2F',
          borderWidth: '7px',
          borderStyle: 'solid'
        };
      }

      // Default: use cue type color with 4px border
      return {
        borderColor: this.cueTypeColor,
        borderWidth: '4px',
        borderStyle: 'solid'
      };
    }
  },
  methods: {
    resolveImagePath(imagePath) {
      if (!imagePath) return '';

      // Handle full URLs
      if (imagePath.startsWith('http')) {
        return imagePath;
      }

      // Handle absolute paths
      if (imagePath.startsWith('/')) {
        return imagePath;
      }

      // For relative paths, ensure they start with /
      return `/${imagePath}`;
    },

    handleImageError() {
      this.imageError = true;
      this.imageLoaded = false;
      this.imageLoading = false;
    },

    handleImageLoad(event) {
      this.imageError = false;
      this.imageLoaded = true;
      this.imageLoading = false;

      // Extract image dimensions from the loaded image
      const img = event.target;
      this.imageWidth = img.naturalWidth;
      this.imageHeight = img.naturalHeight;

      // Extract format from URL
      const url = this.imageUrl;
      if (url) {
        const extension = url.split('.').pop().split('?')[0].toUpperCase();
        this.imageFormat = extension;
      }

      // Try to get file size (requires additional fetch)
      this.fetchImageMetadata();
    },

    async fetchImageMetadata() {
      try {
        const response = await fetch(this.resolveImagePath(this.imageUrl), { method: 'HEAD' });
        if (response.ok) {
          const contentLength = response.headers.get('Content-Length');
          if (contentLength) {
            this.imageSize = parseInt(contentLength, 10);
          }
        }
      } catch (error) {
        console.log('Could not fetch image metadata:', error);
      }
    },

    toggleTab(tab) {
      // Toggle tab: close if already open, open if closed
      if (this.activeTab === tab) {
        this.activeTab = null;
      } else {
        this.activeTab = tab;

        // Initialize editable fields when opening meta tab
        // Use nextTick to break any potential reactivity loops
        if (tab === 'meta') {
          this.$nextTick(() => {
            this.initializeMetaFields();
          });
        }
      }
    },

    initializeMetaFields() {
      // Load current values into editable fields
      this.editableDescription = this.cueData.rawData?.description || '';
      this.editableCredit = this.cueData.rawData?.credit || '';
      this.editableCaption = this.cueData.rawData?.caption || '';
      this.editableDuration = this.cueData.rawData?.duration || '';
      this.editableTags = this.tags || '';
    },

    saveMetaEdit() {
      // Emit update event with new metadata
      const updatedMeta = {
        description: this.editableDescription,
        credit: this.editableCredit,
        caption: this.editableCaption,
        duration: this.editableDuration,
        tags: this.editableTags
      };

      this.$emit('update-meta', {
        cueData: this.cueData,
        metadata: updatedMeta
      });

      // Close the tab after saving
      this.activeTab = null;
    },

    cancelMetaEdit() {
      // Close tab first, then reset values
      this.activeTab = null;
      this.$nextTick(() => {
        this.initializeMetaFields();
      });
    },

    formatFileSize(bytes) {
      if (!bytes) return 'Unknown';

      const units = ['B', 'KB', 'MB', 'GB'];
      let size = bytes;
      let unitIndex = 0;

      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }

      return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
    },

    handleCrop() {
      console.log('Crop tool clicked');
      this.$emit('modify', { action: 'crop', cueData: this.cueData });
    },

    handleEnhance() {
      console.log('Enhance tool clicked');
      this.$emit('modify', { action: 'enhance', cueData: this.cueData });
    },

    handleResize() {
      console.log('Resize tool clicked');
      this.$emit('modify', { action: 'resize', cueData: this.cueData });
    },

    handleComfyUI() {
      console.log('ComfyUI tool clicked');
      this.$emit('modify', { action: 'comfyui', cueData: this.cueData });
    },

    lightenColor(color, percent) {
      // Convert hex to RGB
      let hex = color.replace('#', '');

      // Handle short hex
      if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
      }

      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);

      // Lighten each component
      const newR = Math.min(255, Math.round(r + (255 - r) * (percent / 100)));
      const newG = Math.min(255, Math.round(g + (255 - g) * (percent / 100)));
      const newB = Math.min(255, Math.round(b + (255 - b) * (percent / 100)));

      // Convert back to hex
      const toHex = (n) => {
        const hex = n.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
      };

      return `#${toHex(newR)}${toHex(newG)}${toHex(newB)}`;
    }
  },
  watch: {
    imageUrl: {
      immediate: true,
      handler(newUrl, oldUrl) {
        // Reset states when URL changes
        if (newUrl !== oldUrl) {
          this.imageLoaded = false;
          this.imageError = false;
          this.imageLoading = !!newUrl;
        }
      }
    }
  }
};
</script>

<style scoped>
.cue-card {
  margin: 8px 0;
  border: 4px solid;
  transition: all 0.2s ease;
  cursor: pointer;
  border-radius: 0 !important;
}

.cue-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cue-card.selected {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.image-cue-card {
  max-width: 75%;
  width: 75%;
  /* Margins removed - alignment now controlled by parent .cue-segment flex container */
}

/* Header Styling */
.cue-card-header {
  padding: 0 16px 0 0 !important;
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
  display: flex;
  align-items: stretch;
  gap: 12px;
  font-family: Helvetica, Arial, sans-serif;
  min-height: 48px;
}

.cue-type-badge {
  padding: 2px 16px;
  border-radius: 0;
  font-weight: normal;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-top: 0;
  border-bottom: 0;
  border-left: 0;
  border-right: 4px solid white;
  display: flex;
  align-items: center;
  margin: 0;
}

.cue-slug-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cue-slug-text {
  font-weight: bold;
  font-size: 1.2rem;
  font-family: Helvetica, Arial, sans-serif;
}

.cue-asset-id-header {
  font-size: 0.75rem;
  font-weight: normal;
  color: white;
  opacity: 0.9;
  font-family: 'Courier New', Courier, monospace;
}

.cue-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  opacity: 0.7;
}

.action-btn:hover {
  opacity: 1;
}

.delete-btn:hover {
  color: rgb(var(--v-theme-error));
}

/* Content Styling */
.cue-card-content {
  padding: 0 !important;
}

.image-container {
  position: relative;
  margin: 0;
  padding: 0;
  border-radius: 0;
  overflow: hidden;
  line-height: 0;
}

.cue-image {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 0;
  box-shadow: none;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.error-text {
  margin-top: 8px;
  font-size: 0.8rem;
}

.image-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  gap: 16px;
  background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
  min-height: 200px;
}

.image-loading .loading-text {
  font-size: 1rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
  letter-spacing: 0.5px;
}

.loading-dots::after {
  content: '';
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0%, 24% { content: ''; }
  25%, 49% { content: '.'; }
  50%, 74% { content: '..'; }
  75%, 100% { content: '...'; }
}

/* Tab Buttons */
.tab-buttons {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: 0;
  z-index: 10;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.5), transparent);
  padding: 8px 0 0 0;
}

.tab-button {
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  padding: 12px 32px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s ease;
  font-family: Helvetica, Arial, sans-serif;
  border-top: 2px solid transparent;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.tab-button:first-child {
  border-left: none;
  border-top-left-radius: 4px;
}

.tab-button:last-child {
  border-right: none;
  border-top-right-radius: 4px;
}

.tab-button:hover {
  background-color: rgba(0, 0, 0, 0.8);
  border-top-color: rgba(255, 255, 255, 0.3);
}

.tab-button.active {
  background-color: rgba(0, 0, 0, 0.9);
  border-top-color: white;
}

/* Info Panels */
.info-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: rgba(0, 0, 0, 0.9);
  border-top: 2px solid white;
  max-height: 60%;
  overflow-y: auto;
  z-index: 9;
}

.panel-content {
  padding: 16px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.75rem;
  line-height: 1.6;
  color: white;
}

.info-item {
  margin-bottom: 8px;
}

.info-label {
  font-weight: bold;
  display: inline;
  margin-right: 6px;
  color: rgba(255, 255, 255, 0.9);
}

.info-value {
  font-weight: normal;
  display: inline;
  color: rgba(255, 255, 255, 0.8);
}

/* Modify Tools */
.modify-tools {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.modify-tool-btn {
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-family: Helvetica, Arial, sans-serif;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.modify-tool-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
}

.comfy-note {
  display: flex;
  align-items: center;
  gap: 6px;
  font-style: italic;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 8px;
}

/* Slide Up Animation */
.slide-up-enter-active {
  transition: transform 0.3s ease-out, opacity 0.3s ease-out;
}

.slide-up-leave-active {
  transition: transform 0.3s ease-in, opacity 0.3s ease-in;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* Editable Fields */
.edit-field {
  margin-bottom: 12px;
}

.edit-label {
  display: block;
  font-weight: bold;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
  font-family: 'Courier New', Courier, monospace;
}

.edit-input,
.edit-textarea {
  width: 100%;
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 6px 8px;
  border-radius: 3px;
  font-size: 0.75rem;
  font-family: 'Courier New', Courier, monospace;
  transition: all 0.2s ease;
}

.edit-input:focus,
.edit-textarea:focus {
  outline: none;
  background-color: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.5);
}

.edit-textarea {
  resize: vertical;
  min-height: 40px;
}

.edit-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.edit-btn {
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  font-family: Helvetica, Arial, sans-serif;
}

.cancel-btn {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.cancel-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.save-btn {
  background-color: rgba(33, 150, 243, 0.8);
  color: white;
  border: 1px solid rgba(33, 150, 243, 1);
}

.save-btn:hover {
  background-color: rgba(33, 150, 243, 1);
}

/* Info Styling */
.cue-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cue-slug,
.cue-description,
.cue-asset-id,
.cue-duration {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.info-icon {
  opacity: 0.7;
  flex-shrink: 0;
}

.slug-text {
  font-weight: 500;
  color: rgb(var(--v-theme-primary));
}

.description-text {
  color: rgba(var(--v-theme-on-surface), 0.8);
  line-height: 1.4;
}

.asset-id-text {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.duration-text {
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Footer Styling */
.cue-card-footer {
  padding: 6px 16px !important;
  min-height: 0;
}

.image-path {
  display: flex;
  align-items: center;
  gap: 8px;
}

.path-icon {
  color: white;
  opacity: 0.9;
}

.path-text {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.7rem;
  color: white;
  opacity: 0.9;
  word-break: break-all;
  flex: 1;
}

/* Responsive Design */
@media (max-width: 600px) {
  .cue-card-header {
    padding: 8px 12px !important;
  }

  .cue-card-content {
    padding: 12px !important;
  }

  .cue-image {
    max-height: 200px;
  }
}
</style>