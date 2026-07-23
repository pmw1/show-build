<template>
  <v-card
    class="cue-card placeholder-cue-card"
    :class="[
      { 'selected': selected },
      { 'rif-card-align': cueData.type === 'RIF' },
      { 'cue-complete': cueStatus === 'complete' },
      { 'cue-needs-attention': cueStatus === 'needs_attention' },
      { 'cue-urgent-attention': cueStatus === 'urgent_attention' },
      { 'cue-collapsed': collapsed },
      getAnalysisClass
    ]"
    :style="cardStyleWithStatus"
    variant="elevated"
    @click="$emit('select')"
  >
    <!-- Card Header — the entire header is the double-click hotzone for collapse -->
    <v-card-title class="cue-card-header" :style="headerStyleWithStatus" @dblclick.stop="$emit('toggle-collapsed')">
      <v-icon size="small" class="drag-handle" :color="headerTextColor" style="cursor: grab; margin-right: 8px;">mdi-drag-vertical</v-icon>
      <v-btn
        icon
        size="x-small"
        variant="text"
        class="collapse-toggle"
        :color="headerTextColor"
        tabindex="-1"
        :title="collapsed ? 'Expand cue' : 'Collapse cue'"
        @click.stop="$emit('toggle-collapsed')"
      >
        <v-icon size="small">{{ collapsed ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
      </v-btn>
      <div class="cue-type-badge" :style="badgeStyle">
        {{ cueTypeBadgeLabel }}
      </div>

      <!-- Enumerator Badge (if present) -->
      <div v-if="cueData.enumerator" class="cue-enumerator-badge">
        #{{ cueData.enumerator }}
      </div>

      <div class="cue-title-text">
        {{ formatCueTitle }}
      </div>
      <v-spacer></v-spacer>

      <!-- RIF: Show action buttons and duration in header -->
      <template v-if="cueData.type === 'RIF'">
        <div v-if="!readonly" class="cue-actions">
          <v-btn
            icon
            size="small"
            variant="text"
            :color="headerTextColor"
            @click.stop="$emit('edit')"
            class="action-btn"
            tabindex="-1"
          >
            <v-icon size="small">mdi-pencil</v-icon>
            <v-tooltip activator="parent" location="top">Edit Cue</v-tooltip>
          </v-btn>
          <v-btn
            icon
            size="small"
            variant="text"
            :color="headerTextColor"
            @click.stop="$emit('delete')"
            class="action-btn delete-btn"
            tabindex="-1"
          >
            <v-icon size="small">mdi-delete</v-icon>
            <v-tooltip activator="parent" location="top">Delete Cue</v-tooltip>
          </v-btn>
        </div>
        <div class="duration-display-header">
          <v-icon size="small" :color="headerTextColor">mdi-timer-outline</v-icon>
          <span class="duration-text-header">{{ cueData.duration || '00:00:00:00' }}</span>
        </div>
      </template>

      <!-- Non-RIF/GFX: Show action buttons in header (GFX has its own controls) -->
      <div v-if="!readonly && cueData.type !== 'RIF' && cueData.type !== 'GFX'" class="cue-actions">
        <v-btn
          icon
          size="small"
          variant="text"
          :color="headerTextColor"
          @click.stop="$emit('edit')"
          class="action-btn"
        >
          <v-icon size="small">mdi-pencil</v-icon>
          <v-tooltip activator="parent" location="top">Edit Cue</v-tooltip>
        </v-btn>
        <v-btn
          icon
          size="small"
          variant="text"
          :color="headerTextColor"
          @click.stop="$emit('delete')"
          class="action-btn delete-btn"
        >
          <v-icon size="small">mdi-delete</v-icon>
          <v-tooltip activator="parent" location="top">Delete Cue</v-tooltip>
        </v-btn>
      </div>
    </v-card-title>

    <!-- Card Content (RIF is header-only by design — it has no body to collapse) -->
    <v-card-text v-if="cueData.type !== 'RIF' && !collapsed" class="cue-card-content">
      <!-- FSQ-specific Display - Delegated to FsqCueContent.
           Render for ANY FSQ cue, even before a quote is entered. The old
           "&& cueData.quote" guard made a quote-less FSQ fall through to the
           generic "Display not yet implemented" placeholder, which read as the
           cue "disappearing" on reload. FsqCueContent handles an empty quote
           (renders an empty preview box / edit affordance). -->
      <FsqCueContent
        v-if="cueData.type === 'FSQ'"
        ref="fsqContentRef"
        :cue-data="cueData"
        :readonly="readonly"
        :fsq-dirty="fsqDirty"
        :generatingPNG="generatingPNG"
        :fsq-generation-status="fsqGenerationStatus"
        :fsq-background-video-url="fsqBackgroundVideoUrl"
        @edit-fsq="$emit('edit-fsq', $event)"
        @delete="$emit('delete')"
        @generate-png="handleGeneratePNG"
        @download-png="downloadFsqPNG"
        @view-png="openFsqFullResModal"
        @open-fsq-preview="openFsqPreviewModal"
        @update-meta="handleChildUpdateMeta"
        @apply-all-fsq="$emit('apply-all-fsq', $event)"
      />

      <!-- SOT Display - Delegated to SotCueContent -->
      <SotCueContent
        v-else-if="cueData.type?.toUpperCase() === 'SOT'"
        :cue-data="cueData"
        variant="SOT"
        :job-status="jobStatus"
        :sot-thumbnail-url="sotThumbnailUrl"
        :sot-thumbnail-options="sotThumbnailOptions"
        :current-sot-thumbnail-url="currentSotThumbnailUrl"
        :sot-video-url="sotVideoUrl"
        :sot-transcription="sotTranscription"
        :sot-outcue="sotOutcue"
        :is-job-completed="isJobCompleted"
        :display-duration="displayDuration"
        :display-video-path="displayVideoPath"
        :display-processing-status="displayProcessingStatus"
        :current-thumbnail-sharpness="currentThumbnailSharpness"
        :sharpness-color="sharpnessColor"
        :initial-thumbnail-index="currentThumbnailIndex"
        @open-sot-preview="openSotPreviewModal"
        @update-meta="handleChildUpdateMeta"
      />

      <!-- VO Display - Reuses SotCueContent with VO variant -->
      <SotCueContent
        v-else-if="cueData.type?.toUpperCase() === 'VO'"
        :cue-data="cueData"
        variant="VO"
        :job-status="jobStatus"
        :sot-thumbnail-url="sotThumbnailUrl"
        :sot-thumbnail-options="sotThumbnailOptions"
        :current-sot-thumbnail-url="currentSotThumbnailUrl"
        :sot-video-url="sotVideoUrl"
        :is-job-completed="isJobCompleted"
        :display-duration="displayDuration"
        :display-video-path="displayVideoPath"
        :display-processing-status="displayProcessingStatus"
        :initial-thumbnail-index="currentThumbnailIndex"
        @open-sot-preview="openSotPreviewModal"
        @update-meta="handleChildUpdateMeta"
      />

      <!-- GFX Display - Delegated to GfxCueContent -->
      <GfxCueContent
        v-else-if="cueData.type === 'GFX'"
        ref="gfxContentRef"
        :cue-data="cueData"
        :readonly="readonly"
        :has-gfx-asset="hasGfxAsset"
        :generating-gfx="generatingGfx"
        :gfx-generation-status="gfxGenerationStatus"
        :fsq-background-video-url="fsqBackgroundVideoUrl"
        :xpost-data="xpostData"
        :gfx-active-list-items="gfxActiveListItems"
        :gfx-image-url="gfxCardImageUrl"
        @edit-gfx="$emit('edit-gfx', $event)"
        @delete="$emit('delete')"
        @generate-gfx="handleGenerateGfx"
        @download-gfx-png="downloadGfxPNG"
        @open-gfx-preview="showGfxPreviewModal = true"
        @update-meta="handleChildUpdateMeta"
        @apply-all-gfx="$emit('apply-all-gfx', $event)"
      />

      <!-- NOTE (Directors Note) Display -->
      <div v-else-if="cueData.type === 'NOTE' || cueData.type === 'DIR'" class="dir-container">
        <div class="dir-content">
          <div class="dir-icon-section">
            <v-icon size="32" :color="cueTypeColor">mdi-note-text</v-icon>
          </div>
          <div class="dir-note-section">
            <div v-if="cueData.noteText" class="dir-note-text">
              {{ cueData.noteText }}
            </div>
            <div v-else class="dir-no-content">
              <span style="color: grey;">No note text provided</span>
            </div>
          </div>
        </div>
      </div>

      <!-- IMG Display - Delegated to ImageCueContent (#49: folded in from the
           former standalone ImageCueCard so every cue renders through this shell). -->
      <ImageCueContent
        v-else-if="cueData.type === 'IMG'"
        :cue-data="cueData"
        :readonly="readonly"
        @modify="$emit('modify', $event)"
        @update-meta="handleChildUpdateMeta"
      />

      <!-- Generic Placeholder Display for other cue types -->
      <div v-else class="placeholder-container">
        <div class="placeholder-icon-section">
          <v-icon size="small" :color="cueTypeColor" class="placeholder-icon">
            {{ getCueIcon(cueData.type) }}
          </v-icon>
        </div>

        <div class="placeholder-message">
          <div class="primary-message">
            {{ cueData.slug || 'No Slug' }}
          </div>
          <div class="secondary-message">
            Display not yet implemented
          </div>
        </div>
      </div>

      <!-- Cue Information (hidden for FSQ and IMG — those render their own body) -->
      <div v-if="cueData.type !== 'FSQ' && cueData.type !== 'IMG'" class="cue-info">
        <div v-if="cueData.description" class="cue-description">
          <v-icon size="small" class="info-icon">mdi-text</v-icon>
          <span class="description-text">{{ cueData.description }}</span>
        </div>

        <div v-if="cueData.assetId" class="cue-asset-id">
          <v-icon size="small" class="info-icon">mdi-identifier</v-icon>
          <span class="asset-id-text">{{ cueData.assetId }}</span>
        </div>

        <div v-if="cueData.mediaUrl" class="cue-media-url">
          <v-icon size="small" class="info-icon">mdi-link</v-icon>
          <span class="media-url-text">{{ truncateUrl(cueData.mediaUrl) }}</span>
        </div>

        <!-- Job Status Display (centered in card body) -->
        <div v-if="(showJobStatus && jobStatus) || processingStatusMessage" class="job-status-body" :class="{ 'status-failed': isFailed, 'status-processing': isProcessing }">
          <v-chip
            v-if="showJobStatus && jobStatus"
            :color="jobStatusColor"
            size="small"
            class="job-status-chip-body"
          >
            <v-icon size="x-small" start>
              {{ jobStatus.status === 'processing' ? 'mdi-loading mdi-spin' :
                 jobStatus.status === 'completed' ? 'mdi-check-circle' :
                 jobStatus.status === 'failed' ? 'mdi-alert-circle' :
                 'mdi-clock-outline' }}
            </v-icon>
            {{ jobStatusText }}
          </v-chip>
          <div v-else-if="processingStatusMessage" class="processing-status-inline">
            <v-icon size="small" class="status-icon" :color="isFailed ? 'error' : 'info'">
              {{ isFailed ? 'mdi-alert-circle' : 'mdi-cog' }}
            </v-icon>
            <span class="status-text">{{ processingStatusMessage }}</span>
          </div>
        </div>

        <!-- Retry Button for Failed Jobs -->
        <div v-if="isFailed" class="retry-section">
          <v-btn
            color="warning"
            variant="elevated"
            size="small"
            @click.stop="handleRetry"
            prepend-icon="mdi-refresh"
          >
            Retry Processing
          </v-btn>
        </div>
      </div>
    </v-card-text>

    <!-- Card Footer (hidden for RIF and collapsed) -->
    <v-card-actions v-if="cueData.type !== 'RIF' && !collapsed" class="cue-card-footer" :style="footerStyle">
      <!-- Show duration in footer -->
      <div class="duration-display">
        <v-icon size="small" :color="footerTextColor">mdi-timer-outline</v-icon>
        <span class="duration-text-footer">{{ cueData.duration || '00:00:00:00' }}</span>
      </div>

      <v-spacer></v-spacer>

      <!-- Orbital Action Menu -->
      <div class="orbital-menu" :class="{ 'orbital-open': orbitalOpen }" @click.stop>
        <v-btn
          icon
          size="x-small"
          class="orbital-trigger"
          @click.stop="orbitalOpen = !orbitalOpen"
        >
          <v-icon size="18" :class="{ 'orbital-icon-spin': orbitalOpen }">
            {{ orbitalOpen ? 'mdi-close' : 'mdi-dots-horizontal' }}
          </v-icon>
          <v-tooltip v-if="!orbitalOpen" activator="parent" location="top">Actions</v-tooltip>
        </v-btn>

        <!-- Orbital items radiate outward from trigger -->
        <transition-group name="orbital-item">
          <v-btn
            v-if="orbitalOpen"
            key="edit"
            icon
            size="x-small"
            class="orbital-btn orbital-pos-1"
            @click.stop="orbitalOpen = false; $emit('edit')"
          >
            <v-icon size="16">mdi-pencil</v-icon>
            <v-tooltip activator="parent" location="top">Edit cue</v-tooltip>
          </v-btn>

          <v-btn
            v-if="orbitalOpen && showReprocessButton"
            key="reupload"
            icon
            size="x-small"
            class="orbital-btn orbital-pos-2"
            @click.stop="orbitalOpen = false; handleReupload()"
          >
            <v-icon size="16">mdi-upload</v-icon>
            <v-tooltip activator="parent" location="top">Re-upload video</v-tooltip>
          </v-btn>

          <v-btn
            v-if="orbitalOpen && showReprocessButton"
            key="reprocess"
            icon
            size="x-small"
            class="orbital-btn orbital-pos-3"
            @click.stop="orbitalOpen = false; handleReprocess()"
          >
            <v-icon size="16">mdi-refresh</v-icon>
            <v-tooltip activator="parent" location="top">Reprocess video</v-tooltip>
          </v-btn>

          <v-btn
            v-if="orbitalOpen && cueData.type === 'FSQ'"
            key="genpng"
            icon
            size="x-small"
            class="orbital-btn orbital-pos-2"
            :loading="generatingPNG"
            @click.stop="orbitalOpen = false; handleGeneratePNG()"
          >
            <v-icon size="16">mdi-image-auto-adjust</v-icon>
            <v-tooltip activator="parent" location="top">Generate PNG</v-tooltip>
          </v-btn>

          <v-btn
            v-if="orbitalOpen"
            key="relocate"
            icon
            size="x-small"
            class="orbital-btn orbital-pos-last"
            @click.stop="orbitalOpen = false; $emit('relocate')"
          >
            <v-icon size="16">mdi-truck-delivery</v-icon>
            <v-tooltip activator="parent" location="top">Move to another segment</v-tooltip>
          </v-btn>
        </transition-group>
      </div>

      <!-- Delete Cue Button - Right side -->
      <v-btn
        size="small"
        variant="text"
        @click.stop="$emit('delete')"
        class="delete-cue-btn"
        style="color: white !important;"
      >
        <v-icon size="small" class="me-1">mdi-delete</v-icon>
        DELETE
        <v-tooltip activator="parent" location="top">Delete this cue</v-tooltip>
      </v-btn>
    </v-card-actions>

    <!-- GFX Preview Modal — the rendered PNG keyed over the background video,
         exactly as it will look on air. ESC closes (v-dialog default). -->
    <v-dialog
      v-model="showGfxPreviewModal"
      max-width="960"
    >
      <v-card class="fsq-preview-modal-card">
        <v-card-title class="d-flex align-center pa-2 bg-grey-darken-4">
          <v-icon class="mr-2" color="white">mdi-image-frame</v-icon>
          <span class="text-white">GFX Preview</span>
          <v-spacer></v-spacer>
          <v-chip size="small" color="info" class="mr-2">keyed over background</v-chip>
          <v-btn
            icon
            size="small"
            variant="text"
            color="white"
            @click="showGfxPreviewModal = false"
          >
            <v-icon>mdi-close</v-icon>
            <v-tooltip activator="parent" location="top">Close (ESC)</v-tooltip>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-0">
          <div class="fsq-preview-container">
            <video
              class="fsq-preview-video-bg"
              autoplay
              loop
              muted
              playsinline
            >
              <source :src="fsqBackgroundVideoUrl" type="video/mp4">
            </video>
            <img
              v-if="gfxImageUrl"
              :src="gfxImageUrl"
              class="fsq-preview-png-overlay"
            />
          </div>
        </v-card-text>
        <v-card-actions class="bg-grey-darken-4 pa-2">
          <v-chip size="small" color="grey-darken-2">
            {{ cueData.slug || 'No slug' }}
          </v-chip>
          <v-spacer></v-spacer>
          <span class="text-caption text-grey-lighten-1">Press ESC to close</span>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- FSQ Preview Modal (960x540 - half resolution) -->
    <v-dialog
      v-model="showFsqPreviewModal"
      max-width="960"
    >
      <v-card class="fsq-preview-modal-card">
        <v-card-title class="d-flex align-center pa-2 bg-grey-darken-4">
          <v-icon class="mr-2" color="white">mdi-format-quote-close</v-icon>
          <span class="text-white">FSQ Preview</span>
          <v-spacer></v-spacer>
          <v-chip size="small" color="info" class="mr-2">960×540</v-chip>
          <v-btn
            icon
            size="small"
            variant="text"
            color="white"
            @click="closeFsqPreviewModal"
          >
            <v-icon>mdi-close</v-icon>
            <v-tooltip activator="parent" location="top">Close (ESC)</v-tooltip>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-0">
          <div class="fsq-preview-container">
            <!-- Video Background -->
            <video
              ref="fsqPreviewVideoRef"
              class="fsq-preview-video-bg"
              autoplay
              loop
              muted
              playsinline
            >
              <source :src="fsqBackgroundVideoUrl" type="video/mp4">
            </video>
            <!-- PNG Overlay -->
            <img
              v-if="cueData.mediaUrl"
              :src="fsqThumbnailUrl"
              class="fsq-preview-png-overlay"
            />
          </div>
        </v-card-text>
        <v-card-actions class="bg-grey-darken-4 pa-2">
          <v-chip size="small" color="grey-darken-2">
            {{ cueData.slug || 'No slug' }}
          </v-chip>
          <v-spacer></v-spacer>
          <v-btn
            v-if="cueData.mediaUrl"
            size="small"
            variant="tonal"
            color="deep-purple-lighten-2"
            @click="downloadFsqPNG"
            class="mr-2"
          >
            <v-icon size="small" start>mdi-download</v-icon>
            Download PNG
          </v-btn>
          <span class="text-caption text-grey-lighten-1">Press ESC to close</span>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- FSQ Full-Resolution 1:1 Viewer — the ACTUAL rendered 1920×1080 PNG,
         shown at native size on a fullscreen black canvas. ESC to exit. -->
    <v-dialog
      v-model="showFsqFullResModal"
      fullscreen
      :scrim="false"
      transition="dialog-bottom-transition"
    >
      <div class="fsq-fullres-stage" @click.self="closeFsqFullResModal">
        <v-btn
          icon
          size="small"
          variant="flat"
          color="grey-darken-3"
          class="fsq-fullres-close"
          @click="closeFsqFullResModal"
        >
          <v-icon color="white">mdi-close</v-icon>
          <v-tooltip activator="parent" location="left">Close (ESC)</v-tooltip>
        </v-btn>
        <!-- 1:1 canvas: looping background video, with the rendered PNG (which
             has a transparent window where the video shows through) on top.
             Both are exactly 1920×1080 so they stay pixel-aligned. -->
        <div class="fsq-fullres-canvas" @click.self="closeFsqFullResModal">
          <video
            class="fsq-fullres-video"
            autoplay
            loop
            muted
            playsinline
          >
            <source :src="fsqBackgroundVideoUrl" type="video/mp4">
          </video>
          <img
            v-if="cueData.mediaUrl"
            :src="fsqThumbnailUrl"
            class="fsq-fullres-img"
            alt="FSQ full resolution"
          />
        </div>
        <div class="fsq-fullres-hint text-caption">{{ cueData.slug || 'FSQ' }} · 1920×1080 · press ESC to exit</div>
      </div>
    </v-dialog>

    <!-- SOT Preview Modal (960x540 video player) -->
    <v-dialog
      v-model="showSotPreviewModal"
      max-width="960"
    >
      <v-card class="sot-preview-modal-card">
        <v-card-title class="d-flex align-center pa-2 bg-grey-darken-4">
          <v-icon class="mr-2" color="white">mdi-video</v-icon>
          <span class="text-white">SOT Preview</span>
          <v-spacer></v-spacer>
          <v-chip size="small" color="info" class="mr-2">960×540</v-chip>
          <v-btn
            icon
            size="small"
            variant="text"
            color="white"
            @click="closeSotPreviewModal"
          >
            <v-icon>mdi-close</v-icon>
            <v-tooltip activator="parent" location="top">Close (ESC)</v-tooltip>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-0">
          <div class="sot-preview-container">
            <!-- Countdown Overlay -->
            <transition name="countdown-fade">
              <div v-if="previewCountdown > 0" class="preview-countdown-overlay">
                <div class="countdown-display">
                  <div class="countdown-label">PLAYING IN</div>
                  <div class="countdown-time">{{ previewCountdown.toFixed(1) }}s</div>
                  <div class="countdown-progress">
                    <div class="countdown-progress-bar" :style="{ width: ((1.5 - previewCountdown) / 1.5 * 100) + '%' }"></div>
                  </div>
                </div>
              </div>
            </transition>
            <video
              v-if="showSotPreviewModal"
              ref="sotPreviewVideoRef"
              :src="sotVideoUrl"
              class="sot-preview-video"
              controls
              @loadeddata="onPreviewVideoReady"
            ></video>
          </div>
        </v-card-text>
        <v-card-actions class="bg-grey-darken-4 pa-2">
          <v-chip size="small" color="grey-darken-2">
            {{ cueData.slug || 'No slug' }}
          </v-chip>
          <v-chip v-if="cueData.duration" size="small" color="grey-darken-2" class="ml-2">
            <v-icon size="small" start>mdi-timer-outline</v-icon>
            {{ cueData.duration }}
          </v-chip>
          <v-spacer></v-spacer>
          <span class="text-caption text-grey-lighten-1">Press ESC to close</span>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { getColorValue, resolveVuetifyColor, getReadableTextColor } from '../../../utils/themeColorMap.js';
import { formatTimecode } from '../../../utils/timecode.js';
import { useSOTProcessing } from '../../../composables/useSOTProcessing.js';
import FsqCueContent from './cue-types/FsqCueContent.vue'; // eslint-disable-line no-unused-vars
import SotCueContent from './cue-types/SotCueContent.vue'; // eslint-disable-line no-unused-vars
import GfxCueContent from './cue-types/GfxCueContent.vue'; // eslint-disable-line no-unused-vars
import ImageCueContent from './cue-types/ImageCueContent.vue'; // eslint-disable-line no-unused-vars
import { FSQ_DEFAULTS, FSQ_PNG_SCALE, FSQ_PNG_ATTRIBUTION_SCALE } from '../../../utils/fsqLayout.js';

const props = defineProps({
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
  },
  currentEpisode: {
    type: String,
    default: ''
  },
  // Controlled collapsed state — owned by the cue node (via CueNodeView), so it
  // survives drag-drop and persists into the saved markdown. The card emits
  // 'toggle-collapsed' and never mutates this directly.
  collapsed: {
    type: Boolean,
    default: false
  },
  // Read-only render (version preview): hide edit/delete affordances. The card
  // still renders fully, it just can't be mutated. (todo #35)
  readonly: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['select', 'edit', 'delete', 'update-meta', 'modify', 'reupload-sot-cue', 'edit-fsq', 'edit-gfx', 'relocate', 'apply-all-fsq', 'apply-all-gfx', 'status-changed', 'toggle-collapsed']);

const route = useRoute();
const { getJobByAssetId, retryFailedJob, reprocessJob } = useSOTProcessing();

// Template refs
const fsqContentRef = ref(null);
const gfxContentRef = ref(null);
const fsqPreviewVideoRef = ref(null); // eslint-disable-line no-unused-vars
const sotPreviewVideoRef = ref(null); // eslint-disable-line no-unused-vars
const inlineVideoPlayer = ref(null);

// Reactive data (was data())
const orbitalOpen = ref(false);
const generatingPNG = ref(false);
// Dirty = the rendered PNG no longer matches the cue. On mount, a cue that
// already has a rendered PNG (mediaUrl) is considered up-to-date; one without
// is dirty (needs a first render). Any subsequent edit flips this true via
// handleChildUpdateMeta; a successful render flips it false.
const fsqDirty = ref(!props.cueData?.mediaUrl);
const generatingGfx = ref(false);       // GFX generation in progress
const gfxImageError = ref(false);       // GFX image failed to load
const gfxGenerationStatus = ref(null);  // GFX generation status: null, 'queued', 'generating', 'completed', 'failed'
const gfxTaskId = ref(null);            // Current GFX Celery task ID // eslint-disable-line no-unused-vars
const fsqGenerationStatus = ref(null); // FSQ generation status: null, 'queued', 'generating', 'completed', 'failed'
const fsqTaskId = ref(null);        // Current FSQ Celery task ID // eslint-disable-line no-unused-vars
const fsqCacheBuster = ref(null);   // Timestamp to bust browser cache after regeneration
const jobStatus = ref(null);        // Current job status from API (SOT)
const statusPollInterval = ref(null); // Interval ID for polling
const currentThumbnailIndex = ref(7); // Default to middle thumbnail (index 7 = thumb 8 of 15)
const pollingActive = ref(false);    // Whether we're currently polling
const cueStatus = ref(null);
const thumbnailError = ref(false); // eslint-disable-line no-unused-vars
const gfxGeneratedUrl = ref(null);  // Local override for immediate card refresh after generation
// Inline video player state
const showInlinePlayer = ref(false);
// FSQ preview modal state
const showFsqPreviewModal = ref(false);
// GFX preview modal state (rendered PNG keyed over the background video)
const showGfxPreviewModal = ref(false);
// Full-resolution 1:1 PNG viewer (the actual rendered 1920×1080 file)
const showFsqFullResModal = ref(false);
// SOT preview modal state
const showSotPreviewModal = ref(false);
// Preview countdown state
const previewCountdown = ref(0);
const countdownInterval = ref(null);

// Computed properties
/**
 * Badge label - shows "NOTE: DIRECTOR" for NOTE cues with noteFor, otherwise just the type
 */
const cueTypeBadgeLabel = computed(() => {
  const t = props.cueData.type;
  if ((t === 'NOTE' || t === 'DIR') && props.cueData.noteFor) {
    return `${t}: ${props.cueData.noteFor.toUpperCase()}`;
  }
  if (t === 'GFX' && props.cueData.gfxType === 'xpost') {
    return 'GFX-XPOST';
  }
  return t;
});

/**
 * Card style based on cue_status
 */
const cardStyleWithStatus = computed(() => {
  const baseStyle = getCardStyle.value;

  // Status colors are configurable via Settings → Colors (Global Action Colors).
  switch (cueStatus.value) {
    case 'complete': {
      const completeHex = resolveVuetifyColor(getColorValue('complete'));
      return {
        ...baseStyle,
        backgroundColor: lightenColor(completeHex, 75),
        borderColor: completeHex
      };
    }
    case 'needs_attention':
      return {
        ...baseStyle,
        // Keep body background unchanged, just border
        borderColor: resolveVuetifyColor(getColorValue('needs-attention'))
      };
    case 'urgent_attention':
      return {
        ...baseStyle,
        // Keep body background unchanged, just border
        borderColor: resolveVuetifyColor(getColorValue('urgent-attention')),
        borderWidth: '5px'           // Slightly thicker for urgency
      };
    default:
      return baseStyle;
  }
});

/**
 * Header style based on cue_status
 */
const headerStyleWithStatus = computed(() => {
  // Header bg derived from the same configurable status colors; text color is
  // chosen for contrast automatically.
  switch (cueStatus.value) {
    case 'complete': {
      const bg = darkenColor(resolveVuetifyColor(getColorValue('complete')), 0.2);
      return { backgroundColor: bg, color: getReadableTextColor(bg) };
    }
    case 'needs_attention': {
      const bg = resolveVuetifyColor(getColorValue('needs-attention'));
      return { backgroundColor: bg, color: getReadableTextColor(bg) };
    }
    case 'urgent_attention': {
      const bg = resolveVuetifyColor(getColorValue('urgent-attention'));
      return { backgroundColor: bg, color: getReadableTextColor(bg) };
    }
    default:
      return headerStyle.value;
  }
});

const formatCueTitle = computed(() => {
  const title = props.cueData.slug || props.cueData.title || '';

  // For RIF cues: remove hyphens and capitalize each word
  if (props.cueData.type === 'RIF') {
    return title
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }

  // For XPOST cues: show @handle if available
  if (props.cueData.type === 'GFX' && props.cueData.gfxType === 'xpost') {
    const handle = props.cueData.rawData?.authorHandle || props.cueData.authorHandle;
    if (handle) return `@${handle}`;
  }

  // For all other cues: return as-is
  return title;
});

/**
 * Get all SOT thumbnail options (array of URLs)
 * Uses relative URLs - Vue dev proxy forwards /episodes to backend
 */
const sotThumbnailOptions = computed(() => {
  // Helper function to normalize URL path
  const makeAbsoluteUrl = (url) => {
    if (url.startsWith('http')) {
      return url;
    }
    if (url.startsWith('/episodes')) {
      return url;
    }
    return `/episodes/${url}`;
  };

  // First check cue data for ThumbnailOptions (array from processing)
  if (props.cueData?.thumbnailOptions && Array.isArray(props.cueData.thumbnailOptions)) {
    return props.cueData.thumbnailOptions.map(makeAbsoluteUrl);
  }

  // Check job status for thumbnail_candidates (from database)
  if (jobStatus.value?.thumbnail_candidates && Array.isArray(jobStatus.value.thumbnail_candidates)) {
    // Use final_thumbnail_path to get correct directory (thumbnails, not video)
    const thumbnailPath = jobStatus.value.final_thumbnail_path || '';
    if (thumbnailPath) {
      // Extract the base pattern from final_thumbnail_path (e.g., "0257/assets/thumbnails/airplane-girl-thumb-01.jpg")
      const match = thumbnailPath.match(/^(.+)-thumb-\d+\.(jpg|png)$/);
      if (match) {
        const basePath = match[1];  // "0257/assets/thumbnails/airplane-girl"
        const ext = match[2];  // preserve original extension
        return jobStatus.value.thumbnail_candidates.map((_, i) => {
          return `/episodes/${basePath}-thumb-${String(i + 1).padStart(2, '0')}.${ext}`;
        });
      }
    }
    // Fallback: try to build from video path but use thumbnails directory
    const videoPath = jobStatus.value.final_video_path?.replace(/\.mp4$/, '') || '';
    if (videoPath) {
      // Replace /video/ with /thumbnails/ in the path
      const thumbnailDir = videoPath.replace('/video/', '/thumbnails/');
      return jobStatus.value.thumbnail_candidates.map((_, i) => {
        return `/episodes/${thumbnailDir}-thumb-${String(i + 1).padStart(2, '0')}.jpg`;
      });
    }
  }

  // Generate options based on single thumbnail URL pattern
  if (sotThumbnailUrl.value) {
    const match = sotThumbnailUrl.value.match(/^(.+)-thumb-(\d+)\.(jpg|png)$/);
    if (match) {
      const base = match[1];
      const ext = match[3];  // preserve original extension
      return Array.from({ length: 15 }, (_, i) => `${base}-thumb-${String(i + 1).padStart(2, '0')}.${ext}`);
    }
  }

  // Single thumbnail fallback
  if (sotThumbnailUrl.value) {
    return [sotThumbnailUrl.value];
  }

  return [];
});

/**
 * Get current thumbnail URL based on selected index
 */
const currentSotThumbnailUrl = computed(() => {
  const options = sotThumbnailOptions.value;
  if (options.length === 0) return '';

  // Ensure index is within bounds
  const index = Math.min(Math.max(0, currentThumbnailIndex.value), options.length - 1);
  return options[index] || options[0];
});

/**
 * Get sharpness score for current thumbnail from thumbnail_data
 */
const currentThumbnailSharpness = computed(() => {
  if (!jobStatus.value?.thumbnail_data || !Array.isArray(jobStatus.value.thumbnail_data)) {
    return null;
  }

  // Find thumbnail data for current index (1-based in data)
  const thumbData = jobStatus.value.thumbnail_data.find(
    t => t.index === currentThumbnailIndex.value + 1
  );

  return thumbData?.sharpness || null;
});

/**
 * Check if job is completed (status from API)
 */
const isJobCompleted = computed(() => {
  return jobStatus.value?.status === 'completed';
});

/**
 * Display duration - prioritizes jobStatus data over stale cueData placeholders
 * Treats "calculating", "processing", "queued", "pending" as null values
 */
const displayDuration = computed(() => {
  const stalePlaceholders = ['calculating', 'processing', 'queued', 'pending', ''];

  // Resolve the raw duration value (a seconds decimal from analysis, or an
  // already-formatted timecode string from cueData), then format it ONCE below
  // so every display point (SOT body row, footer, header) shows hh:mm:ss:ff.
  let raw = null;

  // If job is completed, prefer jobStatus data
  if (isJobCompleted.value) {
    raw = jobStatus.value?.post_analysis?.duration ?? jobStatus.value?.video_specs?.duration ?? null;
  }

  // Check cueData, but filter out placeholder values
  if (raw == null) {
    const cueDuration = props.cueData?.duration?.toLowerCase?.() || props.cueData?.duration;
    if (cueDuration && !stalePlaceholders.includes(cueDuration?.toLowerCase?.())) {
      raw = props.cueData.duration;
    }
  }

  // Fallback to jobStatus even if not completed
  if (raw == null) {
    raw = jobStatus.value?.post_analysis?.duration ?? jobStatus.value?.video_specs?.duration ?? null;
  }

  if (raw == null) return null;
  // formatTimecode passes through existing "00:00:05:00" strings and converts a
  // raw seconds decimal (e.g. 12.34) to hh:mm:ss:ff; returns null if unusable.
  return formatTimecode(raw) ?? raw;
});

/**
 * Display video path - prioritizes jobStatus data over stale cueData placeholders
 */
const displayVideoPath = computed(() => {
  const stalePlaceholders = ['processing', 'queued', 'pending', ''];

  // If job is completed, prefer jobStatus data
  if (isJobCompleted.value && jobStatus.value?.final_video_path) {
    return jobStatus.value.final_video_path;
  }

  // Check cueData, but filter out placeholder values
  const cueMediaUrl = props.cueData?.mediaUrl?.toLowerCase?.() || props.cueData?.mediaUrl;
  if (cueMediaUrl && !stalePlaceholders.includes(cueMediaUrl?.toLowerCase?.())) {
    return props.cueData.mediaUrl;
  }

  // Fallback to jobStatus
  if (jobStatus.value?.final_video_path) {
    return jobStatus.value.final_video_path;
  }

  return null;
});

/**
 * Display processing status - prioritizes actual job status over stale cueData
 */
const displayProcessingStatus = computed(() => {
  // If we have live job status, use that
  if (jobStatus.value?.status) {
    const status = jobStatus.value.status;
    if (status === 'completed') return 'Completed';
    if (status === 'failed') {
      const errMsg = jobStatus.value.error_message || '';
      if (errMsg) {
        const cleaned = errMsg.replace(/^Unexpected error:\s*/i, '');
        return `FAILED: ${cleaned}`;
      }
      return 'Failed';
    }
    if (status === 'processing') return jobStatus.value.current_phase || 'Processing...';
    if (status === 'queued') return 'Queued';
    return status;
  }

  // Fallback to cueData
  if (props.cueData?.processingStatus) {
    return props.cueData.processingStatus;
  }

  return null;
});

/**
 * Get color for sharpness indicator based on value
 */
const sharpnessColor = computed(() => {
  const sharpness = currentThumbnailSharpness.value;
  if (!sharpness) return 'grey';

  if (sharpness < 100) return '#D32F2F';  // Red - blurry
  if (sharpness < 150) return '#FF9800';  // Orange - below average
  if (sharpness < 200) return '#FFC107';  // Yellow - average
  return '#4CAF50';  // Green - sharp
});

/**
 * Get SOT thumbnail URL from cue data or job status (base/primary thumbnail)
 * Uses relative URLs - Vue dev proxy forwards /episodes to backend
 */
const sotThumbnailUrl = computed(() => {
  const backendUrl = '';

  // First check cue data for ThumbnailURL (skip stale blob: URLs)
  if (props.cueData?.thumbnailUrl && !props.cueData.thumbnailUrl.startsWith('blob:')) {
    // If already an absolute URL, return as-is
    if (props.cueData.thumbnailUrl.startsWith('http')) {
      return props.cueData.thumbnailUrl;
    }
    // If starts with /episodes, use as relative URL
    if (props.cueData.thumbnailUrl.startsWith('/episodes')) {
      return props.cueData.thumbnailUrl;
    }
    // Otherwise, construct full path
    return `/episodes/${props.cueData.thumbnailUrl}`;
  }

  // Fall back to job status thumbnail path
  if (jobStatus.value?.final_thumbnail_path) {
    const path = jobStatus.value.final_thumbnail_path;
    if (path.startsWith('http')) {
      return path;
    }
    if (path.startsWith('/episodes')) {
      return `${backendUrl}${path}`;
    }
    return `${backendUrl}/episodes/${path}`;
  }

  return '';
});

/**
 * Get SOT transcription from cue data or job status
 */
const sotTranscription = computed(() => {
  // First check cue data (from parsed cue block)
  if (props.cueData?.transcription) {
    return props.cueData.transcription;
  }
  // Fall back to job status transcription
  if (jobStatus.value?.transcription) {
    return jobStatus.value.transcription;
  }
  return '';
});

/**
 * Get SOT outcue from cue data (last 5 words of transcription with "..." prefix)
 */
const sotOutcue = computed(() => {
  // Check cue data for outcue field
  if (props.cueData?.outcue) {
    return props.cueData.outcue;
  }
  return '';
});

/**
 * Get SOT video URL for inline player
 * Uses relative URLs - Vue dev proxy forwards /episodes to backend
 */
const sotVideoUrl = computed(() => {
  const backendUrl = '';

  // First check cue data for MediaURL (skip stale blob: URLs)
  if (props.cueData?.mediaUrl && !props.cueData.mediaUrl.startsWith('blob:')) {
    // If already an absolute URL, return as-is
    if (props.cueData.mediaUrl.startsWith('http')) {
      return props.cueData.mediaUrl;
    }
    // If starts with /episodes, use as relative URL
    if (props.cueData.mediaUrl.startsWith('/episodes')) {
      return props.cueData.mediaUrl;
    }
    // Otherwise, construct full path
    return `/episodes/${props.cueData.mediaUrl}`;
  }

  // Fall back to job status final video path
  if (jobStatus.value?.final_video_path) {
    const path = jobStatus.value.final_video_path;
    if (path.startsWith('http')) {
      return path;
    }
    if (path.startsWith('/episodes')) {
      return `${backendUrl}${path}`;
    }
    return `${backendUrl}/episodes/${path}`;
  }

  return '';
});

/**
 * Get FSQ thumbnail URL - use mediaUrl from cue data
 */
const fsqThumbnailUrl = computed(() => {
  if (!props.cueData?.mediaUrl) return '';
  let url;
  // If it's already a full URL, use it; otherwise prepend /episodes
  if (props.cueData.mediaUrl.startsWith('http') || props.cueData.mediaUrl.startsWith('/')) {
    url = props.cueData.mediaUrl;
  } else {
    // Build episode-relative URL
    const episode = route?.params?.episode || '';
    url = `/episodes/${episode}/assets/quotes/${props.cueData.mediaUrl}`;
  }
  // Add cache buster to force reload after regeneration
  if (fsqCacheBuster.value) {
    url += `?t=${fsqCacheBuster.value}`;
  }
  return url;
});

/**
 * Get GFX image URL from cue data
 */
const gfxActiveListItems = computed(() => {
  const raw = props.cueData?.listItems || props.cueData?.rawData?.listItems;
  if (!raw) return [];
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
    return Array.isArray(parsed) ? parsed.filter(item => item && item.trim()) : [];
  } catch (e) { // eslint-disable-line no-unused-vars
    return [];
  }
});

const hasGfxAsset = computed(() => {
  return !!(gfxGeneratedUrl.value || props.cueData?.assetUrl || props.cueData?.mediaUrl);
});

const xpostData = computed(() => {
  const rd = props.cueData?.rawData || props.cueData || {};
  return {
    name: rd.authorName || '',
    username: rd.authorHandle || '',
    profilePhoto: rd.authorAvatar || '',
    verified: rd.authorVerified === 'true' || rd.authorVerified === true,
    text: (rd.tweetText || '').replace(/\\n/g, '\n'),
    datetime: rd.publishedTime || '',
    views: parseInt(rd.views) || 0,
    likes: parseInt(rd.likes) || 0,
    retweets: parseInt(rd.retweets) || 0,
    replies: parseInt(rd.replies) || 0,
    quotes: parseInt(rd.quotes) || 0,
    bookmarks: parseInt(rd.bookmarks) || 0,
    sourceUrl: rd.sourceUrl || rd.sourceURL || '',
  };
});

const gfxImageUrl = computed(() => { // eslint-disable-line no-unused-vars
  const url = gfxGeneratedUrl.value || props.cueData?.assetUrl || props.cueData?.mediaUrl;
  if (!url) return '';
  if (url.startsWith('http') || url.startsWith('/')) {
    return url;
  }
  const episode = props.currentEpisode || route?.params?.episode || '';
  // X-post renders live in their dedicated directory.
  const gfxDir = (props.cueData?.gfxType || '').toLowerCase() === 'xpost' ? 'gfx/xpost' : 'graphics';
  return `/episodes/${episode}/assets/${gfxDir}/${url}`;
});

// Card-preview URL: xpost cues show the transparent "_key" variant so the
// preview background video shows through (the full-frame PNG is opaque and
// reads as a black slab at card size). The renderer always writes both files.
const gfxCardImageUrl = computed(() => {
  const url = gfxImageUrl.value;
  const gfxTypeVal = (props.cueData?.gfxType || props.cueData?.rawData?.gfxType || '').toLowerCase();
  if (gfxTypeVal !== 'xpost' || !url || !/\.png($|\?)/.test(url)) return url;
  return url.replace(/\.png($|\?)/, '_key.png$1');
});

/**
 * Get FSQ generation status text for display
 */
const fsqStatusText = computed(() => { // eslint-disable-line no-unused-vars
  switch (fsqGenerationStatus.value) {
    case 'queued': return 'Queued';
    case 'generating': return 'Generating...';
    case 'completed': return 'Complete';
    case 'failed': return 'Failed';
    default: return '';
  }
});

/**
 * Get FSQ status chip color
 */
const fsqStatusChipColor = computed(() => { // eslint-disable-line no-unused-vars
  switch (fsqGenerationStatus.value) {
    case 'queued': return 'info';
    case 'generating': return 'warning';
    case 'completed': return 'success';
    case 'failed': return 'error';
    default: return 'grey';
  }
});

/**
 * Get FSQ status chip icon
 */
const fsqStatusChipIcon = computed(() => { // eslint-disable-line no-unused-vars
  switch (fsqGenerationStatus.value) {
    case 'queued': return 'mdi-clock-outline';
    case 'generating': return 'mdi-loading';
    case 'completed': return 'mdi-check-circle';
    case 'failed': return 'mdi-alert-circle';
    default: return 'mdi-help-circle';
  }
});

/**
 * Get GFX generation status text for display
 */
const gfxStatusText = computed(() => { // eslint-disable-line no-unused-vars
  const map = { queued: 'Queued', generating: 'Generating...', completed: 'Complete', failed: 'Failed' }
  return map[gfxGenerationStatus.value] || ''
});

/**
 * Get GFX status chip color
 */
const gfxStatusChipColor = computed(() => { // eslint-disable-line no-unused-vars
  const map = { queued: 'blue-grey', generating: 'amber', completed: 'success', failed: 'error' }
  return map[gfxGenerationStatus.value] || 'grey'
});

/**
 * Get GFX status chip icon
 */
const gfxStatusChipIcon = computed(() => { // eslint-disable-line no-unused-vars
  const map = { queued: 'mdi-clock-outline', generating: 'mdi-cog', completed: 'mdi-check-circle', failed: 'mdi-alert-circle' }
  return map[gfxGenerationStatus.value] || 'mdi-help-circle'
});

/**
 * Get motion background style for FSQ thumbnail container
 * Uses fsqBackgroundVideo from settings
 */
const thumbnailBackgroundStyle = computed(() => { // eslint-disable-line no-unused-vars
  // Fallback gradient for when video isn't loaded
  return {
    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
    backgroundSize: 'cover'
  };
});

/**
 * Get FSQ background video URL from settings or use default
 */
const fsqBackgroundVideoUrl = computed(() => {
  // Try to get from localStorage settings
  try {
    const settings = JSON.parse(localStorage.getItem('fsqSettings') || '{}');
    if (settings.fsq_background_video) {
      return settings.fsq_background_video;
    }
  } catch (e) {
    console.warn('Failed to parse FSQ settings:', e);
  }
  // Default background video path
  return '/assets/preview-background.mp4';
});

const showReprocessButton = computed(() => {
  const cueType = props.cueData.type?.toUpperCase();
  const isSOTorVO = cueType === 'SOT' || cueType === 'VO';
  // Check both assetId (camelCase) and assetid (lowercase from parser)
  const hasAssetId = !!(props.cueData.assetId || props.cueData.assetid);
  const actualAssetId = props.cueData.assetId || props.cueData.assetid;
  console.log(`🔍 PlaceholderCueCard: type=${props.cueData.type}, assetId=${props.cueData.assetId}, assetid=${props.cueData.assetid}, actualAssetId=${actualAssetId}, showButton=${isSOTorVO && hasAssetId}`);
  return isSOTorVO && hasAssetId;
});

const showJobStatus = computed(() => {
  // Show status for SOT/VO cues that have an AssetID (case-insensitive check)
  const cueType = props.cueData.type?.toUpperCase();
  const isSOTorVO = cueType === 'SOT' || cueType === 'VO';
  return isSOTorVO && !!(props.cueData.assetId || props.cueData.assetid);
});

const jobStatusText = computed(() => {
  if (!jobStatus.value) return '';

  const status = jobStatus.value.status;
  const phase = jobStatus.value.current_phase;

  if (status === 'processing' && phase) {
    const phaseNames = {
      'phase1': 'Analyzing',
      'phase2': 'Processing Clips',
      'phase3': 'Finalizing'
    };
    return phaseNames[phase] || phase;
  }
  if (status === 'failed') {
    const errMsg = jobStatus.value.error_message || '';
    if (errMsg) {
      const cleaned = errMsg.replace(/^Unexpected error:\s*/i, '');
      return `FAILED: ${cleaned}`;
    }
    return 'FAILED';
  }
  if (status === 'not_found') return '';
  return status;
});

const jobStatusColor = computed(() => {
  if (!jobStatus.value) return 'grey';

  const status = jobStatus.value.status;
  const phase = jobStatus.value.current_phase;

  // Different colors for different phases
  if (status === 'processing' && phase) {
    const phaseColors = {
      'phase1': 'light-blue',  // Analyzing/trimming
      'phase2': 'indigo',       // Processing clips
      'phase3': 'deep-purple'   // Finalizing
    };
    return phaseColors[phase] || 'blue';
  }

  const statusColors = {
    'queued': 'orange',
    'processing': 'blue',
    'completed': 'green',
    'failed': 'red',
    'not_found': 'grey'
  };

  return statusColors[status] || 'grey';
});

const cueTypeColor = computed(() => {
  if (!props.cueData.type) return 'grey';
  const colorName = getColorValue(props.cueData.type.toLowerCase());
  return resolveVuetifyColor(colorName);
});

// Single source of truth for the header/footer FOREGROUND color (text + icons +
// buttons). Mirrors whatever background the header is actually showing — the
// cue-type color, or the status-border color when one is active — and resolves
// to black or white for WCAG contrast. Bound to every header child so nothing
// stays hardcoded white on a light cue color (FSQ lime, NAT, NOTE, ...).
const headerTextColor = computed(() => headerStyleWithStatus.value.color || '#FFFFFF');
// Footer foreground mirrors the footer background (the cue-type color).
const footerTextColor = computed(() => getReadableTextColor(cueTypeColor.value));

// Text/icon color is chosen for CONTRAST against the cue-type background via
// getReadableTextColor (WCAG 4.5:1; prefers white, flips to black on light cue
// colors like FSQ lime / NAT light-green / NOTE light-yellow). Previously these
// hardcoded white, which was unreadable on light backgrounds.
const cueTypeStyle = computed(() => { // eslint-disable-line no-unused-vars
  const backgroundColor = cueTypeColor.value;
  return {
    backgroundColor: backgroundColor,
    color: getReadableTextColor(backgroundColor)
  };
});

const headerStyle = computed(() => {
  const backgroundColor = cueTypeColor.value;
  return {
    backgroundColor: backgroundColor,
    color: getReadableTextColor(backgroundColor)
  };
});

const badgeStyle = computed(() => {
  const baseColor = cueTypeColor.value;
  // Only lighten if we have a valid hex color string
  const lighterColor = (typeof baseColor === 'string' && baseColor.startsWith('#'))
    ? lightenColor(baseColor, 20)
    : baseColor;
  const bg = lighterColor || '#666';
  return {
    backgroundColor: bg,
    // contrast against the LIGHTENED badge color, not the base
    color: getReadableTextColor(bg)
  };
});

const footerStyle = computed(() => {
  const backgroundColor = cueTypeColor.value;
  return {
    backgroundColor: backgroundColor,
    color: getReadableTextColor(backgroundColor)
  };
});

/**
 * Get CSS class for analysis state
 */
const getAnalysisClass = computed(() => {
  const state = props.cueData?.analysisState;
  if (state === 'analyzing') return 'cue-analyzing';
  if (state === 'needs_review') return 'cue-needs-review';
  return '';
});

/**
 * Get card style including analysis state border
 */
const getCardStyle = computed(() => {
  const state = props.cueData?.analysisState;

  // Check for processing job status
  if (processingJob.value) {
    if (processingJob.value.status === 'failed') {
      // Red 7px border for failed processing
      return {
        borderColor: '#D32F2F',
        borderWidth: '7px',
        borderStyle: 'solid'
      };
    } else if (processingJob.value.status === 'processing') {
      // Blue 7px border while processing
      return {
        borderColor: '#2196F3',
        borderWidth: '7px',
        borderStyle: 'solid'
      };
    }
  }

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

  // Default: use darker version of cue type color with 3px border
  return {
    borderColor: darkenColor(cueTypeColor.value, 0.3),
    borderWidth: '3px',
    borderStyle: 'solid'
  };
});

/**
 * Get processing job for this cue's asset
 */
const processingJob = computed(() => {
  if (!props.cueData?.assetId) return null;
  return getJobByAssetId(props.cueData.assetId);
});

/**
 * Check if this cue is currently processing
 */
const isProcessing = computed(() => {
  return processingJob.value?.status === 'processing';
});

/**
 * Check if this cue's processing failed
 */
const isFailed = computed(() => {
  return processingJob.value?.status === 'failed';
});

/**
 * Get processing status message
 */
const processingStatusMessage = computed(() => {
  if (!processingJob.value) return null;

  const job = processingJob.value;
  if (job.status === 'processing') {
    return job.phase_message || job.current_phase || 'Processing...';
  } else if (job.status === 'failed') {
    const errMsg = job.error_message || job.error || '';
    if (errMsg) {
      // Extract the meaningful part after "Unexpected error: "
      const cleaned = errMsg.replace(/^Unexpected error:\s*/i, '');
      return `FAILED: ${cleaned}`;
    }
    return 'Processing failed';
  } else if (job.status === 'not_found') {
    return null;
  }
  return null;
});

// Methods
/**
 * Forward update-meta events from child cue content components
 */
function handleChildUpdateMeta(payload) {
  // Mark FSQ as dirty when FSQ params change (so Generate PNG button re-enables)
  if (props.cueData.type === 'FSQ') {
    fsqDirty.value = true;
  }
  emit('update-meta', payload);
}

function darkenColor(color, amount) {
  if (!color || color === 'grey') return '#555';
  // Handle hex colors
  let hex = color.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
  if (hex.length !== 6) return color;
  const r = Math.max(0, Math.round(parseInt(hex.substring(0, 2), 16) * (1 - amount)));
  const g = Math.max(0, Math.round(parseInt(hex.substring(2, 4), 16) * (1 - amount)));
  const b = Math.max(0, Math.round(parseInt(hex.substring(4, 6), 16) * (1 - amount)));
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

/**
 * Navigate to previous thumbnail
 */
function prevThumbnail() { // eslint-disable-line no-unused-vars
  if (currentThumbnailIndex.value > 0) {
    currentThumbnailIndex.value--;
    emitSelectedThumbnail();
  }
}

/**
 * Navigate to next thumbnail
 */
function nextThumbnail() { // eslint-disable-line no-unused-vars
  if (currentThumbnailIndex.value < sotThumbnailOptions.value.length - 1) {
    currentThumbnailIndex.value++;
    emitSelectedThumbnail();
  }
}

/**
 * Emit selected thumbnail to parent for saving to cue block
 */
function emitSelectedThumbnail() {
  const selectedUrl = currentSotThumbnailUrl.value;
  console.log(`🖼️ Selected thumbnail ${currentThumbnailIndex.value + 1}: ${selectedUrl}`);
  emit('update-meta', {
    assetId: props.cueData.assetId || props.cueData.assetid,
    field: 'thumbnailUrl',
    value: selectedUrl
  });
}

/**
 * Handle SOT thumbnail error
 */
function handleSotThumbnailError() { // eslint-disable-line no-unused-vars
  console.warn('SOT thumbnail failed to load:', currentSotThumbnailUrl.value);
}

/**
 * Toggle inline video player visibility
 */
function toggleInlinePlayer() { // eslint-disable-line no-unused-vars
  if (sotVideoUrl.value) {
    // If closing, pause video first to prevent race condition
    if (showInlinePlayer.value) {
      const video = inlineVideoPlayer.value;
      if (video) {
        video.pause();
        video.currentTime = 0;
      }
    }
    showInlinePlayer.value = !showInlinePlayer.value;
    // Auto-play when opening with proper promise handling
    if (showInlinePlayer.value) {
      nextTick(() => {
        const video = inlineVideoPlayer.value;
        if (video) {
          const playPromise = video.play();
          if (playPromise !== undefined) {
            playPromise.catch(error => {
              console.log('Inline video auto-play prevented:', error.message);
            });
          }
        }
      });
    }
  } else {
    // Fallback: open in new tab if no video URL available
    openVideoPlayer();
  }
}

/**
 * Handle video metadata loaded
 */
function onVideoLoaded() { // eslint-disable-line no-unused-vars
  console.log('Inline video loaded:', sotVideoUrl.value);
}

/**
 * Open video player for SOT (in new tab)
 * Uses relative URLs - Vue dev proxy forwards /episodes to backend
 */
function openVideoPlayer() {
  const backendUrl = '';
  const videoPath = props.cueData.mediaUrl || jobStatus.value?.final_video_path;
  if (videoPath) {
    let fullPath;
    if (videoPath.startsWith('http')) {
      fullPath = videoPath;
    } else if (videoPath.startsWith('/episodes')) {
      fullPath = `${backendUrl}${videoPath}`;
    } else {
      fullPath = `${backendUrl}/episodes/${videoPath}`;
    }
    window.open(fullPath, '_blank');
  }
}

/**
 * Format media path for display (truncate long paths)
 */
function formatMediaPath(path) { // eslint-disable-line no-unused-vars
  if (!path) return '';
  // Show just the filename
  const parts = path.split('/');
  return parts[parts.length - 1] || path;
}

/**
 * Format warning label for display (extract short description)
 */
function formatWarningLabel(warning) { // eslint-disable-line no-unused-vars
  if (!warning) return '';

  // Extract the type before the colon for display
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

/**
 * Truncate transcription for preview
 */
function truncateTranscription(text) { // eslint-disable-line no-unused-vars
  if (!text) return '';
  if (text.length <= 100) return text;
  return text.substring(0, 100) + '...';
}

/**
 * Preload all thumbnail images for faster navigation
 * Creates Image objects in memory to cache them in the browser
 */
function preloadThumbnails() {
  const options = sotThumbnailOptions.value;
  if (!options || options.length <= 1) return;

  console.log(`🖼️ Preloading ${options.length} thumbnails for ${props.cueData.slug || 'cue'}`);

  options.forEach((url, index) => {
    const img = new Image();
    img.onload = () => {
      if (index === 0) {
        console.log(`✅ First thumbnail preloaded: ${url}`);
      }
    };
    img.onerror = () => {
      console.warn(`⚠️ Failed to preload thumbnail ${index + 1}: ${url}`);
    };
    img.src = url;
  });
}


/**
 * Select quote text for copying
 */
function selectQuoteText(event) { // eslint-disable-line no-unused-vars
  const textElement = event.target;
  if (window.getSelection && document.createRange) {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(textElement);
    selection.removeAllRanges();
    selection.addRange(range);
  }
}

/**
 * Handle thumbnail load error
 */
function handleThumbnailError() { // eslint-disable-line no-unused-vars
  console.warn('FSQ thumbnail failed to load:', props.cueData.mediaUrl);
  thumbnailError.value = true;
}

/**
 * Open FSQ preview modal with video background
 */
function openFsqPreviewModal() {
  console.log('🖼️ Opening FSQ preview modal');
  showFsqPreviewModal.value = true;
  // Add ESC key listener
  nextTick(() => {
    document.addEventListener('keydown', handlePreviewModalEsc);
  });
}

/**
 * Close FSQ preview modal
 */
function closeFsqPreviewModal() {
  console.log('🖼️ Closing FSQ preview modal');
  showFsqPreviewModal.value = false;
  document.removeEventListener('keydown', handlePreviewModalEsc);
}

/**
 * Open the full-resolution 1:1 PNG viewer (actual rendered 1920×1080 file).
 */
function openFsqFullResModal() {
  if (!props.cueData?.mediaUrl) return;
  console.log('🔍 Opening FSQ full-resolution 1:1 viewer');
  showFsqFullResModal.value = true;
  nextTick(() => {
    document.addEventListener('keydown', handlePreviewModalEsc);
  });
}

/**
 * Close the full-resolution 1:1 PNG viewer.
 */
function closeFsqFullResModal() {
  console.log('🔍 Closing FSQ full-resolution viewer');
  showFsqFullResModal.value = false;
  document.removeEventListener('keydown', handlePreviewModalEsc);
}

/**
 * Open SOT preview modal with video player
 */
function openSotPreviewModal() {
  console.log('🎬 Opening SOT preview modal');
  showSotPreviewModal.value = true;
  // Add ESC key listener
  nextTick(() => {
    document.addEventListener('keydown', handlePreviewModalEsc);
  });
}

/**
 * Close SOT preview modal
 */
function closeSotPreviewModal() {
  console.log('🎬 Closing SOT preview modal');
  // Clear countdown interval if running
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value);
    countdownInterval.value = null;
  }
  previewCountdown.value = 0;
  // Pause video before closing to prevent play/pause race condition
  const video = sotPreviewVideoRef.value;
  if (video) {
    video.pause();
    video.currentTime = 0;
  }
  showSotPreviewModal.value = false;
  document.removeEventListener('keydown', handlePreviewModalEsc);
}

/**
 * Handle preview video ready - start countdown then auto-play
 */
function onPreviewVideoReady() {
  const video = sotPreviewVideoRef.value;
  if (video && showSotPreviewModal.value) {
    // Start 1.5 second countdown before playing
    previewCountdown.value = 1.5;

    // Clear any existing interval
    if (countdownInterval.value) {
      clearInterval(countdownInterval.value);
    }

    // Update countdown every 100ms for smooth animation
    countdownInterval.value = setInterval(() => {
      previewCountdown.value -= 0.1;

      if (previewCountdown.value <= 0) {
        previewCountdown.value = 0;
        clearInterval(countdownInterval.value);
        countdownInterval.value = null;

        // Now play the video with promise handling
        const playPromise = video.play();
        if (playPromise !== undefined) {
          playPromise.catch(error => {
            // Auto-play was prevented - this is fine, user can click play
            console.log('Auto-play prevented:', error.message);
          });
        }
      }
    }, 100);
  }
}

/**
 * Handle ESC key to close preview modals
 */
function handlePreviewModalEsc(event) {
  if (event.key === 'Escape') {
    if (showFsqFullResModal.value) {
      closeFsqFullResModal();
    }
    if (showFsqPreviewModal.value) {
      closeFsqPreviewModal();
    }
    if (showSotPreviewModal.value) {
      closeSotPreviewModal();
    }
  }
}

function getCueIcon(cueType) { // eslint-disable-line no-unused-vars
  const iconMap = {
    'SOT': 'mdi-play-circle-outline',
    'VO': 'mdi-microphone',
    'NAT': 'mdi-volume-high',
    'PKG': 'mdi-package-variant',
    'FSQ': 'mdi-format-quote-close',
    'RIF': 'mdi-music-note',
    'VOX': 'mdi-account-voice',
    'MUS': 'mdi-music',
    'LIVE': 'mdi-broadcast',
    'CG': 'mdi-text-box',
    'LOWER': 'mdi-text-box-outline',
    'TITLE': 'mdi-title',
    'CREDIT': 'mdi-account-credit-card',
    'BUMPER': 'mdi-movie-roll',
    'PROMO': 'mdi-bullhorn',
    'TEASE': 'mdi-eye',
    'BREAK': 'mdi-pause',
    'COMMERCIAL': 'mdi-currency-usd'
  };

  return iconMap[cueType?.toUpperCase()] || 'mdi-file-question-outline';
}

function truncateUrl(url) { // eslint-disable-line no-unused-vars
  if (!url) return '';
  if (url.length <= 40) return url;

  const start = url.substring(0, 20);
  const end = url.substring(url.length - 17);
  return `${start}...${end}`;
}

function lightenColor(color, percent) {
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
    const hexVal = n.toString(16);
    return hexVal.length === 1 ? '0' + hexVal : hexVal;
  };

  return `#${toHex(newR)}${toHex(newG)}${toHex(newB)}`;
}

