<template>
  <v-container fluid class="pa-4">
    <v-row align="center">
      <v-col cols="auto">
        <h2 class="text-h4 font-weight-bold mb-6">Settings</h2>
      </v-col>
      <v-spacer />
      <!-- Admin-only: site-wide vs personal write-scope toggle -->
      <v-col v-if="isAdmin" cols="auto" class="pb-6">
        <v-card variant="outlined" class="scope-toggle pa-2">
          <div class="text-caption text-grey-darken-1 mb-1">Editing for</div>
          <v-btn-toggle
            v-model="writeScopeLocal"
            mandatory
            divided
            density="compact"
            :color="writeScopeLocal === 'global' ? 'error' : 'primary'"
            @update:model-value="onScopeChange"
          >
            <v-btn value="user" size="small">
              <v-icon start size="x-small">mdi-account</v-icon>
              Personal
            </v-btn>
            <v-btn value="global" size="small">
              <v-icon start size="x-small">mdi-earth</v-icon>
              Site-wide
            </v-btn>
          </v-btn-toggle>
          <div v-if="writeScopeLocal === 'global'" class="text-caption text-error mt-1">
            <v-icon size="x-small">mdi-alert</v-icon>
            Changes affect all users
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Settings Tabs -->
    <v-row>
      <v-col>
        <v-tabs v-model="activeTab" color="primary" class="mb-4">
          <v-tab value="ai">AI</v-tab>
          <v-tab value="third-party-api">Third Party & API</v-tab>
          <v-tab value="interface">Interface</v-tab>
          <v-tab value="content">Content</v-tab>
          <v-tab value="whiteboard">Whiteboard</v-tab>
          <v-tab value="system">System</v-tab>
        </v-tabs>

        <v-tabs-window v-model="activeTab">
          <!-- AI Tab -->
          <v-tabs-window-item value="ai">
            <v-card flat>
              <v-card-text class="pa-0">
                <v-tabs v-model="aiSubTab" color="primary" density="compact" class="settings-subtabs mb-3">
                  <v-tab value="generation" prepend-icon="mdi-creation">Generation</v-tab>
                  <v-tab value="meta-extraction" prepend-icon="mdi-brain">Meta Extraction</v-tab>
                  <v-tab value="prompts" prepend-icon="mdi-text-box-outline">LLM Prompts</v-tab>
                </v-tabs>

                <v-tabs-window v-model="aiSubTab">
                  <!-- Generation Sub-tab -->
                  <v-tabs-window-item value="generation">
                    <GenerationSettings
                      v-model="generationSettings"
                      @save="handleGenerationSave"
                    />
                  </v-tabs-window-item>

                  <!-- Meta Extraction Sub-tab -->
                  <v-tabs-window-item value="meta-extraction">
                    <MetaExtractionSettings />
                  </v-tabs-window-item>

                  <!-- LLM Prompts Sub-tab -->
                  <v-tabs-window-item value="prompts">
                    <PromptManager />
                  </v-tabs-window-item>
                </v-tabs-window>
              </v-card-text>
            </v-card>
          </v-tabs-window-item>

          <!-- Third Party & API Tab -->
          <v-tabs-window-item value="third-party-api">
            <ApiAccessSettings
              v-model="apiConfigs"
              @save="handleApiSave"
            />
          </v-tabs-window-item>

          <!-- Interface Tab -->
          <v-tabs-window-item value="interface">
            <InterfaceSettings
              v-model="interfaceSettings"
              @save="handleInterfaceSave"
            />
          </v-tabs-window-item>

          <!-- Content Tab -->
          <v-tabs-window-item value="content">
            <v-card flat>
              <v-card-text class="pa-0">
                <v-tabs v-model="contentSubTab" color="primary" density="compact" class="settings-subtabs mb-3">
                  <v-tab value="rundown-templates" prepend-icon="mdi-file-document-outline">Rundown Templates</v-tab>
                  <v-tab value="content-library" prepend-icon="mdi-library">Content Library</v-tab>
                  <v-tab value="episode-blueprint" prepend-icon="mdi-folder-tree">Episode Blueprint</v-tab>
                </v-tabs>

                <v-tabs-window v-model="contentSubTab">
                  <v-tabs-window-item value="rundown-templates">
                    <RundownTemplateManager />
                  </v-tabs-window-item>

                  <v-tabs-window-item value="content-library">
                    <ContentLibraryManager />
                  </v-tabs-window-item>

                  <v-tabs-window-item value="episode-blueprint">
                    <EpisodeBlueprintSettings />
                  </v-tabs-window-item>
                </v-tabs-window>
              </v-card-text>
            </v-card>
          </v-tabs-window-item>

          <!-- Whiteboard Tab -->
          <v-tabs-window-item value="whiteboard">
            <WhiteboardSettings />
          </v-tabs-window-item>

          <!-- System Tab -->
          <v-tabs-window-item value="system">
            <SystemSettings
              v-model="systemSettings"
              @save="handleSystemSave"
            />
          </v-tabs-window-item>
        </v-tabs-window>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import InterfaceSettings from '@/components/settings/InterfaceSettings.vue' // eslint-disable-line no-unused-vars
