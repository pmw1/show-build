<template>
  <div class="prompt-manager">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon left>mdi-brain</v-icon>
        LLM Prompt Overrides
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openCreateDialog" prepend-icon="mdi-plus">
          New Override
        </v-btn>
      </v-card-title>

      <!-- Filters -->
      <v-card-text>
        <div class="d-flex align-center gap-4">
          <v-select
            v-model="filterCategory"
            :items="categories"
            label="Filter by Category"
            clearable
            style="max-width: 250px"
            @update:model-value="loadOverrides"
          ></v-select>
          <v-checkbox
            v-model="showEnabledOnly"
            label="Show Enabled Only"
            hide-details
            @update:model-value="loadOverrides"
          ></v-checkbox>
          <v-spacer></v-spacer>
          <v-chip color="success" v-if="overrides.length">
            {{ overrides.length }} override{{ overrides.length !== 1 ? 's' : '' }}
          </v-chip>
        </div>
      </v-card-text>

      <!-- Overrides Table -->
      <v-card-text>
        <v-data-table
              :headers="headers"
              :items="overrides"
              :loading="loading"
              item-key="id"
              class="elevation-1"
            >
              <!-- Category -->
              <template #[`item.category`]="{ item }">
                <v-chip :color="getCategoryColor(item.category)" size="small">
                  {{ item.category }}
                </v-chip>
              </template>

              <!-- Operation Key with Tooltip -->
              <template #[`item.operation_key`]="{ item }">
                <v-tooltip location="top" max-width="500">
                  <template v-slot:activator="{ props }">
                    <span v-bind="props" class="operation-key-text">
                      {{ item.operation_key }}
                    </span>
                  </template>
                  <div class="tooltip-content">
                    <div class="text-subtitle-2 mb-2">{{ getOperationTitle(item.operation_key) }}</div>
                    <div class="text-caption">{{ getOperationDescription(item.operation_key) }}</div>
                  </div>
                </v-tooltip>
              </template>

              <!-- Enabled Status -->
              <template #[`item.is_enabled`]="{ item }">
                <v-switch
                  :model-value="item.is_enabled"
                  color="success"
                  hide-details
                  @update:model-value="toggleOverride(item)"
                ></v-switch>
              </template>

              <!-- Has System Prompt -->
              <template #[`item.system_prompt`]="{ item }">
                <v-icon v-if="item.system_prompt" color="success">mdi-check</v-icon>
                <v-icon v-else color="grey">mdi-minus</v-icon>
              </template>

              <!-- Has User Prompt -->
              <template #[`item.user_prompt_template`]="{ item }">
                <v-icon v-if="item.user_prompt_template" color="success">mdi-check</v-icon>
                <v-icon v-else color="grey">mdi-minus</v-icon>
              </template>

              <!-- Route Override -->
              <template #[`item.route`]="{ item }">
                <div v-if="item.suggested_service || item.suggested_model" class="text-caption">
                  <div v-if="item.suggested_service">
                    <v-chip size="x-small" color="primary" class="mr-1">{{ item.suggested_service }}</v-chip>
                  </div>
                  <div v-if="item.suggested_model" class="text-truncate" style="max-width: 150px;">
                    {{ item.suggested_model }}
                  </div>
                  <div v-if="item.temperature != null" class="text-grey">
                    T: {{ item.temperature }}
                  </div>
                </div>
                <v-icon v-else color="grey">mdi-minus</v-icon>
              </template>

              <!-- Actions -->
              <template #[`item.actions`]="{ item }">
                <v-btn icon size="small" @click="openEditDialog(item)" class="mr-1">
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
                <v-btn icon size="small" @click="deleteOverride(item)" color="error">
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="1200px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editMode ? 'Edit' : 'Create' }} Prompt Override</span>
        </v-card-title>

        <v-card-text>
          <v-row>
            <!-- Left: Form -->
            <v-col cols="8">
              <v-form ref="formRef">
                <v-row>
                  <v-col cols="6">
                    <v-select
                      v-model="formData.category"
                      :items="categories"
                      label="Category *"
                      :rules="[v => !!v || 'Category is required']"
                      :disabled="editMode"
                    ></v-select>
                  </v-col>

                  <v-col cols="6">
                    <v-select
                      v-model="formData.operation_key"
                      :items="getOperationsForCategory(formData.category)"
                      label="Operation *"
                      :rules="[v => !!v || 'Operation is required']"
                      :disabled="editMode || !formData.category"
                      @update:model-value="onOperationSelected"
                    ></v-select>
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="12">
                    <div class="d-flex align-center mb-2">
                      <label class="text-subtitle-2">System Prompt Override</label>
                      <v-spacer></v-spacer>
                      <v-btn
                        size="small"
                        variant="outlined"
                        color="primary"
                        prepend-icon="mdi-eye"
                        @click="viewDefaultPrompt"
                        :disabled="!formData.operation_key"
                      >
                        View Default
                      </v-btn>
                    </div>
                    <v-textarea
                      v-model="formData.system_prompt"
                      label="System Prompt Override"
                      hint="Leave empty to use default system prompt"
                      rows="6"
                      auto-grow
                    ></v-textarea>
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="12">
                    <v-textarea
                      v-model="formData.user_prompt_template"
                      label="User Prompt Template Override"
                      hint="Use {{variable}} syntax for template variables. See available variables →"
                      rows="8"
                      auto-grow
                    ></v-textarea>
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="12">
                    <v-textarea
                      v-model="formData.notes"
                      label="Developer Notes"
                      hint="Optional notes about this override"
                      rows="3"
                      auto-grow
                    ></v-textarea>
                  </v-col>
                </v-row>

                <!-- LLM Route Override Section -->
                <v-row>
                  <v-col cols="12">
                    <v-divider class="my-4"></v-divider>
                    <div class="text-subtitle-2 mb-3">
                      <v-icon left size="small">mdi-robot</v-icon>
                      LLM Route Override (Optional)
                    </div>
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="6">
                    <v-text-field
                      v-model="formData.suggested_service"
                      label="Suggested Service"
                      hint="e.g., ollama, openai, anthropic, gemini, grok"
                      clearable
                    ></v-text-field>
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      v-model="formData.suggested_model"
                      label="Suggested Model"
                      hint="e.g., grok-2-latest, claude-3-5-sonnet-20241022"
                      clearable
                    ></v-text-field>
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="6">
                    <v-text-field
                      v-model.number="formData.temperature"
                      label="Temperature"
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      hint="0.0 (deterministic) to 2.0 (creative)"
                      clearable
                    ></v-text-field>
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      v-model.number="formData.max_tokens"
                      label="Max Tokens"
                      type="number"
                      hint="e.g., 4096, 8192"
                      clearable
                    ></v-text-field>
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="12">
                    <v-checkbox
                      v-model="formData.is_enabled"
                      label="Enable this override"
                    ></v-checkbox>
                  </v-col>
                </v-row>
              </v-form>
            </v-col>

            <!-- Right: Variables Reference Panel -->
            <v-col cols="4">
              <v-card outlined class="variables-panel">
                <v-card-title class="text-subtitle-1 pa-3">
                  <v-icon left size="small">mdi-code-braces</v-icon>
                  Available Variables
                </v-card-title>
                <v-divider></v-divider>
                <v-card-text class="pa-3">
                  <div v-if="!selectedOperationVariables.length" class="text-caption text-medium-emphasis">
                    Select an operation to see available variables
                  </div>
                  <div v-else>
                    <div
                      v-for="variable in selectedOperationVariables"
                      :key="variable.name"
                      class="variable-item mb-3"
                    >
                      <div class="d-flex align-center mb-1">
                        <v-chip
                          size="small"
                          color="primary"
                          variant="outlined"
                          class="mr-2"
                          @click="insertVariable(variable.name)"
                          style="cursor: pointer"
                        >
                          &#123;&#123;{{ variable.name }}&#125;&#125;
                        </v-chip>
                        <v-btn
                          icon
                          size="x-small"
                          variant="text"
                          @click="insertVariable(variable.name)"
                        >
                          <v-icon size="small">mdi-plus-circle</v-icon>
                        </v-btn>
                      </div>
                      <div class="text-caption text-medium-emphasis">
                        {{ variable.description }}
                      </div>
                      <div v-if="variable.example" class="text-caption mt-1" style="font-style: italic">
                        Example: {{ variable.example }}
                      </div>
                    </div>

                    <v-divider class="my-3"></v-divider>

                    <div class="text-caption text-medium-emphasis">
                      <strong>Usage:</strong> Click a variable chip or + button to insert it into your prompt template.
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" @click="saveOverride" :loading="saving">
            {{ editMode ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- View Default Prompt Modal -->
    <v-dialog v-model="defaultPromptDialog" max-width="800px">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon left>mdi-file-document-outline</v-icon>
          Default Prompt for {{ formData.operation_key }}
        </v-card-title>

        <v-card-text>
          <v-alert type="info" variant="tonal" class="mb-4">
            This is the default prompt that will be used if you don't provide an override.
            You can copy this as a starting point for your custom prompt.
          </v-alert>

          <div v-if="loadingDefaultPrompt" class="text-center pa-4">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <p class="mt-2">Loading default prompt...</p>
          </div>

          <div v-else-if="defaultPromptError" class="text-center pa-4">
            <v-alert type="error" variant="tonal">
              {{ defaultPromptError }}
            </v-alert>
          </div>

          <div v-else>
            <!-- System Prompt -->
            <v-card variant="outlined" class="mb-4">
              <v-card-title class="text-subtitle-1 pa-3 bg-grey-lighten-4">
                <v-icon left size="small">mdi-cog</v-icon>
                System Prompt
                <v-spacer></v-spacer>
                <v-btn
                  size="small"
                  variant="text"
                  color="primary"
                  @click="copyDefaultSystemPrompt"
                >
                  <v-icon left size="small">mdi-content-copy</v-icon>
                  Copy to Override
                </v-btn>
              </v-card-title>
              <v-card-text class="pa-3">
                <pre class="default-prompt-text">{{ defaultPromptData.systemPrompt || 'No system prompt defined' }}</pre>
              </v-card-text>
            </v-card>

            <!-- User Prompt Template -->
            <v-card variant="outlined" class="mb-4">
              <v-card-title class="text-subtitle-1 pa-3 bg-grey-lighten-4">
                <v-icon left size="small">mdi-text</v-icon>
                User Prompt Template
                <v-spacer></v-spacer>
                <v-btn
                  size="small"
                  variant="text"
                  color="primary"
                  @click="copyDefaultUserPrompt"
                >
                  <v-icon left size="small">mdi-content-copy</v-icon>
                  Copy to Override
                </v-btn>
              </v-card-title>
              <v-card-text class="pa-3">
                <pre class="default-prompt-text">{{ defaultPromptData.prompt || 'No user prompt template defined' }}</pre>
              </v-card-text>
            </v-card>

            <!-- Metadata -->
            <v-card variant="outlined">
              <v-card-title class="text-subtitle-1 pa-3 bg-grey-lighten-4">
                <v-icon left size="small">mdi-information</v-icon>
                Prompt Metadata
              </v-card-title>
              <v-card-text class="pa-3">
                <v-list density="compact">
                  <v-list-item v-if="defaultPromptData.version">
                    <v-list-item-title>Version: {{ defaultPromptData.version }}</v-list-item-title>
                  </v-list-item>
                  <v-list-item v-if="defaultPromptData.description">
                    <v-list-item-title>Description: {{ defaultPromptData.description }}</v-list-item-title>
                  </v-list-item>
                  <v-list-item v-if="defaultPromptData.temperature">
                    <v-list-item-title>Temperature: {{ defaultPromptData.temperature }}</v-list-item-title>
                  </v-list-item>
                  <v-list-item v-if="defaultPromptData.maxTokens">
                    <v-list-item-title>Max Tokens: {{ defaultPromptData.maxTokens }}</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="defaultPromptDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { notifyUserStandard, NOTIFICATION_COLORS } from '@/composables/useStandardNotification'

// State
const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const editMode = ref(false)
const overrides = ref([])
const filterCategory = ref(null)
const showEnabledOnly = ref(false)
const formRef = ref(null)

// Categories from backend
const categories = ref(['generate', 'analyze', 'extract', 'refactor', 'compose'])

// Operations by category (loaded from backend)
const operationsByCategory = ref({})

// Form data
const formData = ref({
  id: null,
  category: null,
  operation_key: null,
  system_prompt: '',
  user_prompt_template: '',
  notes: '',
  is_enabled: true,
  suggested_service: null,
  suggested_model: null,
  temperature: null,
  max_tokens: null
})

// Selected operation variables
const selectedOperationVariables = ref([])

// Default prompt modal
const defaultPromptDialog = ref(false)
const loadingDefaultPrompt = ref(false)
const defaultPromptError = ref(null)
const defaultPromptData = ref({
  systemPrompt: '',
  prompt: '',
  version: '',
  description: '',
  temperature: null,
  maxTokens: null
})

// Variable definitions by operation
const operationVariables = {
  // Generate operations
  'generate-segment-script': [
    { name: 'title', description: 'Segment title', example: 'The Rise of AI' },
    { name: 'topic', description: 'Main topic or subject', example: 'Artificial Intelligence' },
    { name: 'duration', description: 'Target duration', example: '5:00' },
    { name: 'tone', description: 'Desired tone', example: 'casual, formal, humorous' },
    { name: 'audience', description: 'Target audience', example: 'developers, general public' },
    { name: 'context', description: 'Additional background', example: 'Follow-up to episode 243' }
  ],
  'generate-ad-script': [
    { name: 'product', description: 'Product/service name', example: 'VPN Service' },
    { name: 'duration', description: 'Ad duration', example: '30 seconds' },
    { name: 'features', description: 'Key features', example: 'secure, fast, unlimited' },
    { name: 'callToAction', description: 'CTA text', example: 'Visit example.com' },
    { name: 'tone', description: 'Ad tone', example: 'professional, friendly' }
  ],
  'generate-promo-script': [
    { name: 'show', description: 'Show name', example: 'Tech Talk Podcast' },
    { name: 'episode', description: 'Episode title/number', example: 'Episode 244' },
    { name: 'duration', description: 'Promo duration', example: '15 seconds' },
    { name: 'hook', description: 'Attention-grabbing hook', example: 'What if AI could...' }
  ],
  'generate-cta-script': [
    { name: 'action', description: 'Desired action', example: 'Subscribe to newsletter' },
    { name: 'platform', description: 'Platform name', example: 'YouTube, Patreon' },
    { name: 'benefit', description: 'User benefit', example: 'Get exclusive content' }
  ],
  'generate-episode-description': [
    { name: 'title', description: 'Episode title', example: 'AI Ethics in 2025' },
    { name: 'topics', description: 'Main topics covered', example: 'AI safety, regulation, privacy' },
    { name: 'guests', description: 'Guest names', example: 'Dr. Jane Smith' },
    { name: 'duration', description: 'Episode duration', example: '45 minutes' }
  ],

  // Analyze operations
  'analyze-script-tone': [
    { name: 'script', description: 'Script content to analyze', example: 'Full script text...' },
    { name: 'targetTone', description: 'Expected tone', example: 'professional, casual' }
  ],
  'analyze-script-length': [
    { name: 'script', description: 'Script content', example: 'Full script text...' },
    { name: 'targetDuration', description: 'Target duration', example: '5:00' },
    { name: 'wordsPerMinute', description: 'Speaking pace', example: '150' }
  ],

  // Extract operations
  'extract-keywords': [
    { name: 'content', description: 'Content to extract from', example: 'Article or script text...' },
    { name: 'maxKeywords', description: 'Max number of keywords', example: '10' }
  ],
  'extract-quotes': [
    { name: 'content', description: 'Content to extract from', example: 'Interview transcript...' },
    { name: 'minLength', description: 'Min quote length', example: '20' }
  ],

  // Refactor operations
  'refactor-shorten-script': [
    { name: 'script', description: 'Original script', example: 'Full script text...' },
    { name: 'targetDuration', description: 'Target duration', example: '3:00' },
    { name: 'preserveKey', description: 'Key points to preserve', example: 'Main argument, conclusion' }
  ],
  'refactor-adjust-tone': [
    { name: 'script', description: 'Original script', example: 'Full script text...' },
    { name: 'currentTone', description: 'Current tone', example: 'formal' },
    { name: 'targetTone', description: 'Desired tone', example: 'casual' }
  ],

  // Common variables (shown for all if not defined)
  'default': [
    { name: 'title', description: 'Item title', example: 'My Content' },
    { name: 'topic', description: 'Main topic', example: 'Technology' },
    { name: 'duration', description: 'Target duration', example: '5:00' },
    { name: 'tone', description: 'Content tone', example: 'casual' },
    { name: 'context', description: 'Additional context', example: 'Background information...' }
  ]
}

// Table headers
const headers = [
  { title: 'Category', key: 'category', sortable: true },
  { title: 'Operation', key: 'operation_key', sortable: true },
  { title: 'System Prompt', key: 'system_prompt', sortable: false },
  { title: 'User Prompt', key: 'user_prompt_template', sortable: false },
  { title: 'Route', key: 'route', sortable: false },
  { title: 'Enabled', key: 'is_enabled', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, width: 120 }
]

// Methods
const loadOperations = async () => {
  try {
    const response = await axios.get('/api/prompts/operations')
    if (response.data.success) {
      operationsByCategory.value = response.data.operations
    }
  } catch (error) {
    console.error('Failed to load operations:', error)
    notifyUserStandard('Failed to load operations', NOTIFICATION_COLORS.ERROR)
  }
}

const loadOverrides = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterCategory.value) params.category = filterCategory.value
    if (showEnabledOnly.value) params.enabled_only = true

    const response = await axios.get('/api/prompts/overrides', { params })
    if (response.data.success) {
      overrides.value = response.data.overrides
    }
  } catch (error) {
    console.error('Failed to load overrides:', error)
    notifyUserStandard('Failed to load prompt overrides', NOTIFICATION_COLORS.ERROR)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editMode.value = false
  formData.value = {
    id: null,
    category: null,
    operation_key: null,
    system_prompt: '',
    user_prompt_template: '',
    notes: '',
    is_enabled: true,
    suggested_service: null,
    suggested_model: null,
    temperature: null,
    max_tokens: null
  }
  dialog.value = true
}

