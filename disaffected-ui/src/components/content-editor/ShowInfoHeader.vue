<template>
  <v-card class="show-info-header full-width-bg" flat>
    <v-card-text class="pa-0">
      <div v-if="loadingRundown" style="margin-bottom: 8px;">
        <v-progress-linear indeterminate color="primary" height="4" rounded></v-progress-linear>
      </div>
      <div class="header-container">
        <!-- Section 1: Episode Info — split left/right -->
        <div class="header-section section-1">
          <div class="section-1-split">
            <!-- Left: Title & Description -->
            <div class="section-1-left">
              <div class="title-ep-badge" v-if="episodeNumber">EP {{ episodeNumber }}</div>
              <div class="episode-title-row">
                <v-text-field
                  :model-value="episodeTitle"
                  @update:model-value="$emit('update:episodeTitle', $event)"
                  variant="plain"
                  density="compact"
                  class="episode-title-input"
                  hide-details
                  single-line
                  placeholder="Untitled Episode"
                />
              </div>
              <div class="ep-desc-wrapper" :class="{ 'ep-desc-llm': descriptionModel }">
                <textarea
                  ref="epDescTextareaRef"
                  :value="description || ''"
                  @input="resizeEpDescTextarea(); $emit('update:description', $event.target.value)"
                  class="ep-desc-textarea"
                  :class="{ 'ep-desc-llm-text': descriptionModel }"
                  placeholder="Type a description of this episode"
                ></textarea>
              </div>
              <div class="ep-desc-actions-row">
                <v-btn
                  size="x-small"
                  variant="tonal"
                  color="primary"
                  class="edit-details-btn"
                  prepend-icon="mdi-square-edit-outline"
                  @click="episodeDetailsModalOpen = true"
                  :disabled="!episodeNumber"
                >
                  Edit Episode Details
                  <v-tooltip activator="parent" location="top">Open the full episode editor</v-tooltip>
                </v-btn>
                <span v-if="descriptionModel" class="ep-desc-model-label">{{ descriptionModel }}</span>
                <v-btn
                  size="x-small"
                  variant="flat"
                  class="ep-desc-action-btn"
                  :class="{ 'ep-desc-btn-on': autoGenerateEnabled, 'ep-desc-btn-off': !autoGenerateEnabled }"
                  @click="$emit('update-segment-field', { field: 'auto_generate_enabled', value: !autoGenerateEnabled })"
                >
                  <v-icon size="10" class="mr-half">{{ autoGenerateEnabled ? 'mdi-lightning-bolt' : 'mdi-lightning-bolt-outline' }}</v-icon>
                  <span>Auto</span>
                  <v-tooltip activator="parent" location="top">{{ autoGenerateEnabled ? 'Auto-describe ON' : 'Auto-describe OFF' }}</v-tooltip>
                </v-btn>
                <v-btn
                  v-if="description"
                  size="x-small"
                  variant="flat"
                  class="ep-desc-action-btn ep-desc-btn-on"
                  @click="$emit('update:description', ''); $emit('update-segment-field', { field: 'auto_generate_enabled', value: true })"
                >
                  <v-icon size="10" class="mr-half">mdi-refresh</v-icon>
                  <span>Regen</span>
                  <v-tooltip activator="parent" location="top">Clear and regenerate episode description</v-tooltip>
                </v-btn>
                <v-btn
                  v-if="description"
                  size="x-small"
                  variant="flat"
                  class="ep-desc-action-btn ep-desc-btn-off"
                  @click="$emit('update:description', '')"
                >
                  <v-icon size="10" class="mr-half">mdi-close</v-icon>
                  <span>Clear</span>
                  <v-tooltip activator="parent" location="top">Clear episode description</v-tooltip>
                </v-btn>
              </div>
            </div>
            <!-- Right: Air Schedule -->
            <div class="section-1-right">
              <div class="air-schedule-block">
                <div class="air-field">
                  <span class="air-label">AIR DATE</span>
                  <v-menu v-model="showDatePicker" :close-on-content-click="false" location="bottom">
                    <template v-slot:activator="{ props }">
                      <span class="air-value clickable" v-bind="props">{{ formattedAirDate || 'Set date' }}</span>
                    </template>
                    <v-date-picker :model-value="airDateForPicker" @update:model-value="handleDateSelect" color="primary"></v-date-picker>
                  </v-menu>
                </div>
                <div class="air-field">
                  <span class="air-label">AIR TIME ({{ timezoneAbbreviation }})</span>
                  <v-menu v-model="showTimePicker" :close-on-content-click="false" location="bottom">
                    <template v-slot:activator="{ props }">
                      <span class="air-value clickable" v-bind="props">{{ airTime || 'Set time' }}</span>
                    </template>
                    <v-time-picker :model-value="airTime" @update:model-value="handleTimeSelect" format="24hr" scrollable></v-time-picker>
                  </v-menu>
                </div>
                <div class="air-divider"></div>
                <div class="air-field">
                  <span class="air-label">UTC</span>
                  <span class="air-value air-utc-val">{{ utcDateTime || '--' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Section 2: Thumbnail -->
        <div class="header-section section-2">
          <div class="section-2-split">
            <!-- Section 2.1: Thumbnail Carousel (left) -->
            <div class="section-2-1">
              <!-- Thumbnail Carousel -->
              <div class="thumbnail-container" v-if="thumbnails && thumbnails.length > 0">
                <div
                  class="thumbnail-viewport"
                  :class="thumbnailViewportClasses"
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
                  <!-- Thumbnail Controls Overlay (inside viewport so they anchor to the image, not the whitespace) -->
                  <div class="thumbnail-controls" @click.stop>
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
                  <!-- Take + Download (side-by-side) -->
                  <div class="thumbnail-action-row">
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
                    <v-btn
                      size="x-small"
                      color="deep-purple"
                      variant="elevated"
                      @click="downloadThumbnail"
                      class="take-btn"
                      :disabled="!currentThumbnailUrl"
                    >
                      <v-icon size="x-small" class="mr-1">mdi-download</v-icon>
                      Download
                      <v-tooltip activator="parent" location="top">Download current thumbnail</v-tooltip>
                    </v-btn>
                  </div>
                  </div>
                </div>
              </div>
              <!-- No Thumbnail — Show generic logo placeholder -->
              <div v-else class="thumbnail-placeholder" @click="$emit('select-thumbnail')" style="cursor: pointer;">
                <img
                  src="/media_assets/generic/hot-logo.jpg"
                  alt="Show logo placeholder"
                  class="episode-thumbnail placeholder-logo"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Section 3: Action Buttons (stacked, full height) -->
        <div class="header-section section-3 section-3-stacked">
          <!-- More Options Dropdown -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                variant="flat"
                rounded="0"
                class="episode-action-btn"
                color="grey-darken-1"
                v-bind="props"
              >
                <v-icon size="small" class="mr-1">mdi-dots-horizontal</v-icon>
                More
              </v-btn>
            </template>
            <v-list>
              <v-list-item @click="$emit('toggle-script-reading')" :disabled="!isTtsConfigured">
                <v-list-item-title>
                  <v-icon size="small" class="mr-2" :color="isReadingScript ? 'error' : 'primary'">{{ isReadingScript ? 'mdi-stop' : 'mdi-volume-high' }}</v-icon>
                  {{ isReadingScript ? 'Stop Reading' : 'Read Script Aloud' }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ isTtsConfigured ? 'Read with TTS' : 'TTS not configured' }}
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

          <!-- Save Button -->
          <v-btn
            variant="flat"
            rounded="0"
            class="episode-action-btn"
            color="primary"
            :loading="saving"
            :disabled="!hasUnsavedChanges"
            @click="$emit('save-episode')"
          >
            <v-icon size="small" class="mr-1">mdi-content-save</v-icon>
            Save
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

    <EpisodeDetailsModal
      v-model="episodeDetailsModalOpen"
      :episode-number="episodeNumber"
      :episode-asset-id="episodeAssetId"
      :episode-title="episodeTitle"
      :subtitle="subtitle"
      :slug="slug"
      :guest="guest"
      :description="description"
      :description-model="descriptionModel"
      :air-date="airDate"
      :air-time="airTime"
      :air-timezone="airTimezone"
      :production-status="productionStatus"
      :production-statuses="productionStatuses"
      :duration="duration"
      @update:episode-title="$emit('update:episodeTitle', $event)"
      @update:subtitle="$emit('update:subtitle', $event)"
      @update:slug="$emit('update:slug', $event)"
      @update:guest="$emit('update:guest', $event)"
      @update:description="$emit('update:description', $event)"
      @update:air-date="$emit('update:airDate', $event)"
      @update:air-time="$emit('update:airTime', $event)"
      @update:air-timezone="$emit('update:airTimezone', $event)"
      @update:production-status="$emit('update:productionStatus', $event)"
      @save="$emit('save-episode')"
    />

  </v-card>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import { getColorValue, resolveVuetifyColor } from '../../utils/themeColorMap';
import { useContentIndicators } from '@/composables/useContentIndicators';
import EpisodeDetailsModal from './modals/EpisodeDetailsModal.vue';

const props = defineProps({
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
  descriptionModel: {
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
      { title: 'Scheduled', value: 'scheduled' },
      { title: 'Draft', value: 'draft' },
      { title: 'Production', value: 'production' },
      { title: 'Running', value: 'running' },
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
  isTtsConfigured: {
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
  autoGenerateEnabled: {
    type: Boolean,
    default: true
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
  },
  selectedItem: {
    type: Object,
    default: null
  },
  saving: {
    type: Boolean,
    default: false
  },
  hasUnsavedChanges: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:airDate', 'update:airTime', 'update:airTimezone', 'update:productionStatus', 'update:title', 'update:slug', 'update:episodeTitle', 'update:subtitle', 'update:guest', 'update:description', 'save-all', 'save-episode', 'toggle-metadata-panel', 'toggle-script-reading', 'request-new-episode-assetid', 'show-assetid-info', 'generate-script', 'thumbnail-selected', 'take-thumbnail', 'select-thumbnail', 'update-segment-field', 'update-episode-field', 'convert-thumbnail-to-png']);

const { llmTextColor } = useContentIndicators() // eslint-disable-line no-unused-vars

const epDescTextareaRef = ref(null)

function resizeEpDescTextarea() {
  const el = epDescTextareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

watch(
  () => props.description,
  (newVal) => nextTick(() => {
    const el = epDescTextareaRef.value
    if (el) el.value = newVal || ''
    resizeEpDescTextarea()
  }),
  { immediate: true }
)

onMounted(() => nextTick(resizeEpDescTextarea))

// data
const currentThumbnailIndex = ref(0);
const assetIdCopied = ref(false); // eslint-disable-line no-unused-vars
const thumbnailError = ref(false);
const thumbnailConverting = ref(false);
const thumbnailConvertSuccess = ref(false);
const showThumbnailPreview = ref(false);
const episodeDetailsModalOpen = ref(false);
const showDatePicker = ref(false);
const showTimePicker = ref(false);
const timezoneOptions = ref([ // eslint-disable-line no-unused-vars
  { label: 'ET', value: 'America/New_York' },
  { label: 'CT', value: 'America/Chicago' },
  { label: 'MT', value: 'America/Denver' },
  { label: 'PT', value: 'America/Los_Angeles' },
  { label: 'UTC', value: 'UTC' }
]);
const priorityOptions = ref(['low', 'normal', 'high', 'urgent']); // eslint-disable-line no-unused-vars

// computed
const formattedAirDate = computed(() => {
  if (!props.airDate) return '';
  try {
    const date = new Date(props.airDate);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  } catch {
    return props.airDate;
  }
});

const airDateForPicker = computed(() => {
  if (!props.airDate) return null;
  try {
    return new Date(props.airDate);
  } catch {
    return null;
  }
});

const timezoneAbbreviation = computed(() => {
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
  return tzAbbreviations[props.showTimezone] || 'ET';
});

const utcDateTime = computed(() => {
  if (!props.airTime || !props.airDate) return '';
  try {
    // Normalize airDate to YYYY-MM-DD (it may arrive as ISO with time, or formatted)
    let dateStr = String(props.airDate).trim();
    const isoMatch = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})/);
    let y, m, d;
    if (isoMatch) {
      y = +isoMatch[1]; m = +isoMatch[2]; d = +isoMatch[3];
    } else {
      const parsed = new Date(dateStr);
      if (isNaN(parsed.getTime())) return '';
      y = parsed.getFullYear(); m = parsed.getMonth() + 1; d = parsed.getDate();
    }
    const timeMatch = String(props.airTime).match(/^(\d{1,2}):(\d{2})/);
    if (!timeMatch) return '';
    const hh = +timeMatch[1];
    const mm = +timeMatch[2];
    if (isNaN(hh) || isNaN(mm)) return '';

    const tz = props.showTimezone || props.airTimezone || 'America/New_York';

    // Compute the UTC instant whose wall-clock time in `tz` equals (y,m,d,hh,mm).
    // Trick: treat (y,m,d,hh,mm) as if it were UTC, then ask what time that
    // instant displays as in `tz`; the difference is the tz's offset at that moment.
    const naiveUTC = Date.UTC(y, m - 1, d, hh, mm);
    const fmt = new Intl.DateTimeFormat('en-US', {
      timeZone: tz, hour12: false,
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    });
    const parts = fmt.formatToParts(new Date(naiveUTC)).reduce((a, p) => {
      if (p.type !== 'literal') a[p.type] = p.value;
      return a;
    }, {});
    const tzReadAsUTC = Date.UTC(
      +parts.year, +parts.month - 1, +parts.day,
      +parts.hour === 24 ? 0 : +parts.hour, +parts.minute
    );
    const offsetMs = tzReadAsUTC - naiveUTC;
    const realUTC = new Date(naiveUTC - offsetMs);
    if (isNaN(realUTC.getTime())) return '';

    const monthName = realUTC.toLocaleDateString('en-US', { month: 'short', timeZone: 'UTC' });
    const dayU = realUTC.getUTCDate();
    const hhU = String(realUTC.getUTCHours()).padStart(2, '0');
    const mmU = String(realUTC.getUTCMinutes()).padStart(2, '0');
    return `${monthName} ${dayU}, ${hhU}:${mmU}`;
  } catch {
    return '';
  }
});

const currentThumbnailUrl = computed(() => {
  if (!props.thumbnails || props.thumbnails.length === 0) {
    return null;
  }
  return props.thumbnails[currentThumbnailIndex.value]?.url || null;
});

const isCurrentThumbnailNonPng = computed(() => {
  const url = currentThumbnailUrl.value;
  if (!url) return false;
  const ext = url.split('.').pop().toLowerCase();
  return ext !== 'png';
});

const thumbnailViewportClasses = computed(() => {
  return {
    'confirmed': isCurrentThumbnailConfirmed.value,
    'non-png': isCurrentThumbnailNonPng.value && !thumbnailConverting.value && !thumbnailConvertSuccess.value,
    'converting': thumbnailConverting.value,
    'convert-success': thumbnailConvertSuccess.value
  };
});

const isCurrentThumbnailConfirmed = computed(() => {
  if (!currentThumbnailUrl.value) {
    return false;
  }
  if (props.takenSourceUrl) {
    return currentThumbnailUrl.value === props.takenSourceUrl;
  }
  return false;
});

const displayEpisodeInfo = computed(() => { // eslint-disable-line no-unused-vars
  if (props.episodeTitle && props.episodeTitle.trim()) {
    return props.episodeTitle;
  } else {
    return props.episodeInfo || 'Episode Production Workspace';
  }
});

const statusColor = computed(() => { // eslint-disable-line no-unused-vars
  const status = (props.productionStatus || '').toLowerCase();
  const colorName = getColorValue(status);
  const resolvedColor = resolveVuetifyColor(colorName);
  return resolvedColor || '#ccc';
});

const statusFieldStyle = computed(() => { // eslint-disable-line no-unused-vars
  if (!props.productionStatus) return {};

  const status = props.productionStatus.toLowerCase();
  const colorName = getColorValue(status);
  const baseColor = resolveVuetifyColor(colorName);
  if (!baseColor) return {};

  const darkerTextColor = darkenColor(baseColor, 0.4);
  const darkerLabelColor = darkenColor(baseColor, 0.5);

  const bgColor = baseColor + '15';
  const borderColor = baseColor + '80';

  return {
    '--status-bg-color': bgColor,
    '--status-border-color': borderColor,
    '--status-text-color': darkerTextColor,
    '--status-label-color': darkerLabelColor,
    '--status-base-color': baseColor
  };
});

// watchers
watch(() => props.thumbnails, () => {
  thumbnailError.value = false;
  navigateToConfirmedThumbnail();
}, { immediate: true });

watch(() => props.takenSourceUrl, () => {
  navigateToConfirmedThumbnail();
});

watch(currentThumbnailUrl, (url) => {
  thumbnailConverting.value = false;
  thumbnailConvertSuccess.value = false;
  if (url && isCurrentThumbnailNonPng.value) {
    nextTick(() => {
      emit('convert-thumbnail-to-png', {
        url: url,
        thumbnail: props.thumbnails[currentThumbnailIndex.value]
      });
      thumbnailConverting.value = true;
    });
  }
});

// methods
function copyAssetId() { // eslint-disable-line no-unused-vars
  const id = props.selectedItem?.asset_id || props.selectedItem?.id;
  if (id) {
    navigator.clipboard.writeText(String(id));
    assetIdCopied.value = true;
    setTimeout(() => { assetIdCopied.value = false; }, 2000);
  }
}

function navigateToConfirmedThumbnail() {
  if (!props.thumbnails || props.thumbnails.length === 0) {
    currentThumbnailIndex.value = 0;
    return;
  }

  if (props.takenSourceUrl) {
    const confirmedIndex = props.thumbnails.findIndex(
      thumb => thumb.url === props.takenSourceUrl
    );
    if (confirmedIndex >= 0) {
      currentThumbnailIndex.value = confirmedIndex;
      return;
    }
  }

  currentThumbnailIndex.value = 0;
}

function handleDateSelect(date) {
  if (date) {
    const isoDate = date.toISOString().split('T')[0];
    emit('update:airDate', isoDate);
  }
  showDatePicker.value = false;
}

function handleTimeSelect(time) {
  emit('update:airTime', time);
  showTimePicker.value = false;
}

function prevThumbnail() {
  if (currentThumbnailIndex.value > 0) {
    currentThumbnailIndex.value--;
    emit('thumbnail-selected', props.thumbnails[currentThumbnailIndex.value]);
  }
}

function nextThumbnail() {
  if (currentThumbnailIndex.value < props.thumbnails.length - 1) {
    currentThumbnailIndex.value++;
    emit('thumbnail-selected', props.thumbnails[currentThumbnailIndex.value]);
  }
}

function handleThumbnailError(event) {
  console.warn('Thumbnail failed to load:', event.target.src);
  thumbnailError.value = true;
}

function onThumbnailConverted() {
  thumbnailConverting.value = false;
  thumbnailConvertSuccess.value = true;
  setTimeout(() => {
    thumbnailConvertSuccess.value = false;
  }, 10000);
}

function takeThumbnail() {
  if (currentThumbnailUrl.value) {
    emit('take-thumbnail', {
      url: currentThumbnailUrl.value,
      thumbnail: props.thumbnails[currentThumbnailIndex.value]
    });
  }
}

async function downloadThumbnail() {
  const url = currentThumbnailUrl.value;
  if (!url) return;

  // Build a sensible filename: prefer the source filename, fall back to episode+index
  const srcName = url.split('?')[0].split('/').pop() || '';
  const ext = srcName.includes('.') ? srcName.split('.').pop() : 'png';
  const filename = srcName || `episode-${props.episodeNumber || 'thumbnail'}-${currentThumbnailIndex.value + 1}.${ext}`;

  try {
    const token = localStorage.getItem('auth-token');
    const response = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
  } catch (err) {
    console.error('Failed to download thumbnail:', err);
    // Fallback: open the URL directly so the browser's native save-as handles it
    window.open(url, '_blank');
  }
}

function getStatusBackgroundColor(status) { // eslint-disable-line no-unused-vars
  if (!status || typeof status !== 'string') return 'transparent';
  try {
    const colorValue = getColorValue(status.toLowerCase());
    if (!colorValue) return 'transparent';
    return colorValue + '20';
  } catch (error) { // eslint-disable-line no-unused-vars
    console.warn('Error getting status color:', error);
    return 'transparent';
  }
}

function saveShowTitle() { // eslint-disable-line no-unused-vars
  console.log('Saving show title');
}

function saveSlug() { // eslint-disable-line no-unused-vars
  console.log('Saving slug');
}

function saveEpisodeTitle() { // eslint-disable-line no-unused-vars
  console.log('Saving episode title');
}

function saveSubtitle() { // eslint-disable-line no-unused-vars
  console.log('Saving subtitle');
}

function saveGuest() { // eslint-disable-line no-unused-vars
  console.log('Saving guest');
}

function saveDescription() { // eslint-disable-line no-unused-vars
  console.log('Saving description');
}

function darkenColor(hexColor, factor) {
  const hex = hexColor.replace('#', '');

  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);

  const newR = Math.round(r * (1 - factor));
  const newG = Math.round(g * (1 - factor));
  const newB = Math.round(b * (1 - factor));

  const toHex = (c) => {
    const h = c.toString(16);
    return h.length === 1 ? '0' + h : h;
  };

  return '#' + toHex(newR) + toHex(newG) + toHex(newB);
}

// Expose methods accessed by parent via $refs
defineExpose({
  onThumbnailConverted
});
</script>

<style scoped>
.show-info-header {
  border-bottom: 2.25px dotted rgba(25, 118, 210, 0.75) !important;
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
  max-height: 150px; /* 50% taller than the previous 100px */
  overflow: hidden;
}

.full-width-bg {
  background-color: white;
  width: 100%;
}

.header-container {
  display: grid;
  /* Column 1: thumbnail (intrinsic width, min 260px so it doesn't collapse)
     Column 2: episode info (takes all remaining space)
     Column 3: action buttons (intrinsic width) */
  grid-template-columns: minmax(260px, auto) 1fr auto;
  gap: 0;
  width: 100%;
  align-items: stretch;
}

.header-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 2px 8px;
}

.section-1,
.section-2 {
  border-right: 1px dotted rgba(0, 0, 0, 0.15);
}

/* Move thumbnail (section 2) to the far left */
.section-2 {
  order: -1;
}

/* Section 1 — Split layout */
.section-1-split {
  display: flex;
  gap: 12px;
  height: 100%;
}

.section-1-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0;
  min-width: 0;
}

