<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="720" persistent>
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
          <!-- ===== PREVIEW ON TOP (full-width, WYSIWYG) ===== -->
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
            <div class="black-bar-overlay" :style="blackBarStyle"></div>
            <div class="quote-preview" :style="previewStyle">
              <div class="quote-text" :style="quoteTextStyle" v-html="formattedQuotePreview"></div>
              <div v-if="includeAttribution && source" class="quote-source" :style="quoteSourceStyle">{{ attributionPrefix }}{{ source }}</div>
            </div>
          </div>

          <!-- Word count + AI status under the preview -->
          <div class="d-flex align-center mb-2" style="gap: 8px;">
            <v-chip v-if="quote && quote.length > 0" size="x-small" color="grey-darken-2">
              {{ quote.trim().split(/\s+/).filter(w => w.length > 0).length }} words
            </v-chip>
            <v-chip v-if="aiState" size="x-small" :color="aiStatusColor">
              <v-icon size="x-small" class="mr-1" :class="{ 'rotating': aiState === 'analyzing' }">{{ aiStatusIcon }}</v-icon>
              {{ aiStatusText }}
            </v-chip>
            <v-spacer></v-spacer>
            <v-btn
              v-if="splitRecommendations && splitRecommendations.length > 1"
              size="x-small"
              variant="tonal"
              color="warning"
              @click="showSplitPanel = !showSplitPanel"
            >
              <v-icon size="x-small" start>mdi-robot</v-icon>
              {{ showSplitPanel ? 'Hide' : 'Show' }} {{ splitRecommendations.length }} splits
            </v-btn>
          </div>

          <!-- ===== TABBED CONTROLS ===== -->
          <v-tabs
            v-model="activeTab"
            density="compact"
            color="primary"
            class="fsq-tabs mb-3"
            grow
          >
            <v-tab value="content"><v-icon size="small" start>mdi-format-quote-close</v-icon>Content</v-tab>
            <v-tab value="style"><v-icon size="small" start>mdi-palette</v-icon>Style</v-tab>
            <v-tab value="layout"><v-icon size="small" start>mdi-page-layout-body</v-icon>Layout</v-tab>
            <v-tab value="output"><v-icon size="small" start>mdi-export</v-icon>Output</v-tab>
          </v-tabs>

          <v-window v-model="activeTab" class="fsq-tab-window">
            <!-- ---------- CONTENT TAB ---------- -->
            <v-window-item value="content">
              <v-textarea
                ref="quoteFieldRef"
                v-model="quote"
                label="Quote"
                placeholder="Enter quote text..."
                variant="outlined"
                rows="4"
                auto-grow
                :rules="quoteRules"
                required
                density="compact"
                hide-details="auto"
                class="mb-3"
                @paste="handleQuotePaste"
                @input="handleQuoteInput"
                @click="updateCursorPosition"
                @keyup="updateCursorPosition"
              />

              <v-row dense class="mb-2" align="center">
                <v-col cols="9">
                  <v-combobox
                    v-model="source"
                    :items="sourceOptions"
                    label="Attribution / Source"
                    placeholder="Source name"
                    variant="outlined"
                    density="compact"
                    :disabled="!includeAttribution"
                    hide-details
                    clearable
                  />
                </v-col>
                <v-col cols="3" class="d-flex align-center justify-center">
                  <v-switch
                    v-model="includeAttribution"
                    density="compact"
                    hide-details
                    color="success"
                    inset
                  >
                    <template #label>
                      <span class="text-caption">{{ includeAttribution ? 'Show' : 'Hide' }}</span>
                    </template>
                  </v-switch>
                </v-col>
              </v-row>

              <v-text-field
                ref="slugFieldRef"
                v-model="slug"
                label="Slug"
                placeholder="short-slug"
                hint="Used for the filename — auto-generated from the quote"
                persistent-hint
                variant="outlined"
                :rules="slugRules"
                required
                density="compact"
                @input="handleSlugInput"
                @blur="normalizeSlug"
              />
            </v-window-item>

            <!-- ---------- STYLE TAB ---------- -->
            <v-window-item value="style">
              <v-row dense class="mb-3">
                <v-col cols="6">
                  <div class="fsq-field-caption">Font</div>
                  <v-select
                    v-model="fontFamily"
                    :items="fontOptions"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>
                <v-col cols="6">
                  <div class="fsq-field-caption">Alignment</div>
                  <v-btn-toggle v-model="quoteStyle" mandatory density="compact" color="primary" class="w-100 fsq-align-toggle">
                    <v-btn value="left" class="flex-grow-1"><v-icon size="small">mdi-format-align-left</v-icon></v-btn>
                    <v-btn value="center" class="flex-grow-1"><v-icon size="small">mdi-format-align-center</v-icon></v-btn>
                    <v-btn value="right" class="flex-grow-1"><v-icon size="small">mdi-format-align-right</v-icon></v-btn>
                  </v-btn-toggle>
                </v-col>
              </v-row>

              <!-- Quote size -->
              <div class="fsq-slider-row">
                <span class="fsq-slider-label">Quote size</span>
                <v-slider v-model="fontSizePx" :min="60" :max="300" :step="2" density="compact" hide-details thumb-label class="fsq-slider" />
                <v-text-field v-model.number="fontSizePx" type="number" suffix="px" density="compact" variant="outlined" hide-details class="fsq-slider-num" />
              </div>

              <!-- Attribution size -->
              <div class="fsq-slider-row">
                <span class="fsq-slider-label">Attrib size</span>
                <v-slider v-model="attributionSizePx" :min="32" :max="240" :step="2" density="compact" hide-details thumb-label class="fsq-slider" :disabled="!includeAttribution" />
                <v-text-field v-model.number="attributionSizePx" type="number" suffix="px" density="compact" variant="outlined" hide-details class="fsq-slider-num" :disabled="!includeAttribution" />
              </div>
            </v-window-item>

            <!-- ---------- LAYOUT TAB ---------- -->
            <v-window-item value="layout">
              <!-- Black box height -->
              <div class="fsq-slider-row">
                <span class="fsq-slider-label">Box height</span>
                <v-slider v-model="boxHeight" :min="0" :max="100" :step="1" density="compact" hide-details thumb-label class="fsq-slider" />
                <v-text-field v-model.number="boxHeight" type="number" suffix="%" density="compact" variant="outlined" hide-details class="fsq-slider-num" />
              </div>
              <!-- Box opacity -->
              <div class="fsq-slider-row">
                <span class="fsq-slider-label">Opacity</span>
                <v-slider v-model="boxOpacity" :min="0" :max="100" :step="1" density="compact" hide-details thumb-label class="fsq-slider" />
                <v-text-field v-model.number="boxOpacity" type="number" suffix="%" density="compact" variant="outlined" hide-details class="fsq-slider-num" />
              </div>
              <!-- Line spacing -->
              <div class="fsq-slider-row">
                <span class="fsq-slider-label">Line space</span>
                <v-slider v-model="lineSpacing" :min="1" :max="100" :step="1" density="compact" hide-details thumb-label class="fsq-slider" />
                <v-text-field v-model.number="lineSpacing" type="number" suffix="%" density="compact" variant="outlined" hide-details class="fsq-slider-num" />
              </div>
            </v-window-item>

            <!-- ---------- OUTPUT TAB ---------- -->
            <v-window-item value="output">
              <div class="fsq-field-caption">Split mode</div>
              <v-btn-toggle v-model="splitMode" mandatory density="compact" color="purple" class="w-100 mb-3">
                <v-btn value="ai" size="small" class="flex-grow-1"><v-icon left size="small">mdi-robot</v-icon>AI</v-btn>
                <v-btn value="manual" size="small" class="flex-grow-1"><v-icon left size="small">mdi-cursor-text</v-icon>Manual</v-btn>
                <v-btn value="none" size="small" class="flex-grow-1"><v-icon left size="small">mdi-file-document</v-icon>Full</v-btn>
              </v-btn-toggle>

              <!-- Manual Split Panel -->
              <v-expand-transition>
                <v-card v-if="splitMode === 'manual'" class="manual-split-panel mb-3" variant="outlined">
                  <v-card-title class="text-caption py-2 bg-purple-lighten-5 d-flex align-center">
                    <v-icon size="small" class="mr-1">mdi-scissors-cutting</v-icon>
                    Manual Split Mode
                  </v-card-title>
                  <v-card-text class="pa-2">
                    <v-alert type="info" variant="tonal" density="compact" class="mb-2 text-caption">
                      Click in the Quote (Content tab) where you want to split, then "Add Split"
                    </v-alert>
                    <div class="d-flex gap-1 mb-2">
                      <v-btn color="purple" variant="outlined" size="x-small" @click="markManualSplit" :disabled="!cursorPosition || !quote">
                        <v-icon left size="x-small">mdi-plus</v-icon>Add Split
                      </v-btn>
                      <v-btn color="grey" variant="outlined" size="x-small" @click="clearManualSplits" :disabled="manualSplitPoints.length === 0">
                        <v-icon left size="x-small">mdi-delete-sweep</v-icon>Clear All
                      </v-btn>
                      <v-spacer></v-spacer>
                      <v-chip size="x-small" color="purple" variant="outlined">{{ manualSplitPoints.length }} split(s)</v-chip>
                    </div>
                    <div v-if="manualSplitPoints.length > 0" class="manual-split-preview mt-2">
                      <v-divider class="mb-2"></v-divider>
                      <div class="text-caption text-grey mb-2">MANUAL SPLITS PREVIEW ({{ manualSplitSegments.length }} parts)</div>
                      <div class="split-parts-grid">
                        <div v-for="(segment, index) in manualSplitSegments" :key="`manual-split-${index}`" class="split-part-preview">
                          <div class="part-label">{{ index + 1 }}/{{ manualSplitSegments.length }}</div>
                          <div class="quote-preview-container split-container">
                            <video class="preview-video-background" autoplay loop muted playsinline>
                              <source :src="previewBackgroundVideo" type="video/mp4">
                            </video>
                            <div class="black-bar-overlay" :style="blackBarStyle"></div>
                            <div class="quote-preview" :style="getSplitPreviewStyle">
                              <div class="quote-text" :style="getSplitTextStyle" v-html="formatSplitSegment(segment)"></div>
                              <div v-if="includeAttribution" class="quote-source" :style="getSplitSourceStyle">{{ attributionPrefix }}{{ source || 'Source' }}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-expand-transition>

              <div class="fsq-field-caption">Render as</div>
              <v-btn-toggle v-model="renderMode" mandatory density="compact" color="lime" class="w-100">
                <v-btn value="png" size="small" class="flex-grow-1"><v-icon size="small" class="mr-1">mdi-file-image</v-icon>PNG</v-btn>
                <v-btn value="video" size="small" class="flex-grow-1"><v-icon size="small" class="mr-1">mdi-video</v-icon>Video</v-btn>
              </v-btn-toggle>
            </v-window-item>
          </v-window>

          <!-- ===== PRIMARY ACTION (always visible, below tabs) ===== -->
          <div class="action-buttons mt-4">
            <template v-if="splitMode === 'manual'">
              <v-btn block color="purple" @click="insertManualSplit" :disabled="!formValid || !quote || manualSplitPoints.length === 0" :loading="loading" variant="elevated" size="large">
                <v-icon size="small" class="mr-1">mdi-scissors-cutting</v-icon>
                {{ editMode ? 'Save' : 'Insert' }} {{ manualSplitSegments.length }} Split(s)
              </v-btn>
            </template>
            <template v-else-if="splitMode === 'ai'">
              <v-btn block color="primary" @click="rejectAIRecommendation" :disabled="!formValid || !quote" :loading="loading" variant="elevated" size="large">
                <v-icon size="small" class="mr-1">{{ editMode ? 'mdi-content-save' : 'mdi-plus' }}</v-icon>
                {{ editMode ? 'Save FSQ' : (splitRecommendations && splitRecommendations.length > 1 ? 'Insert Full Quote' : 'Insert Quote') }}
              </v-btn>
              <v-btn v-if="splitRecommendations && splitRecommendations.length > 1" block color="deep-purple" @click="acceptAIRecommendation" :disabled="!formValid" :loading="loading" variant="elevated" size="default" class="mt-2">
                <v-icon size="small" class="mr-1">mdi-robot</v-icon>
                Insert {{ splitRecommendations.length }} Splits
              </v-btn>
            </template>
            <template v-else>
              <v-btn block color="primary" @click="rejectAIRecommendation" :disabled="!formValid || !quote" :loading="loading" variant="elevated" size="large">
                <v-icon size="small" class="mr-1">{{ editMode ? 'mdi-content-save' : 'mdi-plus' }}</v-icon>
                {{ editMode ? 'Save FSQ' : 'Insert Full Quote' }}
              </v-btn>
            </template>
          </div>

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
                    <div class="black-bar-overlay" :style="blackBarStyle"></div>
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
        <v-btn
          v-if="editMode && pngUrl"
          size="small"
          variant="tonal"
          color="deep-purple"
          @click="showPngPreview = true"
        >
          <v-icon size="small" start>mdi-eye</v-icon>
          View PNG
        </v-btn>
        <span class="text-caption text-grey ml-2">Live preview updates as you edit · Style &amp; Layout tabs hold all parameters</span>
      </v-card-actions>
    </v-card>

    <!-- PNG Preview Modal -->
    <v-dialog v-model="showPngPreview" max-width="960">
      <v-card class="fsq-png-preview-card">
        <v-card-title class="d-flex align-center pa-2 bg-grey-darken-4">
          <v-icon class="mr-2" color="white">mdi-format-quote-close</v-icon>
          <span class="text-white">FSQ Preview</span>
          <v-spacer></v-spacer>
          <v-chip size="small" color="info" class="mr-2">960×540</v-chip>
          <v-btn icon size="small" variant="text" color="white" @click="showPngPreview = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-0">
          <div class="fsq-png-preview-container">
            <video class="fsq-png-preview-video" autoplay loop muted playsinline>
              <source :src="previewBackgroundVideo" type="video/mp4">
            </video>
            <img :src="pngUrl" class="fsq-png-preview-overlay" />
          </div>
        </v-card-text>
        <v-card-actions class="bg-grey-darken-4 pa-2">
          <v-chip size="small" color="grey-darken-2">{{ slug || 'No slug' }}</v-chip>
          <v-spacer></v-spacer>
          <span class="text-caption text-grey-lighten-1">Press ESC to close</span>
        </v-card-actions>
      </v-card>
    </v-dialog>
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
  /* WYSIWYG sizing: descendant `cqh` units resolve against this box. */
  container-type: size;
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

