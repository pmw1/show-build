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
        <div class="cue-actions">
          <v-btn
            icon
            size="small"
            variant="text"
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
            @click.stop="$emit('delete')"
            class="action-btn delete-btn"
            tabindex="-1"
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
      <!-- FSQ-specific Display - Large Preview + Compact Controls Layout -->
      <div v-if="cueData.type === 'FSQ' && cueData.quote" class="fsq-preview-layout">
        <!-- Left Side: 65% - Large Preview with animated background -->
        <div class="fsq-preview-side">
          <div
            class="fsq-large-preview"
            :class="{ 'clickable': cueData.mediaUrl }"
            @click.stop="cueData.mediaUrl && openFsqPreviewModal()"
          >
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
            <!-- Quote text overlay (live preview) -->
            <div class="fsq-preview-quote-overlay" :style="fsqPreviewStyle">
              <div class="fsq-preview-quote-wrapper">
                <div class="fsq-preview-quote-text" :style="fsqPreviewTextStyle">{{ cueData.quote }}</div>
              </div>
              <div v-if="cueData.attribution" class="fsq-preview-attribution" :style="fsqPreviewAttributionStyle">— {{ cueData.attribution }}</div>
            </div>
            <!-- Click indicator if PNG exists -->
            <div v-if="cueData.mediaUrl" class="fsq-preview-click-hint">
              <v-icon size="20" color="white">mdi-magnify-plus</v-icon>
              <span>View Full</span>
            </div>
            <!-- PNG Generated indicator -->
            <div v-if="cueData.mediaUrl" class="fsq-png-indicator">
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
            :variant="cueData.mediaUrl ? 'outlined' : 'elevated'"
            :color="cueData.mediaUrl ? 'primary' : 'success'"
            @click.stop="handleGeneratePNG"
            :loading="generatingPNG"
            class="mb-2"
          >
            <v-icon size="small" start>{{ cueData.mediaUrl ? 'mdi-sync' : 'mdi-creation' }}</v-icon>
            {{ cueData.mediaUrl ? 'Regenerate' : 'Generate PNG' }}
          </v-btn>

          <!-- Edit FSQ Button -->
          <v-btn
            block
            size="small"
            variant="text"
            color="primary"
            class="mb-2"
            @click.stop="$emit('edit-fsq', cueData)"
          >
            <v-icon size="small" start>mdi-pencil</v-icon>
            Edit FSQ
          </v-btn>

          <!-- Status Indicator -->
          <div v-if="fsqGenerationStatus" class="fsq-status-chip mb-2">
            <v-chip size="x-small" :color="fsqStatusChipColor" variant="tonal">
              <v-icon size="x-small" start :class="{ 'mdi-spin': fsqGenerationStatus === 'generating' }">{{ fsqStatusChipIcon }}</v-icon>
              {{ fsqStatusText }}
            </v-chip>
          </div>

          <!-- Compact Style Controls -->
          <div class="fsq-compact-controls">
            <!-- Font Size -->
            <div class="fsq-control-row fsq-slider-row">
              <span class="fsq-control-label">Size</span>
              <v-slider
                v-model="localFontSize"
                :min="15"
                :max="50"
                :step="1"
                density="compact"
                hide-details
                thumb-label
                class="fsq-control-slider"
                @update:model-value="emitParamChange('fontSize', $event)"
              />
              <span class="fsq-slider-value">{{ localFontSize }}px</span>
            </div>

            <!-- Font Family -->
            <div class="fsq-control-row">
              <span class="fsq-control-label">Font</span>
              <v-select
                v-model="localFontFamily"
                :items="fontFamilyOptions"
                density="compact"
                hide-details
                variant="outlined"
                class="fsq-control-input"
                @update:model-value="emitParamChange('fontFamily', $event)"
              />
            </div>

            <!-- Box Height -->
            <div class="fsq-control-row">
              <span class="fsq-control-label">Height</span>
              <v-text-field
                v-model.number="localBoxHeight"
                type="number"
                density="compact"
                hide-details
                variant="outlined"
                suffix="%"
                :min="50"
                :max="100"
                class="fsq-control-input"
                @update:model-value="emitParamChange('boxHeight', $event)"
              />
            </div>

            <!-- Box Opacity -->
            <div class="fsq-control-row">
              <span class="fsq-control-label">Opacity</span>
              <v-text-field
                v-model.number="localBoxOpacity"
                type="number"
                density="compact"
                hide-details
                variant="outlined"
                suffix="%"
                :min="50"
                :max="100"
                class="fsq-control-input"
                @update:model-value="emitParamChange('boxOpacity', $event)"
              />
            </div>

            <!-- Line Spacing -->
            <div class="fsq-control-row">
              <span class="fsq-control-label">Spacing</span>
              <v-text-field
                v-model.number="localLineSpacing"
                type="number"
                density="compact"
                hide-details
                variant="outlined"
                suffix="%"
                :min="10"
                :max="60"
                class="fsq-control-input"
                @update:model-value="emitParamChange('lineSpacing', $event)"
              />
            </div>

            <!-- Alignment -->
            <div class="fsq-control-row">
              <span class="fsq-control-label">Align</span>
              <v-btn-toggle
                v-model="localAlignment"
                mandatory
                density="compact"
                color="primary"
                class="fsq-control-toggle"
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

            <!-- Revert Button -->
            <v-btn
              block
              size="x-small"
              variant="text"
              color="grey"
              class="mt-2"
              @click.stop="revertFsqChanges"
            >
              <v-icon size="small" start>mdi-undo</v-icon>
              Revert
            </v-btn>
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

        <!-- Thumbnail + Info Layout (when completed, has thumbnail, or has any display data) -->
        <div v-if="sotThumbnailUrl || isJobCompleted || displayDuration || displayVideoPath" class="sot-completed-layout">
          <!-- Left: Thumbnail with navigation -->
          <div class="sot-thumbnail-wrapper">
            <div class="sot-thumbnail-section">
              <img
                v-if="currentSotThumbnailUrl"
                :src="currentSotThumbnailUrl"
                class="sot-thumbnail-img sot-thumbnail-clickable"
                @click="openSotPreviewModal"
                @error="handleSotThumbnailError"
              />
              <div v-else class="sot-thumbnail-placeholder">
                <v-icon size="48" color="grey-darken-1">mdi-video-outline</v-icon>
                <span class="sot-placeholder-text">No Thumbnail</span>
              </div>
              <!-- Play overlay icon -->
              <div v-if="currentSotThumbnailUrl" class="sot-play-overlay" @click.stop="openSotPreviewModal">
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
            <!-- Duration (uses computed displayDuration to handle stale placeholders) -->
            <div v-if="displayDuration" class="sot-info-row">
              <v-icon size="small" color="primary">mdi-timer-outline</v-icon>
              <span class="sot-info-label">Duration:</span>
              <span class="sot-info-value">{{ displayDuration }}</span>
            </div>

            <!-- Media URL (uses computed displayVideoPath to handle stale placeholders) -->
            <div v-if="displayVideoPath" class="sot-info-row">
              <v-icon size="small" color="primary">mdi-video</v-icon>
              <span class="sot-info-label">Video:</span>
              <span class="sot-info-value sot-media-path">{{ formatMediaPath(displayVideoPath) }}</span>
            </div>

            <!-- Processing Status (uses computed displayProcessingStatus for live status) -->
            <div v-if="displayProcessingStatus" class="sot-info-row">
              <v-icon size="small" :color="isJobCompleted ? 'success' : 'info'">{{ isJobCompleted ? 'mdi-check-circle' : 'mdi-progress-clock' }}</v-icon>
              <span class="sot-info-label">Status:</span>
              <span class="sot-info-value">{{ displayProcessingStatus }}</span>
            </div>

            <!-- Transcription Preview -->
            <div v-if="sotTranscription" class="sot-transcription-preview">
              <v-icon size="small" color="primary">mdi-text</v-icon>
              <span class="sot-transcription-text">{{ truncateTranscription(sotTranscription) }}</span>
              <v-tooltip activator="parent" location="top" max-width="400">
                <span style="white-space: pre-wrap;">{{ sotTranscription }}</span>
              </v-tooltip>
            </div>

            <!-- Enhanced Video Specs (from job status) -->
            <div v-if="jobStatus?.video_specs" class="sot-info-row">
              <v-icon size="small" color="secondary">mdi-cog</v-icon>
              <span class="sot-info-label">Specs:</span>
              <span class="sot-info-value sot-tech-specs">
                {{ jobStatus.video_specs.resolution }}
                <span v-if="jobStatus.video_specs.codec !== 'unknown' && jobStatus.video_specs.codec !== 'processing'"> &bull; {{ jobStatus.video_specs.codec }}</span>
                <span v-if="jobStatus.video_specs.file_size_mb"> &bull; {{ jobStatus.video_specs.file_size_mb }}MB</span>
              </span>
            </div>

            <!-- Audio Info (from job status) -->
            <div v-if="jobStatus?.audio_analysis" class="sot-info-row">
              <v-icon size="small" color="secondary">mdi-volume-high</v-icon>
              <span class="sot-info-label">Audio:</span>
              <span class="sot-info-value">{{ jobStatus.audio_analysis.channels }}</span>
            </div>

            <!-- Warnings Badge (blur, audio issues) -->
            <div v-if="jobStatus?.warnings?.length" class="sot-warnings-row">
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

            <!-- Thumbnail Sharpness Indicator -->
            <div v-if="currentThumbnailSharpness" class="sot-info-row sot-sharpness-row">
              <v-icon size="small" :color="sharpnessColor">mdi-image-filter-hdr</v-icon>
              <span class="sot-info-label">Sharpness:</span>
              <span class="sot-info-value" :style="{ color: sharpnessColor }">{{ currentThumbnailSharpness.toFixed(0) }}</span>
              <v-tooltip activator="parent" location="top">
                Thumbnail sharpness score (higher = sharper). Below 100 may indicate blur.
              </v-tooltip>
            </div>
          </div>

          <!-- Outcue Display - Full Width at Bottom (MOVED INSIDE completed layout) -->
          <div v-if="sotOutcue" class="sot-outcue-banner">
            <span class="sot-outcue-label">OUTCUE:</span>
            <span class="sot-outcue-text">{{ sotOutcue }}</span>
          </div>
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

      <!-- VO (Voice Over) Display - Similar to SOT but without transcription/outcue -->
      <div v-else-if="cueData.type?.toUpperCase() === 'VO'" class="sot-container vo-container">
        <!-- Inline Video Player (discreet, toggleable) -->
        <div v-if="showInlinePlayer && sotVideoUrl" class="sot-inline-player-container">
          <div class="sot-inline-player-header">
            <span class="sot-inline-player-title">B-Roll Preview</span>
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

        <!-- Thumbnail + Info Layout (when completed, has thumbnail, or has any display data) -->
        <div v-if="sotThumbnailUrl || isJobCompleted || displayDuration || displayVideoPath" class="sot-completed-layout">
          <!-- Left: Thumbnail with navigation -->
          <div class="sot-thumbnail-wrapper">
            <div class="sot-thumbnail-section">
              <img
                v-if="currentSotThumbnailUrl"
                :src="currentSotThumbnailUrl"
                class="sot-thumbnail-img sot-thumbnail-clickable"
                @click="openSotPreviewModal"
                @error="handleSotThumbnailError"
              />
              <div v-else class="sot-thumbnail-placeholder">
                <v-icon size="48" color="grey-darken-1">mdi-video-outline</v-icon>
                <span class="sot-placeholder-text">No Thumbnail</span>
              </div>
              <!-- Play overlay icon -->
              <div v-if="currentSotThumbnailUrl" class="sot-play-overlay" @click.stop="openSotPreviewModal">
                <v-icon size="48" color="white">mdi-play-circle</v-icon>
              </div>
              <!-- VO Badge -->
              <div class="vo-badge">
                <v-icon size="14" color="white">mdi-microphone-off</v-icon>
                <span>B-ROLL</span>
              </div>
              <!-- Completion badge -->
              <div v-if="jobStatus && jobStatus.status === 'completed'" class="sot-complete-badge" style="bottom: 35px;">
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

          <!-- Right: Info (no transcription for VO) -->
          <div class="sot-info-section">
            <!-- Duration (uses computed displayDuration to handle stale placeholders) -->
            <div v-if="displayDuration" class="sot-info-row">
              <v-icon size="small" color="primary">mdi-timer-outline</v-icon>
              <span class="sot-info-label">Duration:</span>
              <span class="sot-info-value">{{ displayDuration }}</span>
            </div>

            <!-- Media URL (uses computed displayVideoPath to handle stale placeholders) -->
            <div v-if="displayVideoPath" class="sot-info-row">
              <v-icon size="small" color="primary">mdi-video</v-icon>
              <span class="sot-info-label">Video:</span>
              <span class="sot-info-value sot-media-path">{{ formatMediaPath(displayVideoPath) }}</span>
            </div>

            <!-- Processing Status (uses computed displayProcessingStatus for live status) -->
            <div v-if="displayProcessingStatus" class="sot-info-row">
              <v-icon size="small" :color="isJobCompleted ? 'success' : 'info'">{{ isJobCompleted ? 'mdi-check-circle' : 'mdi-progress-clock' }}</v-icon>
              <span class="sot-info-label">Status:</span>
              <span class="sot-info-value">{{ displayProcessingStatus }}</span>
            </div>

            <!-- VO indicator (no audio) -->
            <div class="sot-info-row vo-notice">
              <v-icon size="small" color="grey">mdi-microphone-off</v-icon>
              <span class="sot-info-label">Type:</span>
              <span class="sot-info-value">Voice Over (B-Roll)</span>
            </div>
          </div>
        </div>

        <!-- Processing In Progress (no thumbnail yet) -->
        <div v-else-if="jobStatus && jobStatus.status === 'processing'" class="sot-processing-layout">
          <v-progress-circular indeterminate size="40" width="3" color="primary"></v-progress-circular>
          <div class="sot-processing-info">
            <div class="sot-processing-phase">{{ jobStatus.current_phase || 'Processing...' }}</div>
            <div class="sot-processing-message">B-Roll video is being processed</div>
          </div>
        </div>

        <!-- No Job Status Yet -->
        <div v-else class="sot-pending-layout">
          <v-icon size="48" color="grey-lighten-1">mdi-video-off-outline</v-icon>
          <span class="sot-pending-text">Awaiting processing</span>
        </div>
      </div>

      <!-- GFX-specific Display -->
      <div v-else-if="cueData.type === 'GFX'" class="gfx-container">
        <div class="gfx-preview-section">
          <!-- Show generated image if available -->
          <div v-if="cueData.assetUrl || cueData.mediaUrl" class="gfx-image-preview">
            <img
              :src="gfxImageUrl"
              alt="GFX Preview"
              class="gfx-preview-img"
              @error="handleGfxImageError"
            />
            <div class="gfx-generated-badge">
              <v-icon size="12" color="success">mdi-check-circle</v-icon>
              <span>Generated</span>
            </div>
          </div>
          <!-- Show text preview if not generated -->
          <div v-else class="gfx-text-preview">
            <div v-if="cueData.title" class="gfx-title">{{ cueData.title }}</div>
            <div v-if="cueData.body" class="gfx-body">{{ formatGfxBody(cueData.body) }}</div>
            <div v-if="!cueData.body && !cueData.title" class="gfx-no-content">No content</div>
          </div>
        </div>

        <div class="gfx-controls">
          <!-- Generate/Regenerate Button -->
          <v-btn
            block
            size="small"
            :variant="(cueData.assetUrl || cueData.mediaUrl) ? 'outlined' : 'elevated'"
            :color="(cueData.assetUrl || cueData.mediaUrl) ? 'primary' : 'success'"
            @click.stop="handleGenerateGfx"
            :loading="generatingGfx"
            class="mb-2"
          >
            <v-icon size="small" start>{{ (cueData.assetUrl || cueData.mediaUrl) ? 'mdi-sync' : 'mdi-creation' }}</v-icon>
            {{ (cueData.assetUrl || cueData.mediaUrl) ? 'Regenerate' : 'Generate GFX' }}
          </v-btn>

          <!-- Style info -->
          <div v-if="cueData.fontSize || cueData.fontFamily" class="gfx-style-info">
            <span v-if="cueData.fontSize">{{ cueData.fontSize }}</span>
            <span v-if="cueData.fontFamily"> · {{ cueData.fontFamily }}</span>
          </div>
        </div>
      </div>

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

      <!-- Re-upload Button (SOT only) -->
      <v-btn
        v-if="showReprocessButton"
        size="x-small"
        variant="text"
        color="white"
        @click.stop="handleReupload"
        class="reupload-btn"
      >
        <v-icon size="small">mdi-upload</v-icon>
        <span style="margin-left: 4px;">Re-upload</span>
        <v-tooltip activator="parent" location="top">
          Upload new video while keeping metadata
        </v-tooltip>
      </v-btn>

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
          <span class="text-caption text-grey-lighten-1">Press ESC to close</span>
        </v-card-actions>
      </v-card>
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