import ApiAccessSettings from '@/components/settings/ApiAccessSettings.vue' // eslint-disable-line no-unused-vars
import GenerationSettings from '@/components/settings/GenerationSettings.vue' // eslint-disable-line no-unused-vars
import MetaExtractionSettings from '@/components/settings/MetaExtractionSettings.vue' // eslint-disable-line no-unused-vars
import SystemSettings from '@/components/settings/SystemSettings.vue' // eslint-disable-line no-unused-vars
import PromptManager from '@/components/PromptManager.vue' // eslint-disable-line no-unused-vars
import RundownTemplateManager from '@/components/settings/RundownTemplateManager.vue' // eslint-disable-line no-unused-vars
import ContentLibraryManager from '@/components/settings/ContentLibraryManager.vue' // eslint-disable-line no-unused-vars
import EpisodeBlueprintSettings from '@/components/settings/EpisodeBlueprintSettings.vue' // eslint-disable-line no-unused-vars
import { applyIndicatorCSSVars } from '@/composables/useContentIndicators'
import WhiteboardSettings from '@/components/settings/WhiteboardSettings.vue' // eslint-disable-line no-unused-vars
import { useUserPrefs } from '@/composables/useUserPrefs'

// Admin detection (permissive — falls back closed at the API layer anyway).
const isAdmin = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('user-data') || '{}')
    if (u.is_admin || u.is_superuser) return true
    if (u.access_level === 'admin') return true
    if (typeof u.role === 'string' && u.role.toLowerCase().includes('admin')) return true
    if (Array.isArray(u.roles) && u.roles.some(r => String(r).toLowerCase().includes('admin'))) return true
    if (Array.isArray(u.permissions) && (u.permissions.includes('admin.*') || u.permissions.includes('*'))) return true
  } catch { /* noop */ }
  return false
})

// Local mirror of the active write scope. Defaults to 'user' on enter,
// resets to 'user' on leave so other parts of the app aren't accidentally
// writing to the global default.
const writeScopeLocal = ref('user')

function onScopeChange(next) {
  writeScopeLocal.value = next
  userPrefs.setScope(next)
}

onMounted(() => {
  // Always start in personal scope when entering Settings.
  writeScopeLocal.value = 'user'
  userPrefs.setScope('user')
})

onBeforeUnmount(() => {
  // Belt-and-suspenders reset so a leftover 'global' scope can't bite us
  // from another view.
  userPrefs.setScope('user')
})