const openEditDialog = (item) => {
  editMode.value = true
  formData.value = {
    id: item.id,
    category: item.category,
    operation_key: item.operation_key,
    system_prompt: item.system_prompt || '',
    user_prompt_template: item.user_prompt_template || '',
    notes: item.notes || '',
    is_enabled: item.is_enabled,
    suggested_service: item.suggested_service || null,
    suggested_model: item.suggested_model || null,
    temperature: item.temperature,
    max_tokens: item.max_tokens
  }
  // Populate variables panel for the selected operation
  onOperationSelected(item.operation_key)
  dialog.value = true
}

const closeDialog = () => {
  dialog.value = false
  formData.value = {
    id: null,
    category: null,
    operation_key: null,
    system_prompt: '',
    user_prompt_template: '',
    notes: '',
    is_enabled: true,
    suggested_service: null,
    suggested_model: null,
    temperature: null,
    max_tokens: null
  }
}

const saveOverride = async () => {
  // Validate form
  const { valid } = await formRef.value.validate()
  if (!valid) {
    notifyUserStandard('Please fill in required fields', NOTIFICATION_COLORS.WARNING)
    return
  }

  saving.value = true
  try {
    if (editMode.value) {
      // Update existing override
      await axios.patch(`/api/prompts/overrides/${formData.value.id}`, {
        system_prompt: formData.value.system_prompt,
        user_prompt_template: formData.value.user_prompt_template,
        notes: formData.value.notes,
        is_enabled: formData.value.is_enabled
      })
      notifyUserStandard('Prompt override updated', NOTIFICATION_COLORS.SUCCESS)
    } else {
      // Create new override
      await axios.post('/api/prompts/overrides', formData.value)
      notifyUserStandard('Prompt override created', NOTIFICATION_COLORS.SUCCESS)
    }

    closeDialog()
    await loadOverrides()
  } catch (error) {
    console.error('Failed to save override:', error)
    const message = error.response?.data?.detail || 'Failed to save prompt override'
    notifyUserStandard(message, NOTIFICATION_COLORS.ERROR)
  } finally {
    saving.value = false
  }
}