/**
 * Handle retry button click
 */
async function handleRetry() { // eslint-disable-line no-unused-vars
  if (!processingJob.value?.temp_job_id) {
    console.error('Cannot retry: no temp_job_id found');
    return;
  }

  console.log(`🔄 Retrying failed job from cue card: ${processingJob.value.temp_job_id}`);
  const success = await retryFailedJob(processingJob.value.temp_job_id);

  if (success) {
    console.log('✅ Retry initiated successfully');
  }
}

/**
 * Download GFX PNG image
 */
function downloadGfxPNG() { // eslint-disable-line no-unused-vars
  const mediaUrl = props.cueData.assetUrl || props.cueData.mediaUrl
  if (!mediaUrl) return

  const url = mediaUrl.startsWith('http') ? mediaUrl : `${window.location.origin}${mediaUrl}`
  const filename = mediaUrl.split('/').pop() || `${props.cueData.slug || 'gfx'}.png`

  const authToken = localStorage.getItem('auth-token')
  fetch(url, {
    headers: authToken ? { 'Authorization': `Bearer ${authToken}` } : {}
  })
    .then(res => {
      if (!res.ok) throw new Error('Download failed')
      return res.blob()
    })
    .then(blob => {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(a.href)
    })
    .catch(err => {
      console.error('GFX PNG download error:', err)
    })
}