/* Tabbed controls */
.fsq-tabs {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.fsq-tab-window {
  min-height: 170px;   /* keep modal height stable across tabs */
  padding-top: 14px;
}
/* Tighten the compact-modal default vertical rhythm so floating-label fields
   don't crowd the field below them. */
.compact-fsq-modal :deep(.v-input) {
  margin-bottom: 0;
}

/* Slider + editable-number rows (Style / Layout tabs) */
.fsq-slider-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}
.fsq-slider-label {
  flex: 0 0 72px;
  font-size: 11px;
  color: rgba(0, 0, 0, 0.65);
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.3px;
  line-height: 1.1;
}
.fsq-slider {
  flex: 1 1 auto;
  min-width: 0;
}
/* Compact number box: tight width, right-aligned, small suffix so the
   value + unit never wrap or collide with the slider's thumb bubble. */
.fsq-slider-num {
  flex: 0 0 78px;
}
.fsq-slider-num :deep(input) {
  text-align: right;
  font-size: 12px;
  padding-right: 2px;
}
.fsq-slider-num :deep(.v-text-field__suffix) {
  font-size: 11px;
  opacity: 0.7;
  padding-left: 2px;
  min-width: 0;
}
.fsq-slider-num :deep(.v-field__input) {
  padding-top: 0;
  padding-bottom: 0;
}

/* Small caption above a control (Font, Alignment, Split mode, Render as) —
   replaces floating labels in tight rows so heights line up and nothing
   overlaps. */
.fsq-field-caption {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.65);
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.3px;
  margin-bottom: 4px;
  line-height: 1.1;
}
/* Match the alignment toggle's height to the compact select beside it. */
.fsq-align-toggle.v-btn-toggle {
  height: 40px;
}
.fsq-align-toggle :deep(.v-btn) {
  height: 40px;
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
  font-size: 0.8rem;
}

