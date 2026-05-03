<template>
  <div class="content-library-manager">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-library</v-icon>
        Content Library Manager
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="showCreateDialog = true">
          <v-icon class="mr-2">mdi-plus</v-icon>
          Add Library Item
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-tabs v-model="activeTab" class="mb-4">
          <v-tab value="library">Library Items</v-tab>
          <v-tab value="type-settings">Rundown Item Types</v-tab>
        </v-tabs>

        <v-window v-model="activeTab">
          <!-- Library Items Tab -->
          <v-window-item value="library">
            <!-- Filters -->
            <v-row class="mb-4">
              <v-col cols="4">
                <v-select
                  v-model="filterType"
                  label="Filter by Type"
                  :items="typeOptions"
                  clearable
                  variant="outlined"
                  density="compact"
                  hide-details
                ></v-select>
              </v-col>
              <v-col cols="4">
                <v-text-field
                  v-model="searchQuery"
                  label="Search"
                  prepend-inner-icon="mdi-magnify"
                  variant="outlined"
                  density="compact"
                  hide-details
                  clearable
                ></v-text-field>
              </v-col>
              <v-col cols="4">
                <v-select
                  v-model="filterStatus"
                  label="Status"
                  :items="statusOptions"
                  variant="outlined"
                  density="compact"
                  hide-details
                ></v-select>
              </v-col>
            </v-row>

            <!-- Library Items Table -->
            <v-data-table
              :headers="libraryHeaders"
              :items="filteredLibraryItems"
              :loading="loadingLibrary"
              class="elevation-1"
              density="compact"
            >
              <template #[`item.item_type`]="{ item }">
                <v-chip :color="getTypeColor(item.item_type)" size="small" label>
                  {{ item.item_type }}
                </v-chip>
              </template>

              <template #[`item.is_active`]="{ item }">
                <v-icon :color="item.is_active ? 'success' : 'grey'" size="small">
                  {{ item.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
                </v-icon>
              </template>

              <template #[`item.valid_range`]="{ item }">
                <span class="text-caption">
                  {{ formatDate(item.valid_from) }} - {{ formatDate(item.valid_until) }}
                </span>
              </template>

              <template #[`item.placement_count`]="{ item }">
                <v-chip v-if="item.placement_count > 0" color="primary" size="x-small">
                  {{ item.placement_count }}
                </v-chip>
                <span v-else class="text-grey">0</span>
              </template>

              <template #[`item.actions`]="{ item }">
                <v-btn icon size="small" @click="editItem(item)">
                  <v-icon size="small">mdi-pencil</v-icon>
                </v-btn>
                <v-btn icon size="small" @click="viewUsage(item)">
                  <v-icon size="small">mdi-calendar-clock</v-icon>
                </v-btn>
                <v-btn icon size="small" @click="toggleItemActive(item)">
                  <v-icon size="small" :color="item.is_active ? 'grey' : 'success'">
                    {{ item.is_active ? 'mdi-eye-off' : 'mdi-eye' }}
                  </v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-window-item>

          <!-- Type Settings Tab -->
          <v-window-item value="type-settings">
            <v-alert type="info" variant="tonal" class="mb-4">
              Configure which content types are <strong>reusable</strong>. When a type is marked as reusable,
              users will be prompted to select from the library instead of creating a new item.
            </v-alert>

            <!-- Core Rundown Items Section -->
            <h3 class="text-subtitle-1 font-weight-bold mb-2 mt-4">
              <v-icon class="mr-1">mdi-television-classic</v-icon>
              Core Rundown Items
            </h3>
            <p class="text-caption text-grey mb-2">
              Built-in types that cannot be deleted. Configure behavior flags like reusability.
            </p>
            <v-data-table
              :headers="typeSettingsHeaders"
              :items="coreTypeSettings"
              :loading="loadingTypeSettings"
              class="elevation-1 mb-6"
              density="compact"
            >
              <template #[`item.is_reusable`]="{ item }">
                <v-switch
                  v-model="item.is_reusable"
                  color="primary"
                  hide-details
                  density="compact"
                  @change="updateTypeSetting(item)"
                ></v-switch>
              </template>

              <template #[`item.color`]="{ item }">
                <v-chip v-if="item.color" :color="item.color" size="small" label>
                  {{ item.color }}
                </v-chip>
              </template>

              <template #[`item.is_active`]="{ item }">
                <v-icon :color="item.is_active ? 'success' : 'grey'" size="small">
                  {{ item.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
                </v-icon>
              </template>
            </v-data-table>

            <!-- Custom Rundown Items Section -->
            <div class="d-flex align-center mb-2 mt-6">
              <h3 class="text-subtitle-1 font-weight-bold">
                <v-icon class="mr-1">mdi-shape-plus</v-icon>
                Custom Rundown Items
              </h3>
              <v-spacer></v-spacer>
              <v-btn color="primary" size="small" @click="showCustomTypeDialog = true">
                <v-icon class="mr-1">mdi-plus</v-icon>
                Add Custom Type
              </v-btn>
            </div>
            <p class="text-caption text-grey mb-2">
              User-defined types that can be added or removed as needed.
            </p>
            <v-data-table
              :headers="customTypeHeaders"
              :items="customTypeSettings"
              :loading="loadingTypeSettings"
              class="elevation-1"
              density="compact"
            >
              <template #[`item.is_reusable`]="{ item }">
                <v-switch
                  v-model="item.is_reusable"
                  color="primary"
                  hide-details
                  density="compact"
                  @change="updateTypeSetting(item)"
                ></v-switch>
              </template>

              <template #[`item.color`]="{ item }">
                <v-chip v-if="item.color" :color="item.color" size="small" label>
                  {{ item.color }}
                </v-chip>
              </template>

              <template #[`item.icon`]="{ item }">
                <v-icon v-if="item.icon" size="small">{{ item.icon }}</v-icon>
              </template>

              <template #[`item.actions`]="{ item }">
                <v-btn icon size="small" color="error" @click="deleteCustomType(item)">
                  <v-icon size="small">mdi-delete</v-icon>
                </v-btn>
              </template>

              <template #no-data>
                <div class="text-center py-4 text-grey">
                  No custom types defined yet. Click "Add Custom Type" to create one.
                </div>
              </template>
            </v-data-table>

            <v-btn color="secondary" class="mt-4" @click="seedTypeSettings" :loading="seeding">
              <v-icon class="mr-2">mdi-database-plus</v-icon>
              Seed Default Core Settings
            </v-btn>
          </v-window-item>
        </v-window>
      </v-card-text>
    </v-card>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="600" persistent>
      <v-card>
        <v-card-title>
          {{ editingItem ? 'Edit Library Item' : 'Create Library Item' }}
        </v-card-title>

        <v-card-text>
          <v-form ref="formRef">
            <v-select
              v-model="formData.item_type"
              label="Content Type"
              :items="reusableTypes"
              :rules="[v => !!v || 'Type is required']"
              required
            ></v-select>

            <v-text-field
              v-model="formData.title"
              label="Title"
              :rules="[v => !!v || 'Title is required']"
              required
            ></v-text-field>

            <v-text-field
              v-model="formData.customer_name"
              label="Customer/Sponsor Name"
            ></v-text-field>

            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.duration"
                  label="Duration"
                  placeholder="00:00:30"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="formData.priority"
                  label="Priority"
                  :items="['high', 'normal', 'low']"
                ></v-select>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.valid_from"
                  label="Valid From"
                  type="date"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.valid_until"
                  label="Valid Until"
                  type="date"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-textarea
              v-model="formData.script_content"
              label="Script Content"
              rows="4"
            ></v-textarea>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" @click="saveItem" :loading="saving">
            {{ editingItem ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Usage History Dialog -->
    <v-dialog v-model="showUsageDialog" max-width="600">
      <v-card>
        <v-card-title>
          Usage History: {{ usageItem?.title }}
        </v-card-title>

        <v-card-text>
          <v-list v-if="usageHistory.length > 0" lines="two" density="compact">
            <v-list-item
              v-for="usage in usageHistory"
              :key="usage.id"
              :class="{ 'text-decoration-line-through': usage.removed_at }"
            >
              <v-list-item-title>
                Episode {{ usage.episode_number }}
              </v-list-item-title>
              <v-list-item-subtitle>
                {{ formatDateTime(usage.placed_at) }}
                <span v-if="usage.removed_at" class="text-error">
                  (Removed {{ formatDateTime(usage.removed_at) }})
                </span>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
          <div v-else class="text-center py-8 text-grey">
            No usage history yet
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showUsageDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Create Custom Type Dialog -->
    <v-dialog v-model="showCustomTypeDialog" max-width="500" persistent>
      <v-card>
        <v-card-title>
          <v-icon class="mr-2">mdi-shape-plus</v-icon>
          Create Custom Rundown Item Type
        </v-card-title>

        <v-card-text>
          <v-form ref="customTypeFormRef">
            <v-text-field
              v-model="customTypeForm.type_name"
              label="Type ID"
              hint="Lowercase letters and underscores only (e.g., news_brief)"
              :rules="[
                v => !!v || 'Type ID is required',
                v => /^[a-z][a-z0-9_]*$/.test(v) || 'Use lowercase letters, numbers, and underscores only'
              ]"
              required
              persistent-hint
            ></v-text-field>

            <v-text-field
              v-model="customTypeForm.display_name"
              label="Display Name"
              hint="Human-readable name (e.g., News Brief)"
              :rules="[v => !!v || 'Display name is required']"
              required
              persistent-hint
            ></v-text-field>

            <v-textarea
              v-model="customTypeForm.description"
              label="Description"
              rows="2"
              hint="Brief description of this type"
              persistent-hint
            ></v-textarea>

            <v-row>
              <v-col cols="6">
                <v-select
                  v-model="customTypeForm.color"
                  label="Color"
                  :items="colorOptions"
                  item-title="title"
                  item-value="value"
                >
                  <template #item="{ props, item }">
                    <v-list-item v-bind="props">
                      <template #prepend>
                        <div
                          class="color-preview mr-2"
                          :style="{ backgroundColor: item.value, width: '20px', height: '20px', borderRadius: '4px' }"
                        ></div>
                      </template>
                    </v-list-item>
                  </template>
                  <template #selection="{ item }">
                    <div class="d-flex align-center">
                      <div
                        class="color-preview mr-2"
                        :style="{ backgroundColor: item.value, width: '16px', height: '16px', borderRadius: '4px' }"
                      ></div>
                      {{ item.title }}
                    </div>
                  </template>
                </v-select>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="customTypeForm.icon"
                  label="Icon"
                  hint="MDI icon name (e.g., mdi-newspaper)"
                  persistent-hint
                >
                  <template #prepend-inner>
                    <v-icon>{{ customTypeForm.icon || 'mdi-shape' }}</v-icon>
                  </template>
                </v-text-field>
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="customTypeForm.default_duration"
                  label="Default Duration"
                  placeholder="00:00:30"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-switch
                  v-model="customTypeForm.is_reusable"
                  label="Reusable"
                  hint="Show in library picker"
                  persistent-hint
                  color="primary"
                ></v-switch>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="closeCustomTypeDialog">Cancel</v-btn>
          <v-btn color="primary" @click="createCustomType" :loading="creatingCustomType">
            Create Type
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { getColorValue } from '@/utils/themeColorMap.js';

// Template refs
const formRef = ref(null);
const customTypeFormRef = ref(null);

// Reactive state
const activeTab = ref('library');

// Library items
const libraryItems = ref([]);
const loadingLibrary = ref(false);
const filterType = ref(null);
const filterStatus = ref('active');
const searchQuery = ref('');

// Type settings
const typeSettings = ref([]);
const loadingTypeSettings = ref(false);
const seeding = ref(false);

// Create/Edit dialog
const showCreateDialog = ref(false);
const editingItem = ref(null);
const saving = ref(false);
const formData = ref({
  item_type: '',
  title: '',
  customer_name: '',
  duration: '',
  priority: 'normal',
  valid_from: '',
  valid_until: '',
  script_content: ''
});

// Usage dialog
const showUsageDialog = ref(false);
const usageItem = ref(null);
const usageHistory = ref([]);

// Custom type dialog
const showCustomTypeDialog = ref(false);
const creatingCustomType = ref(false);
const customTypeForm = ref({
  type_name: '',
  display_name: '',
  description: '',
  color: 'grey',
  icon: 'mdi-shape',
  default_duration: '00:00:30',
  is_reusable: false
});

// Color options for custom types
const colorOptions = [
  { title: 'Grey', value: 'grey' },
  { title: 'Blue Grey', value: 'blue-grey' },
  { title: 'Blue', value: 'blue' },
  { title: 'Indigo', value: 'indigo' },
  { title: 'Deep Purple', value: 'deep-purple' },
  { title: 'Purple', value: 'purple' },
  { title: 'Pink', value: 'pink' },
  { title: 'Red', value: 'red' },
  { title: 'Deep Orange', value: 'deep-orange' },
  { title: 'Orange', value: 'orange' },
  { title: 'Amber', value: 'amber' },
  { title: 'Yellow', value: 'yellow' },
  { title: 'Lime', value: 'lime' },
  { title: 'Light Green', value: 'light-green' },
  { title: 'Green', value: 'green' },
  { title: 'Teal', value: 'teal' },
  { title: 'Cyan', value: 'cyan' },
  { title: 'Light Blue', value: 'light-blue' },
  { title: 'Brown', value: 'brown' }
];

// Table headers
const libraryHeaders = [
  { title: 'Type', key: 'item_type', width: '100px' },
  { title: 'Title', key: 'title' },
  { title: 'Customer', key: 'customer_name' },
  { title: 'Duration', key: 'duration', width: '80px' },
  { title: 'Valid Range', key: 'valid_range', width: '180px' },
  { title: 'Placements', key: 'placement_count', width: '100px', align: 'center' },
  { title: 'Active', key: 'is_active', width: '70px', align: 'center' },
  { title: 'Actions', key: 'actions', width: '120px', align: 'center', sortable: false }
];

const typeSettingsHeaders = [
  { title: 'Type', key: 'type_name' },
  { title: 'Display Name', key: 'display_name' },
  { title: 'Reusable', key: 'is_reusable', width: '100px' },
  { title: 'Color', key: 'color', width: '100px' },
  { title: 'Default Duration', key: 'default_duration', width: '120px' },
  { title: 'Active', key: 'is_active', width: '70px', align: 'center' }
];

const customTypeHeaders = [
  { title: 'Type ID', key: 'type_name' },
  { title: 'Display Name', key: 'display_name' },
  { title: 'Description', key: 'description' },
  { title: 'Reusable', key: 'is_reusable', width: '100px' },
  { title: 'Color', key: 'color', width: '100px' },
  { title: 'Icon', key: 'icon', width: '70px', align: 'center' },
  { title: 'Actions', key: 'actions', width: '80px', align: 'center', sortable: false }
];

const typeOptions = [
  { title: 'All Types', value: null },
  { title: 'Advertisement', value: 'advertisement' },
  { title: 'Promo', value: 'promo' },
  { title: 'CTA', value: 'cta' }
];

const statusOptions = [
  { title: 'Active Only', value: 'active' },
  { title: 'All Items', value: 'all' },
  { title: 'Inactive Only', value: 'inactive' }
];

// Computed
const filteredLibraryItems = computed(() => {
  let items = libraryItems.value;

  if (filterType.value) {
    items = items.filter(item => item.item_type === filterType.value);
  }

  if (filterStatus.value === 'active') {
    items = items.filter(item => item.is_active);
  } else if (filterStatus.value === 'inactive') {
    items = items.filter(item => !item.is_active);
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    items = items.filter(item =>
      item.title?.toLowerCase().includes(query) ||
      item.customer_name?.toLowerCase().includes(query)
    );
  }

  return items;
});

const reusableTypes = computed(() => {
  return typeSettings.value
    .filter(s => s.is_reusable)
    .map(s => ({ title: s.display_name, value: s.type_name }));
});

const coreTypeSettings = computed(() => {
  return typeSettings.value.filter(s => s.is_core === true);
});

const customTypeSettings = computed(() => {
  return typeSettings.value.filter(s => s.is_core === false);
});

// Methods
async function loadLibraryItems() {
  loadingLibrary.value = true;
  try {
    const token = localStorage.getItem('auth-token');
    const response = await axios.get('/api/content-library/?include_test_data=false&limit=500', {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    libraryItems.value = response.data.items || [];
  } catch (error) {
    console.error('Error loading library items:', error);
  } finally {
    loadingLibrary.value = false;
  }
}

async function loadTypeSettings() {
  loadingTypeSettings.value = true;
  try {
    const token = localStorage.getItem('auth-token');
    const response = await axios.get('/api/content-library/type-settings/', {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    typeSettings.value = response.data.settings || [];
    console.log('Type settings loaded:', typeSettings.value.length, 'items');
    console.log('Core types:', typeSettings.value.filter(s => s.is_core === true).length);
    console.log('Custom types:', typeSettings.value.filter(s => s.is_core === false).length);
  } catch (error) {
    console.error('Error loading type settings:', error);
  } finally {
    loadingTypeSettings.value = false;
  }
}

async function seedTypeSettings() {
  seeding.value = true;
  try {
    const token = localStorage.getItem('auth-token');
    await axios.post('/api/content-library/type-settings/seed', {}, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    await loadTypeSettings();
  } catch (error) {
    console.error('Error seeding type settings:', error);
  } finally {
    seeding.value = false;
  }
}

async function updateTypeSetting(setting) {
  try {
    const token = localStorage.getItem('auth-token');
    await axios.patch(`/api/content-library/type-settings/${setting.type_name}`, {
      is_reusable: setting.is_reusable
    }, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
  } catch (error) {
    console.error('Error updating type setting:', error);
    // Revert the change
    setting.is_reusable = !setting.is_reusable;
  }
}

function editItem(item) {
  editingItem.value = item;
  formData.value = {
    item_type: item.item_type,
    title: item.title,
    customer_name: item.customer_name || '',
    duration: item.duration || '',
    priority: item.priority || 'normal',
    valid_from: item.valid_from ? item.valid_from.split('T')[0] : '',
    valid_until: item.valid_until ? item.valid_until.split('T')[0] : '',
    script_content: item.script_content || ''
  };
  showCreateDialog.value = true;
}

async function viewUsage(item) {
  usageItem.value = item;
  usageHistory.value = [];
  showUsageDialog.value = true;

  try {
    const response = await axios.get(`/api/content-library/${item.asset_id}/usage`);
    usageHistory.value = response.data.placements || [];
  } catch (error) {
    console.error('Error loading usage history:', error);
  }
}

async function toggleItemActive(item) {
  try {
    await axios.patch(`/api/content-library/${item.asset_id}`, {
      is_active: !item.is_active
    });
    item.is_active = !item.is_active;
  } catch (error) {
    console.error('Error toggling item status:', error);
  }
}

async function saveItem() {
  const { valid } = await formRef.value.validate();
  if (!valid) return;

  saving.value = true;
  try {
    const data = {
      ...formData.value,
      valid_from: formData.value.valid_from ? new Date(formData.value.valid_from).toISOString() : null,
      valid_until: formData.value.valid_until ? new Date(formData.value.valid_until).toISOString() : null
    };

    if (editingItem.value) {
      await axios.patch(`/api/content-library/${editingItem.value.asset_id}`, data);
    } else {
      await axios.post('/api/content-library/', data);
    }

    await loadLibraryItems();
    closeDialog();
  } catch (error) {
    console.error('Error saving library item:', error);
  } finally {
    saving.value = false;
  }
}

function closeDialog() {
  showCreateDialog.value = false;
  editingItem.value = null;
  formData.value = {
    item_type: '',
    title: '',
    customer_name: '',
    duration: '',
    priority: 'normal',
    valid_from: '',
    valid_until: '',
    script_content: ''
  };
}

function getTypeColor(type) {
  return getColorValue(type);
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

function formatDateTime(dateStr) {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
}

// Custom type management methods
async function createCustomType() {
  if (customTypeFormRef.value) {
    const { valid } = await customTypeFormRef.value.validate();
    if (!valid) return;
  }

  creatingCustomType.value = true;
  try {
    const token = localStorage.getItem('auth-token');
    await axios.post('/api/content-library/custom-types/', customTypeForm.value, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    await loadTypeSettings();
    closeCustomTypeDialog();
  } catch (error) {
    console.error('Error creating custom type:', error);
    const message = error.response?.data?.detail || 'Failed to create custom type';
    alert(message);
  } finally {
    creatingCustomType.value = false;
  }
}

async function deleteCustomType(typeItem) {
  if (!confirm(`Are you sure you want to delete the custom type "${typeItem.display_name}"? This action cannot be undone.`)) {
    return;
  }

  try {
    const token = localStorage.getItem('auth-token');
    await axios.delete(`/api/content-library/custom-types/${typeItem.type_name}`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    await loadTypeSettings();
  } catch (error) {
    console.error('Error deleting custom type:', error);
    const message = error.response?.data?.detail || 'Failed to delete custom type';
    alert(message);
  }
}

function closeCustomTypeDialog() {
  showCustomTypeDialog.value = false;
  customTypeForm.value = {
    type_name: '',
    display_name: '',
    description: '',
    color: 'grey',
    icon: 'mdi-shape',
    default_duration: '00:00:30',
    is_reusable: false
  };
  // Reset form validation
  if (customTypeFormRef.value) {
    customTypeFormRef.value.resetValidation();
  }
}

// Lifecycle
onMounted(() => {
  loadLibraryItems();
  loadTypeSettings();
});
</script>

<style scoped>
.content-library-manager {
  padding: 16px;
}
</style>
