<template>
  <div
    :class="['metadata-panel', panelWidth === 'narrow' ? 'narrow' : 'wide']"
    :style="{ width: panelWidthValue }"
  >
    <v-card class="h-auto" flat>
      <!-- Metadata Header -->
      <v-card-title
        class="d-flex align-center pa-2 metadata-title"
        :style="itemHeaderStyle"
      >
        <div class="header-content">
          <div v-if="item?.slug" class="text-h6">{{ item.slug }}</div>
          <div v-else-if="item" class="header-fallback">
            <div class="text-h6">{{ (item.type || 'Unknown Type').toUpperCase() }}</div>
            <div class="asset-id-subtitle">{{ item.id || 'No AssetID' }}</div>
          </div>
          <div v-else class="text-h6">No Item Selected</div>
        </div>
        <v-spacer></v-spacer>
        <v-btn
          icon
          size="small"
          @click="$emit('toggle-width')"
        >
          <v-icon>{{ panelWidth === 'narrow' ? 'mdi-arrow-expand-horizontal' : 'mdi-arrow-collapse-horizontal' }}</v-icon>
        </v-btn>
        <v-btn icon size="small" @click="$emit('close')">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-divider></v-divider>
      
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
        </div>
      </v-card-text>
    </v-card>
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
    'open-wpm-tool'
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
    itemTypes: {
      type: Array,
      default: () => [
        { title: 'Segment', value: 'segment' },
        { title: 'Advertisement', value: 'ad' },
        { title: 'Promo', value: 'promo' },
        { title: 'Call to Action', value: 'cta' },
        { title: 'Transition', value: 'trans' }
      ]
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
      loadingSpeakers: false
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
    }
  }
}
</script>

<style scoped>
.metadata-panel {
  height: auto; /* Grow with content */
  border-left: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  overflow: visible; /* Scrolls with page */
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 15 !important; /* Highest - appear above all other panels */
  padding-bottom: 50vh; /* Add whitespace equal to 50% of viewport height */
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
  overflow-y: visible; /* No internal scroll - page scrolls */
  flex: 1; /* Take remaining space after metadata-title */
  overflow-x: hidden;
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

/* Status-themed fields with dynamic coloring based on episode status */
:deep(.status-themed-field .v-field) {
  background-color: v-bind('statusThemeColors.primary') !important;
  border: 1px solid v-bind('statusThemeColors.border') !important;
}

:deep(.status-themed-field .v-field__outline) {
  border-color: v-bind('statusThemeColors.border') !important;
}

:deep(.status-themed-field .v-field__outline--focused) {
  border-color: v-bind('statusThemeColors.accent') !important;
  border-width: 2px !important;
}

:deep(.status-themed-field .v-field-label) {
  color: v-bind('statusThemeColors.accent') !important;
  font-weight: 500 !important;
}

:deep(.status-themed-field .v-field-label--floating) {
  color: v-bind('statusThemeColors.accent') !important;
}

:deep(.status-themed-field .v-select__selection) {
  font-weight: 600 !important;
  color: v-bind('statusThemeColors.accent') !important;
}

:deep(.status-themed-field .v-field__input) {
  color: v-bind('statusThemeColors.accent') !important;
}

:deep(.status-themed-field textarea) {
  color: v-bind('statusThemeColors.accent') !important;
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
  border-radius: 0 !important;
}

/* Remove rounded corners from all input fields */
:deep(.v-field) {
  border-radius: 0 !important;
}

:deep(.v-field__outline) {
  border-radius: 0 !important;
}

:deep(.v-field__field) {
  border-radius: 0 !important;
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
  --v-field-border-width: 1px !important;
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

</style>