/* NOTE: the previous translateY(-1em)/(-1.7em) overrides on floating labels
   were removed — they were hacks for the old two-column layout and pushed
   labels out of their fields, causing the overlap. Vuetify positions the
   floating label correctly on its own at density="compact". */

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
  /* WYSIWYG sizing: descendant `cqh` units resolve against this box. */
  container-type: size;
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

/* PNG Preview Modal */
.fsq-png-preview-card {
  border-radius: 0 !important;
  overflow: hidden;
}

.fsq-png-preview-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #000;
}

.fsq-png-preview-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

.fsq-png-preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  z-index: 2;
}
</style>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick, getCurrentInstance } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useLLM } from '@/composables/useLLM'
import { useLLMState } from '@/composables/useLLMState'
import { useAsyncAnalysis } from '@/composables/useAsyncAnalysis'
import { getColorValue } from '@/utils/themeColorMap'
import { FSQ_DEFAULTS, FSQ_FONT_MAP, FSQ_PNG_SCALE, fsqPreviewCanvasHeightUnit, computeLineHeight, computeBlackBarStyle } from '@/utils/fsqLayout'
import { registerModalEsc } from '@/composables/useModalStack'
import { useDoubleEnterToSlug } from '@/composables/useDoubleEnterToSlug'

// ---- Props & Emits ----
const props = defineProps({
  show: { type: Boolean, required: true },
  currentEpisode: { type: String, default: '' },
  speakerWpm: { type: Number, default: 150 },
  editMode: { type: Boolean, default: false },
  initialData: { type: Object, default: null }
})

const emit = defineEmits(['update:show', 'submit'])

// ---- Composables ----
const route = useRoute()
const { intelligentQuoteSplit, normalizeNestedQuotes, lastUsedModel } = useLLM()
const llmState = useLLMState()
const $toast = getCurrentInstance()?.appContext.config.globalProperties.$toast

// ---- Template Refs ----
const fsqFormRef = ref(null)
const quoteFieldRef = ref(null)
const previewVideoRef = ref(null)
const slugFieldRef = ref(null)

// ---- Reactive State (data) ----
const formValid = ref(false)
const loading = ref(false)
const error = ref('')
const quote = ref('')
const slug = ref('')
const slugAutoGenerated = ref(true)
const source = ref('')
const sourceOptions = ref([])
const includeAttribution = ref(true)
const quoteStyle = ref(FSQ_DEFAULTS.alignment)
const fontFamily = ref(FSQ_DEFAULTS.fontFamily)
const fontSize = ref(FSQ_DEFAULTS.fontSize)
// Display the size input in REAL canvas-pixel units while keeping `fontSize`
// in the legacy 1/4-scale that the storage and downstream code expect.
const fontSizePx = computed({
  get: () => Math.round(fontSize.value * FSQ_PNG_SCALE),
  set: (px) => { fontSize.value = Math.max(1, Math.round(px / FSQ_PNG_SCALE)); }
})
// Attribution size: legacy 1/4-scale ref + real-px bridge (mirrors the card).
const attributionSize = ref(FSQ_DEFAULTS.attributionSize)
const attributionSizePx = computed({
  get: () => Math.round(attributionSize.value * FSQ_PNG_SCALE),
  set: (px) => { attributionSize.value = Math.max(1, Math.round(px / FSQ_PNG_SCALE)); }
})
// Layout params — same units/ranges the per-cue card sliders use.
const boxHeight = ref(FSQ_DEFAULTS.boxHeight)       // % of canvas height
const boxOpacity = ref(FSQ_DEFAULTS.boxOpacity)     // % opacity
const lineSpacing = ref(FSQ_DEFAULTS.lineSpacing)   // % of font size
// Which control tab is showing (Content / Style / Layout / Output).
const activeTab = ref('content')
const renderMode = ref('png')
const duration = ref('00:00:05:00')
// Original AssetID when editing an existing cue. Preserves the on-disk
// media identity across edits so updating cue metadata does not orphan
// the rendered PNG / job records bound to the original AssetID.
const initialAssetId = ref(null)
const lastSubmittedSource = ref('')
const sourceAutopopulated = ref(false)
let analyzeTimeout = null
const aiActionPending = ref(false)
const aiPreviousQuote = ref('')
const splitRecommendations = ref(null)
const aiGenerationInfo = ref(null)
const aiRecommendationExpanded = ref([])
const previewBackgroundVideo = ref('/assets/preview-background.mp4')
// Quote formatting settings
const stripExteriorQuotes = ref(true)
const regenerateExteriorQuotes = ref(false)
const normalizeInteriorQuotes = ref(true)
const attributionDashStyle = ref('regular')
// Split preview controls
const splitQuoteStyle = ref('left')
const splitFontFamily = ref('serif')
const splitFontSize = ref(25)
// Split mode control
const splitMode = ref('ai')
const cursorPosition = ref(null)
// Manual split markers
const manualSplitPoints = ref([])
const manualSplitExpanded = ref(false) // eslint-disable-line no-unused-vars
// Manual split preview controls
const manualSplitQuoteStyle = ref('left')
const manualSplitFontFamily = ref('serif')
const manualSplitFontSize = ref(25)
// UI state
const showSplitPanel = ref(false)
const showPngPreview = ref(false)

// ---- aiFieldMixin inlined state ----
const aiAnalysisState = ref({}) // eslint-disable-line no-unused-vars
const aiRecommendations = ref({}) // eslint-disable-line no-unused-vars
const aiAnalysisIds = ref({}) // eslint-disable-line no-unused-vars
let aiDebounceTimers = {}
const aiAnalyzing = ref(false)
const aiAnalysisComplete = ref(false) // eslint-disable-line no-unused-vars

// AI state / message (used directly, not from mixin)
const aiState = ref(null)
const aiMessage = ref('')

// ---- Computed (from aiFieldMixin) ----
const hasActiveAnalysis = computed(() => { // eslint-disable-line no-unused-vars
  return Object.values(aiAnalysisState.value).some(state => state === 'analyzing')
})

const hasReviewPending = computed(() => { // eslint-disable-line no-unused-vars
  return Object.values(aiAnalysisState.value).some(state => state === 'needs_review')
})

const getFieldBorderStyle = computed(() => { // eslint-disable-line no-unused-vars
  return (fieldName) => {
    const state = aiAnalysisState.value[fieldName]
    if (state === 'analyzing') {
      return { border: '7px solid #9C27B0', borderRadius: '4px' }
    } else if (state === 'needs_review') {
      return { border: '7px solid #D32F2F', borderRadius: '4px' }
    }
    return {}
  }
})

// ---- Computed ----
const cueTypeColor = computed(() => {
  return getColorValue('fsq')
})

const pngUrl = computed(() => {
  const data = props.initialData?.rawData || props.initialData
  if (!data?.mediaUrl) return ''
  if (data.mediaUrl.startsWith('http') || data.mediaUrl.startsWith('/')) {
    return data.mediaUrl
  }
  const episode = route?.params?.episode || props.currentEpisode || ''
  return `/episodes/${episode}/assets/quotes/${data.mediaUrl}`
})

const aiStatusColor = computed(() => {
  switch (aiState.value) {
    case 'analyzing': return 'purple'
    case 'rejected': return 'error'
    case 'approved': return 'success'
    case 'auto': return 'info'
    default: return 'grey'
  }
})

const aiStatusIcon = computed(() => {
  switch (aiState.value) {
    case 'analyzing': return 'mdi-brain'
    case 'rejected': return 'mdi-alert-circle'
    case 'approved': return 'mdi-check-circle'
    case 'auto': return 'mdi-robot'
    default: return 'mdi-help-circle'
  }
})

const aiStatusText = computed(() => {
  switch (aiState.value) {
    case 'analyzing': return 'Analyzing...'
    case 'rejected': return 'Review needed'
    case 'approved': return 'Approved'
    case 'auto': return 'Auto-processed'
    default: return ''
  }
})

const quoteFieldClass = computed(() => { // eslint-disable-line no-unused-vars
  return llmState.getVisualClass('field', 'fsq-quote-field')
})

