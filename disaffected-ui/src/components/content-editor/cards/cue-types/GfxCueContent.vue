<template>
  <div class="fsq-preview-layout">
    <!-- Left Side: 65% - Live Preview with animated background -->
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
        <!-- Black bar overlay -->
        <div class="fsq-preview-black-bar"></div>

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

        <!-- Standard GFX content overlay -->
        <div v-else class="gfx-preview-overlay">
          <div v-if="cueData.gfxTitle" class="gfx-overlay-title" :style="{ textAlign: cueData.titleAlign || 'center' }">{{ cueData.gfxTitle }}</div>
          <div v-if="cueData.body" class="gfx-overlay-body" :style="{ textAlign: cueData.textAlign || 'center' }">{{ formatGfxBody(cueData.body) }}</div>
          <ul v-if="gfxActiveListItems.length" class="gfx-overlay-list">
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

    <!-- Right Side: 35% - Compact Controls -->
    <div class="fsq-controls-side">
      <!-- Generate/Regenerate Button -->
      <v-btn
        block
        size="small"
        :variant="hasGfxAsset ? 'outlined' : 'elevated'"
        :color="hasGfxAsset ? 'primary' : 'success'"
        @click.stop="$emit('generate-gfx')"
        :loading="generatingGfx"
        class="mb-2"
      >
        <v-icon size="small" start>{{ hasGfxAsset ? 'mdi-sync' : 'mdi-creation' }}</v-icon>
        {{ hasGfxAsset ? 'Regenerate' : 'Generate GFX' }}
      </v-btn>

      <!-- Edit GFX Button -->
      <v-btn
        block
        size="small"
        variant="text"
        color="primary"
        class="mb-2"
        @click.stop="$emit('edit-gfx', cueData)"
      >
        <v-icon size="small" start>mdi-pencil</v-icon>
        Edit GFX
      </v-btn>

      <!-- Download PNG Button -->
      <v-btn
        v-if="hasGfxAsset"
        block
        size="small"
        variant="text"
        color="deep-purple"
        class="mb-2"
        @click.stop="$emit('download-gfx-png')"
      >
        <v-icon size="small" start>mdi-download</v-icon>
        Download PNG
      </v-btn>

      <!-- GFX Generation Status -->
      <div v-if="gfxGenerationStatus" class="fsq-status-chip mb-2">
        <v-chip size="x-small" :color="gfxStatusChipColor" variant="tonal">
          <v-icon size="x-small" start :class="{ 'mdi-spin': gfxGenerationStatus === 'generating' }">{{ gfxStatusChipIcon }}</v-icon>
          {{ gfxStatusText }}
        </v-chip>
      </div>

      <!-- Compact Style Controls -->
      <div class="fsq-compact-controls">
        <!-- Font Size -->
        <div class="fsq-control-row fsq-slider-row">
          <span class="fsq-control-label">Size</span>
          <v-slider
            v-model="localGfxFontSize"
            :min="10"
            :max="50"
            :step="1"
            density="compact"
            hide-details
            thumb-label
            class="fsq-control-slider"
            @update:model-value="emitGfxParamChange('fontSize', $event + 'px')"
          />
          <span class="fsq-slider-value">{{ localGfxFontSize }}px</span>
        </div>

        <!-- Font Family -->
        <div class="fsq-control-row">
          <span class="fsq-control-label">Font</span>
          <v-select
            v-model="localGfxFontFamily"
            :items="fontFamilyOptions"
            density="compact"
            hide-details
            variant="outlined"
            class="fsq-control-input"
            @update:model-value="emitGfxParamChange('fontFamily', $event)"
          />
        </div>

        <!-- Alignment -->
        <div class="fsq-control-row">
          <span class="fsq-control-label">Align</span>
          <v-btn-toggle
            v-model="localGfxAlignment"
            mandatory
            density="compact"
            color="primary"
            class="fsq-control-toggle"
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
      </div>

      <!-- Delete Button -->
      <v-btn
        block
        size="default"
        variant="tonal"
        color="error"
        @click.stop="$emit('delete')"
        class="mt-2"
      >
        <v-icon size="small" start>mdi-delete</v-icon>
        Delete
      </v-btn>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GfxCueContent',
  emits: ['edit-gfx', 'delete', 'generate-gfx', 'download-gfx-png', 'update-meta'],
  props: {
    cueData: {
      type: Object,
      required: true
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
  },
  data() {
    return {
      localGfxFontSize: parseInt(this.cueData?.fontSize) || 25,
      localGfxFontFamily: this.cueData?.fontFamily || 'sans-serif',
      localGfxAlignment: this.cueData?.textAlign || 'center',
      fontFamilyOptions: [
        { title: 'Sans-Serif', value: 'sans-serif' },
        { title: 'Serif', value: 'serif' }
      ]
    };
  },
  computed: {
    gfxStatusText() {
      const map = { queued: 'Queued', generating: 'Generating...', completed: 'Complete', failed: 'Failed' };
      return map[this.gfxGenerationStatus] || '';
    },
    gfxStatusChipColor() {
      const map = { queued: 'blue-grey', generating: 'amber', completed: 'success', failed: 'error' };
      return map[this.gfxGenerationStatus] || 'grey';
    },
    gfxStatusChipIcon() {
      const map = { queued: 'mdi-clock-outline', generating: 'mdi-cog', completed: 'mdi-check-circle', failed: 'mdi-alert-circle' };
      return map[this.gfxGenerationStatus] || 'mdi-help-circle';
    }
  },
  methods: {
    formatMetric(n) {
      if (!n) return '0';
      if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
      if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
      return String(n);
    },
    formatGfxBody(body) {
      if (!body) return '';
      const unescaped = body.replace(/\\n/g, '\n');
      return unescaped.length > 200 ? unescaped.substring(0, 200) + '...' : unescaped;
    },
    emitGfxParamChange(paramName, value) {
      console.log(`GFX param changed: ${paramName} = ${value}`);
      this.$emit('update-meta', {
        assetId: this.cueData.assetId,
        field: paramName,
        value: value
      });
    }
  },
  expose: ['localGfxFontSize', 'localGfxFontFamily', 'localGfxAlignment']
};
</script>

