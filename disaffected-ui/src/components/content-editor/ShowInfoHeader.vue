<template>
  <v-card class="show-info-header full-width-bg" flat>
    <v-card-text class="pa-1">
      <div v-if="loadingRundown" style="margin-bottom: 8px;">
        <v-progress-linear indeterminate color="primary" height="4" rounded></v-progress-linear>
      </div>
      <div class="header-container">
        <!-- Section 1: Episode Title and Description -->
        <div class="header-section section-1">
          <div class="field-with-label">
            <label class="field-label">Episode Title</label>
            <v-text-field
              :model-value="episodeTitle"
              @update:model-value="$emit('update:episodeTitle', $event)"
              variant="outlined"
              density="compact"
              class="episode-title-input"
              hide-details
              single-line
              placeholder="Enter episode title..."
            />
          </div>
          <div class="field-with-label">
            <label class="field-label">Description</label>
            <v-textarea
              :model-value="description"
              @update:model-value="$emit('update:description', $event)"
              variant="outlined"
              density="compact"
              class="episode-description-input"
              hide-details
              rows="2"
              no-resize
              placeholder="Enter episode description..."
            />
          </div>
          <!-- Air Date and Air Time Row -->
          <div class="air-datetime-row">
            <div class="field-with-label air-date-field">
              <label class="field-label">Air Date</label>
              <v-menu
                v-model="showDatePicker"
                :close-on-content-click="false"
                location="bottom"
              >
                <template v-slot:activator="{ props }">
                  <input
                    type="text"
                    :value="formattedAirDate"
                    readonly
                    v-bind="props"
                    class="air-date-native-input"
                    placeholder="Select date"
                  />
                </template>
                <v-date-picker
                  :model-value="airDateForPicker"
                  @update:model-value="handleDateSelect"
                  color="primary"
                ></v-date-picker>
              </v-menu>
            </div>
            <div class="field-with-label air-time-et-field">
              <label class="field-label">Air Time ({{ timezoneAbbreviation }})</label>
              <v-menu
                v-model="showTimePicker"
                :close-on-content-click="false"
                location="bottom"
              >
                <template v-slot:activator="{ props }">
                  <input
                    type="text"
                    :value="airTime"
                    readonly
                    v-bind="props"
                    class="air-time-native-input"
                    placeholder="HH:MM"
                  />
                </template>
                <v-time-picker
                  :model-value="airTime"
                  @update:model-value="handleTimeSelect"
                  format="24hr"
                  scrollable
                ></v-time-picker>
              </v-menu>
            </div>
            <div class="field-with-label air-utc-field">
              <label class="field-label">UTC</label>
              <input
                type="text"
                :value="utcDateTime"
                readonly
                class="air-utc-display"
                placeholder="--"
              />
            </div>
          </div>
        </div>

        <!-- Section 2: Split into 2.1 (Thumbnail) and 2.2 (Reserved) -->
        <div class="header-section section-2">
          <div class="section-2-split">
            <!-- Section 2.1: Thumbnail Carousel (left) -->
            <div class="section-2-1">
              <!-- Thumbnail Carousel -->
              <div class="thumbnail-container" v-if="thumbnails && thumbnails.length > 0">
                <div
                  class="thumbnail-viewport"
                  :class="{ 'confirmed': isCurrentThumbnailConfirmed }"
                  @click="showThumbnailPreview = true"
                  style="cursor: pointer;"
                >
                  <div
                    class="thumbnail-track"
                    :style="{ transform: `translateX(-${currentThumbnailIndex * 100}%)` }"
                  >
                    <img
                      v-for="(thumb, index) in thumbnails"
                      :key="thumb.url"
                      :src="thumb.url"
                      :alt="'Episode ' + episodeNumber + ' thumbnail ' + (index + 1)"
                      class="episode-thumbnail"
                      :class="{ 'active': index === currentThumbnailIndex }"
                      @error="handleThumbnailError"
                    />
                  </div>
                </div>
                <!-- Thumbnail Controls Overlay -->
                <div class="thumbnail-controls">
                  <!-- Navigation (only if multiple) -->
                  <div v-if="thumbnails.length > 1" class="thumbnail-nav">
                    <v-btn
                      icon
                      size="x-small"
                      variant="text"
                      @click="prevThumbnail"
                      :disabled="currentThumbnailIndex === 0"
                      class="thumbnail-nav-btn"
                    >
                      <v-icon size="small">mdi-chevron-left</v-icon>
                    </v-btn>
                    <span class="thumbnail-counter">{{ currentThumbnailIndex + 1 }}/{{ thumbnails.length }}</span>
                    <v-btn
                      icon
                      size="x-small"
                      variant="text"
                      @click="nextThumbnail"
                      :disabled="currentThumbnailIndex === thumbnails.length - 1"
                      class="thumbnail-nav-btn"
                    >
                      <v-icon size="small">mdi-chevron-right</v-icon>
                    </v-btn>
                  </div>
                  <!-- Take Button -->
                  <v-btn
                    size="x-small"
                    :color="isCurrentThumbnailConfirmed ? 'success' : 'primary'"
                    variant="elevated"
                    @click="takeThumbnail"
                    class="take-btn"
                    :disabled="isCurrentThumbnailConfirmed"
                  >
                    <v-icon size="x-small" class="mr-1">{{ isCurrentThumbnailConfirmed ? 'mdi-check' : 'mdi-camera' }}</v-icon>
                    {{ isCurrentThumbnailConfirmed ? 'Confirmed' : 'Take' }}
                  </v-btn>
                </div>
              </div>
              <!-- No Thumbnail Placeholder -->
              <div v-else class="thumbnail-placeholder">
                <v-icon size="x-large" color="grey-lighten-1">mdi-image-off</v-icon>
                <span class="placeholder-label">No Poster Found</span>
                <v-btn
                  size="x-small"
                  variant="text"
                  color="grey"
                  class="mt-2 select-thumbnail-btn"
                  @click="$emit('select-thumbnail')"
                >
                  <v-icon size="x-small" class="mr-1">mdi-folder-open</v-icon>
                  Select
                </v-btn>
              </div>
            </div>
            <!-- Section 2.2: Reserved -->
            <div class="section-2-2">
              <div class="section-placeholder">
                <span class="placeholder-text">2.2</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Section 3: Reserved for future use -->
        <div class="header-section section-3">
          <div class="section-placeholder">
            <span class="placeholder-text">Section 3</span>
          </div>
        </div>

        <!-- Section 4: Action Buttons -->
        <div class="header-section section-4 d-flex align-center justify-end gap-1">
          <!-- More Options Dropdown -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                size="x-small"
                color="grey"
                variant="outlined"
                class="header-action-btn"
                v-bind="props"
              >
                <v-icon size="x-small" class="mr-1">mdi-dots-horizontal</v-icon>
                More
              </v-btn>
            </template>
            <v-list>
              <v-list-item @click="$emit('toggle-script-reading')" :disabled="!isXttsConfigured">
                <v-list-item-title>
                  <v-icon size="small" class="mr-2" :color="isReadingScript ? 'error' : 'primary'">{{ isReadingScript ? 'mdi-stop' : 'mdi-volume-high' }}</v-icon>
                  {{ isReadingScript ? 'Stop Reading' : 'Read Script Aloud' }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ isXttsConfigured ? 'Read with XTTS' : 'XTTS not configured' }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-divider></v-divider>
              <v-list-item @click="$emit('request-new-episode-assetid')">
                <v-list-item-title>
                  <v-icon size="small" class="mr-2">mdi-refresh</v-icon>
                  Request New Episode AssetID
                </v-list-item-title>
              </v-list-item>
              <v-list-item @click="$emit('show-assetid-info')">
                <v-list-item-title>
                  <v-icon size="small" class="mr-2">mdi-identifier</v-icon>
                  Show AssetID Info
                </v-list-item-title>
              </v-list-item>
              <v-divider></v-divider>
              <!-- Script Generation Submenu -->
              <v-list-group>
                <template v-slot:activator="{ props }">
                  <v-list-item v-bind="props" :disabled="!episodeNumber">
                    <template v-slot:prepend>
                      <v-icon size="small" color="primary">mdi-script-text</v-icon>
                    </template>
                    <v-list-item-title>Generate Script</v-list-item-title>
                  </v-list-item>
                </template>
                <v-list-item @click="$emit('generate-script', 'host_full')" :disabled="!episodeNumber">
                  <v-list-item-title>
                    <v-icon size="small" class="mr-2" color="blue">mdi-file-document</v-icon>
                    Host Script (Full)
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    Complete script with images, cues, and visuals
                  </v-list-item-subtitle>
                </v-list-item>
                <v-list-item @click="$emit('generate-script', 'host_clean')" :disabled="!episodeNumber">
                  <v-list-item-title>
                    <v-icon size="small" class="mr-2" color="green">mdi-text</v-icon>
                    Host Script (Clean)
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    Teleprompter-friendly, large text, minimal cues
                  </v-list-item-subtitle>
                </v-list-item>
                <v-list-item @click="$emit('generate-script', 'production')" :disabled="!episodeNumber">
                  <v-list-item-title>
                    <v-icon size="small" class="mr-2" color="orange">mdi-clipboard-list</v-icon>
                    Production Rundown
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    Technical details, compact, all cue info
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list-group>
            </v-list>
          </v-menu>

          <!-- Save All Button (rightmost) - Always clickable for manual save -->
          <v-btn
            size="x-small"
            :color="saveState?.hasChanges ? 'primary' : 'success'"
            variant="elevated"
            @click="$emit('save-all')"
            class="header-action-btn"
          >
            <v-icon size="x-small" class="mr-1">{{ saveState?.hasChanges ? 'mdi-content-save' : 'mdi-check-circle' }}</v-icon>
            {{ saveState?.hasChanges ? 'Save' : 'Saved' }}
            <v-tooltip activator="parent" location="bottom">{{ saveState?.hasChanges ? 'Save all changes now' : 'Click to force save (already synchronized)' }}</v-tooltip>
          </v-btn>
        </div>
      </div>
    </v-card-text>

    <!-- Thumbnail Preview Modal -->
    <v-dialog v-model="showThumbnailPreview" max-width="90vw" max-height="90vh">
      <v-card class="thumbnail-preview-modal">
        <v-card-title class="d-flex justify-space-between align-center pa-2">
          <span class="text-subtitle-1">Thumbnail Preview</span>
          <v-btn icon size="small" variant="text" @click="showThumbnailPreview = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-2 d-flex justify-center align-center">
          <img
            v-if="currentThumbnailUrl"
            :src="currentThumbnailUrl"
            :alt="'Episode ' + episodeNumber + ' thumbnail preview'"
            class="thumbnail-preview-image"
          />
        </v-card-text>
        <v-card-actions class="justify-center pa-2" v-if="thumbnails && thumbnails.length > 1">
          <v-btn
            icon
            variant="outlined"
            @click="prevThumbnail"
            :disabled="currentThumbnailIndex === 0"
          >
            <v-icon>mdi-chevron-left</v-icon>
          </v-btn>
          <span class="mx-4">{{ currentThumbnailIndex + 1 }} / {{ thumbnails.length }}</span>
          <v-btn
            icon
            variant="outlined"
            @click="nextThumbnail"
            :disabled="currentThumbnailIndex === thumbnails.length - 1"
          >
            <v-icon>mdi-chevron-right</v-icon>
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-card>
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap';