/**
 * Render (or re-render) an X-post tweet-card PNG. Uses the captured
 * gfx_xpost_cues row; for legacy cues inserted before the capture endpoint
 * existed, falls back to capturing from the cue block's own fields first.
 */
async function generateXpostPng() {
  try {
    generatingGfx.value = true;
    gfxGenerationStatus.value = 'queued';
    const token = localStorage.getItem('auth-token');
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };

    const response = await fetch(
      `/api/gfx/xpost/${encodeURIComponent(props.cueData.assetId)}/render?priority=high`,
      { method: 'POST', headers }
    );

    if (response.status === 404) {
      console.log('ℹ️ No captured row for this X-post cue — capturing from the cue block first');
      const captured = await captureXpostFromRawData(headers);
      if (!captured?.task_id) {
        throw new Error('X-post capture from cue block failed (no render task dispatched)');
      }
      gfxGenerationStatus.value = 'generating';
      pollGfxTaskStatus(captured.task_id, 45);
      return;
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to queue X-post render');
    }

    const result = await response.json();
    console.log('✅ X-post render queued:', result.task_id);
    gfxGenerationStatus.value = 'generating';
    pollGfxTaskStatus(result.task_id, 45);
  } catch (error) {
    console.error('❌ X-post render failed:', error);
    gfxGenerationStatus.value = 'failed';
  } finally {
    generatingGfx.value = false;
  }
}