const userPrefs = useUserPrefs()
// Per-user pref `settings.tabs` consolidates the three localStorage keys.
// Read with one-time fallback to legacy values for migration.
const _legacyTabs = {
  active: localStorage.getItem('settingsActiveTab') || 'ai',
  ai: localStorage.getItem('settingsAiSubTab') || 'generation',
  content: localStorage.getItem('settingsContentSubTab') || 'rundown-templates'
}
const _savedTabs = userPrefs.get('settings.tabs', _legacyTabs)
const activeTab = ref(_savedTabs.active || _legacyTabs.active)
const aiSubTab = ref(_savedTabs.ai || _legacyTabs.ai)
const contentSubTab = ref(_savedTabs.content || _legacyTabs.content)
const apiConfigs = ref({
  ollama: {
    host: '',
    apiKey: '',
    enabled: false
  },
  openai: {
    apiKey: '',
    organization: '',
    enabled: false
  },
  anthropic: {
    apiKey: '',
    enabled: false
  },
  gemini: {
    apiKey: '',
    enabled: false
  },
  grok: {
    apiKey: '',
    enabled: false
  },
  google: {
    clientId: '',
    clientSecret: '',
    serviceAccount: '',
    driveEnabled: false,
    calendarEnabled: false
  },
  youtube: {
    apiKey: '',
    clientId: '',
    enabled: false
  },
  vimeo: {
    accessToken: '',
    enabled: false
  },
  twitter: {
    bearerToken: '',
    apiKey: '',
    apiSecret: '',
    enabled: false
  },
  tiktok: {
    clientKey: '',
    clientSecret: '',
    enabled: false
  },
  aws: {
    accessKeyId: '',
    secretAccessKey: '',
    region: '',
    bucket: '',
    enabled: false
  },
  slack: {
    botToken: '',
    webhookUrl: '',
    enabled: false
  },
  discord: {
    botToken: '',
    webhookUrl: '',
    enabled: false
  },
  twilio: {
    accountSid: '',
    authToken: '',
    phoneNumber: '',
    enabled: false
  },
  asterisk: {
    host: '',
    amiPort: '5038',
    amiUsername: '',
    amiSecret: '',
    conferenceContext: 'conferences',
    recordingsPath: '/var/spool/asterisk/monitor',
    enabled: false
  },
  email: {
    provider: '',
    apiKey: '',
    fromEmail: '',
    enabled: false
  },
  github: {
    accessToken: '',
    organization: '',
    enabled: false
  },
  gitlab: {
    accessToken: '',
    baseUrl: 'https://gitlab.com',
    enabled: false
  },
  zapier: {
    webhookUrl: '',
    enabled: false
  },
  stabilityAi: {
    apiKey: '',
    enabled: false
  },
  elevenLabs: {
    apiKey: '',
    enabled: false
  },
  webhooks: {
    endpoint: '',
    secret: '',
    enabled: false
  },
  vmix: {
    host: '',
    port: '8088',
    remoteMediaPath: '',
    enabled: false
  },
  comfyui: {
    host: '',
    port: '8188',
    enabled: false
  }
})
// System settings (managed by SystemSettings component)
const systemSettings = ref({})
// Interface settings
const interfaceSettings = ref({
  theme: 'dark',
  editorFontSize: 14,
  editorFontFamily: 'monospace',
  editorLineNumbers: true,
  editorWordWrap: true,
  editorAutoSave: true,
  pastePlainTextOnly: true,  // Strip formatting when pasting (enabled by default)
  // Autoformat settings
  autoformatEnabled: true,           // Enable periodic autoformat
  autoformatInterval: 30,            // Interval in seconds (default 30)
  autoformatStripSpans: true,        // Strip <span> tags from Google Docs
  autoformatRemoveEmptyParagraphs: true,  // Remove empty <p> tags
  autoformatRemoveLeadingDashes: true,    // Remove leading dashes from paragraphs
  autoformatCleanWhitespace: true,   // Clean up extra spaces and &nbsp;
  // Layout settings
  sidebarWidth: 300,
  compactMode: false,
  showToolbarLabels: true,
  highContrast: false,
  reducedMotion: false,
  keyboardShortcuts: true
})
// Generation settings
const generationSettings = ref({
  fsqBackgroundVideo: '/assets/preview-background.mp4',
  templateLibraryPath: '/mnt/sync/disaffected/templates',
  mediaAssetsPath: '/mnt/sync/disaffected/media assets'
})
// Content Generator settings (for Ctrl+Alt+Shift+# test content)
const contentGeneratorService = ref('ollama')
const contentGeneratorModel = ref('llama3:latest')
const savingContentGenerator = ref(false) // eslint-disable-line no-unused-vars
const availableOllamaModels = ref([])
const contentGeneratorServiceOptions = [ // eslint-disable-line no-unused-vars
  { title: 'Auto (Smart Routing)', value: 'auto' },
  { title: 'Ollama (Local)', value: 'ollama' },
  { title: 'OpenAI', value: 'openai' },
  { title: 'Anthropic', value: 'anthropic' },
  { title: 'Gemini', value: 'gemini' },
  { title: 'Grok', value: 'grok' }
]
const contentGeneratorModelOptions = ref([])