export default {
  name: 'ShowInfoHeader',
  emits: ['update:airDate', 'update:airTime', 'update:airTimezone', 'update:productionStatus', 'update:title', 'update:slug', 'update:episodeTitle', 'update:subtitle', 'update:guest', 'update:description', 'save-all', 'toggle-metadata-panel', 'toggle-script-reading', 'request-new-episode-assetid', 'show-assetid-info', 'generate-script', 'thumbnail-selected', 'take-thumbnail', 'select-thumbnail'],
  data() {
    return {
      currentThumbnailIndex: 0,
      thumbnailError: false,
      showThumbnailPreview: false,
      showDatePicker: false,
      showTimePicker: false,
      timezoneOptions: [
        { label: 'ET', value: 'America/New_York' },
        { label: 'CT', value: 'America/Chicago' },
        { label: 'MT', value: 'America/Denver' },
        { label: 'PT', value: 'America/Los_Angeles' },
        { label: 'UTC', value: 'UTC' }
      ]
    };
  },
  props: {
    title: {
      type: String,
      default: 'Disaffected'
    },
    episodeInfo: {
      type: String,
      default: 'Episode Production Workspace'
    },
    episodeAssetId: {
      type: String,
      default: ''
    },
    slug: {
      type: String,
      default: ''
    },
    episodeTitle: {
      type: String,
      default: ''
    },
    subtitle: {
      type: String,
      default: ''
    },
    guest: {
      type: String,
      default: ''
    },
    description: {
      type: String,
      default: ''
    },
    airDate: {
      type: String,
      default: ''
    },
    airTime: {
      type: String,
      default: ''
    },
    airTimezone: {
      type: String,
      default: 'America/New_York'
    },
    showTimezone: {
      type: String,
      default: 'America/New_York'
    },
    productionStatus: {
      type: String,
      default: 'draft'
    },
    duration: {
      type: String,
      default: '00:00:00'
    },
    productionStatuses: {
      type: Array,
      default: () => [
        { title: 'Draft', value: 'draft' },
        { title: 'Approved', value: 'approved' },
        { title: 'Production', value: 'production' },
        { title: 'Completed', value: 'completed' }
      ]
    },
    loadingRundown: {
      type: Boolean,
      default: false
    },
    isDummy: {
      type: Boolean,
      default: false
    },
    saveState: {
      type: Object,
      default: () => ({
        hasChanges: false,
        buttonText: 'Synchronized',
        buttonColor: 'success',
        buttonIcon: 'mdi-check-circle',
        isDisabled: true,
        tooltip: 'Episode is synchronized - no changes to save'
      })
    },
    showMetadataPanel: {
      type: Boolean,
      default: false
    },
    isXttsConfigured: {
      type: Boolean,
      default: false
    },
    isReadingScript: {
      type: Boolean,
      default: false
    },
    episodeNumber: {
      type: String,
      default: ''
    },
    thumbnails: {
      type: Array,
      default: () => []
    },
    confirmedThumbnailUrl: {
      type: String,
      default: null
    },
    takenSourceUrl: {
      type: String,
      default: null
    }
  },
  watch: {
    thumbnails: {
      handler() {
        // Reset index when thumbnails change (e.g., episode change)
        this.thumbnailError = false;
        // If we have a confirmed thumbnail, navigate to it; otherwise start at 0
        this.navigateToConfirmedThumbnail();
      },
      immediate: true
    },
    takenSourceUrl: {
      handler() {
        // When confirmed thumbnail URL changes, navigate to it
        this.navigateToConfirmedThumbnail();
      }
    }
  },
  computed: {
    formattedAirDate() {
      // Format the ISO date string for display (e.g., "Jan 20, 2026")
      if (!this.airDate) return '';
      try {
        const date = new Date(this.airDate);
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
      } catch {
        return this.airDate;
      }
    },
    airDateForPicker() {
      // Convert ISO string to Date object for v-date-picker
      if (!this.airDate) return null;
      try {
        return new Date(this.airDate);
      } catch {
        return null;
      }
    },
    timezoneAbbreviation() {
      // Map IANA timezone to abbreviation
      const tzAbbreviations = {
        'America/New_York': 'ET',
        'America/Chicago': 'CT',
        'America/Denver': 'MT',
        'America/Los_Angeles': 'PT',
        'UTC': 'UTC',
        'America/Phoenix': 'AZ',
        'America/Anchorage': 'AK',
        'Pacific/Honolulu': 'HT'
      };
      return tzAbbreviations[this.showTimezone] || 'ET';
    },
    timezoneOffsetHours() {
      // Standard offsets (non-DST) in hours from UTC
      const offsets = {
        'America/New_York': -5,
        'America/Chicago': -6,
        'America/Denver': -7,
        'America/Los_Angeles': -8,
        'UTC': 0,
        'America/Phoenix': -7,
        'America/Anchorage': -9,
        'Pacific/Honolulu': -10
      };
      return offsets[this.showTimezone] ?? -5;
    },
    utcDateTime() {
      // Calculate UTC date/time from show timezone
      if (!this.airTime || !this.airDate) return '';
      try {
        // Create a date object in the show's timezone
        const localDate = new Date(this.airDate + 'T' + this.airTime + ':00');
        // Convert to UTC by subtracting the timezone offset
        const utcDate = new Date(localDate.getTime() - (this.timezoneOffsetHours * 60 * 60 * 1000));

        const month = utcDate.toLocaleDateString('en-US', { month: 'short' });
        const day = utcDate.getDate();
        const utcHours = String(utcDate.getHours()).padStart(2, '0');
        const utcMinutes = String(utcDate.getMinutes()).padStart(2, '0');

        return `${month} ${day}, ${utcHours}:${utcMinutes}`;
      } catch {
        return '';
      }
    },
    currentThumbnailUrl() {
      if (!this.thumbnails || this.thumbnails.length === 0) {
        return null;
      }
      return this.thumbnails[this.currentThumbnailIndex]?.url || null;
    },
    isCurrentThumbnailConfirmed() {
      // Check if the current thumbnail matches the one that was taken/confirmed
      if (!this.currentThumbnailUrl) {
        return false;
      }
      // Compare against the original source URL that was taken
      if (this.takenSourceUrl) {
        return this.currentThumbnailUrl === this.takenSourceUrl;
      }
      // Fallback: no thumbnail has been confirmed yet
      return false;
    },
    displayEpisodeInfo() {
      // Show episode title if available, otherwise fall back to episodeInfo prop
      if (this.episodeTitle && this.episodeTitle.trim()) {
        return this.episodeTitle;
      } else {
        return this.episodeInfo || 'Episode Production Workspace';
      }
    },
    statusColor() {
      // Status values now directly match color keys ('draft', 'approved', 'production', 'completed')
      const status = (this.productionStatus || '').toLowerCase();
      const colorName = getColorValue(status);
      const resolvedColor = resolveVuetifyColor(colorName);
      return resolvedColor || '#ccc'; // fallback to grey
    },
    statusFieldStyle() {
      if (!this.productionStatus) return {};
      
      // Status values now directly match color keys
      const status = this.productionStatus.toLowerCase();
      const colorName = getColorValue(status);
      const baseColor = resolveVuetifyColor(colorName);
      if (!baseColor) return {};
      
      // Create darker variant by reducing lightness
      const darkerTextColor = this.darkenColor(baseColor, 0.4); // 40% darker
      const darkerLabelColor = this.darkenColor(baseColor, 0.5); // 50% darker for labels
      
      // Create themed variations
      const bgColor = baseColor + '15'; // 15% opacity for subtle background
      const borderColor = baseColor + '80'; // 80% opacity for border
      
      return {
        '--status-bg-color': bgColor,
        '--status-border-color': borderColor,
        '--status-text-color': darkerTextColor,
        '--status-label-color': darkerLabelColor,
        '--status-base-color': baseColor
      };
    }
  },
  methods: {
    navigateToConfirmedThumbnail() {
      // Navigate to the confirmed thumbnail if it exists in the list
      if (!this.thumbnails || this.thumbnails.length === 0) {
        this.currentThumbnailIndex = 0;
        return;
      }

      if (this.takenSourceUrl) {
        // Find the index of the confirmed thumbnail
        const confirmedIndex = this.thumbnails.findIndex(
          thumb => thumb.url === this.takenSourceUrl
        );
        if (confirmedIndex >= 0) {
          this.currentThumbnailIndex = confirmedIndex;
          return;
        }
      }

      // Default to first thumbnail if no confirmed thumbnail found
      this.currentThumbnailIndex = 0;
    },
    handleDateSelect(date) {
      // Convert Date object to ISO string (YYYY-MM-DD)
      if (date) {
        const isoDate = date.toISOString().split('T')[0];
        this.$emit('update:airDate', isoDate);
      }
      this.showDatePicker = false;
    },
    handleTimeSelect(time) {
      this.$emit('update:airTime', time);
      this.showTimePicker = false;
    },
    prevThumbnail() {
      if (this.currentThumbnailIndex > 0) {
        this.currentThumbnailIndex--;
        this.$emit('thumbnail-selected', this.thumbnails[this.currentThumbnailIndex]);
      }
    },
    nextThumbnail() {
      if (this.currentThumbnailIndex < this.thumbnails.length - 1) {
        this.currentThumbnailIndex++;
        this.$emit('thumbnail-selected', this.thumbnails[this.currentThumbnailIndex]);
      }
    },
    handleThumbnailError(event) {
      console.warn('Thumbnail failed to load:', event.target.src);
      this.thumbnailError = true;
    },
    takeThumbnail() {
      if (this.currentThumbnailUrl) {
        this.$emit('take-thumbnail', {
          url: this.currentThumbnailUrl,
          thumbnail: this.thumbnails[this.currentThumbnailIndex]
        });
      }
    },
    getStatusBackgroundColor(status) {
      if (!status || typeof status !== 'string') return 'transparent';
      try {
        const colorValue = getColorValue(status.toLowerCase());
        if (!colorValue) return 'transparent';
        // Add some transparency to make text readable
        return colorValue + '20'; // Add 20% opacity
      } catch (error) {
        console.warn('Error getting status color:', error);
        return 'transparent';
      }
    },
    saveShowTitle() {
      // Emit save event or handle save logic
      console.log('Saving show title');
    },
    saveSlug() {
      console.log('Saving slug');
    },
    saveEpisodeTitle() {
      console.log('Saving episode title');
    },
    saveSubtitle() {
      console.log('Saving subtitle');
    },
    saveGuest() {
      console.log('Saving guest');
    },
    saveDescription() {
      console.log('Saving description');
    },
    darkenColor(hexColor, factor) {
      // Remove # if present
      const hex = hexColor.replace('#', '');
      
      // Parse RGB components
      const r = parseInt(hex.substr(0, 2), 16);
      const g = parseInt(hex.substr(2, 2), 16);
      const b = parseInt(hex.substr(4, 2), 16);
      
      // Darken by reducing each component
      const newR = Math.round(r * (1 - factor));
      const newG = Math.round(g * (1 - factor));
      const newB = Math.round(b * (1 - factor));
      
      // Convert back to hex
      const toHex = (c) => {
        const hex = c.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
      };
      
      return '#' + toHex(newR) + toHex(newG) + toHex(newB);
    }
  }
};
</script>

