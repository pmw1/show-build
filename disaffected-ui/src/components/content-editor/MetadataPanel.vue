<template>
  <div
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

              <!-- Segment Info -->
              <v-expansion-panels v-if="element.key === 'segmentinfo' && item" v-model="expandedPanels" multiple>
                <v-expansion-panel value="segmentinfo">
                  <v-expansion-panel-title class="compact-panel-title">
                    <v-icon size="x-small" class="panel-drag-handle mr-1" style="cursor: grab;">mdi-drag-horizontal-variant</v-icon>
                    <v-icon size="small" class="mr-1">mdi-information-outline</v-icon>
                    Segment Info
                    <template v-slot:actions="{ expanded }">
                      <v-chip v-if="!expanded && item.slug" size="x-small" variant="tonal" color="primary" class="ml-1">{{ item.slug }}</v-chip>
                      <v-icon :icon="expanded ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
                    </template>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <div v-if="item.asset_id || item.id" class="asset-id-row mb-1">
                      <span class="asset-id-label">ID:</span>
                      <span class="asset-id-value">{{ item.asset_id || item.id }}</span>
                      <v-icon size="10" class="asset-id-copy" @click="copyToClipboard(item.asset_id || item.id)">mdi-content-copy</v-icon>
                    </div>
                    <v-text-field :placeholder="slugPlaceholder" :model-value="item.slug || ''" @update:model-value="$emit('update-segment-field', { field: 'slug', value: $event })" variant="underlined" density="compact" hide-details class="sidebar-field mb-1" :color="segmentTypeColor" />
                    <v-text-field :placeholder="titlePlaceholder" :model-value="item.title || ''" @update:model-value="$emit('update-segment-field', { field: 'title', value: $event })" variant="underlined" density="compact" hide-details class="sidebar-field mb-1" :color="segmentTypeColor" />
                    <div class="d-flex ga-2 mb-1">
                      <v-text-field :placeholder="durationPlaceholder" :model-value="item.duration || ''" readonly variant="underlined" density="compact" hide-details class="sidebar-field" style="flex: 1.2;" :color="segmentTypeColor" />
                      <v-select placeholder="Priority" :model-value="item.priority || 'normal'" :items="priorityOptions" @update:model-value="$emit('update-segment-field', { field: 'priority', value: $event })" variant="underlined" density="compact" hide-details class="sidebar-field" style="flex: 1;" :color="segmentTypeColor" />
                    </div>
                    <v-textarea :placeholder="descriptionPlaceholder" :model-value="item.description || ''" @update:model-value="$emit('update-segment-field', { field: 'description', value: $event })" variant="underlined" density="compact" hide-details rows="2" no-resize class="sidebar-field mb-1" :color="segmentTypeColor" />
                    <v-text-field v-if="item.type === 'ad'" :placeholder="!item.customer ? 'Name of the advertiser or sponsor' : 'Customer'" :model-value="item.customer || ''" @update:model-value="$emit('update-segment-field', { field: 'customer', value: $event })" variant="underlined" density="compact" hide-details class="sidebar-field" :color="segmentTypeColor" />
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

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
                    <AssetPoolPanel :episode-number="episodeNumber" :rundown-items="rundownItems" :panel-width="panelWidth" @place-item="$emit('place-library-item', $event)" @create-new-item="$emit('create-new-library-item', $event)" />
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
                      <v-list-item v-for="(version, idx) in versionHistory.slice(0, 10)" :key="version.version_number" class="version-item px-2" :class="{ 'current-version': idx === 0 }">
                        <template v-slot:prepend><v-chip size="x-small" :color="idx === 0 ? 'primary' : 'grey'" class="mr-2">v{{ version.version_number }}</v-chip></template>
                        <v-list-item-title class="text-body-2">{{ formatVersionDate(version.created_at) }}</v-list-item-title>
                        <v-list-item-subtitle class="text-caption">{{ version.content_length || 0 }} chars<span v-if="version.created_by"> &bull; {{ version.created_by }}</span></v-list-item-subtitle>
                        <template v-slot:append>
                          <v-btn v-if="idx > 0" icon size="x-small" variant="text" color="primary" @click="$emit('restore-version', version.version_number)"><v-icon size="small">mdi-restore</v-icon><v-tooltip activator="parent" location="left">Restore this version</v-tooltip></v-btn>
                          <v-chip v-else size="x-small" color="success" variant="tonal">Current</v-chip>
                        </template>
                      </v-list-item>
                    </v-list>
                    <div v-if="versionHistory.length > 10" class="text-caption text-grey text-center mt-1">Showing 10 of {{ versionHistory.length }} versions</div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <!-- Asset Generation -->
              <v-expansion-panels v-if="element.key === 'assetgen' && episodeNumber" v-model="expandedPanels" multiple>
                <v-expansion-panel value="assetgen">
                  <v-expansion-panel-title class="compact-panel-title">
                    <v-icon size="x-small" class="panel-drag-handle mr-1" style="cursor: grab;">mdi-drag-horizontal-variant</v-icon>
                    <v-icon size="small" class="mr-1">mdi-image-multiple</v-icon>
                    Asset Generation
                    <template v-slot:actions="{ expanded }">
                      <v-icon :icon="expanded ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
                    </template>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <div class="asset-generation-buttons">
                      <v-btn size="small" variant="tonal" color="amber-darken-2" :loading="regeneratingFSQ" :disabled="regeneratingFSQ" @click="regenerateAllFSQ" class="mb-2" block><v-icon left size="small">mdi-format-quote-close</v-icon> Regenerate All Quotes</v-btn>
                      <div v-if="fsqRegenerationStatus" class="text-caption mt-1" :class="fsqRegenerationStatus.includes('Error') ? 'text-error' : 'text-success'">{{ fsqRegenerationStatus }}</div>
                      <v-btn size="small" variant="tonal" color="blue-darken-2" :loading="enumeratingCues" :disabled="enumeratingCues" @click="enumerateCueBlocks" class="mb-2 mt-2" block><v-icon left size="small">mdi-format-list-numbered</v-icon> Enumerate Cue Blocks</v-btn>
                      <div v-if="enumerationStatus" class="text-caption mt-1" :class="enumerationStatus.includes('Error') ? 'text-error' : 'text-success'">{{ enumerationStatus }}</div>
                      <v-btn size="small" variant="tonal" color="teal-darken-2" :loading="gatheringMedia" :disabled="gatheringMedia" @click="gatherForShow" class="mb-2 mt-2" block><v-icon left size="small">mdi-folder-download</v-icon> Gather for Show</v-btn>
                      <v-progress-linear v-if="gatheringMedia && gatherProgress > 0" :model-value="gatherProgress" color="teal" height="6" class="mt-1 mb-1" />
                      <div v-if="gatherStatus" class="text-caption mt-1" :class="gatherStatus.includes('Error') ? 'text-error' : 'text-success'">{{ gatherStatus }}<v-btn v-if="gatherResults" size="x-small" variant="text" color="primary" @click="showGatherResultsModal = true" class="ml-1">Details</v-btn></div>
                      <v-btn size="small" variant="tonal" color="deep-purple-darken-1" :loading="packagingGraphics" :disabled="packagingGraphics" @click="downloadGraphicsPackage" class="mb-2 mt-2" block><v-icon left size="small">mdi-package-down</v-icon> Download Graphics Package</v-btn>
                      <div v-if="graphicsPackageStatus" class="text-caption mt-1" :class="graphicsPackageStatus.includes('Error') ? 'text-error' : 'text-success'">{{ graphicsPackageStatus }}</div>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <!-- Documents -->
              <v-expansion-panels v-if="element.key === 'documents' && episodeNumber" v-model="expandedPanels" multiple>
                <v-expansion-panel value="documents">
                  <v-expansion-panel-title class="compact-panel-title">
                    <v-icon size="x-small" class="panel-drag-handle mr-1" style="cursor: grab;">mdi-drag-horizontal-variant</v-icon>
                    <v-icon size="small" class="mr-1">mdi-file-document-multiple-outline</v-icon>
                    Documents
                    <template v-slot:actions="{ expanded }">
                      <v-chip v-if="!expanded && generatedDocuments.length > 0" size="x-small" variant="tonal" color="secondary" class="ml-1">{{ generatedDocuments.length }}</v-chip>
                      <v-icon :icon="expanded ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
                    </template>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <div v-if="loadingDocuments" class="text-center py-2"><v-progress-circular indeterminate size="20" width="2" color="primary" /></div>
                    <div v-else-if="generatedDocuments.length === 0" class="text-center py-2">
                      <p class="text-caption text-grey">No generated documents yet</p>
                      <v-btn size="x-small" variant="text" color="primary" @click="$emit('generate-host-script')"><v-icon left size="small">mdi-plus</v-icon> Generate Host Script</v-btn>
                    </div>
                    <v-list v-else density="compact" class="document-list pa-0">
                      <v-list-item v-for="doc in generatedDocuments" :key="doc.filename" :href="doc.url" target="_blank" class="document-item px-2">
                        <template v-slot:prepend><v-icon :color="getDocumentIconColor(doc.format)" size="small">{{ getDocumentIcon(doc.format) }}</v-icon></template>
                        <v-list-item-title class="text-body-2">{{ formatDocumentName(doc) }}<span v-if="doc.revision" class="revision-badge">R{{ doc.revision }}</span></v-list-item-title>
                        <v-list-item-subtitle class="text-caption d-flex align-center">
                          <span>{{ doc.size_formatted }} &bull; {{ doc.modified_formatted }}</span>
                          <a v-if="doc.pastRevisions && doc.pastRevisions.length > 0" href="#" class="past-revisions-link ml-2" @click.prevent.stop="openRevisionsModal(doc)">past revisions ({{ doc.pastRevisions.length }})</a>
                        </v-list-item-subtitle>
                        <template v-slot:append><v-btn icon size="x-small" variant="text" :href="doc.url" target="_blank" @click.stop><v-icon size="small">mdi-open-in-new</v-icon></v-btn></template>
                      </v-list-item>
                    </v-list>
                    <div class="document-actions mt-2">
                      <v-btn size="x-small" variant="tonal" color="success" class="mr-1" @click="$emit('generate-host-script')" :loading="hostScriptLoading"><v-icon left size="small">mdi-script-text-outline</v-icon> Host Script</v-btn>
                      <v-btn size="x-small" variant="tonal" color="primary" class="mr-1" @click="$emit('generate-media-list')" :loading="mediaListLoading"><v-icon left size="small">mdi-playlist-play</v-icon> Media List</v-btn>
                      <v-btn size="x-small" variant="tonal" color="secondary" class="mr-1" @click="$emit('generate-prompter-files')" disabled><v-icon left size="small">mdi-script-text</v-icon> Prompter<v-tooltip activator="parent" location="bottom">Coming Soon</v-tooltip></v-btn>
                      <v-btn size="x-small" variant="text" color="primary" @click="loadGeneratedDocuments" :loading="loadingDocuments"><v-icon size="small">mdi-refresh</v-icon></v-btn>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

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

