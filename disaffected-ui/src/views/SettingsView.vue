<template>
  <v-container fluid class="pa-4">
    <v-row>
      <v-col>
        <h2 class="text-h4 font-weight-bold mb-6">Settings</h2>
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
                <v-tabs v-model="aiSubTab" direction="vertical" color="primary">
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
                <v-tabs v-model="contentSubTab" direction="vertical" color="primary">
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

<script>
import InterfaceSettings from '@/components/settings/InterfaceSettings.vue'
import ApiAccessSettings from '@/components/settings/ApiAccessSettings.vue'
import GenerationSettings from '@/components/settings/GenerationSettings.vue'
import MetaExtractionSettings from '@/components/settings/MetaExtractionSettings.vue'
import SystemSettings from '@/components/settings/SystemSettings.vue'
import PromptManager from '@/components/PromptManager.vue'
import RundownTemplateManager from '@/components/settings/RundownTemplateManager.vue'
import ContentLibraryManager from '@/components/settings/ContentLibraryManager.vue'
import EpisodeBlueprintSettings from '@/components/settings/EpisodeBlueprintSettings.vue'
import WhiteboardSettings from '@/components/settings/WhiteboardSettings.vue'

export default {
  name: 'SettingsView',
  components: {
    InterfaceSettings,
    ApiAccessSettings,
    GenerationSettings,
    MetaExtractionSettings,
    SystemSettings,
    PromptManager,
    RundownTemplateManager,
    ContentLibraryManager,
    EpisodeBlueprintSettings,
    WhiteboardSettings
  },
  data() {
    return {
      activeTab: localStorage.getItem('settingsActiveTab') || 'ai', // Restore last used tab or default to AI
      aiSubTab: localStorage.getItem('settingsAiSubTab') || 'generation', // Sub-tab for AI section
      contentSubTab: localStorage.getItem('settingsContentSubTab') || 'rundown-templates', // Sub-tab for Content section
      apiConfigs: {
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
        }
      },
      // System settings (managed by SystemSettings component)
      systemSettings: {},
      // Interface settings
      interfaceSettings: {
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
      },
      // Generation settings
      generationSettings: {
        fsqBackgroundVideo: '/assets/preview-background.mp4',
        templateLibraryPath: '/mnt/sync/disaffected/templates',
        mediaAssetsPath: '/mnt/sync/disaffected/media assets'
      },
      // Content Generator settings (for Ctrl+Alt+Shift+# test content)
      contentGeneratorService: 'ollama',
      contentGeneratorModel: 'llama3:latest',
      savingContentGenerator: false,
      availableOllamaModels: [],
      contentGeneratorServiceOptions: [
        { title: 'Auto (Smart Routing)', value: 'auto' },
        { title: 'Ollama (Local)', value: 'ollama' },
        { title: 'OpenAI', value: 'openai' },
        { title: 'Anthropic', value: 'anthropic' },
        { title: 'Gemini', value: 'gemini' },
        { title: 'Grok', value: 'grok' }
      ],
      contentGeneratorModelOptions: []
    }
  },
  watch: {
    activeTab(newTab) {
      // Save the current tab to localStorage for persistence across page reloads
      localStorage.setItem('settingsActiveTab', newTab);
    },
    aiSubTab(newSubTab) {
      // Save the AI sub-tab to localStorage for persistence
      localStorage.setItem('settingsAiSubTab', newSubTab);
    },
    contentGeneratorService() {
      this.updateModelOptions()
    }
  },
  methods: {
    
    // Load settings for components
    async loadAllSettings() {
      try {
        // Load general settings
        const response = await fetch('/api/settings/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        })

        if (response.ok) {
          const settings = await response.json()

          // Load interface settings
          if (settings.interface) {
            this.interfaceSettings = { ...this.interfaceSettings, ...settings.interface }
          }

          // Load generation settings
          if (settings.generation) {
            this.generationSettings = { ...this.generationSettings, ...settings.generation }
          }

          // Load system settings (pass to SystemSettings component)
          if (settings.system || settings.media_paths) {
            this.systemSettings = {
              ...this.systemSettings,
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

            // Flatten development
            if (config.development) {
              Object.assign(flattened, config.development)
            }

            // Update apiConfigs with loaded data, preserving defaults for missing fields
            this.apiConfigs = { ...this.apiConfigs, ...flattened }
          }
        }
      } catch (error) {
        console.error('Failed to load settings:', error)
      }
    },
    
    async handleInterfaceSave(settings) {
      // Update local state
      this.interfaceSettings = settings
      console.log('Interface settings saved:', settings)

      // Also save to localStorage for immediate access by EditorPanel
      localStorage.setItem('showbuild_interface_settings', JSON.stringify(settings))

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
    },
    
    handleApiSave(configs) {
      // Update local state
      this.apiConfigs = configs
      console.log('API configuration saved:', configs)
    },
    
    handleSystemSave(settings) {
      // Update local state
      this.systemSettings = settings
      console.log('System settings saved:', settings)
      // The actual saving is handled by the SystemSettings component
    },

    async handleGenerationSave(settings) {
      // Update local state
      this.generationSettings = settings
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
    },

    // Content Generator methods
    async loadContentGeneratorSettings() {
      // Load from localStorage (where useLLM.js stores routing settings)
      const saved = localStorage.getItem('llm-routing-settings')
      if (saved) {
        try {
          const settings = JSON.parse(saved)
          // Parse the contentExpansion setting (format: "service:model" or "auto")
          const contentExpansion = settings.routing?.contentExpansion || 'auto'
          if (contentExpansion === 'auto') {
            this.contentGeneratorService = 'auto'
            this.contentGeneratorModel = null
          } else if (contentExpansion.includes(':')) {
            const parts = contentExpansion.split(':')
            this.contentGeneratorService = parts[0]
            this.contentGeneratorModel = parts.slice(1).join(':')
          } else {
            this.contentGeneratorService = contentExpansion
            this.contentGeneratorModel = null
          }

          // Also check ollamaModels for contentExpansion
          if (settings.ollamaModels?.contentExpansion) {
            this.contentGeneratorModel = settings.ollamaModels.contentExpansion
          }
        } catch (e) {
          console.error('Failed to parse llm-routing-settings:', e)
        }
      }

      // Load available Ollama models
      await this.loadOllamaModels()
    },

    async loadOllamaModels() {
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
          this.availableOllamaModels = data.models?.map(m => m.name) || []
          console.log('📋 Loaded Ollama models:', this.availableOllamaModels)
          this.updateModelOptions()
        } else {
          console.warn('Ollama models endpoint returned:', response.status)
          this.loadFallbackModels()
        }
      } catch (e) {
        console.error('Failed to load Ollama models:', e)
        this.loadFallbackModels()
      }
    },

    loadFallbackModels() {
      // Fallback to common models if API unavailable
      this.availableOllamaModels = [
        'llama3:latest',
        'mistral:7b',
        'deepseek-r1:8b',
        'Qwen2.5-Coder:7b',
        'codellama:34b'
      ]
      this.updateModelOptions()
    },

    updateModelOptions() {
      if (this.contentGeneratorService === 'ollama') {
        this.contentGeneratorModelOptions = this.availableOllamaModels.map(m => ({
          title: m,
          value: m
        }))
      } else if (this.contentGeneratorService === 'openai') {
        this.contentGeneratorModelOptions = [
          { title: 'GPT-4', value: 'gpt-4' },
          { title: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
          { title: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
        ]
      } else if (this.contentGeneratorService === 'anthropic') {
        this.contentGeneratorModelOptions = [
          { title: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
          { title: 'Claude 3 Opus', value: 'claude-3-opus-20240229' },
          { title: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307' }
        ]
      } else if (this.contentGeneratorService === 'gemini') {
        this.contentGeneratorModelOptions = [
          { title: 'Gemini 2.0 Flash', value: 'gemini-2.0-flash' },
          { title: 'Gemini 1.5 Pro', value: 'gemini-1.5-pro' }
        ]
      } else if (this.contentGeneratorService === 'grok') {
        this.contentGeneratorModelOptions = [
          { title: 'Grok 4', value: 'grok-4-latest' },
          { title: 'Grok 3', value: 'grok-3' }
        ]
      } else {
        this.contentGeneratorModelOptions = []
      }
    },

    selectOllamaModel(model) {
      this.contentGeneratorService = 'ollama'
      this.contentGeneratorModel = model
      this.updateModelOptions()
    },

    saveContentGeneratorSettings() {
      this.savingContentGenerator = true

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
      if (this.contentGeneratorService === 'auto') {
        settings.routing.contentExpansion = 'auto'
      } else if (this.contentGeneratorModel) {
        settings.routing.contentExpansion = `${this.contentGeneratorService}:${this.contentGeneratorModel}`
        // Also set in ollamaModels if using Ollama
        if (this.contentGeneratorService === 'ollama') {
          settings.ollamaModels.contentExpansion = this.contentGeneratorModel
        }
      } else {
        settings.routing.contentExpansion = this.contentGeneratorService
      }

      // Save to localStorage
      localStorage.setItem('llm-routing-settings', JSON.stringify(settings))

      console.log('✅ Content Generator settings saved:', {
        service: this.contentGeneratorService,
        model: this.contentGeneratorModel,
        routing: settings.routing.contentExpansion
      })

      setTimeout(() => {
        this.savingContentGenerator = false
      }, 500)
    },

    resetContentGeneratorToDefaults() {
      this.contentGeneratorService = 'ollama'
      this.contentGeneratorModel = 'llama3:latest'
      this.updateModelOptions()
      this.saveContentGeneratorSettings()
    }
  },
  async mounted() {
    // Load existing configurations when component mounts
    await this.loadAllSettings()
    // Load content generator settings
    await this.loadContentGeneratorSettings()
  }
}
</script>

<style scoped>
.v-tabs {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
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