<style scoped>
.show-info-header {
  border-bottom: 1px solid #e0e0e0;
  min-height: 0;
  height: auto;
  max-height: none;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  background-color: white;
  transition: height 0.2s;
  margin-top: 20px; /* Push down to avoid overlap with app navigation */
  padding-top: 0;
  position: relative !important; /* Override any Vuetify position: sticky */
}

.full-width-bg {
  background-color: white;
  width: 100%;
}

.header-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  width: 100%;
  align-items: stretch;
}

.header-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
}

.section-1,
.section-2,
.section-3 {
  border-right: 1px dotted #ccc;
}

/* Section 2 - Split into 2.1 and 2.2 */
.section-2 {
  display: flex;
  align-items: stretch;
  overflow: hidden;
  padding: 0 !important;
}

.section-2-split {
  display: flex;
  width: 100%;
  height: 100%;
  gap: 0;
}

.section-2-1 {
  flex: 0 0 65%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  position: relative;
  border-right: 1px dotted #ddd;
  padding: 8px;
}

.section-2-2 {
  flex: 0 0 35%;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 8px;
}

.section-2-1 .thumbnail-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.section-2-1 .episode-thumbnail {
  flex-shrink: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-2-1 .thumbnail-placeholder {
  width: 100%;
  aspect-ratio: 16 / 9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 4px;
  border: 1px dashed #ccc;
}

.section-2-1 .thumbnail-placeholder .placeholder-label {
  font-size: 0.75rem;
  color: #999;
  margin-top: 4px;
}

.section-2-1 .thumbnail-placeholder .select-thumbnail-btn {
  font-size: 0.7rem;
  opacity: 0.7;
}

.section-2-1 .thumbnail-placeholder .select-thumbnail-btn:hover {
  opacity: 1;
}

/* Viewport clips the overflow - 16:9 aspect ratio */
.thumbnail-viewport {
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  border-radius: 4px;
  border: 3px solid #ccc;
  transition: border-color 0.3s ease, border-width 0.3s ease;
}

/* Green border when thumbnail is confirmed/taken */
.thumbnail-viewport.confirmed {
  border: 5px solid #4CAF50;
}

/* Track holds all thumbnails in a row and slides */
.thumbnail-track {
  display: flex;
  height: 100%;
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Thumbnail controls overlay - centered on the image */
.thumbnail-controls {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.thumbnail-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 12px;
  padding: 2px 8px;
  backdrop-filter: blur(4px);
}

.thumbnail-nav-btn {
  min-width: 20px !important;
  width: 20px !important;
  height: 20px !important;
  color: white !important;
}

.thumbnail-nav-btn:disabled {
  color: rgba(255, 255, 255, 0.4) !important;
}

.thumbnail-counter {
  font-size: 0.65rem;
  color: white;
  padding: 0 4px;
  font-weight: 500;
}

.take-btn {
  font-size: 0.65rem !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  height: 22px !important;
  padding: 0 8px !important;
}


.placeholder-label {
  font-size: 0.7rem;
  color: #999;
  margin-top: 4px;
}

.section-1 {
  /* Episode title and description */
}

.section-2,
.section-3 {
  /* Reserved for future use */
}

.section-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.placeholder-text {
  color: #ccc;
  font-size: 0.75rem;
  font-style: italic;
}

.section-4 {
  /* Action buttons - align to top right */
  flex-direction: row;
  align-items: flex-start;
  justify-content: flex-end;
}

.header-action-btn {
  min-width: 70px !important;
  height: 24px !important;
  font-size: 0.7rem !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
}

.field-with-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
}

.field-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.episode-title-input {
  width: 100%;
}

.episode-description-input {
  width: 100%;
}

/* Styling for the episode fields */
:deep(.episode-title-input .v-field__input) {
  font-size: 0.875rem !important;
  font-weight: bold !important;
  padding: 4px 8px !important;
  min-height: 28px !important;
}

:deep(.episode-description-input .v-field__input) {
  font-size: 0.875rem !important;
  padding: 4px 8px !important;
  line-height: 1.3 !important;
}

/* Remove borders and style backgrounds */
:deep(.episode-title-input .v-field__outline),
:deep(.episode-description-input .v-field__outline) {
  display: none !important;
}

:deep(.episode-title-input .v-field) {
  background-color: #f5f5f5 !important;
  border-radius: 4px;
}

:deep(.episode-description-input .v-field) {
  background-color: #f5f5f5 !important;
  border-radius: 4px;
}

/* Air Date/Time Row - side by side, condensed */
.air-datetime-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.air-datetime-row .air-date-field {
  flex: 0 0 50%;
}

.air-datetime-row .air-time-et-field {
  flex: 0 0 25%;
}

.air-datetime-row .air-utc-field {
  flex: 0 0 calc(25% - 16px);
}

.air-datetime-row .field-label {
  font-size: 0.65rem;
}

.air-utc-display {
  width: 100%;
  font-size: 0.875rem;
  padding: 6px 8px;
  min-height: 28px;
  background-color: #e8e8e8;
  border: none;
  border-radius: 4px;
  color: rgba(0, 0, 0, 0.6);
  font-family: inherit;
  cursor: default;
}

/* Air Date/Time input styling to match other fields */
:deep(.air-date-input .v-field__input),
:deep(.air-time-input .v-field__input) {
  font-size: 0.875rem !important;
  padding: 4px 8px !important;
  min-height: 28px !important;
}

:deep(.air-date-input .v-field__outline),
:deep(.air-time-input .v-field__outline) {
  display: none !important;
}

:deep(.air-date-input .v-field),
:deep(.air-time-input .v-field) {
  background-color: #f5f5f5 !important;
  border-radius: 4px;
}

/* Native time input for 24-hour format */
.air-date-native-input,
.air-time-native-input {
  width: 100%;
  font-size: 0.875rem;
  padding: 6px 8px;
  min-height: 28px;
  background-color: #f5f5f5;
  border: none;
  border-radius: 4px;
  color: rgba(0, 0, 0, 0.87);
  font-family: inherit;
  cursor: pointer;
}

.air-date-native-input:focus,
.air-time-native-input:focus {
  outline: 2px solid var(--v-theme-primary, #1976d2);
  outline-offset: -2px;
}

/* Air time with timezone layout */
.air-time-with-tz {
  display: flex;
  align-items: center;
  gap: 4px;
}

.air-time-with-tz .air-time-native-input {
  flex: 1;
  min-width: 60px;
}

.timezone-select {
  flex: 0 0 auto;
  max-width: 55px;
}

:deep(.timezone-select .v-field__input) {
  font-size: 0.75rem !important;
  padding: 4px !important;
  min-height: 28px !important;
}

:deep(.timezone-select .v-select__selection-text) {
  font-size: 0.75rem !important;
}

.show-title-fit {
  width: 100%;
  display: block;
  white-space: normal;
  word-wrap: break-word;
  font-size: clamp(0.7rem, 1.4vw, 1.1rem) !important;
  font-weight: bold !important;
  text-transform: uppercase !important;
}

.fields-area {
  display: grid;
  grid-template-columns: 200px;
  grid-gap: 0;
  row-gap: 0;
  flex: 2 1 600px;
  justify-content: flex-end;
  align-self: flex-start;
  justify-items: end;
}

.fields-area > * {
  grid-column: 1;
}

.showinfo-field {
  width: 200px !important; /* Fixed width for all fields */
  min-width: 200px !important;
  max-width: 200px !important;
  font-size: 0.8rem !important; /* 20% smaller font */
}

/* Clean Vuetify component styling with consistent dimensions */
:deep(.showinfo-field .v-field__input) {
  padding: 4px 8px !important; /* Reduced internal padding */
  min-height: 24px !important; /* Reduced height */
  font-size: 0.75rem !important; /* Smaller font */
  line-height: 1.2 !important;
}

:deep(.showinfo-field .v-field__field) {
  height: 24px !important; /* Reduced height */
  min-height: 24px !important;
}

:deep(.showinfo-field .v-field__outline) {
  --v-field-border-width: 2px !important; /* Slightly thicker border for theming */
}

/* Consistent select dropdown styling */
:deep(.showinfo-field .v-select__selection) {
  font-size: 0.8rem !important;
  line-height: 1.2 !important;
}

/* Status-themed field coloring using database colors */
:deep(.status-field .v-field),
:deep(.airdate-field .v-field),
:deep(.duration-field .v-field) {
  background-color: var(--status-bg-color, transparent) !important;
}

:deep(.status-field .v-field__outline),
:deep(.airdate-field .v-field__outline),
:deep(.duration-field .v-field__outline) {
  border-color: var(--status-border-color, currentColor) !important;
}

/* Status-themed text coloring - darker variants for all field values */
:deep(.status-field .v-field__input input),
:deep(.airdate-field .v-field__input input),
:deep(.duration-field .v-field__input input),
:deep(.status-field .v-select__selection) {
  color: var(--status-text-color, currentColor) !important;
  font-weight: 500 !important;
}

/* Status-themed labels - much darker variants */
:deep(.status-field .v-field-label),
:deep(.airdate-field .v-field-label),
:deep(.duration-field .v-field-label) {
  color: var(--status-label-color, currentColor) !important;
  opacity: 1 !important;
  font-weight: 500 !important;
}

/* Status indicator directly below duration field */
.status-indicator {
  width: 200px !important; /* Same width as text fields */
  height: 32px;
  background-color: var(--status-base-color, #ccc);
  color: #ffffff;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  margin-top: 4px; /* Small gap between duration field and status */
  grid-column: 2; /* Place in same column as other fields */
}

:deep(.v-label) {
  top: 50% !important;
  transform: translateY(-50%) !important;
}

:deep(.v-field--focused .v-label),
:deep(.v-field--dirty .v-label) {
  top: 0 !important;
  transform: translateY(-50%) scale(0.75) !important;
}

.asset-id-display {
  font-family: 'Courier New', monospace !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
  margin-top: 2px !important;
}

.show-title-container {
  display: flex;
  align-items: center;
  width: 100%;
  line-height: 1;
}

.dummy-indicator {
  color: #ff0000 !important;
  font-weight: bold !important;
  font-size: clamp(0.7rem, 1.4vw, 1.1rem) !important;
  text-transform: uppercase !important;
  margin-left: 4px;
  align-self: center;
  line-height: 1;
}

/* Editable field styling */
.show-title-input {
  width: 100% !important;
  margin-bottom: 2px !important;
}

.show-title-input :deep(.v-field__input) {
  font-size: clamp(0.7rem, 1.4vw, 1.1rem) !important;
  font-weight: bold !important;
  text-transform: uppercase !important;
  padding: 0 !important;
  min-height: auto !important;
  width: 100% !important;
  line-height: 1 !important;
  display: flex !important;
  align-items: center !important;
}

.show-title-input :deep(.v-field__field) {
  padding: 0 !important;
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  min-height: auto !important;
}

.slug-input,
.episode-title-input,
.subtitle-input,
.guest-input,
.description-input {
  width: 100% !important;
  margin-bottom: 4px !important;
}

.slug-input :deep(.v-field__input),
.subtitle-input :deep(.v-field__input),
.guest-input :deep(.v-field__input) {
  font-size: 0.75rem !important;
  padding: 1px 0 !important;
  min-height: auto !important;
  width: 100% !important;
}

.description-input :deep(.v-field__input) {
  font-size: 0.75rem !important;
  padding: 1px 0 !important;
  min-height: auto !important;
  width: 100% !important;
}

.slug-input :deep(.v-field__field),
.subtitle-input :deep(.v-field__field),
.guest-input :deep(.v-field__field),
.description-input :deep(.v-field__field) {
  width: 100% !important;
}

.show-title-input :deep(.v-field__outline),
.slug-input :deep(.v-field__outline),
.subtitle-input :deep(.v-field__outline),
.guest-input :deep(.v-field__outline),
.description-input :deep(.v-field__outline) {
  display: none !important;
}

/* Keep visible borders for episode title and description fields */

/* Show subtle underline on hover/focus */
.show-title-input:hover :deep(.v-field__field),
.slug-input:hover :deep(.v-field__field),
.subtitle-input:hover :deep(.v-field__field),
.guest-input:hover :deep(.v-field__field),
.description-input:hover :deep(.v-field__field) {
  border-bottom: 1px solid rgba(0,0,0,0.2) !important;
}

.show-title-input:focus-within :deep(.v-field__field),
.slug-input:focus-within :deep(.v-field__field),
.subtitle-input:focus-within :deep(.v-field__field),
.guest-input:focus-within :deep(.v-field__field),
.description-input:focus-within :deep(.v-field__field) {
  border-bottom: 2px solid var(--v-theme-primary) !important;
}

/* Icon styling for all editable fields with icons */
.slug-input :deep(.v-field__prepend-inner),
.subtitle-input :deep(.v-field__prepend-inner),
.guest-input :deep(.v-field__prepend-inner),
.description-input :deep(.v-field__prepend-inner) {
  padding-right: 4px !important;
  opacity: 0.6;
}

.slug-input :deep(.v-field__prepend-inner .v-icon),
.subtitle-input :deep(.v-field__prepend-inner .v-icon),
.guest-input :deep(.v-field__prepend-inner .v-icon),
.description-input :deep(.v-field__prepend-inner .v-icon) {
  font-size: 14px !important;
}

/* Action Buttons Area */
.action-buttons-area {
  flex-shrink: 0;
  min-width: fit-content;
}

/* Button Styles - Match EditorPanel toolbar buttons */
.save-all-btn {
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
  height: 48px !important;
  min-height: 48px !important;
}

.save-all-btn:disabled {
  background-color: rgb(var(--v-theme-success)) !important;
  color: white !important;
  opacity: 1 !important;
}

.metadata-toggle-btn {
  height: 48px !important;
  min-height: 48px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

.more-options-btn {
  height: 48px !important;
  min-height: 48px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

/* Thumbnail Preview Modal */
.thumbnail-preview-modal {
  background: #1a1a1a;
}

.thumbnail-preview-modal .v-card-title {
  background: #2a2a2a;
  color: white;
}

.thumbnail-preview-modal .v-card-text {
  background: #1a1a1a;
  min-height: 60vh;
}

.thumbnail-preview-image {
  max-width: 100%;
  max-height: 75vh;
  object-fit: contain;
  border-radius: 4px;
}

.thumbnail-preview-modal .v-card-actions {
  background: #2a2a2a;
  color: white;
}
</style>
