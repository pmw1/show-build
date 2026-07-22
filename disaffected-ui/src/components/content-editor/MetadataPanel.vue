<template>
  <div
    ref="metadataRootRef"
    :class="['metadata-panel', panelWidth === 'narrow' ? 'narrow' : 'wide']"
    :style="{ width: panelWidthValue, height: panelHeightValue }"
  >
    <!-- Tab-shaped control buttons on left edge -->
    <div class="tab-controls-left">
      <v-btn
        icon
        size="small"
        @click="$emit('toggle-width')"
        class="tab-btn"
      >
        <v-icon>{{ panelWidth === 'narrow' ? 'mdi-arrow-expand-horizontal' : 'mdi-arrow-collapse-horizontal' }}</v-icon>
      </v-btn>
      <v-btn
        icon
        size="small"
        @click="$emit('close')"
        class="tab-btn"
      >
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </div>

    <v-card class="metadata-card" flat>
      <!-- ═══════════════════════════════════════════════
           ZONE A — Always Visible (top, flex-shrink: 0)
           ═══════════════════════════════════════════════ -->
      <div class="zone-a">
        <!-- No Item Selected State (when no item, show placeholder) -->
        <div v-if="!item" class="text-center py-4 px-2">
          <v-icon size="36" color="grey-lighten-1" class="mb-1">mdi-information-outline</v-icon>
          <p class="text-body-2 text-grey-lighten-1">No Item Selected</p>
          <p class="text-caption text-grey">Select a rundown item to view metadata</p>
        </div>
      </div>

      <!-- Save/Sync Status Header -->
      <v-btn
        block
        variant="flat"
        density="compact"
        rounded="0"
        class="save-header-btn"
        :style="saveState.hasChanges ? { backgroundColor: '#1976D2', color: '#ffffff', height: '48px', maxHeight: '48px' } : { backgroundColor: '#4CAF50', color: '#ffffff', height: '48px', maxHeight: '48px' }"
        @click="$emit('save-all')"
      >
        <v-icon left size="small">{{ saveState.buttonIcon || 'mdi-check-circle' }}</v-icon>
        {{ saveState.buttonText || 'Synchronized' }}
      </v-btn>

      <!-- Status Bar (black normally, red throbbing if needs-attention) -->
      <div :class="['sidebar-status-bar', { 'needs-attention-throb': currentItemNeedsAttention }]"></div>

      <!-- ═══════════════════════════════════════════════
           SEGMENT INFO — Always Visible (own block)
           ═══════════════════════════════════════════════ -->
      <div v-if="item" class="segment-info-block">
        <div class="segment-info-header" :style="blockHeaderStyle">
          <v-icon size="small" class="mr-1">mdi-information-outline</v-icon>
          <span class="segment-info-title">Segment Info</span>
        </div>
        <div class="segment-info-body">
          <div v-if="item.asset_id || item.id" class="asset-id-row mb-1">
            <span class="asset-id-label">ID:</span>
            <span class="asset-id-value">{{ item.asset_id || item.id }}</span>
            <v-icon size="10" class="asset-id-copy" @click="copyToClipboard(item.asset_id || item.id)">mdi-content-copy</v-icon>
            <span class="duration-inline" :title="durationPlaceholder">
              <v-icon size="10" class="duration-inline-icon">mdi-timer-outline</v-icon>
              {{ item.duration || '00:00:00' }}
            </span>
          </div>
          <v-text-field :placeholder="slugPlaceholder" :model-value="item.slug || ''" @update:model-value="$emit('update-segment-field', { field: 'slug', value: $event })" variant="underlined" density="compact" hide-details class="sidebar-field mb-1" :color="segmentTypeColor">
            <template v-slot:append-inner>
              <v-btn
                icon
                size="x-small"
                variant="text"
                color="purple"
                :loading="generatingSlug"
                :disabled="generatingSlug"
                @click="generateSlug"
                title="Generate a short broadcast slug from the title + script with AI"
              >
                <v-icon size="small">mdi-auto-fix</v-icon>
              </v-btn>
            </template>
          </v-text-field>
          <v-text-field :placeholder="titlePlaceholder" :model-value="item.title || ''" @update:model-value="$emit('update-segment-field', { field: 'title', value: $event })" variant="underlined" density="compact" hide-details class="sidebar-field mb-1" :color="segmentTypeColor" />
          <div class="description-wrapper">
                      <textarea
                        ref="descriptionTextareaRef"
                        :placeholder="descriptionPlaceholder"
                        :value="item.description || ''"
                        @input="resizeDescriptionTextarea(); $emit('update-segment-field', { field: 'description', value: $event.target.value })"
                        class="sidebar-description-raw"
                        :disabled="regenerating"
                      ></textarea>
                      <!-- Regenerating overlay -->
                      <div v-if="regenerating" class="regen-overlay">
                        <v-progress-circular indeterminate size="24" width="2" color="white" />
                        <span class="regen-overlay-text">Regenerating...</span>
                      </div>
                    </div>
                    <!-- Description action buttons (below textarea, right-aligned) -->
                    <div v-if="!regenerating" class="desc-actions-row">
                      <span v-if="item.description_model" class="desc-model-label">{{ item.description_model }}</span>
                      <v-btn
                        size="x-small"
                        variant="flat"
                        class="desc-action-btn"
                        :class="{ 'auto-desc-on': item.auto_description_enabled !== false, 'auto-desc-off': item.auto_description_enabled === false }"
                        @click="$emit('update-segment-field', { field: 'auto_description_enabled', value: !(item.auto_description_enabled !== false) })"
                      >
                        <v-icon size="10" class="mr-half">{{ item.auto_description_enabled !== false ? 'mdi-lightning-bolt' : 'mdi-lightning-bolt-outline' }}</v-icon>
                        <span>Auto</span>
                        <v-tooltip activator="parent" location="top">{{ item.auto_description_enabled !== false ? 'Auto-description ON — sweeper will fill empty descriptions' : 'Auto-description OFF — sweeper will skip this segment' }}</v-tooltip>
                      </v-btn>
                      <v-btn
                        v-if="item.description"
                        size="x-small"
                        variant="flat"
                        class="desc-action-btn regen-color"
                        @click="showRegenModal = true"
                      >
                        <v-icon size="10" class="mr-half">mdi-refresh</v-icon>
                        <span>Regen</span>
                        <v-tooltip activator="parent" location="top">Regenerate description</v-tooltip>
                      </v-btn>
                      <v-btn
                        v-if="item.description"
                        size="x-small"
                        variant="flat"
                        class="desc-action-btn auto-desc-off"
                        @click="$emit('update-segment-field', { field: 'description', value: '' }); $emit('update-segment-field', { field: 'description_model', value: '' })"
                      >
                        <v-icon size="10" class="mr-half">mdi-close</v-icon>
                        <span>Clear</span>
                        <v-tooltip activator="parent" location="top">Clear description (sweeper will regenerate if Auto is on)</v-tooltip>
                      </v-btn>
                    </div>

                    <!-- Regenerate Description Modal -->
                    <v-dialog v-model="showRegenModal" max-width="480" @keydown.esc="showRegenModal = false">
                      <v-card>
                        <v-card-title class="d-flex align-center">
                          <v-icon color="purple" class="mr-2">mdi-refresh</v-icon>
                          Regenerate Description
                          <v-spacer />
                          <v-btn icon="mdi-close" variant="text" size="small" @click="showRegenModal = false" />
                        </v-card-title>
                        <v-divider />
                        <v-card-text class="pa-4">
                          <p class="text-body-2 mb-3">
                            The current description will be sent to the LLM along with your feedback so it knows what to change.
                          </p>
                          <div class="text-caption text-grey mb-1">Current description:</div>
                          <div class="current-desc-preview pa-2 mb-3 rounded">{{ item.description }}</div>
                          <v-textarea
                            v-model="regenFeedback"
                            label="What would you like different?"
                            placeholder="e.g. Make it shorter, less dramatic, focus on the guest's perspective..."
                            variant="outlined"
                            density="compact"
                            rows="3"
                            auto-grow
                            autofocus
                            hide-details
                          />
                        </v-card-text>
                        <v-divider />
                        <v-card-actions class="pa-3">
                          <v-spacer />
                          <v-btn variant="text" @click="showRegenModal = false">Cancel</v-btn>
                          <v-btn
                            color="purple"
                            variant="flat"
                            prepend-icon="mdi-refresh"
                            @click="regenerateDescription"
                          >
                            Regenerate
                          </v-btn>
                        </v-card-actions>
                      </v-card>
                    </v-dialog>

                    <!-- Tone badges + inline add button -->
                    <div class="tone-field mb-1 sidebar-field">
                      <span class="tone-label text-caption text-grey-darken-1">Tone</span>
                      <div class="tone-badges d-flex flex-wrap ga-1">
                        <v-chip
                          v-for="(t, ti) in parsedTones"
                          :key="t + ti"
                          closable
                          size="x-small"
                          :color="isToneLlmGenerated ? llmTextColor : '#1976D2'"
                          variant="flat"
                          class="tone-badge"
                          @click:close="removeTone(ti)"
                        >
                          {{ t }}
                        </v-chip>
                        <v-menu :close-on-content-click="false" location="bottom start">
                          <template #activator="{ props: menuProps }">
                            <v-chip
                              v-bind="menuProps"
                              size="x-small"
                              variant="outlined"
                              color="primary"
                              class="add-tone-btn"
                            >
                              <v-icon size="10" start>mdi-plus</v-icon>
                              Tone
                            </v-chip>
                          </template>
                          <v-card class="add-tone-card pa-2" min-width="220">
                            <div v-if="availableTones.length > 0" class="d-flex flex-wrap ga-1 mb-2">
                              <v-chip
                                v-for="opt in availableTones"
                                :key="opt"
                                size="x-small"
                                variant="tonal"
                                color="primary"
                                class="add-tone-option"
                                @click="addToneValue(opt)"
                              >
                                {{ opt }}
                              </v-chip>
                            </div>
                            <v-text-field
                              v-model="toneInput"
                              placeholder="Custom tone, Enter to add"
                              variant="underlined"
                              density="compact"
                              hide-details
                              class="add-tone-input"
                              autofocus
                              @keydown.enter.prevent="commitToneInput"
                            />
                          </v-card>
                        </v-menu>
                      </div>
                    </div>

                    <!-- Tone rationale -->
                    <div v-if="item.tone_rationale" class="tone-rationale-text mb-1">{{ item.tone_rationale }}</div>

                    <v-text-field v-if="item.type === 'ad'" :placeholder="!item.customer ? 'Name of the advertiser or sponsor' : 'Customer'" :model-value="item.customer || ''" @update:model-value="$emit('update-segment-field', { field: 'customer', value: $event })" variant="underlined" density="compact" hide-details class="sidebar-field" :color="segmentTypeColor" />
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════
           ALL SECTIONS — Collapsible
           ═══════════════════════════════════════════════ -->
      <div class="zone-b">
        <draggable
          v-model="panelOrder"
          item-key="key"
          handle=".panel-drag-handle"
          :animation="200"
          ghost-class="panel-ghost"
          class="metadata-panels-draggable"
        >
          <template #item="{ element }">
            <div class="draggable-panel-wrapper">

              <!-- Asset Pool -->
              <v-expansion-panels v-if="element.key === 'assetpool' && episodeNumber" v-model="expandedPanels" multiple>
                <v-expansion-panel value="assetpool">
                  <v-expansion-panel-title class="compact-panel-title">
                    <v-icon size="x-small" class="panel-drag-handle mr-1" style="cursor: grab;">mdi-drag-horizontal-variant</v-icon>
                    <v-icon size="small" class="mr-1">mdi-package-variant</v-icon>
                    Asset Pool
                    <template v-slot:actions="{ expanded }">
                      <v-icon :icon="expanded ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
                    </template>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <AssetPoolPanel :episode-number="episodeNumber" :rundown-items="rundownItems" :panel-width="panelWidth" :selected-item-label="selectedItemLabel" @place-item="$emit('place-library-item', $event)" @create-new-item="$emit('create-new-library-item', $event)" @reinsert-pool-media="$emit('reinsert-pool-media', $event)" @insert-whiteboard-cue="$emit('insert-whiteboard-cue', $event)" />
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <!-- People & Resources -->
              <v-expansion-panels v-if="element.key === 'people' && item" v-model="expandedPanels" multiple>
                <v-expansion-panel value="people">
                  <v-expansion-panel-title class="compact-panel-title">
                    <v-icon size="x-small" class="panel-drag-handle mr-1" style="cursor: grab;">mdi-drag-horizontal-variant</v-icon>
                    <v-icon size="small" class="mr-1">mdi-account-group-outline</v-icon>
                    People & Resources
                    <template v-slot:actions="{ expanded }">
                      <v-chip v-if="!expanded && (item.guests || item.tags)" size="x-small" variant="tonal" color="primary" class="ml-1">{{ [item.guests ? 'Guests' : '', item.tags ? 'Tags' : ''].filter(Boolean).join(', ') }}</v-chip>
                      <v-icon :icon="expanded ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
                    </template>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-textarea placeholder="Names of guests appearing in this segment" :model-value="item.guests || ''" @update:model-value="updateField('guests', $event)" variant="underlined" density="compact" rows="2" hide-details class="sidebar-field mb-1" :color="segmentTypeColor" />
                    <v-textarea placeholder="Links, references, or source material" :model-value="item.resources || ''" @update:model-value="updateField('resources', $event)" variant="underlined" density="compact" rows="2" hide-details class="sidebar-field mb-1" :color="segmentTypeColor" />
                    <v-text-field placeholder="Add tags to categorize this segment" :model-value="item.tags || ''" @update:model-value="updateField('tags', $event)" variant="underlined" density="compact" hide-details class="sidebar-field" :color="segmentTypeColor" />
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <!-- Speaker Stats -->
              <v-expansion-panels v-if="element.key === 'speaker' && item" v-model="expandedPanels" multiple>
                <v-expansion-panel value="speaker">
                  <v-expansion-panel-title class="compact-panel-title">
                    <v-icon size="x-small" class="panel-drag-handle mr-1" style="cursor: grab;">mdi-drag-horizontal-variant</v-icon>
                    <v-icon size="small" class="mr-1">mdi-account-voice</v-icon>
                    Speaker Stats
                    <template v-slot:actions="{ expanded }">
                      <v-chip v-if="!expanded && selectedSpeaker" size="x-small" variant="tonal" color="primary" class="ml-1">{{ selectedSpeaker.wpm }} WPM</v-chip>
                      <v-icon :icon="expanded ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
                    </template>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-select placeholder="Assign a speaker for WPM calculation" :model-value="item.speaker_id || null" :items="speakers" item-title="name" item-value="id" @update:model-value="updateField('speaker_id', $event)" variant="underlined" density="compact" hide-details class="sidebar-field mb-1" clearable :color="segmentTypeColor">
                      <template v-slot:prepend-inner><v-icon size="small">mdi-account-voice</v-icon></template>
                    </v-select>
                    <div v-if="selectedSpeaker" class="speaker-wpm-display">
                      <v-card variant="tonal" color="primary" class="pa-2">
                        <div class="d-flex justify-space-between align-center">
                          <div><div class="text-caption">Words Per Minute</div><div class="text-h6">{{ selectedSpeaker.wpm }}</div></div>
                          <div class="text-right"><div class="text-caption">Range</div><div class="text-body-2">{{ selectedSpeaker.wpm_min }} - {{ selectedSpeaker.wpm_max }}</div></div>
                        </div>
                      </v-card>
                    </div>
                    <v-btn size="x-small" variant="text" color="primary" class="mt-1" @click="$emit('open-wpm-tool')">
                      <v-icon left size="small">mdi-speedometer</v-icon> Measure WPM
                    </v-btn>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <!-- Versions -->
              <v-expansion-panels v-if="element.key === 'versions' && item" v-model="expandedPanels" multiple>
                <v-expansion-panel value="versions">
                  <v-expansion-panel-title class="compact-panel-title">
                    <v-icon size="x-small" class="panel-drag-handle mr-1" style="cursor: grab;">mdi-drag-horizontal-variant</v-icon>
                    <v-icon size="small" class="mr-1">mdi-history</v-icon>
                    Versions
                    <template v-slot:actions="{ expanded }">
                      <v-chip v-if="!expanded && versionHistory.length > 0" size="x-small" variant="tonal" color="info" class="ml-1">{{ versionHistory.length }}</v-chip>
                      <v-icon :icon="expanded ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
                    </template>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <div v-if="loadingVersions" class="text-center py-2"><v-progress-circular indeterminate size="20" width="2" color="primary" /></div>
                    <div v-else-if="versionHistory.length === 0" class="text-center py-2">
                      <p class="text-caption text-grey">No saved versions yet</p>
                      <p class="text-caption text-grey-lighten-1">Versions are created on manual save (Ctrl+S)</p>
                    </div>
                    <v-list v-else density="compact" class="version-list pa-0">
                      <v-list-item v-for="(version, idx) in versionHistory.slice(0, visibleVersionCount)" :key="version.version_number" class="version-item px-2" :class="{ 'current-version': idx === 0 }">
                        <template v-slot:prepend><v-chip size="x-small" :color="idx === 0 ? 'primary' : 'grey'" class="mr-2">v{{ version.version_number }}</v-chip></template>
                        <v-list-item-title class="text-body-2">{{ formatVersionDate(version.created_at) }}</v-list-item-title>
                        <v-list-item-subtitle class="text-caption">{{ version.content_length || 0 }} chars<span v-if="version.created_by"> &bull; {{ version.created_by }}</span></v-list-item-subtitle>
                        <!-- Per-version actions: labeled Preview + Restore (todo #35). Current
                             version shows a chip instead. -->
                        <div class="version-actions mt-1">
                          <template v-if="idx > 0">
                            <v-btn size="x-small" variant="tonal" color="primary" class="mr-1" prepend-icon="mdi-eye" @click="$emit('preview-version', version.version_number)">Preview</v-btn>
                            <v-btn size="x-small" variant="tonal" color="warning" prepend-icon="mdi-restore" @click="$emit('restore-version', version.version_number)">Restore</v-btn>
                          </template>
                          <v-chip v-else size="x-small" color="success" variant="tonal">Current</v-chip>
                        </div>
                      </v-list-item>
                    </v-list>
                    <div v-if="versionHistory.length > visibleVersionCount" class="text-center mt-1">
                      <v-btn size="x-small" variant="text" color="primary" prepend-icon="mdi-chevron-down" @click="visibleVersionCount += 10">
                        Show more ({{ visibleVersionCount }} of {{ versionHistory.length }})
                      </v-btn>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <!-- Workflow Tools -->
              <v-expansion-panels v-if="element.key === 'assetgen' && episodeNumber" v-model="expandedPanels" multiple>
                <v-expansion-panel value="assetgen">
                  <v-expansion-panel-title class="compact-panel-title">
                    <v-icon size="x-small" class="panel-drag-handle mr-1" style="cursor: grab;">mdi-drag-horizontal-variant</v-icon>
                    <v-icon size="small" class="mr-1">mdi-wrench</v-icon>
                    Workflow Tools
                    <template v-slot:actions="{ expanded }">
                      <v-icon :icon="expanded ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
                    </template>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <div class="asset-generation-buttons">
                      <!-- Generate Script with flyout -->
                      <v-btn size="small" variant="tonal" color="indigo-darken-1" :loading="generatingScript" class="mb-1" block @click="scriptFlyoutOpen = !scriptFlyoutOpen">
                        <v-icon left size="small">mdi-script-text-outline</v-icon> Generate Script
                        <v-spacer />
                        <v-icon size="small" :class="{ 'rotate-90': scriptFlyoutOpen }">mdi-chevron-right</v-icon>
                      </v-btn>
                      <v-expand-transition>
                        <div v-if="scriptFlyoutOpen" class="script-flyout ml-4">
                          <v-btn v-for="st in scriptTypes" :key="st.preset" size="x-small" variant="text" :color="st.color" block class="script-flyout-btn" @click="generateScriptPreset(st.preset)">
                            <v-icon left size="small">{{ st.icon }}</v-icon> {{ st.label }}
                          </v-btn>
                        </div>
                      </v-expand-transition>

                      <v-btn size="small" variant="tonal" color="amber-darken-2" :loading="regeneratingFSQ" :disabled="regeneratingFSQ" @click="regenerateAllFSQ" class="mb-2 mt-2" block><v-icon left size="small">mdi-format-quote-close</v-icon> Regenerate All Quotes</v-btn>
                      <div v-if="fsqRegenerationStatus" class="text-caption mt-1" :class="fsqRegenerationStatus.includes('Error') ? 'text-error' : 'text-success'">{{ fsqRegenerationStatus }}</div>
                      <v-btn size="small" variant="tonal" color="deep-purple-darken-2" :loading="regeneratingGFX" :disabled="regeneratingGFX" @click="regenerateAllGFX" class="mb-2 mt-2" block><v-icon left size="small">mdi-image-multiple</v-icon> Regenerate All Graphics</v-btn>
                      <div v-if="gfxRegenerationStatus" class="text-caption mt-1" :class="gfxRegenerationStatus.includes('Error') ? 'text-error' : 'text-success'">{{ gfxRegenerationStatus }}</div>
                      <v-btn size="small" variant="tonal" color="blue-darken-2" :loading="enumeratingCues" :disabled="enumeratingCues" @click="enumerateCueBlocks" class="mb-2 mt-2" block><v-icon left size="small">mdi-format-list-numbered</v-icon> Enumerate Cue Blocks</v-btn>
                      <div v-if="enumerationStatus" class="text-caption mt-1" :class="enumerationStatus.includes('Error') ? 'text-error' : 'text-success'">{{ enumerationStatus }}</div>
                      <v-btn size="small" variant="tonal" color="teal-darken-2" :loading="gatheringMedia" :disabled="gatheringMedia" @click="gatherForShow" class="mb-2 mt-2" block><v-icon left size="small">mdi-folder-download</v-icon> Gather for Show</v-btn>
                      <v-progress-linear v-if="gatheringMedia && gatherProgress > 0" :model-value="gatherProgress" color="teal" height="6" class="mt-1 mb-1" />
                      <div v-if="gatherStatus" class="text-caption mt-1" :class="gatherStatus.includes('Error') ? 'text-error' : 'text-success'">{{ gatherStatus }}<v-btn v-if="gatherResults" size="x-small" variant="text" color="primary" @click="showGatherResultsModal = true" class="ml-1">Details</v-btn></div>
                      <v-btn size="small" variant="tonal" color="cyan-darken-2" :loading="exportingToVmix" :disabled="exportingToVmix" @click="exportToVmix" class="mb-2 mt-2" block><v-icon left size="small">mdi-television-classic</v-icon> Export to vMix</v-btn>
                      <div v-if="vmixExportStatus" class="text-caption mt-1" :class="vmixExportStatus.includes('Error') ? 'text-error' : 'text-success'">{{ vmixExportStatus }}</div>
                      <v-btn size="small" variant="tonal" color="deep-purple-darken-1" :loading="packagingGraphics" :disabled="packagingGraphics" @click="downloadGraphicsPackage" class="mb-2 mt-2" block><v-icon left size="small">mdi-package-down</v-icon> Download Graphics Package</v-btn>
                      <div v-if="graphicsPackageStatus" class="text-caption mt-1" :class="graphicsPackageStatus.includes('Error') ? 'text-error' : 'text-success'">{{ graphicsPackageStatus }}</div>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <!-- Documents section removed — scripts now live in Asset Pool > Scripts tab -->

            </div>
          </template>
        </draggable>
      </div>

    </v-card>

    <!-- Gather Results Modal -->
    <v-dialog v-model="showGatherResultsModal" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-folder-download</v-icon>
          Media Gather Results
          <v-spacer />
          <v-btn icon size="small" @click="showGatherResultsModal = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text v-if="gatherResults">
          <v-alert
            :type="gatherResults.failed > 0 ? 'warning' : 'success'"
            density="compact"
            class="mb-3"
          >
            <strong>{{ gatherResults.copied }}</strong> files copied,
            <strong>{{ gatherResults.skipped }}</strong> skipped (no media),
            <strong>{{ gatherResults.failed }}</strong> failed
          </v-alert>

          <div v-if="gatherResults.files && gatherResults.files.length > 0" class="mb-3">
            <div class="text-subtitle-2 text-success mb-1">
              <v-icon size="small" color="success">mdi-check-circle</v-icon>
              Successfully Copied ({{ gatherResults.files.length }})
            </div>
            <v-list density="compact" class="gather-results-list">
              <v-list-item
                v-for="file in gatherResults.files"
                :key="file.dest"
                class="px-2"
              >
                <template v-slot:prepend>
                  <v-chip size="x-small" :color="getTypeColor(file.type)" class="mr-2">
                    {{ file.type }}
                  </v-chip>
                </template>
                <v-list-item-title class="text-body-2">{{ file.dest }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </div>

          <div v-if="gatherResults.failures && gatherResults.failures.length > 0" class="mb-3">
            <div class="text-subtitle-2 text-error mb-1">
              <v-icon size="small" color="error">mdi-alert-circle</v-icon>
              Failed - File Not Found ({{ gatherResults.failures.length }})
            </div>
            <v-list density="compact" class="gather-results-list error-list">
              <v-list-item
                v-for="(failure, idx) in gatherResults.failures"
                :key="idx"
                class="px-2"
              >
                <template v-slot:prepend>
                  <v-chip size="x-small" :color="getTypeColor(failure.type)" class="mr-2">
                    {{ failure.type }}
                  </v-chip>
                </template>
                <v-list-item-title class="text-body-2">{{ failure.slug }}</v-list-item-title>
                <v-list-item-subtitle class="text-caption text-error">
                  {{ failure.mediaUrl }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </div>

          <div v-if="gatherResults.skippedCues && gatherResults.skippedCues.length > 0">
            <div class="text-subtitle-2 text-grey mb-1">
              <v-icon size="small" color="grey">mdi-skip-next</v-icon>
              Skipped - No MediaURL ({{ gatherResults.skippedCues.length }})
            </div>
            <v-list density="compact" class="gather-results-list">
              <v-list-item
                v-for="(skipped, idx) in gatherResults.skippedCues"
                :key="idx"
                class="px-2"
              >
                <template v-slot:prepend>
                  <v-chip size="x-small" :color="getTypeColor(skipped.type)" class="mr-2">
                    {{ skipped.type }}
                  </v-chip>
                </template>
                <v-list-item-title class="text-body-2 text-grey">{{ skipped.slug || 'No slug' }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </div>

          <v-divider class="my-3" />
          <div class="text-caption text-grey">
            <v-icon size="small">mdi-folder</v-icon>
            Output: {{ gatherResults.media_list_path }}
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="showGatherResultsModal = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Graphics Package Modal -->
    <v-dialog v-model="showGraphicsPackageModal" max-width="550">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="deep-purple">mdi-package-down</v-icon>
          Graphics Package
          <v-spacer />
          <v-btn icon size="small" @click="showGraphicsPackageModal = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text>
          <div v-if="packagingGraphics" class="text-center py-4">
            <v-progress-circular indeterminate color="deep-purple" size="48" class="mb-3" />
            <div class="text-body-2">{{ graphicsPackageModalStatus }}</div>
          </div>
          <div v-else-if="graphicsPackageInfo">
            <v-alert type="success" density="compact" class="mb-3">
              <strong>{{ graphicsPackageInfo.file_count }}</strong> files packaged
              <span v-if="graphicsPackageInfo.cached" class="ml-1">(cached)</span>
            </v-alert>
            <div class="d-flex justify-space-between mb-2 text-body-2">
              <span>Package size:</span>
              <strong>{{ formatFileSize(graphicsPackageInfo.zip_size) }}</strong>
            </div>
            <div class="d-flex justify-space-between mb-3 text-body-2">
              <span>Uncompressed:</span>
              <span>{{ formatFileSize(graphicsPackageInfo.total_uncompressed_size) }}</span>
            </div>
            <div v-if="graphicsPackageInfo.type_counts" class="mb-3">
              <div class="text-subtitle-2 mb-1">Contents by type</div>
              <div class="d-flex flex-wrap ga-1">
                <v-chip
                  v-for="(count, type) in graphicsPackageInfo.type_counts"
                  :key="type"
                  size="small"
                  :color="getTypeColor(type)"
                  variant="tonal"
                >
                  {{ type }}: {{ count }}
                </v-chip>
              </div>
            </div>
            <div class="mb-3">
              <div class="text-subtitle-2 mb-1">Files ({{ graphicsPackageInfo.files.length }})</div>
              <v-list density="compact" class="gather-results-list" style="max-height: 250px; overflow-y: auto;">
                <v-list-item
                  v-for="file in graphicsPackageInfo.files"
                  :key="file.name"
                  class="px-2"
                >
                  <template v-slot:prepend>
                    <v-chip size="x-small" :color="getTypeColor(file.type)" class="mr-2">
                      {{ file.type }}
                    </v-chip>
                  </template>
                  <v-list-item-title class="text-body-2">{{ file.name }}</v-list-item-title>
                  <template v-slot:append>
                    <span class="text-caption text-grey">{{ formatFileSize(file.size) }}</span>
                  </template>
                </v-list-item>
              </v-list>
            </div>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn
            v-if="graphicsPackageInfo"
            color="deep-purple"
            variant="flat"
            @click="triggerGraphicsDownload"
          >
            <v-icon left size="small">mdi-download</v-icon>
            Download ZIP
          </v-btn>
          <v-btn variant="text" @click="showGraphicsPackageModal = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Past Revisions Modal -->
    <v-dialog v-model="showRevisionsModal" max-width="500">
      <v-card>
        <v-card-title class="text-subtitle-1 d-flex align-center">
          <v-icon size="small" class="mr-2">mdi-history</v-icon>
          Past Revisions: {{ selectedDocument?.type || formatDocumentName(selectedDocument) }}
          <v-spacer />
          <v-btn icon size="small" @click="showRevisionsModal = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-0">
          <v-list density="compact" v-if="selectedDocument?.pastRevisions?.length > 0">
            <v-list-item
              v-for="rev in selectedDocument.pastRevisions"
              :key="rev.revision"
              :href="rev.url"
              target="_blank"
              class="revision-list-item"
            >
              <template v-slot:prepend>
                <v-icon size="small" :color="getDocumentIconColor(rev.format)">
                  {{ getDocumentIcon(rev.format) }}
                </v-icon>
              </template>
              <v-list-item-title class="text-body-2">
                {{ rev.filename }}
                <span class="revision-badge">R{{ rev.revision }}</span>
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption">
                {{ rev.size_formatted }} &bull; {{ rev.modified_formatted }}
              </v-list-item-subtitle>
              <template v-slot:append>
                <v-btn
                  icon
                  size="x-small"
                  variant="text"
                  :href="rev.url"
                  target="_blank"
                  @click.stop
                >
                  <v-icon size="small">mdi-open-in-new</v-icon>
                </v-btn>
              </template>
            </v-list-item>
          </v-list>
          <div v-else class="pa-4 text-center text-grey">
            No past revisions available
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            size="small"
            variant="text"
            @click="showRevisionsModal = false"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick, getCurrentInstance } from 'vue'
import { themeColorMap, getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'
import { useContentIndicators } from '@/composables/useContentIndicators'
import AssetPoolPanel from './AssetPoolPanel.vue' // eslint-disable-line no-unused-vars
import draggable from 'vuedraggable' // eslint-disable-line no-unused-vars

const emit = defineEmits([
  'close',
  'toggle-width',
  'update-field',
  'save-all',
  'open-wpm-tool',
  'generate-host-script',
  'generate-script',
  'generate-media-list',
  'generate-prompter-files',
  'refresh-rundown',
  'cues-enumerated',
  'show-notification',
  'restore-version',
  'preview-version',
  'place-library-item',
  'create-new-library-item',
  'reinsert-pool-media',
  'insert-whiteboard-cue',
  'update-segment-field',
  'scripts-updated',
  'reset-fields'
])

const props = defineProps({
  panelWidth: {
    type: String,
    default: 'wide',
    validator: (value) => ['narrow', 'wide'].includes(value)
  },
  panelHeight: {
    type: Number,
    default: null
  },
  item: {
    type: Object,
    default: () => null
  },
  episodeNumber: {
    type: String,
    default: null
  },
  itemTypes: {
    type: Array,
    default: () => [
      { title: 'Segment', value: 'segment' },
      { title: 'Advertisement', value: 'ad' },
      { title: 'Promo', value: 'promo' },
      { title: 'Call to Action', value: 'cta' },
      { title: 'Transition', value: 'trans' }
    ]
  },
  mediaListLoading: {
    type: Boolean,
    default: false
  },
  hostScriptLoading: {
    type: Boolean,
    default: false
  },
  saveState: {
    type: Object,
    default: () => ({
      hasChanges: false
    })
  },
  versionHistory: {
    type: Array,
    default: () => []
  },
  loadingVersions: {
    type: Boolean,
    default: false
  },
  rundownItems: {
    type: Array,
    default: () => []
  }
})

const instance = getCurrentInstance()
const $axios = instance.appContext.config.globalProperties.$axios

// --- data ---
// How many version rows are shown; the "Show more" button bumps this by 10 (todo #35).
const visibleVersionCount = ref(10)

const expandedPanels = ref(['segmentinfo'])
const panelOrder = ref([
  { key: 'assetpool' },
  { key: 'people' },
  { key: 'speaker' },
  { key: 'versions' },
  { key: 'assetgen' }
])
const statusOptions = ref([ // eslint-disable-line no-unused-vars
  'scheduled',
  'draft',
  'production',
  'running',
  'completed'
])
const { llmTextColor } = useContentIndicators()

const priorityOptions = computed(() => { // eslint-disable-line no-unused-vars
  // Pull editorial priority tags from settings, fall back to defaults
  const defaults = ['main-feature', 'top-story', 'second-feature', 'third-feature', 'deep-dive', 'kicker', 'breaking', 'urgent', 'high', 'normal', 'low']
  try {
    const saved = localStorage.getItem('real-content-settings')
    if (saved) {
      const s = JSON.parse(saved)
      const order = s.episodeDescription?.priorityOrder
      if (Array.isArray(order) && order.length > 0) {
        const tags = order.map(p => p.tag).filter(Boolean)
        // Append production tags that aren't in the editorial list
        for (const d of ['urgent', 'high', 'normal', 'low']) {
          if (!tags.includes(d)) tags.push(d)
        }
        return tags
      }
    }
  } catch (e) { /* ignore */ }
  return defaults
})
const speakers = ref([])
const loadingSpeakers = ref(false) // eslint-disable-line no-unused-vars
const generatedDocuments = ref([])
const loadingDocuments = ref(false)
const regeneratingFSQ = ref(false)
const fsqRegenerationStatus = ref('')
const regeneratingGFX = ref(false)
const gfxRegenerationStatus = ref('')
const enumeratingCues = ref(false)
const enumerationStatus = ref('')
const gatheringMedia = ref(false)
const gatherProgress = ref(0)
const gatherStatus = ref('')
const gatherResults = ref(null)
const showGatherResultsModal = ref(false)
const exportingToVmix = ref(false)
const vmixExportStatus = ref('')
const packagingGraphics = ref(false)
const graphicsPackageStatus = ref('')
const graphicsPackageInfo = ref(null)
const graphicsPackageModalStatus = ref('')
const showGraphicsPackageModal = ref(false)
const showRevisionsModal = ref(false)
const selectedDocument = ref(null)

// Ref on the panel root so the LLM-color scanner can find all sidebar-field
// inputs without touching each field's template.
const metadataRootRef = ref(null)

// --- Tone badge field -------------------------------------------------------
// `item.tone` is a comma-separated string ("serious,sarcastic").
// We parse it into an array for display as chips, and serialize back on edit.
const toneInput = ref('')
const descriptionTextareaRef = ref(null)

// --- Regenerate description -------------------------------------------------
// --- Generate Script flyout -----------------------------------------------
const scriptFlyoutOpen = ref(false)
// Generation now runs in ContentEditor's overlay; the flyout button's loading
// state is no longer driven locally.
const generatingScript = ref(false)

const scriptTypes = [
  { preset: 'host_full', label: 'Host Script', icon: 'mdi-script-text', color: 'indigo' },
  { preset: 'production', label: 'Director Script', icon: 'mdi-clipboard-list', color: 'teal' },
  { preset: 'show_caller', label: 'Show Caller', icon: 'mdi-bullhorn', color: 'orange' },
  { preset: 'media_list', label: 'Media List', icon: 'mdi-folder-multiple-image', color: 'green' }
]

async function generateScriptPreset(preset) {
  if (!props.episodeNumber) return

  // Every script generation now shows the full progress overlay handled by
  // ContentEditor (the same modal experience as Media List), instead of a
  // silent inline API call. Each preset delegates to the matching handler.
  scriptFlyoutOpen.value = false

  // Media List has a dedicated endpoint + overlay.
  if (preset === 'media_list') {
    emit('generate-media-list')
    return
  }

  // host_full / host_clean / production (and any future /scripts/generate
  // preset) → the generic overlay-driven generator in ContentEditor.
  emit('generate-script', preset)
}

const showRegenModal = ref(false)
const regenFeedback = ref('')
const regenerating = ref(false)

async function regenerateDescription() {
  if (!props.item || !props.item.asset_id) return
  // Close modal immediately — the overlay spinner takes over
  const assetId = props.item.asset_id || props.item.id
  const prevDesc = props.item.description || ''
  const feedback = regenFeedback.value || ''
  showRegenModal.value = false
  regenFeedback.value = ''
  regenerating.value = true
  try {
    const response = await $axios.post(`/episodes/regenerate-description`, {
      asset_id: assetId,
      previous_description: prevDesc,
      feedback: feedback
    })
    if (response.data && response.data.description) {
      emit('update-segment-field', { field: 'description', value: response.data.description })
      if (response.data.description_model) {
        emit('update-segment-field', { field: 'description_model', value: response.data.description_model })
      }
      nextTick(resizeDescriptionTextarea)
    }
  } catch (error) {
    console.error('Regeneration failed:', error)
  } finally {
    regenerating.value = false
  }
}

// LLM slug generation (todo: slug-gen feature). Generates a short broadcast
// slug from the title + script body; if the current slug is 5+ words the
// backend includes it and shortens it. The result is emitted as a field update
// so it persists through the normal path.
const generatingSlug = ref(false)
async function generateSlug() {
  if (!props.item || !(props.item.asset_id || props.item.id)) return
  const assetId = props.item.asset_id || props.item.id
  generatingSlug.value = true
  try {
    const response = await $axios.post(`/episodes/generate-slug`, { asset_id: assetId })
    if (response.data && response.data.slug) {
      emit('update-segment-field', { field: 'slug', value: response.data.slug })
    }
  } catch (error) {
    console.error('Slug generation failed:', error)
    if (window.notifyUserStandard) {
      const msg = error.response?.data?.detail || 'Slug generation failed'
      window.notifyUserStandard(msg, '#F44336', 4000)
    }
  } finally {
    generatingSlug.value = false
  }
}

// Auto-resize the plain description textarea to fit its content.
function resizeDescriptionTextarea() {
  const el = descriptionTextareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

// Sync textarea DOM value + resize whenever the item changes (new segment selected, LLM fills it, etc.)
watch(
  () => props.item && props.item.description,
  (newVal) => nextTick(() => {
    const el = descriptionTextareaRef.value
    if (el) el.value = newVal || ''
    resizeDescriptionTextarea()
  }),
  { immediate: true }
)

// Also resize after initial mount
onMounted(() => nextTick(resizeDescriptionTextarea))

// Listen for LLM segment updates — refresh description if the current item was updated
function handleLLMSegmentUpdate(event) {
  const { asset_id, content_type } = event.detail || {}
  if (!asset_id || !props.item) return
  const currentId = props.item.asset_id || props.item.id
  if (asset_id !== currentId) return
  if (content_type !== 'segment_description' && content_type !== 'segment_tone') return

  // Fetch the updated fields from the backend
  $axios.get(`/episodes/rundown-item/${asset_id}`).then(resp => {
    const data = resp.data
    if (data.description !== undefined) {
      emit('update-segment-field', { field: 'description', value: data.description })
    }
    if (data.description_model !== undefined) {
      emit('update-segment-field', { field: 'description_model', value: data.description_model })
    }
    if (data.tone !== undefined) {
      emit('update-segment-field', { field: 'tone', value: data.tone })
    }
    if (data.tone_rationale !== undefined) {
      emit('update-segment-field', { field: 'tone_rationale', value: data.tone_rationale })
    }
    if (data.llm_generated_fields !== undefined) {
      emit('update-segment-field', { field: 'llm_generated_fields', value: data.llm_generated_fields })
    }
    nextTick(resizeDescriptionTextarea)
  }).catch(err => {
    console.warn('Failed to refresh segment after LLM update:', err)
  })
}
onMounted(() => window.addEventListener('llm-segment-updated', handleLLMSegmentUpdate))
onUnmounted(() => window.removeEventListener('llm-segment-updated', handleLLMSegmentUpdate))

const parsedTones = computed(() => {
  const raw = props.item && props.item.tone
  if (!raw || typeof raw !== 'string') return []
  return raw.split(',').map(t => t.trim()).filter(Boolean)
})

const isToneLlmGenerated = computed(() => {
  const fields = props.item && props.item.llm_generated_fields
  return Array.isArray(fields) && fields.includes('tone')
})

// Palette options minus already-applied tones, used by the inline "+ Tone" menu
const availableTones = computed(() => {
  const applied = new Set(parsedTones.value.map(t => t.toLowerCase()))
  return tonePaletteOptions.value.filter(opt => !applied.has(String(opt).toLowerCase()))
})

// Background color for sidebar block headers (Settings → Color Selector → General UI → Block Header)
const blockHeaderStyle = computed(() => {
  const color = resolveVuetifyColor(getColorValue('block-header'))
  return color ? { backgroundColor: color, color: '#ffffff' } : {}
})

// Load tone palette from real-content-settings (same as GenerationSettings.vue)
const tonePaletteOptions = computed(() => {
  try {
    const saved = localStorage.getItem('real-content-settings')
    if (saved) {
      const s = JSON.parse(saved)
      if (Array.isArray(s.tonePalette)) return s.tonePalette
    }
  } catch (e) { /* ignore */ }
  return ['serious', 'somber', 'skeptical', 'irreverent', 'sarcastic', 'lighthearted', 'urgent', 'analytical', 'mocking']
})

function handleToneInput(val) { // eslint-disable-line no-unused-vars
  // v-combobox may fire with an item from the dropdown
  if (val && typeof val === 'string' && val.trim()) {
    addToneValue(val.trim())
    nextTick(() => { toneInput.value = '' })
  }
}

function commitToneInput() {
  const raw = typeof toneInput.value === 'string' ? toneInput.value.trim() : ''
  if (!raw) return
  // Support comma-separated batch input ("serious, sarcastic, urgent")
  const parts = raw.split(',').map(t => t.trim().toLowerCase()).filter(Boolean)
  for (const part of parts) addToneValue(part)
  toneInput.value = ''
}

function addToneValue(val) {
  const normalized = val.toLowerCase().replace(/\s+/g, ' ')
  const existing = parsedTones.value
  if (existing.map(t => t.toLowerCase()).includes(normalized)) return
  const updated = [...existing, normalized].join(',')
  emit('update-segment-field', { field: 'tone', value: updated })
}

function removeTone(index) {
  const updated = parsedTones.value.filter((_, i) => i !== index).join(',')
  emit('update-segment-field', { field: 'tone', value: updated })
}

// --- Priority tag system (same pattern as tone) ---
const priorityInput = ref('')

const parsedPriorities = computed(() => {
  const raw = props.item && props.item.priority
  if (!raw || typeof raw !== 'string') return []
  return raw.split(',').map(t => t.trim()).filter(Boolean)
})

function getPriorityColor(tag) { // eslint-disable-line no-unused-vars
  try {
    const saved = localStorage.getItem('real-content-settings')
    if (saved) {
      const s = JSON.parse(saved)
      const order = s.episodeDescription?.priorityOrder
      if (Array.isArray(order)) {
        const match = order.find(p => p.tag === tag)
        if (match && match.color) return match.color
      }
    }
  } catch (e) { /* ignore */ }
  const fallback = { 'main-feature': '#b71c1c', 'top-story': '#d32f2f', 'second-feature': '#e64a19', 'third-feature': '#f57c00', 'deep-dive': '#1565c0', 'kicker': '#43a047', 'breaking': '#c62828', 'urgent': '#d32f2f', 'high': '#e64a19', 'normal': '#757575', 'low': '#9e9e9e' }
  return fallback[tag] || '#757575'
}

function handlePriorityInput(val) { // eslint-disable-line no-unused-vars
  if (val && typeof val === 'string' && val.trim()) {
    addPriorityValue(val.trim())
    nextTick(() => { priorityInput.value = '' })
  }
}

function commitPriorityInput() { // eslint-disable-line no-unused-vars
  const raw = typeof priorityInput.value === 'string' ? priorityInput.value.trim() : ''
  if (!raw) return
  const parts = raw.split(',').map(t => t.trim().toLowerCase()).filter(Boolean)
  for (const part of parts) addPriorityValue(part)
  priorityInput.value = ''
}

function addPriorityValue(val) {
  const normalized = val.toLowerCase().replace(/\s+/g, '-')
  const existing = parsedPriorities.value
  if (existing.map(t => t.toLowerCase()).includes(normalized)) return
  const updated = [...existing, normalized].join(',')
  emit('update-segment-field', { field: 'priority', value: updated })
}

function removePriority(index) { // eslint-disable-line no-unused-vars
  const updated = parsedPriorities.value.filter((_, i) => i !== index).join(',')
  emit('update-segment-field', { field: 'priority', value: updated })
}

// --- LLM-generated field highlighter ---------------------------------------
// Single bottleneck: the backend marks which fields were filled by the LLM by
// listing their names on `item.llm_generated_fields`. We then walk every
// `.sidebar-field` input/textarea under the panel root ONCE per item/field
// change, match each element to its underlying field by comparing its current
// value against `item[field]`, and toggle the `.llm-generated` CSS class.
// There's zero per-field template wiring — add or remove any sidebar field
// and this still works.
watch(
  () => [
    props.item && props.item.llm_generated_fields,
    props.item,
    metadataRootRef.value
  ],
  async () => {
    await nextTick()
    const root = metadataRootRef.value
    if (!root) return
    const llmFields = Array.isArray(props.item && props.item.llm_generated_fields)
      ? props.item.llm_generated_fields
      : []
    // Clear any prior markers so edits/backend updates are reflected.
    root.querySelectorAll('.llm-generated').forEach(el => {
      el.classList.remove('llm-generated')
    })
    if (!props.item || llmFields.length === 0) return

    // Scan Vuetify sidebar-field inputs
    const inputs = root.querySelectorAll('.sidebar-field input, .sidebar-field textarea')
    const claimed = new WeakSet()
    for (const field of llmFields) {
      const target = String((props.item[field] ?? ''))
      if (!target) continue
      for (const el of inputs) {
        if (claimed.has(el)) continue
        if ((el.value ?? '') === target) {
          const wrap = el.closest('.sidebar-field')
          if (wrap) {
            wrap.classList.add('llm-generated')
            claimed.add(el)
          }
          break
        }
      }
    }

    // Also scan plain HTML elements (description textarea, tone field)
    if (llmFields.includes('description') && descriptionTextareaRef.value) {
      const el = descriptionTextareaRef.value
      if ((el.value ?? '') === String(props.item.description ?? '')) {
        el.classList.add('llm-generated')
      }
    }
    if (llmFields.includes('tone')) {
      const toneEl = root.querySelector('.tone-field')
      if (toneEl) toneEl.classList.add('llm-generated')
    }
  },
  { deep: true, immediate: true }
)

// When the user edits any sidebar-field, immediately strip its LLM color so
// they get instant visual feedback that the text is now theirs. Delegated
// listener — no per-field wiring.
function handleSidebarInput(event) {
  const wrap = event.target.closest && event.target.closest('.sidebar-field')
  if (wrap && wrap.classList.contains('llm-generated')) {
    wrap.classList.remove('llm-generated')
  }
  // Also handle the plain description textarea
  if (event.target === descriptionTextareaRef.value && event.target.classList.contains('llm-generated')) {
    event.target.classList.remove('llm-generated')
  }
}

onMounted(() => {
  if (metadataRootRef.value) {
    metadataRootRef.value.addEventListener('input', handleSidebarInput, true)
  }
})
// (root is torn down with the component; no explicit removal needed.)

const panelWidthValue = computed(() => {
  return props.panelWidth === 'narrow' ? '330px' : '440px'
})

const panelHeightValue = computed(() => {
  return props.panelHeight ? `${props.panelHeight}px` : '100vh'
})

// Friendly label of the currently-selected rundown item's type, used by
// AssetPoolPanel to title its "Add to {type}" buttons.
const selectedItemLabel = computed(() => { // eslint-disable-line no-unused-vars
  if (!props.item || !props.item.type) return ''
  const match = (props.itemTypes || []).find(t => t.value === props.item.type)
  if (match?.title) return match.title
  // Fallback: capitalize the raw type.
  const t = String(props.item.type)
  return t.charAt(0).toUpperCase() + t.slice(1)
})

const itemHeaderStyle = computed(() => { // eslint-disable-line no-unused-vars
  if (!props.item) {
    return {
      backgroundColor: '#f5f5f5',
      color: '#666'
    }
  }

  const itemType = props.item.type || 'segment'
  const colorValue = getColorValue(itemType.toLowerCase()) || 'grey'
  const backgroundColor = resolveVuetifyColor(colorValue)
  const colorMapping = themeColorMap[itemType] || themeColorMap.unknown
  const textColor = colorMapping.textColor || '#ffffff'

  return {
    backgroundColor: backgroundColor,
    color: textColor
  }
})

const statusThemeColors = computed(() => { // eslint-disable-line no-unused-vars
  if (!props.item) {
    return {
      primary: '#e3f2fd',
      border: '#90caf9',
      accent: '#1976d2'
    }
  }

  const status = props.item.status || 'draft'
  const statusColors = {
    draft: {
      primary: '#f5f5f5',
      border: '#bdbdbd',
      accent: '#616161'
    },
    approved: {
      primary: '#e8f5e8',
      border: '#81c784',
      accent: '#2e7d32'
    },
    production: {
      primary: '#fff3e0',
      border: '#ffb74d',
      accent: '#f57c00'
    },
    completed: {
      primary: '#e3f2fd',
      border: '#64b5f6',
      accent: '#1976d2'
    }
  }

  return statusColors[status] || statusColors.draft
})

const currentItemNeedsAttention = computed(() => {
  const content = props.item?.script || props.item?.script_content
  if (!content) return false
  return content.includes('data-needs-attention="true"') || /NeedsAttention:\s*true/i.test(content)
})

const segmentTypeColor = computed(() => {
  if (!props.item) return undefined
  const itemType = props.item.type || 'segment'
  return resolveVuetifyColor(getColorValue(itemType.toLowerCase()) || 'grey')
})

const slugPlaceholder = computed(() => {
  if (!props.item) return 'Slug'
  const slug = props.item.slug || ''
  return /^Segment-\d+$/i.test(slug) || !slug ? 'Enter a descriptive slug' : 'Slug'
})

const titlePlaceholder = computed(() => {
  if (!props.item) return 'Title'
  const title = props.item.title || ''
  return /^Segment-\d+$/i.test(title) || !title ? 'Give this segment a title' : 'Title'
})

const durationPlaceholder = computed(() => {
  if (!props.item) return 'Duration'
  return !props.item.duration || props.item.duration === '00:00:00' ? 'Expected duration (HH:MM:SS)' : 'Duration'
})

const descriptionPlaceholder = computed(() => {
  if (!props.item) return 'Description'
  return !props.item.description ? 'Type the segment\'s short description' : 'Description'
})

const selectedSpeaker = computed(() => {
  if (!props.item?.speaker_id || !speakers.value.length) {
    return null
  }
  return speakers.value.find(s => s.id === props.item.speaker_id)
})

// --- methods ---
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(() => {})
}

function updateField(fieldName, value) {
  emit('update-field', { field: fieldName, value: value })
}

function resetFields() { // eslint-disable-line no-unused-vars
  emit('reset-fields')
}

async function loadSpeakers() {
  loadingSpeakers.value = true
  try {
    const authToken = localStorage.getItem('auth-token')
    const response = await $axios.get('/speakers/', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    })

    if (response.data.success) {
      speakers.value = response.data.data
      autoDetectSpeaker()
    }
  } catch (error) {
    console.error('Error loading speakers:', error)
  } finally {
    loadingSpeakers.value = false
  }
}

function autoDetectSpeaker() {
  if (!props.item || props.item.speaker_id || !speakers.value.length) return
  const content = props.item.script_content || props.item.script || ''
  if (!content) return
  // Extract speaker names from <p class="speakername"> patterns
  const matches = content.match(/class="([a-zA-Z_-]+)"/g)
  if (!matches || !matches.length) return
  // Count occurrences of each class name
  const counts = {}
  matches.forEach(m => {
    const name = m.match(/class="([^"]+)"/)[1].toLowerCase()
    counts[name] = (counts[name] || 0) + 1
  })
  // Find the most common class name
  const dominant = Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0]
  // Match against speakers (case-insensitive)
  const match = speakers.value.find(s => s.name.toLowerCase() === dominant)
  if (match) {
    emit('update-field', { field: 'speaker_id', value: match.id })
  }
}

async function regenerateAllFSQ() {
  if (!props.episodeNumber) {
    fsqRegenerationStatus.value = 'Error: No episode selected'
    return
  }

  regeneratingFSQ.value = true
  fsqRegenerationStatus.value = ''

  try {
    const authToken = localStorage.getItem('auth-token')
    const response = await $axios.post(
      `/fsq/regenerate-all/${props.episodeNumber}`,
      { regenerate_existing: true },
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      }
    )

    if (response.data.success) {
      const { generated, skipped, failed, total_fsqs } = response.data
      fsqRegenerationStatus.value = `Generated: ${generated}/${total_fsqs}, Skipped: ${skipped}, Failed: ${failed}`
    } else {
      fsqRegenerationStatus.value = 'Error: ' + (response.data.message || 'Unknown error')
    }
  } catch (error) {
    console.error('Error regenerating FSQ assets:', error)
    fsqRegenerationStatus.value = 'Error: ' + (error.response?.data?.detail || error.message)
  } finally {
    regeneratingFSQ.value = false
  }
}