<script>
import { themeColorMap, getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'
import AssetPoolPanel from './AssetPoolPanel.vue'
import draggable from 'vuedraggable'

export default {
  name: 'MetadataPanel',
  components: {
    AssetPoolPanel,
    draggable
  },
  emits: [
    'close',
    'toggle-width',
    'update-field',
    'save-all',
    'open-wpm-tool',
    'generate-host-script',
    'generate-media-list',
    'generate-prompter-files',
    'refresh-rundown',
    'show-notification',
    'restore-version',
    'place-library-item',
    'create-new-library-item',
    'update-segment-field'
  ],
  props: {
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
  },
  data() {
    return {
      expandedPanels: ['segmentinfo'],
      panelOrder: [
        { key: 'segmentinfo' },
        { key: 'assetpool' },
        { key: 'people' },
        { key: 'speaker' },
        { key: 'versions' },
        { key: 'assetgen' },
        { key: 'documents' }
      ],
      statusOptions: [
        'draft',
        'approved',
        'production',
        'completed'
      ],
      priorityOptions: [
        'low',
        'normal',
        'high',
        'urgent'
      ],
      speakers: [],
      loadingSpeakers: false,
      generatedDocuments: [],
      loadingDocuments: false,
      regeneratingFSQ: false,
      fsqRegenerationStatus: '',
      enumeratingCues: false,
      enumerationStatus: '',
      gatheringMedia: false,
      gatherProgress: 0,
      gatherStatus: '',
      gatherResults: null,
      showGatherResultsModal: false,
      packagingGraphics: false,
      graphicsPackageStatus: '',
      graphicsPackageInfo: null,
      graphicsPackageModalStatus: '',
      showGraphicsPackageModal: false,
      showRevisionsModal: false,
      selectedDocument: null
    }
  },
  watch: {
    item: {
      handler() {
        this.autoDetectSpeaker()
      }
    },
    expandedPanels: {
      handler(newVal, oldVal) {
        // Link assetgen and documents — opening one opens the other
        const had = (arr, v) => arr && arr.includes(v)
        const has = (v) => newVal && newVal.includes(v)
        const assetgenJustOpened = has('assetgen') && !had(oldVal, 'assetgen')
        const documentsJustOpened = has('documents') && !had(oldVal, 'documents')
        const assetgenJustClosed = !has('assetgen') && had(oldVal, 'assetgen')
        const documentsJustClosed = !has('documents') && had(oldVal, 'documents')
        if (assetgenJustOpened && !has('documents')) {
          this.expandedPanels = [...newVal, 'documents']
        } else if (documentsJustOpened && !has('assetgen')) {
          this.expandedPanels = [...newVal, 'assetgen']
        } else if (assetgenJustClosed && has('documents')) {
          this.expandedPanels = newVal.filter(v => v !== 'documents')
        } else if (documentsJustClosed && has('assetgen')) {
          this.expandedPanels = newVal.filter(v => v !== 'assetgen')
        }
      }
    },
    episodeNumber: {
      handler(newVal) {
        if (newVal) {
          this.loadGeneratedDocuments()
        }
      },
      immediate: true
    }
  },
  mounted() {
    this.loadSpeakers()
  },
  computed: {
    panelWidthValue() {
      return this.panelWidth === 'narrow' ? '330px' : '440px'
    },
    panelHeightValue() {
      return this.panelHeight ? `${this.panelHeight}px` : '100vh'
    },

    itemHeaderStyle() {
      if (!this.item) {
        return {
          backgroundColor: '#f5f5f5',
          color: '#666'
        }
      }

      const itemType = this.item.type || 'segment'
      const colorValue = getColorValue(itemType.toLowerCase()) || 'grey'
      const backgroundColor = resolveVuetifyColor(colorValue)
      const colorMapping = themeColorMap[itemType] || themeColorMap.unknown
      const textColor = colorMapping.textColor || '#ffffff'

      return {
        backgroundColor: backgroundColor,
        color: textColor
      }
    },

    statusThemeColors() {
      if (!this.item) {
        return {
          primary: '#e3f2fd',
          border: '#90caf9',
          accent: '#1976d2'
        }
      }

      const status = this.item.status || 'draft'
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
    },

    currentItemNeedsAttention() {
      const content = this.item?.script || this.item?.script_content
      if (!content) return false
      return content.includes('data-needs-attention="true"') || /NeedsAttention:\s*true/i.test(content)
    },

    segmentTypeColor() {
      if (!this.item) return undefined
      const itemType = this.item.type || 'segment'
      return resolveVuetifyColor(getColorValue(itemType.toLowerCase()) || 'grey')
    },

    slugPlaceholder() {
      if (!this.item) return 'Slug'
      const slug = this.item.slug || ''
      return /^Segment-\d+$/i.test(slug) || !slug ? 'Enter a descriptive slug' : 'Slug'
    },

    titlePlaceholder() {
      if (!this.item) return 'Title'
      const title = this.item.title || ''
      return /^Segment-\d+$/i.test(title) || !title ? 'Give this segment a title' : 'Title'
    },

    durationPlaceholder() {
      if (!this.item) return 'Duration'
      return !this.item.duration || this.item.duration === '00:00:00' ? 'Expected duration (HH:MM:SS)' : 'Duration'
    },

    descriptionPlaceholder() {
      if (!this.item) return 'Description'
      return !this.item.description ? 'Type the segment\'s short description' : 'Description'
    },

    selectedSpeaker() {
      if (!this.item?.speaker_id || !this.speakers.length) {
        return null
      }
      return this.speakers.find(s => s.id === this.item.speaker_id)
    }
  },
  methods: {
    copyToClipboard(text) {
      navigator.clipboard.writeText(text).catch(() => {})
    },
    updateField(fieldName, value) {
      this.$emit('update-field', { field: fieldName, value: value })
    },
    resetFields() {
      this.$emit('reset-fields')
    },
    async loadSpeakers() {
      this.loadingSpeakers = true
      try {
        const authToken = localStorage.getItem('auth-token')
        const response = await this.$axios.get('/speakers/', {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        })

        if (response.data.success) {
          this.speakers = response.data.data
          this.autoDetectSpeaker()
        }
      } catch (error) {
        console.error('Error loading speakers:', error)
      } finally {
        this.loadingSpeakers = false
      }
    },

    autoDetectSpeaker() {
      if (!this.item || this.item.speaker_id || !this.speakers.length) return
      const content = this.item.script_content || this.item.script || ''
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
      const match = this.speakers.find(s => s.name.toLowerCase() === dominant)
      if (match) {
        this.$emit('update-field', { field: 'speaker_id', value: match.id })
      }
    },

    async regenerateAllFSQ() {
      if (!this.episodeNumber) {
        this.fsqRegenerationStatus = 'Error: No episode selected'
        return
      }

      this.regeneratingFSQ = true
      this.fsqRegenerationStatus = ''

      try {
        const authToken = localStorage.getItem('auth-token')
        const response = await this.$axios.post(
          `/fsq/regenerate-all/${this.episodeNumber}`,
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
          this.fsqRegenerationStatus = `Generated: ${generated}/${total_fsqs}, Skipped: ${skipped}, Failed: ${failed}`
        } else {
          this.fsqRegenerationStatus = 'Error: ' + (response.data.message || 'Unknown error')
        }
      } catch (error) {
        console.error('Error regenerating FSQ assets:', error)
        this.fsqRegenerationStatus = 'Error: ' + (error.response?.data?.detail || error.message)
      } finally {
        this.regeneratingFSQ = false
      }
    },

    async enumerateCueBlocks() {
      if (!this.episodeNumber) {
        this.enumerationStatus = 'Error: No episode selected'
        return
      }

      this.enumeratingCues = true
      this.enumerationStatus = ''

      try {
        const authToken = localStorage.getItem('auth-token')
        const response = await this.$axios.post(
          `/episodes/${this.episodeNumber}/enumerate-cues`,
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
          this.enumerationStatus = status
          this.$emit('refresh-rundown')
        } else {
          this.enumerationStatus = 'Error: ' + (response.data.message || 'Unknown error')
        }
      } catch (error) {
        console.error('Error enumerating cue blocks:', error)
        this.enumerationStatus = 'Error: ' + (error.response?.data?.detail || error.message)
      } finally {
        this.enumeratingCues = false
      }
    },

    async gatherForShow() {
      if (!this.episodeNumber) {
        this.gatherStatus = 'Error: No episode selected'
        return
      }

      this.gatheringMedia = true
      this.gatherProgress = 0
      this.gatherStatus = 'Gathering media files...'
      this.gatherResults = null

      try {
        const authToken = localStorage.getItem('auth-token')
        const response = await this.$axios.post(
          `/episodes/${this.episodeNumber}/gather-media`,
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
          this.gatherProgress = 100
          this.gatherStatus = `Gathered: ${copied}/${total} files, ${skipped} skipped, ${failed} failed`
          this.gatherResults = response.data

          if (failed > 0) {
            this.showGatherResultsModal = true
          }

          this.$emit('show-notification', {
            message: `Media gather complete: ${copied} files copied to media-list`,
            type: failed > 0 ? 'warning' : 'success'
          })
        } else {
          this.gatherStatus = 'Error: ' + (response.data.message || 'Unknown error')
        }
      } catch (error) {
        console.error('Error gathering media:', error)
        this.gatherStatus = 'Error: ' + (error.response?.data?.detail || error.message)
      } finally {
        this.gatheringMedia = false
      }
    },

    async downloadGraphicsPackage() {
      if (!this.episodeNumber) {
        this.graphicsPackageStatus = 'Error: No episode selected'
        return
      }

      this.packagingGraphics = true
      this.graphicsPackageStatus = ''
      this.graphicsPackageInfo = null
      this.graphicsPackageModalStatus = 'Creating graphics package...'
      this.showGraphicsPackageModal = true

      try {
        const authToken = localStorage.getItem('auth-token')
        const response = await this.$axios.post(
          `/episodes/${this.episodeNumber}/graphics-package`,
          {},
          {
            headers: {
              'Authorization': `Bearer ${authToken}`,
              'Content-Type': 'application/json'
            }
          }
        )

        if (response.data.success) {
          this.graphicsPackageInfo = response.data
          this.graphicsPackageStatus = `Package ready: ${response.data.file_count} files (${this.formatFileSize(response.data.zip_size)})`

          this.$emit('show-notification', {
            message: `Graphics package ready: ${response.data.file_count} files`,
            type: 'success'
          })
        } else {
          this.graphicsPackageStatus = 'Error: ' + (response.data.message || 'Unknown error')
        }
      } catch (error) {
        console.error('Error creating graphics package:', error)
        this.graphicsPackageStatus = 'Error: ' + (error.response?.data?.detail || error.message)
        this.showGraphicsPackageModal = false
      } finally {
        this.packagingGraphics = false
      }
    },

    triggerGraphicsDownload() {
      if (!this.graphicsPackageInfo?.download_url) return

      const authToken = localStorage.getItem('auth-token')
      const baseURL = this.$axios.defaults.baseURL || ''
      const url = `${baseURL}${this.graphicsPackageInfo.download_url}`

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
          a.download = this.graphicsPackageInfo.zip_filename
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          URL.revokeObjectURL(a.href)
        })
        .catch(err => {
          console.error('Download error:', err)
          this.graphicsPackageStatus = 'Error: Download failed'
        })
    },

    formatFileSize(bytes) {
      if (!bytes || bytes === 0) return '0 B'
      const units = ['B', 'KB', 'MB', 'GB']
      let i = 0
      let size = bytes
      while (size >= 1024 && i < units.length - 1) {
        size /= 1024
        i++
      }
      return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
    },

    getTypeColor(cueType) {
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
    },

    async loadGeneratedDocuments() {
      if (!this.episodeNumber) {
        this.generatedDocuments = []
        return
      }

      this.loadingDocuments = true
      try {
        const authToken = localStorage.getItem('auth-token')
        const response = await this.$axios.get(`/scripts/episode/${this.episodeNumber}/generated`, {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        })

        this.generatedDocuments = response.data.documents || []
      } catch (error) {
        console.error('Error loading generated documents:', error)
        this.generatedDocuments = []
      } finally {
        this.loadingDocuments = false
      }
    },

    getDocumentIcon(format) {
      const icons = {
        pdf: 'mdi-file-pdf-box',
        html: 'mdi-language-html5',
        txt: 'mdi-file-document-outline'
      }
      return icons[format] || 'mdi-file-outline'
    },

    getDocumentIconColor(format) {
      const colors = {
        pdf: 'red',
        html: 'orange',
        txt: 'grey'
      }
      return colors[format] || 'grey'
    },

    formatDocumentName(doc) {
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
    },

    openRevisionsModal(doc) {
      this.selectedDocument = doc
      this.showRevisionsModal = true
    },

    formatVersionDate(dateString) {
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
  }
}
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