// Watchers
function _persistTabs() {
  const value = { active: activeTab.value, ai: aiSubTab.value, content: contentSubTab.value }
  // localStorage kept as offline fallback for unauthenticated reload
  localStorage.setItem('settingsActiveTab', value.active)
  localStorage.setItem('settingsAiSubTab', value.ai)
  localStorage.setItem('settingsContentSubTab', value.content)
  userPrefs.set('settings.tabs', value)
}

watch(activeTab, _persistTabs)
watch(aiSubTab, _persistTabs)
watch(contentSubTab, _persistTabs)

watch(contentGeneratorService, () => {
  updateModelOptions()
})

// Methods
async function loadAllSettings() {
  try {
    // Load general settings
    const response = await fetch('/api/settings/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })

    if (response.ok) {
      const settings = await response.json()

      // Load interface settings — global default first, then layer
      // the current user's personal override on top (if any).
      if (settings.interface) {
        interfaceSettings.value = { ...interfaceSettings.value, ...settings.interface }
      }
      const personal = userPrefs.get('interface.settings', null)
      if (personal && typeof personal === 'object') {
        interfaceSettings.value = { ...interfaceSettings.value, ...personal }
        // Also update localStorage so non-Settings consumers
        // (ContentEditor, EditorPaste) see the user's values immediately.
        localStorage.setItem('showbuild_interface_settings', JSON.stringify(interfaceSettings.value))
      }

      // Load generation settings
      if (settings.generation) {
        generationSettings.value = { ...generationSettings.value, ...settings.generation }
      }

      // Load system settings (pass to SystemSettings component)
      if (settings.system || settings.media_paths) {
        systemSettings.value = {
          ...systemSettings.value,
          ...settings.system,
          // Map media paths to system settings structure
          showRoot: settings.media_paths?.show_root || '/mnt/sync/disaffected',
          episodesPath: settings.media_paths?.episodes_folder || '',
          mediaAssetsPath: settings.media_paths?.media_assets || '',
          libraryPath: settings.media_paths?.blueprints || '',
          uploadsPath: settings.media_paths?.uploads || '',
          processPath: settings.media_paths?.process || '',
          archiveEnabled: settings.media_paths?.archive_enabled || false,
          archiveType: settings.media_paths?.archive_type || 's3',
          archiveEndpoint: settings.media_paths?.archive_endpoint || ''
        }
      }
    }

    // Load API configurations separately
    const apiResponse = await fetch('/api/settings/api-configs', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })

    if (apiResponse.ok) {
      const apiData = await apiResponse.json()
      console.log('🔑 API Configs Response:', apiData)
      if (apiData.success && apiData.data) {
        // Flatten the hierarchical API config structure for the frontend form
        const config = apiData.data
        const flattened = {}

        // Flatten preproduction AI services
        if (config.preproduction?.ai_services) {
          console.log('🔓 AI Services loaded:', config.preproduction.ai_services)
          Object.assign(flattened, config.preproduction.ai_services)
        }

        // Flatten preproduction storage
        if (config.preproduction?.storage) {
          Object.assign(flattened, config.preproduction.storage)
        }

        // Flatten preproduction communication
        if (config.preproduction?.communication) {
          Object.assign(flattened, config.preproduction.communication)
        }

        // Flatten promotion social media
        if (config.promotion?.social_media) {
          Object.assign(flattened, config.promotion.social_media)
        }

        // Flatten production control
        if (config.production?.control) {
          Object.assign(flattened, config.production.control)
        }

        // Flatten generation ai_services (comfyui)
        if (config.generation?.ai_services) {
          Object.assign(flattened, config.generation.ai_services)
        }

        // Flatten development
        if (config.development) {
          Object.assign(flattened, config.development)
        }

        // Update apiConfigs with loaded data, preserving defaults for missing fields
        apiConfigs.value = { ...apiConfigs.value, ...flattened }
      }
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
  }
}

async function handleInterfaceSave(settings) {
  // Update local state
  interfaceSettings.value = settings
  console.log('Interface settings saved:', settings)

  // localStorage stays as the offline / cross-component cache so existing
  // readers (ContentEditor, useEditorPaste, useContentIndicators) keep
  // working unchanged. The per-user pref is the source of truth on next
  // hydrate and travels with the user across devices.
  localStorage.setItem('showbuild_interface_settings', JSON.stringify(settings))
  userPrefs.set('interface.settings', settings)
  // Re-apply indicator CSS vars so color changes take effect immediately
  applyIndicatorCSSVars()

  // Persist to backend
  try {
    const response = await fetch('/api/settings/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      },
      body: JSON.stringify({
        interface: settings
      })
    })

    if (response.ok) {
      console.log('✅ Interface settings saved to database')
    } else {
      console.error('Failed to save interface settings:', await response.text())
    }
  } catch (error) {
    console.error('Error saving interface settings:', error)
  }
}