async function regenerateAllGFX() {
  if (!props.episodeNumber) {
    gfxRegenerationStatus.value = 'Error: No episode selected'
    return
  }

  regeneratingGFX.value = true
  gfxRegenerationStatus.value = ''

  try {
    const authToken = localStorage.getItem('auth-token')
    const response = await $axios.post(
      `/gfx/regenerate-all/${props.episodeNumber}`,
      { regenerate_existing: true },
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      }
    )

    if (response.data.success) {
      const { generated, skipped, failed, total_gfxs } = response.data
      gfxRegenerationStatus.value = `Generated: ${generated}/${total_gfxs}, Skipped: ${skipped}, Failed: ${failed}`
    } else {
      gfxRegenerationStatus.value = 'Error: ' + (response.data.message || 'Unknown error')
    }
  } catch (error) {
    console.error('Error regenerating GFX assets:', error)
    gfxRegenerationStatus.value = 'Error: ' + (error.response?.data?.detail || error.message)
  } finally {
    regeneratingGFX.value = false
  }
}

async function enumerateCueBlocks() {
  if (!props.episodeNumber) {
    enumerationStatus.value = 'Error: No episode selected'
    return
  }

  enumeratingCues.value = true
  enumerationStatus.value = ''

  try {
    const authToken = localStorage.getItem('auth-token')
    const response = await $axios.post(
      `/episodes/${props.episodeNumber}/enumerate-cues`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      }
    )

    if (response.data.success) {
      const { enumerated, files_renamed, total, skipped_non_media } = response.data
      const mediaCues = total - (skipped_non_media || 0)
      let status = `${enumerated} of ${mediaCues} media cues enumerated, ${files_renamed} files renamed`
      if (skipped_non_media > 0) {
        status += ` (${skipped_non_media} non-media skipped)`
      }
      enumerationStatus.value = status
      // Refresh the open editor content in place (no manual page reload needed).
      emit('cues-enumerated')
    } else {
      enumerationStatus.value = 'Error: ' + (response.data.message || 'Unknown error')
    }
  } catch (error) {
    console.error('Error enumerating cue blocks:', error)
    enumerationStatus.value = 'Error: ' + (error.response?.data?.detail || error.message)
  } finally {
    enumeratingCues.value = false
  }
}