const toggleOverride = async (item) => {
  try {
    await axios.post(`/api/prompts/overrides/${item.id}/toggle`)
    notifyUserStandard(
      `Override ${item.is_enabled ? 'disabled' : 'enabled'}`,
      NOTIFICATION_COLORS.SUCCESS,
      1500
    )
    await loadOverrides()
  } catch (error) {
    console.error('Failed to toggle override:', error)
    notifyUserStandard('Failed to toggle override', NOTIFICATION_COLORS.ERROR)
  }
}

const deleteOverride = async (item) => {
  if (!confirm(`Delete override for ${item.category}.${item.operation_key}?`)) {
    return
  }

  try {
    await axios.delete(`/api/prompts/overrides/${item.id}`)
    notifyUserStandard('Prompt override deleted', NOTIFICATION_COLORS.SUCCESS)
    await loadOverrides()
  } catch (error) {
    console.error('Failed to delete override:', error)
    notifyUserStandard('Failed to delete prompt override', NOTIFICATION_COLORS.ERROR)
  }
}

const getCategoryColor = (category) => {
  const colors = {
    generate: 'blue',
    analyze: 'purple',
    extract: 'green',
    refactor: 'orange',
    compose: 'pink',
    inventory: 'teal'
  }
  return colors[category] || 'grey'
}