// Rebuild the capture payload from the parsed cue block (camelCase rawData
// keys) — legacy-cue recovery path for generateXpostPng.
async function captureXpostFromRawData(headers) {
  const raw = props.cueData.rawData || {};
  const parseJson = (v, fallback) => {
    if (v == null || v === '') return fallback;
    if (typeof v !== 'string') return v;
    try { return JSON.parse(v); } catch { return fallback; }
  };
  const toNum = v => {
    const n = parseInt(String(v ?? '').replace(/[^0-9]/g, ''), 10);
    return Number.isFinite(n) ? n : null;
  };
  const unesc = s => (typeof s === 'string' ? s.replace(/\\n/g, '\n') : s);
  const episode = props.currentEpisode || route?.params?.episode || '';

  const payload = {
    asset_id: props.cueData.assetId,
    episode_number: episode || '0000',
    slug: props.cueData.slug || 'xpost',
    xpost_name: raw.authorName || null,
    xpost_username: raw.authorHandle || null,
    xpost_profile_photo: raw.authorAvatar || null,
    xpost_verified: String(raw.authorVerified ?? '') === 'true',
    xpost_bio: unesc(raw.authorBio) || null,
    xpost_followers: toNum(raw.authorFollowers),
    xpost_following: toNum(raw.authorFollowing),
    xpost_post_text: unesc(raw.tweetText) || null,
    xpost_tweet_id: raw.tweetId || null,
    xpost_conversation_id: raw.conversationId || null,
    xpost_media_urls: parseJson(raw.mediaUrls, null),
    xpost_media_objects: parseJson(raw.mediaObjects, null),
    xpost_datetime: raw.publishedTime || null,
    xpost_view_count: toNum(raw.views),
    xpost_likes: toNum(raw.likes),
    xpost_retweets: toNum(raw.retweets),
    xpost_replies: toNum(raw.replies),
    xpost_quotes: toNum(raw.quotes),
    xpost_bookmarks: toNum(raw.bookmarks),
    xpost_source_url: raw.sourceUrl || null,
    xpost_platform: 'x',
    xpost_entities: parseJson(raw.entities, null),
    xpost_referenced_tweets: parseJson(raw.referencedTweets, null),
    aspect_ratio: raw.aspectRatio || null,
    title: unesc(raw.title) || null,
    notes: parseJson(raw.notes, null),
    render: true,
    priority: 'high',
  };

  const resp = await fetch('/api/gfx/xpost', {
    method: 'POST', headers, body: JSON.stringify(payload)
  });
  if (!resp.ok) return null;
  return await resp.json();
}

