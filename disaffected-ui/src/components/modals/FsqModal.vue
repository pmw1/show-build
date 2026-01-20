<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="1100" persistent>
    <v-card class="fsq-modal-card">
      <v-card-title class="d-flex align-center text-black py-2" :class="`bg-${cueTypeColor}`">
        <v-icon class="mr-2" size="small">mdi-format-quote-close</v-icon>
        <span class="text-body-1">Full-Screen Quote (FSQ)</span>
        <v-spacer></v-spacer>
        <v-btn icon size="x-small" variant="text" @click="cancel" color="black">
          <v-icon size="small">mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="pb-2 compact-fsq-modal pa-3">
        <v-form ref="fsqFormRef" v-model="formValid">
          <!-- TWO-COLUMN LAYOUT -->
          <v-row dense>
            <!-- LEFT COLUMN: Large Preview -->
            <v-col cols="7">
              <!-- Large Preview Container -->
              <div class="large-preview-container mb-2">
                <video
                  ref="previewVideoRef"
                  class="preview-video-background"
                  autoplay
                  loop
                  muted
                  playsinline
                  @loadeddata="handleVideoLoaded"
                  @error="handleVideoError"
                >
                  <source :src="previewBackgroundVideo" type="video/mp4">
                </video>
                <div class="black-bar-overlay"></div>
                <div class="quote-preview" :style="previewStyle">
                  <div class="quote-text" :style="quoteTextStyle" v-html="formattedQuotePreview"></div>
                  <div v-if="includeAttribution && source" class="quote-source" :style="quoteSourceStyle">{{ attributionPrefix }}{{ source }}</div>
                </div>
              </div>

              <!-- Word count and AI status below preview -->
              <div class="d-flex align-center justify-space-between mb-2">
                <div v-if="quote && quote.length > 0" class="word-count-badge">
                  <v-chip size="x-small" color="grey-darken-2">{{ quote.trim().split(/\s+/).filter(w => w.length > 0).length }} words</v-chip>
                </div>
                <div v-if="aiState" class="ai-status-badge">
                  <v-chip size="x-small" :color="aiStatusColor">
                    <v-icon size="x-small" class="mr-1" :class="{ 'rotating': aiState === 'analyzing' }">{{ aiStatusIcon }}</v-icon>
                    {{ aiStatusText }}
                  </v-chip>
                </div>
              </div>

              <!-- AI Recommendation Panel (if splits detected) -->
              <v-alert
                v-if="splitRecommendations && splitRecommendations.length > 1"
                type="warning"
                variant="tonal"
                density="compact"
                class="mb-2"
              >
                <div class="d-flex align-center">
                  <v-icon size="small" class="mr-2">mdi-robot</v-icon>
                  <span class="text-caption">AI suggests {{ splitRecommendations.length }} splits</span>
                  <v-spacer></v-spacer>
                  <v-btn size="x-small" variant="text" color="warning" @click="showSplitPanel = !showSplitPanel">
                    {{ showSplitPanel ? 'Hide' : 'Show' }}
                  </v-btn>
                </div>
              </v-alert>
            </v-col>

            <!-- RIGHT COLUMN: Compact Controls -->
            <v-col cols="5">
              <!-- Quote Text Input -->
              <div class="quote-input-wrapper mb-2">
                <v-textarea
                  ref="quoteFieldRef"
                  v-model="quote"
                  label="Quote"
                  placeholder="Enter quote text..."
                  variant="outlined"
                  rows="5"
                  auto-grow
                  :rules="quoteRules"
                  required
                  density="compact"
                  hide-details="auto"
                  @paste="handleQuotePaste"
                  @input="handleQuoteInput"
                />
              </div>

              <!-- Slug -->
              <v-text-field
                ref="slugFieldRef"
                v-model="slug"
                label="Slug"
                placeholder="short-slug"
                variant="outlined"
                :rules="slugRules"
                required
                density="compact"
                hide-details="auto"
                class="mb-2"
                @input="handleSlugInput"
                @blur="normalizeSlug"
              />

              <!-- Attribution Row -->
              <v-row dense class="mb-2">
                <v-col cols="8">
                  <v-combobox
                    v-model="source"
                    :items="sourceOptions"
                    label="Attribution"
                    placeholder="Source name"
                    variant="outlined"
                    density="compact"
                    :disabled="!includeAttribution"
                    hide-details
                    clearable
                  />
                </v-col>
                <v-col cols="4" class="d-flex align-center justify-center">
                  <v-switch
                    v-model="includeAttribution"
                    density="compact"
                    hide-details
                    color="success"
                  >
                    <template #label>
                      <span class="text-caption">{{ includeAttribution ? 'On' : 'Off' }}</span>
                    </template>
                  </v-switch>
                </v-col>
              </v-row>

              <v-divider class="mb-2"></v-divider>

              <!-- Style Settings - Compact Text Fields -->
              <div class="style-settings">
                <div class="text-caption text-grey mb-1">STYLE SETTINGS</div>
                <v-row dense class="mb-1">
                  <v-col cols="4">
                    <v-text-field
                      v-model.number="fontSize"
                      label="Size"
                      type="number"
                      variant="outlined"
                      density="compact"
                      hide-details
                      suffix="px"
                      min="10"
                      max="50"
                    />
                  </v-col>
                  <v-col cols="8">
                    <v-select
                      v-model="fontFamily"
                      :items="fontOptions"
                      label="Font"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </v-col>
                </v-row>
                <v-row dense class="mb-2">
                  <v-col cols="12">
                    <v-btn-toggle
                      v-model="quoteStyle"
                      mandatory
                      density="compact"
                      color="primary"
                      class="w-100"
                    >
                      <v-btn value="left" size="small" class="flex-grow-1">
                        <v-icon size="small">mdi-format-align-left</v-icon>
                      </v-btn>
                      <v-btn value="center" size="small" class="flex-grow-1">
                        <v-icon size="small">mdi-format-align-center</v-icon>
                      </v-btn>
                      <v-btn value="right" size="small" class="flex-grow-1">
                        <v-icon size="small">mdi-format-align-right</v-icon>
                      </v-btn>
                    </v-btn-toggle>
                  </v-col>
                </v-row>
              </div>

              <!-- Render Mode -->
              <div class="render-mode-section">
                <div class="text-caption text-grey mb-1">OUTPUT</div>
                <v-btn-toggle
                  v-model="renderMode"
                  mandatory
                  density="compact"
                  color="lime"
                  class="w-100 mb-2"
                >
                  <v-btn value="png" size="small" class="flex-grow-1">
                    <v-icon size="small" class="mr-1">mdi-file-image</v-icon>
                    PNG
                  </v-btn>
                  <v-btn value="video" size="small" class="flex-grow-1">
                    <v-icon size="small" class="mr-1">mdi-video</v-icon>
                    Video
                  </v-btn>
                </v-btn-toggle>
              </div>

              <!-- Action Buttons -->
              <div class="action-buttons mt-2">
                <v-btn
                  block
                  color="warning"
                  @click="rejectAIRecommendation"
                  :disabled="!formValid || !quote"
                  :loading="loading"
                  variant="elevated"
                  size="default"
                >
                  <v-icon size="small" class="mr-1">mdi-plus</v-icon>
                  {{ splitRecommendations && splitRecommendations.length > 1 ? 'Insert Full Quote' : 'Insert Quote' }}
                </v-btn>
                <v-btn
                  v-if="splitRecommendations && splitRecommendations.length > 1"
                  block
                  color="deep-purple"
                  @click="acceptAIRecommendation"
                  :disabled="!formValid"
                  :loading="loading"
                  variant="elevated"
                  size="small"
                  class="mt-1"
                >
                  <v-icon size="small" class="mr-1">mdi-robot</v-icon>
                  Insert {{ splitRecommendations.length }} Splits
                </v-btn>
              </div>
            </v-col>
          </v-row>

          <!-- SPLIT PREVIEW PANEL (collapsible, shown when AI recommends splits) -->
          <v-expand-transition>
            <div v-if="showSplitPanel && splitRecommendations && splitRecommendations.length > 1" class="split-preview-panel mt-3">
              <v-divider class="mb-2"></v-divider>
              <div class="text-caption text-grey mb-2">AI RECOMMENDED SPLITS</div>
              <div class="split-parts-grid">
                <div
                  v-for="(segment, index) in splitRecommendations"
                  :key="`split-${index}`"
                  class="split-part-preview"
                >
                  <div class="part-label">{{ index + 1 }}/{{ splitRecommendations.length }}</div>
                  <div class="quote-preview-container split-container">
                    <video class="preview-video-background" autoplay loop muted playsinline>
                      <source :src="previewBackgroundVideo" type="video/mp4">
                    </video>
                    <div class="black-bar-overlay"></div>
                    <div class="quote-preview" :style="getSplitPreviewStyle">
                      <div class="quote-text" :style="getSplitTextStyle" v-html="formatSplitSegment(segment)"></div>
                      <div v-if="includeAttribution" class="quote-source" :style="getSplitSourceStyle">{{ attributionPrefix }}{{ source || 'Source' }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </v-expand-transition>

          <!-- Error Display -->
          <v-alert
            v-if="error"
            type="error"
            variant="tonal"
            class="mt-2"
            density="compact"
          >
            {{ error }}
          </v-alert>
        </v-form>
      </v-card-text>

      <!-- Simplified footer with Cancel button -->
      <v-card-actions class="px-3 py-2">
        <v-btn size="small" color="error" @click="cancel" variant="text">
          Cancel
        </v-btn>
        <v-spacer></v-spacer>
        <span class="text-caption text-grey">Style settings auto-populated from saved defaults</span>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.fsq-modal-card {
  max-height: 90vh;
  overflow-y: auto;
}

/* Large Preview Container - Left Column */
.large-preview-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 4px;
  overflow: hidden;
  background: #000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.large-preview-container .preview-video-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

.large-preview-container .black-bar-overlay {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  background: rgba(0, 0, 0, 0.75);
  z-index: 2;
  pointer-events: none;
}

.large-preview-container .quote-preview {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  color: white;
  padding: 8% 8% 15% 8%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  z-index: 3;
}

/* Word count and AI status badges */
.word-count-badge,
.ai-status-badge {
  display: inline-flex;
}

/* Quote input wrapper - compact styling */
.quote-input-wrapper :deep(textarea) {
  font-size: 13px !important;
  line-height: 1.4 !important;
}

/* Style settings section */
.style-settings {
  background: rgba(255, 255, 255, 0.03);
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 8px;
}

/* Render mode section */
.render-mode-section {
  background: rgba(255, 255, 255, 0.03);
  padding: 8px;
  border-radius: 4px;
}

/* Split preview panel */
.split-preview-panel {
  background: rgba(103, 58, 183, 0.1);
  padding: 12px;
  border-radius: 4px;
  border: 1px solid rgba(103, 58, 183, 0.3);
}

.compact-fsq-modal {
  font-size: 0.9rem;
}

.compact-fsq-modal :deep(.v-label),
.compact-fsq-modal :deep(.v-field-label),
.compact-fsq-modal :deep(.v-input__details),
.compact-fsq-modal :deep(.v-messages) {
  font-size: 0.85rem;
}

:deep(.v-field-label--floating) {
  transform: translateY(-1em) !important;
}

:deep(.v-text-field .v-field-label--floating) {
  transform: translateY(-1.7em) !important;
}

/* Larger Quote Field */
.large-quote-field :deep(textarea) {
  font-size: 16px !important;
  line-height: 1.6 !important;
  padding: 12px !important;
}

.large-quote-field :deep(.v-field__input) {
  min-height: 200px !important;
}

/* AI Processing Visual Feedback */
.ai-analyzing {
  margin-top: 7px !important;
  margin-bottom: 7px !important;
}

.ai-analyzing :deep(.v-field) {
  border: 7px solid #9C27B0 !important;
  border-radius: 0 !important;
}

.ai-analyzing :deep(textarea) {
  max-height: none !important;
  overflow-y: hidden !important;
}

.ai-rejected {
  margin-top: 7px !important;
  margin-bottom: 7px !important;
}

.ai-rejected :deep(.v-field) {
  border: 7px solid #F44336 !important;
  border-radius: 0 !important;
}

.ai-rejected :deep(textarea) {
  max-height: none !important;
  overflow-y: hidden !important;
}

.ai-approved {
  margin-top: 7px !important;
  margin-bottom: 7px !important;
}

.ai-approved :deep(.v-field) {
  border: 7px solid #4CAF50 !important;
  border-radius: 0 !important;
}

.ai-approved :deep(textarea) {
  max-height: none !important;
  overflow-y: hidden !important;
}

.ai-auto {
  margin-top: 7px !important;
  margin-bottom: 7px !important;
}

.ai-auto :deep(.v-field) {
  border: 7px solid #2196F3 !important;
  border-radius: 0 !important;
}

.ai-auto :deep(textarea) {
  max-height: none !important;
  overflow-y: hidden !important;
}

/* AI Model Badge */
.ai-model-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  z-index: 100;
  pointer-events: none;
  font-family: 'Courier New', monospace;
  font-size: 9px;
  line-height: 1.2;
  padding: 4px 6px;
  background: rgba(0, 0, 0, 0.85);
  color: white;
  border-radius: 2px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.ai-model-badge.badge-analyzing {
  border-left: 3px solid #9C27B0;
}

.ai-model-badge.badge-rejected {
  border-left: 3px solid #F44336;
}

.ai-model-badge.badge-approved {
  border-left: 3px solid #4CAF50;
}

.ai-model-badge.badge-auto {
  border-left: 3px solid #2196F3;
}

.badge-content {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.badge-service {
  font-weight: bold;
  text-transform: uppercase;
  opacity: 0.8;
  font-size: 8px;
}

.badge-model {
  font-weight: normal;
  color: #00ff00;
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Base styles for all quote preview containers - 16:9 aspect ratio */
.quote-preview-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 0 !important;
  overflow: hidden;
  background: #000;
}

.preview-video-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

.black-bar-overlay {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  background: rgba(0, 0, 0, 0.75);
  z-index: 2;
  pointer-events: none;
}

.quote-preview {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  color: white;
  padding: 10% 10% 20% 10%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  z-index: 3;
  box-sizing: border-box;
}

.quote-text {
  font-style: italic;
  line-height: 1.4;
  font-family: Georgia, serif;
  width: 100%;
  word-wrap: break-word;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
  flex-shrink: 0;
  /* Font size comes from computed property - scaled to match 1920px rendering */
}

.quote-source {
  font-weight: 500;
  color: rgba(255,255,255,0.9);
  text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
  position: absolute;
  bottom: 5%;
  left: 10%;
  right: 10%;
  /* Font size inherited and scaled from parent */
}

.quote-timestamp {
  font-size: 0.85rem;
  color: #b0b0b0;
  font-family: 'Courier New', monospace;
}

/* Responsive scaling now handled by percentage-based font sizes that scale with container */

.font-size-slider {
  margin-top: 8px;
}

.word-count-display {
  font-size: 12px;
  color: #666;
  text-align: left;
  margin-top: 4px;
}

.ai-feedback-message {
  font-size: 13px;
  padding: 4px 8px;
  margin-top: 4px;
  font-weight: 500;
}

.ai-message-analyzing {
  color: #9C27B0;
}

.ai-message-rejected {
  color: #D32F2F;
}

.ai-message-approved {
  color: #388E3C;
}

.ai-message-auto {
  color: #1976D2;
}

.ai-credit-text {
  font-size: 9px;
  color: #999;
  font-family: 'Courier New', monospace;
  margin-top: -8px;
  margin-bottom: 8px;
  padding-left: 4px;
  opacity: 0.7;
}

.split-segment {
  background: rgba(33, 150, 243, 0.05);
  padding: 8px 12px;
  border-radius: 0 !important;
  border-left: 3px solid #2196F3;
}

.segment-text {
  font-style: italic;
  color: #424242;
  line-height: 1.5;
}

.ai-recommendation-panel {
  border-radius: 0 !important;
}

.ai-recommendation-panel.ai-panel-analyzing {
  border: 3px solid #9C27B0;
}

.ai-recommendation-panel.ai-panel-analyzing .ai-recommendation-header {
  background: linear-gradient(135deg, rgba(156, 39, 176, 0.1) 0%, rgba(156, 39, 176, 0.05) 100%);
}

.ai-recommendation-panel.ai-panel-rejected {
  border: 3px solid #F44336;
}

.ai-recommendation-panel.ai-panel-rejected .ai-recommendation-header {
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%);
}

.ai-recommendation-panel.ai-panel-approved {
  border: 3px solid #4CAF50;
}

.ai-recommendation-panel.ai-panel-approved .ai-recommendation-header {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%);
}