function handleApiSave(configs) {
  // Update local state
  apiConfigs.value = configs
  console.log('API configuration saved:', configs)
}

function handleSystemSave(settings) {
  // Update local state
  systemSettings.value = settings
  console.log('System settings saved:', settings)
  // The actual saving is handled by the SystemSettings component
}

async function handleGenerationSave(settings) {
  // Update local state
  generationSettings.value = settings
  console.log('Generation settings saved:', settings)

  // Persist to backend
  try {
    const response = await fetch('/api/settings/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      },
      body: JSON.stringify({
        generation: settings
      })
    })

    if (response.ok) {
      console.log('✅ Generation settings saved to database')
    } else {
      console.error('Failed to save generation settings:', await response.text())
    }
  } catch (error) {
    console.error('Error saving generation settings:', error)
  }
}

// Content Generator methods
async function loadContentGeneratorSettings() {
  // Load from localStorage (where useLLM.js stores routing settings)
  const saved = localStorage.getItem('llm-routing-settings')
  if (saved) {
    try {
      const settings = JSON.parse(saved)
      // Parse the contentExpansion setting (format: "service:model" or "auto")
      const contentExpansion = settings.routing?.contentExpansion || 'auto'
      if (contentExpansion === 'auto') {
        contentGeneratorService.value = 'auto'
        contentGeneratorModel.value = null
      } else if (contentExpansion.includes(':')) {
        const parts = contentExpansion.split(':')
        contentGeneratorService.value = parts[0]
        contentGeneratorModel.value = parts.slice(1).join(':')
      } else {
        contentGeneratorService.value = contentExpansion
        contentGeneratorModel.value = null
      }

      // Also check ollamaModels for contentExpansion
      if (settings.ollamaModels?.contentExpansion) {
        contentGeneratorModel.value = settings.ollamaModels.contentExpansion
      }
    } catch (e) {
      console.error('Failed to parse llm-routing-settings:', e)
    }
  }

  // Load available Ollama models
  await loadOllamaModels()
}

async function loadOllamaModels() {
  try {
    // Use the correct endpoint: /api/llm/ollama/models
    const response = await fetch('/api/llm/ollama/models', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      // Ollama returns { models: [{ name: 'llama3:latest', ... }, ...] }
      availableOllamaModels.value = data.models?.map(m => m.name) || []
      console.log('📋 Loaded Ollama models:', availableOllamaModels.value)
      updateModelOptions()
    } else {
      console.warn('Ollama models endpoint returned:', response.status)
      loadFallbackModels()
    }
  } catch (e) {
    console.error('Failed to load Ollama models:', e)
    loadFallbackModels()
  }
}

function loadFallbackModels() {
  // Fallback to common models if API unavailable
  availableOllamaModels.value = [
    'llama3:latest',
    'mistral:7b',
    'deepseek-r1:8b',
    'Qwen2.5-Coder:7b',
    'codellama:34b'
  ]
  updateModelOptions()
}