async function gatherForShow() {
  if (!props.episodeNumber) {
    gatherStatus.value = 'Error: No episode selected'
    return
  }

  gatheringMedia.value = true
  gatherProgress.value = 0
  gatherStatus.value = 'Gathering media files...'
  gatherResults.value = null

  try {
    const authToken = localStorage.getItem('auth-token')
    const response = await $axios.post(
      `/episodes/${props.episodeNumber}/gather-media`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      }
    )

    if (response.data.success) {
      const { copied, skipped, failed, total } = response.data
      gatherProgress.value = 100
      gatherStatus.value = `Gathered: ${copied}/${total} files, ${skipped} skipped, ${failed} failed`
      gatherResults.value = response.data

      if (failed > 0) {
        showGatherResultsModal.value = true
      }

      emit('show-notification', {
        message: `Media gather complete: ${copied} files copied to media-list`,
        type: failed > 0 ? 'warning' : 'success'
      })
    } else {
      gatherStatus.value = 'Error: ' + (response.data.message || 'Unknown error')
    }
  } catch (error) {
    console.error('Error gathering media:', error)
    gatherStatus.value = 'Error: ' + (error.response?.data?.detail || error.message)
  } finally {
    gatheringMedia.value = false
  }
}

async function exportToVmix() {
  if (!props.episodeNumber) {
    vmixExportStatus.value = 'Error: No episode selected'
    return
  }
  exportingToVmix.value = true
  vmixExportStatus.value = 'Sending to vMix...'
  try {
    const response = await $axios.post(`/vmix/build-list/${props.episodeNumber}`)
    const { added, failed, total } = response.data
    if (failed > 0) {
      vmixExportStatus.value = `Partial: ${added}/${total} added, ${failed} failed`
    } else if (total === 0) {
      vmixExportStatus.value = 'No media files found. Run Gather for Show first.'
    } else {
      vmixExportStatus.value = `Sent ${added} items to vMix`
    }
  } catch (error) {
    console.error('Error exporting to vMix:', error)
    vmixExportStatus.value = 'Error: ' + (error.response?.data?.detail || error.message)
  } finally {
    exportingToVmix.value = false
  }
}

