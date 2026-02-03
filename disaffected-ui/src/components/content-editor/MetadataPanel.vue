<template>
  <div
    :class="['metadata-panel', panelWidth === 'narrow' ? 'narrow' : 'wide']"
    :style="{ width: panelWidthValue }"
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
      <!-- Slug Header -->
      <div v-if="item && item.slug" class="slug-header" :class="saveState?.hasChanges ? 'has-changes' : 'saved'">
        {{ item.slug }}
      </div>

      <!-- AssetID Display -->
      <div v-if="item && (item.asset_id || item.id)" class="asset-id-row">
        <span class="asset-id-label">AssetID:</span>
        <span class="asset-id-value">{{ item.asset_id || item.id }}</span>
        <v-btn
          icon
          size="x-small"
          variant="text"
          class="copy-btn"
          @click="copyAssetId"
        >
          <v-icon size="small">mdi-content-copy</v-icon>
          <v-tooltip activator="parent" location="top">Copy AssetID</v-tooltip>
        </v-btn>
        <span v-if="assetIdCopied" class="copied-indicator">Copied!</span>
      </div>

      <!-- Metadata Content -->
      <v-card-text class="pa-2 metadata-content">
        <div v-if="!item" class="text-center py-8">
          <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-information-outline</v-icon>
          <p class="text-h6 text-grey-lighten-1">No Item Selected</p>
          <p class="text-caption text-grey">Select a rundown item to view metadata</p>
        </div>

        <div v-else class="metadata-fields">
          <!-- Primary Information -->
          <div class="metadata-section mb-3">
            <h4 class="section-title">Primary Information</h4>

            <!-- 1. Slug at top position -->
            <v-text-field
              label="Slug"
              :model-value="item.slug || ''"
              @update:model-value="updateField('slug', $event)"
              variant="outlined"
              density="compact"
              class="compact-field-tight status-themed-field"
            />

            <!-- 2. Title in 2nd position -->
            <v-text-field
              label="Title"
              :model-value="item.title || ''"
              @update:model-value="updateField('title', $event)"
              variant="outlined"
              density="compact"
              class="compact-field-tight status-themed-field"
            />

            <!-- Duration and Priority inline row -->
            <div class="duration-priority-row">
              <v-text-field
                label="Duration"
                :model-value="item.duration || ''"
                @update:model-value="updateField('duration', $event)"
                variant="outlined"
                density="compact"
                class="compact-field-tight inline-field duration-field status-themed-field"
              />

              <v-select
                label="Priority"
                :model-value="item.priority || 'normal'"
                :items="priorityOptions"
                @update:model-value="updateField('priority', $event)"
                variant="outlined"
                density="compact"
                class="compact-field-tight inline-field priority-field status-themed-field"
              />
            </div>
          </div>

          <!-- Content & Production -->
          <div class="metadata-section mb-3">
            <h4 class="section-title">Content & Production</h4>

            <!-- 5. Description as multiline (5 lines) -->
            <v-textarea
              label="Description"
              :model-value="item.description || ''"
              @update:model-value="updateField('description', $event)"
              variant="outlined"
              density="compact"
              rows="5"
              class="compact-field-tight status-themed-field"
            />

            <!-- 6. Customer field only for ads -->
            <v-text-field
              v-if="item.type === 'ad'"
              label="Customer"
              :model-value="item.customer || ''"
              @update:model-value="updateField('customer', $event)"
              variant="outlined"
              density="compact"
              class="compact-field status-themed-field"
            />

            <!-- 7. Link -->
            <v-text-field
              label="Link"
              :model-value="item.link || ''"
              @update:model-value="updateField('link', $event)"
              variant="outlined"
              density="compact"
              class="compact-field-tight status-themed-field"
            />
          </div>

          <!-- People and Resources -->
          <div class="metadata-section mb-3">
            <h4 class="section-title">People & Resources</h4>

            <!-- 8. Guests -->
            <v-textarea
              label="Guests"
              :model-value="item.guests || ''"
              @update:model-value="updateField('guests', $event)"
              variant="outlined"
              density="compact"
              rows="2"
              class="compact-field-tight status-themed-field"
            />

            <!-- 8. Resources -->
            <v-textarea
              label="Resources"
              :model-value="item.resources || ''"
              @update:model-value="updateField('resources', $event)"
              variant="outlined"
              density="compact"
              rows="2"
              class="compact-field-tight status-themed-field"
            />

            <!-- 8. Tags -->
            <v-text-field
              label="Tags"
              :model-value="item.tags || ''"
              @update:model-value="updateField('tags', $event)"
              variant="outlined"
              density="compact"
              class="compact-field-tight status-themed-field"
              hint="Comma-separated tags"
              persistent-hint
            />
          </div>

          <!-- Speaker Stats -->
          <div class="metadata-section mb-3">
            <h4 class="section-title">Speaker Stats</h4>

            <v-select
              label="Speaker"
              :model-value="item.speaker_id || null"
              :items="speakers"
              item-title="name"
              item-value="id"
              @update:model-value="updateField('speaker_id', $event)"
              variant="outlined"
              density="compact"
              class="compact-field-tight status-themed-field"
              clearable
            >
              <template v-slot:prepend-inner>
                <v-icon size="small">mdi-account-voice</v-icon>
              </template>
            </v-select>

            <!-- WPM Display (when speaker is selected) -->
            <div v-if="selectedSpeaker" class="speaker-wpm-display">
              <v-card variant="tonal" color="primary" class="pa-2">
                <div class="d-flex justify-space-between align-center">
                  <div>
                    <div class="text-caption">Words Per Minute</div>
                    <div class="text-h6">{{ selectedSpeaker.wpm }}</div>
                  </div>
                  <div class="text-right">
                    <div class="text-caption">Range</div>
                    <div class="text-body-2">{{ selectedSpeaker.wpm_min }} - {{ selectedSpeaker.wpm_max }}</div>
                  </div>
                </div>
              </v-card>
            </div>

            <!-- WPM Measurement Tool Link -->
            <v-btn
              size="x-small"
              variant="text"
              color="primary"
              class="mt-1"
              @click="$emit('open-wpm-tool')"
            >
              <v-icon left size="small">mdi-speedometer</v-icon>
              Measure WPM
            </v-btn>
          </div>

          <!-- System Information -->
          <div v-if="item.server_message || item.created_at" class="metadata-section mb-3">
            <h4 class="section-title secondary">System Information</h4>

            <v-textarea
              v-if="item.server_message"
              label="Server Message"
              :model-value="item.server_message || ''"
              variant="outlined"
              density="compact"
              readonly
              rows="2"
              class="compact-field"
            />

            <!-- 9. Created At -->
            <v-text-field
              v-if="item.created_at"
              label="Created At"
              :model-value="item.created_at || ''"
              variant="outlined"
              density="compact"
              readonly
              class="compact-field"
            />
          </div>

          <!-- Action Buttons -->
          <div class="metadata-actions mt-4">

            <v-btn
              color="secondary"
              variant="outlined"
              size="small"
              @click="resetFields"
            >
              <v-icon left>mdi-refresh</v-icon>
              Reset
            </v-btn>
          </div>

          <!-- Version History Section -->
          <div class="metadata-section mt-4 version-history-section">
            <h4 class="section-title">
              <v-icon size="small" class="mr-1">mdi-history</v-icon>
              Version History
            </h4>

            <!-- Loading State -->
            <div v-if="loadingVersions" class="text-center py-2">
              <v-progress-circular indeterminate size="20" width="2" color="primary" />
            </div>

            <!-- No Versions -->
            <div v-else-if="versionHistory.length === 0" class="text-center py-2">
              <p class="text-caption text-grey">No saved versions yet</p>
              <p class="text-caption text-grey-lighten-1">Versions are created on manual save (Ctrl+S)</p>
            </div>

            <!-- Version List -->
            <v-list v-else density="compact" class="version-list pa-0">
              <v-list-item
                v-for="(version, idx) in versionHistory.slice(0, 10)"
                :key="version.version_number"
                class="version-item px-2"
                :class="{ 'current-version': idx === 0 }"
              >
                <template v-slot:prepend>
                  <v-chip
                    size="x-small"
                    :color="idx === 0 ? 'primary' : 'grey'"
                    class="mr-2"
                  >
                    v{{ version.version_number }}
                  </v-chip>
                </template>
                <v-list-item-title class="text-body-2">
                  {{ formatVersionDate(version.created_at) }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  {{ version.content_length || 0 }} chars
                  <span v-if="version.created_by"> &bull; {{ version.created_by }}</span>
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn
                    v-if="idx > 0"
                    icon
                    size="x-small"
                    variant="text"
                    color="primary"
                    @click="$emit('restore-version', version.version_number)"
                  >
                    <v-icon size="small">mdi-restore</v-icon>
                    <v-tooltip activator="parent" location="left">Restore this version</v-tooltip>
                  </v-btn>
                  <v-chip v-else size="x-small" color="success" variant="tonal">Current</v-chip>
                </template>
              </v-list-item>
            </v-list>

            <!-- Show more versions hint -->
            <div v-if="versionHistory.length > 10" class="text-caption text-grey text-center mt-1">
              Showing 10 of {{ versionHistory.length }} versions
            </div>
          </div>
        </div>

        <!-- Asset Generation Section -->
        <div v-if="episodeNumber" class="metadata-section mt-4 asset-generation-section">
          <h4 class="section-title">
            <v-icon size="small" class="mr-1">mdi-image-multiple</v-icon>
            Asset Generation
          </h4>
          <div class="asset-generation-buttons">
            <v-btn
              size="small"
              variant="tonal"
              color="amber-darken-2"
              :loading="regeneratingFSQ"
              :disabled="regeneratingFSQ"
              @click="regenerateAllFSQ"
              class="mb-2"
              block
            >
              <v-icon left size="small">mdi-format-quote-close</v-icon>
              Regenerate All Quotes
            </v-btn>
            <div v-if="fsqRegenerationStatus" class="text-caption mt-1" :class="fsqRegenerationStatus.includes('Error') ? 'text-error' : 'text-success'">
              {{ fsqRegenerationStatus }}
            </div>

            <v-btn
              size="small"
              variant="tonal"
              color="blue-darken-2"
              :loading="enumeratingCues"
              :disabled="enumeratingCues"
              @click="enumerateCueBlocks"
              class="mb-2 mt-2"
              block
            >
              <v-icon left size="small">mdi-format-list-numbered</v-icon>
              Enumerate Cue Blocks
            </v-btn>
            <div v-if="enumerationStatus" class="text-caption mt-1" :class="enumerationStatus.includes('Error') ? 'text-error' : 'text-success'">
              {{ enumerationStatus }}
            </div>

            <v-btn
              size="small"
              variant="tonal"
              color="teal-darken-2"
              :loading="gatheringMedia"
              :disabled="gatheringMedia"
              @click="gatherForShow"
              class="mb-2 mt-2"
              block
            >
              <v-icon left size="small">mdi-folder-download</v-icon>
              Gather for Show
            </v-btn>
            <v-progress-linear
              v-if="gatheringMedia && gatherProgress > 0"
              :model-value="gatherProgress"
              color="teal"
              height="6"
              class="mt-1 mb-1"
            />
            <div v-if="gatherStatus" class="text-caption mt-1" :class="gatherStatus.includes('Error') ? 'text-error' : 'text-success'">
              {{ gatherStatus }}
              <v-btn
                v-if="gatherResults"
                size="x-small"
                variant="text"
                color="primary"
                @click="showGatherResultsModal = true"
                class="ml-1"
              >
                Details
              </v-btn>
            </div>
          </div>
        </div>

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
              <!-- Summary -->
              <v-alert
                :type="gatherResults.failed > 0 ? 'warning' : 'success'"
                density="compact"
                class="mb-3"
              >
                <strong>{{ gatherResults.copied }}</strong> files copied,
                <strong>{{ gatherResults.skipped }}</strong> skipped (no media),
                <strong>{{ gatherResults.failed }}</strong> failed
              </v-alert>

              <!-- Successful Files -->
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

              <!-- Failed Files -->
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

              <!-- Skipped (no MediaURL) -->
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

              <!-- Output Path -->
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

        <!-- Generated Documents Section (episode-level, always shown) -->
        <div v-if="episodeNumber" class="metadata-section mt-4 generated-documents-section">
          <h4 class="section-title">
            <v-icon size="small" class="mr-1">mdi-file-document-multiple-outline</v-icon>
            Generated Documents
          </h4>

          <!-- Loading State -->
          <div v-if="loadingDocuments" class="text-center py-2">
            <v-progress-circular indeterminate size="20" width="2" color="primary" />
          </div>

          <!-- No Documents -->
          <div v-else-if="generatedDocuments.length === 0" class="text-center py-2">
            <p class="text-caption text-grey">No generated documents yet</p>
            <v-btn
              size="x-small"
              variant="text"
              color="primary"
              @click="$emit('generate-host-script')"
            >
              <v-icon left size="small">mdi-plus</v-icon>
              Generate Host Script
            </v-btn>
          </div>

          <!-- Document List -->
          <v-list v-else density="compact" class="document-list pa-0">
            <v-list-item
              v-for="doc in generatedDocuments"
              :key="doc.filename"
              :href="doc.url"
              target="_blank"
              class="document-item px-2"
            >
              <template v-slot:prepend>
                <v-icon
                  :color="getDocumentIconColor(doc.format)"
                  size="small"
                >
                  {{ getDocumentIcon(doc.format) }}
                </v-icon>
              </template>
              <v-list-item-title class="text-body-2">
                {{ formatDocumentName(doc) }}
                <span v-if="doc.revision" class="revision-badge">R{{ doc.revision }}</span>
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption d-flex align-center">
                <span>{{ doc.size_formatted }} • {{ doc.modified_formatted }}</span>
                <a
                  v-if="doc.pastRevisions && doc.pastRevisions.length > 0"
                  href="#"
                  class="past-revisions-link ml-2"
                  @click.prevent.stop="openRevisionsModal(doc)"
                >
                  past revisions ({{ doc.pastRevisions.length }})
                </a>
              </v-list-item-subtitle>
              <template v-slot:append>
                <v-btn
                  icon
                  size="x-small"
                  variant="text"
                  :href="doc.url"
                  target="_blank"
                  @click.stop
                >
                  <v-icon size="small">mdi-open-in-new</v-icon>
                </v-btn>
              </template>
            </v-list-item>
          </v-list>

          <!-- Action Buttons -->
          <div class="document-actions mt-2">
            <v-btn
              size="x-small"
              variant="tonal"
              color="success"
              class="mr-1"
              @click="$emit('generate-host-script')"
              :loading="hostScriptLoading"
            >
              <v-icon left size="small">mdi-script-text-outline</v-icon>
              Host Script
            </v-btn>

            <v-btn
              size="x-small"
              variant="tonal"
              color="primary"
              class="mr-1"
              @click="$emit('generate-media-list')"
              :loading="mediaListLoading"
            >
              <v-icon left size="small">mdi-playlist-play</v-icon>
              Media List
            </v-btn>

            <v-btn
              size="x-small"
              variant="tonal"
              color="secondary"
              class="mr-1"
              @click="$emit('generate-prompter-files')"
              disabled
            >
              <v-icon left size="small">mdi-script-text</v-icon>
              Prompter
              <v-tooltip activator="parent" location="bottom">Coming Soon</v-tooltip>
            </v-btn>

            <v-btn
              size="x-small"
              variant="text"
              color="primary"
              @click="loadGeneratedDocuments"
              :loading="loadingDocuments"
            >
              <v-icon size="small">mdi-refresh</v-icon>
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>

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
                {{ rev.size_formatted }} • {{ rev.modified_formatted }}
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

export default {
  name: 'MetadataPanel',
  emits: [
    'close',
    'toggle-width',
    'update-field',
    'open-wpm-tool',
    'generate-host-script',
    'generate-media-list',
    'generate-prompter-files',
    'refresh-rundown',
    'show-notification',
    'restore-version'
  ],
  props: {
    panelWidth: {
      type: String,
      default: 'wide',
      validator: (value) => ['narrow', 'wide'].includes(value)
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
    }
  },
  data() {
    return {
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
      assetIdCopied: false,
      showRevisionsModal: false,
      selectedDocument: null
    }
  },
  watch: {
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
      return this.panelWidth === 'narrow' ? '300px' : '400px'
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

    // Status-based color scheme for input fields
    statusThemeColors() {
      if (!this.item) {
        return {
          primary: '#e3f2fd',
          border: '#90caf9',
          accent: '#1976d2'
        }
      }

      const status = this.item.status || 'draft'

      // Define color schemes based on episode status
      const statusColors = {
        draft: {
          primary: '#f5f5f5',    // Light gray
          border: '#bdbdbd',     // Medium gray
          accent: '#616161'      // Dark gray (matches grey-darken-2)
        },
        approved: {
          primary: '#e8f5e8',    // Light green
          border: '#81c784',     // Medium green
          accent: '#2e7d32'      // Dark green
        },
        production: {
          primary: '#fff3e0',    // Light orange
          border: '#ffb74d',     // Medium orange
          accent: '#f57c00'      // Dark orange
        },
        completed: {
          primary: '#e3f2fd',    // Light blue
          border: '#64b5f6',     // Medium blue
          accent: '#1976d2'      // Dark blue
        }
      }

      return statusColors[status] || statusColors.draft
    },

    selectedSpeaker() {
      if (!this.item?.speaker_id || !this.speakers.length) {
        return null
      }
      return this.speakers.find(s => s.id === this.item.speaker_id)
    }
  },
  methods: {
    updateField(fieldName, value) {
      this.$emit('update-field', { field: fieldName, value: value })
    },
    async copyAssetId() {
      const assetId = this.item?.asset_id || this.item?.id
      if (!assetId) return

      try {
        await navigator.clipboard.writeText(String(assetId))
        this.assetIdCopied = true
        setTimeout(() => {
          this.assetIdCopied = false
        }, 2000)
      } catch (err) {
        console.error('Failed to copy AssetID:', err)
      }
    },
    resetFields() {
      // Reset to original item values (would need to track original values)
      // For now, just emit a reset event
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
        }
      } catch (error) {
        console.error('Error loading speakers:', error)
        // Fail silently - speaker dropdown will just be empty
      } finally {
        this.loadingSpeakers = false
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
          const { enumerated, files_renamed, total } = response.data
          this.enumerationStatus = `Enumerated: ${enumerated}/${total} cues, ${files_renamed} files renamed`
          // Emit event to refresh the rundown data
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

          // Store full results for modal
          this.gatherResults = response.data

          // Auto-show modal if there are failures
          if (failed > 0) {
            this.showGatherResultsModal = true
          }

          // Show toast notification
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
      // Extract readable name from filename
      // e.g., "0249-HOST-SCRIPT.html" -> "Host Script"
      // e.g., "0249-HOST-SCRIPT-2025-01-18.html" -> "Host Script 2025-01-18"
      let name = doc.filename
        .replace(/^\d+-/, '') // Remove episode number prefix
        .replace(/\.(html|pdf|txt)$/i, '') // Remove extension
        .replace(/-/g, ' ') // Replace dashes with spaces

      // Title case (but preserve date format)
      name = name.split(' ')
        .map(word => {
          // Check if it looks like a date part (YYYY, MM, DD)
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

        // Relative time for recent versions
        if (diffMins < 1) return 'Just now'
        if (diffMins < 60) return `${diffMins} min ago`
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

        // Absolute date for older versions
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
/* Slug Header at top of panel */
.slug-header {
  padding: 12px 16px;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.slug-header.has-changes {
  background-color: rgb(var(--v-theme-primary));
}

.slug-header.saved {
  background-color: rgb(var(--v-theme-success));
}

/* AssetID Display Row */
.asset-id-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 4px 12px;
  background-color: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  font-size: 0.7rem;
}

.asset-id-label {
  color: rgba(0, 0, 0, 0.5);
  font-weight: 500;
}

.asset-id-value {
  font-family: 'Roboto Mono', monospace;
  color: rgba(0, 0, 0, 0.7);
  font-weight: 600;
}

.asset-id-row .copy-btn {
  opacity: 0.6;
  transition: opacity 0.2s;
}

.asset-id-row .copy-btn:hover {
  opacity: 1;
}

.copied-indicator {
  color: rgb(var(--v-theme-success));
  font-size: 0.65rem;
  font-weight: 600;
  animation: fadeIn 0.2s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.metadata-panel {
  height: 100vh; /* Full viewport height */
  border-left: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  overflow: hidden; /* Panel itself doesn't scroll - content inside does */
  display: flex;
  flex-direction: column;
  position: sticky !important; /* Stick to top when scrolling */
  top: 0 !important;
  z-index: 15 !important; /* Highest - appear above all other panels */
  align-self: flex-start; /* Required for sticky to work in flex container */
}

/* Card fills the panel and allows content to scroll */
.metadata-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0; /* Critical: allows flex child to shrink for scrolling */
  overflow: hidden;
}

.metadata-title {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  min-height: 56px;
}

.header-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.header-fallback {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.asset-id-subtitle {
  font-size: 0.6rem !important;
  font-weight: 400 !important;
  opacity: 0.8;
  margin-top: -2px;
  line-height: 1.1;
}

.metadata-content {
  overflow-y: auto !important; /* Independent scrolling for content area */
  flex: 1 1 0 !important; /* Flex grow, shrink, and basis 0 for proper scrolling */
  overflow-x: hidden;
  min-height: 0 !important; /* Critical: Allow flex shrinking for scroll to work */
  max-height: none !important; /* Override any Vuetify max-height */
}

/* Compact section styling */
.metadata-section {
  border-left: 2px solid var(--v-primary-base);
  padding-left: 8px;
  margin-left: 4px;
}

/* Section titles - much smaller and tighter */
.section-title {
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
  color: var(--v-primary-base) !important;
  margin: 0 0 6px -12px !important;
  padding: 0 !important;
  line-height: 1.2 !important;
}

.section-title.secondary {
  color: var(--v-secondary-base) !important;
}

/* Compact field styling */
.compact-field {
  margin-bottom: 1px !important;
}

/* Tighter compact field styling for basic information */
.compact-field-tight {
  margin-bottom: 0px !important;
}

/* Inline field styling for horizontal layouts */
.inline-field {
  flex: 1;
  margin-bottom: 0 !important;
  min-width: 0; /* Allow fields to shrink */
}

/* Duration and Priority row layout */
.duration-priority-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.duration-field {
  flex: 1.2 !important; /* Duration gets more space */
  max-width: 140px;
}

.priority-field {
  flex: 1 !important;
  max-width: none;
}

/* Clean minimal field styling - matching ShowInfoHeader */
:deep(.status-themed-field .v-field) {
  background-color: #f5f5f5 !important;
  border-radius: 4px !important;
}

:deep(.status-themed-field .v-field__outline) {
  display: none !important;
}

:deep(.status-themed-field .v-field-label) {
  color: rgba(0, 0, 0, 0.6) !important;
  font-weight: 500 !important;
  font-size: 0.75rem !important;
}

:deep(.status-themed-field .v-field__input) {
  font-size: 0.875rem !important;
  padding: 4px 8px !important;
  color: rgba(0, 0, 0, 0.87) !important;
}

:deep(.status-themed-field textarea) {
  font-size: 0.875rem !important;
  padding: 4px 8px !important;
  color: rgba(0, 0, 0, 0.87) !important;
  line-height: 1.3 !important;
}

:deep(.status-themed-field .v-select__selection) {
  font-size: 0.875rem !important;
  color: rgba(0, 0, 0, 0.87) !important;
}

.metadata-actions {
  position: sticky;
  bottom: 0;
  background: white;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  margin: 0 -8px;
  padding: 8px;
}

.metadata-actions .v-btn {
  font-size: 0.7rem !important;
  padding: 0 8px !important;
  height: 28px !important;
}

/* Narrow mode adjustments */
.metadata-panel.narrow .metadata-content {
  padding: 6px;
}

.metadata-panel.narrow .metadata-section {
  margin-bottom: 10px;
  padding-left: 6px;
}

.metadata-panel.narrow .metadata-actions {
  padding: 6px;
}

.metadata-panel.narrow .metadata-actions .v-btn {
  width: 100%;
  margin: 1px 0;
  font-size: 0.65rem !important;
  height: 24px !important;
}

/* Ultra-compact field styling */
:deep(.compact-field .v-field) {
  font-size: 0.75rem !important;
  border-radius: 4px !important;
  background-color: #f5f5f5 !important;
}

:deep(.compact-field .v-field__outline) {
  display: none !important;
}

/* Clean minimal styling for all input fields */
:deep(.v-field) {
  border-radius: 4px !important;
  background-color: #f5f5f5 !important;
}

:deep(.v-field__outline) {
  display: none !important;
}

:deep(.v-field__field) {
  border-radius: 4px !important;
}

:deep(.compact-field .v-field__input) {
  min-height: 26px !important;
  padding: 4px 8px !important;
  font-size: 0.75rem !important;
}

:deep(.compact-field .v-field__field) {
  min-height: 26px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

:deep(.compact-field .v-field-label) {
  font-size: 0.7rem !important;
  line-height: 1.1 !important;
}

/* Raise floating labels by 0.75em for all fields in metadata panel */
:deep(.v-field-label) {
  transform: translateY(-0.75em) !important;
}

/* Move specific textarea labels (guests, resources, description) down by 0.75em */
:deep(.v-textarea .v-field-label) {
  transform: translateY(0em) !important;
}

:deep(.compact-field .v-field__outline) {
  display: none !important;
}

/* Compact select dropdown */
:deep(.compact-field .v-select__selection) {
  font-size: 0.75rem !important;
  line-height: 1.2 !important;
}

/* Compact textarea */
:deep(.compact-field textarea) {
  font-size: 0.75rem !important;
  line-height: 1.3 !important;
  padding: 4px 8px !important;
}

/* Compact hint text */
:deep(.compact-field .v-messages) {
  font-size: 0.65rem !important;
  min-height: 12px !important;
  padding-top: 2px !important;
}

/* Tighter content padding overall */
.metadata-content {
  padding: 6px 8px !important;
}

/* Primary Save Button Styling */
.primary-save-section {
  padding: 8px 0;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-primary), 0.05);
  margin: 12px -8px;
  padding: 12px 8px;
}

/* Speaker WPM Display */
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

/* Tab-shaped control buttons on left edge */
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

/* Generated Documents Section */
.generated-documents-section {
  border-left-color: var(--v-secondary-base);
}

.generated-documents-section .section-title {
  color: var(--v-secondary-base) !important;
}

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

/* Revision badge */
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

/* Past revisions link */
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

/* Revision modal list item */
.revision-list-item {
  min-height: 48px !important;
}

/* Document action buttons */
.document-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.document-actions .v-btn {
  font-size: 0.65rem !important;
}

/* Gather Results Modal */
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

/* Version History Section */
.version-history-section {
  border-left-color: var(--v-info-base);
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

</style>