function updateModelOptions() {
  if (contentGeneratorService.value === 'ollama') {
    contentGeneratorModelOptions.value = availableOllamaModels.value.map(m => ({
      title: m,
      value: m
    }))
  } else if (contentGeneratorService.value === 'openai') {
    contentGeneratorModelOptions.value = [
      { title: 'GPT-4', value: 'gpt-4' },
      { title: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
      { title: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
    ]
  } else if (contentGeneratorService.value === 'anthropic') {
    contentGeneratorModelOptions.value = [
      { title: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
      { title: 'Claude 3 Opus', value: 'claude-3-opus-20240229' },
      { title: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307' }
    ]
  } else if (contentGeneratorService.value === 'gemini') {
    contentGeneratorModelOptions.value = [
      { title: 'Gemini 2.0 Flash', value: 'gemini-2.0-flash' },
      { title: 'Gemini 1.5 Pro', value: 'gemini-1.5-pro' }
    ]
  } else if (contentGeneratorService.value === 'grok') {
    contentGeneratorModelOptions.value = [
      { title: 'Grok 4', value: 'grok-4-latest' },
      { title: 'Grok 3', value: 'grok-3' }
    ]
  } else {
    contentGeneratorModelOptions.value = []
  }
}

function selectOllamaModel(model) { // eslint-disable-line no-unused-vars
  contentGeneratorService.value = 'ollama'
  contentGeneratorModel.value = model
  updateModelOptions()
}

function saveContentGeneratorSettings() { // eslint-disable-line no-unused-vars
  savingContentGenerator.value = true

  // Load existing settings or create new
  let settings = {}
  const saved = localStorage.getItem('llm-routing-settings')
  if (saved) {
    try {
      settings = JSON.parse(saved)
    } catch (e) {
      settings = {}
    }
  }

  // Ensure structure exists
  if (!settings.routing) settings.routing = {}
  if (!settings.ollamaModels) settings.ollamaModels = {}

  // Set the content expansion routing
  if (contentGeneratorService.value === 'auto') {
    settings.routing.contentExpansion = 'auto'
  } else if (contentGeneratorModel.value) {
    settings.routing.contentExpansion = `${contentGeneratorService.value}:${contentGeneratorModel.value}`
    // Also set in ollamaModels if using Ollama
    if (contentGeneratorService.value === 'ollama') {
      settings.ollamaModels.contentExpansion = contentGeneratorModel.value
    }
  } else {
    settings.routing.contentExpansion = contentGeneratorService.value
  }

  // Save to localStorage AND the per-user pref (DB-backed, cross-device).
  localStorage.setItem('llm-routing-settings', JSON.stringify(settings))
  userPrefs.set('llm.routing', settings)

  console.log('✅ Content Generator settings saved:', {
    service: contentGeneratorService.value,
    model: contentGeneratorModel.value,
    routing: settings.routing.contentExpansion
  })

  setTimeout(() => {
    savingContentGenerator.value = false
  }, 500)
}

function resetContentGeneratorToDefaults() { // eslint-disable-line no-unused-vars
  contentGeneratorService.value = 'ollama'
  contentGeneratorModel.value = 'llama3:latest'
  updateModelOptions()
  saveContentGeneratorSettings()
}

// Lifecycle
onMounted(async () => {
  // Load existing configurations when component mounts
  await loadAllSettings()
  // Load content generator settings
  await loadContentGeneratorSettings()
})
</script>

<style scoped>
.v-tabs {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

/* Sub-tabs (under each top-level Settings tab) — slimmer + tinted so the
   hierarchy reads as "section › subsection" instead of two equal rows. */
.settings-subtabs {
  background: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.settings-subtabs :deep(.v-tab) {
  font-size: 0.8rem !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  min-height: 36px !important;
  height: 36px !important;
}

.scope-toggle {
  background: rgba(0, 0, 0, 0.02);
}

.v-card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

/* Vertical tabs for AI & LLM section */
.v-tabs--vertical {
  min-width: 200px;
  border-right: 1px solid rgba(0, 0, 0, 0.12);
}

.compact-color-selector {
  padding: 0;
  max-height: 400px;
  overflow-y: auto;
}

.compact-color-selector :deep(table) {
  font-size: 0.875rem;
}

.compact-color-selector :deep(th),
.compact-color-selector :deep(td) {
  padding: 4px 8px !important;
}

.compact-color-selector :deep(.v-field) {
  min-height: 32px !important;
}

.compact-color-selector :deep(.v-field__input) {
  padding: 4px 8px !important;
  min-height: 32px !important;
}

</style>