async function downloadGraphicsPackage() {
  if (!props.episodeNumber) {
    graphicsPackageStatus.value = 'Error: No episode selected'
    return
  }

  packagingGraphics.value = true
  graphicsPackageStatus.value = ''
  graphicsPackageInfo.value = null
  graphicsPackageModalStatus.value = 'Creating graphics package...'
  showGraphicsPackageModal.value = true

  try {
    const authToken = localStorage.getItem('auth-token')
    const response = await $axios.post(
      `/episodes/${props.episodeNumber}/graphics-package`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      }
    )

    if (response.data.success) {
      graphicsPackageInfo.value = response.data
      graphicsPackageStatus.value = `Package ready: ${response.data.file_count} files (${formatFileSize(response.data.zip_size)})`

      emit('show-notification', {
        message: `Graphics package ready: ${response.data.file_count} files`,
        type: 'success'
      })
    } else {
      graphicsPackageStatus.value = 'Error: ' + (response.data.message || 'Unknown error')
    }
  } catch (error) {
    console.error('Error creating graphics package:', error)
    graphicsPackageStatus.value = 'Error: ' + (error.response?.data?.detail || error.message)
    showGraphicsPackageModal.value = false
  } finally {
    packagingGraphics.value = false
  }
}

function triggerGraphicsDownload() {
  if (!graphicsPackageInfo.value?.download_url) return

  const authToken = localStorage.getItem('auth-token')
  const baseURL = $axios.defaults.baseURL || ''
  const url = `${baseURL}${graphicsPackageInfo.value.download_url}`

  fetch(url, {
    headers: { 'Authorization': `Bearer ${authToken}` }
  })
    .then(res => {
      if (!res.ok) throw new Error('Download failed')
      return res.blob()
    })
    .then(blob => {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = graphicsPackageInfo.value.zip_filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(a.href)
    })
    .catch(err => {
      console.error('Download error:', err)
      graphicsPackageStatus.value = 'Error: Download failed'
    })
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

function getTypeColor(cueType) {
  const colors = {
    'FSQ': 'purple',
    'IMG': 'blue',
    'SOT': 'green',
    'GFX': 'orange',
    'DIR': 'grey',
    'RIF': 'cyan',
    'BUMP': 'pink',
    'STING': 'amber',
    'PKG': 'teal'
  }
  return colors[cueType?.toUpperCase()] || 'grey'
}

async function loadGeneratedDocuments() {
  if (!props.episodeNumber) {
    generatedDocuments.value = []
    return
  }

  loadingDocuments.value = true
  try {
    const authToken = localStorage.getItem('auth-token')
    const response = await $axios.get(`/scripts/episode/${props.episodeNumber}/generated`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    })

    generatedDocuments.value = response.data.documents || []
  } catch (error) {
    console.error('Error loading generated documents:', error)
    generatedDocuments.value = []
  } finally {
    loadingDocuments.value = false
  }
}

