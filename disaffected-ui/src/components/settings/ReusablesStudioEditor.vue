<template>
  <v-card class="reusables-editor h-100 d-flex flex-column">
    <!-- Header -->
    <v-card-title class="d-flex align-center py-2 px-4 border-b">
      <v-btn icon variant="text" size="small" @click="$emit('close')">
        <v-icon>mdi-close</v-icon>
      </v-btn>
      <v-chip
        v-if="localItem"
        :color="getTypeColor(localItem.item_type)"
        size="small"
        label
        class="mx-2"
      >
        {{ formatTypeName(localItem.item_type) }}
      </v-chip>
      <span class="text-truncate flex-grow-1">{{ localItem?.title || 'New Item' }}</span>
      <v-spacer></v-spacer>
      <!-- Save indicator -->
      <v-chip
        v-if="saveStatus"
        :color="saveStatus === 'saved' ? 'success' : 'warning'"
        size="x-small"
        variant="tonal"
        class="mr-2"
      >
        <v-icon size="x-small" class="mr-1">
          {{ saveStatus === 'saved' ? 'mdi-check' : 'mdi-loading mdi-spin' }}
        </v-icon>
        {{ saveStatus === 'saved' ? 'Saved' : 'Saving...' }}
      </v-chip>
      <v-btn color="primary" size="small" @click="saveItem" :loading="saving">
        <v-icon class="mr-1">mdi-content-save</v-icon>
        Save
      </v-btn>
    </v-card-title>

    <!-- Metadata Section (Collapsible) -->
    <v-expansion-panels v-model="metadataExpanded" class="metadata-panel">
      <v-expansion-panel value="metadata">
        <v-expansion-panel-title class="py-2">
          <v-icon class="mr-2" size="small">mdi-information</v-icon>
          Metadata
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-row dense>
            <v-col cols="12">
              <v-text-field
                v-model="localItem.title"
                label="Title"
                variant="outlined"
                density="compact"
                hide-details
                @update:model-value="markDirty"
              ></v-text-field>
            </v-col>
            <v-col cols="6">
              <v-autocomplete
                v-model="localItem.customer_name"
                label="Customer/Sponsor"
                :items="customers"
                item-title="display_name"
                item-value="company_name"
                variant="outlined"
                density="compact"
                hide-details
                clearable
                @update:model-value="markDirty"
              >
                <template #no-data>
                  <v-list-item>
                    <v-list-item-title>No customers found. <a href="/settings" target="_blank">Add customers in Settings</a></v-list-item-title>
                  </v-list-item>
                </template>
              </v-autocomplete>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="localItem.duration"
                label="Duration"
                variant="outlined"
                density="compact"
                hide-details
                placeholder="00:00:30"
                @update:model-value="markDirty"
              ></v-text-field>
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="localItem.priority"
                label="Priority"
                :items="priorityOptions"
                variant="outlined"
                density="compact"
                hide-details
                @update:model-value="markDirty"
              ></v-select>
            </v-col>
            <v-col cols="6">
              <v-switch
                v-model="localItem.is_active"
                label="Active"
                color="success"
                density="compact"
                hide-details
                @update:model-value="markDirty"
              ></v-switch>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="localItem.valid_from"
                label="Valid From"
                type="date"
                variant="outlined"
                density="compact"
                hide-details
                @update:model-value="markDirty"
              ></v-text-field>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="localItem.valid_until"
                label="Valid Until"
                type="date"
                variant="outlined"
                density="compact"
                hide-details
                @update:model-value="markDirty"
              ></v-text-field>
            </v-col>
          </v-row>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Editor Panel -->
    <div class="editor-wrapper flex-grow-1 overflow-hidden">
      <EditorPanel
        ref="editorPanelRef"
        :editorMode="editorMode"
        :scriptContent="localItem?.script_content || ''"
        :scratchContent="localItem?.scratch_content || ''"
        :item="syntheticItem"
        :currentItemMetadata="{}"
        :showRundownPanel="false"
        :showMetadataPanel="false"
        :hasUnsavedChanges="isDirty"
        context="library"
        @update:editorMode="editorMode = $event"
        @update:scriptContent="handleScriptContentUpdate"
        @update:scratchContent="handleScratchContentUpdate"
        @save="saveItem"
        @insert-cue="handleInsertCue"
      />
    </div>

    <!-- Footer with Usage Stats -->
    <v-card-actions class="border-t pa-2">
      <v-btn
        v-if="localItem?.asset_id"
        variant="text"
        size="small"
        @click="$emit('view-usage')"
      >
        <v-icon class="mr-1">mdi-history</v-icon>
        {{ placementCount }} placements
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn
        v-if="localItem?.asset_id"
        color="error"
        variant="text"
        size="small"
        @click="confirmDelete"
      >
        <v-icon class="mr-1">mdi-delete</v-icon>
        Delete
      </v-btn>
    </v-card-actions>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">Delete Item?</v-card-title>
        <v-card-text>
          Are you sure you want to delete "{{ localItem?.title }}"?
          <br><br>
          <strong>This action cannot be undone.</strong>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="deleteItem">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { debounce } from 'lodash-es'
import EditorPanel from '@/components/content-editor/EditorPanel.vue'
import axios from 'axios'

const props = defineProps({
  item: {
    type: Object,
    default: null
  },
  isNew: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'saved', 'deleted', 'view-usage'])

// Refs
const editorPanelRef = ref(null)