const quoteFieldStyle = computed(() => { // eslint-disable-line no-unused-vars
  return llmState.getVisualStyle('field', 'fsq-quote-field')
})

const isLLMActive = computed(() => { // eslint-disable-line no-unused-vars
  return llmState.isTargetActive('field', 'fsq-quote-field')
})

const currentLLMOperation = computed(() => { // eslint-disable-line no-unused-vars
  const ops = llmState.getOperationsForTarget('field', 'fsq-quote-field')
  return ops.length > 0 ? ops[ops.length - 1] : null
})

const quoteRules = computed(() => {
  return [
    v => !!v || 'Quote text is required',
    v => !v || v.length >= 10 || 'Quote must be at least 10 characters'
  ]
})

const slugRules = computed(() => {
  return [
    v => !!v || 'Slug is required'
  ]
})

const sourceRules = computed(() => { // eslint-disable-line no-unused-vars
  return [
    v => !!v || 'Source/attribution is required',
    v => !v || v.length <= 100 || 'Source must be 100 characters or less'
  ]
})

const styleOptions = computed(() => { // eslint-disable-line no-unused-vars
  return [
    { title: 'Centered', value: 'center' },
    { title: 'Left Aligned', value: 'left' },
    { title: 'Right Aligned', value: 'right' },
    { title: 'Large Text', value: 'large' },
    { title: 'Elegant', value: 'elegant' }
  ]
})

const durationOptions = computed(() => { // eslint-disable-line no-unused-vars
  return [
    { title: '3 seconds', value: '00:00:03:00' },
    { title: '5 seconds', value: '00:00:05:00' },
    { title: '7 seconds', value: '00:00:07:00' },
    { title: '10 seconds', value: '00:00:10:00' },
    { title: '15 seconds', value: '00:00:15:00' },
    { title: 'Custom', value: 'custom' }
  ]
})

const fontOptions = computed(() => {
  return [
    { title: 'Sans Serif (Helvetica)', value: 'sans-serif' },
    { title: 'Serif (Georgia)', value: 'serif' },
    { title: 'Monospace (Courier)', value: 'monospace' }
  ]
})

const previewStyle = computed(() => {
  return {
    alignItems: quoteStyle.value === 'center' ? 'center' :
               quoteStyle.value === 'left' ? 'flex-start' :
               quoteStyle.value === 'right' ? 'flex-end' : 'center'
  }
})

const quoteTextStyle = computed(() => {
  // Sized as a fraction of preview-container height that matches what the
  // PNG renderer produces on a 1080px canvas — true WYSIWYG.
  return {
    fontFamily: FSQ_FONT_MAP[fontFamily.value] || FSQ_FONT_MAP['sans-serif'],
    fontSize: fsqPreviewCanvasHeightUnit(fontSize.value),
    lineHeight: computeLineHeight(lineSpacing.value),
    textAlign: quoteStyle.value || FSQ_DEFAULTS.alignment
  }
})

const quoteSourceStyle = computed(() => {
  // Use the explicit attribution size if set; otherwise fall back to the
  // renderer's auto rule (quote × attributionRatio) so the preview matches
  // the generated PNG.
  const effectiveAttrib = attributionSize.value
    || (fontSize.value || FSQ_DEFAULTS.fontSize) * FSQ_DEFAULTS.attributionRatio
  return {
    fontFamily: FSQ_FONT_MAP[fontFamily.value] || FSQ_FONT_MAP['sans-serif'],
    fontSize: fsqPreviewCanvasHeightUnit(effectiveAttrib),
    textAlign: quoteStyle.value || FSQ_DEFAULTS.alignment
  }
})

// Live black-bar overlay driven by the Layout params (height + opacity), so
// the preview reflects those sliders just like the rendered PNG will.
const blackBarStyle = computed(() => computeBlackBarStyle(boxHeight.value, boxOpacity.value))

const formattedQuotePreview = computed(() => {
  let rawText = quote.value || 'Quote text will appear here...'
  // Mirror host_script_generator._format_fsq: only strip stored exterior
  // quotes when regenerating, to avoid doubled marks. Otherwise render
  // verbatim regardless of the strip-on-input setting.
  if (regenerateExteriorQuotes.value) {
    rawText = rawText.trim().replace(/^"+|"+$/g, '')
  }
  const escaped = rawText
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')

  if (regenerateExteriorQuotes.value) {
    return '\u201C' + escaped + '\u201D'
  }
  return escaped
})

const attributionPrefix = computed(() => {
  const dashMap = {
    'regular': '\u2014 ',
    'emdash': '\u2014',
    'none': ''
  }
  return dashMap[attributionDashStyle.value] || '\u2014 '
})

// Split previews mirror the live style controls so each split part looks
// exactly like the main preview (same font, size, alignment, spacing).
const getSplitPreviewStyle = computed(() => previewStyle.value)
const getSplitTextStyle = computed(() => quoteTextStyle.value)
const getSplitSourceStyle = computed(() => quoteSourceStyle.value)

const getManualSplitPreviewStyle = computed(() => { // eslint-disable-line no-unused-vars
  return {
    alignItems: manualSplitQuoteStyle.value === 'center' ? 'center' :
               manualSplitQuoteStyle.value === 'left' ? 'flex-start' :
               manualSplitQuoteStyle.value === 'right' ? 'flex-end' : 'center'
  }
})

const getManualSplitTextStyle = computed(() => { // eslint-disable-line no-unused-vars
  const fontMap = {
    'sans-serif': 'Helvetica, Arial, sans-serif',
    'serif': 'Georgia, "Times New Roman", serif',
    'monospace': '"Courier New", Courier, monospace'
  }
  return {
    fontFamily: fontMap[manualSplitFontFamily.value] || fontMap['sans-serif'],
    fontSize: fsqPreviewCanvasHeightUnit(manualSplitFontSize.value),
    textAlign: manualSplitQuoteStyle.value === 'center' ? 'center' :
              manualSplitQuoteStyle.value === 'left' ? 'left' :
              manualSplitQuoteStyle.value === 'right' ? 'right' : 'center'
  }
})

const getManualSplitSourceStyle = computed(() => { // eslint-disable-line no-unused-vars
  const fontMap = {
    'sans-serif': 'Helvetica, Arial, sans-serif',
    'serif': 'Georgia, "Times New Roman", serif',
    'monospace': '"Courier New", Courier, monospace'
  }
  const derivedAttrib = (manualSplitFontSize.value || FSQ_DEFAULTS.fontSize) * FSQ_DEFAULTS.attributionRatio
  return {
    fontFamily: fontMap[manualSplitFontFamily.value] || fontMap['sans-serif'],
    fontSize: fsqPreviewCanvasHeightUnit(derivedAttrib),
    textAlign: manualSplitQuoteStyle.value === 'center' ? 'center' :
              manualSplitQuoteStyle.value === 'left' ? 'left' :
              manualSplitQuoteStyle.value === 'right' ? 'right' : 'center'
  }
})

const manualSplitSegments = computed(() => {
  if (!quote.value || manualSplitPoints.value.length === 0) {
    return [quote.value]
  }

  const segments = []
  let lastIndex = 0

  const sortedPoints = [...manualSplitPoints.value].sort((a, b) => a - b)

  for (const splitPoint of sortedPoints) {
    const segment = quote.value.substring(lastIndex, splitPoint).trim()
    if (segment) segments.push(segment)
    lastIndex = splitPoint
  }

  const finalSegment = quote.value.substring(lastIndex).trim()
  if (finalSegment) segments.push(finalSegment)

  return segments
})

// ---- aiFieldMixin inlined methods ----
function triggerAnalysis(fieldName, fieldValue, config, debounceMs = 2000) { // eslint-disable-line no-unused-vars
  if (aiDebounceTimers[fieldName]) {
    clearTimeout(aiDebounceTimers[fieldName])
  }
  if (aiAnalysisIds.value[fieldName]) {
    const { cancel } = useAsyncAnalysis()
    cancel(aiAnalysisIds.value[fieldName])
    delete aiAnalysisIds.value[fieldName]
  }
  aiAnalysisState.value[fieldName] = null
  aiRecommendations.value[fieldName] = null
  aiDebounceTimers[fieldName] = setTimeout(async () => {
    await startAnalysis(fieldName, fieldValue, config)
  }, debounceMs)
  console.log(`\u23F1\uFE0F Analysis debounce started for ${fieldName} (${debounceMs}ms)`)
}