.ai-recommendation-panel.ai-panel-auto {
  border: 3px solid #2196F3;
}

.ai-recommendation-panel.ai-panel-auto .ai-recommendation-header {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(33, 150, 243, 0.05) 100%);
}

.ai-recommendation-header {
  font-weight: 600;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.15) 0%, rgba(255, 193, 7, 0.05) 100%) !important;
  border-left: 4px solid #FFC107 !important;
}

.ai-recommendation-content {
  padding: 12px 0;
}

.fsq-modal-card :deep(.v-field),
.fsq-modal-card :deep(.v-text-field),
.fsq-modal-card :deep(.v-textarea),
.fsq-modal-card :deep(.v-card),
.fsq-modal-card :deep(.v-alert),
.fsq-modal-card :deep(.v-btn),
.fsq-modal-card :deep(.v-expansion-panel),
.fsq-modal-card :deep(.v-chip) {
  border-radius: 0 !important;
}
</style>

<script>
import axios from 'axios'
import { useLLM } from '@/composables/useLLM'
import { useLLMState } from '@/composables/useLLMState'
import aiFieldMixin from '@/mixins/aiFieldMixin'
import { getColorValue } from '@/utils/themeColorMap'

export default {
  name: 'FsqModal',
  mixins: [aiFieldMixin],
  props: {
    show: { type: Boolean, required: true },
    currentEpisode: { type: String, default: '' },
    speakerWpm: { type: Number, default: 150 },  // Speaker WPM from profile
    editMode: { type: Boolean, default: false },
    initialData: { type: Object, default: null }
  },
  emits: ['update:show', 'submit'],
  data() {
    return {
      formValid: false,
      loading: false,
      error: '',
      quote: '',
      slug: '',
      slugAutoGenerated: true,  // Track if slug was auto-generated or manually edited
      source: '',
      sourceOptions: [],  // Autocomplete options from previous FSQ sources in episode
      includeAttribution: true,
      quoteStyle: 'left',  // Default alignment: left
      fontFamily: 'serif',  // Default font: serif (Georgia)
      fontSize: 25,
      renderMode: 'png',  // Default render mode: Transparent PNG
      duration: '00:00:05:00',
      lastSubmittedSource: '',
      sourceAutopopulated: false,
      analyzeTimeout: null,
      aiActionPending: false,  // Keep for accept/reject flow
      aiPreviousQuote: '',     // Keep for revert functionality
      splitRecommendations: null,  // Keep for split recommendations
      aiGenerationInfo: null,  // Keep for AI model attribution
      aiRecommendationExpanded: [],  // Keep for UI state
      previewBackgroundVideo: '/assets/preview-background.mp4',  // Default, loaded from settings
      // Quote formatting settings
      stripExteriorQuotes: true,
      regenerateExteriorQuotes: false,
      normalizeInteriorQuotes: true,
      attributionDashStyle: 'regular',
      // Split preview controls (separate from original)
      splitQuoteStyle: 'left',
      splitFontFamily: 'serif',
      splitFontSize: 25,
      // Manual split markers
      manualSplitPoints: [],  // Array of character positions for manual splits
      manualSplitExpanded: false,  // Whether manual split section is expanded
      // Manual split preview controls (separate from LLM split)
      manualSplitQuoteStyle: 'left',
      manualSplitFontFamily: 'serif',
      manualSplitFontSize: 25,
      // UI state for new compact layout
      showSplitPanel: false
    }
  },
  setup() {
    const { intelligentQuoteSplit, normalizeNestedQuotes, lastUsedModel } = useLLM()
    const llmState = useLLMState()
    return { intelligentQuoteSplit, normalizeNestedQuotes, lastUsedModel, llmState }
  },
  watch: {
    async show(newVal) {
      if (newVal) {
        // Add escape key listener when dialog opens
        document.addEventListener('keydown', this.handleEscapeKey)
        // Fetch sources from current episode rundown
        await this.fetchEpisodeSources()

        // Load initial data if in edit mode
        if (this.editMode && this.initialData) {
          console.log('📝 Loading FSQ for editing:', this.initialData);
          this.loadInitialData();
        } else if (!this.source) {
          // Auto-populate source from last submitted or most recent in episode
          if (this.lastSubmittedSource) {
            this.source = this.lastSubmittedSource
            this.sourceAutopopulated = true
          } else if (this.sourceOptions.length > 0) {
            // Use most recent source (first in list)
            this.source = this.sourceOptions[0]
            this.sourceAutopopulated = true
          }
        }

        this.$nextTick(() => {
          if (this.$refs.quoteFieldRef) {
            this.$refs.quoteFieldRef.focus()
          }

          // Restart video preview when modal opens
          if (this.$refs.previewVideoRef) {
            this.$refs.previewVideoRef.load()
            this.$refs.previewVideoRef.play().catch(err => {
              console.warn('⚠️ Video autoplay prevented:', err)
            })
          }
        })
      } else {
        // Remove escape key listener when dialog closes
        document.removeEventListener('keydown', this.handleEscapeKey)
      }
    },
    source(newVal) {
      if (this.sourceAutopopulated && newVal !== this.lastSubmittedSource) {
        this.sourceAutopopulated = false
      }
    }
  },
  computed: {
    // Cue type color for header - dynamically loaded from database
    cueTypeColor() {
      return getColorValue('fsq')
    },

    // AI status display computed properties for compact layout
    aiStatusColor() {
      switch (this.aiState) {
        case 'analyzing': return 'purple'
        case 'rejected': return 'error'
        case 'approved': return 'success'
        case 'auto': return 'info'
        default: return 'grey'
      }
    },
    aiStatusIcon() {
      switch (this.aiState) {
        case 'analyzing': return 'mdi-brain'
        case 'rejected': return 'mdi-alert-circle'
        case 'approved': return 'mdi-check-circle'
        case 'auto': return 'mdi-robot'
        default: return 'mdi-help-circle'
      }
    },
    aiStatusText() {
      switch (this.aiState) {
        case 'analyzing': return 'Analyzing...'
        case 'rejected': return 'Review needed'
        case 'approved': return 'Approved'
        case 'auto': return 'Auto-processed'
        default: return ''
      }
    },

    // LLM visual feedback from universal framework
    quoteFieldClass() {
      return this.llmState.getVisualClass('field', 'fsq-quote-field')
    },
    quoteFieldStyle() {
      return this.llmState.getVisualStyle('field', 'fsq-quote-field')
    },
    isLLMActive() {
      return this.llmState.isTargetActive('field', 'fsq-quote-field')
    },
    currentLLMOperation() {
      const ops = this.llmState.getOperationsForTarget('field', 'fsq-quote-field')
      return ops.length > 0 ? ops[ops.length - 1] : null
    },

    quoteRules() {
      return [
        v => !!v || 'Quote text is required',
        v => !v || v.length >= 10 || 'Quote must be at least 10 characters'
      ]
    },
    slugRules() {
      return [
        v => !!v || 'Slug is required'
      ]
    },
    sourceRules() {
      return [
        v => !!v || 'Source/attribution is required',
        v => !v || v.length <= 100 || 'Source must be 100 characters or less'
      ]
    },
    styleOptions() {
      return [
        { title: 'Centered', value: 'center' },
        { title: 'Left Aligned', value: 'left' },
        { title: 'Right Aligned', value: 'right' },
        { title: 'Large Text', value: 'large' },
        { title: 'Elegant', value: 'elegant' }
      ]
    },
    durationOptions() {
      return [
        { title: '3 seconds', value: '00:00:03:00' },
        { title: '5 seconds', value: '00:00:05:00' },
        { title: '7 seconds', value: '00:00:07:00' },
        { title: '10 seconds', value: '00:00:10:00' },
        { title: '15 seconds', value: '00:00:15:00' },
        { title: 'Custom', value: 'custom' }
      ]
    },
    fontOptions() {
      return [
        { title: 'Sans Serif (Helvetica)', value: 'sans-serif' },
        { title: 'Serif (Georgia)', value: 'serif' },
        { title: 'Monospace (Courier)', value: 'monospace' }
      ]
    },
    previewStyle() {
      return {
        alignItems: this.quoteStyle === 'center' ? 'center' :
                   this.quoteStyle === 'left' ? 'flex-start' :
                   this.quoteStyle === 'right' ? 'flex-end' : 'center'
      }
    },
    quoteTextStyle() {
      const fontMap = {
        'sans-serif': 'Helvetica, Arial, sans-serif',
        'serif': 'Georgia, "Times New Roman", serif',
        'monospace': '"Courier New", Courier, monospace'
      }
      // Calculate font size as viewport width units to scale with container
      // fontSize is the pixel value at 1920px wide, convert to vw units
      const fontSizeVw = (this.fontSize / 1920) * 100

      return {
        fontFamily: fontMap[this.fontFamily] || fontMap['sans-serif'],
        fontSize: `${fontSizeVw}vw`,
        textAlign: this.quoteStyle === 'center' ? 'center' :
                  this.quoteStyle === 'left' ? 'left' :
                  this.quoteStyle === 'right' ? 'right' : 'center'
      }
    },
    quoteSourceStyle() {
      const fontMap = {
        'sans-serif': 'Helvetica, Arial, sans-serif',
        'serif': 'Georgia, "Times New Roman", serif',
        'monospace': '"Courier New", Courier, monospace'
      }
      return {
        fontFamily: fontMap[this.fontFamily] || fontMap['sans-serif'],
        textAlign: this.quoteStyle === 'center' ? 'center' :
                  this.quoteStyle === 'left' ? 'left' :
                  this.quoteStyle === 'right' ? 'right' : 'center'
      }
    },
    formattedQuotePreview() {
      const rawText = this.quote || 'Quote text will appear here...';
      const decoded = this.decodeQuoteText(rawText);
      const escaped = decoded
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>');

      // Add quotes back based on settings
      if (this.regenerateExteriorQuotes) {
        return '"' + escaped + '"';
      }
      return escaped;
    },

    attributionPrefix() {
      // Return the appropriate dash/prefix based on settings
      const dashMap = {
        'regular': '— ',
        'emdash': '—',
        'none': ''
      }
      return dashMap[this.attributionDashStyle] || '— '
    },

    // Split preview computed properties
    getSplitPreviewStyle() {
      return {
        alignItems: this.splitQuoteStyle === 'center' ? 'center' :
                   this.splitQuoteStyle === 'left' ? 'flex-start' :
                   this.splitQuoteStyle === 'right' ? 'flex-end' : 'center'
      }
    },
    getSplitTextStyle() {
      const fontMap = {
        'sans-serif': 'Helvetica, Arial, sans-serif',
        'serif': 'Georgia, "Times New Roman", serif',
        'monospace': '"Courier New", Courier, monospace'
      }
      // Calculate font size as viewport width units to scale with container
      // splitFontSize is the pixel value at 1920px wide, convert to vw units
      const fontSizeVw = (this.splitFontSize / 1920) * 100

      return {
        fontFamily: fontMap[this.splitFontFamily] || fontMap['sans-serif'],
        fontSize: `${fontSizeVw}vw`,
        textAlign: this.splitQuoteStyle === 'center' ? 'center' :
                  this.splitQuoteStyle === 'left' ? 'left' :
                  this.splitQuoteStyle === 'right' ? 'right' : 'center'
      }
    },
    getSplitSourceStyle() {
      const fontMap = {
        'sans-serif': 'Helvetica, Arial, sans-serif',
        'serif': 'Georgia, "Times New Roman", serif',
        'monospace': '"Courier New", Courier, monospace'
      }
      return {
        fontFamily: fontMap[this.splitFontFamily] || fontMap['sans-serif'],
        textAlign: this.splitQuoteStyle === 'center' ? 'center' :
                  this.splitQuoteStyle === 'left' ? 'left' :
                  this.splitQuoteStyle === 'right' ? 'right' : 'center'
      }
    },

    // Manual split preview computed properties
    getManualSplitPreviewStyle() {
      return {
        alignItems: this.manualSplitQuoteStyle === 'center' ? 'center' :
                   this.manualSplitQuoteStyle === 'left' ? 'flex-start' :
                   this.manualSplitQuoteStyle === 'right' ? 'flex-end' : 'center'
      }
    },
    getManualSplitTextStyle() {
      const fontMap = {
        'sans-serif': 'Helvetica, Arial, sans-serif',
        'serif': 'Georgia, "Times New Roman", serif',
        'monospace': '"Courier New", Courier, monospace'
      }
      // Calculate font size as viewport width units to scale with container
      const fontSizeVw = (this.manualSplitFontSize / 1920) * 100

      return {
        fontFamily: fontMap[this.manualSplitFontFamily] || fontMap['sans-serif'],
        fontSize: `${fontSizeVw}vw`,
        textAlign: this.manualSplitQuoteStyle === 'center' ? 'center' :
                  this.manualSplitQuoteStyle === 'left' ? 'left' :
                  this.manualSplitQuoteStyle === 'right' ? 'right' : 'center'
      }
    },
    getManualSplitSourceStyle() {
      const fontMap = {
        'sans-serif': 'Helvetica, Arial, sans-serif',
        'serif': 'Georgia, "Times New Roman", serif',
        'monospace': '"Courier New", Courier, monospace'
      }
      return {
        fontFamily: fontMap[this.manualSplitFontFamily] || fontMap['sans-serif'],
        textAlign: this.manualSplitQuoteStyle === 'center' ? 'center' :
                  this.manualSplitQuoteStyle === 'left' ? 'left' :
                  this.manualSplitQuoteStyle === 'right' ? 'right' : 'center'
      }
    },

    // Manual split segments computed from split points
    manualSplitSegments() {
      if (!this.quote || this.manualSplitPoints.length === 0) {
        return [this.quote]
      }

      const segments = []
      let lastIndex = 0

      // Sort split points to ensure correct order
      const sortedPoints = [...this.manualSplitPoints].sort((a, b) => a - b)

      for (const splitPoint of sortedPoints) {
        const segment = this.quote.substring(lastIndex, splitPoint).trim()
        if (segment) segments.push(segment)
        lastIndex = splitPoint
      }

      // Add final segment
      const finalSegment = this.quote.substring(lastIndex).trim()
      if (finalSegment) segments.push(finalSegment)

      return segments
    }
  },
  async mounted() {
    document.addEventListener('keydown', this.handleKeydown)
    await this.loadDefaultSettings()
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown)
    document.removeEventListener('keydown', this.handleEscapeKey)
  },
  methods: {
    /**
     * Load initial data when editing an existing FSQ cue
     */
    loadInitialData() {
      if (!this.initialData) return;

      const data = this.initialData.rawData || this.initialData;

      // Load quote and attribution from cue data
      this.quote = data.quote || '';
      this.source = data.attribution || '';
      this.slug = data.slug || '';
      this.slugAutoGenerated = false;  // Don't auto-generate when editing

      // Load style settings if available
      // Check all possible field names: quoteStyle (legacy), alignment (card data), style (parsed cue)
      const styleValue = data.quoteStyle || data.alignment || data.style;
      if (styleValue) {
        // Backward compatibility: normalize 'centered' to 'center'
        this.quoteStyle = styleValue === 'centered' ? 'center' : styleValue;
      }
      if (data.fontFamily) this.fontFamily = data.fontFamily;
      if (data.fontSize) this.fontSize = parseInt(data.fontSize) || 25;
      if (data.duration) this.duration = data.duration;

      console.log('✅ Loaded FSQ data for editing:', { quote: this.quote, source: this.source, slug: this.slug, style: this.quoteStyle });
    },

    /**
     * Load default settings from database
     */
    async loadDefaultSettings() {
      try {
        const token = localStorage.getItem('auth-token')
        const response = await axios.get('/api/settings/', {
          headers: token ? {
            'Authorization': `Bearer ${token}`
          } : {}
        })

        const settings = response.data.generation || {}
        console.log('📥 Loaded FSQ default settings:', settings)

        // Apply default alignment (normalize 'centered' → 'center' for backward compatibility)
        if (settings.fsq_default_alignment) {
          this.quoteStyle = settings.fsq_default_alignment === 'centered' ? 'center' : settings.fsq_default_alignment
        }

        // Apply default font
        if (settings.fsq_default_font) {
          this.fontFamily = settings.fsq_default_font
        }

        // Apply default font size
        if (settings.fsq_default_font_size) {
          this.fontSize = settings.fsq_default_font_size
        }

        // Apply default attribution setting
        if (settings.fsq_include_attribution_by_default !== undefined) {
          this.includeAttribution = settings.fsq_include_attribution_by_default
        }

        // Apply preview background video path
        if (settings.fsq_background_video) {
          this.previewBackgroundVideo = settings.fsq_background_video
        }

        // Apply quote formatting settings
        if (settings.fsq_strip_exterior_quotes !== undefined) {
          this.stripExteriorQuotes = settings.fsq_strip_exterior_quotes
        }
        if (settings.fsq_regenerate_exterior_quotes !== undefined) {
          this.regenerateExteriorQuotes = settings.fsq_regenerate_exterior_quotes
        }
        if (settings.fsq_normalize_interior_quotes !== undefined) {
          this.normalizeInteriorQuotes = settings.fsq_normalize_interior_quotes
        }
        if (settings.fsq_attribution_dash_style) {
          this.attributionDashStyle = settings.fsq_attribution_dash_style
        }

        console.log('✅ FSQ defaults applied:', {
          alignment: this.quoteStyle,
          font: this.fontFamily,
          fontSize: this.fontSize,
          includeAttribution: this.includeAttribution,
          previewVideo: this.previewBackgroundVideo,
          stripExteriorQuotes: this.stripExteriorQuotes,
          regenerateExteriorQuotes: this.regenerateExteriorQuotes,
          normalizeInteriorQuotes: this.normalizeInteriorQuotes,
          attributionDashStyle: this.attributionDashStyle
        })

      } catch (error) {
        console.error('Failed to load FSQ default settings:', error)
        // Keep hardcoded defaults if loading fails
      }
    },

    // Fetch all FSQ sources from current episode rundown
    async fetchEpisodeSources() {
      if (!this.currentEpisode) {
        console.log('⚠️ No current episode specified for source lookup')
        return
      }

      try {
        const token = localStorage.getItem('auth-token')
        const response = await axios.get(`/api/episodes/${this.currentEpisode}/rundown`, {
          headers: token ? {
            'Authorization': `Bearer ${token}`
          } : {}
        })

        // API returns array directly or object with rundown property
        let rundownItems = response.data
        if (rundownItems && !Array.isArray(rundownItems)) {
          rundownItems = rundownItems.rundown || rundownItems.items || []
        }
        if (!Array.isArray(rundownItems)) {
          console.warn('⚠️ Unexpected response format, expected array:', rundownItems)
          rundownItems = []
        }

        const sources = []

        // Extract attribution from all FSQ cues in the rundown
        rundownItems.forEach(item => {
          if (item.script) {
            // Match [Attribution: ...] pattern in FSQ cues
            const attributionMatches = item.script.matchAll(/\[Attribution:\s*([^\]]+)\]/g)
            for (const match of attributionMatches) {
              const source = match[1].trim()
              if (source && !sources.includes(source)) {
                sources.push(source)
              }
            }
          }
        })

        // Reverse to show most recent first (assuming rundown is chronological)
        this.sourceOptions = sources.reverse()
        console.log(`📋 Loaded ${sources.length} unique FSQ sources from episode ${this.currentEpisode}`)

      } catch (error) {
        console.error('❌ Failed to fetch episode sources:', error)
        this.sourceOptions = []
      }
    },

    // Normalize slug to lowercase with hyphens (auto-correct on blur)
    normalizeSlug() {
      if (!this.slug) return

      this.slug = this.slug
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9\s-]/g, '')  // Remove special characters
        .replace(/\s+/g, '-')           // Replace spaces with hyphens
        .replace(/-+/g, '-')            // Replace multiple hyphens with single
        .replace(/^-+|-+$/g, '')        // Remove leading/trailing hyphens
        .substring(0, 50)               // Limit to 50 characters
    },

    // Calculate duration based on word count and speaker WPM
    calculateDurationFromWPM(wordCount) {
      const wpm = this.speakerWpm || 150
      const durationInSeconds = Math.ceil((wordCount / wpm) * 60)

      const hours = Math.floor(durationInSeconds / 3600)
      const minutes = Math.floor((durationInSeconds % 3600) / 60)
      const seconds = durationInSeconds % 60

      // Return in HH:MM:SS:FF format (frames = 00 for FSQ)
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:00`
    },

    hasNestedQuotes(text) {
      if (!text) return false

      // Decode and strip surrounding quotes first
      let decoded = this.decodeQuoteText(text)

      // Now check for quotes INSIDE the text (not encapsulating)
      const doubleQuotes = (decoded.match(/"/g) || []).length
      const singleQuotes = (decoded.match(/'/g) || []).length
      const apostrophes = (decoded.match(/[a-z]'|'[a-z]/gi) || []).length
      const actualSingleQuotes = singleQuotes - apostrophes

      // If there are double quotes inside (after stripping outer quotes), we have nested quotes
      const hasInternalDoubleQuotes = doubleQuotes > 0
      const hasMixedQuotes = doubleQuotes > 0 && actualSingleQuotes > 0
      const hasMultipleDoubles = doubleQuotes > 2
      const hasMultipleSingles = actualSingleQuotes > 2

      const hasNesting = hasInternalDoubleQuotes || hasMixedQuotes || hasMultipleDoubles || hasMultipleSingles

      if (hasNesting) {
        console.log('🔍 Nested quotes detected:', {
          text: decoded,
          doubleQuotes,
          singleQuotes,
          apostrophes,
          actualSingleQuotes,
          hasInternalDoubleQuotes,
          hasMixedQuotes,
          hasMultipleDoubles,
          hasMultipleSingles
        })
      }

      return hasNesting
    },

    decodeQuoteText(text) {
      if (!text) return text

      let decoded = text
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/\\"/g, '"')
        .replace(/\\'/g, "'")
        .replace(/\\n/g, '\n')
        .replace(/\\r/g, '\r')
        .replace(/\\t/g, '\t')
        .replace(/\\\\/g, '\\')

      // Strip surrounding quotes based on settings
      if (this.stripExteriorQuotes) {
        decoded = decoded.trim()
        if ((decoded.startsWith('"') && decoded.endsWith('"')) ||
            (decoded.startsWith("'") && decoded.endsWith("'"))) {
          decoded = decoded.slice(1, -1).trim()
          console.log('🔓 Stripped exterior quotes per settings')
        }
      }

      return decoded
    },

    handleKeydown(event) {
      console.log('⌨️ FsqModal keydown:', event.key, 'show:', this.show)
      if (event.key === 'Escape' && this.show) {
        console.log('🚪 Closing FSQ modal via Esc key')
        event.preventDefault()
        event.stopPropagation()
        this.cancel()
      }
    },

    async handleQuotePaste() {
      console.log('📋 Paste detected, waiting for v-model update...')
      await this.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))
      console.log('📋 Quote pasted (length: ' + this.quote.length + ')')

      // Cancel any ongoing analysis
      this.cancelAnalysis()

      // If there's a pending action, clear it (user is pasting new content)
      if (this.aiActionPending) {
        console.log('🔄 Clearing pending AI action - user pasted new content')
        this.aiActionPending = false
        this.aiPreviousQuote = ''
      }

      // Reset AI state
      this.aiState = null
      this.aiMessage = ''
      this.splitRecommendations = null
      this.aiGenerationInfo = null

      // Auto-detect and extract attribution from pasted content
      this.autoExtractAttribution()

      // Use debounce for paste too (gives user time to edit after paste)
      clearTimeout(this.analyzeTimeout)
      this.analyzeTimeout = setTimeout(() => {
        if (this.quote && this.quote.length > 20) {
          console.log('🤖 Starting AI analysis after paste (2s delay)...')
          this.analyzeQuote()
        }
      }, 2000)
    },

    handleQuoteInput() {
      // Cancel any ongoing analysis immediately when user starts typing
      if (this.aiState === 'analyzing') {
        console.log('⏸️ User started typing - cancelling ongoing analysis')
        this.cancelAnalysis()
      }

      // Detect significant text changes (clearing field or major edits)
      const significantChange = Math.abs(this.quote.length - (this.aiPreviousQuote?.length || 0)) > 50

      // If there's a pending action but the text has changed significantly, reset everything
      if (this.aiActionPending && significantChange) {
        console.log('🔄 Significant text change detected - resetting AI state')
        this.aiActionPending = false
        this.aiPreviousQuote = ''
        this.aiState = null
        this.aiMessage = ''
        this.splitRecommendations = null
        this.aiGenerationInfo = null
      }

      // Auto-detect and extract attribution from quote text
      this.autoExtractAttribution()

      // Auto-generate slug from first 3 words if slug is empty
      this.autoGenerateSlug()
    },

    handleSlugInput() {
      // Mark slug as manually edited (stop auto-generation)
      this.slugAutoGenerated = false
    },

    autoGenerateSlug() {
      // Only auto-generate if slug was auto-generated (not manually edited by user)
      if (this.slugAutoGenerated && this.quote && this.quote.trim()) {
        const cleanedQuote = this.decodeQuoteText(this.quote)
        const words = cleanedQuote
          .trim()
          .split(/\s+/)
          .filter(word => word.length > 0)
          .slice(0, 3)

        if (words.length > 0) {
          this.slug = words
            .join(' ')
            .toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-')
            .replace(/^-+|-+$/g, '')
        }
      }

      // Clear AI state when user is actively editing (but not if there's a pending action)
      if (this.aiState && this.aiState !== 'analyzing' && !this.aiActionPending) {
        this.aiState = null
        this.aiMessage = ''
        this.splitRecommendations = null
        this.aiGenerationInfo = null
      }

      // Don't trigger new analysis if there's a pending action (user hasn't accepted/rejected yet)
      if (this.aiActionPending) {
        return
      }

      // Reset debounce timer - analysis will start 2 seconds after user stops typing
      clearTimeout(this.analyzeTimeout)
      this.analyzeTimeout = setTimeout(() => {
        if (this.quote.length > 20) {
          console.log('🤖 Triggering AI quote analysis after typing pause (2s)...')
          this.analyzeQuote()
        }
      }, 2000)
    },

    /**
     * Auto-detect and extract attribution from quote text
     * This runs BEFORE exterior quote stripping to detect content outside the quotes
     *
     * Typical patterns:
     * "Quote text"
     * - Person Name
     *
     * "Quote text"
     * — Person Name
     *
     * "Quote text" - Person Name
     */
    autoExtractAttribution() {
      if (!this.quote || this.quote.trim().length === 0) return

      const text = this.quote.trim()

      // Attribution patterns - prioritize newline-separated format (most common)
      const patterns = [
        // Pattern 1: Quote on first line(s), attribution on new line starting with dash/emdash
        // This is the most common format when pasting from documents
        /^([""]?.+?[""]?)\s*\n\s*[—\-–]\s*(.+)$/s,

        // Pattern 2: Quote on first line(s), attribution on new line (no dash)
        // Handles cases where newline itself indicates attribution
        /^([""].+?[""])\s*\n\s*([A-Z].+)$/s,

        // Pattern 3: Same line - quote followed by dash and attribution
        /^([""]?.+?[""]?)\s*[—\-–]\s*(.+)$/,

        // Pattern 4: Dash at very end of text (after closing quote)
        /^(.+?[""])\s*[—\-–]\s*(.+)$/
      ]

      for (const pattern of patterns) {
        const match = text.match(pattern)
        if (match) {
          const potentialQuote = match[1].trim()
          const potentialAttribution = match[2].trim()

          // Validate: attribution should be reasonable
          const isValidAttribution = (
            potentialAttribution.length > 2 &&
            potentialAttribution.length < 100 &&
            potentialQuote.length > 10 &&
            potentialQuote.length > potentialAttribution.length &&
            // Attribution should start with capital letter or dash
            potentialAttribution.match(/^[—\-–]?[A-Z]/) &&
            // Quote should have some content (not just quotes)
            potentialQuote.replace(/[""\s]/g, '').length > 5
          )

          if (isValidAttribution) {
            console.log('✂️ Auto-detected attribution:', {
              quote: potentialQuote,
              attribution: potentialAttribution,
              pattern: pattern.source.substring(0, 50) + '...'
            })

            // Clean the quote: remove surrounding quotes (will be processed later by strip settings)
            let cleanQuote = potentialQuote
              .replace(/^[""]/, '')
              .replace(/[""]$/, '')
              .trim()

            // Clean the attribution: remove leading dash if present
            let cleanAttribution = potentialAttribution
              .replace(/^[—\-–]\s*/, '')
              .trim()

            // Always extract attribution if found in quote text - override whatever is in the field
            this.quote = cleanQuote
            this.source = cleanAttribution
            this.includeAttribution = true
            this.sourceAutopopulated = false // Clear flag since we're replacing with extracted value
            console.log('✅ Attribution auto-extracted (overriding existing):', {
              extractedQuote: cleanQuote.substring(0, 50) + '...',
              extractedAttribution: cleanAttribution
            })
            return // Stop after first match
          }
        }
      }
    },

    cancelAnalysis() {
      // Cancel the debounce timeout
      clearTimeout(this.analyzeTimeout)

      // Stop any active LLM operations on this field
      const ops = this.llmState.getOperationsForTarget('field', 'fsq-quote-field')
      ops.forEach(op => {
        this.llmState.stopOperation(op.id, {
          notify: false,
          message: 'Analysis cancelled by user'
        })
      })
    },

    async analyzeQuote() {
      if (!this.quote || this.quote.length < 20) {
        console.log('⏭️ Quote too short for AI analysis (< 20 chars)')
        return
      }

      // Use universal LLM framework with automatic state management
      const result = await this.llmState.withLLM(
        'field',
        'fsq-quote-field',
        'analyzing',
        async () => {
          // STEP 1: Decode escape sequences (auto-approve, no user action needed)
          let workingQuote = this.decodeQuoteText(this.quote)
          if (workingQuote !== this.quote) {
            console.log('🔓 Auto-stripping surrounding quotes:', { before: this.quote, after: workingQuote })
            this.quote = workingQuote
            // Don't return - continue with analysis
          }

          // STEP 2: Check for nested quotes (auto-approve, no user action needed)
          // Only normalize if setting is enabled
          if (this.normalizeInteriorQuotes && this.hasNestedQuotes(workingQuote)) {
            console.log('📝 Nested quotes detected, normalizing...')
            const normalized = await this.normalizeNestedQuotes(workingQuote)

            if (normalized !== this.quote) {
              console.log('✨ Auto-normalizing nested quotes:', { before: this.quote, after: normalized })
              this.quote = normalized
              workingQuote = normalized
              // Don't return - continue with analysis
            }
          } else if (!this.normalizeInteriorQuotes) {
            console.log('⏭️ Skipping nested quote normalization (disabled in settings)')
          }

          // STEP 3: Load settings
          console.log('📥 Loading generation settings from backend...')
          const token = localStorage.getItem('auth-token')
          const settingsResponse = await axios.get('/api/settings/', {
            headers: token ? {
              'Authorization': `Bearer ${token}`
            } : {}
          })

          const settings = settingsResponse.data.generation || {}
          const splitConfig = {
            maxLines: settings.fsq_max_lines || 5,
            charsPerLine: settings.fsq_chars_per_line || 50,
            fontSize: settings.default_font_size || '19px',
            minSecondScreen: settings.fsq_min_second_screen || 80,
            splitStrategy: settings.fsq_split_strategy || 'smart',
            balanceThresholdPercent: settings.fsq_balance_threshold_percent || 30,
            preferSentenceBoundaries: settings.fsq_prefer_sentence_boundaries !== false,
            allowMidSentenceSplit: settings.fsq_allow_mid_sentence_split || false,
            overflowHandling: settings.fsq_overflow_handling || 'multi_segment'
          }

          // STEP 4: Call AI for split analysis
          console.log('🧠 Calling intelligentQuoteSplit() with smart split logic...')
          const segments = await this.intelligentQuoteSplit(workingQuote, splitConfig)

          const now = new Date()
          this.aiGenerationInfo = {
            model: this.lastUsedModel?.model || 'qwen2.5-coder:7b',
            service: this.lastUsedModel?.service || 'ollama',
            timestamp: now.toLocaleString('en-US', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false
            })
          }

          if (segments.length > 1) {
            this.splitRecommendations = segments
            this.aiRecommendationExpanded = []
            console.log(`✂️ AI recommends splitting into ${segments.length} segments`)
            return { action: 'split', segments, count: segments.length }
          } else {
            this.splitRecommendations = null
            this.aiRecommendationExpanded = []
            console.log('✅ AI approved - quote fits as single FSQ')
            return { action: 'approved' }
          }
        },
        {
          model: 'qwen2.5-coder:7b',
          persistent: false,
          notify: true,
          notificationTitle: 'FSQ Quote Analysis',
          priority: this.llmState.PRIORITY.NORMAL,
          state: this.llmState.STATE.ANALYZING,
          metadata: {
            component: 'FSQ Modal',
            location: 'Quote Field',
            fieldName: 'quote',
            operation: 'split-analysis'
          }
        }
      )

      // Handle result
      if (result) {
        if (result.action === 'decoded' || result.action === 'normalized') {
          // User action required - will show accept/reject buttons
          return
        }
      }
    },

    generateSlugFromQuote(quoteText) {
      return quoteText
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-+|-+$/g, '')
        .substring(0, 50)
        || 'fsq-quote'
    },

    splitQuoteIntoSegments(quoteText, maxLength = 300) {
      if (quoteText.length <= maxLength) {
        return [quoteText]
      }

      const segments = []
      let currentSegment = ''

      const sentences = quoteText.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [quoteText]

      for (const sentence of sentences) {
        if ((currentSegment + sentence).length <= maxLength) {
          currentSegment += sentence
        } else {
          if (currentSegment) {
            segments.push(currentSegment.trim())
          }
          currentSegment = sentence
        }
      }

      if (currentSegment) {
        segments.push(currentSegment.trim())
      }

      return segments
    },

    async submit() {
      const isValid = await this.$refs.fsqFormRef.validate()
      console.log('Form validation result:', isValid)
      if (!isValid) {
        console.warn('Form validation failed')
        return
      }

      // Cancel any ongoing AI analysis - user has made their decision
      if (this.aiAnalyzing) {
        console.log('⏸️ User submitted during analysis - cancelling AI analysis')
        this.cancelAnalysis()
      }

      this.loading = true
      this.error = ''

      try {
        const currentEpisode = this.$route.params.episode || this.currentEpisode

        if (!currentEpisode) {
          throw new Error('No episode ID available')
        }

        const quoteSegments = this.splitRecommendations && this.splitRecommendations.length > 0
          ? this.splitRecommendations
          : [this.quote.trim()]

        console.log(`Creating ${quoteSegments.length} FSQ cue(s)`)

        if (this.includeAttribution && this.source && this.source.trim()) {
          this.lastSubmittedSource = this.source.trim()
        }

        for (let i = 0; i < quoteSegments.length; i++) {
          const segment = quoteSegments[i]
          const isMultipart = quoteSegments.length > 1

          const assetId = await this.generateAssetId()

          // Generate slug for this segment
          let slug
          if (isMultipart) {
            // For multi-part quotes, generate slug from first 3 words of this part
            const cleanedSegment = this.decodeQuoteText(segment)
            const words = cleanedSegment
              .trim()
              .split(/\s+/)
              .filter(word => word.length > 0)
              .slice(0, 3)

            const segmentSlug = words
              .join(' ')
              .toLowerCase()
              .replace(/[^a-z0-9\s-]/g, '')
              .replace(/\s+/g, '-')
              .replace(/-+/g, '-')
              .replace(/^-+|-+$/g, '')

            slug = `${i + 1}of${quoteSegments.length}-${segmentSlug}`
          } else {
            slug = this.slug
          }

          console.log(`Creating FSQ cue ${i + 1}/${quoteSegments.length} (media generation deferred)...`)

          const wordCount = segment.trim().split(/\s+/).filter(word => word.length > 0).length;
          const cleanQuote = this.decodeQuoteText(segment);

          // Calculate duration based on word count and speaker WPM
          const calculatedDuration = this.calculateDurationFromWPM(wordCount);

          const cueData = {
            type: 'FSQ',
            assetId: assetId,
            slug: slug,
            quote: cleanQuote,
            style: this.quoteStyle,
            fontFamily: this.fontFamily,
            fontSize: this.fontSize,
            renderMode: this.renderMode,
            duration: calculatedDuration,
            wordCount: wordCount,
            part: isMultipart ? `${i + 1}x${quoteSegments.length}` : '1x1'
          }

          if (this.includeAttribution && this.source && this.source.trim()) {
            cueData.source = this.source.trim()
          }

          console.log(`Creating FSQ cue ${i + 1} with asset:`, cueData)

          this.$emit('submit', cueData)

          // No delay between segments - user can place them consecutively
        }

        this.reset()
        this.$emit('update:show', false)

      } catch (error) {
        console.error('Error creating FSQ cue:', error)
        this.error = error.response?.data?.detail || 'Failed to create quote cue. Please try again.'
      } finally {
        this.loading = false
      }
    },

    handleEscapeKey(event) {
      if (event.key === 'Escape' && this.show) {
        this.cancel()
      }
    },

    cancel() {
      // Cancel any ongoing analysis
      this.cancelAnalysis()

      this.$emit('update:show', false)
      this.reset()
    },

    // Video preview handlers
    handleVideoLoaded() {
      console.log('✅ FSQ preview video loaded successfully')
      // Ensure video is playing
      if (this.$refs.previewVideoRef) {
        this.$refs.previewVideoRef.play().catch(err => {
          console.warn('⚠️ Video autoplay blocked:', err)
        })
      }
    },

    handleVideoError(event) {
      console.error('❌ FSQ preview video failed to load:', event)
      console.error('Video element:', this.$refs.previewVideoRef)
      console.error('Video src:', this.$refs.previewVideoRef?.src)
    },

    async generateAssetId() {
      try {
        console.log('Requesting AssetID for FSQ cue')

        const slug = this.quote.trim()
          .toLowerCase()
          .replace(/[^a-z0-9\s-]/g, '')
          .replace(/\s+/g, '-')
          .replace(/-+/g, '-')
          .replace(/^-+|-+$/g, '')
          .substring(0, 50)

        const formData = new FormData()
        formData.append('slug', slug || 'fsq-quote')
        formData.append('type', 'fsq')

        const response = await axios.post('/assetid/generate-legacy', formData, {
          headers: {
            'Accept': 'application/json',
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          }
        })

        if (response.data && response.data.id) {
          console.log('Successfully generated AssetID:', response.data.id)
          return response.data.id
        } else {
          throw new Error('Invalid response format: missing id field')
        }
      } catch (error) {
        console.warn('AssetID generation failed, using fallback:', error)
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        let result = 'LOCAL_FSQ_'
        for (let i = 0; i < 8; i++) {
          result += chars.charAt(Math.floor(Math.random() * chars.length))
        }
        console.log('Generated local fallback AssetID:', result)
        return result
      }
    },

    reset() {
      // Cancel any ongoing analysis
      this.cancelAnalysis()

      this.quote = ''
      this.slug = ''
      this.slugAutoGenerated = true  // Reset flag for next use
      this.source = ''
      this.sourceAutopopulated = false
      this.includeAttribution = true
      this.quoteStyle = 'left'
      this.fontFamily = 'sans-serif'
      this.fontSize = 25
      this.duration = '00:00:05:00'
      this.error = ''
      this.loading = false
      this.aiState = null
      this.splitRecommendations = null
      this.aiGenerationInfo = null
      this.aiActionPending = false
      this.aiPreviousQuote = ''
      // Reset manual split state
      this.manualSplitPoints = []
      this.manualSplitExpanded = false
      this.manualSplitQuoteStyle = 'left'
      this.manualSplitFontFamily = 'serif'
      this.manualSplitFontSize = 25

      this.$nextTick(() => {
        if (this.$refs.fsqFormRef) {
          this.$refs.fsqFormRef.resetValidation()
        }
      })
    },

    acceptAIChange() {
      console.log('✅ User accepted AI change')
      this.aiActionPending = false
      this.aiPreviousQuote = ''
      this.aiMessage = ''
      this.analyzeQuote()
    },

    rejectAIChange() {
      console.log('❌ User rejected AI change - reverting')
      this.quote = this.aiPreviousQuote
      this.aiPreviousQuote = ''
      this.aiActionPending = false
      this.aiState = null
      this.aiMessage = ''
    },

    async acceptAIRecommendation() {
      console.log('Accepting AI split recommendation and submitting...')
      await this.submit()
    },

    async rejectAIRecommendation() {
      this.splitRecommendations = null
      this.aiState = null
      this.aiGenerationInfo = null
      await this.submit()
    },

    async suggestDifferentSplit() {
      console.log('Requesting alternative split suggestion...')

      if (!this.quote || this.quote.length < 20) {
        console.warn('Quote too short for alternative split analysis')
        return
      }

      this.aiAnalyzing = true
      this.aiState = 'analyzing'

      try {
        const settingsResponse = await axios.get('/api/settings/', {
          headers: {
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          }
        })

        const settings = settingsResponse.data.generation || {}

        const splitConfig = {
          maxLines: settings.fsq_max_lines || 5,
          charsPerLine: settings.fsq_chars_per_line || 50,
          fontSize: settings.default_font_size || '19px',
          minSecondScreen: settings.fsq_min_second_screen || 80,
          splitStrategy: settings.fsq_split_strategy || 'smart',
          balanceThresholdPercent: settings.fsq_balance_threshold_percent || 30,
          preferSentenceBoundaries: settings.fsq_prefer_sentence_boundaries !== false,
          allowMidSentenceSplit: settings.fsq_allow_mid_sentence_split || false,
          overflowHandling: settings.fsq_overflow_handling || 'multi_segment',
          temperature: 0.5
        }

        const segments = await this.intelligentQuoteSplit(this.quote, splitConfig)

        console.log('Alternative AI quote analysis result:', segments)

        const now = new Date()
        this.aiGenerationInfo = {
          model: this.lastUsedModel?.model || 'qwen2.5-coder:7b',
          service: this.lastUsedModel?.service || 'ollama',
          timestamp: now.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
          })
        }

        if (segments.length > 1) {
          this.aiState = 'rejected'
          this.splitRecommendations = segments
          console.log('New split suggestion:', segments.length, 'segments')
        } else {
          this.aiState = 'approved'
          this.splitRecommendations = null
          setTimeout(() => {
            this.aiState = null
          }, 2000)
        }
      } catch (error) {
        console.error('Alternative split analysis failed:', error)
        this.aiState = 'rejected'
      } finally {
        this.aiAnalyzing = false
      }
    },

    // NEW METHODS FOR DUAL PREVIEW MODE

    /**
     * Format a split segment for preview display
     */
    formatSplitSegment(segment) {
      const decoded = this.decodeQuoteText(segment);
      const escaped = decoded
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>');

      // Apply same quote formatting rules as original
      if (this.regenerateExteriorQuotes) {
        return '"' + escaped + '"';
      }
      return escaped;
    },

    /**
     * Accept LLM split - use split preview controls
     */
    async acceptLLMSplit() {
      console.log('✅ Accepting LLM split with split preview controls');
      // Temporarily swap controls to use split settings
      const originalQuoteStyle = this.quoteStyle;
      const originalFontFamily = this.fontFamily;
      const originalFontSize = this.fontSize;

      this.quoteStyle = this.splitQuoteStyle;
      this.fontFamily = this.splitFontFamily;
      this.fontSize = this.splitFontSize;

      await this.acceptAIRecommendation();

      // Restore original (though modal will likely close)
      this.quoteStyle = originalQuoteStyle;
      this.fontFamily = originalFontFamily;
      this.fontSize = originalFontSize;
    },

    /**
     * Reject LLM split - use original preview controls
     */
    async rejectLLMSplit() {
      console.log('❌ Rejecting LLM split, inserting original with original controls');
      await this.rejectAIRecommendation();
    },

    /**
     * Mark manual split point
     */
    markManualSplit() {
      // Get cursor position in the quote text
      const selection = window.getSelection();
      if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const offset = range.startOffset;

        // Add split point if not already present
        if (!this.manualSplitPoints.includes(offset)) {
          this.manualSplitPoints.push(offset);
          this.manualSplitPoints.sort((a, b) => a - b);
          console.log('✂️ Manual split point added at position:', offset);
        }
      }
    },

    /**
     * Remove manual split point
     */
    removeManualSplit(index) {
      this.manualSplitPoints.splice(index, 1);
      console.log('🗑️ Manual split point removed');
    },

    /**
     * Apply manual split - create split recommendations from manual markers
     */
    applyManualSplit() {
      if (this.manualSplitPoints.length === 0) return;

      const segments = [];
      let lastIndex = 0;

      // Create segments from split points
      for (const splitPoint of this.manualSplitPoints) {
        const segment = this.quote.substring(lastIndex, splitPoint).trim();
        if (segment) {
          segments.push(segment);
        }
        lastIndex = splitPoint;
      }

      // Add final segment
      const finalSegment = this.quote.substring(lastIndex).trim();
      if (finalSegment) {
        segments.push(finalSegment);
      }

      // Apply manual segments as split recommendations
      this.splitRecommendations = segments;
      this.aiState = 'auto';  // Mark as user-generated
      this.aiGenerationInfo = {
        model: 'Manual Split',
        timestamp: new Date().toLocaleString('en-US')
      };

      console.log('✅ Manual split applied:', segments.length, 'parts');
    },

    /**
     * Insert manual split - use manual segments with manual split preview controls
     */
    async insertManualSplit() {
      console.log('✅ Inserting manual split with manual split preview controls');
      // Temporarily swap controls to use manual split settings
      const originalQuoteStyle = this.quoteStyle;
      const originalFontFamily = this.fontFamily;
      const originalFontSize = this.fontSize;

      this.quoteStyle = this.manualSplitQuoteStyle;
      this.fontFamily = this.manualSplitFontFamily;
      this.fontSize = this.manualSplitFontSize;

      // Set split recommendations to manual segments
      const tempSplitRecs = this.splitRecommendations;
      this.splitRecommendations = this.manualSplitSegments;

      await this.acceptAIRecommendation();

      // Restore original (though modal will likely close)
      this.quoteStyle = originalQuoteStyle;
      this.fontFamily = originalFontFamily;
      this.fontSize = originalFontSize;
      this.splitRecommendations = tempSplitRecs;
    }
  }
}
</script>

<style scoped>
/* Dual Preview Mode Layout */
.dual-preview-mode {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 24px;
}

/* LLM Recommended Split Section - Purple Dotted Border */
.split-preview-section {
  border: 4px dotted #9C27B0;
  border-radius: 8px;
  padding: 16px;
  background: rgba(156, 39, 176, 0.03);
}

.split-preview-section .section-title {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  color: #9C27B0;
}

/* Multi-part previews - stacked vertically */
.split-parts-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.split-part-preview {
  position: relative;
  width: 100%;
}

.part-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: #9C27B0;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}

/* 16:9 aspect ratio container with proper video display */
.split-container .quote-preview-container {
  margin-bottom: 0;
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #000;
}

.split-container .preview-video-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.split-container .black-bar-overlay {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  background: rgba(0, 0, 0, 0.75);
  z-index: 2;
  pointer-events: none;
}

.split-container .quote-preview {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  color: white;
  padding: 10% 10% 20% 10%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  z-index: 3;
  box-sizing: border-box;
}

.split-container .quote-text {
  max-width: 100%;
  word-wrap: break-word;
  color: white;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
}

.split-container .quote-source {
  margin-top: 20px;
  color: rgba(255,255,255,0.9);
  text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
}

/* Original Quote Section - Black Dotted Border */
.original-preview-section {
  border: 4px dotted #333;
  border-radius: 8px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
}

.original-preview-section .section-title {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  color: #333;
}

/* 16:9 aspect ratio for original preview too */
.original-preview-section .quote-preview-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #000;
}

.original-preview-section .preview-video-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.original-preview-section .black-bar-overlay {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  background: rgba(0, 0, 0, 0.75);
  z-index: 2;
  pointer-events: none;
}

.original-preview-section .quote-preview {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  color: white;
  padding: 10% 10% 20% 10%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  z-index: 3;
  box-sizing: border-box;
}

.original-preview-section .quote-text {
  max-width: 100%;
  word-wrap: break-word;
  color: white;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
}

.original-preview-section .quote-source {
  margin-top: 20px;
  color: rgba(255,255,255,0.9);
  text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
}

/* Manual Split Section - Blue Dotted Border */
.manual-split-section {
  border: 4px dotted #2196F3;
  border-radius: 8px;
  padding: 16px;
  background: rgba(33, 150, 243, 0.03);
}

.manual-split-section .section-title {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  color: #2196F3;
}

.manual-split-quote-display {
  background: white;
  border: 1px solid #E0E0E0;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Georgia', serif;
  font-size: 16px;
  line-height: 1.6;
  cursor: text;
  min-height: 100px;
  user-select: text;
}

.manual-split-quote-display:hover {
  background: #F5F5F5;
  border-color: #2196F3;
}

.manual-markers-display {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* Reject AI button - yellow with green hover */
.reject-ai-btn:hover {
  background-color: #4CAF50 !important;
  color: white !important;
}

/* Collapsible header */
.collapsible-header {
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
}

.collapsible-header:hover {
  background-color: rgba(33, 150, 243, 0.05);
}

/* No responsive changes needed - already vertical stacking */
</style>