.section-1-right {
  flex: 0 0 140px;
  display: flex;
  align-items: flex-start;
  border-left: 1px dotted rgba(0, 0, 0, 0.1);
  padding-left: 12px;
}

/* Air schedule block */
.air-schedule-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.air-field {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.air-label {
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #9e9e9e;
  text-transform: uppercase;
}

.air-value {
  font-size: 13px;
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;
  color: #212121;
  letter-spacing: 0.3px;
}

.air-value.clickable {
  cursor: pointer;
  transition: color 0.15s;
}

.air-value.clickable:hover {
  color: #1976D2;
}

.air-utc-val {
  color: #757575;
  font-size: 11px;
  font-weight: 500;
}

.air-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.08);
  margin: 2px 0;
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
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 4px;
  max-height: 140px; /* Scaled with the 150px header */
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
  object-fit: contain; /* Display full image, never crop */
  background: #000;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-2-1 .thumbnail-placeholder .placeholder-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.section-2-1 .thumbnail-placeholder {
  width: 100%;
  height: 100%;
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

/* Viewport sized by height so the thumbnail always fits within the header.
   Width auto-computes from the 16:9 aspect ratio. */
.thumbnail-viewport {
  position: relative; /* anchor for .thumbnail-controls overlay */
  height: 100%;
  max-height: 100%;
  aspect-ratio: 16 / 9;
  width: auto;
  max-width: 100%;
  overflow: hidden;
  border-radius: 4px;
  border: 3px solid #ccc;
  transition: border-color 0.3s ease, border-width 0.3s ease;
}