// Operation metadata for tooltips
const operationMetadata = {
  'inventory-match-file-to-slot': {
    title: 'File to Slot Matcher',
    description: 'Determines if a specific file matches an expected episode file slot (e.g., episode_info, rundown_json). Called when validating individual files against canonical expectations.'
  },
  'inventory-classify-stray-file': {
    title: 'Stray File Classifier',
    description: 'Classifies unmatched files into categories (test file, backup, duplicate, temp, etc.) and suggests actions (keep/delete/relocate). Called for files that don\'t match any expected slots.'
  },
  'inventory-batch-match-slots': {
    title: 'Batch Slot Matcher',
    description: 'Analyzes entire episode directory tree and matches files to 25 semantic slots in batches. Called during episode file inventory scans to classify captures, exports, thumbnails, projects, and assets. Uses DeepSeek R1 by default for better reasoning.'
  }
}

const getOperationTitle = (operationKey) => {
  return operationMetadata[operationKey]?.title || operationKey
}

const getOperationDescription = (operationKey) => {
  return operationMetadata[operationKey]?.description || 'No description available for this operation.'
}

const getOperationsForCategory = (category) => {
  if (!category || !operationsByCategory.value[category]) {
    return []
  }
  return operationsByCategory.value[category]
}

// Handle operation selection - load variables
const onOperationSelected = (operationKey) => {
  if (operationKey && operationVariables[operationKey]) {
    selectedOperationVariables.value = operationVariables[operationKey]
  } else {
    // Show default variables if operation not found
    selectedOperationVariables.value = operationVariables['default']
  }
}

