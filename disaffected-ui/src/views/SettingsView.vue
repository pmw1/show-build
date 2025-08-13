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
          <v-tab value="api">API Access</v-tab>
          <v-tab value="interface">Interface</v-tab>
          <v-tab value="rundown">Rundown</v-tab>
          <v-tab value="system">System</v-tab>
        </v-tabs>

        <v-tabs-window v-model="activeTab">
          <!-- API Access Tab -->
          <v-tabs-window-item value="api">
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

          <!-- Rundown Tab -->
          <v-tabs-window-item value="rundown">
            <RundownSettings 
              v-model="rundownSettings"
              @save="handleRundownSave"
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
import RundownSettings from '@/components/settings/RundownSettings.vue'
import SystemSettings from '@/components/settings/SystemSettings.vue'

export default {
  name: 'SettingsView',
  components: {
    InterfaceSettings,
    ApiAccessSettings,
    RundownSettings,
    SystemSettings
  },
  data() {
    return {
      activeTab: localStorage.getItem('settingsActiveTab') || 'api', // Restore last used tab or default to API
      apiConfigs: {
        ollama: {
          host: '',
          apiKey: '',
          enabled: false
        },
        whisper: {
          host: '',
          endpoint: '',
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
      // Rundown settings
      rundownSettings: {
        itemTypes: [
          { id: 1, name: 'Segment', prefix: 'SEG', defaultDuration: 300, color: 'primary', enabled: true },
          { id: 2, name: 'Break', prefix: 'BRK', defaultDuration: 120, color: 'warning', enabled: true },
          { id: 3, name: 'Promo', prefix: 'PRO', defaultDuration: 30, color: 'info', enabled: true },
          { id: 4, name: 'Teaser', prefix: 'TSR', defaultDuration: 15, color: 'secondary', enabled: true }
        ],
        defaultSegmentDuration: 300,
        defaultBreakDuration: 120,
        showBacktiming: true,
        autoCalculateTiming: true,
        autoNumber: true,
        numberingStart: 10,
        numberingStep: 10,
        defaultExportFormat: 'Markdown',
        includeTimingInExport: true,
        includeNotesInExport: true
      }
    }
  },
  watch: {
    activeTab(newTab) {
      // Save the current tab to localStorage for persistence across page reloads
      localStorage.setItem('settingsActiveTab', newTab);
    }
  },
  methods: {
    
    // Load settings for components
    async loadAllSettings() {
      try {
        const response = await fetch('/api/settings/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        
        if (response.ok) {
          const settings = await response.json()
          
          // Load interface settings
          if (settings.interface) {
            this.interfaceSettings = { ...this.interfaceSettings, ...settings.interface }
          }
          
          // Load rundown settings  
          if (settings.rundown) {
            this.rundownSettings = { ...this.rundownSettings, ...settings.rundown }
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
    
    handleRundownSave(settings) {
      // Update local state
      this.rundownSettings = settings
      console.log('Rundown settings saved:', settings)
    },
    
    handleSystemSave(settings) {
      // Update local state
      this.systemSettings = settings
      console.log('System settings saved:', settings)
      // The actual saving is handled by the SystemSettings component
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