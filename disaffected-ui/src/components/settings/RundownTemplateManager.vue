<template>
  <v-card flat class="rundown-template-manager">
    <v-card-title class="d-flex align-center pa-4">
      <v-icon class="me-2">mdi-playlist-edit</v-icon>
      Rundown Templates
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        @click="showCreateTemplateDialog = true"
      >
        New Template
      </v-btn>
    </v-card-title>

    <v-card-text>
      <!-- Template List -->
      <v-row>
        <v-col cols="12" md="4">
          <v-card variant="outlined">
            <v-card-title class="text-subtitle-1 pa-3">
              Templates
              <v-chip size="small" class="ml-2">{{ templates.length }}</v-chip>
            </v-card-title>
            <v-divider></v-divider>
            <v-list density="compact" class="pa-0">
              <v-list-item
                v-for="template in templates"
                :key="template.id"
                :class="{ 'v-list-item--active': selectedTemplate?.id === template.id }"
                @click="selectTemplate(template)"
              >
                <v-list-item-title>
                  {{ template.name }}
                  <v-chip
                    v-if="template.is_default"
                    size="x-small"
                    color="primary"
                    class="ml-2"
                  >
                    DEFAULT
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ template.items?.length || 0 }} items
                  <span v-if="template.description"> • {{ template.description }}</span>
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-menu location="bottom end">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon="mdi-dots-vertical"
                        variant="text"
                        size="small"
                        v-bind="props"
                        @click.stop
                      ></v-btn>
                    </template>
                    <v-list>
                      <v-list-item @click="editTemplate(template)">
                        <v-list-item-title>
                          <v-icon size="small" class="mr-2">mdi-pencil</v-icon>
                          Edit
                        </v-list-item-title>
                      </v-list-item>
                      <v-list-item @click="cloneTemplate(template)">
                        <v-list-item-title>
                          <v-icon size="small" class="mr-2">mdi-content-copy</v-icon>
                          Clone
                        </v-list-item-title>
                      </v-list-item>
                      <v-list-item @click="confirmDeleteTemplate(template)">
                        <v-list-item-title>
                          <v-icon size="small" class="mr-2" color="error">mdi-delete</v-icon>
                          Delete
                        </v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </v-menu>
                </template>
              </v-list-item>
            </v-list>
          </v-card>
        </v-col>

        <!-- Template Items Editor -->
        <v-col cols="12" md="8">
          <v-card v-if="selectedTemplate" variant="outlined">
            <v-card-title class="text-subtitle-1 pa-3 d-flex align-center">
              <v-icon class="me-2">mdi-format-list-bulleted</v-icon>
              {{ selectedTemplate.name }} - Items
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                size="small"
                prepend-icon="mdi-plus"
                @click="showAddItemDialog = true"
              >
                Add Item
              </v-btn>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-0">
              <!-- Draggable Items List -->
              <draggable
                v-model="templateItems"
                tag="div"
                :item-key="item => item.id"
                :animation="200"
                class="template-items-container"
                ghost-class="ghost-item"
                chosen-class="chosen-item"
                drag-class="drag-item"
                @start="handleDragStart"
                @end="handleDragEnd"
              >
                <template #item="{ element: item }">
                  <v-card
                    flat
                    class="template-item-card"
                    :class="{ 'selected-item': selectedItemId === item.id }"
                    @click="selectedItemId = item.id"
                  >
                    <div class="compact-rundown-row">
                      <!-- Index Number Cell -->
                      <div class="index-number-cell">
                        <div class="index-number">{{ item.sort_order }}</div>
                      </div>

                      <!-- Type -->
                      <div class="type-label">
                        {{ (item.item_type || 'UNKNOWN').toUpperCase().substring(0, 3) }}
                      </div>

                      <!-- Title/Slug -->
                      <div class="slug-column">
                        <div class="slug-text">{{ item.title || item.slug || 'Untitled' }}</div>
                      </div>

                      <!-- Duration -->
                      <div class="duration-display">
                        {{ item.duration || '00:00:00' }}
                      </div>

                      <!-- Menu for selected item -->
                      <v-menu v-if="selectedItemId === item.id" location="bottom end">
                        <template v-slot:activator="{ props }">
                          <v-btn
                            icon="mdi-dots-vertical"
                            size="small"
                            variant="text"
                            class="item-menu-btn-right"
                            v-bind="props"
                            @click.stop
                          ></v-btn>
                        </template>
                        <v-list>
                          <v-list-item @click="editItem(item)">
                            <v-list-item-title>
                              <v-icon size="small" class="mr-2">mdi-pencil</v-icon>
                              Edit
                            </v-list-item-title>
                          </v-list-item>
                          <v-list-item @click="deleteItem(item)">
                            <v-list-item-title>
                              <v-icon size="small" class="mr-2" color="error">mdi-delete</v-icon>
                              Delete
                            </v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </v-menu>
                    </div>
                  </v-card>
                </template>
              </draggable>

              <!-- Empty state -->
              <div v-if="!templateItems || templateItems.length === 0" class="text-center py-8">
                <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-playlist-remove</v-icon>
                <p class="text-h6 text-grey-lighten-1">No items in template</p>
                <p class="text-caption text-grey">Click "Add Item" to create template items</p>
              </div>
            </v-card-text>
          </v-card>

          <!-- No template selected -->
          <v-card v-else variant="outlined" class="text-center py-12">
            <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-playlist-edit</v-icon>
            <p class="text-h6 text-grey-lighten-1">Select a template to edit</p>
            <p class="text-caption text-grey">Choose a template from the list or create a new one</p>
          </v-card>
        </v-col>
      </v-row>
    </v-card-text>

    <!-- Create/Edit Template Dialog -->
    <v-dialog v-model="showTemplateDialog" max-width="600" persistent>
      <v-card>
        <v-card-title>
          {{ editingTemplate ? 'Edit Template' : 'Create Template' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="templateFormRef" v-model="templateFormValid">
            <v-text-field
              v-model="templateForm.name"
              label="Template Name"
              :rules="[v => !!v || 'Name is required']"
              required
            ></v-text-field>

            <v-textarea
              v-model="templateForm.description"
              label="Description"
              rows="2"
              hint="Optional description"
            ></v-textarea>

            <v-select
              v-model="templateForm.episode_template_id"
              :items="episodeTemplates"
              item-title="name"
              item-value="id"
              label="Episode Template"
              :rules="[v => !!v || 'Episode template is required']"
              required
            ></v-select>

            <v-select
              v-model="templateForm.organization_id"
              :items="organizations"
              item-title="name"
              item-value="id"
              label="Organization"
              :rules="[v => !!v || 'Organization is required']"
              required
            ></v-select>

            <v-checkbox
              v-model="templateForm.is_default"
              label="Set as default template"
              hint="Default templates are auto-selected when creating episodes"
              persistent-hint
            ></v-checkbox>

            <v-checkbox
              v-model="templateForm.is_active"
              label="Active"
              hint="Inactive templates are hidden from episode creation"
              persistent-hint
            ></v-checkbox>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeTemplateDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="saving"
            :disabled="!templateFormValid"
            @click="saveTemplate"
          >
            {{ editingTemplate ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Add/Edit Item Dialog -->
    <v-dialog v-model="showItemDialog" max-width="600" persistent>
      <v-card>
        <v-card-title>
          {{ editingItem ? 'Edit Item' : 'Add Item' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="itemFormRef" v-model="itemFormValid">
            <v-select
              v-model="itemForm.item_type"
              :items="itemTypes"
              label="Item Type"
              :rules="[v => !!v || 'Item type is required']"
              required
            ></v-select>

            <v-text-field
              v-model="itemForm.title"
              label="Title"
              hint="Display name for this item"
            ></v-text-field>

            <v-text-field
              v-model="itemForm.slug"
              label="Slug"
              hint="URL-friendly identifier"
            ></v-text-field>

            <v-text-field
              v-model="itemForm.duration"
              label="Duration"
              placeholder="00:05:00"
              hint="Format: HH:MM:SS"
              :rules="durationRules"
            ></v-text-field>

            <v-textarea
              v-model="itemForm.script_content"
              label="Default Script Content"
              rows="3"
              hint="Optional default content for this item type"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeItemDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="saving"
            :disabled="!itemFormValid"
            @click="saveItem"
          >
            {{ editingItem ? 'Update' : 'Add' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Template Confirmation -->
    <v-dialog v-model="showDeleteTemplateDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="text-h6">Delete Template?</v-card-title>
        <v-card-text>
          Are you sure you want to delete the template <strong>{{ templateToDelete?.name }}</strong>?
          This will also delete all {{ templateToDelete?.items?.length || 0 }} items in the template.
          <br><br>
          <strong>This action cannot be undone.</strong>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showDeleteTemplateDialog = false">Cancel</v-btn>
          <v-btn
            color="error"
            :loading="deleting"
            @click="deleteTemplate"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Clone Template Dialog -->
    <v-dialog v-model="showCloneDialog" max-width="500" persistent>
      <v-card>
        <v-card-title>Clone Template</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="cloneName"
            label="New Template Name"
            :rules="[v => !!v || 'Name is required']"
            autofocus
          ></v-text-field>
          <v-textarea
            v-model="cloneDescription"
            label="Description"
            rows="2"
          ></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showCloneDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="cloning"
            :disabled="!cloneName"
            @click="saveClone"
          >
            Clone
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Error/Success Snackbar -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      location="bottom"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import draggable from 'vuedraggable'

// Auth helper - get headers with JWT token
const getAuthHeaders = () => {
  const token = localStorage.getItem('auth-token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Reactive state
const templates = ref([])
const selectedTemplate = ref(null)
const selectedItemId = ref(null)
const episodeTemplates = ref([])
const organizations = ref([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const cloning = ref(false)

// Dialog states
const showTemplateDialog = ref(false)
const showCreateTemplateDialog = ref(false)
const showAddItemDialog = ref(false)
const showItemDialog = ref(false)
const showDeleteTemplateDialog = ref(false)
const showCloneDialog = ref(false)

// Snackbar state
const snackbar = ref({
  show: false,
  message: '',
  color: 'error',
  timeout: 5000
})

const showSnackbar = (message, color = 'error') => {
  snackbar.value.message = message
  snackbar.value.color = color
  snackbar.value.show = true
}

// Form states
const templateFormValid = ref(false)
const itemFormValid = ref(false)
const editingTemplate = ref(null)
const editingItem = ref(null)
const templateToDelete = ref(null)
const templateToClone = ref(null)
const cloneName = ref('')
const cloneDescription = ref('')

// Form data
const templateForm = ref({
  name: '',
  description: '',
  organization_id: null,
  episode_template_id: null,
  is_default: false,
  is_active: true,
  sort_order: 0
})

const itemForm = ref({
  item_type: 'segment',
  title: '',
  slug: '',
  duration: '00:05:00',
  script_content: '',
  sort_order: 10
})

// Item types - loaded dynamically from API
const itemTypes = ref([])

// Load rundown item types from backend enum
const loadItemTypes = async () => {
  try {
    const response = await axios.get('/api/rundown-templates/item-types', { headers: getAuthHeaders() })
    // Convert enum object {SEGMENT: 'segment', AD: 'ad', ...} to dropdown format
    itemTypes.value = Object.entries(response.data).map(([key, value]) => ({
      title: key.split('_').map(word => word.charAt(0) + word.slice(1).toLowerCase()).join(' '),
      value: value
    })).sort((a, b) => a.title.localeCompare(b.title))
  } catch (error) {
    console.error('Error loading item types:', error)
    // Fallback to basic types if API fails
    itemTypes.value = [
      { title: 'Segment', value: 'segment' },
      { title: 'Ad', value: 'ad' },
      { title: 'Break', value: 'break' }
    ]
  }
}

// Validation rules
const durationRules = [
  v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Duration must be in HH:MM:SS format'
]

// Computed
const templateItems = computed({
  get() {
    return selectedTemplate.value?.items || []
  },
  set(newValue) {
    if (selectedTemplate.value) {
      selectedTemplate.value.items = newValue
    }
  }
})

// Watch for create dialog
watch(showCreateTemplateDialog, (val) => {
  if (val) {
    editingTemplate.value = null
    resetTemplateForm()
    showTemplateDialog.value = true
    showCreateTemplateDialog.value = false
  }
})

watch(showAddItemDialog, (val) => {
  if (val) {
    editingItem.value = null
    resetItemForm()
    showItemDialog.value = true
    showAddItemDialog.value = false
  }
})

// Methods
const loadTemplates = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/rundown-templates/', { headers: getAuthHeaders() })
    templates.value = response.data
  } catch (error) {
    console.error('Error loading templates:', error)
  } finally {
    loading.value = false
  }
}

const loadEpisodeTemplates = async () => {
  try {
    const response = await axios.get('/api/episodes/templates', { headers: getAuthHeaders() })
    episodeTemplates.value = response.data
  } catch (error) {
    console.error('Error loading episode templates:', error)
  }
}

const loadOrganizations = async () => {
  try {
    const response = await axios.get('/api/organizations/', { headers: getAuthHeaders() })
    organizations.value = response.data
  } catch (error) {
    console.error('Error loading organizations:', error)
  }
}

const selectTemplate = async (template) => {
  try {
    // Fetch full template with items
    const response = await axios.get(`/api/rundown-templates/${template.id}`, { headers: getAuthHeaders() })
    selectedTemplate.value = response.data
    selectedItemId.value = null
  } catch (error) {
    console.error('Error loading template details:', error)
  }
}

const resetTemplateForm = () => {
  templateForm.value = {
    name: '',
    description: '',
    organization_id: organizations.value[0]?.id || null,
    episode_template_id: episodeTemplates.value[0]?.id || null,
    is_default: false,
    is_active: true,
    sort_order: templates.value.length
  }
}

const resetItemForm = () => {
  const nextSortOrder = templateItems.value.length > 0
    ? Math.max(...templateItems.value.map(item => item.sort_order)) + 10
    : 10

  itemForm.value = {
    item_type: 'segment',
    title: '',
    slug: '',
    duration: '00:05:00',
    script_content: '',
    sort_order: nextSortOrder
  }
}

const editTemplate = (template) => {
  editingTemplate.value = template
  templateForm.value = {
    name: template.name,
    description: template.description,
    organization_id: template.organization_id,
    episode_template_id: template.episode_template_id,
    is_default: template.is_default,
    is_active: template.is_active,
    sort_order: template.sort_order
  }
  showTemplateDialog.value = true
}

const closeTemplateDialog = () => {
  showTemplateDialog.value = false
  editingTemplate.value = null
  resetTemplateForm()
}

const saveTemplate = async () => {
  try {
    saving.value = true

    if (editingTemplate.value) {
      // Update existing template
      await axios.put(`/api/rundown-templates/${editingTemplate.value.id}`, templateForm.value, { headers: getAuthHeaders() })
    } else {
      // Create new template
      await axios.post('/api/rundown-templates/', templateForm.value, { headers: getAuthHeaders() })
    }

    await loadTemplates()
    closeTemplateDialog()
  } catch (error) {
    console.error('Error saving template:', error)
    showSnackbar(`Error saving template: ${error.response?.data?.detail || error.message}`)
  } finally {
    saving.value = false
  }
}

const editItem = (item) => {
  editingItem.value = item
  itemForm.value = {
    item_type: item.item_type,
    title: item.title,
    slug: item.slug,
    duration: item.duration,
    script_content: item.script_content,
    sort_order: item.sort_order
  }
  showItemDialog.value = true
}

const closeItemDialog = () => {
  showItemDialog.value = false
  editingItem.value = null
  resetItemForm()
}

const saveItem = async () => {
  try {
    saving.value = true

    if (editingItem.value) {
      // Update existing item
      await axios.put(`/api/rundown-templates/items/${editingItem.value.id}`, itemForm.value, { headers: getAuthHeaders() })
    } else {
      // Create new item
      await axios.post(`/api/rundown-templates/${selectedTemplate.value.id}/items`, itemForm.value, { headers: getAuthHeaders() })
    }

    // Reload template to get updated items
    await selectTemplate(selectedTemplate.value)
    closeItemDialog()
  } catch (error) {
    console.error('Error saving item:', error)
    showSnackbar(`Error saving item: ${error.response?.data?.detail || error.message}`)
  } finally {
    saving.value = false
  }
}

const deleteItem = async (item) => {
  if (!confirm(`Delete item "${item.title || item.slug}"?`)) return

  try {
    await axios.delete(`/api/rundown-templates/items/${item.id}`, { headers: getAuthHeaders() })
    await selectTemplate(selectedTemplate.value)
  } catch (error) {
    console.error('Error deleting item:', error)
    showSnackbar(`Error deleting item: ${error.response?.data?.detail || error.message}`)
  }
}

const confirmDeleteTemplate = (template) => {
  templateToDelete.value = template
  showDeleteTemplateDialog.value = true
}

const deleteTemplate = async () => {
  try {
    deleting.value = true
    await axios.delete(`/api/rundown-templates/${templateToDelete.value.id}`, { headers: getAuthHeaders() })

    if (selectedTemplate.value?.id === templateToDelete.value.id) {
      selectedTemplate.value = null
    }

    await loadTemplates()
    showDeleteTemplateDialog.value = false
    templateToDelete.value = null
  } catch (error) {
    console.error('Error deleting template:', error)
    showSnackbar(`Error deleting template: ${error.response?.data?.detail || error.message}`)
  } finally {
    deleting.value = false
  }
}

const cloneTemplate = (template) => {
  templateToClone.value = template
  cloneName.value = `${template.name} (Copy)`
  cloneDescription.value = template.description
  showCloneDialog.value = true
}

const saveClone = async () => {
  try {
    cloning.value = true
    await axios.post(`/api/rundown-templates/${templateToClone.value.id}/clone`, {
      name: cloneName.value,
      description: cloneDescription.value
    }, { headers: getAuthHeaders() })

    await loadTemplates()
    showCloneDialog.value = false
    templateToClone.value = null
    cloneName.value = ''
    cloneDescription.value = ''
  } catch (error) {
    console.error('Error cloning template:', error)
    showSnackbar(`Error cloning template: ${error.response?.data?.detail || error.message}`)
  } finally {
    cloning.value = false
  }
}

const handleDragStart = () => {
  console.log('Drag started')
}

const handleDragEnd = async () => {
  console.log('Drag ended')

  // Update sort_order based on new positions
  templateItems.value.forEach((item, index) => {
    item.sort_order = (index + 1) * 10
  })

  // Reorder on backend
  try {
    const itemIds = templateItems.value.map(item => item.id)
    await axios.post(`/api/rundown-templates/${selectedTemplate.value.id}/items/reorder`, itemIds, { headers: getAuthHeaders() })
  } catch (error) {
    console.error('Error reordering items:', error)
  }
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadTemplates(),
    loadEpisodeTemplates(),
    loadOrganizations(),
    loadItemTypes()
  ])
})
</script>

<style scoped>
.rundown-template-manager {
  height: 100%;
}

.template-items-container {
  min-height: 200px;
  max-height: 600px;
  overflow-y: auto;
}

/* Compact Rundown Row - Match RundownPanel.vue */
.compact-rundown-row {
  display: grid;
  grid-template-columns: 50px 60px 1fr 80px;
  gap: 0px 8px;
  padding: 0px 50px 0px 0px;
  align-items: center;
  font-size: 11px;
  font-family: 'Roboto Mono', monospace;
  height: 100%;
  min-height: 2.5em;
}

.template-item-card {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  cursor: grab;
  transition: background-color 0.2s;
}

.template-item-card:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.template-item-card:active {
  cursor: grabbing;
}

.selected-item {
  background-color: rgba(25, 118, 210, 0.12) !important;
  border-left: 4px solid #1976D2 !important;
}

/* Index Number Cell */
.index-number-cell {
  background-color: rgba(255, 255, 255, 0.09);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
  height: 100%;
  align-self: stretch;
  min-width: 50px;
}

.index-number {
  font-weight: 600;
  font-size: 11px;
}

/* Type Label */
.type-label {
  font-weight: 700;
  font-size: 10px;
  letter-spacing: 0.5px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* Slug Column */
.slug-column {
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}

.slug-text {
  font-weight: 400;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Duration Display */
.duration-display {
  position: absolute;
  right: 50px;
  font-size: 11px;
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;
}

/* Item Menu Button */
.item-menu-btn-right {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
}

/* Drag classes */
.ghost-item {
  opacity: 0.5;
  background-color: #f5f5f5;
}

.chosen-item {
  opacity: 1;
}

.drag-item {
  opacity: 0.8;
  transform: rotate(2deg);
}

/* Remove rounded corners */
.template-item-card,
.v-card,
.v-card-title {
  border-radius: 0 !important;
}
</style>