<script>
import { getColorValue, resolveVuetifyColor } from '../../../utils/themeColorMap.js';
import { useSOTProcessing } from '../../../composables/useSOTProcessing.js';

export default {
  name: 'PlaceholderCueCard',
  emits: ['select', 'edit', 'delete', 'update-meta', 'reupload-sot-cue', 'edit-fsq'],
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
      generatingGfx: false,       // GFX generation in progress
      gfxImageError: false,       // GFX image failed to load
      fsqGenerationStatus: null, // FSQ generation status: null, 'queued', 'generating', 'completed', 'failed'
      fsqTaskId: null,        // Current FSQ Celery task ID
      fsqCacheBuster: null,   // Timestamp to bust browser cache after regeneration
      jobStatus: null,        // Current job status from API (SOT)
      statusPollInterval: null, // Interval ID for polling
      currentThumbnailIndex: 7, // Default to middle thumbnail (index 7 = thumb 8 of 15)
      pollingActive: false,    // Whether we're currently polling
      // Three-state cue status: null (unchecked), 'complete', 'needs_attention', 'urgent_attention'
      cueStatus: this.cueData?.cue_status || null,
      // FSQ editable parameters (local state)
      localFontFamily: this.cueData?.fontFamily || 'sans-serif',
      localFontSize: parseInt(this.cueData?.fontSize) || 25,  // Max font size in px for auto-fitting
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
      showInlinePlayer: false,
      // FSQ preview modal state
      showFsqPreviewModal: false,
      // SOT preview modal state
      showSotPreviewModal: false,
      // Preview countdown state
      previewCountdown: 0,
      countdownInterval: null
    };
  },
  computed: {
    /**
     * Badge label - shows "NOTE: DIRECTOR" for NOTE cues with noteFor, otherwise just the type
     */
    cueTypeBadgeLabel() {
      const t = this.cueData.type;
      if ((t === 'NOTE' || t === 'DIR') && this.cueData.noteFor) {
        return `${t}: ${this.cueData.noteFor.toUpperCase()}`;
      }
      return t;
    },
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
     * Uses relative URLs - Vue dev proxy forwards /episodes to backend
     */
    sotThumbnailOptions() {
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
      if (this.cueData?.thumbnailOptions && Array.isArray(this.cueData.thumbnailOptions)) {
        return this.cueData.thumbnailOptions.map(makeAbsoluteUrl);
      }

      // Check job status for thumbnail_candidates (from database)
      if (this.jobStatus?.thumbnail_candidates && Array.isArray(this.jobStatus.thumbnail_candidates)) {
        // Use final_thumbnail_path to get correct directory (thumbnails, not video)
        const thumbnailPath = this.jobStatus.final_thumbnail_path || '';
        if (thumbnailPath) {
          // Extract the base pattern from final_thumbnail_path (e.g., "0257/assets/thumbnails/airplane-girl-thumb-01.jpg")
          const match = thumbnailPath.match(/^(.+)-thumb-\d+\.(jpg|png)$/);
          if (match) {
            const basePath = match[1];  // "0257/assets/thumbnails/airplane-girl"
            const ext = match[2];  // preserve original extension
            return this.jobStatus.thumbnail_candidates.map((_, i) => {
              return `/episodes/${basePath}-thumb-${String(i + 1).padStart(2, '0')}.${ext}`;
            });
          }
        }
        // Fallback: try to build from video path but use thumbnails directory
        const videoPath = this.jobStatus.final_video_path?.replace(/\.mp4$/, '') || '';
        if (videoPath) {
          // Replace /video/ with /thumbnails/ in the path
          const thumbnailDir = videoPath.replace('/video/', '/thumbnails/');
          return this.jobStatus.thumbnail_candidates.map((_, i) => {
            return `/episodes/${thumbnailDir}-thumb-${String(i + 1).padStart(2, '0')}.jpg`;
          });
        }
      }

      // Generate options based on single thumbnail URL pattern
      if (this.sotThumbnailUrl) {
        const match = this.sotThumbnailUrl.match(/^(.+)-thumb-(\d+)\.(jpg|png)$/);
        if (match) {
          const base = match[1];
          const ext = match[3];  // preserve original extension
          return Array.from({ length: 15 }, (_, i) => `${base}-thumb-${String(i + 1).padStart(2, '0')}.${ext}`);
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
     * Get sharpness score for current thumbnail from thumbnail_data
     */
    currentThumbnailSharpness() {
      if (!this.jobStatus?.thumbnail_data || !Array.isArray(this.jobStatus.thumbnail_data)) {
        return null;
      }

      // Find thumbnail data for current index (1-based in data)
      const thumbData = this.jobStatus.thumbnail_data.find(
        t => t.index === this.currentThumbnailIndex + 1
      );

      return thumbData?.sharpness || null;
    },

    /**
     * Check if job is completed (status from API)
     */
    isJobCompleted() {
      return this.jobStatus?.status === 'completed';
    },

    /**
     * Display duration - prioritizes jobStatus data over stale cueData placeholders
     * Treats "calculating", "processing", "queued", "pending" as null values
     */
    displayDuration() {
      const stalePlaceholders = ['calculating', 'processing', 'queued', 'pending', ''];

      // If job is completed, prefer jobStatus data
      if (this.isJobCompleted) {
        // Try post_analysis duration first
        if (this.jobStatus?.post_analysis?.duration) {
          return this.jobStatus.post_analysis.duration;
        }
        // Try video_specs duration
        if (this.jobStatus?.video_specs?.duration) {
          return this.jobStatus.video_specs.duration;
        }
      }

      // Check cueData, but filter out placeholder values
      const cueDuration = this.cueData?.duration?.toLowerCase?.() || this.cueData?.duration;
      if (cueDuration && !stalePlaceholders.includes(cueDuration?.toLowerCase?.())) {
        return this.cueData.duration;
      }

      // Fallback to jobStatus even if not completed
      if (this.jobStatus?.post_analysis?.duration) {
        return this.jobStatus.post_analysis.duration;
      }
      if (this.jobStatus?.video_specs?.duration) {
        return this.jobStatus.video_specs.duration;
      }

      return null;
    },

    /**
     * Display video path - prioritizes jobStatus data over stale cueData placeholders
     */
    displayVideoPath() {
      const stalePlaceholders = ['processing', 'queued', 'pending', ''];

      // If job is completed, prefer jobStatus data
      if (this.isJobCompleted && this.jobStatus?.final_video_path) {
        return this.jobStatus.final_video_path;
      }

      // Check cueData, but filter out placeholder values
      const cueMediaUrl = this.cueData?.mediaUrl?.toLowerCase?.() || this.cueData?.mediaUrl;
      if (cueMediaUrl && !stalePlaceholders.includes(cueMediaUrl?.toLowerCase?.())) {
        return this.cueData.mediaUrl;
      }

      // Fallback to jobStatus
      if (this.jobStatus?.final_video_path) {
        return this.jobStatus.final_video_path;
      }

      return null;
    },

    /**
     * Display processing status - prioritizes actual job status over stale cueData
     */
    displayProcessingStatus() {
      // If we have live job status, use that
      if (this.jobStatus?.status) {
        const status = this.jobStatus.status;
        if (status === 'completed') return 'Completed';
        if (status === 'failed') return 'Failed';
        if (status === 'processing') return this.jobStatus.current_phase || 'Processing...';
        if (status === 'queued') return 'Queued';
        return status;
      }

      // Fallback to cueData
      if (this.cueData?.processingStatus) {
        return this.cueData.processingStatus;
      }

      return null;
    },

    /**
     * Get color for sharpness indicator based on value
     */
    sharpnessColor() {
      const sharpness = this.currentThumbnailSharpness;
      if (!sharpness) return 'grey';

      if (sharpness < 100) return '#D32F2F';  // Red - blurry
      if (sharpness < 150) return '#FF9800';  // Orange - below average
      if (sharpness < 200) return '#FFC107';  // Yellow - average
      return '#4CAF50';  // Green - sharp
    },

    /**
     * Get SOT thumbnail URL from cue data or job status (base/primary thumbnail)
     * Uses relative URLs - Vue dev proxy forwards /episodes to backend
     */
    sotThumbnailUrl() {
      const backendUrl = '';

      // First check cue data for ThumbnailURL (skip stale blob: URLs)
      if (this.cueData?.thumbnailUrl && !this.cueData.thumbnailUrl.startsWith('blob:')) {
        // If already an absolute URL, return as-is
        if (this.cueData.thumbnailUrl.startsWith('http')) {
          return this.cueData.thumbnailUrl;
        }
        // If starts with /episodes, use as relative URL
        if (this.cueData.thumbnailUrl.startsWith('/episodes')) {
          return this.cueData.thumbnailUrl;
        }
        // Otherwise, construct full path
        return `/episodes/${this.cueData.thumbnailUrl}`;
      }

      // Fall back to job status thumbnail path
      if (this.jobStatus?.final_thumbnail_path) {
        const path = this.jobStatus.final_thumbnail_path;
        if (path.startsWith('http')) {
          return path;
        }
        if (path.startsWith('/episodes')) {
          return `${backendUrl}${path}`;
        }
        return `${backendUrl}/episodes/${path}`;
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
     * Uses relative URLs - Vue dev proxy forwards /episodes to backend
     */
    sotVideoUrl() {
      const backendUrl = '';

      // First check cue data for MediaURL (skip stale blob: URLs)
      if (this.cueData?.mediaUrl && !this.cueData.mediaUrl.startsWith('blob:')) {
        // If already an absolute URL, return as-is
        if (this.cueData.mediaUrl.startsWith('http')) {
          return this.cueData.mediaUrl;
        }
        // If starts with /episodes, use as relative URL
        if (this.cueData.mediaUrl.startsWith('/episodes')) {
          return this.cueData.mediaUrl;
        }
        // Otherwise, construct full path
        return `/episodes/${this.cueData.mediaUrl}`;
      }

      // Fall back to job status final video path
      if (this.jobStatus?.final_video_path) {
        const path = this.jobStatus.final_video_path;
        if (path.startsWith('http')) {
          return path;
        }
        if (path.startsWith('/episodes')) {
          return `${backendUrl}${path}`;
        }
        return `${backendUrl}/episodes/${path}`;
      }

      return '';
    },

    /**
     * Get FSQ thumbnail URL - use mediaUrl from cue data
     */
    fsqThumbnailUrl() {
      if (!this.cueData?.mediaUrl) return '';
      let url;
      // If it's already a full URL, use it; otherwise prepend /episodes
      if (this.cueData.mediaUrl.startsWith('http') || this.cueData.mediaUrl.startsWith('/')) {
        url = this.cueData.mediaUrl;
      } else {
        // Build episode-relative URL
        const episode = this.$route?.params?.episode || '';
        url = `/episodes/${episode}/assets/quotes/${this.cueData.mediaUrl}`;
      }
      // Add cache buster to force reload after regeneration
      if (this.fsqCacheBuster) {
        url += `?t=${this.fsqCacheBuster}`;
      }
      return url;
    },

    /**
     * Get GFX image URL from cue data
     */
    gfxImageUrl() {
      const url = this.cueData?.assetUrl || this.cueData?.mediaUrl;
      if (!url) return '';
      // If it's already a full URL, use it
      if (url.startsWith('http') || url.startsWith('/')) {
        return url;
      }
      // Build episode-relative URL
      const episode = this.currentEpisode || this.$route?.params?.episode || '';
      return `/episodes/${episode}/assets/graphics/${url}`;
    },

    /**
     * Get FSQ generation status text for display
     */
    fsqStatusText() {
      switch (this.fsqGenerationStatus) {
        case 'queued': return 'Queued';
        case 'generating': return 'Generating...';
        case 'completed': return 'Complete';
        case 'failed': return 'Failed';
        default: return '';
      }
    },

    /**
     * Get FSQ status chip color
     */
    fsqStatusChipColor() {
      switch (this.fsqGenerationStatus) {
        case 'queued': return 'info';
        case 'generating': return 'warning';
        case 'completed': return 'success';
        case 'failed': return 'error';
        default: return 'grey';
      }
    },

    /**
     * Get FSQ status chip icon
     */
    fsqStatusChipIcon() {
      switch (this.fsqGenerationStatus) {
        case 'queued': return 'mdi-clock-outline';
        case 'generating': return 'mdi-loading';
        case 'completed': return 'mdi-check-circle';
        case 'failed': return 'mdi-alert-circle';
        default: return 'mdi-help-circle';
      }
    },

    /**
     * Get FSQ preview container style (alignment)
     */
    fsqPreviewStyle() {
      const alignment = this.localAlignment || 'left';
      return {
        textAlign: alignment,
        justifyContent: alignment === 'center' ? 'center' : alignment === 'right' ? 'flex-end' : 'flex-start'
      };
    },

    /**
     * Get FSQ preview text style
     */
    fsqPreviewTextStyle() {
      const fontFamily = this.localFontFamily || 'serif';
      const fontSize = this.localFontSize || 25;
      const lineSpacing = this.localLineSpacing || 30;
      const alignment = this.localAlignment || 'center';

      // Map font family names to CSS
      const fontMap = {
        'serif': 'Georgia, "Times New Roman", serif',
        'sans-serif': 'Arial, Helvetica, sans-serif',
        'monospace': '"Courier New", Courier, monospace',
        'cursive': 'cursive'
      };

      // Scale font size for preview (smaller container)
      const scaledFontSize = Math.max(10, fontSize * 0.5);

      return {
        fontFamily: fontMap[fontFamily] || fontFamily,
        fontSize: `${scaledFontSize}px`,
        lineHeight: `${100 + lineSpacing}%`,
        color: 'white',
        textAlign: alignment,
        width: '100%'
      };
    },

    /**
     * Get FSQ preview attribution style
     */
    fsqPreviewAttributionStyle() {
      const fontFamily = this.localFontFamily || 'serif';
      const fontSize = this.localFontSize || 25;
      const alignment = this.localAlignment || 'center';

      const fontMap = {
        'serif': 'Georgia, "Times New Roman", serif',
        'sans-serif': 'Arial, Helvetica, sans-serif',
        'monospace': '"Courier New", Courier, monospace',
        'cursive': 'cursive'
      };

      // Attribution is smaller than main text
      const scaledFontSize = Math.max(8, fontSize * 0.35);

      return {
        fontFamily: fontMap[fontFamily] || fontFamily,
        fontSize: `${scaledFontSize}px`,
        color: 'rgba(255, 255, 255, 0.8)',
        marginTop: '8px',
        fontStyle: 'italic',
        textAlign: alignment,
        width: '100%'
      };
    },

    /**
     * Get motion background style for FSQ thumbnail container
     * Uses fsqBackgroundVideo from settings
     */
    thumbnailBackgroundStyle() {
      // Fallback gradient for when video isn't loaded
      return {
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        backgroundSize: 'cover'
      };
    },

    /**
     * Get FSQ background video URL from settings or use default
     */
    fsqBackgroundVideoUrl() {
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
    },

    showReprocessButton() {
      const cueType = this.cueData.type?.toUpperCase();
      const isSOTorVO = cueType === 'SOT' || cueType === 'VO';
      // Check both assetId (camelCase) and assetid (lowercase from parser)
      const hasAssetId = !!(this.cueData.assetId || this.cueData.assetid);
      const actualAssetId = this.cueData.assetId || this.cueData.assetid;
      console.log(`🔍 PlaceholderCueCard: type=${this.cueData.type}, assetId=${this.cueData.assetId}, assetid=${this.cueData.assetid}, actualAssetId=${actualAssetId}, showButton=${isSOTorVO && hasAssetId}`);
      return isSOTorVO && hasAssetId;
    },

    showJobStatus() {
      // Show status for SOT/VO cues that have an AssetID (case-insensitive check)
      const cueType = this.cueData.type?.toUpperCase();
      const isSOTorVO = cueType === 'SOT' || cueType === 'VO';
      return isSOTorVO && !!(this.cueData.assetId || this.cueData.assetid);
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
        // If closing, pause video first to prevent race condition
        if (this.showInlinePlayer) {
          const video = this.$refs.inlineVideoPlayer;
          if (video) {
            video.pause();
            video.currentTime = 0;
          }
        }
        this.showInlinePlayer = !this.showInlinePlayer;
        // Auto-play when opening with proper promise handling
        if (this.showInlinePlayer) {
          this.$nextTick(() => {
            const video = this.$refs.inlineVideoPlayer;
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
     * Uses relative URLs - Vue dev proxy forwards /episodes to backend
     */
    openVideoPlayer() {
      const backendUrl = '';
      const videoPath = this.cueData.mediaUrl || this.jobStatus?.final_video_path;
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
     * Format warning label for display (extract short description)
     */
    formatWarningLabel(warning) {
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
     * Preload all thumbnail images for faster navigation
     * Creates Image objects in memory to cache them in the browser
     */
    preloadThumbnails() {
      const options = this.sotThumbnailOptions;
      if (!options || options.length <= 1) return;

      console.log(`🖼️ Preloading ${options.length} thumbnails for ${this.cueData.slug || 'cue'}`);

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
     * Revert FSQ style changes back to saved values
     */
    revertFsqChanges() {
      console.log('↩️ Reverting FSQ changes to saved values');
      this.localFontFamily = this.cueData?.fontFamily || 'sans-serif';
      this.localFontSize = parseInt(this.cueData?.fontSize) || 25;
      this.localBoxHeight = parseInt(this.cueData?.boxHeight) || 80;
      this.localBoxOpacity = parseInt(this.cueData?.boxOpacity) || 75;
      this.localLineSpacing = parseInt(this.cueData?.lineSpacing) || 30;
      this.localAlignment = this.cueData?.alignment || this.cueData?.style || 'center';
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

    /**
     * Open FSQ preview modal with video background
     */
    openFsqPreviewModal() {
      console.log('🖼️ Opening FSQ preview modal');
      this.showFsqPreviewModal = true;
      // Add ESC key listener
      this.$nextTick(() => {
        document.addEventListener('keydown', this.handlePreviewModalEsc);
      });
    },

    /**
     * Close FSQ preview modal
     */
    closeFsqPreviewModal() {
      console.log('🖼️ Closing FSQ preview modal');
      this.showFsqPreviewModal = false;
      document.removeEventListener('keydown', this.handlePreviewModalEsc);
    },

    /**
     * Open SOT preview modal with video player
     */
    openSotPreviewModal() {
      console.log('🎬 Opening SOT preview modal');
      this.showSotPreviewModal = true;
      // Add ESC key listener
      this.$nextTick(() => {
        document.addEventListener('keydown', this.handlePreviewModalEsc);
      });
    },

    /**
     * Close SOT preview modal
     */
    closeSotPreviewModal() {
      console.log('🎬 Closing SOT preview modal');
      // Clear countdown interval if running
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
        this.countdownInterval = null;
      }
      this.previewCountdown = 0;
      // Pause video before closing to prevent play/pause race condition
      const video = this.$refs.sotPreviewVideoRef;
      if (video) {
        video.pause();
        video.currentTime = 0;
      }
      this.showSotPreviewModal = false;
      document.removeEventListener('keydown', this.handlePreviewModalEsc);
    },

    /**
     * Handle preview video ready - start countdown then auto-play
     */
    onPreviewVideoReady() {
      const video = this.$refs.sotPreviewVideoRef;
      if (video && this.showSotPreviewModal) {
        // Start 1.5 second countdown before playing
        this.previewCountdown = 1.5;

        // Clear any existing interval
        if (this.countdownInterval) {
          clearInterval(this.countdownInterval);
        }

        // Update countdown every 100ms for smooth animation
        this.countdownInterval = setInterval(() => {
          this.previewCountdown -= 0.1;

          if (this.previewCountdown <= 0) {
            this.previewCountdown = 0;
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;

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
    },

    /**
     * Handle ESC key to close preview modals
     */
    handlePreviewModalEsc(event) {
      if (event.key === 'Escape') {
        if (this.showFsqPreviewModal) {
          this.closeFsqPreviewModal();
        }
        if (this.showSotPreviewModal) {
          this.closeSotPreviewModal();
        }
      }
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
     * Handle re-upload button click - Open SotModal with existing metadata but no mediaUrl
     * This allows uploading a new video while keeping the slug, description, credits, etc.
     */
    handleReupload() {
      console.log('📤 Re-upload requested for SOT cue:', this.cueData.slug);

      // Clear failed status immediately - we're starting fresh with a new video
      this.jobStatus = null;

      // Stop polling for old job status
      if (this.statusPollInterval) {
        clearInterval(this.statusPollInterval);
        this.statusPollInterval = null;
        this.pollingActive = false;
        console.log('🛑 Stopped polling old job status for re-upload');
      }

      // Build re-upload data: preserve metadata but clear mediaUrl so user must upload new file
      const reuploadData = {
        assetId: this.cueData.assetId || this.cueData.assetid,
        slug: this.cueData.slug,
        description: this.cueData.description || this.cueData.text || '',
        duration: this.cueData.duration,
        transcription: this.cueData.transcription,
        credits: this.cueData.credits,
        // Explicitly do NOT include mediaUrl - user will upload a new video
        // mediaUrl: null,
        // thumbnailUrl: null,
        // trimStart/trimEnd will be set when the new video is loaded
      };

      console.log('📤 Re-upload data:', reuploadData);
      this.$emit('reupload-sot-cue', reuploadData);
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
        return;
      }

      if (!this.cueData.quote) {
        console.error('Cannot generate PNG: no quote text found');
        return;
      }

      try {
        this.generatingPNG = true;
        this.fsqGenerationStatus = 'queued';
        console.log(`🎨 Generating FSQ PNG for: ${this.cueData.assetId}`);

        const token = localStorage.getItem('auth-token');
        // Use prop first, then fallback to route params
        const episode = this.currentEpisode || this.$route?.params?.episode || '';

        // Use LOCAL state values (from editable controls) not cueData values
        // Scale up font size: slider shows 15-50, but renderer needs 60-200px for 1920x1080 canvas
        const scaledMaxFontSize = this.localFontSize * 4;
        const requestData = {
          episode_id: episode,
          quote: this.cueData.quote,
          attribution: this.cueData.attribution || this.cueData.source || '',
          slug: this.cueData.slug || 'quote',
          asset_id: this.cueData.assetId,
          alignment: this.localAlignment,
          font_family: this.localFontFamily,
          max_font_size: scaledMaxFontSize,
          box_height: this.localBoxHeight,
          box_opacity: this.localBoxOpacity,
          line_spacing: this.localLineSpacing,
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

        // Update status to generating and store task ID
        this.fsqGenerationStatus = 'generating';
        this.fsqTaskId = result.task_id;

        // Poll for completion (silent - no alerts)
        this.pollTaskStatus(result.task_id);

      } catch (error) {
        console.error('❌ Error generating FSQ PNG:', error);
        this.fsqGenerationStatus = 'failed';
      } finally {
        this.generatingPNG = false;
      }
    },

    /**
     * Generate GFX image from cue data
     */
    async handleGenerateGfx() {
      if (!this.cueData.assetId) {
        console.error('Cannot generate GFX: no assetId found');
        return;
      }

      if (!this.cueData.body) {
        console.error('Cannot generate GFX: no body text found');
        return;
      }

      try {
        this.generatingGfx = true;
        console.log(`🎨 Generating GFX for: ${this.cueData.assetId}`);

        const token = localStorage.getItem('auth-token');
        const episode = this.currentEpisode || this.$route?.params?.episode || '';

        const requestData = {
          episode_id: episode,
          gfx_type: this.cueData.gfxType || 'fullscreen-text',
          body: this.cueData.body?.replace(/\\n/g, '\n') || '',
          slug: this.cueData.slug || 'gfx',
          asset_id: this.cueData.assetId,
          title: this.cueData.title || null,
          alignment: this.cueData.textAlign || 'center',
          font_family: this.cueData.fontFamily || 'sans-serif',
          font_size: parseInt(this.cueData.fontSize) || 25,
          render_mode: this.cueData.renderMode || 'png',
          priority: 'high'
        };

        console.log('📤 Sending GFX generation request:', requestData);

        const response = await fetch('/api/gfx/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          },
          body: JSON.stringify(requestData)
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to generate GFX');
        }

        const result = await response.json();
        console.log('✅ GFX generated:', result);

        // Update cue with generated asset URL
        if (result.asset_url) {
          this.$emit('update-cue-field', {
            assetId: this.cueData.assetId,
            field: 'assetUrl',
            value: result.asset_url
          });
          // Force image reload
          this.gfxImageError = false;
        }

      } catch (error) {
        console.error('❌ Error generating GFX:', error);
        alert('Failed to generate GFX: ' + error.message);
      } finally {
        this.generatingGfx = false;
      }
    },

    /**
     * Format GFX body text for display (unescape newlines)
     */
    formatGfxBody(body) {
      if (!body) return '';
      // Unescape \n to actual newlines, then truncate for preview
      const unescaped = body.replace(/\\n/g, '\n');
      // Truncate to 200 chars for preview
      return unescaped.length > 200 ? unescaped.substring(0, 200) + '...' : unescaped;
    },

    /**
     * Handle GFX image load error
     */
    handleGfxImageError() {
      console.warn('GFX image failed to load:', this.gfxImageUrl);
      this.gfxImageError = true;
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
              this.fsqGenerationStatus = 'completed';

              // Update the cue block with the generated mediaUrl
              if (status.result.asset_url) {
                console.log('📝 Updating cue mediaUrl to:', status.result.asset_url);
                this.$emit('update-meta', {
                  assetId: this.cueData.assetId,
                  field: 'mediaUrl',
                  value: status.result.asset_url
                });
              }

              // Wait 1 second for file to be fully written, then force thumbnail reload
              setTimeout(() => {
                console.log('🔄 Forcing thumbnail reload after 1s delay');
                this.fsqCacheBuster = Date.now();
              }, 1000);

              // Clear status after 3 seconds
              setTimeout(() => {
                if (this.fsqGenerationStatus === 'completed') {
                  this.fsqGenerationStatus = null;
                }
              }, 3000);

            } else {
              console.error('❌ PNG generation failed:', status.error);
              this.fsqGenerationStatus = 'failed';
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
        // Use appropriate endpoint based on cue type (SOT or VO)
        const cueType = this.cueData.type?.toUpperCase();
        const endpoint = cueType === 'VO' ? `/api/vo/job-status/${assetId}` : `/api/sot/job-status/${assetId}`;
        const response = await fetch(endpoint, {
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

  watch: {
    // Watch for assetId changes to start/stop polling dynamically
    showJobStatus: {
      handler(newVal, oldVal) {
        console.log('👁️ showJobStatus changed:', oldVal, '->', newVal);
        if (newVal && !oldVal) {
          // assetId was added - start polling
          console.log('🚀 AssetID appeared - starting status polling');
          this.startPolling();
        } else if (!newVal && oldVal) {
          // assetId was removed - stop polling
          this.stopPolling();
        }
      },
      immediate: false
    },
    // Watch jobStatus object for changes (nested path doesn't work when parent is null)
    jobStatus: {
      handler(newJobStatus, oldJobStatus) {
        const newStatus = newJobStatus?.status;
        const oldStatus = oldJobStatus?.status;
        console.log('📊 jobStatus watcher fired:', oldStatus, '->', newStatus);

        if (newStatus === 'completed' && oldStatus !== 'completed') {
          console.log('✅ Job completed - emitting refresh request');
          this.$emit('status-changed', {
            status: newStatus,
            assetId: this.cueData.assetId || this.cueData.assetid
          });
        }
      },
      deep: true
    },
    // Watch sotThumbnailOptions to preload thumbnails when they become available
    sotThumbnailOptions: {
      handler(newOptions, oldOptions) {
        // Preload when we get new options (e.g., after job status updates)
        if (newOptions && newOptions.length > 1 && (!oldOptions || oldOptions.length <= 1)) {
          console.log('📷 Thumbnail options now available, preloading...');
          this.preloadThumbnails();
        }
      },
      immediate: false
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

    // Preload thumbnails if already available on mount
    if (this.sotThumbnailOptions && this.sotThumbnailOptions.length > 1) {
      this.preloadThumbnails();
    }
  },

  beforeUnmount() {
    // Clean up polling interval
    this.stopPolling();
    // Clean up countdown interval
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }
    // Clean up ESC key listener for preview modals
    document.removeEventListener('keydown', this.handlePreviewModalEsc);
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

/* GFX Container Styles */
.gfx-container {
  display: flex;
  gap: 16px;
  padding: 12px;
}

.gfx-preview-section {
  flex: 1;
  min-width: 0;
}

.gfx-image-preview {
  position: relative;
  border-radius: 4px;
  overflow: hidden;
}

.gfx-preview-img {
  width: 100%;
  max-height: 200px;
  object-fit: contain;
  background: #1a1a1a;
  border-radius: 4px;
}

.gfx-generated-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  padding: 2px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #4CAF50;
}

.gfx-text-preview {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 16px;
  border-radius: 4px;
  color: white;
  min-height: 80px;
}

.gfx-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #fff;
}

.gfx-body {
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  color: rgba(255, 255, 255, 0.9);
}

.gfx-no-content {
  font-style: italic;
  color: rgba(255, 255, 255, 0.5);
}

.gfx-controls {
  width: 140px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.gfx-style-info {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-align: center;
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

/* FSQ Preview Layout - Large preview on left, controls on right */
.fsq-preview-layout {
  display: flex;
  gap: 12px;
  width: 100%;
  padding: 8px;
}

/* Left side: 65% - Large preview */
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
  justify-content: flex-start;
  padding: 5% 10% 8% 10%;
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
  font-style: italic;
  word-wrap: break-word;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
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