async function startAnalysis(fieldName, fieldValue, config) { // eslint-disable-line no-unused-vars
  const { analyzeField } = useAsyncAnalysis()
  aiAnalysisState.value[fieldName] = 'analyzing'
  aiAnalyzing.value = true
  console.log(`\uD83D\uDD0D Starting analysis for field: ${fieldName}`)
  try {
    const analysisId = await analyzeField({
      cueType: config.cueType,
      fieldName: fieldName,
      fieldValue: fieldValue,
      assetId: config.assetId || undefined,
      analysisType: config.analysisType,
      analysisParams: config.analysisParams || {},
      analyzerFunction: config.analyzerFunction || null
    })
    aiAnalysisIds.value[fieldName] = analysisId
    pollAnalysisState(fieldName, analysisId)
  } catch (err) { // eslint-disable-line no-unused-vars
    console.error(`\u274C Analysis failed for ${fieldName}:`, err)
    aiAnalysisState.value[fieldName] = 'error'
    aiAnalyzing.value = false
  }
}

function pollAnalysisState(fieldName, analysisId) { // eslint-disable-line no-unused-vars
  const asyncAnalysis = useAsyncAnalysis()
  const checkState = () => {
    const state = asyncAnalysis.getState(analysisId)
    if (!state || state === 'analyzing') {
      setTimeout(checkState, 500)
      return
    }
    aiAnalysisState.value[fieldName] = state
    aiAnalyzing.value = false
    aiAnalysisComplete.value = true
    if (state === 'needs_review') {
      const recommendations = asyncAnalysis.getRecommendations(analysisId)
      aiRecommendations.value[fieldName] = recommendations
      console.log(`\u2705 Analysis complete for ${fieldName}: needs review`)
      console.log(`   Recommendations:`, recommendations)
      if (fieldName === 'quote' && recommendations?.splitRecommendations) {
        aiRecommendationExpanded.value = recommendations.splitRecommendations
      }
    } else if (state === 'complete') {
      console.log(`\u2705 Analysis complete for ${fieldName}: no action needed`)
    } else if (state === 'error') {
      console.error(`\u274C Analysis error for ${fieldName}`)
    }
  }
  checkState()
}

function cancelFieldAnalysis(fieldName) { // eslint-disable-line no-unused-vars
  if (aiDebounceTimers[fieldName]) {
    clearTimeout(aiDebounceTimers[fieldName])
    delete aiDebounceTimers[fieldName]
  }
  if (aiAnalysisIds.value[fieldName]) {
    const { cancel } = useAsyncAnalysis()
    cancel(aiAnalysisIds.value[fieldName])
    delete aiAnalysisIds.value[fieldName]
  }
  aiAnalysisState.value[fieldName] = null
  aiRecommendations.value[fieldName] = null
  aiAnalyzing.value = hasActiveAnalysis.value
  console.log(`\u23F8\uFE0F Cancelled analysis for ${fieldName}`)
}

function cancelAllAnalyses() { // eslint-disable-line no-unused-vars
  Object.keys(aiAnalysisState.value).forEach(fieldName => {
    cancelFieldAnalysis(fieldName)
  })
  aiAnalyzing.value = false
  aiAnalysisComplete.value = false
  aiRecommendationExpanded.value = []
  console.log(`\u23F8\uFE0F Cancelled all analyses`)
}

function resetAnalysisState() { // eslint-disable-line no-unused-vars
  aiAnalysisState.value = {}
  aiRecommendations.value = {}
  aiAnalysisIds.value = {}
  aiDebounceTimers = {}
  aiAnalyzing.value = false
  aiAnalysisComplete.value = false
  aiRecommendationExpanded.value = []
  console.log(`\uD83D\uDD04 Reset analysis state`)
}

function getAnalysisClass(fieldName) { // eslint-disable-line no-unused-vars
  const state = aiAnalysisState.value[fieldName]
  if (state === 'analyzing') return 'ai-analyzing'
  if (state === 'needs_review') return 'ai-needs-review'
  if (state === 'complete') return 'ai-complete'
  if (state === 'error') return 'ai-error'
  return ''
}

// ---- Methods ----

function loadInitialData() {
  if (!props.initialData) return

  const data = props.initialData.rawData || props.initialData

  initialAssetId.value = data.assetId || props.initialData.assetId || null

  quote.value = data.quote || ''
  source.value = data.attribution || ''
  slug.value = data.slug || ''
  slugAutoGenerated.value = false

  const styleValue = data.quoteStyle || data.alignment || data.style
  if (styleValue) {
    quoteStyle.value = styleValue === 'centered' ? 'center' : styleValue
  }
  if (data.fontFamily) fontFamily.value = data.fontFamily
  if (data.fontSize) fontSize.value = parseInt(data.fontSize) || FSQ_DEFAULTS.fontSize
  if (data.attributionSize) attributionSize.value = parseInt(data.attributionSize) || FSQ_DEFAULTS.attributionSize
  if (data.boxHeight !== undefined && data.boxHeight !== '') boxHeight.value = parseInt(data.boxHeight)
  if (data.boxOpacity !== undefined && data.boxOpacity !== '') boxOpacity.value = parseInt(data.boxOpacity)
  if (data.lineSpacing !== undefined && data.lineSpacing !== '') lineSpacing.value = parseInt(data.lineSpacing)
  if (data.renderMode) renderMode.value = data.renderMode
  if (data.duration) duration.value = data.duration
  // Edit mode shows the full quote as-is \u2014 don't let AI re-split on open.
  splitMode.value = 'none'

  console.log('\u2705 Loaded FSQ data for editing:', { quote: quote.value, source: source.value, slug: slug.value, style: quoteStyle.value })
}

async function loadDefaultSettings() {
  try {
    const token = localStorage.getItem('auth-token')
    const response = await axios.get('/api/settings/', {
      headers: token ? {
        'Authorization': `Bearer ${token}`
      } : {}
    })

    const settings = response.data.generation || {}
    console.log('\uD83D\uDCE5 Loaded FSQ default settings:', settings)

    if (settings.fsq_default_alignment) {
      quoteStyle.value = settings.fsq_default_alignment === 'centered' ? 'center' : settings.fsq_default_alignment
    }
    if (settings.fsq_default_font) {
      fontFamily.value = settings.fsq_default_font
    }
    if (settings.fsq_default_font_size) {
      fontSize.value = settings.fsq_default_font_size
    }
    if (settings.fsq_include_attribution_by_default !== undefined) {
      includeAttribution.value = settings.fsq_include_attribution_by_default
    }
    if (settings.fsq_background_video) {
      previewBackgroundVideo.value = settings.fsq_background_video
    }
    if (settings.fsq_strip_exterior_quotes !== undefined) {
      stripExteriorQuotes.value = settings.fsq_strip_exterior_quotes
    }
    if (settings.fsq_regenerate_exterior_quotes !== undefined) {
      regenerateExteriorQuotes.value = settings.fsq_regenerate_exterior_quotes
    }
    if (settings.fsq_normalize_interior_quotes !== undefined) {
      normalizeInteriorQuotes.value = settings.fsq_normalize_interior_quotes
    }
    if (settings.fsq_attribution_dash_style) {
      attributionDashStyle.value = settings.fsq_attribution_dash_style
    }

    console.log('\u2705 FSQ defaults applied:', {
      alignment: quoteStyle.value,
      font: fontFamily.value,
      fontSize: fontSize.value,
      includeAttribution: includeAttribution.value,
      previewVideo: previewBackgroundVideo.value,
      stripExteriorQuotes: stripExteriorQuotes.value,
      regenerateExteriorQuotes: regenerateExteriorQuotes.value,
      normalizeInteriorQuotes: normalizeInteriorQuotes.value,
      attributionDashStyle: attributionDashStyle.value
    })

  } catch (err) { // eslint-disable-line no-unused-vars
    console.error('Failed to load FSQ default settings:', err)
  }
}