function getDocumentIcon(format) {
  const icons = {
    pdf: 'mdi-file-pdf-box',
    html: 'mdi-language-html5',
    txt: 'mdi-file-document-outline'
  }
  return icons[format] || 'mdi-file-outline'
}

function getDocumentIconColor(format) {
  const colors = {
    pdf: 'red',
    html: 'orange',
    txt: 'grey'
  }
  return colors[format] || 'grey'
}

function formatDocumentName(doc) {
  if (!doc) return ''
  let name = doc.filename
    .replace(/^\d+-/, '')
    .replace(/\.(html|pdf|txt)$/i, '')
    .replace(/-/g, ' ')

  name = name.split(' ')
    .map(word => {
      if (/^\d{4}$/.test(word) || /^\d{2}$/.test(word)) {
        return word
      }
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    })
    .join(' ')

  return name
}

function openRevisionsModal(doc) { // eslint-disable-line no-unused-vars
  selectedDocument.value = doc
  showRevisionsModal.value = true
}

function formatVersionDate(dateString) {
  if (!dateString) return 'Unknown date'
  try {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} min ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateString
  }
}

// --- watchers ---
watch(() => props.item, () => {
  autoDetectSpeaker()
})

// (documents panel removed — linked auto-open logic no longer needed)

watch(() => props.episodeNumber, (newVal) => {
  if (newVal) {
    loadGeneratedDocuments()
  }
}, { immediate: true })