/**
 * Poll GFX Celery task status until completion
 */
async function pollGfxTaskStatus(taskId, maxAttempts = 30) {
  let attempts = 0;

  const poll = async () => {
    if (attempts >= maxAttempts) {
      console.log('⏱️ GFX polling timeout');
      gfxGenerationStatus.value = 'failed';
      return;
    }

    attempts++;

    try {
      const token = localStorage.getItem('auth-token');
      const response = await fetch(`/api/gfx/task/${taskId}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });

      if (!response.ok) {
        console.error('Failed to check GFX task status');
        return;
      }

      const status = await response.json();
      console.log(`📊 GFX Task ${taskId} status:`, status.state);

      if (status.ready) {
        if (status.successful) {
          console.log('🎉 GFX generation completed!', status.result);
          gfxGenerationStatus.value = 'completed';

          if (status.result.asset_url) {
            const assetUrl = status.result.asset_url;
            console.log('📝 Updating GFX assetUrl to:', assetUrl);

            // Store locally so card refreshes immediately
            gfxGeneratedUrl.value = assetUrl;
            gfxImageError.value = false;

            // Update the cue block in the script (persists to database)
            emit('update-meta', {
              assetId: props.cueData.assetId,
              field: 'assetUrl',
              value: assetUrl
            });

            // Flip Status too so pending badges clear after a regenerate.
            emit('update-meta', {
              assetId: props.cueData.assetId,
              field: 'status',
              value: 'generated'
            });
          }

          setTimeout(() => {
            if (gfxGenerationStatus.value === 'completed') {
              gfxGenerationStatus.value = null;
            }
          }, 3000);

        } else {
          console.error('❌ GFX generation failed:', status.error);
          gfxGenerationStatus.value = 'failed';
        }
      } else {
        setTimeout(poll, 2000);
      }
    } catch (error) {
      console.error('Error polling GFX task status:', error);
    }
  };

  poll();
}

/**
 * Handle re-upload button click - Open SotModal with existing metadata but no mediaUrl
 * This allows uploading a new video while keeping the slug, description, credits, etc.
 */
function handleReupload() {
  console.log('📤 Re-upload requested for SOT cue:', props.cueData.slug);

  // Clear failed status immediately - we're starting fresh with a new video
  jobStatus.value = null;

  // Stop polling for old job status
  if (statusPollInterval.value) {
    clearInterval(statusPollInterval.value);
    statusPollInterval.value = null;
    pollingActive.value = false;
    console.log('🛑 Stopped polling old job status for re-upload');
  }

  // Build re-upload data: preserve metadata but clear mediaUrl so user must upload new file
  const reuploadData = {
    assetId: props.cueData.assetId || props.cueData.assetid,
    slug: props.cueData.slug,
    description: props.cueData.description || props.cueData.text || '',
    duration: props.cueData.duration,
    transcription: props.cueData.transcription,
    credits: props.cueData.credits,
    // Explicitly do NOT include mediaUrl - user will upload a new video
    // mediaUrl: null,
    // thumbnailUrl: null,
    // trimStart/trimEnd will be set when the new video is loaded
  };

  console.log('📤 Re-upload data:', reuploadData);
  emit('reupload-sot-cue', reuploadData);
}

/**
 * Handle reprocess button click - Clean up and restart processing
 */
async function handleReprocess() {
  const assetId = props.cueData.assetId || props.cueData.assetid;
  if (!assetId) {
    console.error('Cannot reprocess: no assetId found');
    return;
  }

  console.log(`🔄 Reprocessing SOT from cue card: ${assetId}`);
  const success = await reprocessJob(assetId);

  if (success) {
    console.log('✅ Reprocess initiated successfully');
  } else {
    console.error('❌ Retry failed');
  }
}

/**
 * Handle Generate PNG button click - Queue Celery task for FSQ PNG generation
 */
function downloadFsqPNG() {
  if (!props.cueData.mediaUrl) return

  const url = fsqThumbnailUrl.value
  const filename = props.cueData.mediaUrl.split('/').pop() || `${props.cueData.slug || 'fsq'}.png`

  const authToken = localStorage.getItem('auth-token')
  fetch(url, {
    headers: authToken ? { 'Authorization': `Bearer ${authToken}` } : {}
  })
    .then(res => {
      if (!res.ok) throw new Error('Download failed')
      return res.blob()
    })
    .then(blob => {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(a.href)
    })
    .catch(err => {
      console.error('FSQ PNG download error:', err)
    })
}

async function handleGeneratePNG() {
  if (!props.cueData.assetId) {
    console.error('Cannot generate PNG: no assetId found');
    return;
  }

  if (!props.cueData.quote) {
    console.error('Cannot generate PNG: no quote text found');
    return;
  }

  try {
    generatingPNG.value = true;
    fsqGenerationStatus.value = 'queued';
    console.log(`🎨 Generating FSQ PNG for: ${props.cueData.assetId}`);

    const token = localStorage.getItem('auth-token');
    // Use prop first, then fallback to route params
    const episode = props.currentEpisode || route?.params?.episode || '';

    // Use LOCAL state values (from editable controls) not cueData values
    // Get values from child component ref or fall back to cueData
    const fsqRef = fsqContentRef.value;
    const localFontSize = fsqRef?.localFontSize ?? (parseInt(props.cueData?.fontSize) || FSQ_DEFAULTS.fontSize);
    const localAlignment = fsqRef?.localAlignment ?? (props.cueData?.alignment || FSQ_DEFAULTS.alignment);
    const localFontFamily = fsqRef?.localFontFamily ?? (props.cueData?.fontFamily || FSQ_DEFAULTS.fontFamily);
    const localBoxHeight = fsqRef?.localBoxHeight ?? (parseInt(props.cueData?.boxHeight) || FSQ_DEFAULTS.boxHeight);
    const localBoxOpacity = fsqRef?.localBoxOpacity ?? (parseInt(props.cueData?.boxOpacity) || FSQ_DEFAULTS.boxOpacity);
    const localLineSpacing = fsqRef?.localLineSpacing ?? (parseInt(props.cueData?.lineSpacing) || FSQ_DEFAULTS.lineSpacing);
    const localAttributionSize = fsqRef?.localAttributionSize ?? (parseInt(props.cueData?.attributionSize) || FSQ_DEFAULTS.attributionSize);
    // Scale up the user's UI value to PNG-space and force it as the EXACT
    // rendered size (not a max-fit cap). Sending font_size — not
    // max_font_size — makes the renderer skip its auto-fit search and use
    // exactly this size, so the slider value drives the output reliably.
    const scaledFontSize = localFontSize * FSQ_PNG_SCALE;
    // Attribution size needs the same UI→PNG-space scale as the quote font.
    // Without this, a UI value of 16 was reaching the renderer as 16px on
    // a 1920×1080 canvas (unreadable), while the modal preview at 0.5×
    // looked fine — matching the user's report of "OK in preview, too
    // tiny in the generated PNG."
    const scaledAttributionSize = localAttributionSize
      ? localAttributionSize * FSQ_PNG_ATTRIBUTION_SCALE
      : null;
    const requestData = {
      episode_id: episode,
      quote: props.cueData.quote,
      attribution: props.cueData.attribution || props.cueData.source || '',
      slug: props.cueData.slug || 'quote',
      asset_id: props.cueData.assetId,
      alignment: localAlignment,
      font_family: localFontFamily,
      font_size: scaledFontSize,
      box_height: localBoxHeight,
      box_opacity: localBoxOpacity,
      line_spacing: localLineSpacing,
      attribution_size: scaledAttributionSize,
      duration: props.cueData.duration || '00:00:05:00',
      // Overwrite-in-place: when the cue already has a rendered PNG, hand the
      // worker its existing path so the regenerate writes to the SAME file
      // (no slug-renamed orphan). New FSQs send null → worker names it fresh.
      existing_media_url: props.cueData.mediaUrl || null
    };

    console.log('📤 Sending FSQ PNG generation request:', requestData);

    const response = await fetch('/api/fsq/generate-async', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to queue PNG generation');
    }

    const result = await response.json();
    console.log('✅ PNG generation queued:', result);

    // Update status to generating and store task ID
    fsqGenerationStatus.value = 'generating';
    fsqTaskId.value = result.task_id;

    // Poll for completion (silent - no alerts)
    pollTaskStatus(result.task_id);

  } catch (error) {
    console.error('❌ Error generating FSQ PNG:', error);
    fsqGenerationStatus.value = 'failed';
  } finally {
    generatingPNG.value = false;
  }
}

/**
 * Generate GFX image from cue data
 */
async function handleGenerateGfx() {
  if (!props.cueData.assetId) {
    console.error('Cannot generate GFX: no assetId found');
    return;
  }

  // X-post cues render via the dedicated tweet-card pipeline (from the
  // captured gfx_xpost_cues row) — never the fullscreen-text renderer.
  const gfxTypeVal = (props.cueData.gfxType || props.cueData.rawData?.gfxType || '').toLowerCase();
  if (gfxTypeVal === 'xpost') {
    await generateXpostPng();
    return;
  }

  // Allow generation with body OR list items OR title
  const gfxTitleCheck = props.cueData.gfxTitle || props.cueData.rawData?.title || null;
  const rawListItems = props.cueData.listItems || props.cueData.rawData?.listItems || null;
  const hasListItems = rawListItems && (
    typeof rawListItems === 'string' ? JSON.parse(rawListItems).length > 0 : rawListItems.length > 0
  );
  if (!props.cueData.body && !gfxTitleCheck && !hasListItems) {
    console.error('Cannot generate GFX: no body, title, or list items found');
    return;
  }

  try {
    generatingGfx.value = true;
    gfxGenerationStatus.value = 'queued';
    console.log(`🎨 Generating GFX for: ${props.cueData.assetId}`);

    const token = localStorage.getItem('auth-token');
    const episode = props.currentEpisode || route?.params?.episode || '';

    // Use gfxTitle (actual title text) not title (card display label)
    const gfxTitle = props.cueData.gfxTitle || props.cueData.rawData?.title || null;
    const listItems = props.cueData.listItems || props.cueData.rawData?.listItems || null;
    let parsedListItems = null;
    if (listItems) {
      parsedListItems = typeof listItems === 'string' ? JSON.parse(listItems) : listItems;
    }

    // Use LOCAL state values from child component faceplate controls, not stale cueData.
    // Slider values live in the child via defineExpose; cueData fields are
    // the persisted floor. Local > persisted > default.
    const gfxRef = gfxContentRef.value;
    const localGfxAlignment = gfxRef?.localGfxAlignment ?? (props.cueData?.textAlign || 'center');
    const localGfxFontFamily = gfxRef?.localGfxFontFamily ?? (props.cueData?.fontFamily || 'sans-serif');
    const localGfxFontSize = gfxRef?.localGfxFontSize ?? (parseInt(props.cueData?.fontSize) || 25);
    const localGfxTitleFontSize = gfxRef?.localGfxTitleFontSize ?? (parseInt(props.cueData?.titleFontSize) || 36);
    const localGfxLineSpacing = gfxRef?.localGfxLineSpacing ?? (parseInt(props.cueData?.lineSpacing) || 30);
    const localGfxBoxHeight = gfxRef?.localGfxBoxHeight ?? (parseInt(props.cueData?.boxHeight) || 80);
    const localGfxBoxOpacity = gfxRef?.localGfxBoxOpacity ?? (parseInt(props.cueData?.boxOpacity) || 75);
    const localVerticalOffset = gfxRef?.localVerticalOffset ?? (parseInt(props.cueData?.verticalOffset) || 0);
    const requestData = {
      episode_id: episode,
      gfx_type: props.cueData.gfxType || props.cueData.rawData?.gfxType || 'fullscreen-text',
      body: (props.cueData.body || props.cueData.rawData?.body || '').replace(/\\n/g, '\n'),
      slug: props.cueData.slug || 'gfx',
      asset_id: props.cueData.assetId,
      title: gfxTitle,
      alignment: localGfxAlignment,
      font_family: localGfxFontFamily,
      font_size: localGfxFontSize,
      title_font_size: localGfxTitleFontSize,
      line_spacing: localGfxLineSpacing,
      box_height: localGfxBoxHeight,
      box_opacity: localGfxBoxOpacity,
      vertical_offset: localVerticalOffset,
      render_mode: props.cueData.renderMode || props.cueData.rawData?.renderMode || 'png',
      priority: 'high',
      title_alignment: props.cueData.titleAlign || props.cueData.rawData?.titleAlign || null,
      title_pin_to_top: (props.cueData.titlePinToTop || props.cueData.rawData?.titlePinToTop) === 'true' || props.cueData.titlePinToTop === true,
      title_margin_top: (props.cueData.titleMarginTop || props.cueData.rawData?.titleMarginTop) ? parseFloat(props.cueData.titleMarginTop || props.cueData.rawData?.titleMarginTop) : 1.0,
      title_margin_bottom: (props.cueData.titleMarginBottom || props.cueData.rawData?.titleMarginBottom) ? parseFloat(props.cueData.titleMarginBottom || props.cueData.rawData?.titleMarginBottom) : 1.5,
      list_items: parsedListItems,
      enumerator: props.cueData.enumerator || null
    };

    console.log('📤 Sending GFX generation request:', requestData);

    const response = await fetch('/api/gfx/generate-async', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to queue GFX generation');
    }

    const result = await response.json();
    console.log('✅ GFX generation queued:', result);

    gfxGenerationStatus.value = 'generating';
    gfxTaskId.value = result.task_id;

    // Poll for completion
    pollGfxTaskStatus(result.task_id);

  } catch (error) {
    console.error('❌ Error generating GFX:', error);
    gfxGenerationStatus.value = 'failed';
  } finally {
    generatingGfx.value = false;
  }
}

function formatMetric(n) { // eslint-disable-line no-unused-vars
  if (!n) return '0';
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

/**
 * Format GFX body text for display (unescape newlines)
 */
function formatGfxBody(body) { // eslint-disable-line no-unused-vars
  if (!body) return '';
  // Unescape \n to actual newlines, then truncate for preview
  const unescaped = body.replace(/\\n/g, '\n');
  // Truncate to 200 chars for preview
  return unescaped.length > 200 ? unescaped.substring(0, 200) + '...' : unescaped;
}

/**
 * Handle GFX image load error
 */
function handleGfxImageError() { // eslint-disable-line no-unused-vars
  console.warn('GFX image failed to load:', gfxImageUrl.value);
  gfxImageError.value = true;
}

/**
 * Poll Celery task status until completion
 */
async function pollTaskStatus(taskId, maxAttempts = 30) {
  let attempts = 0;

  const poll = async () => {
    if (attempts >= maxAttempts) {
      console.log('⏱️ Polling timeout - task may still be processing');
      return;
    }

    attempts++;

    try {
      const token = localStorage.getItem('auth-token');
      const response = await fetch(`/api/fsq/task/${taskId}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });

      if (!response.ok) {
        console.error('Failed to check task status');
        return;
      }

      const status = await response.json();
      console.log(`📊 Task ${taskId} status:`, status.state);

      if (status.ready) {
        if (status.successful) {
          console.log('🎉 PNG generation completed!', status.result);
          fsqGenerationStatus.value = 'completed';
          fsqDirty.value = false;

          // Update the cue block with the generated mediaUrl
          if (status.result.asset_url) {
            console.log('📝 Updating cue mediaUrl to:', status.result.asset_url);
            emit('update-meta', {
              assetId: props.cueData.assetId,
              field: 'mediaUrl',
              value: status.result.asset_url
            });
          }

          // Wait 1 second for file to be fully written, then force thumbnail reload
          setTimeout(() => {
            console.log('🔄 Forcing thumbnail reload after 1s delay');
            fsqCacheBuster.value = Date.now();
          }, 1000);

          // Clear status after 3 seconds
          setTimeout(() => {
            if (fsqGenerationStatus.value === 'completed') {
              fsqGenerationStatus.value = null;
            }
          }, 3000);

        } else {
          console.error('❌ PNG generation failed:', status.error);
          fsqGenerationStatus.value = 'failed';
        }
      } else {
        // Still processing, poll again in 2 seconds
        setTimeout(poll, 2000);
      }
    } catch (error) {
      console.error('Error polling task status:', error);
    }
  };

  // Start polling
  poll();
}