<style scoped>
.fsq-preview-layout {
  display: flex;
  gap: 12px;
  width: 100%;
  padding: 8px;
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
  justify-content: flex-start;
  padding: 4% 8%;
  z-index: 3;
  box-sizing: border-box;
  overflow: hidden;
}

.gfx-overlay-title {
  color: white;
  font-weight: bold;
  font-size: 1.1vw;
  margin-bottom: 0.4em;
  text-align: center;
}

.gfx-overlay-body {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.85vw;
  line-height: 1.4;
  white-space: pre-wrap;
  text-align: center;
}

.gfx-overlay-list {
  list-style: disc;
  padding-left: 1.5em;
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.75vw;
  line-height: 1.5;
}

.gfx-overlay-list li {
  margin-bottom: 0.2em;
}

.gfx-overlay-empty {
  color: rgba(255, 255, 255, 0.3);
  font-style: italic;
  font-size: 0.9vw;
  text-align: center;
  margin-top: 2em;
}

/* Controls side */
.fsq-controls-side {
  flex: 0 0 35%;
  display: flex;
  flex-direction: column;
}

.fsq-status-chip {
  display: flex;
  justify-content: center;
}

.fsq-compact-controls {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(0, 0, 0, 0.02);
  padding: 8px;
  border-radius: 4px;
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

.fsq-control-input {
  flex: 1;
}

.fsq-control-input :deep(.v-field__input) {
  font-size: 12px;
  min-height: 28px;
  padding: 4px 8px;
}

.fsq-control-input :deep(.v-field__append-inner) {
  padding-top: 2px;
}

.fsq-control-toggle {
  flex: 1;
}

.fsq-slider-row {
  flex-wrap: nowrap;
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
</style>