/* Green border when thumbnail is confirmed/taken */
.thumbnail-viewport.confirmed {
  border: 5px solid #4CAF50;
}

/* Red border for non-PNG thumbnails */
.thumbnail-viewport.non-png {
  border: 5px solid #F44336;
}

/* Pulsing border during conversion */
.thumbnail-viewport.converting {
  border: 5px solid #F44336;
  animation: pulse-border 1.5s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% { border-color: #F44336; }
  50% { border-color: #FF8A80; }
}

/* Blue border on successful conversion, fades out over 10s */
.thumbnail-viewport.convert-success {
  border: 5px solid #2196F3;
  animation: fade-blue-border 10s ease-out forwards;
}

@keyframes fade-blue-border {
  0% { border-color: #2196F3; }
  70% { border-color: #2196F3; }
  100% { border-color: #ccc; }
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
  right: 8px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
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

.thumbnail-action-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.take-btn {
  font-size: 0.5rem !important;      /* was 0.65rem */
  text-transform: none !important;
  letter-spacing: 0 !important;
  height: 17px !important;            /* was 22px */
  padding: 0 6px !important;          /* was 0 8px */
}

.take-btn :deep(.v-icon) {
  font-size: 11px !important;         /* scaled down to match */
}

.take-btn :deep(.mr-1) {
  margin-right: 2px !important;
}


.placeholder-label {
  font-size: 0.7rem;
  color: #999;
  margin-top: 4px;
}

.section-1 {
  /* Episode title and description */
}

.section-2 {
  /* Thumbnail section */
}

/* Section 3: Action buttons */
.section-3 {
  flex-direction: row;
  align-items: flex-start;
  justify-content: flex-end;
  padding: 4px 8px !important;
}

.asset-id-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 0;
  font-size: 0.75rem;
}

.asset-id-label {
  color: #666;
  font-weight: 500;
}

.asset-id-value {
  font-family: monospace;
  color: #1565C0;
  font-weight: 600;
}

.copy-btn {
  opacity: 0.5;
}

.copy-btn:hover {
  opacity: 1;
}

.copied-indicator {
  color: #4CAF50;
  font-size: 0.7rem;
  font-weight: 500;
}

.segment-dur-pri-row {
  display: flex;
  gap: 6px;
  align-items: flex-start;
}

.segment-meta-input {
  font-size: 0.8rem;
}

:deep(.segment-meta-input .v-field) {
  border-radius: 4px !important;
  background-color: rgba(0, 0, 0, 0.03) !important;
}

:deep(.segment-meta-input .v-field__input) {
  font-size: 0.8rem !important;
  padding: 2px 6px !important;
  min-height: 24px !important;
}

:deep(.segment-meta-input textarea) {
  font-size: 0.8rem !important;
  padding: 2px 6px !important;
  line-height: 1.3 !important;
}

:deep(.segment-meta-input .v-field__outline) {
  --v-field-border-opacity: 0.15;
}

:deep(.segment-meta-input .v-select__selection) {
  font-size: 0.8rem !important;
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

/* section-4 removed — merged into section-3 */

/* Section 3 — buttons side-by-side, filling full height */
.section-3-stacked {
  display: flex !important;
  flex-direction: row !important;
  align-items: stretch !important;
  gap: 0 !important;
  padding: 0 !important;
}

.episode-action-btn {
  flex: 1 1 0 !important;
  min-width: 0 !important;
  height: 100% !important;
  font-size: 0.65rem !important;
  text-transform: none !important;
  letter-spacing: 0.2px !important;
  font-weight: 600 !important;
  white-space: nowrap;
  border-radius: 0 !important;
  padding: 0 10px !important;
}

.episode-save-btn {
  flex: 1 !important;
  min-width: 0 !important;
  width: 100% !important;
  font-size: 0.65rem !important;
  text-transform: none !important;
  letter-spacing: 0.2px !important;
  font-weight: 600 !important;
  white-space: nowrap;
  border-radius: 0 !important;
  padding: 0 10px !important;
}

.header-action-btn {
  flex: 1 !important;
  width: 100% !important;
  min-width: 0 !important;
  height: auto !important;
  font-size: 0.7rem !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  border-radius: 0 !important;
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

/* Episode badge */
.title-ep-badge {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 1.5px;
  color: #1976D2;
  text-transform: uppercase;
  line-height: 1;
  margin-bottom: 4px;
  opacity: 0.7;
}

.auto-describe-toggle {
  margin-left: 2px;
}
.auto-describe-switch {
  flex: 0 0 auto;
}
.auto-describe-switch :deep(.v-selection-control) {
  min-height: 20px;
}
.auto-describe-label {
  font-size: 0.68rem !important;
  font-weight: 500;
  letter-spacing: 0.3px;
  cursor: default;
}

.episode-title-input {
  width: 100%;
  margin-top: 0 !important;
}

.episode-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.episode-title-row .episode-title-input {
  flex: 1;
  min-width: 0;
}

.edit-details-btn {
  flex: 0 0 auto;
  text-transform: none !important;
  letter-spacing: 0 !important;
  font-size: 0.7rem !important;
  height: 24px !important;
  min-height: 24px !important;
  padding: 0 8px !important;
}

.episode-description-input {
  width: 100%;
  margin-top: -14px !important;
}

.ep-desc-wrapper {
  width: 100%;
  margin-top: -6px;
  border-radius: 3px;
  transition: border-color 0.2s;
}

.ep-desc-wrapper.ep-desc-llm {
  border: 1px solid var(--llm-indicator-border, #7e57c2);
  border-radius: 3px;
  padding: 1px;
}

.ep-desc-textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  overflow: hidden;
  background: transparent;
  font-size: 0.85rem;
  line-height: 1.4;
  color: #555;
  padding: 2px 4px;
  font-family: inherit;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.ep-desc-textarea::placeholder {
  color: #999;
  font-style: normal;
}

.ep-desc-textarea.ep-desc-llm-text {
  color: var(--llm-indicator-text, #7e57c2);
  font-style: italic;
}

.ep-desc-actions-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  margin-top: 0px;
  margin-bottom: 2px;
}

.ep-desc-actions-row .edit-details-btn {
  margin-right: auto;
}

.ep-desc-model-label {
  font-size: 0.5rem;
  color: var(--llm-indicator-text, #7e57c2);
  opacity: 0.7;
  letter-spacing: 0.2px;
  line-height: 1;
}

.mr-half {
  margin-right: 2px;
}

.ep-desc-action-btn {
  text-transform: none !important;
  font-size: 0.55rem !important;
  height: 16px !important;
  padding: 0 4px !important;
  min-width: 0 !important;
  border-radius: 3px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.ep-desc-btn-on {
  background-color: var(--llm-indicator-text, #7e57c2) !important;
  color: white !important;
}

.ep-desc-btn-off {
  background-color: #e0e0e0 !important;
  color: #999 !important;
}

/* Title — bold, editorial headline */
:deep(.episode-title-input .v-field__input) {
  font-size: 1.15rem !important;
  font-weight: 800 !important;
  padding: 0 !important;
  min-height: 26px !important;
  color: #111 !important;
  letter-spacing: -0.4px;
  font-family: 'Roboto', 'Segoe UI', sans-serif;
}

:deep(.episode-title-input .v-field__input::placeholder) {
  color: #888 !important;
  font-weight: 400 !important;
  font-style: normal;
  letter-spacing: 0;
}

/* Description — subdued, secondary text */
:deep(.episode-description-input .v-field__input) {
  font-size: 0.78rem !important;
  padding: 0 !important;
  min-height: 20px !important;
  line-height: 1.3 !important;
  color: #555 !important;
  letter-spacing: 0.1px;
}

:deep(.episode-description-input .v-field__input::placeholder) {
  color: #777 !important;
  font-style: normal;
  font-weight: 300 !important;
}

/* Plain variant — no background, no border */
:deep(.episode-title-input .v-field),
:deep(.episode-description-input .v-field) {
  background: transparent !important;
}

/* Air date/time — old row styles removed, now in section-1-right */

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