async function fetchEpisodeSources() {
  if (!props.currentEpisode) {
    console.log('\u26A0\uFE0F No current episode specified for source lookup')
    return
  }

  try {
    const token = localStorage.getItem('auth-token')
    const response = await axios.get(`/api/episodes/${props.currentEpisode}/rundown`, {
      headers: token ? {
        'Authorization': `Bearer ${token}`
      } : {}
    })

    let rundownItems = response.data
    if (rundownItems && !Array.isArray(rundownItems)) {
      rundownItems = rundownItems.rundown || rundownItems.items || []
    }
    if (!Array.isArray(rundownItems)) {
      console.warn('\u26A0\uFE0F Unexpected response format, expected array:', rundownItems)
      rundownItems = []
    }

    const sources = []

    rundownItems.forEach(item => {
      if (item.script) {
        const attributionMatches = item.script.matchAll(/\[Attribution:\s*([^\]]+)\]/g)
        for (const match of attributionMatches) {
          const src = match[1].trim()
          if (src && !sources.includes(src)) {
            sources.push(src)
          }
        }
      }
    })

    sourceOptions.value = sources.reverse()
    console.log(`\uD83D\uDCCB Loaded ${sources.length} unique FSQ sources from episode ${props.currentEpisode}`)

  } catch (err) { // eslint-disable-line no-unused-vars
    console.error('\u274C Failed to fetch episode sources:', err)
    sourceOptions.value = []
  }
}

function normalizeSlug() {
  if (!slug.value) return

  slug.value = slug.value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 50)
}