// Insert variable into user prompt template
const insertVariable = (variableName) => {
  const variable = `{{${variableName}}}`
  const textarea = document.querySelector('textarea[label="User Prompt Template Override"]')

  if (textarea) {
    const cursorPos = textarea.selectionStart
    const textBefore = formData.value.user_prompt_template.substring(0, cursorPos)
    const textAfter = formData.value.user_prompt_template.substring(cursorPos)

    formData.value.user_prompt_template = textBefore + variable + textAfter

    // Move cursor after inserted variable
    setTimeout(() => {
      textarea.focus()
      textarea.selectionStart = textarea.selectionEnd = cursorPos + variable.length
    }, 0)

    notifyUserStandard(`Inserted ${variable}`, NOTIFICATION_COLORS.INFO, 1000)
  } else {
    // Fallback: append to end
    if (formData.value.user_prompt_template) {
      formData.value.user_prompt_template += ' ' + variable
    } else {
      formData.value.user_prompt_template = variable
    }
    notifyUserStandard(`Added ${variable}`, NOTIFICATION_COLORS.INFO, 1000)
  }
}

// View default prompt
const viewDefaultPrompt = async () => {
  if (!formData.value.operation_key) {
    notifyUserStandard('Please select an operation first', NOTIFICATION_COLORS.WARNING)
    return
  }

  defaultPromptDialog.value = true
  loadingDefaultPrompt.value = true
  defaultPromptError.value = null

  try {
    // Import and get default prompt from useLLMPrompts
    const { getLLMPrompt } = await import('@/composables/useLLMPrompts')

    // Get default prompt (without category to avoid override lookup)
    const promptData = await getLLMPrompt(formData.value.operation_key, {})

    defaultPromptData.value = {
      systemPrompt: promptData.systemPrompt || '',
      prompt: promptData.prompt || '',
      version: promptData.version || '',
      description: promptData.description || '',
      temperature: promptData.temperature,
      maxTokens: promptData.maxTokens
    }

    console.log('Loaded default prompt:', defaultPromptData.value)
  } catch (error) {
    console.error('Failed to load default prompt:', error)
    defaultPromptError.value = `Failed to load default prompt: ${error.message}`
  } finally {
    loadingDefaultPrompt.value = false
  }
}

