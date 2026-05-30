<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="700" scrollable>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-library</v-icon>
        Select {{ displayTypeName }} from Library
        <v-spacer></v-spacer>
        <v-btn icon size="small" variant="text" @click="cancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text>
        <!-- Search and filters -->
        <v-row class="mb-4">
          <v-col cols="8">
            <v-text-field
              v-model="searchQuery"
              label="Search by title or customer"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              @input="debouncedSearch"
            ></v-text-field>
          </v-col>
          <v-col cols="4">
            <v-select
              v-model="priorityFilter"
              label="Priority"
              :items="priorityOptions"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            ></v-select>
          </v-col>
        </v-row>

        <!-- Loading state -->
        <div v-if="loading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" size="40"></v-progress-circular>
          <p class="mt-4 text-body-2">Loading library items...</p>
        </div>

        <!-- Empty state -->
        <div v-else-if="libraryItems.length === 0" class="text-center py-8">
          <v-icon size="64" color="grey-lighten-1">mdi-package-variant</v-icon>
          <p class="mt-4 text-body-1">No {{ displayTypeName.toLowerCase() }}s found in library</p>
          <v-btn color="primary" variant="outlined" class="mt-4" @click="createNew">
            <v-icon class="mr-2">mdi-plus</v-icon>
            Create New {{ displayTypeName }}
          </v-btn>
        </div>

        <!-- Library items list -->
        <v-list v-else lines="two" class="library-list">
          <v-list-item
            v-for="item in libraryItems"
            :key="item.asset_id"
            @click="selectItem(item)"
            :class="{ 'selected-item': selectedItem?.asset_id === item.asset_id }"
            class="library-item mb-2"
          >
            <template v-slot:prepend>
              <v-avatar :color="getTypeColor(itemType)" size="40">
                <v-icon color="white">{{ getTypeIcon(itemType) }}</v-icon>
              </v-avatar>
            </template>

            <v-list-item-title class="font-weight-medium">
              {{ item.title }}
            </v-list-item-title>

            <v-list-item-subtitle>
              <span v-if="item.customer_name" class="mr-4">
                <v-icon size="small" class="mr-1">mdi-account</v-icon>
                {{ item.customer_name }}
              </span>
              <span v-if="item.duration" class="mr-4">
                <v-icon size="small" class="mr-1">mdi-clock-outline</v-icon>
                {{ item.duration }}
              </span>
              <span v-if="item.placement_count > 0">
                <v-icon size="small" class="mr-1">mdi-calendar-check</v-icon>
                {{ item.placement_count }} scheduled
              </span>
            </v-list-item-subtitle>

            <template v-slot:append>
              <div class="d-flex flex-column align-end">
                <v-chip v-if="item.priority === 'high'" color="error" size="x-small" class="mb-1">High</v-chip>
                <v-chip v-else-if="item.priority === 'low'" color="grey" size="x-small" class="mb-1">Low</v-chip>
                <span class="text-caption text-grey">
                  {{ formatDate(item.valid_from) }} - {{ formatDate(item.valid_until) }}
                </span>
              </div>
            </template>
          </v-list-item>
        </v-list>

        <!-- Pagination info -->
        <div v-if="!loading && totalItems > libraryItems.length" class="text-center mt-4">
          <v-btn variant="text" @click="loadMore" :loading="loadingMore">
            Load more ({{ libraryItems.length }} of {{ totalItems }})
          </v-btn>
        </div>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-btn color="secondary" variant="outlined" @click="createNew">
          <v-icon class="mr-2">mdi-plus</v-icon>
          Create New
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn color="secondary" @click="cancel">Cancel</v-btn>
        <v-btn
          color="primary"
          @click="confirmSelection"
          :disabled="!selectedItem"
        >
          <v-icon class="mr-2">mdi-check</v-icon>
          Add to Rundown
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { getColorValue } from '@/utils/themeColorMap.js';
import { registerModalEsc } from '@/composables/useModalStack';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  itemType: {
    type: String,
    required: true
  },
  episodeNumber: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:show', 'select', 'create-new']);

