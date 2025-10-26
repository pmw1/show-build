<template>
  <v-card
    class="cue-card placeholder-cue-card"
    :class="[
      { 'selected': selected },
      { 'rif-card-align': cueData.type === 'RIF' },
      getAnalysisClass
    ]"
    :style="getCardStyle"
    variant="elevated"
    @click="$emit('select')"
  >
    <!-- Card Header -->
    <v-card-title class="cue-card-header" :style="headerStyle">
      <v-icon size="small" class="drag-handle" style="cursor: grab; margin-right: 8px;">mdi-drag-vertical</v-icon>
      <div class="cue-type-badge" :style="badgeStyle">
        {{ cueData.type }}
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
      <!-- FSQ-specific Display -->
      <div v-if="cueData.type === 'FSQ' && cueData.quote" class="fsq-container">
        <div class="fsq-quote-section">
          <v-icon size="48" :color="cueTypeColor" class="quote-icon">mdi-format-quote-close</v-icon>
          <div class="fsq-quote-text">{{ cueData.quote }}</div>
        </div>
        <div v-if="cueData.attribution" class="fsq-attribution">
          — {{ cueData.attribution }}
        </div>
      </div>

      <!-- Generic Placeholder Display for non-FSQ or FSQ without quote -->
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
  emits: ['select', 'edit', 'delete'],
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
      pollingActive: false    // Whether we're currently polling
    };
  },
  computed: {
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

    showReprocessButton() {
      const isSOT = this.cueData.type === 'SOT';
      // Check both assetId (camelCase) and assetid (lowercase from parser)
      const hasAssetId = !!(this.cueData.assetId || this.cueData.assetid);
      const actualAssetId = this.cueData.assetId || this.cueData.assetid;
      console.log(`🔍 PlaceholderCueCard: type=${this.cueData.type}, assetId=${this.cueData.assetId}, assetid=${this.cueData.assetid}, actualAssetId=${actualAssetId}, showButton=${isSOT && hasAssetId}`);
      return isSOT && hasAssetId;
    },

    showJobStatus() {
      // Show status for SOT cues that have an AssetID
      return this.cueData.type === 'SOT' && !!(this.cueData.assetId || this.cueData.assetid);
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
        const episode = this.$route.params.episode;

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
}

.cue-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cue-card.selected {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
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

/* FSQ-specific Styling */
.fsq-container {
  padding: 16px;
  background-color: rgba(var(--v-theme-surface-variant), 0.05);
  border-radius: 0;
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