/**
 * Fetch job status from API by AssetID
 */
async function fetchJobStatus() {
  const assetId = props.cueData.assetId || props.cueData.assetid;

  console.log('🔍 fetchJobStatus called for cue:', {
    slug: props.cueData.slug,
    type: props.cueData.type,
    assetId: assetId,
    cueData: props.cueData
  });

  if (!assetId) {
    console.warn('⚠️ No AssetID found in cue data, cannot fetch job status');
    return;
  }

  try {
    const token = localStorage.getItem('auth-token');
    // Use appropriate endpoint based on cue type (SOT or VO)
    const cueType = props.cueData.type?.toUpperCase();
    const endpoint = cueType === 'VO' ? `/api/vo/job-status/${assetId}` : `/api/sot/job-status/${assetId}`;
    const response = await fetch(endpoint, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });

    if (!response.ok) {
      console.error(`Failed to fetch job status for ${assetId}`, response.status);
      return;
    }

    const status = await response.json();
    jobStatus.value = status;

    console.log(`📊 Job status for ${assetId}:`, status);

    // Stop polling if job is in terminal state
    if (status.status === 'completed') {
      stopPolling();
    }
  } catch (error) {
    console.error('Error fetching job status:', error);
  }
}

/**
 * Start polling for job status updates
 */
