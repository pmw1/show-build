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
          <v-tab value="ai-llm">AI & LLM</v-tab>
          <v-tab value="interface">Interface</v-tab>
          <v-tab value="system">System</v-tab>
        </v-tabs>

        <v-tabs-window v-model="activeTab">
          <!-- AI & LLM Tab (consolidates API Access, Generation, Prompts) -->
          <v-tabs-window-item value="ai-llm">
            <v-card flat>
              <v-card-text class="pa-0">
                <v-tabs v-model="aiSubTab" direction="vertical" color="primary">
                  <v-tab value="api-access" prepend-icon="mdi-key">API Access</v-tab>
                  <v-tab value="generation" prepend-icon="mdi-creation">Generation</v-tab>
                  <v-tab value="prompts" prepend-icon="mdi-brain">LLM Prompts</v-tab>
                </v-tabs>

                <v-tabs-window v-model="aiSubTab">
                  <!-- API Access Sub-tab -->
                  <v-tabs-window-item value="api-access">
                    <ApiAccessSettings
                      v-model="apiConfigs"
                      @save="handleApiSave"
                    />
                  </v-tabs-window-item>

                  <!-- Generation Sub-tab -->
                  <v-tabs-window-item value="generation">
                    <GenerationSettings
                      v-model="generationSettings"
                      @save="handleGenerationSave"
                    />
                  </v-tabs-window-item>

                  <!-- LLM Prompts Sub-tab -->
                  <v-tabs-window-item value="prompts">
                    <PromptManager />
                  </v-tabs-window-item>
                </v-tabs-window>
              </v-card-text>
            </v-card>
          </v-tabs-window-item>

          <!-- Interface Tab -->
          <v-tabs-window-item value="interface">
            <InterfaceSettings
              v-model="interfaceSettings"
              @save="handleInterfaceSave"
            />
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
import SystemSettings from '@/components/settings/SystemSettings.vue'
import PromptManager from '@/components/PromptManager.vue'

export default {
  name: 'SettingsView',
  components: {
    InterfaceSettings,
    ApiAccessSettings,
    GenerationSettings,
    SystemSettings,
    PromptManager
  },
  data() {
    return {
      activeTab: localStorage.getItem('settingsActiveTab') || 'ai-llm', // Restore last used tab or default to AI & LLM
      aiSubTab: localStorage.getItem('settingsAiSubTab') || 'api-access', // Sub-tab for AI & LLM section
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
      }
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
    
    handleInterfaceSave(settings) {
      // Update local state
      this.interfaceSettings = settings
      console.log('Interface settings saved:', settings)
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
  },
  async mounted() {
    // Load existing configurations when component mounts
    await this.loadAllSettings()
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