// Local state
const localItem = ref(null)
const editorMode = ref('script')
const metadataExpanded = ref([])
const isDirty = ref(false)
const saving = ref(false)
const saveStatus = ref(null)
const deleteDialog = ref(false)
const customers = ref([])

// Priority options
const priorityOptions = [
  { title: 'High', value: 'high' },
  { title: 'Normal', value: 'normal' },
  { title: 'Low', value: 'low' }
]

// Computed
const syntheticItem = computed(() => {
  if (!localItem.value) return null
  return {
    id: localItem.value.asset_id,
    title: localItem.value.title,
    slug: localItem.value.slug,
    item_type: localItem.value.item_type,
    duration: localItem.value.duration,
    status: localItem.value.is_active ? 'active' : 'inactive'
  }
})

const placementCount = computed(() => {
  return localItem.value?.placement_count || 0
})

// Helper for auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('auth-token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

// Load customers for dropdown
const loadCustomers = async () => {
  try {
    const response = await axios.get('/api/customers/dropdown', {
      headers: getAuthHeaders()
    })
    customers.value = response.data.customers || []
  } catch (error) {
    console.error('Failed to load customers:', error)
    customers.value = []
  }
}

// Load customers on mount
onMounted(() => {
  loadCustomers()
})

// Debounced autosave
const debouncedSave = debounce(async () => {
  if (!localItem.value?.asset_id || !isDirty.value) return

  saveStatus.value = 'saving'
  try {
    await axios.patch(`/api/content-library/${localItem.value.asset_id}`, {
      title: localItem.value.title,
      script_content: localItem.value.script_content,
      scratch_content: localItem.value.scratch_content,
      duration: localItem.value.duration,
      customer_name: localItem.value.customer_name,
      priority: localItem.value.priority,
      is_active: localItem.value.is_active,
      valid_from: localItem.value.valid_from,
      valid_until: localItem.value.valid_until
    }, {
      headers: getAuthHeaders()
    })
    saveStatus.value = 'saved'
    isDirty.value = false
    emit('saved')

    // Clear saved indicator after 2 seconds
    setTimeout(() => {
      if (saveStatus.value === 'saved') {
        saveStatus.value = null
      }
    }, 2000)
  } catch (error) {
    console.error('Autosave failed:', error)
    saveStatus.value = null
  }
}, 500)

// Methods
const markDirty = () => {
  isDirty.value = true
  debouncedSave()
}

const handleScriptContentUpdate = (newContent) => {
  if (localItem.value) {
    localItem.value.script_content = newContent
    markDirty()
  }
}

const handleScratchContentUpdate = (newContent) => {
  if (localItem.value) {
    localItem.value.scratch_content = newContent
    markDirty()
  }
}

const handleInsertCue = (cueData) => {
  // Handle cue insertion - this will be handled by EditorPanel
  console.log('Cue inserted:', cueData)
}

const saveItem = async () => {
  if (!localItem.value?.asset_id) return

  saving.value = true
  try {
    await axios.patch(`/api/content-library/${localItem.value.asset_id}`, {
      title: localItem.value.title,
      script_content: localItem.value.script_content,
      scratch_content: localItem.value.scratch_content,
      duration: localItem.value.duration,
      customer_name: localItem.value.customer_name,
      priority: localItem.value.priority,
      is_active: localItem.value.is_active,
      valid_from: localItem.value.valid_from,
      valid_until: localItem.value.valid_until
    }, {
      headers: getAuthHeaders()
    })
    isDirty.value = false
    saveStatus.value = 'saved'
    emit('saved')

    setTimeout(() => {
      if (saveStatus.value === 'saved') {
        saveStatus.value = null
      }
    }, 2000)
  } catch (error) {
    console.error('Save failed:', error)
  } finally {
    saving.value = false
  }
}

const confirmDelete = () => {
  deleteDialog.value = true
}

const deleteItem = async () => {
  if (!localItem.value?.asset_id) return

  try {
    await axios.delete(`/api/content-library/${localItem.value.asset_id}`, {
      headers: getAuthHeaders(),
      params: { hard_delete: true }
    })
    deleteDialog.value = false
    emit('deleted')
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

const formatTypeName = (typeName) => {
  if (!typeName) return ''
  return typeName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

const getTypeColor = (typeName) => {
  const colorMap = {
    advertisement: 'green',
    promo: 'purple',
    cta: 'orange',
    transition: 'blue-grey',
    segment: 'blue',
    interview: 'teal'
  }
  return colorMap[typeName] || 'grey'
}

// Watch for prop changes
watch(() => props.item, (newItem) => {
  if (newItem) {
    // Deep copy to avoid mutating prop
    localItem.value = JSON.parse(JSON.stringify(newItem))
    isDirty.value = false
    saveStatus.value = null

    // Format dates for input fields if needed
    if (localItem.value.valid_from) {
      localItem.value.valid_from = localItem.value.valid_from.split('T')[0]
    }
    if (localItem.value.valid_until) {
      localItem.value.valid_until = localItem.value.valid_until.split('T')[0]
    }
  }
}, { immediate: true })
</script>

<style scoped>
.reusables-editor {
  height: 100%;
  max-height: calc(100vh - 80px);
}

.metadata-panel {
  flex-shrink: 0;
}

.metadata-panel :deep(.v-expansion-panel-text__wrapper) {
  padding: 8px 16px;
}

.editor-wrapper {
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.editor-wrapper :deep(.editor-panel) {
  height: 100%;
}

.border-b {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-t {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.h-100 {
  height: 100%;
}
</style>
