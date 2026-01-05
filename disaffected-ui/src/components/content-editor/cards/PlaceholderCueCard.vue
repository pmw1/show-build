<template>
  <v-card
    class="cue-card placeholder-cue-card"
    :class="[
      { 'selected': selected },
      { 'rif-card-align': cueData.type === 'RIF' },
      { 'cue-complete': cueStatus === 'complete' },
      { 'cue-needs-attention': cueStatus === 'needs_attention' },
      { 'cue-urgent-attention': cueStatus === 'urgent_attention' },
      getAnalysisClass
    ]"
    :style="cardStyleWithStatus"
    variant="elevated"
    @click="$emit('select')"
  >
    <!-- Three-state checkbox in upper right corner -->
    <!-- States: unchecked -> complete (green) -> needs_attention (yellow) -> urgent_attention (red) -> unchecked -->
    <div
      class="cue-checkbox-container"
      :class="checkboxContainerClass"
      @click.stop="cycleCheckboxState"
    >
      <v-icon
        :color="checkboxIconColor"
        size="24"
      >
        {{ checkboxIcon }}
      </v-icon>
      <v-tooltip activator="parent" location="left">
        {{ checkboxTooltip }}
      </v-tooltip>
    </div>
    <!-- Card Header -->
    <v-card-title class="cue-card-header" :style="headerStyleWithStatus">
      <v-icon size="small" class="drag-handle" style="cursor: grab; margin-right: 8px;">mdi-drag-vertical</v-icon>
      <div class="cue-type-badge" :style="badgeStyle">
        {{ cueData.type }}
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
        <div class="cue-actions">
          <v-btn
            icon
            size="small"
            variant="text"
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
            @click.stop="$emit('delete')"
            class="action-btn delete-btn"
          >
            <v-icon size="small">mdi-delete</v-icon>
            <v-tooltip activator="parent" location="top">Delete Cue</v-tooltip>
          </v-btn>
        </div>
        <div class="duration-display-header">
          <v-icon size="small" color="white">mdi-timer-outline</v-icon>
          <span class="duration-text-header">{{ cueData.duration || '00:00:00:00' }}</span>
        </div>
      </template>

      <!-- Non-RIF: Show action buttons in header -->
      <div v-if="cueData.type !== 'RIF'" class="cue-actions">
        <v-btn
          icon
          size="small"
          variant="text"
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
          @click.stop="$emit('delete')"
          class="action-btn delete-btn"
        >
          <v-icon size="small">mdi-delete</v-icon>
          <v-tooltip activator="parent" location="top">Delete Cue</v-tooltip>
        </v-btn>
      </div>
    </v-card-title>

    <!-- Card Content (hidden entirely for RIF) -->
    <v-card-text v-if="cueData.type !== 'RIF'" class="cue-card-content">
      <!-- FSQ-specific Display - Redesigned 75/25 Layout -->
      <div v-if="cueData.type === 'FSQ' && cueData.quote" class="fsq-redesigned-container">
        <!-- Left Side: 75% - Quote Text (selectable/copyable) -->
        <div class="fsq-quote-side">
          <div class="fsq-quote-block">
            <v-icon size="32" :color="cueTypeColor" class="fsq-quote-icon-left">mdi-format-quote-open</v-icon>
            <div class="fsq-quote-full-text" @click="selectQuoteText">{{ cueData.quote }}</div>
            <v-icon size="32" :color="cueTypeColor" class="fsq-quote-icon-right">mdi-format-quote-close</v-icon>
          </div>
          <div v-if="cueData.attribution" class="fsq-attribution-full">
            — {{ cueData.attribution }}
          </div>
        </div>

        <!-- Right Side: 25% - Thumbnail Preview + Parameters -->
        <div class="fsq-params-side">
          <!-- Regenerate Button (sync style) -->
          <v-btn
            size="small"
            variant="outlined"
            color="primary"
            @click.stop="handleGeneratePNG"
            :loading="generatingPNG"
            class="fsq-regenerate-btn"
          >
            <v-icon size="small" start>mdi-sync</v-icon>
            {{ cueData.mediaUrl ? 'Regenerate' : 'Generate' }}
          </v-btn>

          <!-- Thumbnail Preview with Motion Background -->
          <div class="fsq-thumbnail-container" :style="thumbnailBackgroundStyle">
            <img
              v-if="cueData.mediaUrl"
              :src="fsqThumbnailUrl"
              class="fsq-thumbnail-img"
              @error="handleThumbnailError"
            />
            <div v-else class="fsq-thumbnail-placeholder">
              <v-icon size="24" color="grey-darken-1">mdi-image-off</v-icon>
              <span class="fsq-placeholder-text">No PNG</span>
            </div>
          </div>

          <!-- Editable Parameters -->
          <div class="fsq-params-controls">
            <!-- Font Family -->
            <div class="fsq-param-row">
              <label class="fsq-param-label">Font</label>
              <v-select
                v-model="localFontFamily"
                :items="fontFamilyOptions"
                density="compact"
                hide-details
                variant="outlined"
                class="fsq-param-select"
                @update:model-value="emitParamChange('fontFamily', $event)"
              />
            </div>

            <!-- Box Height % -->
            <div class="fsq-param-row">
              <label class="fsq-param-label">Box Height</label>
              <v-slider
                v-model="localBoxHeight"
                :min="50"
                :max="100"
                :step="5"
                density="compact"
                hide-details
                thumb-label
                color="primary"
                class="fsq-param-slider"
                @update:model-value="emitParamChange('boxHeight', $event)"
              />
            </div>

            <!-- Box Opacity % -->
            <div class="fsq-param-row">
              <label class="fsq-param-label">Opacity</label>
              <v-slider
                v-model="localBoxOpacity"
                :min="50"
                :max="100"
                :step="5"
                density="compact"
                hide-details
                thumb-label
                color="primary"
                class="fsq-param-slider"
                @update:model-value="emitParamChange('boxOpacity', $event)"
              />
            </div>

            <!-- Line Spacing % -->
            <div class="fsq-param-row">
              <label class="fsq-param-label">Line Spacing</label>
              <v-slider
                v-model="localLineSpacing"
                :min="10"
                :max="60"
                :step="5"
                density="compact"
                hide-details
                thumb-label
                color="primary"
                class="fsq-param-slider"
                @update:model-value="emitParamChange('lineSpacing', $event)"
              />
            </div>

            <!-- Alignment -->
            <div class="fsq-param-row">
              <label class="fsq-param-label">Align</label>
              <v-btn-toggle
                v-model="localAlignment"
                mandatory
                density="compact"
                class="fsq-param-toggle"
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
          </div>
        </div>
      </div>

      <!-- SOT Display with Thumbnail, Video and Transcription -->
      <div v-else-if="cueData.type?.toUpperCase() === 'SOT'" class="sot-container">
        <!-- Inline Video Player (discreet, toggleable) -->
        <div v-if="showInlinePlayer && sotVideoUrl" class="sot-inline-player-container">
          <div class="sot-inline-player-header">
            <span class="sot-inline-player-title">Video Preview</span>
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
            ref="inlineVideoPlayer"
            :src="sotVideoUrl"
            controls
            class="sot-inline-video"
            @loadedmetadata="onVideoLoaded"
          ></video>
        </div>

        <!-- Thumbnail + Info Layout (when completed or has thumbnail) -->
        <div v-if="sotThumbnailUrl || (jobStatus && jobStatus.status === 'completed')" class="sot-completed-layout">
          <!-- Left: Thumbnail with navigation -->
          <div class="sot-thumbnail-wrapper">
            <div class="sot-thumbnail-section">
              <img
                v-if="currentSotThumbnailUrl"
                :src="currentSotThumbnailUrl"
                class="sot-thumbnail-img"
                @click="toggleInlinePlayer"
                @error="handleSotThumbnailError"
              />
              <div v-else class="sot-thumbnail-placeholder">
                <v-icon size="48" color="grey-darken-1">mdi-video-outline</v-icon>
                <span class="sot-placeholder-text">No Thumbnail</span>
              </div>
              <!-- Play overlay icon -->
              <div v-if="currentSotThumbnailUrl" class="sot-play-overlay" @click.stop="toggleInlinePlayer">
                <v-icon size="48" color="white">mdi-play-circle</v-icon>
              </div>
              <!-- Completion badge -->
              <div v-if="jobStatus && jobStatus.status === 'completed'" class="sot-complete-badge">
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
            <div v-if="cueData.duration || (jobStatus && jobStatus.post_analysis)" class="sot-info-row">
              <v-icon size="small" color="primary">mdi-timer-outline</v-icon>
              <span class="sot-info-label">Duration:</span>
              <span class="sot-info-value">{{ cueData.duration || jobStatus?.post_analysis?.duration || '—' }}</span>
            </div>

            <!-- Media URL -->
            <div v-if="cueData.mediaUrl || (jobStatus && jobStatus.final_video_path)" class="sot-info-row">
              <v-icon size="small" color="primary">mdi-video</v-icon>
              <span class="sot-info-label">Video:</span>
              <span class="sot-info-value sot-media-path">{{ formatMediaPath(cueData.mediaUrl || jobStatus?.final_video_path) }}</span>
            </div>

            <!-- Processing Status -->
            <div v-if="cueData.processingStatus" class="sot-info-row">
              <v-icon size="small" color="success">mdi-check-circle</v-icon>
              <span class="sot-info-label">Status:</span>
              <span class="sot-info-value">{{ cueData.processingStatus }}</span>
            </div>

            <!-- Transcription Preview -->
            <div v-if="sotTranscription" class="sot-transcription-preview">
              <v-icon size="small" color="primary">mdi-text</v-icon>
              <span class="sot-transcription-text">{{ truncateTranscription(sotTranscription) }}</span>
              <v-tooltip activator="parent" location="top" max-width="400">
                <span style="white-space: pre-wrap;">{{ sotTranscription }}</span>
              </v-tooltip>
            </div>
          </div>
        </div>

        <!-- Outcue Display - Full Width at Bottom -->
        <div v-if="sotOutcue" class="sot-outcue-banner">
          <span class="sot-outcue-label">OUTCUE:</span>
          <span class="sot-outcue-text">{{ sotOutcue }}</span>
        </div>

        <!-- Processing In Progress (no thumbnail yet) -->
        <div v-else-if="jobStatus && jobStatus.status === 'processing'" class="sot-processing-layout">
          <v-progress-circular indeterminate size="40" width="3" color="primary"></v-progress-circular>
          <div class="sot-processing-info">
            <div class="sot-processing-phase">{{ jobStatus.current_phase || 'Processing...' }}</div>
            <div class="sot-processing-message">Video is being processed</div>
          </div>
        </div>

        <!-- No Job Status Yet -->
        <div v-else class="sot-pending-layout">
          <v-icon size="48" color="grey-lighten-1">mdi-video-off-outline</v-icon>
          <span class="sot-pending-text">Awaiting processing</span>
        </div>
      </div>

      <!-- Generic Placeholder Display for non-SOT, non-FSQ -->
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

      <!-- Cue Information (hidden for FSQ) -->
      <div v-if="cueData.type !== 'FSQ'" class="cue-info">
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

        <!-- Processing Status Display -->
        <div v-if="processingStatusMessage" class="processing-status" :class="{ 'status-failed': isFailed, 'status-processing': isProcessing }">
          <v-icon size="small" class="status-icon" :color="isFailed ? 'error' : 'info'">
            {{ isFailed ? 'mdi-alert-circle' : 'mdi-cog' }}
          </v-icon>
          <span class="status-text">{{ processingStatusMessage }}</span>
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

    <!-- Card Footer (hidden for RIF) -->
    <v-card-actions v-if="cueData.type !== 'RIF'" class="cue-card-footer" :style="footerStyle">
      <!-- Delete Cue Button - Left side -->
      <v-btn
        size="x-small"
        variant="text"
        color="white"
        @click.stop="$emit('delete')"
        class="delete-cue-btn"
      >
        <v-icon size="small">mdi-delete</v-icon>
        <span style="margin-left: 4px;">Delete</span>
        <v-tooltip activator="parent" location="top">
          Delete this cue
        </v-tooltip>
      </v-btn>

      <!-- Show duration in footer -->
      <div class="duration-display">
        <v-icon size="small" color="white">mdi-timer-outline</v-icon>
        <span class="duration-text-footer">{{ cueData.duration || '00:00:00:00' }}</span>
      </div>

      <v-spacer></v-spacer>

      <!-- Job Status Indicator (SOT only) -->
      <v-chip
        v-if="showJobStatus && jobStatus"
        :color="jobStatusColor"
        size="small"
        class="job-status-chip"
        style="margin-right: 8px;"
      >
        <v-icon size="x-small" start>
          {{ jobStatus.status === 'processing' ? 'mdi-loading mdi-spin' :
             jobStatus.status === 'completed' ? 'mdi-check-circle' :
             jobStatus.status === 'failed' ? 'mdi-alert-circle' :
             'mdi-clock-outline' }}
        </v-icon>
        {{ jobStatusText }}
        <v-tooltip activator="parent" location="top">
          <div v-if="jobStatus.error_message">
            <strong>Error:</strong> {{ jobStatus.error_message }}
          </div>
          <div v-else>
            Job Status: {{ jobStatus.status }}<br>
            Phase: {{ jobStatus.current_phase || 'N/A' }}<br>
            Updated: {{ new Date(jobStatus.updated_at).toLocaleTimeString() }}
          </div>
        </v-tooltip>
      </v-chip>

      <!-- Reprocess Button (SOT only) -->
      <v-btn
        v-if="showReprocessButton"
        size="x-small"
        variant="text"
        color="white"
        @click.stop="handleReprocess"
        class="reprocess-btn"
      >
        <v-icon size="small">mdi-refresh</v-icon>
        <span style="margin-left: 4px;">Reprocess</span>
        <v-tooltip activator="parent" location="top">
          Clean up and restart video processing
        </v-tooltip>
      </v-btn>

      <!-- Generate PNG Button (FSQ only) -->
      <v-btn
        v-if="cueData.type === 'FSQ'"
        size="x-small"
        variant="text"
        color="white"
        @click.stop="handleGeneratePNG"
        :loading="generatingPNG"
        class="generate-png-btn"
      >
        <v-icon size="small">mdi-image-auto-adjust</v-icon>
        <span style="margin-left: 4px;">Generate PNG</span>
        <v-tooltip activator="parent" location="top">
          Generate full-screen quote PNG graphic using Celery worker
        </v-tooltip>
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '../../../utils/themeColorMap.js';
import { useSOTProcessing } from '../../../composables/useSOTProcessing.js';