function calculateDurationFromWPM(wordCount) {
  const wpm = props.speakerWpm || 150
  const durationInSeconds = Math.ceil((wordCount / wpm) * 60)

  const hours = Math.floor(durationInSeconds / 3600)
  const minutes = Math.floor((durationInSeconds % 3600) / 60)
  const seconds = durationInSeconds % 60

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:00`
}

function hasNestedQuotes(text) {
  if (!text) return false

  let decoded = decodeQuoteText(text)

  const doubleQuotes = (decoded.match(/"/g) || []).length
  const singleQuotes = (decoded.match(/'/g) || []).length
  const apostrophes = (decoded.match(/[a-z]'|'[a-z]/gi) || []).length
  const actualSingleQuotes = singleQuotes - apostrophes

  const hasInternalDoubleQuotes = doubleQuotes > 0
  const hasMixedQuotes = doubleQuotes > 0 && actualSingleQuotes > 0
  const hasMultipleDoubles = doubleQuotes > 2
  const hasMultipleSingles = actualSingleQuotes > 2

  const hasNesting = hasInternalDoubleQuotes || hasMixedQuotes || hasMultipleDoubles || hasMultipleSingles

  if (hasNesting) {
    console.log('\uD83D\uDD0D Nested quotes detected:', {
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
}

function decodeQuoteText(text) {
  // Entity/escape decode only. Exterior-quote stripping is a paste-time
  // concern and lives in stripExteriorQuotesIfEnabled() \u2014 DO NOT add it
  // back here. Calling this from save paths must not mutate exterior
  // quote marks; the stored quote should round-trip verbatim so the host
  // script generator can honor regenerateExteriorQuotes correctly.
  if (!text) return text

  return text
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
}

function stripExteriorQuotesIfEnabled(text) {
  if (!text || !stripExteriorQuotes.value) return text
  let decoded = text.trim()
  if ((decoded.startsWith('"') && decoded.endsWith('"')) ||
      (decoded.startsWith("'") && decoded.endsWith("'"))) {
    decoded = decoded.slice(1, -1).trim()
    console.log('\uD83D\uDD13 Stripped exterior quotes per settings')
  }
  return decoded
}

// ESC handled by global modal stack
registerModalEsc(() => props.show, () => cancel(), 'FsqModal')
useDoubleEnterToSlug(() => props.show, slugFieldRef)

async function handleQuotePaste() {
  console.log('\uD83D\uDCCB Paste detected, waiting for v-model update...')
  await nextTick()
  await new Promise(resolve => setTimeout(resolve, 50))
  console.log('\uD83D\uDCCB Quote pasted (length: ' + quote.value.length + ')')

  // Apply strip-exterior-quotes setting at paste time only. The stored
  // quote should otherwise round-trip verbatim through save/load so the
  // host-script render setting (regenerate exterior quotes) is the single
  // source of truth for what ships in the final script.
  const stripped = stripExteriorQuotesIfEnabled(quote.value)
  if (stripped !== quote.value) {
    quote.value = stripped
  }

  cancelAnalysis()

  if (aiActionPending.value) {
    console.log('\uD83D\uDD04 Clearing pending AI action - user pasted new content')
    aiActionPending.value = false
    aiPreviousQuote.value = ''
  }

  aiState.value = null
  aiMessage.value = ''
  splitRecommendations.value = null
  aiGenerationInfo.value = null

  autoExtractAttribution()

  clearTimeout(analyzeTimeout)
  analyzeTimeout = setTimeout(() => {
    if (quote.value && quote.value.length > 20) {
      console.log('\uD83E\uDD16 Starting AI analysis after paste (2s delay)...')
      analyzeQuote()
    }
  }, 2000)
}

function handleQuoteInput() {
  if (aiState.value === 'analyzing') {
    console.log('\u23F8\uFE0F User started typing - cancelling ongoing analysis')
    cancelAnalysis()
  }

  const significantChange = Math.abs(quote.value.length - (aiPreviousQuote.value?.length || 0)) > 50

  if (aiActionPending.value && significantChange) {
    console.log('\uD83D\uDD04 Significant text change detected - resetting AI state')
    aiActionPending.value = false
    aiPreviousQuote.value = ''
    aiState.value = null
    aiMessage.value = ''
    splitRecommendations.value = null
    aiGenerationInfo.value = null
  }

  autoExtractAttribution()
  autoGenerateSlug()
}

function handleSlugInput() {
  slugAutoGenerated.value = false
}

function autoGenerateSlug() {
  if (slugAutoGenerated.value && quote.value && quote.value.trim()) {
    const cleanedQuote = decodeQuoteText(quote.value)
    const words = cleanedQuote
      .trim()
      .split(/\s+/)
      .filter(word => word.length > 0)
      .slice(0, 3)

    if (words.length > 0) {
      slug.value = words
        .join(' ')
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-+|-+$/g, '')
    }
  }

  if (aiState.value && aiState.value !== 'analyzing' && !aiActionPending.value) {
    aiState.value = null
    aiMessage.value = ''
    splitRecommendations.value = null
    aiGenerationInfo.value = null
  }

  if (aiActionPending.value) {
    return
  }

  clearTimeout(analyzeTimeout)
  analyzeTimeout = setTimeout(() => {
    if (quote.value.length > 20) {
      console.log('\uD83E\uDD16 Triggering AI quote analysis after typing pause (2s)...')
      analyzeQuote()
    }
  }, 2000)
}

function autoExtractAttribution() {
  if (!quote.value || quote.value.trim().length === 0) return

  const text = quote.value.trim()

  const patterns = [
    /^([""\u201C]?.+?[""\u201D]?)\s*\n\s*[\u2014\-\u2013]\s*(.+)$/s,
    /^([""\u201C].+?[""\u201D])\s*\n\s*([A-Z].+)$/s,
    /^([""\u201C]?.+?[""\u201D]?)\s*[\u2014\-\u2013]\s*(.+)$/,
    /^(.+?[""\u201D])\s*[\u2014\-\u2013]\s*(.+)$/
  ]

  for (const pattern of patterns) {
    const match = text.match(pattern)
    if (match) {
      const potentialQuote = match[1].trim()
      const potentialAttribution = match[2].trim()

      const isValidAttribution = (
        potentialAttribution.length > 2 &&
        potentialAttribution.length < 100 &&
        potentialQuote.length > 10 &&
        potentialQuote.length > potentialAttribution.length &&
        potentialAttribution.match(/^[\u2014\-\u2013]?[A-Z]/) &&
        potentialQuote.replace(/[""\u201C\u201D\s]/g, '').length > 5
      )

      if (isValidAttribution) {
        console.log('\u2702\uFE0F Auto-detected attribution:', {
          quote: potentialQuote,
          attribution: potentialAttribution,
          pattern: pattern.source.substring(0, 50) + '...'
        })

        let cleanQuote = potentialQuote
          .replace(/^[""\u201C]/, '')
          .replace(/[""\u201D]$/, '')
          .trim()

        let cleanAttribution = potentialAttribution
          .replace(/^[\u2014\-\u2013]\s*/, '')
          .trim()

        quote.value = cleanQuote
        source.value = cleanAttribution
        includeAttribution.value = true
        sourceAutopopulated.value = false
        console.log('\u2705 Attribution auto-extracted (overriding existing):', {
          extractedQuote: cleanQuote.substring(0, 50) + '...',
          extractedAttribution: cleanAttribution
        })
        return
      }
    }
  }
}

function cancelAnalysis() {
  clearTimeout(analyzeTimeout)

  const ops = llmState.getOperationsForTarget('field', 'fsq-quote-field')
  ops.forEach(op => {
    llmState.stopOperation(op.id, {
      notify: false,
      message: 'Analysis cancelled by user'
    })
  })
}

async function analyzeQuote() {
  if (splitMode.value === 'manual') {
    console.log('\u23ED\uFE0F Manual split mode - skipping AI analysis')
    return
  }

  if (splitMode.value === 'none') {
    console.log('\u23ED\uFE0F No split mode - skipping AI analysis')
    return
  }

  if (!quote.value || quote.value.length < 20) {
    console.log('\u23ED\uFE0F Quote too short for AI analysis (< 20 chars)')
    return
  }

  const result = await llmState.withLLM(
    'field',
    'fsq-quote-field',
    'analyzing',
    async () => {
      let workingQuote = decodeQuoteText(quote.value)
      if (workingQuote !== quote.value) {
        console.log('\uD83D\uDD13 Auto-stripping surrounding quotes:', { before: quote.value, after: workingQuote })
        quote.value = workingQuote
      }

      if (normalizeInteriorQuotes.value && hasNestedQuotes(workingQuote)) {
        console.log('\uD83D\uDCDD Nested quotes detected, normalizing...')
        const normalized = await normalizeNestedQuotes(workingQuote)

        if (normalized !== quote.value) {
          console.log('\u2728 Auto-normalizing nested quotes:', { before: quote.value, after: normalized })
          quote.value = normalized
          workingQuote = normalized
        }
      } else if (!normalizeInteriorQuotes.value) {
        console.log('\u23ED\uFE0F Skipping nested quote normalization (disabled in settings)')
      }

      console.log('\uD83D\uDCE5 Loading generation settings from backend...')
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

      console.log('\uD83E\uDDE0 Calling intelligentQuoteSplit() with smart split logic...')
      const segments = await intelligentQuoteSplit(workingQuote, splitConfig)

      const now = new Date()
      aiGenerationInfo.value = {
        model: lastUsedModel?.model || 'qwen2.5-coder:7b',
        service: lastUsedModel?.service || 'ollama',
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
        splitRecommendations.value = segments
        aiRecommendationExpanded.value = []
        console.log(`\u2702\uFE0F AI recommends splitting into ${segments.length} segments`)
        return { action: 'split', segments, count: segments.length }
      } else {
        splitRecommendations.value = null
        aiRecommendationExpanded.value = []
        console.log('\u2705 AI approved - quote fits as single FSQ')
        return { action: 'approved' }
      }
    },
    {
      model: 'qwen2.5-coder:7b',
      persistent: false,
      notify: true,
      notificationTitle: 'FSQ Quote Analysis',
      priority: llmState.PRIORITY.NORMAL,
      state: llmState.STATE.ANALYZING,
      metadata: {
        component: 'FSQ Modal',
        location: 'Quote Field',
        fieldName: 'quote',
        operation: 'split-analysis'
      }
    }
  )

  if (result) {
    if (result.action === 'decoded' || result.action === 'normalized') {
      return
    }
  }
}

function generateSlugFromQuote(quoteText) { // eslint-disable-line no-unused-vars
  return quoteText
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 50)
    || 'fsq-quote'
}

function splitQuoteIntoSegments(quoteText, maxLength = 300) { // eslint-disable-line no-unused-vars
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
}

async function submit() {
  const isValid = await fsqFormRef.value.validate()
  console.log('Form validation result:', isValid)
  if (!isValid) {
    console.warn('Form validation failed')
    return
  }

  if (aiAnalyzing.value) {
    console.log('\u23F8\uFE0F User submitted during analysis - cancelling AI analysis')
    cancelAnalysis()
  }

  loading.value = true
  error.value = ''

  try {
    const currentEpisode = route.params.episode || props.currentEpisode

    if (!currentEpisode) {
      throw new Error('No episode ID available')
    }

    const quoteSegments = splitRecommendations.value && splitRecommendations.value.length > 0
      ? splitRecommendations.value
      : [quote.value.trim()]

    console.log(`Creating ${quoteSegments.length} FSQ cue(s)`)

    if (includeAttribution.value && source.value && source.value.trim()) {
      lastSubmittedSource.value = source.value.trim()
    }

    for (let i = 0; i < quoteSegments.length; i++) {
      const segment = quoteSegments[i]
      const isMultipart = quoteSegments.length > 1

      // In edit mode, reuse the original AssetID for the first (or only) segment
      // so existing rendered media + job records stay bound. Additional split
      // segments still mint new AssetIDs since they are genuinely new cues.
      const assetId = (props.editMode && initialAssetId.value && i === 0)
        ? initialAssetId.value
        : await generateAssetId()

      let segSlug
      if (isMultipart) {
        const cleanedSegment = decodeQuoteText(segment)
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

        segSlug = `${i + 1}of${quoteSegments.length}-${segmentSlug}`
      } else {
        segSlug = slug.value
      }

      console.log(`Creating FSQ cue ${i + 1}/${quoteSegments.length} (media generation deferred)...`)

      const wordCount = segment.trim().split(/\s+/).filter(word => word.length > 0).length
      const cleanQuote = decodeQuoteText(segment)

      const calculatedDuration = calculateDurationFromWPM(wordCount)

      const cueData = {
        type: 'FSQ',
        assetId: assetId,
        slug: segSlug,
        quote: cleanQuote,
        alignment: quoteStyle.value,
        style: quoteStyle.value,  // backward compat for existing cue parsing
        fontFamily: fontFamily.value,
        fontSize: fontSize.value,
        attributionSize: attributionSize.value,
        boxHeight: boxHeight.value,
        boxOpacity: boxOpacity.value,
        lineSpacing: lineSpacing.value,
        renderMode: renderMode.value,
        duration: calculatedDuration,
        wordCount: wordCount,
        part: isMultipart ? `${i + 1}x${quoteSegments.length}` : '1x1'
      }

      if (includeAttribution.value && source.value && source.value.trim()) {
        cueData.source = source.value.trim()
        cueData.attribution = source.value.trim()  // canonical name
      }

      console.log(`Creating FSQ cue ${i + 1} with asset:`, cueData)

      emit('submit', cueData)
    }

    reset()
    emit('update:show', false)

  } catch (err) { // eslint-disable-line no-unused-vars
    console.error('Error creating FSQ cue:', err)
    error.value = err.response?.data?.detail || 'Failed to create quote cue. Please try again.'
  } finally {
    loading.value = false
  }
}

function cancel() {
  cancelAnalysis()

  emit('update:show', false)
  reset()
}

function handleVideoLoaded() {
  console.log('\u2705 FSQ preview video loaded successfully')
  if (previewVideoRef.value) {
    previewVideoRef.value.play().catch(err => {
      console.warn('\u26A0\uFE0F Video autoplay blocked:', err)
    })
  }
}

function handleVideoError(event) {
  console.error('\u274C FSQ preview video failed to load:', event)
  console.error('Video element:', previewVideoRef.value)
  console.error('Video src:', previewVideoRef.value?.src)
}

async function generateAssetId() {
  try {
    console.log('Requesting AssetID for FSQ cue')

    const slugStr = quote.value.trim()
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 50)

    const formData = new FormData()
    formData.append('slug', slugStr || 'fsq-quote')
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
  } catch (err) { // eslint-disable-line no-unused-vars
    console.warn('AssetID generation failed, using fallback:', err)
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    let result = 'LOCAL_FSQ_'
    for (let i = 0; i < 8; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    console.log('Generated local fallback AssetID:', result)
    return result
  }
}

function reset() {
  cancelAnalysis()

  initialAssetId.value = null
  quote.value = ''
  slug.value = ''
  slugAutoGenerated.value = true
  source.value = ''
  sourceAutopopulated.value = false
  includeAttribution.value = true
  quoteStyle.value = FSQ_DEFAULTS.alignment
  fontFamily.value = FSQ_DEFAULTS.fontFamily
  fontSize.value = FSQ_DEFAULTS.fontSize
  attributionSize.value = FSQ_DEFAULTS.attributionSize
  boxHeight.value = FSQ_DEFAULTS.boxHeight
  boxOpacity.value = FSQ_DEFAULTS.boxOpacity
  lineSpacing.value = FSQ_DEFAULTS.lineSpacing
  activeTab.value = 'content'
  duration.value = '00:00:05:00'
  error.value = ''
  loading.value = false
  aiState.value = null
  splitRecommendations.value = null
  aiGenerationInfo.value = null
  aiActionPending.value = false
  aiPreviousQuote.value = ''
  manualSplitPoints.value = []
  manualSplitExpanded.value = false
  manualSplitQuoteStyle.value = 'left'
  manualSplitFontFamily.value = 'serif'
  manualSplitFontSize.value = 25

  nextTick(() => {
    if (fsqFormRef.value) {
      fsqFormRef.value.resetValidation()
    }
  })
}

function acceptAIChange() { // eslint-disable-line no-unused-vars
  console.log('\u2705 User accepted AI change')
  aiActionPending.value = false
  aiPreviousQuote.value = ''
  aiMessage.value = ''
  analyzeQuote()
}

function rejectAIChange() { // eslint-disable-line no-unused-vars
  console.log('\u274C User rejected AI change - reverting')
  quote.value = aiPreviousQuote.value
  aiPreviousQuote.value = ''
  aiActionPending.value = false
  aiState.value = null
  aiMessage.value = ''
}

async function acceptAIRecommendation() {
  console.log('Accepting AI split recommendation and submitting...')
  await submit()
}

async function rejectAIRecommendation() {
  splitRecommendations.value = null
  aiState.value = null
  aiGenerationInfo.value = null
  await submit()
}

async function suggestDifferentSplit() { // eslint-disable-line no-unused-vars
  console.log('Requesting alternative split suggestion...')

  if (!quote.value || quote.value.length < 20) {
    console.warn('Quote too short for alternative split analysis')
    return
  }

  aiAnalyzing.value = true
  aiState.value = 'analyzing'

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

    const segments = await intelligentQuoteSplit(quote.value, splitConfig)

    console.log('Alternative AI quote analysis result:', segments)

    const now = new Date()
    aiGenerationInfo.value = {
      model: lastUsedModel?.model || 'qwen2.5-coder:7b',
      service: lastUsedModel?.service || 'ollama',
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
      aiState.value = 'rejected'
      splitRecommendations.value = segments
      console.log('New split suggestion:', segments.length, 'segments')
    } else {
      aiState.value = 'approved'
      splitRecommendations.value = null
      setTimeout(() => {
        aiState.value = null
      }, 2000)
    }
  } catch (err) { // eslint-disable-line no-unused-vars
    console.error('Alternative split analysis failed:', err)
    aiState.value = 'rejected'
  } finally {
    aiAnalyzing.value = false
  }
}

function formatSplitSegment(segment) {
  const decoded = decodeQuoteText(segment)
  const escaped = decoded
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')

  if (regenerateExteriorQuotes.value) {
    return '\u201C' + escaped + '\u201D'
  }
  return escaped
}

async function acceptLLMSplit() { // eslint-disable-line no-unused-vars
  console.log('\u2705 Accepting LLM split with split preview controls')
  const originalQuoteStyle = quoteStyle.value
  const originalFontFamily = fontFamily.value
  const originalFontSize = fontSize.value

  quoteStyle.value = splitQuoteStyle.value
  fontFamily.value = splitFontFamily.value
  fontSize.value = splitFontSize.value

  await acceptAIRecommendation()

  quoteStyle.value = originalQuoteStyle
  fontFamily.value = originalFontFamily
  fontSize.value = originalFontSize
}

async function rejectLLMSplit() { // eslint-disable-line no-unused-vars
  console.log('\u274C Rejecting LLM split, inserting original with original controls')
  await rejectAIRecommendation()
}

function updateCursorPosition(event) {
  if (event && event.target) {
    cursorPosition.value = event.target.selectionStart
  }
}

function clearManualSplits() {
  manualSplitPoints.value = []
  console.log('\uD83D\uDDD1\uFE0F All manual split points cleared')
}

function markManualSplit() {
  if (!cursorPosition.value && cursorPosition.value !== 0) {
    $toast?.warning('Click in the quote text to place cursor')
    return
  }

  const exists = manualSplitPoints.value.some(
    pos => Math.abs(pos - cursorPosition.value) < 5
  )

  if (exists) {
    $toast?.warning('Split marker already exists near this position')
    return
  }

  manualSplitPoints.value.push(cursorPosition.value)
  manualSplitPoints.value.sort((a, b) => a - b)

  $toast?.success(`Split added at position ${cursorPosition.value}`)
  console.log('\u2702\uFE0F Manual split points:', manualSplitPoints.value)
}

function removeManualSplit(index) { // eslint-disable-line no-unused-vars
  manualSplitPoints.value.splice(index, 1)
  console.log('\uD83D\uDDD1\uFE0F Manual split point removed')
}

function applyManualSplit() { // eslint-disable-line no-unused-vars
  if (manualSplitPoints.value.length === 0) return

  const segments = []
  let lastIndex = 0

  for (const splitPoint of manualSplitPoints.value) {
    const segment = quote.value.substring(lastIndex, splitPoint).trim()
    if (segment) {
      segments.push(segment)
    }
    lastIndex = splitPoint
  }

  const finalSegment = quote.value.substring(lastIndex).trim()
  if (finalSegment) {
    segments.push(finalSegment)
  }

  splitRecommendations.value = segments
  aiState.value = 'auto'
  aiGenerationInfo.value = {
    model: 'Manual Split',
    timestamp: new Date().toLocaleString('en-US')
  }

  console.log('\u2705 Manual split applied:', segments.length, 'parts')
}

async function insertManualSplit() {
  console.log('\u2705 Inserting manual split using the live style controls')
  // Use the style the user actually set (Style/Layout tabs) \u2014 no override.
  const tempSplitRecs = splitRecommendations.value
  splitRecommendations.value = manualSplitSegments.value

  await acceptAIRecommendation()

  splitRecommendations.value = tempSplitRecs
}

// ---- Watchers ----
watch(() => props.show, async (newVal) => {
  if (newVal) {
    await fetchEpisodeSources()

    if (props.editMode && props.initialData) {
      console.log('\uD83D\uDCDD Loading FSQ for editing:', props.initialData)
      loadInitialData()
    } else if (!source.value) {
      if (lastSubmittedSource.value) {
        source.value = lastSubmittedSource.value
        sourceAutopopulated.value = true
      } else if (sourceOptions.value.length > 0) {
        source.value = sourceOptions.value[0]
        sourceAutopopulated.value = true
      }
    }

    nextTick(() => {
      if (quoteFieldRef.value) {
        quoteFieldRef.value.focus()
      }

      if (previewVideoRef.value) {
        previewVideoRef.value.load()
        previewVideoRef.value.play().catch(err => {
          console.warn('\u26A0\uFE0F Video autoplay prevented:', err)
        })
      }
    })
  }
})

watch(source, (newVal) => {
  if (sourceAutopopulated.value && newVal !== lastSubmittedSource.value) {
    sourceAutopopulated.value = false
  }
})

// ---- Lifecycle ----
onMounted(async () => {
  await loadDefaultSettings()
})

onBeforeUnmount(() => {
  // ESC listener auto-cleaned by registerModalEsc.
  // Clean up aiFieldMixin debounce timers
  Object.values(aiDebounceTimers).forEach(timer => {
    clearTimeout(timer)
  })
  console.log('\uD83E\uDDF9 aiFieldMixin: Component unmounting, analyses will continue in background')
})
</script>

<style scoped>
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

/* Manual Split Mode Styling */
.manual-split-panel {
  background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
}

.manual-split-panel .v-card-title {
  font-weight: 500;
  font-size: 0.875rem;
}
</style>