function startPolling() {
  if (pollingActive.value) return;

  pollingActive.value = true;

  // Fetch immediately
  fetchJobStatus();

  // Then poll every 3 seconds
  statusPollInterval.value = setInterval(() => {
    fetchJobStatus();
  }, 3000);

  console.log('📡 Started polling job status');
}

/**
 * Stop polling for job status updates
 */
function stopPolling() {
  if (statusPollInterval.value) {
    clearInterval(statusPollInterval.value);
    statusPollInterval.value = null;
    pollingActive.value = false;
    console.log('🛑 Stopped polling job status');
  }
}

// Watchers
// Watch for assetId changes to start/stop polling dynamically
// Mark an FSQ dirty whenever its content/style changes (e.g. quote text edited
// via the FSQ modal, or any style param) so the rendered PNG is treated as
// stale: the button reverts to "Regenerate" and View/Download PNG hide until a
// new PNG is generated. We deliberately exclude mediaUrl from the signature —
// a successful render updates mediaUrl and must NOT re-mark the cue dirty.
watch(
  () => {
    if (props.cueData?.type !== 'FSQ') return null;
    const d = props.cueData;
    return [
      d.quote, d.attribution, d.source, d.alignment, d.style,
      d.fontFamily, d.fontSize, d.attributionSize,
      d.boxHeight, d.boxOpacity, d.lineSpacing,
    ].join('|');
  },
  (next, prev) => {
    // Skip the initial run (prev === undefined) and non-FSQ cues.
    if (prev === undefined || next === null) return;
    if (next !== prev) {
      fsqDirty.value = true;
    }
  }
);

watch(showJobStatus, (newVal, oldVal) => {
  console.log('👁️ showJobStatus changed:', oldVal, '->', newVal);
  if (newVal && !oldVal) {
    // assetId was added - start polling
    console.log('🚀 AssetID appeared - starting status polling');
    startPolling();
  } else if (!newVal && oldVal) {
    // assetId was removed - stop polling
    stopPolling();
  }
});

// Watch jobStatus object for changes (nested path doesn't work when parent is null)
watch(jobStatus, (newJobStatus, oldJobStatus) => {
  const newStatus = newJobStatus?.status;
  const oldStatus = oldJobStatus?.status;
  console.log('📊 jobStatus watcher fired:', oldStatus, '->', newStatus);

  if (newStatus === 'completed' && oldStatus !== 'completed') {
    console.log('✅ Job completed - emitting refresh request');
    emit('status-changed', {
      status: newStatus,
      assetId: props.cueData.assetId || props.cueData.assetid
    });
  }
}, { deep: true });

// Watch sotThumbnailOptions to preload thumbnails when they become available
watch(sotThumbnailOptions, (newOptions, oldOptions) => {
  // Preload when we get new options (e.g., after job status updates)
  if (newOptions && newOptions.length > 1 && (!oldOptions || oldOptions.length <= 1)) {
    console.log('📷 Thumbnail options now available, preloading...');
    preloadThumbnails();
  }
});

// Lifecycle hooks
onMounted(() => {
  console.log('🔍 PlaceholderCueCard MOUNTED:', {
    type: props.cueData?.type,
    assetId: props.cueData?.assetId,
    assetid: props.cueData?.assetid,
    allKeys: Object.keys(props.cueData || {}),
    showReprocessButton: showReprocessButton.value
  });

  // Start polling if this is a SOT cue with AssetID
  if (showJobStatus.value) {
    startPolling();
  }

  // Preload thumbnails if already available on mount
  if (sotThumbnailOptions.value && sotThumbnailOptions.value.length > 1) {
    preloadThumbnails();
  }
});

onBeforeUnmount(() => {
  // Clean up polling interval
  stopPolling();
  // Clean up countdown interval
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value);
    countdownInterval.value = null;
  }
  // Clean up ESC key listener for preview modals
  document.removeEventListener('keydown', handlePreviewModalEsc);
});

// Expose for parent component access (even though no current $refs access found,
// expose key methods that child components or future parents might need)
defineExpose({
  handleGeneratePNG,
  handleGenerateGfx,
  fetchJobStatus,
  startPolling,
  stopPolling
});
</script>

<style scoped>
.cue-card {
  margin: 8px 0;
  border: 3px solid;
  transition: all 0.2s ease;
  cursor: pointer;
  border-radius: 0 !important;
  position: relative;
  /* Per-user knob: cue card text size (Settings → Editor Display) */
  font-size: var(--editor-cue-font-size, inherit);
}

.cue-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cue-card.selected {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

/* Card border states for needs_attention and urgent_attention */
.cue-needs-attention {
  border-color: #FFC107 !important;
}

.cue-urgent-attention {
  border-color: #D32F2F !important;
  border-width: 5px !important;
}

.placeholder-cue-card {
  /* Full-width cue: fill the available editor column so the card matches the
     paragraph width. The old 75% cap was a legacy (contenteditable-era) value
     that left the card at ~60-70% of the script area. */
  max-width: 100%;
  width: 100%;
  /* Margins removed - alignment now controlled by parent .cue-segment flex container */
  transition: all 0.2s ease;
}

/* Collapsed state — compact single-line card */
.cue-collapsed {
  max-height: 48px;
  overflow: hidden;
}

.cue-collapsed .cue-card-header {
  cursor: pointer;
  min-height: 48px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.cue-collapsed .cue-type-badge {
  font-size: 0.7rem;
}

.cue-collapsed .cue-title-text {
  font-size: 0.8rem;
}

/* RIF card right-alignment removed - now controlled by global cue card alignment setting */

/* Header Styling */
.cue-card-header {
  padding: 0 16px 0 0 !important;
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

.cue-enumerator-badge {
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 0.9rem;
  /* tint from currentColor so the badge chip + its text both follow the header's
     contrast-aware color (readable on light cue colors, not hardcoded white) */
  background-color: color-mix(in srgb, currentColor 18%, transparent);
  color: currentColor;
  display: flex;
  align-items: center;
  margin-left: -8px;
  font-family: 'Courier New', monospace;
}

.job-status-chip {
  margin-left: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.cue-title-text {
  font-weight: bold;
  font-size: 1.2rem;
  font-family: Helvetica, Arial, sans-serif;
  flex: 1;
  display: flex;
  align-items: center;
}

.cue-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.cue-actions-footer {
  display: flex;
  gap: 4px;
  align-items: center;
}

.action-btn {
  opacity: 0.7;
  /* inherit the header's contrast-aware color (headerTextColor) instead of
     forcing white — so Edit/Delete icons stay readable on light cue colors */
  color: currentColor;
}

.action-btn:hover {
  opacity: 1;
}

.delete-btn:hover {
  /* keep contrast on hover too (was hardcoded white) */
  color: currentColor;
}

/* Duration Display in Header (RIF only) */
.duration-display-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  /* inherit the header's contrast-aware color (was hardcoded white) */
  color: currentColor;
  font-weight: 500;
  margin-right: 8px;
}

.duration-text-header {
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 0.5px;
}

/* Content Styling */
.cue-card-content {
  /* Per-user knob: cue card density (compact / comfortable / roomy) */
  padding: var(--editor-cue-density, 16px) !important;
}

.placeholder-container {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: rgba(var(--v-theme-surface-variant), 0.1);
  border-radius: 0;
  border: 2px dashed rgba(var(--v-theme-outline), 0.3);
  margin-bottom: 12px;
}

.placeholder-icon-section {
  flex-shrink: 0;
}

.placeholder-icon {
  opacity: 0.7;
}

.placeholder-message {
  flex: 1;
}

.primary-message {
  font-weight: 600;
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.9);
  margin-bottom: 4px;
}

.secondary-message {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-style: italic;
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

/* GFX Container Styles */
/* GFX Preview Overlay (inside FSQ-style animated background) */
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

/* DIR (Directors Note) Styling */
.dir-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background-color: rgba(var(--v-theme-surface-variant), 0.05);
  border-radius: 4px;
  margin-bottom: 12px;
}

.dir-content {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.dir-icon-section {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dir-note-section {
  flex: 1;
}

.dir-note-text {
  font-size: 1rem;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.87);
  white-space: pre-wrap;
  font-style: italic;
  padding: 8px;
  background-color: rgba(var(--v-theme-warning), 0.05);
  border-left: 4px solid rgb(var(--v-theme-warning));
  border-radius: 4px;
}

.dir-no-content {
  font-size: 0.9rem;
  font-style: italic;
  padding: 8px;
}

/* SOT Container Styling */
.sot-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  background-color: rgba(var(--v-theme-surface-variant), 0.05);
  border-radius: 4px;
}

/* SOT Completed Layout - Thumbnail + Info side by side */
.sot-completed-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

/* Wrapper for thumbnail + navigation */
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

/* Thumbnail Navigation */
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

/* VO (Voice Over) Badge */
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

/* VO Container - slight purple tint to distinguish from SOT */
.vo-container {
  border-left: 3px solid #9C27B0;
}

/* VO Notice in info section */
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

/* Technical specs display */
.sot-tech-specs {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.8rem;
}

/* Warnings row */
.sot-warnings-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

/* Sharpness indicator row */
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

/* SOT Outcue Banner - Full Width at Bottom */
.sot-outcue-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.15) 0%, rgba(255, 152, 0, 0.1) 100%);
  border: 2px solid #ffc107;
  border-radius: 6px;
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