export default {
  name: 'PlaceholderCueCard',
  emits: ['select', 'edit', 'delete', 'update-meta'],
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
    },
    currentEpisode: {
      type: String,
      default: ''
    }
  },
  setup() {
    const { getJobByAssetId, retryFailedJob, reprocessJob } = useSOTProcessing();

    return {
      getJobByAssetId,
      retryFailedJob,
      reprocessJob
    };
  },
  data() {
    return {
      generatingPNG: false,
      jobStatus: null,        // Current job status from API
      statusPollInterval: null, // Interval ID for polling
      currentThumbnailIndex: 7, // Default to middle thumbnail (index 7 = thumb 8 of 15)
      pollingActive: false,    // Whether we're currently polling
      // Three-state cue status: null (unchecked), 'complete', 'needs_attention', 'urgent_attention'
      cueStatus: this.cueData?.cue_status || null,
      // FSQ editable parameters (local state)
      localFontFamily: this.cueData?.fontFamily || 'sans-serif',
      localBoxHeight: parseInt(this.cueData?.boxHeight) || 80,
      localBoxOpacity: parseInt(this.cueData?.boxOpacity) || 75,
      localLineSpacing: parseInt(this.cueData?.lineSpacing) || 30,
      localAlignment: this.cueData?.alignment || this.cueData?.style || 'center',
      thumbnailError: false,
      // Font family options
      fontFamilyOptions: [
        { title: 'Sans-Serif', value: 'sans-serif' },
        { title: 'Serif', value: 'serif' }
      ],
      // Inline video player state
      showInlinePlayer: false
    };
  },
  computed: {
    /**
     * Checkbox icon based on cue_status
     */
    checkboxIcon() {
      switch (this.cueStatus) {
        case 'complete':
          return 'mdi-checkbox-marked';
        case 'needs_attention':
          return 'mdi-alert-box';
        case 'urgent_attention':
          return 'mdi-close-box';
        default:
          return 'mdi-checkbox-blank-outline';
      }
    },

    /**
     * Checkbox icon color based on cue_status
     */
    checkboxIconColor() {
      switch (this.cueStatus) {
        case 'complete':
          return 'white';
        case 'needs_attention':
          return '#1a1a1a';  // Dark for contrast on yellow
        case 'urgent_attention':
          return 'white';
        default:
          return 'grey-darken-1';
      }
    },

    /**
     * Checkbox container CSS class based on cue_status
     */
    checkboxContainerClass() {
      switch (this.cueStatus) {
        case 'complete':
          return 'checkbox-complete';
        case 'needs_attention':
          return 'checkbox-needs-attention';
        case 'urgent_attention':
          return 'checkbox-urgent-attention';
        default:
          return '';
      }
    },

    /**
     * Tooltip text for checkbox based on current state
     */
    checkboxTooltip() {
      switch (this.cueStatus) {
        case 'complete':
          return 'Click: Needs Attention';
        case 'needs_attention':
          return 'Click: URGENT ATTENTION';
        case 'urgent_attention':
          return 'Click: Clear status';
        default:
          return 'Click: Mark Complete';
      }
    },

    /**
     * Card style based on cue_status
     */
    cardStyleWithStatus() {
      const baseStyle = this.getCardStyle;

      switch (this.cueStatus) {
        case 'complete':
          return {
            ...baseStyle,
            backgroundColor: '#C8E6C9',  // Light green background
            borderColor: '#4CAF50'       // Green border
          };
        case 'needs_attention':
          return {
            ...baseStyle,
            // Keep body background unchanged, just border
            borderColor: '#FFC107'       // Yellow/amber border
          };
        case 'urgent_attention':
          return {
            ...baseStyle,
            // Keep body background unchanged, just border
            borderColor: '#D32F2F',      // Red border
            borderWidth: '5px'           // Slightly thicker for urgency
          };
        default:
          return baseStyle;
      }
    },

    /**
     * Header style based on cue_status
     */
    headerStyleWithStatus() {
      switch (this.cueStatus) {
        case 'complete':
          return {
            backgroundColor: '#388E3C',  // Darker green header
            color: 'white'
          };
        case 'needs_attention':
          return {
            backgroundColor: '#FFD54F',  // Bright yellow header
            color: '#1a1a1a'             // Dark text for readability
          };
        case 'urgent_attention':
          return {
            backgroundColor: '#D32F2F',  // Red header
            color: 'white'
          };
        default:
          return this.headerStyle;
      }
    },

    formatCueTitle() {
      const title = this.cueData.slug || this.cueData.title || '';

      // For RIF cues: remove hyphens and capitalize each word
      if (this.cueData.type === 'RIF') {
        return title
          .split('-')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
          .join(' ');
      }

      // For all other cues: return as-is
      return title;
    },

    /**
     * Get all SOT thumbnail options (array of URLs)
     */
    sotThumbnailOptions() {
      // First check cue data for ThumbnailOptions (array from processing)
      if (this.cueData?.thumbnailOptions && Array.isArray(this.cueData.thumbnailOptions)) {
        return this.cueData.thumbnailOptions.map(url => {
          if (url.startsWith('/episodes') || url.startsWith('http')) {
            return url;
          }
          return `/episodes/${url}`;
        });
      }

      // Check job status for thumbnail_candidates (from database)
      if (this.jobStatus?.thumbnail_candidates && Array.isArray(this.jobStatus.thumbnail_candidates)) {
        // These are filenames like "sot_xxx_4_thumb_01.jpg", need to build full path
        const basePath = this.jobStatus.final_video_path?.replace(/\.mp4$/, '') || '';
        if (basePath) {
          const dirPath = basePath.substring(0, basePath.lastIndexOf('/'));
          const slug = basePath.substring(basePath.lastIndexOf('/') + 1);
          return this.jobStatus.thumbnail_candidates.map((_, i) => {
            return `/episodes/${dirPath}/${slug}-thumb-${String(i + 1).padStart(2, '0')}.jpg`;
          });
        }
      }

      // Generate options based on single thumbnail URL pattern
      if (this.sotThumbnailUrl) {
        // Try to extract base pattern (e.g., /episodes/0251/assets/thumbnails/slug-thumb-08.jpg)
        const match = this.sotThumbnailUrl.match(/^(.+)-thumb-(\d+)\.jpg$/);
        if (match) {
          const base = match[1];
          // Generate 15 thumbnail URLs
          return Array.from({ length: 15 }, (_, i) => `${base}-thumb-${String(i + 1).padStart(2, '0')}.jpg`);
        }
      }

      // Single thumbnail fallback
      if (this.sotThumbnailUrl) {
        return [this.sotThumbnailUrl];
      }

      return [];
    },

    /**
     * Get current thumbnail URL based on selected index
     */
    currentSotThumbnailUrl() {
      const options = this.sotThumbnailOptions;
      if (options.length === 0) return '';

      // Ensure index is within bounds
      const index = Math.min(Math.max(0, this.currentThumbnailIndex), options.length - 1);
      return options[index] || options[0];
    },

    /**
     * Get SOT thumbnail URL from cue data or job status (base/primary thumbnail)
     */
    sotThumbnailUrl() {
      // First check cue data for ThumbnailURL
      if (this.cueData?.thumbnailUrl) {
        // If it's a relative path, prepend /episodes
        if (this.cueData.thumbnailUrl.startsWith('/episodes') || this.cueData.thumbnailUrl.startsWith('http')) {
          return this.cueData.thumbnailUrl;
        }
        return `/episodes/${this.cueData.thumbnailUrl}`;
      }

      // Fall back to job status thumbnail path
      if (this.jobStatus?.final_thumbnail_path) {
        return `/episodes/${this.jobStatus.final_thumbnail_path}`;
      }

      return '';
    },

    /**
     * Get SOT transcription from cue data or job status
     */
    sotTranscription() {
      // First check cue data (from parsed cue block)
      if (this.cueData?.transcription) {
        return this.cueData.transcription;
      }
      // Fall back to job status transcription
      if (this.jobStatus?.transcription) {
        return this.jobStatus.transcription;
      }
      return '';
    },

    /**
     * Get SOT outcue from cue data (last 5 words of transcription with "..." prefix)
     */
    sotOutcue() {
      // Check cue data for outcue field
      if (this.cueData?.outcue) {
        return this.cueData.outcue;
      }
      return '';
    },

    /**
     * Get SOT video URL for inline player
     */
    sotVideoUrl() {
      // First check cue data for MediaURL
      if (this.cueData?.mediaUrl) {
        if (this.cueData.mediaUrl.startsWith('/episodes') || this.cueData.mediaUrl.startsWith('http')) {
          return this.cueData.mediaUrl;
        }
        return `/episodes/${this.cueData.mediaUrl}`;
      }

      // Fall back to job status final video path
      if (this.jobStatus?.final_video_path) {
        return `/episodes/${this.jobStatus.final_video_path}`;
      }

      return '';
    },

    /**
     * Get FSQ thumbnail URL - use mediaUrl from cue data
     */
    fsqThumbnailUrl() {
      if (!this.cueData?.mediaUrl) return '';
      // If it's already a full URL, use it; otherwise prepend /episodes
      if (this.cueData.mediaUrl.startsWith('http') || this.cueData.mediaUrl.startsWith('/')) {
        return this.cueData.mediaUrl;
      }
      // Build episode-relative URL
      const episode = this.$route?.params?.episode || '';
      return `/episodes/${episode}/assets/quotes/${this.cueData.mediaUrl}`;
    },

    /**
     * Get motion background style for FSQ thumbnail container
     * Uses fsqBackgroundVideo from settings
     */
    thumbnailBackgroundStyle() {
      // Get FSQ background video from settings (localStorage)
      // Note: Video backgrounds require special handling with <video> element
      // For now, use a gradient as CSS background fallback
      // TODO: Implement video background with poster frame extraction
      return {
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        backgroundSize: 'cover'
      };
    },

    showReprocessButton() {
      const isSOT = this.cueData.type?.toUpperCase() === 'SOT';
      // Check both assetId (camelCase) and assetid (lowercase from parser)
      const hasAssetId = !!(this.cueData.assetId || this.cueData.assetid);
      const actualAssetId = this.cueData.assetId || this.cueData.assetid;
      console.log(`🔍 PlaceholderCueCard: type=${this.cueData.type}, assetId=${this.cueData.assetId}, assetid=${this.cueData.assetid}, actualAssetId=${actualAssetId}, showButton=${isSOT && hasAssetId}`);
      return isSOT && hasAssetId;
    },

    showJobStatus() {
      // Show status for SOT cues that have an AssetID (case-insensitive check)
      return this.cueData.type?.toUpperCase() === 'SOT' && !!(this.cueData.assetId || this.cueData.assetid);
    },

    jobStatusText() {
      if (!this.jobStatus) return '';

      const status = this.jobStatus.status;
      const phase = this.jobStatus.current_phase;

      if (status === 'processing' && phase) {
        const phaseNames = {
          'phase1': 'Analyzing',
          'phase2': 'Processing Clips',
          'phase3': 'Finalizing'
        };
        return phaseNames[phase] || phase;
      }
      return status;
    },

    jobStatusColor() {
      if (!this.jobStatus) return 'grey';

      const status = this.jobStatus.status;
      const phase = this.jobStatus.current_phase;

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

    footerStyle() {
      const backgroundColor = this.cueTypeColor;
      return {
        backgroundColor: backgroundColor,
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

      // Check for processing job status
      if (this.processingJob) {
        if (this.processingJob.status === 'failed') {
          // Red 7px border for failed processing
          return {
            borderColor: '#D32F2F',
            borderWidth: '7px',
            borderStyle: 'solid'
          };
        } else if (this.processingJob.status === 'processing') {
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

      // Default: use cue type color with 4px border
      return {
        borderColor: this.cueTypeColor,
        borderWidth: '4px',
        borderStyle: 'solid'
      };
    },

    /**
     * Get processing job for this cue's asset
     */
    processingJob() {
      if (!this.cueData?.assetId) return null;
      return this.getJobByAssetId(this.cueData.assetId);
    },

    /**
     * Check if this cue is currently processing
     */
    isProcessing() {
      return this.processingJob?.status === 'processing';
    },

    /**
     * Check if this cue's processing failed
     */
    isFailed() {
      return this.processingJob?.status === 'failed';
    },

    /**
     * Get processing status message
     */
    processingStatusMessage() {
      if (!this.processingJob) return null;

      const job = this.processingJob;
      if (job.status === 'processing') {
        return job.phase_message || job.current_phase || 'Processing...';
      } else if (job.status === 'failed') {
        return 'Processing failed';
      }
      return null;
    }
  },
  methods: {
    /**
     * Navigate to previous thumbnail
     */
    prevThumbnail() {
      if (this.currentThumbnailIndex > 0) {
        this.currentThumbnailIndex--;
        this.emitSelectedThumbnail();
      }
    },

    /**
     * Navigate to next thumbnail
     */
    nextThumbnail() {
      if (this.currentThumbnailIndex < this.sotThumbnailOptions.length - 1) {
        this.currentThumbnailIndex++;
        this.emitSelectedThumbnail();
      }
    },

    /**
     * Emit selected thumbnail to parent for saving to cue block
     */
    emitSelectedThumbnail() {
      const selectedUrl = this.currentSotThumbnailUrl;
      console.log(`🖼️ Selected thumbnail ${this.currentThumbnailIndex + 1}: ${selectedUrl}`);
      this.$emit('update-meta', {
        assetId: this.cueData.assetId || this.cueData.assetid,
        field: 'thumbnailUrl',
        value: selectedUrl
      });
    },

    /**
     * Handle SOT thumbnail error
     */
    handleSotThumbnailError() {
      console.warn('SOT thumbnail failed to load:', this.currentSotThumbnailUrl);
    },

    /**
     * Toggle inline video player visibility
     */
    toggleInlinePlayer() {
      if (this.sotVideoUrl) {
        this.showInlinePlayer = !this.showInlinePlayer;
        // Auto-play when opening
        if (this.showInlinePlayer) {
          this.$nextTick(() => {
            if (this.$refs.inlineVideoPlayer) {
              this.$refs.inlineVideoPlayer.play();
            }
          });
        }
      } else {
        // Fallback: open in new tab if no video URL available
        this.openVideoPlayer();
      }
    },

    /**
     * Handle video metadata loaded
     */
    onVideoLoaded() {
      console.log('Inline video loaded:', this.sotVideoUrl);
    },

    /**
     * Open video player for SOT (in new tab)
     */
    openVideoPlayer() {
      const videoPath = this.cueData.mediaUrl || this.jobStatus?.final_video_path;
      if (videoPath) {
        const fullPath = videoPath.startsWith('/episodes') ? videoPath : `/episodes/${videoPath}`;
        window.open(fullPath, '_blank');
      }
    },

    /**
     * Format media path for display (truncate long paths)
     */
    formatMediaPath(path) {
      if (!path) return '';
      // Show just the filename
      const parts = path.split('/');
      return parts[parts.length - 1] || path;
    },

    /**
     * Truncate transcription for preview
     */
    truncateTranscription(text) {
      if (!text) return '';
      if (text.length <= 100) return text;
      return text.substring(0, 100) + '...';
    },

    /**
     * Cycle through checkbox states: null -> complete -> needs_attention -> urgent_attention -> null
     */
    cycleCheckboxState() {
      // Define the state cycle
      const states = [null, 'complete', 'needs_attention', 'urgent_attention'];
      const currentIndex = states.indexOf(this.cueStatus);
      const nextIndex = (currentIndex + 1) % states.length;
      this.cueStatus = states[nextIndex];

      const statusLabels = {
        null: 'unchecked',
        'complete': 'Complete',
        'needs_attention': 'Needs Attention',
        'urgent_attention': 'URGENT ATTENTION'
      };
      console.log(`📋 Cue ${this.cueData.assetId || this.cueData.slug} status: ${statusLabels[this.cueStatus]}`);

      // Emit to parent for persistence in YAML frontmatter
      this.$emit('update-meta', {
        assetId: this.cueData.assetId,
        field: 'cue_status',
        value: this.cueStatus
      });
    },

    /**
     * Emit parameter change to parent for cue data update
     */
    emitParamChange(paramName, value) {
      console.log(`📝 FSQ param changed: ${paramName} = ${value}`);
      this.$emit('update-meta', {
        assetId: this.cueData.assetId,
        field: paramName,
        value: value
      });
    },

    /**
     * Select quote text for copying
     */
    selectQuoteText(event) {
      const textElement = event.target;
      if (window.getSelection && document.createRange) {
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(textElement);
        selection.removeAllRanges();
        selection.addRange(range);
      }
    },

    /**
     * Handle thumbnail load error
     */
    handleThumbnailError() {
      console.warn('FSQ thumbnail failed to load:', this.cueData.mediaUrl);
      this.thumbnailError = true;
    },

    getCueIcon(cueType) {
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
    },

    truncateUrl(url) {
      if (!url) return '';
      if (url.length <= 40) return url;

      const start = url.substring(0, 20);
      const end = url.substring(url.length - 17);
      return `${start}...${end}`;
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
    },

    /**
     * Handle retry button click
     */
    async handleRetry() {
      if (!this.processingJob?.temp_job_id) {
        console.error('Cannot retry: no temp_job_id found');
        return;
      }

      console.log(`🔄 Retrying failed job from cue card: ${this.processingJob.temp_job_id}`);
      const success = await this.retryFailedJob(this.processingJob.temp_job_id);

      if (success) {
        console.log('✅ Retry initiated successfully');
      }
    },

    /**
     * Handle reprocess button click - Clean up and restart processing
     */
    async handleReprocess() {
      const assetId = this.cueData.assetId || this.cueData.assetid;
      if (!assetId) {
        console.error('Cannot reprocess: no assetId found');
        return;
      }

      console.log(`🔄 Reprocessing SOT from cue card: ${assetId}`);
      const success = await this.reprocessJob(assetId);

      if (success) {
        console.log('✅ Reprocess initiated successfully');
      } else {
        console.error('❌ Retry failed');
      }
    },

    /**
     * Handle Generate PNG button click - Queue Celery task for FSQ PNG generation
     */
    async handleGeneratePNG() {
      if (!this.cueData.assetId) {
        console.error('Cannot generate PNG: no assetId found');
        alert('Error: No Asset ID found for this quote');
        return;
      }

      if (!this.cueData.quote) {
        console.error('Cannot generate PNG: no quote text found');
        alert('Error: No quote text found');
        return;
      }

      try {
        this.generatingPNG = true;
        console.log(`🎨 Generating FSQ PNG for: ${this.cueData.assetId}`);

        const token = localStorage.getItem('auth-token');
        // Use prop first, then fallback to route params
        const episode = this.currentEpisode || this.$route?.params?.episode || '';

        const requestData = {
          episode_id: episode,
          quote: this.cueData.quote,
          attribution: this.cueData.attribution || this.cueData.source || '',
          slug: this.cueData.slug || 'quote',
          asset_id: this.cueData.assetId,
          alignment: this.cueData.alignment || this.cueData.style || 'center',
          font_family: this.cueData.fontFamily || 'serif',
          font_size: this.cueData.fontSize || 70,
          duration: this.cueData.duration || '00:00:05:00'
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

        // Show success notification
        alert(`FSQ PNG generation started!\n\nTask ID: ${result.task_id}\n\nThe PNG will be generated by a Celery worker. Check the assets folder in a few seconds.`);

        // Optionally, poll for completion
        this.pollTaskStatus(result.task_id);

      } catch (error) {
        console.error('❌ Error generating FSQ PNG:', error);
        alert(`Error generating PNG: ${error.message}`);
      } finally {
        this.generatingPNG = false;
      }
    },

    /**
     * Poll Celery task status until completion
     */
    async pollTaskStatus(taskId, maxAttempts = 30) {
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
              alert(`PNG generated successfully!\n\nFilename: ${status.result.filename}\nPath: ${status.result.asset_path}`);
            } else {
              console.error('❌ PNG generation failed:', status.error);
              alert(`PNG generation failed: ${status.error}`);
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
    },

    /**
     * Fetch job status from API by AssetID
     */
    async fetchJobStatus() {
      const assetId = this.cueData.assetId || this.cueData.assetid;

      console.log('🔍 fetchJobStatus called for cue:', {
        slug: this.cueData.slug,
        type: this.cueData.type,
        assetId: assetId,
        cueData: this.cueData
      });

      if (!assetId) {
        console.warn('⚠️ No AssetID found in cue data, cannot fetch job status');
        return;
      }

      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`/api/sot/job-status/${assetId}`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });

        if (!response.ok) {
          console.error(`Failed to fetch job status for ${assetId}`, response.status);
          return;
        }

        const status = await response.json();
        this.jobStatus = status;

        console.log(`📊 Job status for ${assetId}:`, status);

        // Stop polling if job is in terminal state
        if (status.status === 'completed' || status.status === 'failed' || status.status === 'not_found') {
          this.stopPolling();
        }
      } catch (error) {
        console.error('Error fetching job status:', error);
      }
    },

    /**
     * Start polling for job status updates
     */
    startPolling() {
      if (this.pollingActive) return;

      this.pollingActive = true;

      // Fetch immediately
      this.fetchJobStatus();

      // Then poll every 3 seconds
      this.statusPollInterval = setInterval(() => {
        this.fetchJobStatus();
      }, 3000);

      console.log('📡 Started polling job status');
    },

    /**
     * Stop polling for job status updates
     */
    stopPolling() {
      if (this.statusPollInterval) {
        clearInterval(this.statusPollInterval);
        this.statusPollInterval = null;
        this.pollingActive = false;
        console.log('🛑 Stopped polling job status');
      }
    }
  },

  mounted() {
    console.log('🔍 PlaceholderCueCard MOUNTED:', {
      type: this.cueData?.type,
      assetId: this.cueData?.assetId,
      assetid: this.cueData?.assetid,
      allKeys: Object.keys(this.cueData || {}),
      showReprocessButton: this.showReprocessButton
    });

    // Start polling if this is a SOT cue with AssetID
    if (this.showJobStatus) {
      this.startPolling();
    }
  },

  beforeUnmount() {
    // Clean up polling interval
    this.stopPolling();
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
  position: relative;
}

.cue-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cue-card.selected {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

/* Checkbox container in upper right */
.cue-checkbox-container {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 20;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.9);
  transition: background-color 0.2s ease;
}

.cue-checkbox-container:hover {
  background-color: rgba(255, 255, 255, 1);
}

/* Three-state checkbox container styles */
.cue-checkbox-container.checkbox-complete {
  background-color: rgba(56, 142, 60, 0.9);  /* Green */
}

.cue-checkbox-container.checkbox-complete:hover {
  background-color: rgba(56, 142, 60, 1);
}

.cue-checkbox-container.checkbox-needs-attention {
  background-color: rgba(255, 193, 7, 0.95);  /* Yellow/amber */
}

.cue-checkbox-container.checkbox-needs-attention:hover {
  background-color: rgba(255, 193, 7, 1);
}

.cue-checkbox-container.checkbox-urgent-attention {
  background-color: rgba(211, 47, 47, 0.95);  /* Red */
}

.cue-checkbox-container.checkbox-urgent-attention:hover {
  background-color: rgba(211, 47, 47, 1);
}

/* Legacy class for backwards compatibility */
.cue-complete .cue-checkbox-container {
  background-color: rgba(56, 142, 60, 0.9);
}

.cue-complete .cue-checkbox-container:hover {
  background-color: rgba(56, 142, 60, 1);
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
  max-width: 75%;
  width: 75%;
  /* Margins removed - alignment now controlled by parent .cue-segment flex container */
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
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
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
  color: white;
}

.action-btn:hover {
  opacity: 1;
}

.delete-btn:hover {
  color: white;
}

/* Duration Display in Header (RIF only) */
.duration-display-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: white;
  font-weight: 500;
  margin-right: 8px;
}

.duration-text-header {
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 0.5px;
}

/* Content Styling */
.cue-card-content {
  padding: 16px !important;
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
  max-height: 200px;
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

/* FSQ Redesigned 75/25 Layout */
.fsq-redesigned-container {
  display: flex;
  gap: 16px;
  width: 100%;
  background-color: #ffffff;
  border-radius: 0;
  padding: 16px;
  min-height: 200px;
}

/* Left side: 75% - Quote text area */
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

/* Right side: 25% - Parameters and thumbnail */
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
}

.fsq-thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
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

/* Delete Cue Button */
.delete-cue-btn {
  opacity: 0.7;
  margin-right: 12px;
}

.delete-cue-btn:hover {
  opacity: 1;
  background-color: rgba(244, 67, 54, 0.2) !important;
}

.duration-display {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: white;
  font-weight: 500;
}

.duration-text-footer {
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 0.5px;
}

/* Processing Status */
.processing-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  padding: 8px 12px;
  border-radius: 4px;
  margin-top: 8px;
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
</style>