// Data
const libraryItems = ref([]);
const selectedItem = ref(null);
const loading = ref(false);
const loadingMore = ref(false);
const searchQuery = ref('');
const priorityFilter = ref(null);
const totalItems = ref(0);
const offset = ref(0);
const limit = ref(20);
let searchTimeout = null;
const priorityOptions = ref([
  { title: 'All Priorities', value: null },
  { title: 'High Priority', value: 'high' },
  { title: 'Normal Priority', value: 'normal' },
  { title: 'Low Priority', value: 'low' }
]);

// Computed
const displayTypeName = computed(() => {
  const typeNames = {
    'advertisement': 'Advertisement',
    'ad': 'Advertisement',
    'promo': 'Promo',
    'cta': 'Call to Action',
    'transition': 'Transition',
    'stinger': 'Stinger'
  };
  return typeNames[props.itemType] || props.itemType;
});

// Methods — ESC handled by global modal stack
registerModalEsc(() => props.show, () => cancel(), 'ContentLibraryPickerModal');

function reset() {
  libraryItems.value = [];
  selectedItem.value = null;
  searchQuery.value = '';
  priorityFilter.value = null;
  offset.value = 0;
}

async function loadLibraryItems() {
  loading.value = true;

  try {
    const typeMapping = {
      'ad': 'advertisement'
    };
    const queryType = typeMapping[props.itemType] || props.itemType;

    const params = new URLSearchParams({
      item_type: queryType,
      is_active: 'true',
      limit: limit.value.toString(),
      offset: offset.value.toString()
    });

    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }

    const today = new Date().toISOString();
    params.append('valid_on', today);

    const response = await axios.get(`/api/content-library/?${params.toString()}`);

    if (response.data) {
      if (offset.value === 0) {
        libraryItems.value = response.data.items || [];
      } else {
        libraryItems.value = [...libraryItems.value, ...(response.data.items || [])];
      }
      totalItems.value = response.data.total || 0;
    }
  } catch (error) {
    console.error('Error loading library items:', error);
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

function loadMore() {
  loadingMore.value = true;
  offset.value += limit.value;
  loadLibraryItems();
}

function debouncedSearch() {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  searchTimeout = setTimeout(() => {
    offset.value = 0;
    libraryItems.value = [];
    loadLibraryItems();
  }, 300);
}

function selectItem(item) {
  selectedItem.value = item;
}

function confirmSelection() {
  if (selectedItem.value) {
    emit('select', {
      libraryItem: selectedItem.value,
      itemType: props.itemType
    });
    cancel();
  }
}

function createNew() {
  emit('create-new', {
    itemType: props.itemType
  });
  cancel();
}

function cancel() {
  emit('update:show', false);
}

function getTypeColor(type) {
  return getColorValue(type);
}

function getTypeIcon(type) {
  const icons = {
    'advertisement': 'mdi-currency-usd',
    'ad': 'mdi-currency-usd',
    'promo': 'mdi-bullhorn',
    'cta': 'mdi-hand-pointing-right',
    'transition': 'mdi-swap-horizontal',
    'stinger': 'mdi-flash'
  };
  return icons[type] || 'mdi-file-document';
}

function formatDate(dateStr) {
  if (!dateStr) return 'No limit';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

// Watchers
watch(() => props.show, (newVal) => {
  if (newVal) {
    loadLibraryItems();
  } else {
    reset();
  }
});

watch(priorityFilter, () => {
  offset.value = 0;
  libraryItems.value = [];
  loadLibraryItems();
});

// Lifecycle — ESC auto-registered; only the search debounce needs cleanup
onBeforeUnmount(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
});
</script>

<style scoped>
.library-list {
  max-height: 400px;
  overflow-y: auto;
}

.library-item {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.library-item:hover {
  border-color: rgba(var(--v-theme-primary), 0.5);
  background-color: rgba(var(--v-theme-primary), 0.04);
}

.selected-item {
  border-color: rgb(var(--v-theme-primary)) !important;
  background-color: rgba(var(--v-theme-primary), 0.08) !important;
}
</style>