/* SOT Processing Layout */
.sot-processing-layout {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background-color: rgba(33, 150, 243, 0.05);
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

/* SOT Pending Layout */
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

/* Inline Video Player - Discreet, collapsible */
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
  /* Per-user knob: inline image/video preview max height */
  max-height: var(--editor-image-max-height, 200px);
  background: #000;
}

.sot-video-player {
  width: 100%;
}

.sot-transcription {
  padding: 12px;
  background-color: rgba(var(--v-theme-surface), 0.3);
  border-left: 3px solid rgb(var(--v-theme-primary));
  border-radius: 4px;
}

.transcription-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.87);
}

.transcription-text {
  font-size: 0.9rem;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.7);
  white-space: pre-wrap;
}

.sot-parent-link {
  display: flex;
  align-items: center;
  padding: 8px;
  background-color: rgba(var(--v-theme-info), 0.1);
  border-radius: 4px;
  font-size: 0.85rem;
}

.sot-processing-status {
  display: flex;
  align-items: center;
  padding: 8px;
  background-color: rgba(var(--v-theme-primary), 0.1);
  border-radius: 4px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
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
.cue-duration,
.cue-media-url {
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

.media-url-text {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  word-break: break-all;
}

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

/* Left side of top row: preview */
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

/* Black bar styles now come from dynamic :style binding (computeBlackBarStyle)
   when box height/opacity sliders are connected. Fallback for static rendering: */
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

/* Right side: 35% - Compact controls */
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

/* Wide controls variant (below preview) */
.fsq-compact-controls--wide {
  width: 100%;
}

.fsq-slider-row--full {
  width: 100%;
}

/* 3-per-row grid for FSQ adjustment controls */
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

/* Apply All FSQ button on slider rows */
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

/* FSQ footer row with delete */
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

/* Legacy FSQ styles (kept for backwards compatibility) */
.fsq-redesigned-container {
  display: flex;
  gap: 16px;
  width: 100%;
  background-color: #ffffff;
  border-radius: 0;
  padding: 16px;
  min-height: 200px;
}

.fsq-quote-side {
  flex: 0 0 75%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 16px;
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: 4px;
}

.fsq-quote-block {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.fsq-quote-icon-left {
  flex-shrink: 0;
  opacity: 0.5;
}

.fsq-quote-icon-right {
  flex-shrink: 0;
  opacity: 0.5;
  align-self: flex-end;
}

.fsq-quote-full-text {
  flex: 1;
  font-size: 1.1rem;
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.87);
  font-style: italic;
  cursor: text;
  user-select: text;
  padding: 8px;
}

.fsq-quote-full-text:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.fsq-attribution-full {
  font-size: 0.95rem;
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
  margin-top: 16px;
  margin-left: 40px;
  font-style: normal;
}

.fsq-params-side {
  flex: 0 0 25%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
}

/* Regenerate button */
.fsq-regenerate-btn {
  width: 100%;
  text-transform: none;
  font-weight: 500;
}

/* FSQ Generation Status Indicator */
.fsq-status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  margin-top: 4px;
}

.fsq-status-queued {
  background-color: rgba(158, 158, 158, 0.2);
  color: #9e9e9e;
}

.fsq-status-generating {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.fsq-status-completed {
  background-color: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.fsq-status-failed {
  background-color: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.fsq-status-icon {
  font-size: 14px;
}

.fsq-status-text {
  letter-spacing: 0.5px;
}

/* Thumbnail container with motion background */
.fsq-thumbnail-container {
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: #000;
}

.fsq-thumbnail-container.clickable {
  cursor: pointer;
}

.fsq-thumbnail-container.clickable:hover .fsq-thumbnail-click-hint {
  opacity: 1;
}

.fsq-thumbnail-video-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

.fsq-thumbnail-img {
  position: relative;
  width: 100%;
  height: 100%;
  object-fit: contain;
  z-index: 2;
}

.fsq-thumbnail-click-hint {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 3;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 4px;
  padding: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

/* FSQ Preview Modal Styles */
/* Full-resolution 1:1 FSQ viewer — black fullscreen canvas; the PNG is shown
   at its native 1920×1080 (no scaling). If the viewport is smaller, the stage
   scrolls so the image stays true 1:1. */
.fsq-fullres-stage {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
}

/* The true-1:1 canvas: fixed 1920×1080 box holding the video + PNG layers. */
.fsq-fullres-canvas {
  position: relative;
  width: 1920px;
  height: 1080px;
  flex: 0 0 auto;       /* never let flexbox shrink it below native size */
  background: #000;
}

.fsq-fullres-video {
  position: absolute;
  inset: 0;
  width: 1920px;
  height: 1080px;
  object-fit: cover;
  z-index: 1;
}

.fsq-fullres-img {
  position: absolute;
  inset: 0;
  width: 1920px;
  height: 1080px;
  object-fit: none;     /* render the PNG 1:1, no resampling */
  z-index: 2;           /* PNG sits over the video; its transparent window shows it through */
  display: block;
}

.fsq-fullres-close {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 10;
}

.fsq-fullres-hint {
  position: fixed;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  color: rgba(255, 255, 255, 0.6);
  background: rgba(0, 0, 0, 0.5);
  padding: 2px 10px;
  border-radius: 4px;
  pointer-events: none;
}

.fsq-preview-modal-card {
  border-radius: 0 !important;
  overflow: hidden;
}

.fsq-preview-container {
  width: 100%;
  aspect-ratio: 16/9;
  position: relative;
  overflow: hidden;
  background: #000;
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

.fsq-preview-png-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  z-index: 2;
}

/* SOT Preview Modal Styles */
.sot-preview-modal-card {
  border-radius: 0 !important;
  overflow: hidden;
}

.sot-preview-container {
  width: 100%;
  aspect-ratio: 16/9;
  position: relative;
  overflow: hidden;
  background: #000;
}

.sot-preview-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Preview Countdown Overlay */
.preview-countdown-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.85);
  z-index: 10;
}

.countdown-display {
  text-align: center;
  background: rgba(0, 0, 0, 0.9);
  padding: 24px 48px;
  border-radius: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  min-width: 200px;
}

.countdown-label {
  color: #90CAF9;
  font-size: 12px;
  font-weight: bold;
  font-family: 'Helvetica', Arial, sans-serif;
  letter-spacing: 2px;
  margin-bottom: 8px;
}

.countdown-time {
  color: white;
  font-size: 48px;
  font-weight: bold;
  font-family: 'Orbitron', 'Courier New', monospace;
  letter-spacing: 3px;
  text-shadow: 0 0 15px rgba(255, 255, 255, 0.5);
  font-variant-numeric: tabular-nums;
}

.countdown-progress {
  margin-top: 16px;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.countdown-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #81C784);
  transition: width 0.1s linear;
}

/* Countdown fade transition */
.countdown-fade-enter-active,
.countdown-fade-leave-active {
  transition: opacity 0.3s ease;
}

.countdown-fade-enter-from,
.countdown-fade-leave-to {
  opacity: 0;
}

.sot-thumbnail-clickable {
  cursor: pointer;
}

.fsq-thumbnail-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: rgba(0, 0, 0, 0.4);
}

.fsq-placeholder-text {
  font-size: 0.75rem;
  text-transform: uppercase;
}

/* FSQ Parameters controls */
.fsq-params-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fsq-param-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.fsq-param-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.fsq-param-select {
  font-size: 0.85rem;
}

.fsq-param-slider {
  margin-top: 0;
  margin-bottom: 0;
}

.fsq-param-toggle {
  width: 100%;
}

.fsq-param-toggle .v-btn {
  flex: 1;
}

/* FSQ Generated checkmark in header */
.fsq-generated-check {
  margin-right: 8px;
}

/* Legacy FSQ styles (kept for backwards compatibility) */
.fsq-container {
  padding: 16px;
  background-color: rgba(0, 0, 0, 0.7);
  border-radius: 0;
  width: 100%;
  height: 80%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  top: 10%;
}

.fsq-quote-section {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 24px;
}

.quote-icon {
  flex-shrink: 0;
  opacity: 0.6;
  margin-top: 4px;
}

.fsq-quote-text {
  flex: 1;
  font-size: calc(1rem + 2pt);
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.95);
  font-style: italic;
}

.fsq-attribution {
  font-size: 0.95rem;
  color: rgba(var(--v-theme-on-surface), 0.75);
  font-weight: 500;
  margin-left: 64px;
  font-style: normal;
}

/* Footer Styling */
.cue-card-footer {
  padding: 8px 16px !important;
  border-top: none;
  justify-content: flex-start;
}

/* Delete Cue Button - right aligned, highlighted */
.delete-cue-btn {
  margin-left: auto !important;
  font-size: 0.85rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.delete-cue-btn:hover {
  background-color: rgba(244, 67, 54, 0.3) !important;
}

.duration-display {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  /* inherit the footer's contrast-aware color (was hardcoded white) */
  color: currentColor;
  font-weight: 500;
}

.duration-text-footer {
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 0.5px;
}

/* Processing Status */
.job-status-body {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 12px;
  margin-top: 8px;
  border-radius: 4px;
}

.job-status-chip-body {
  max-width: 100%;
  white-space: normal;
  height: auto !important;
  padding: 4px 10px;
}

.job-status-chip-body :deep(.v-chip__content) {
  white-space: normal;
  word-break: break-word;
}

.processing-status-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
}

.status-processing {
  background-color: rgba(33, 150, 243, 0.1);
  border-left: 3px solid #2196F3;
}

.status-failed {
  background-color: rgba(211, 47, 47, 0.1);
  border-left: 3px solid #D32F2F;
}

.status-icon {
  flex-shrink: 0;
}

.status-text {
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

/* Retry Section */
.retry-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-outline), 0.2);
  display: flex;
  justify-content: center;
}

/* Responsive Design */
@media (max-width: 600px) {
  .cue-card-header {
    padding: 8px 12px !important;
  }

  .cue-card-content {
    padding: 12px !important;
  }

  .placeholder-container {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }

  .primary-message {
    font-size: 0.9rem;
  }
}

/* ---- Orbital Action Menu ---- */
.orbital-menu {
  position: relative;
  display: inline-flex;
  align-items: center;
  height: 28px;
}

.orbital-trigger {
  opacity: 0.7;
  transition: opacity 0.2s;
  z-index: 2;
}

.orbital-open .orbital-trigger {
  opacity: 1;
}

.orbital-icon-spin {
  transition: transform 0.3s ease;
  transform: rotate(90deg);
}

.orbital-btn {
  position: absolute;
  bottom: 0;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 1;
  background: rgba(50, 50, 50, 0.95) !important;
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(4px);
}

.orbital-btn:hover {
  background: rgba(80, 80, 80, 1) !important;
  border-color: rgba(255, 255, 255, 0.6);
}

/* Closed state: all buttons stacked at trigger position */
.orbital-btn.orbital-pos-1,
.orbital-btn.orbital-pos-2,
.orbital-btn.orbital-pos-3,
.orbital-btn.orbital-pos-last {
  transform: translateX(0);
}

/* Open state: spread left in a row with fixed spacing */
.orbital-open .orbital-btn {
  opacity: 1;
  pointer-events: auto;
}
.orbital-open .orbital-pos-1 {
  transform: translateX(-32px);
  transition-delay: 0s;
}
.orbital-open .orbital-pos-2 {
  transform: translateX(-60px);
  transition-delay: 0.03s;
}
.orbital-open .orbital-pos-3 {
  transform: translateX(-88px);
  transition-delay: 0.06s;
}
.orbital-open .orbital-pos-last {
  transform: translateX(-116px);
  transition-delay: 0.09s;
}

/* Transition group classes */
.orbital-item-enter-active {
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.orbital-item-leave-active {
  transition: opacity 0.15s ease-in, transform 0.15s ease-in;
}
.orbital-item-enter-from,
.orbital-item-leave-to {
  opacity: 0;
  transform: translateX(0) !important;
}
</style>