// Copy default system prompt to override
const copyDefaultSystemPrompt = () => {
  if (defaultPromptData.value.systemPrompt) {
    formData.value.system_prompt = defaultPromptData.value.systemPrompt
    notifyUserStandard('System prompt copied to override', NOTIFICATION_COLORS.SUCCESS, 2000)
    defaultPromptDialog.value = false
  }
}

// Copy default user prompt to override
const copyDefaultUserPrompt = () => {
  if (defaultPromptData.value.prompt) {
    formData.value.user_prompt_template = defaultPromptData.value.prompt
    notifyUserStandard('User prompt copied to override', NOTIFICATION_COLORS.SUCCESS, 2000)
    defaultPromptDialog.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await loadOperations()
  await loadOverrides()
})
</script>

<style scoped>
.prompt-manager {
  padding: 20px;
}

.variables-panel {
  position: sticky;
  top: 20px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.variable-item {
  padding: 8px;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.02);
}

.variable-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.default-prompt-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
}

.operation-key-text {
  cursor: help;
  border-bottom: 1px dotted currentColor;
  display: inline-block;
}

.operation-key-text:hover {
  opacity: 0.8;
}

.tooltip-content {
  text-align: left;
  padding: 4px;
}

/* Fix textarea top line fading/clipping issue */
.prompt-manager :deep(.v-textarea .v-field__input) {
  padding-top: 12px !important;
  min-height: 60px;
}

.prompt-manager :deep(.v-textarea textarea) {
  padding-top: 8px !important;
}

/* Make disabled category/operation fields more visible */
.prompt-manager :deep(.v-select--disabled .v-select__selection) {
  opacity: 0.8 !important;
  color: rgba(0, 0, 0, 0.7) !important;
}

.prompt-manager :deep(.v-select--disabled .v-field__input) {
  opacity: 1 !important;
}

.prompt-manager :deep(.v-select--disabled) {
  opacity: 0.9 !important;
}
</style>