// --- lifecycle ---
onMounted(() => {
  loadSpeakers()
})
</script>

<style scoped>
/* ═══════════════════════════════════════
   PANEL LAYOUT — 3-Zone Flex Column
   ═══════════════════════════════════════ */
.metadata-panel {
  max-height: 100vh;
  border-left: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex-shrink: 0; /* Never shrink - maintain width regardless of editor content */
  position: sticky !important;
  top: 0 !important;
  z-index: 15 !important;
  align-self: flex-start;
  margin-left: 4px;
}

.metadata-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.sidebar-status-bar {
  height: 4px;
  flex-shrink: 0;
  background-color: #000000;
}

.sidebar-status-bar.needs-attention-throb {
  animation: attention-throb 1.2s ease-in-out infinite;
}

@keyframes attention-throb {
  0%, 100% { background-color: #d32f2f; }
  50% { background-color: #f44336; box-shadow: 0 0 6px rgba(244, 67, 54, 0.5); }
}

/* Zone A — Always visible, never compressed */
.zone-a {
  flex-shrink: 0;
}

.save-header-btn {
  flex-shrink: 0;
  border-radius: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  height: 48px !important;
  max-height: 48px !important;
  min-height: 48px !important;
  font-size: 0.75rem !important;
  letter-spacing: 0.5px !important;
}

.zone-a-fields {
  padding: 4px 8px !important;
}

/* Zone C — Asset Pool (below fields, above collapsibles) */
.zone-c {
  flex: 1;
  min-height: 150px;
  overflow: hidden;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

/* Zone B — Collapsible, fills remaining space, scrollable */
.zone-b {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

/* ═══════════════════════════════════════
   EXPANSION PANEL — Compact Styling
   ═══════════════════════════════════════ */
.compact-panel-title {
  min-height: 32px !important;
  padding: 0 12px !important;
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.3px !important;
}

:deep(.v-expansion-panel-title) {
  min-height: 32px !important;
  padding: 0 12px !important;
}

:deep(.v-expansion-panel-title__overlay) {
  opacity: 0 !important;
}

:deep(.v-expansion-panel-text__wrapper) {
  padding: 4px 8px 8px !important;
}

:deep(.v-expansion-panel) {
  border-radius: 0 !important;
}

:deep(.v-expansion-panel::after) {
  display: none !important;
}

:deep(.v-expansion-panels) {
  gap: 0 !important;
}

:deep(.v-expansion-panel--active > .v-expansion-panel-title) {
  min-height: 32px !important;
}

/* ═══════════════════════════════════════
   SLUG HEADER & ASSET ID
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   COMPACT FIELDS
   ═══════════════════════════════════════ */
.compact-field {
  margin-bottom: 1px !important;
}

.compact-field-tight {
  margin-bottom: 0px !important;
}

.sidebar-field {
  margin-bottom: 0px !important;
}

/* Tone badge field */
.priority-field {
  border: none;
  padding: 2px 6px 2px 6px;
}

.priority-label {
  display: block;
  font-size: 0.6rem !important;
  font-weight: 500;
  margin-bottom: 1px;
  letter-spacing: 0.3px;
  line-height: 1;
}

.priority-badge {
  font-weight: 600;
  letter-spacing: 0.3px;
  text-transform: lowercase;
}

.priority-input :deep(.v-field__input) {
  font-size: 0.65rem !important;
  min-height: 14px !important;
  padding: 0 4px !important;
}

.tone-field {
  border: none;
  padding: 2px 6px 2px 6px;
}

/* Script flyout sub-buttons */
.script-flyout {
  border-left: 2px solid rgba(0, 0, 0, 0.1);
  padding-left: 6px;
  margin-bottom: 4px;
}
.script-flyout-btn {
  justify-content: flex-start !important;
  text-transform: none !important;
  font-size: 0.75rem !important;
  min-height: 26px !important;
  height: 26px !important;
}
.script-flyout-btn :deep(.v-btn__content) {
  justify-content: flex-start !important;
}

.rotate-90 {
  transform: rotate(90deg);
  transition: transform 0.2s;
}

/* Workflow Tools buttons — left-align text */
.asset-generation-buttons :deep(.v-btn) {
  justify-content: flex-start !important;
  text-align: left !important;
}
.asset-generation-buttons :deep(.v-btn__content) {
  justify-content: flex-start !important;
}

.tone-label {
  display: block;
  font-size: 0.6rem !important;
  font-weight: 500;
  margin-bottom: 1px;
  letter-spacing: 0.3px;
  line-height: 1;
}

.add-tone-btn {
  cursor: pointer !important;
  font-weight: 600 !important;
  letter-spacing: 0.4px !important;
  text-transform: uppercase;
}

.add-tone-option {
  cursor: pointer !important;
}

.add-tone-card {
  border-radius: 6px;
}

.tone-badge {
  font-weight: 600;
  letter-spacing: 0.3px;
  text-transform: lowercase;
}

.tone-input :deep(.v-field__input) {
  font-size: 0.65rem !important;
  min-height: 14px !important;
  padding: 0 4px !important;
}

.tone-rationale-text {
  font-size: 0.55rem;
  line-height: 1.3;
  color: var(--llm-indicator-text, #7e57c2);
  font-style: italic;
  padding: 0 6px;
  word-wrap: break-word;
}

/* LLM-generated field highlight — applied by a single programmatic scanner
   on the MetadataPanel root, so no per-field wiring is needed. Purple to
   match the Claude/robot color used elsewhere in the app. */
:deep(.sidebar-field.llm-generated),
.sidebar-description-raw.llm-generated {
  border: 1.5px solid var(--llm-indicator-border, #7e57c2) !important;
  border-radius: 4px;
}

/* Tone field: no border when LLM-generated — chips handle the color instead */
.tone-field.llm-generated {
  border: none !important;
}

:deep(.sidebar-field.llm-generated input),
:deep(.sidebar-field.llm-generated textarea),
:deep(.sidebar-field.llm-generated .v-field__input),
:deep(.sidebar-field.llm-generated .v-select__selection-text),
.sidebar-description-raw.llm-generated {
  color: var(--llm-indicator-text, #7e57c2) !important;
  font-style: italic;
}
:deep(.sidebar-field .v-field) {
  --v-field-padding-start: 4px;
  --v-field-padding-end: 4px;
}
:deep(.sidebar-field .v-field__input) {
  font-size: 0.8rem !important;
  padding: 2px 4px !important;
  min-height: 24px !important;
}
:deep(.sidebar-field textarea) {
  font-size: 0.8rem !important;
  padding: 2px 4px !important;
  line-height: 1.4 !important;
}

/* Plain description textarea — bypasses Vuetify entirely for reliable auto-resize */
.sidebar-description-raw {
  width: 100%;
  font-size: 0.8rem;
  line-height: 1.4;
  padding: 6px 4px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  background: transparent;
  color: inherit;
  font-family: inherit;
  resize: none;
  overflow: hidden;
  min-height: 36px;
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.2s;
}
.sidebar-description-raw:focus {
  border-color: #1976d2;
}
.sidebar-description-raw::placeholder {
  font-size: 0.75rem;
  color: #9e9e9e;
}

.description-wrapper {
  position: relative;
}

.mr-half {
  margin-right: 2px;
}

.desc-actions-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  margin-top: 0px;
  margin-bottom: 6px;
}

.desc-model-label {
  font-size: 0.5rem;
  color: var(--llm-indicator-text, #7e57c2);
  opacity: 0.7;
  letter-spacing: 0.2px;
  margin-right: auto;
  line-height: 1;
}

.desc-action-btn {
  text-transform: none !important;
  font-size: 0.55rem !important;
  height: 16px !important;
  padding: 0 4px !important;
  min-width: 0 !important;
  border-radius: 3px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.desc-action-btn.regen-color {
  background-color: var(--llm-indicator-text, #7e57c2) !important;
  color: white !important;
}

.auto-desc-on {
  background-color: var(--llm-indicator-text, #7e57c2) !important;
  color: white !important;
}

.auto-desc-off {
  background-color: #e0e0e0 !important;
  color: #999 !important;
}

.regen-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--llm-indicator-overlay, rgba(126, 87, 194, 0.85));
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  z-index: 2;
}

.regen-overlay-text {
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.current-desc-preview {
  font-size: 0.78rem;
  line-height: 1.4;
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.08);
  max-height: 120px;
  overflow-y: auto;
  color: #555;
}
:deep(.sidebar-field .v-field-label) {
  font-size: 0.75rem !important;
}
:deep(.sidebar-field .v-select__selection) {
  font-size: 0.8rem !important;
}
:deep(.sidebar-field input::placeholder),
:deep(.sidebar-field textarea::placeholder) {
  font-size: 0.75rem !important;
  color: #9e9e9e !important;
}

.asset-id-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 0;
}
.asset-id-label {
  font-size: 9px;
  color: #9e9e9e;
  font-weight: 600;
  text-transform: uppercase;
}
.asset-id-value {
  font-size: 9px;
  font-family: 'Roboto Mono', monospace;
  color: #616161;
  letter-spacing: 0.3px;
}
.asset-id-copy {
  cursor: pointer;
  color: #bdbdbd;
  margin-left: 2px;
}
.asset-id-copy:hover {
  color: #1976D2;
}

/* Duration pulled inline with the ID at the top-right of Segment Info */
.duration-inline {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  font-family: 'Roboto Mono', monospace;
  color: #616161;
  font-weight: 500;
  letter-spacing: 0.3px;
}
.duration-inline-icon {
  color: #9e9e9e;
}

/* Always-expanded Segment Info block (replaces the old expansion-panel) */
.segment-info-block {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
  flex-shrink: 0;
}
.segment-info-header {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  background: #1976D2;            /* default blue, overridden by inline style */
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  font-weight: 500;
  font-size: 0.85rem;
  color: #ffffff;
}
.segment-info-header :deep(.v-icon) {
  color: #ffffff;
}
.segment-info-title {
  font-size: 0.85rem;
  font-weight: 500;
}
.segment-info-body {
  padding: 8px 12px 10px;
}

.inline-field {
  flex: 1;
  margin-bottom: 0 !important;
  min-width: 0;
}

.duration-priority-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.duration-field {
  flex: 1.2 !important;
  max-width: 140px;
}

.priority-field {
  flex: 1 !important;
  max-width: none;
}

/* Removed aggressive global field overrides — using Vuetify solo-filled variant */

/* Legacy compact-field styles kept for any remaining usage */

/* ═══════════════════════════════════════
   SPEAKER WPM DISPLAY
   ═══════════════════════════════════════ */
.speaker-wpm-display {
  margin-top: 8px;
}

.speaker-wpm-display .v-card {
  border-radius: 4px;
}

.speaker-wpm-display .text-caption {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.8;
}

.speaker-wpm-display .text-h6 {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.2;
}

.speaker-wpm-display .text-body-2 {
  font-size: 0.8rem;
  font-weight: 600;
}

/* ═══════════════════════════════════════
   TAB CONTROLS
   ═══════════════════════════════════════ */
.tab-controls-left {
  position: absolute;
  left: -32px;
  top: 50vh;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 1000;
}

.tab-btn {
  border-radius: 8px 0 0 8px !important;
  background-color: rgba(25, 118, 210, 0.9) !important;
  color: white !important;
  box-shadow: -2px 2px 8px rgba(0, 0, 0, 0.3) !important;
  transition: all 0.2s ease !important;
  width: 32px !important;
  height: 40px !important;
}

.tab-btn:hover {
  background-color: rgba(25, 118, 210, 1) !important;
  transform: translateX(-4px) !important;
  box-shadow: -4px 4px 12px rgba(0, 0, 0, 0.4) !important;
}

.tab-btn .v-icon {
  color: white !important;
}

/* ═══════════════════════════════════════
   DOCUMENTS & VERSIONS
   ═══════════════════════════════════════ */
.document-list {
  background: transparent !important;
}

.document-item {
  border-radius: 4px;
  margin-bottom: 2px;
}

.document-item:hover {
  background: rgba(var(--v-theme-primary), 0.08);
}

.document-item .v-list-item-title {
  font-weight: 500;
}

.document-item .v-list-item-subtitle {
  font-size: 0.65rem !important;
  opacity: 0.7;
}

.revision-badge {
  display: inline-block;
  font-size: 0.6rem;
  font-weight: 600;
  padding: 1px 4px;
  margin-left: 6px;
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
  border-radius: 3px;
  vertical-align: middle;
}

.past-revisions-link {
  font-size: 0.6rem;
  color: #888;
  text-decoration: none;
  white-space: nowrap;
}

.past-revisions-link:hover {
  color: rgb(var(--v-theme-primary));
  text-decoration: underline;
}

.revision-list-item {
  min-height: 48px !important;
}

.document-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.document-actions .v-btn {
  font-size: 0.65rem !important;
}

.gather-results-list {
  max-height: 200px;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
}

.gather-results-list.error-list {
  background: rgba(244, 67, 54, 0.05);
}

.gather-results-list .v-list-item {
  min-height: 32px !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.gather-results-list .v-list-item:last-child {
  border-bottom: none;
}

.version-list {
  background: transparent !important;
  max-height: 250px;
  overflow-y: auto;
}

.version-item {
  background: #f5f5f5;
  border-radius: 4px;
  margin-bottom: 4px;
  min-height: 40px !important;
}

.version-item.current-version {
  background: rgba(var(--v-theme-primary), 0.08);
}

.version-item:hover {
  background: rgba(var(--v-theme-primary), 0.12);
}

.version-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ═══════════════════════════════════════
   NARROW MODE
   ═══════════════════════════════════════ */
.metadata-panel.narrow .zone-a-fields {
  padding: 4px 6px !important;
}

.metadata-panel.narrow .compact-panel-title {
  font-size: 0.65rem !important;
  padding: 0 8px !important;
}
.metadata-panels-draggable {
  display: flex;
  flex-direction: column;
}
.draggable-panel-wrapper {
  margin-bottom: 0;
}
.panel-ghost {
  opacity: 0.4;
  background: rgba(25, 118, 210, 0.1);
}
.panel-drag-handle {
  opacity: 0.3;
  transition: opacity 0.2s;
}
.panel-drag-handle:hover {
  opacity: 0.8;
}
</style>
